import math
from models import Cell


class SimulationManager:
    def __init__(self, grid_width, grid_height, sensors, wind_direction=0, wind_strength=0):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.sensors = sensors
        self.wind_direction = wind_direction
        self.wind_strength = wind_strength
        self.steps = []
        self._init_grid()

    def _init_grid(self):
        grid = [[Cell() for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        for s in self.sensors:
            grid[s.y][s.x].status = "polluted" if s.polluted else "clean"
            # Set polluted_by for both polluted and clean cells to track source
            grid[s.y][s.x].polluted_by = s
        self.steps = [grid]

    def next_step(self):
        prev = self.steps[-1]
        new = [[Cell() for _ in range(self.grid_width)] for _ in range(self.grid_height)]

        for y in range(self.grid_height):
            for x in range(self.grid_width):
                new[y][x].status = prev[y][x].status
                new[y][x].polluted_by = prev[y][x].polluted_by

        # Вычисляем смещение от ветра
        wind_offset_x = 0
        wind_offset_y = 0
        if self.wind_strength > 0:
            scale_factor = max(self.grid_width, self.grid_height)
            strength_pixels = (self.wind_strength / 100.0) * scale_factor
            
            # User Interface Dial: 0 = East (Right), counter-clockwise = increasing angle.
            # To match dial direction, negate the angle for screen coordinates.
            # Math Coordinates (Screen): Y-axis is inverted, so we negate the angle.
            rad = math.radians(-self.wind_direction)
            wind_offset_x = int(round(math.cos(rad) * strength_pixels))
            wind_offset_y = int(round(math.sin(rad) * strength_pixels))

        # Dictionary to track candidates for this step: (x, y) -> (dist_sq, sensor)
        candidates = {}

        # 1. Identify all potential claims for this step
        for s in self.sensors:
            s.radius += 1
            # Apply wind offset
            source_x = s.x + wind_offset_x
            source_y = s.y + wind_offset_y
            
            for dx in range(-s.radius, s.radius + 1):
                for dy in range(-s.radius, s.radius + 1):
                    # Check strictly inside current radius
                    dist_sq = dx * dx + dy * dy
                    if dist_sq > s.radius * s.radius:
                        continue
                    
                    nx, ny = source_x + dx, source_y + dy
                    
                    if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                        # Only consider if not already filled in previous step
                        if prev[ny][nx].status is None:
                            # Calculate exact distance from source (not just dx,dy which are relative to displaced source)
                            # Actually dx, dy are correct relative distance from the "effective source" 
                            # which is what determines the circle.
                            
                            # If this cell is already a candidate, compare distances
                            if (nx, ny) in candidates:
                                existing_dist, existing_s = candidates[(nx, ny)]
                                if dist_sq < existing_dist:
                                    candidates[(nx, ny)] = (dist_sq, s)
                            else:
                                candidates[(nx, ny)] = (dist_sq, s)

        # 2. Apply the best candidates
        for (cx, cy), (dist, s) in candidates.items():
            new[cy][cx].status = "polluted" if s.polluted else "clean"
            new[cy][cx].polluted_by = s

        self.steps.append(new)

    def reset(self):
        self.steps.clear()
        for s in self.sensors:
            s.radius = 0
        self._init_grid()
