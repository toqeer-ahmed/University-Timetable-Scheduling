from flask import Flask, render_template, request, jsonify
import pandas as pd
from data_loader import clean_and_structure_data
from scheduler import GeneticAlgorithmScheduler
from constraints import calculate_fitness

app = Flask(__name__)

# Cache the loaded data
data_cache = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate_timetable():
    global data_cache
    if data_cache is None:
        data_cache = clean_and_structure_data()

    req_data = request.json
    generations = int(req_data.get('generations', 100))
    population = int(req_data.get('population', 50))

    scheduler = GeneticAlgorithmScheduler(data_cache, population_size=population, mutation_rate=0.2, elitism=0.1)
    best_schedule, best_fit, best_hc = scheduler.run(max_generations=generations)

    fit, hc, sp = calculate_fitness(best_schedule, data_cache)

    # Format the data for the frontend
    timetable_data = []
    for s_id, assignment in best_schedule.items():
        session = next(s for s in data_cache['sessions'] if s['session_id'] == s_id)
        room = data_cache['rooms'][assignment['room_id']]
        slot = data_cache['time_slots'][assignment['slot_id']]
        
        slot_keys = list(data_cache['time_slots'].keys())
        start_slot_index = slot_keys.index(assignment['slot_id'])
        duration = session.get('duration', 1)
        end_slot_id = slot_keys[min(start_slot_index + duration - 1, len(slot_keys) - 1)]
        end_slot = data_cache['time_slots'][end_slot_id]

        course = data_cache['courses'][session['course_id']]
        group = data_cache['groups'][session['group_id']]
        
        teacher_names = [data_cache['teachers'][tid]['name'] for tid in session['teacher_ids']]
        teachers_str = ", ".join(teacher_names)

        timetable_data.append({
            'day': slot['day'],
            'start_time': slot['start_time'],
            'end_time': end_slot['end_time'],
            'group': group['name'],
            'course': course['name'],
            'type': course['type'],
            'teachers': teachers_str,
            'room': room['name']
        })

    # Sort data logically
    day_order = {'Mon': 1, 'Tue': 2, 'Wed': 3, 'Thu': 4, 'Fri': 5}
    timetable_data.sort(key=lambda x: (day_order.get(x['day'], 99), x['start_time'], x['room']))

    return jsonify({
        'status': 'success',
        'metrics': {
            'hard_conflicts': hc,
            'soft_penalty': sp,
            'fitness': round(fit, 6)
        },
        'timetable': timetable_data
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
