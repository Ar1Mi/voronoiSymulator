from PyQt6.QtCore import QThread, pyqtSignal
from simulation import SimulationManager
import copy
import time

class SimulationWorker(QThread):
    finished = pyqtSignal(list, list, list, float) # cycle_results, accumulated_grid, accumulation_details, duration
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, grid_width, grid_height, sensors, wind_direction, wind_strength):
        super().__init__()
        self.grid_width = grid_width
        self.grid_height = grid_height
        # Deepcopy sensors to avoid threading issues
        self.sensors = copy.deepcopy(sensors)
        self.wind_direction = wind_direction
        self.wind_strength = wind_strength
        self.cycle_results = []
        self.accumulated_grid = []
        self.accumulation_details = []

    def _create_sim(self):
        return SimulationManager(
            self.grid_width, self.grid_height, self.sensors,
            self.wind_direction, self.wind_strength
        )

    def _run_single_sim_cycle(self, sim):
        """Run one full simulation cycle until stable."""
        sim.reset()
        max_steps = self.grid_width + self.grid_height + 100
        
        for _ in range(max_steps):
            prev_grid = sim.steps[-1]
            sim.next_step()
            curr_grid = sim.steps[-1]
            
            has_changes = False
            for y in range(self.grid_height):
                for x in range(self.grid_width):
                    if prev_grid[y][x].status is None and curr_grid[y][x].status is not None:
                        has_changes = True
                        break
                if has_changes:
                    break
            
            if not has_changes:
                sim.steps.pop()
                break

    def run(self):
        try:
            start_time = time.time()
            n_sensors = len(self.sensors)
            if n_sensors < 2:
                self.finished.emit([], [], [], 0.0)
                return

            self.cycle_results = []
            
            # Sort sensors
            clean_order = sorted(range(n_sensors), key=lambda k: self.sensors[k].pollution_value)
            
            # Create SimulationManager ONCE (Pre-calculates geometry)
            # This is the heavy lifting, done only once.
            base_sim = self._create_sim()
            
            total_cycles = n_sensors - 1
            for i in range(1, n_sensors):
                current_progress = int(((i - 1) / total_cycles) * 100)
                self.progress.emit(current_progress)

                num_clean = i
                clean_indices = set(clean_order[:num_clean])
                
                # Update sensor statuses in the single sim instance
                for idx, s in enumerate(base_sim.sensors):
                    s.polluted = idx not in clean_indices
                
                # OPTIMIZATION:
                # Instead of running step-by-step, we just ask for the final grid
                # based on the pre-calculated Voronoi map.
                final_grid = base_sim.compute_final_grid()
                
                # We store only the final grid. Step count is effectively max_distance or just ignored.
                # If UI needs to see animation of "weighted sum cycles", it can't anymore
                # but usually weighted sum is just a calculation result.
                # If we need steps for UI, we could generate them, but that defeats optimization.
                # Assuming 'cycle_results' is mainly for the 'Cycle View' slider which shows FINAL state of each cycle.
                
                import math
                self.cycle_results.append({
                    'final_grid': final_grid,
                    'step_count': math.ceil(base_sim.max_distance) + 1 # Include +1 for radius coverage
                })

            self._calculate_accumulation()
            self.progress.emit(100)
            
            end_time = time.time()
            duration = end_time - start_time
            
            self.finished.emit(self.cycle_results, self.accumulated_grid, self.accumulation_details, duration)

        except Exception as e:
            self.error.emit(str(e))

    def _calculate_accumulation(self):
        self.accumulated_grid = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        self.accumulation_details = [[[] for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        
        for i, res in enumerate(self.cycle_results):
            final_grid = res['final_grid']
            if not final_grid: continue
            for y in range(self.grid_height):
                for x in range(self.grid_width):
                    cell = final_grid[y][x]
                    if (cell.status == "polluted" or cell.status == "clean") and cell.polluted_by:
                        # Note: cell.polluted_by is a Sensor object. 
                        # We need to make sure we access the correct pollution value.
                        # Since we deepcopied sensors, these are the worker's sensor objects.
                         pollution_val = cell.polluted_by.pollution_value if cell.status == "polluted" else 0.0
                         self.accumulated_grid[y][x] += pollution_val
                         
                         self.accumulation_details[y][x].append({
                            'cycle': i + 1,
                            'sensor_pos': (cell.polluted_by.x, cell.polluted_by.y),
                            'pollution_value': pollution_val
                         })
