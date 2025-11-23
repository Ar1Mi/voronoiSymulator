from simulation import SimulationManager
from models import Sensor


class SimulationController:
    def __init__(self, grid_width, grid_height, sensors, wind_direction, wind_strength):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.sensors = sensors
        self.wind_direction = wind_direction
        self.wind_strength = wind_strength
        self.sim = None
        self._create_sim()

    def _create_sim(self):
        self.sim = SimulationManager(
            self.grid_width, self.grid_height, self.sensors,
            self.wind_direction, self.wind_strength,
            variable_wind=False
        )

    def run(self):
        """Run simulation until all reachable cells are colored."""
        self._create_sim()
        self.sim.reset()
        
        # Maximum steps to prevent infinite loops
        max_steps = self.grid_width + self.grid_height + 100
        
        for step in range(max_steps):
            prev_grid = self.sim.steps[-1]
            self.sim.next_step()
            curr_grid = self.sim.steps[-1]
            
            # Check if any new cells were colored in this step
            has_changes = False
            for y in range(self.grid_height):
                for x in range(self.grid_width):
                    if prev_grid[y][x].status is None and curr_grid[y][x].status is not None:
                        has_changes = True
                        break
                if has_changes:
                    break
            
            # Stop if no new cells were colored
            if not has_changes:
                break
        
        return len(self.sim.steps) - 1

    def add_sensor(self, x, y, polluted):
        for s in self.sensors:
            if s.x == x and s.y == y:
                return False
        self.sensors.append(Sensor(x, y, polluted))
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
            if not any(s.x == x and s.y == y for s in self.sensors):
                polluted = random.choice([True, False])
                self.sensors.append(Sensor(x, y, polluted))
            attempts += 1
            
        self._create_sim()

    def clear_sensors(self):
        self.sensors.clear()
        self._create_sim()

    def set_grid_size(self, width, height):
        self.grid_width = width
        self.grid_height = height
        self.sensors.clear()
        self._create_sim()

    def update_wind(self, direction, strength):
        self.wind_direction = direction
        self.wind_strength = strength
