import math
from models import Cell
import copy

class SimulationManager:
    def __init__(self, grid_width, grid_height, sensors, wind_direction=0, wind_strength=0):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.sensors = sensors
        self.wind_direction = wind_direction
        self.wind_strength = wind_strength
        self.steps = []
        
        # Optimization: Pre-calculate geometry (Voronoi Regions)
        self.sorted_pixels = [] # List of (distance, x, y, sensor)
        self.max_distance = 0
        self.current_pixel_idx = 0
        self.current_radius = -1
        
        self._precalculate_geometry()
        self._init_grid()

    def _precalculate_geometry(self):
        """
        Pre-calculates the owner (nearest sensor) for every pixel in the grid.
        Accounts for wind by shifting effective sensor positions.
        Stores pixels sorted by distance to their owner.
        """
        # Calculate wind offset
        wind_offset_x = 0
        wind_offset_y = 0
        if self.wind_strength > 0:
            scale_factor = max(self.grid_width, self.grid_height)
            strength_pixels = (self.wind_strength / 100.0) * scale_factor
            
            # Match existing logic from previous implementation
            rad = math.radians(-self.wind_direction)
            wind_offset_x = int(round(math.cos(rad) * strength_pixels))
            wind_offset_y = int(round(math.sin(rad) * strength_pixels))
            
        # Pre-calculate effective positions for all sensors
        # Tuple: (sensor, effective_x, effective_y)
        effective_sources = []
        for s in self.sensors:
            effective_sources.append((s, s.x + wind_offset_x, s.y + wind_offset_y))
            
        # For every pixel in the grid, find the nearest sensor
        pixels = []
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                best_dist_sq = float('inf')
                best_sensor = None
                
                # Check against all sensors
                for s, sx, sy in effective_sources:
                    dx = x - sx
                    dy = y - sy
                    dist_sq = dx*dx + dy*dy
                    
                    if dist_sq < best_dist_sq:
                        best_dist_sq = dist_sq
                        best_sensor = s
                
                if best_sensor:
                    dist = math.sqrt(best_dist_sq)
                    pixels.append((dist, x, y, best_sensor))
        
        # Sort all pixels by distance (simulating the expanding timeline)
        self.sorted_pixels = sorted(pixels, key=lambda p: p[0])
        
        if self.sorted_pixels:
            self.max_distance = self.sorted_pixels[-1][0]

    def _init_grid(self):
        # Initial state (Time 0)
        self.current_grid = [[Cell() for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        self.steps = [self._copy_grid(self.current_grid)]
        
        # Reset trackers
        self.current_pixel_idx = 0
        self.current_radius = -1

    def next_step(self):
        """
        Advances the simulation by one time step (radius increment).
        Reveals pixels whose distance <= current_radius.
        """
        self.current_radius += 1
        has_new = False
        limit = len(self.sorted_pixels)
        
        # Process pixels potentially belonging to this time step
        # Note: We loop until we find a pixel with distance > current_radius
        while self.current_pixel_idx < limit:
            dist, x, y, sensor = self.sorted_pixels[self.current_pixel_idx]
            
            # Use a small epsilon or logic to handle float distances vs integer steps
            if dist > self.current_radius:
                break
                
            # Update pixel status
            cell = self.current_grid[y][x]
            if cell.status is None:
                cell.status = "polluted" if sensor.polluted else "clean"
                cell.polluted_by = sensor
                has_new = True
                
            self.current_pixel_idx += 1
            
        # Save snapshot
        self.steps.append(self._copy_grid(self.current_grid))
        
    def _copy_grid(self, grid):
         new_grid = []
         for row in grid:
             new_row = []
             for cell in row:
                 new_c = Cell()
                 new_c.status = cell.status
                 new_c.polluted_by = cell.polluted_by
                 new_row.append(new_c)
             new_grid.append(new_row)
         return new_grid
         
    def reset(self):
        self.current_pixel_idx = 0
        self.current_radius = -1
        self._init_grid()
        
    def compute_final_grid(self):
        """
        Returns the final grid state directly without stepping.
        Used for optimized Weighted Sum calculations.
        """
        grid = [[Cell() for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        
        for dist, x, y, sensor in self.sorted_pixels:
            grid[y][x].status = "polluted" if sensor.polluted else "clean"
            grid[y][x].polluted_by = sensor
            
        return grid
