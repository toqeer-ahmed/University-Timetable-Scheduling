import random
from constraints import calculate_fitness

class GeneticAlgorithmScheduler:
    def __init__(self, data, population_size=50, mutation_rate=0.1, elitism=0.1):
        self.data = data
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.elitism = int(population_size * elitism)
        
        # Precompute valid rooms for each session to reduce hard conflicts from the start
        self.valid_rooms_per_session = {}
        for session in self.data['sessions']:
            s_id = session['session_id']
            group_id = session['group_id']
            group_size = self.data['groups'][group_id]['total_students']
            course_type = session['course_type']
            
            valid_rooms = []
            for r_id, room in self.data['rooms'].items():
                if room['capacity'] >= group_size and room['room_type'] == course_type:
                    valid_rooms.append(r_id)
                    
            # Fallback if no perfect room is found (shouldn't happen with valid dataset, but safe to have)
            if not valid_rooms:
                print(f"Warning: No perfect room found for session {s_id}. Relaxing constraints for pre-computation.")
                valid_rooms = list(self.data['rooms'].keys())
                
            self.valid_rooms_per_session[s_id] = valid_rooms

        self.time_slot_ids = list(self.data['time_slots'].keys())
        self.valid_slots_per_session = {}
        for session in self.data['sessions']:
            self.valid_slots_per_session[session['session_id']] = self._get_valid_start_slots(session['duration'])

    def _get_valid_start_slots(self, duration):
        valid_slots = []
        slot_keys = self.time_slot_ids
        for i in range(len(slot_keys) - duration + 1):
            valid = True
            day = self.data['time_slots'][slot_keys[i]]['day']
            for j in range(1, duration):
                if self.data['time_slots'][slot_keys[i+j]]['day'] != day:
                    valid = False
                    break
            if valid:
                valid_slots.append(slot_keys[i])
        
        # Fallback if no valid consecutive slots exist (e.g. data anomaly)
        if not valid_slots:
            valid_slots = slot_keys
            
        return valid_slots

    def _create_random_schedule(self):
        schedule = {}
        for session in self.data['sessions']:
            s_id = session['session_id']
            # Pick a valid room
            room_id = random.choice(self.valid_rooms_per_session[s_id])
            # Pick a random time slot valid for the duration
            slot_id = random.choice(self.valid_slots_per_session[s_id])
            
            schedule[s_id] = {
                "room_id": room_id,
                "slot_id": slot_id
            }
        return schedule

    def _initialize_population(self):
        return [self._create_random_schedule() for _ in range(self.population_size)]

    def _crossover(self, parent1, parent2):
        child = {}
        for s_id in parent1.keys():
            # 50% chance from either parent
            if random.random() > 0.5:
                child[s_id] = parent1[s_id].copy()
            else:
                child[s_id] = parent2[s_id].copy()
        return child

    def _mutate(self, schedule):
        for s_id in schedule.keys():
            if random.random() < self.mutation_rate:
                # Mutate either room or slot
                if random.random() > 0.5:
                    schedule[s_id]['room_id'] = random.choice(self.valid_rooms_per_session[s_id])
                else:
                    schedule[s_id]['slot_id'] = random.choice(self.valid_slots_per_session[s_id])
        return schedule

    def _tournament_selection(self, population_with_fitness, tournament_size=3):
        tournament = random.sample(population_with_fitness, tournament_size)
        # Select best from tournament
        best = max(tournament, key=lambda item: item[1])
        return best[0]

    def run(self, max_generations=1000):
        print("Initializing population...")
        population = self._initialize_population()
        
        best_schedule = None
        best_fitness = -1
        best_hard_conflicts = float('inf')

        for generation in range(max_generations):
            # Calculate fitness for all
            pop_fitness = []
            for ind in population:
                fit, hc, sp = calculate_fitness(ind, self.data)
                pop_fitness.append((ind, fit, hc, sp))
                
                # Update overall best
                if fit > best_fitness:
                    best_fitness = fit
                    best_schedule = ind
                    best_hard_conflicts = hc

            # Sort population by fitness descending
            pop_fitness.sort(key=lambda x: x[1], reverse=True)
            
            if generation % 10 == 0:
                best_gen_hc = pop_fitness[0][2]
                print(f"Generation {generation}: Best Fitness = {pop_fitness[0][1]:.6f} | Hard Conflicts = {best_gen_hc}")
            
            # Check stopping condition
            if best_hard_conflicts == 0:
                print(f"\nSolution found at generation {generation} with 0 Hard Conflicts!")
                break

            # Next generation
            new_population = []
            
            # Elitism
            for i in range(self.elitism):
                new_population.append(pop_fitness[i][0])
                
            # Breed the rest
            while len(new_population) < self.population_size:
                parent1 = self._tournament_selection(pop_fitness)
                parent2 = self._tournament_selection(pop_fitness)
                
                child = self._crossover(parent1, parent2)
                child = self._mutate(child)
                new_population.append(child)
                
            population = new_population

        return best_schedule, best_fitness, best_hard_conflicts
