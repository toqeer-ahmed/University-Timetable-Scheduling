import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import sys

from data_loader import clean_and_structure_data
from scheduler import GeneticAlgorithmScheduler
from constraints import calculate_fitness

def generate_reports(schedule, data):
    print("\nGenerating Reports and Validating Schedule...")
    fit, hc, sp = calculate_fitness(schedule, data)
    print(f"Final Validation - Hard Conflicts: {hc}, Soft Penalty: {sp}, Fitness: {fit:.6f}")

    # Prepare readable data for DataFrame
    rows = []
    for s_id, assignment in schedule.items():
        session = next(s for s in data['sessions'] if s['session_id'] == s_id)
        room = data['rooms'][assignment['room_id']]
        slot = data['time_slots'][assignment['slot_id']]
        
        slot_keys = list(data['time_slots'].keys())
        start_slot_index = slot_keys.index(assignment['slot_id'])
        duration = session.get('duration', 1)
        end_slot_id = slot_keys[min(start_slot_index + duration - 1, len(slot_keys) - 1)]
        end_slot = data['time_slots'][end_slot_id]

        course = data['courses'][session['course_id']]
        group = data['groups'][session['group_id']]
        
        # Combine teacher names
        teacher_names = [data['teachers'][tid]['name'] for tid in session['teacher_ids']]
        teachers_str = ", ".join(teacher_names)

        rows.append({
            'Day': slot['day'],
            'Start Time': slot['start_time'],
            'End Time': end_slot['end_time'],
            'Group': group['name'],
            'Course': course['name'],
            'Type': course['type'],
            'Teachers': teachers_str,
            'Room': room['name']
        })

    df = pd.DataFrame(rows)
    
    # Sort for better readability
    day_order = {'Mon': 1, 'Tue': 2, 'Wed': 3, 'Thu': 4, 'Fri': 5}
    df['Day_Order'] = df['Day'].map(day_order)
    df = df.sort_values(by=['Day_Order', 'Start Time', 'Room']).drop(columns=['Day_Order'])

    # Export to Excel
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"University_Timetable_{timestamp}.xlsx"
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='All Sessions', index=False)
        
        # Group-wise
        for group_name, group_df in df.groupby('Group'):
            # Sheet names limit is 31 chars, clean group name
            sheet_name = str(group_name)[:31].replace(':', '').replace('/', '_')
            group_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
    print(f"Excel timetable exported to: {output_file}")
    
    return df

def generate_visualization(df):
    print("\nGenerating Room Utilization Heatmap...")
    # Create a pivot table: Rows=Rooms, Columns=Day+Time, Values=Count (1 if occupied, 0 else)
    df['TimeSlot'] = df['Day'] + " " + df['Start Time']
    
    # Cross tabulation
    utilization = pd.crosstab(df['Room'], df['TimeSlot'])
    
    plt.figure(figsize=(15, 10))
    sns.heatmap(utilization, cmap='Blues', linewidths=0.5, linecolor='gray', cbar=False)
    plt.title('Room Utilization Heatmap')
    plt.xlabel('Time Slot')
    plt.ylabel('Room')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    viz_file = "Room_Utilization_Heatmap.png"
    plt.savefig(viz_file, dpi=300)
    print(f"Visualization saved to: {viz_file}")

if __name__ == "__main__":
    print("="*50)
    print("UNIVERSITY TIMETABLE SCHEDULING SYSTEM (AI-BASED)")
    print("="*50)

    # 1 & 2. Load and clean data
    data = clean_and_structure_data()

    # 3 & 4 & 5. Initialize Scheduler and Run GA
    # Using smaller population/generations for fast testing. 
    # For optimal results, increase population_size and max_generations.
    scheduler = GeneticAlgorithmScheduler(data, population_size=100, mutation_rate=0.2, elitism=0.1)
    
    print("\nStarting Optimization (Genetic Algorithm)...")
    best_schedule, best_fit, best_hc = scheduler.run(max_generations=200)

    if best_hc > 0:
        print(f"\n[WARNING] The algorithm stopped with {best_hc} hard conflicts.")
        print("To improve this, you can increase 'max_generations' and 'population_size' in main.py")
    else:
        print(f"\n[SUCCESS] Perfect Schedule Found! 0 Hard Conflicts.")

    # 6 & 7. Validation and Output Generation
    try:
        df = generate_reports(best_schedule, data)
        generate_visualization(df)
        print("\nAll tasks completed successfully!")
    except ImportError as e:
        print(f"\nMissing library for export/visualization: {e}")
        print("Please run: pip install pandas openpyxl matplotlib seaborn")
