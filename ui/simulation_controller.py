from PyQt6.QtCore import QObject, pyqtSignal
from simulation import SimulationManager
from models import Sensor
from .worker import SimulationWorker
import random
import json
import os
import csv


class SimulationController(QObject):
    sim_finished = pyqtSignal(list, list, list, float) # cycle_results, accumulated_grid, accumulation_details, duration
    sim_error = pyqtSignal(str)
    sim_progress = pyqtSignal(int)

    def __init__(self, grid_width, grid_height, sensors, wind_direction, wind_strength):
        super().__init__()
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.sensors = sensors
        self.wind_direction = wind_direction
        self.wind_strength = wind_strength
        self.sim = None
        self.cycle_results = []
        self.accumulated_grid = []
        self.accumulation_details = []
        self.csv_grid = None
        self.true_source_pos = None
        self._create_sim()

        self.worker = None
        
        # For on-the-fly viewing
        self._current_view_cycle_index = None

    def _create_sim(self):
        self.sim = SimulationManager(
            self.grid_width, self.grid_height, self.sensors,
            self.wind_direction, self.wind_strength
        )
        # Reset view cycle tracking when sim is recreated
        self._current_view_cycle_index = None

    def run(self):
        """Run single simulation synchronously (for debugging or simple run)."""
        self._create_sim()
        self.sim.reset()
        
        # Deterministic termination based on geometry
        import math
        target_radius = math.ceil(self.sim.max_distance)
        
        # Loop until we cover the max distance
        # We use a safety break just in case, but rely on radius comparison
        max_safety_steps = self.grid_width + self.grid_height + 1000
        
        steps_taken = 0
        while self.sim.current_radius < target_radius and steps_taken < max_safety_steps:
            self.sim.next_step()
            steps_taken += 1
        
        return len(self.sim.steps) - 1

    def run_async(self):
        """Run multi-cycle simulation in a background thread."""
        if self.worker and self.worker.isRunning():
            return

        self.worker = SimulationWorker(
            self.grid_width, self.grid_height, self.sensors,
            self.wind_direction, self.wind_strength
        )
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.error.connect(self._on_worker_error)
        self.worker.progress.connect(self._on_worker_progress)
        self.worker.start()

    def _on_worker_finished(self, cycle_results, accumulated_grid, accumulation_details, duration):
        self.cycle_results = cycle_results
        self.accumulated_grid = accumulated_grid
        if hasattr(self, 'accumulation_details'):
             self.accumulation_details = accumulation_details
        else:
             # create attribute if not exists (though init creates it)
             self.accumulation_details = accumulation_details
        
        self.sim_finished.emit(cycle_results, accumulated_grid, accumulation_details, duration)
        
        # Invalidate the view cache so that subsequent requests for cycle grids 
        # (via get_cycle_grid) force a re-creation of the simulation with updated parameters.
        self._current_view_cycle_index = None
        
        self.worker.deleteLater()
        self.worker = None

    def _on_worker_progress(self, val):
        self.sim_progress.emit(val)

    def _on_worker_error(self, msg):
        self.sim_error.emit(msg)
        self.worker.deleteLater()
        self.worker = None

    def run_multi_cycle(self):
        """Deprecated: Use run_async instead."""
        pass

        pass

    def get_cycle_grid(self, cycle_index, step_index):
        """
        Reconstruct the grid for a specific cycle and step on the fly.
        """
        if not self.sensors:
             return None
             
        # Check if we need to re-configure the simulation for this cycle
        if self._current_view_cycle_index != cycle_index:
            # Recreate sensor configuration for this cycle
            n_sensors = len(self.sensors)
            
            # Sort sensors by pollution value (must match worker logic)
            clean_order = sorted(range(n_sensors), key=lambda k: self.sensors[k].pollution_value)
            
            # cycle_index 0 -> i=1 (1 clean sensor)
            num_clean = cycle_index + 1
            clean_indices = set(clean_order[:num_clean])
            
            for idx, s in enumerate(self.sensors):
                s.polluted = idx not in clean_indices
            
            # Create fresh sim
            self._create_sim()
            self.sim.reset()
            self._current_view_cycle_index = cycle_index
            
        # Now advance self.sim to step_step_index
        # If we are ahead, we need to reset
        current_sim_step = len(self.sim.steps) - 1
        
        if step_index < current_sim_step:
            self.sim.reset()
            current_sim_step = 0
            
        while current_sim_step < step_index:
            self.sim.next_step()
            current_sim_step += 1
            
            # Safety break if simulation stopped growing but requested step is higher
            # (Though user shouldn't request higher than max which we returned)
            if len(self.sim.steps) > 1 and self.sim.steps[-1] == self.sim.steps[-2]:
                 # Converged? Usually we check is_stable inside next_step logic or loop
                 # SimulationManager just appends.
                 pass

        # Return the requested step
        # Clamp to available steps
        avail_steps = len(self.sim.steps)
        req_step = min(step_index, avail_steps - 1)
        return self.sim.steps[req_step]

    def add_sensor(self, x, y, value=1.0):
        # Auto-fill from CSV if available
        if self.csv_grid:
            csv_height = len(self.csv_grid)
            csv_width = len(self.csv_grid[0]) if csv_height > 0 else 0
            if csv_width > 0 and csv_height > 0:
                cx = int(x * csv_width / self.grid_width)
                cy = int(y * csv_height / self.grid_height)
                cx = max(0, min(cx, csv_width - 1))
                cy = max(0, min(cy, csv_height - 1))
                value = self.csv_grid[cy][cx]

        for s in self.sensors:
            if s.x == x and s.y == y:
                return False
        self.sensors.append(Sensor(x, y, value))
        self._create_sim()
        return True

    def auto_place_sensors(self, count=10):
        import random
        self.sensors.clear()
        attempts = 0
        max_attempts = count * 10  # Prevent infinite loop
        
        while len(self.sensors) < count and attempts < max_attempts:
            x = random.randint(0, self.grid_width - 1)
            y = random.randint(0, self.grid_height - 1)
            
            # Avoid duplicates
            # Avoid duplicates
            if not any(s.x == x and s.y == y for s in self.sensors):
                # Random value for variety
                val = random.uniform(0.0001, 100.0)
                self.sensors.append(Sensor(x, y, val))
            attempts += 1
            
        self._create_sim()
    
    def remove_sensor(self, x, y):
        """Remove sensor at (x, y) if it exists."""
        initial_len = len(self.sensors)
        # Filter out sensor at this location
        self.sensors = [s for s in self.sensors if not (s.x == x and s.y == y)]
        
        if len(self.sensors) < initial_len:
            self._create_sim()
            return True
        return False


    def clear_sensors(self):
        self.sensors.clear()
        self.csv_grid = None
        self.true_source_pos = None
        self._create_sim()

    def set_grid_size(self, width, height):
        self.grid_width = width
        self.grid_height = height
        self.sensors.clear()
        
        # Clear simulation results to prevent crashes due to size mismatch
        self.cycle_results = []
        self.accumulated_grid = []
        self.accumulation_details = []
        
        self._create_sim()
    
    def clear_simulation_results(self):
        """Clear simulation steps but keep sensors."""
        self.cycle_results = []
        self.accumulated_grid = []
        self.accumulation_details = []
        self.csv_grid = None
        
        if self.sim:
            self.sim.reset()


    def update_wind(self, direction, strength):
        self.wind_direction = direction
        self.wind_strength = strength

    def update_sensor_value(self, x, y, new_value):
        for s in self.sensors:
            if s.x == x and s.y == y:
                s.pollution_value = new_value
                # Assuming updating a value requires re-creating sim setup if needed
                # But run_multi_cycle will re-sort anyway.
                # However, visual feedback might be good if we visualized values (we don't yet).
                return True
        return False


    def import_csv_data(self, file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        data_grid = []
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                # Use semicolon delimiter
                reader = csv.reader(f, delimiter=';')
                rows = list(reader)
        except UnicodeDecodeError:
             # Fallback
             with open(file_path, 'r', encoding='latin-1') as f:
                reader = csv.reader(f, delimiter=';')
                rows = list(reader)


        # Parse from x=2 y=3 to x=11 y=12 (1-based from user request)
        # 1-based x=2 is index 1. 1-based x=11 is index 10.
        # 1-based y=3 is index 2. 1-based y=12 is index 11.
        start_x, end_x = 1, 10
        start_y, end_y = 2, 11
        
        # Validate CSV size
        # We need at least end_y + 1 rows (since 0-indexed)
        if len(rows) <= end_y:
            raise ValueError(f"CSV file too small: need at least {end_y + 1} rows, got {len(rows)}")
        
        for r_idx in range(start_y, end_y + 1):
            row = rows[r_idx]
            if len(row) <= end_x:
                raise ValueError(f"CSV row {r_idx} too short: need at least {end_x + 1} columns")
            
            extracted_row = []
            for c_idx in range(start_x, end_x + 1):
                try:
                    # Replace comma with dot for decimals
                    val_str = row[c_idx].replace(',', '.')
                    val = float(val_str)
                    extracted_row.append(val)
                except ValueError:
                    extracted_row.append(0.0) # Default to 0 if not a number
            data_grid.append(extracted_row)

        csv_height = len(data_grid)
        csv_width = len(data_grid[0]) if csv_height > 0 else 0
        
        if csv_width == 0 or csv_height == 0:
             raise ValueError("Extracted CSV data is empty")

        self.true_source_pos = None  # (x, y) in grid coordinates
        self.csv_grid = data_grid

        # Parse True Source from Row 0 (First 3 columns: x, y, z)
        # Values are 0-10000.
        if len(rows) > 0:
            header_row = rows[0]
            if len(header_row) >= 2:
                try:
                    # Replace comma with dot just in case
                    ts_x_str = header_row[0].replace(',', '.').strip()
                    ts_y_str = header_row[1].replace(',', '.').strip()
                    
                    if not ts_x_str or not ts_y_str:
                         print(f"Empty True Source strings: '{ts_x_str}', '{ts_y_str}'")
                         raise ValueError("Empty strings")
                    
                    ts_x = float(ts_x_str)
                    ts_y = float(ts_y_str)
                    
                    # Map 0-10000 to Grid Dimensions
                    # x_sim = (x_csv / 10000) * grid_width
                    # y_sim = (y_csv / 10000) * grid_height
                    
                    sim_x = (ts_x / 10000.0) * self.grid_width
                    sim_y = (ts_y / 10000.0) * self.grid_height
                    
                    self.true_source_pos = (sim_x, sim_y)
                    print(f"Parsed True Source: CSV({ts_x}, {ts_y}) -> SIM({sim_x}, {sim_y})")
                except ValueError as e:
                    print(f"Could not parse True Source coordinates from CSV header: {e}. Row: {header_row[:3]}")



        # Map sensors
        for s in self.sensors:
            # cx = int(sim_x * CSV_width  / Sim_width)
            # cy = int(sim_y * CSV_height / Sim_height)
            
            cx = int(s.x * csv_width / self.grid_width)
            cy = int(s.y * csv_height / self.grid_height)
            
            # Clamp to bounds just in case
            cx = max(0, min(cx, csv_width - 1))
            cy = max(0, min(cy, csv_height - 1))
            
            s.pollution_value = data_grid[cy][cx]
            
        self._create_sim()

    def save_simulation(self, file_path):
        """Save current simulation state to a JSON file."""
        data = {
            "version": 1,
            "grid": {
                "width": self.grid_width,
                "height": self.grid_height
            },
            "wind": {
                "direction": self.wind_direction,
                "strength": self.wind_strength
            },
            "sensors": [
                {
                    "x": s.x,
                    "y": s.y,
                    "pollution_value": s.pollution_value,
                    "polluted": s.polluted
                } for s in self.sensors
            ]
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def load_simulation(self, file_path):
        """Load simulation state from a JSON file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Basic validation
        if "grid" not in data or "sensors" not in data:
            raise ValueError("Invalid simulation file format")
            
        # Restore configuration
        self.grid_width = data["grid"]["width"]
        self.grid_height = data["grid"]["height"]
        
        if "wind" in data:
            self.wind_direction = data["wind"]["direction"]
            self.wind_strength = data["wind"]["strength"]
            
        # Restore sensors
        self.sensors.clear()
        for s_data in data["sensors"]:
            # Ensure sensor is within new grid bounds
            if s_data["x"] < self.grid_width and s_data["y"] < self.grid_height:
                sensor = Sensor(s_data["x"], s_data["y"], s_data["pollution_value"])
                # We trust the saved state for 'polluted' flag if we wanted to restore exact state,
                # but SimulationManager usually re-evaluates. 
                # For now let's mostly trust the position and value.
                self.sensors.append(sensor)
        
        # Reset simulation with new parameters
        self.cycle_results = []
        self.accumulated_grid = []
        self.accumulation_details = []
        self._create_sim()
        
        return {
            "grid_width": self.grid_width,
            "grid_height": self.grid_height,
            "wind_direction": self.wind_direction,
            "wind_strength": self.wind_strength,
            "sensors_count": len(self.sensors)
        }

    def get_max_pollution_source(self):
        """Find the max pollution value and its position in the CSV source data."""
        if not self.csv_grid:
            return None
        
        max_val = -1.0
        max_pos = None
        
        rows = len(self.csv_grid)
        cols = len(self.csv_grid[0]) if rows > 0 else 0
        
        for y in range(rows):
            for x in range(cols):
                val = self.csv_grid[y][x]
                if val > max_val:
                    max_val = val
                    max_pos = (x, y)
                    
        return {
            "value": max_val,
            "pos": max_pos, # (x, y) in CSV coordinates
            "grid_dims": (cols, rows)
        }

    def calculate_accuracy_metrics(self):
        """
        Calculate quantitative metrics:
        1. Classification Error (Ec): Area_predicted / Area_total
        2. Accuracy Error (Ea): Distance from Centroid_predicted to TrueSource
        3. Relevance (R): 1 if TrueSource is inside Predicted Area, 0 otherwise
        """
        if not self.sensors or not self.sim or not self.sim.steps:
            return None

        # 1. Identify Winner Sensor (Dirtiest)
        dirtiest_sensor = max(self.sensors, key=lambda s: s.pollution_value)
        
        # 2. Determine Predicted Area (Algorithm's Result)
        # We need to know which cells belong to the dirtiest sensor in the final state.
        # This mirrors the logic in calculate_dirtiest_sensor_stats but simpler.
        
        # Wind offset logic for analytical calculation
        wind_offset_x = 0
        wind_offset_y = 0
        if self.wind_strength > 0:
            import math
            scale_factor = max(self.grid_width, self.grid_height)
            strength_pixels = (self.wind_strength / 100.0) * scale_factor
            
            # Match offset in simulation.py: 0 angle = East (Right).
            # Math: 0 rad = Right.
            # Simulation.py uses: rad = math.radians(-self.wind_direction)
            rad = math.radians(-self.wind_direction)
            wind_offset_x = int(round(math.cos(rad) * strength_pixels))
            wind_offset_y = int(round(math.sin(rad) * strength_pixels))

        # Pre-calculate sensor effective positions
        sensor_positions = []
        for s in self.sensors:
            # User requested shift in opposite direction (Downwind match).
            eff_x = s.x + wind_offset_x
            eff_y = s.y + wind_offset_y
            sensor_positions.append((s, eff_x, eff_y))

        predicted_cells = []
        centroid_x_sum = 0
        centroid_y_sum = 0
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                best_dist = float('inf')
                best_s = None
                
                for s, sx, sy in sensor_positions:
                    dx = x - sx
                    dy = y - sy
                    dist_sq = dx*dx + dy*dy
                    
                    if dist_sq < best_dist:
                        best_dist = dist_sq
                        best_s = s
                
                if best_s == dirtiest_sensor:
                    predicted_cells.append((x, y))
                    centroid_x_sum += x
                    centroid_y_sum += y

        count_predicted = len(predicted_cells)
        total_cells = self.grid_width * self.grid_height
        
        # Metric 1: Classification Error
        ec = 0.0
        if total_cells > 0:
            ec = count_predicted / total_cells
            
        # Metric 2 & 3 need True Source
        # Metric 2 & 3 need True Source
        ea = None
        es = None  # Error of Search
        relevance = 0
        cx, cy = 0, 0

        # Calculate Centroid of Predicted Area (Independent of True Source)
        if count_predicted > 0:
            cx = centroid_x_sum / count_predicted
            cy = centroid_y_sum / count_predicted

        if self.true_source_pos:
            tx, ty = self.true_source_pos
            
            # Metric 3: Relevance (Is True Source inside?)
            # We check if the integer grid cell of true source is in predicted_cells
            # Simple flooring of float position
            tx_int, ty_int = int(tx), int(ty)
            
            if (tx_int, ty_int) in predicted_cells:
                relevance = 1
            else:
                # Edge case: checking 4 neighbors if it hits exactly on border?
                # For simplicity, strict containment of integer cell.
                relevance = 0
                
            # Metric 2: Accuracy Error (Distance to Centroid)
            if count_predicted > 0:
                dx = cx - tx
                dy = cy - ty
                import math
                ea = math.sqrt(dx*dx + dy*dy)
            else:
                 # If no area predicted, error is undefined or max diagonal?
                 # Let's return None or a large number.
                 ea = None

            # Metric 4: Error of Search (Es)
            # Find which sensor covers the true source
            # We need to re-evaluate which sensor claims (tx, ty)
            # We already have sensor_positions adjusted for wind
            
            best_dist_source = float('inf')
            true_source_sensor = None
            
            for s, sx, sy in sensor_positions:
                dx = tx_int - sx
                dy = ty_int - sy
                dist_sq = dx*dx + dy*dy
                
                if dist_sq < best_dist_source:
                    best_dist_source = dist_sq
                    true_source_sensor = s
            
            if true_source_sensor:
                # Rank sensors by pollution value (Descending)
                # This matches the "Dirtiest" logic
                sorted_sensors = sorted(self.sensors, key=lambda s: s.pollution_value, reverse=True)
                
                # Find rank of true_source_sensor (0-based index)
                try:
                    rank_idx = sorted_sensors.index(true_source_sensor)
                    # We need sum of areas of sensors from index 0 to rank_idx (inclusive)
                    
                    # To calculate areas efficiently without full grid iteration for each sensor:
                    # We can iterate grid ONCE and count areas for all sensors.
                    sensor_areas = {s: 0 for s in self.sensors}
                    
                    for y in range(self.grid_height):
                        for x in range(self.grid_width):
                            best_dist = float('inf')
                            best_s_cell = None
                            
                            for s, sx, sy in sensor_positions:
                                dx = x - sx
                                dy = y - sy
                                dist_sq = dx*dx + dy*dy
                                
                                if dist_sq < best_dist:
                                    best_dist = dist_sq
                                    best_s_cell = s
                            
                            if best_s_cell:
                                sensor_areas[best_s_cell] += 1
                                
                    # Sum areas of top k+1 sensors
                    cumulative_area = 0
                    for i in range(rank_idx + 1):
                        s_top = sorted_sensors[i]
                        cumulative_area += sensor_areas.get(s_top, 0)
                        
                    if total_cells > 0:
                        es = cumulative_area / total_cells
                        
                except ValueError:
                    # Should not happen if sensor is in list
                    es = None
            else:
                 es = None


        return {
            "ec": ec,
            "ea": ea,
            "es": es,
            "source_rank": rank_idx + 1 if 'rank_idx' in locals() else None,
            "relevance": relevance,
            "dirtiest_sensor_val": dirtiest_sensor.pollution_value,
            "centroid": (cx, cy) if count_predicted > 0 else None
        }

