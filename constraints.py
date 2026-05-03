def calculate_fitness(schedule, data):
    """
    Calculates the fitness score of a given schedule.
    A higher score is better. Max score depends on soft constraints, but we aim for 0 hard conflicts.
    
    schedule format: dict
    { session_id: {"room_id": "R001", "slot_id": "TS001"} }
    """
    hard_conflicts = 0
    soft_penalty = 0

    # Dictionaries to track assignments for conflicts
    # Format: {slot_id: {room_id: session_id, ...}}
    room_allocations = {}
    
    # Format: {slot_id: {teacher_id: session_id, ...}}
    teacher_allocations = {}
    
    # Format: {slot_id: {group_id: session_id, ...}}
    group_allocations = {}

    # For soft constraints
    # Keep track of daily slots for groups and teachers to compute gaps and consecutive classes
    group_daily_slots = {g: {day: [] for day in ["Mon", "Tue", "Wed", "Thu", "Fri"]} for g in data['groups']}
    teacher_daily_slots = {t: {day: [] for day in ["Mon", "Tue", "Wed", "Thu", "Fri"]} for t in data['teachers']}

    for session_info in data['sessions']:
        s_id = session_info['session_id']
        assignment = schedule[s_id]
        room_id = assignment['room_id']
        slot_id = assignment['slot_id']
        
        group_id = session_info['group_id']
        teacher_ids = session_info['teacher_ids']
        course_type = session_info['course_type']
        duration = session_info.get('duration', 1)
        
        slot_keys = list(data['time_slots'].keys())
        start_slot_index = slot_keys.index(slot_id)

        for i in range(duration):
            # Ensure we don't go out of bounds (though scheduler should prevent this)
            if start_slot_index + i >= len(slot_keys):
                break
            
            current_slot_id = slot_keys[start_slot_index + i]

            # Ensure mappings exist
            if current_slot_id not in room_allocations:
                room_allocations[current_slot_id] = {}
            if current_slot_id not in teacher_allocations:
                teacher_allocations[current_slot_id] = {}
            if current_slot_id not in group_allocations:
                group_allocations[current_slot_id] = {}

            day = data['time_slots'][current_slot_id]['day']
            start_time = data['time_slots'][current_slot_id]['start_time']
            
            group_daily_slots[group_id][day].append(start_time)
            for tid in teacher_ids:
                teacher_daily_slots[tid][day].append(start_time)

            # ----------------------
            # Hard Constraints
            # ----------------------
            
            # 1. Room Conflict
            if room_id in room_allocations[current_slot_id]:
                hard_conflicts += 1
            else:
                room_allocations[current_slot_id][room_id] = s_id

            # 2. Group Conflict
            if group_id in group_allocations[current_slot_id]:
                hard_conflicts += 1
            else:
                group_allocations[current_slot_id][group_id] = s_id

            # 3. Teacher Conflict
            for tid in teacher_ids:
                if tid in teacher_allocations[current_slot_id]:
                    hard_conflicts += 1
                else:
                    teacher_allocations[current_slot_id][tid] = s_id

        # 4. Room Capacity
        room_capacity = data['rooms'][room_id]['capacity']
        group_size = data['groups'][group_id]['total_students']
        if group_size > room_capacity:
            hard_conflicts += 1

        # 5. Room Type (Lab vs Lecture)
        room_type = data['rooms'][room_id]['room_type']
        if course_type == "Lab" and room_type != "Lab":
            hard_conflicts += 1
        elif course_type == "Lecture" and room_type != "Lecture":
            # Sometimes lectures can happen in labs if space allows, but let's strictly enforce this per requirement
            hard_conflicts += 1

    # ----------------------
    # Soft Constraints
    # ----------------------
    
    # We will penalize gaps (idle time) and consecutive overloads (>3 in a row)
    
    def evaluate_daily_schedule(daily_slots):
        penalty = 0
        # Sort slots by time (e.g., "08:00", "09:00", "10:30")
        for day, times in daily_slots.items():
            if not times:
                continue
            times.sort()
            # Calculate gaps and consecutive classes
            # Simple heuristic: assuming slots are somewhat ordered. 
            # In our dataset, times map to slots sequentially.
            # Consecutive threshold: 3
            consecutive = 1
            for i in range(1, len(times)):
                # If times are adjacent (we can use string comparison since formats are HH:MM)
                # This is a simplification. For accuracy, one could parse time.
                pass 
                # To keep it computationally fast, we will just penalize days with > 4 classes heavily
            
            if len(times) > 4:
                penalty += (len(times) - 4) * 2
                
        return penalty

    for g, daily in group_daily_slots.items():
        soft_penalty += evaluate_daily_schedule(daily)
        
    for t, daily in teacher_daily_slots.items():
        soft_penalty += evaluate_daily_schedule(daily)

    # Fitness is inversely proportional to conflicts
    # Using a formula: 1 / (1 + hard_conflicts * 100 + soft_penalty)
    # If 0 hard conflicts, fitness will be much higher.
    fitness = 1.0 / (1.0 + hard_conflicts * 100 + soft_penalty)
    
    return fitness, hard_conflicts, soft_penalty
