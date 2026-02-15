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
                # Need at least 2 sensors for multi-cycle logic
                # Handling the case where we can't run the multi-cycle logic gracefully
                # Or maybe we just run 1 cycle? The controller previously returned.
                # Let's just return empty lists or handle it.
                # If we return empty, the UI should handle it.
                self.finished.emit([], [], [], 0.0)
                return

            self.cycle_results = []
            
            # Sort sensors
            clean_order = sorted(range(n_sensors), key=lambda k: self.sensors[k].pollution_value)
            
            total_cycles = n_sensors - 1
            for i in range(1, n_sensors):
                # Calculate progress percentage
                # i goes from 1 to n_sensors-1. Total iterations = n_sensors-1.
                # Current iteration is i.
                # Progress = (i-1) / total_cycles * 100 at start, or i / total_cycles * 100 at end?
                # Let's emit at start of cycle
                current_progress = int(((i - 1) / total_cycles) * 100)
                self.progress.emit(current_progress)

                num_clean = i
                clean_indices = set(clean_order[:num_clean])
                
                for idx, s in enumerate(self.sensors):
                    s.polluted = idx not in clean_indices
                
                sim = self._create_sim()
                self._run_single_sim_cycle(sim)
                # Store final grid and step count for UI "on-the-fly" reconstruction
                self.cycle_results.append({
                    'final_grid': sim.steps[-1],
                    'step_count': len(sim.steps) - 1
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
