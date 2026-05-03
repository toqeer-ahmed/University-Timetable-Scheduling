import sys
import os

# Add data folder to path if needed to import formatted_data
sys.path.append(os.path.join(os.path.dirname(__file__), 'data'))

try:
    from formatted_data import courses, teachers, groups, offerings, rooms, time_slots
except ImportError:
    print("Error: Could not import data from formatted_data.py")
    sys.exit(1)

def is_lab_course(course):
    """Determine if a course is a lab based on its code or name."""
    name = course['name'].lower()
    code = course['code'].lower()
    if 'lab' in name or code.endswith('l'):
        return True
    return False

def clean_and_structure_data():
    print("Step 1 & 2: Loading, Cleaning, and Structuring Data...")

    # 1. Normalize Courses
    structured_courses = {}
    for c in courses:
        # Standardize name
        c['name'] = c['name'].strip()
        c['code'] = c['code'].strip()
        c['type'] = 'Lab' if is_lab_course(c) else 'Lecture'
        structured_courses[c['course_id']] = c

    # 2. Normalize Teachers and handle multiple teachers
    structured_teachers = {}
    
    # We will map old teacher IDs to a list of new sub-teacher IDs if they are split
    teacher_id_mapping = {} 
    
    for t in teachers:
        names = [n.strip() for n in t['name'].replace('&', ',').split(',')]
        if len(names) > 1:
            sub_ids = []
            for idx, name in enumerate(names):
                new_id = f"{t['teacher_id']}_{idx+1}"
                structured_teachers[new_id] = {
                    "teacher_id": new_id,
                    "name": name,
                    "department": t['department']
                }
                sub_ids.append(new_id)
            teacher_id_mapping[t['teacher_id']] = sub_ids
        else:
            structured_teachers[t['teacher_id']] = t
            teacher_id_mapping[t['teacher_id']] = [t['teacher_id']]

    # 3. Normalize Groups
    structured_groups = {}
    for g in groups:
        structured_groups[g['group_id']] = g

    # 4. Normalize Rooms
    structured_rooms = {}
    for r in rooms:
        structured_rooms[r['room_id']] = r

    # 5. Normalize Time Slots
    structured_time_slots = {}
    for ts in time_slots:
        structured_time_slots[ts['slot_id']] = ts

    # 6. Validate Foreign Keys & Expand Offerings based on required sessions
    structured_offerings = []
    
    teacher_assigned_load = {tid: 0 for tid in structured_teachers}
    group_enrolled_courses = {gid: [] for gid in structured_groups}
    course_required_sessions = {cid: c['sessions_required'] for cid, c in structured_courses.items()}

    inconsistencies = []

    for o in offerings:
        cid = o['course_id']
        tid = o['teacher_id']
        gid = o['group_id']

        # Validation
        if cid not in structured_courses:
            inconsistencies.append(f"Offering {o['offering_id']}: Invalid course_id {cid}")
            continue
        if tid not in teacher_id_mapping:
            inconsistencies.append(f"Offering {o['offering_id']}: Invalid teacher_id {tid}")
            continue
        if gid not in structured_groups:
            inconsistencies.append(f"Offering {o['offering_id']}: Invalid group_id {gid}")
            continue

        sessions_needed = course_required_sessions[cid]
        assigned_teacher_ids = teacher_id_mapping[tid]

        # Register group enrollment
        if cid not in group_enrolled_courses[gid]:
            group_enrolled_courses[gid].append(cid)

        # Update teacher load (sessions per week)
        for sub_tid in assigned_teacher_ids:
            teacher_assigned_load[sub_tid] += sessions_needed

        # Expand offerings
        for session_index in range(1, sessions_needed + 1):
            expanded_offering = {
                "session_id": f"{o['offering_id']}_S{session_index}",
                "original_offering_id": o['offering_id'],
                "course_id": cid,
                "teacher_ids": assigned_teacher_ids, # List of teachers for this session
                "group_id": gid,
                "course_type": structured_courses[cid]['type'],
                "duration": 3 if structured_courses[cid]['type'] == 'Lab' else 1
            }
            structured_offerings.append(expanded_offering)

    if inconsistencies:
        print("Detected Inconsistencies:")
        for inc in inconsistencies:
            print(f" - {inc}")
        print("Continuing with valid records...\n")
    else:
        print("Validation Passed: No inconsistencies found.\n")

    print(f"Loaded {len(structured_courses)} courses.")
    print(f"Loaded {len(structured_teachers)} teachers (after splitting multiple teachers).")
    print(f"Loaded {len(structured_groups)} groups.")
    print(f"Loaded {len(structured_rooms)} rooms.")
    print(f"Loaded {len(structured_time_slots)} time slots.")
    print(f"Expanded to {len(structured_offerings)} individual sessions to schedule.\n")

    return {
        "courses": structured_courses,
        "teachers": structured_teachers,
        "groups": structured_groups,
        "rooms": structured_rooms,
        "time_slots": structured_time_slots,
        "sessions": structured_offerings,
        "teacher_load": teacher_assigned_load,
        "group_courses": group_enrolled_courses,
        "course_sessions": course_required_sessions
    }

if __name__ == "__main__":
    data = clean_and_structure_data()
    # Let's print a small sample
    print("Sample Session to Schedule:")
    print(data['sessions'][0])
