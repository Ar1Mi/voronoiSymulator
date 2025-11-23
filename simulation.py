import math
from models import Cell


class SimulationManager:
    def __init__(self, grid_width, grid_height, sensors, wind_direction=0, wind_strength=0,
                 variable_wind=False, min_wind=0, max_wind=5, wind_change_rate=0.5):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.sensors = sensors
        self.wind_direction = wind_direction
        self.wind_strength = wind_strength
        self.variable_wind = variable_wind
        self.min_wind = min_wind
        self.max_wind = max_wind
        self.wind_change_rate = wind_change_rate
        self.current_wind_change = wind_change_rate
        self.steps = []
        self._init_grid()

    def _init_grid(self):
        grid = [[Cell() for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        for s in self.sensors:
            grid[s.y][s.x].status = "polluted" if s.polluted else "clean"
        self.steps = [grid]

    def next_step(self):
        if self.variable_wind:
            self._update_variable_wind()

        prev = self.steps[-1]
        new = [[Cell() for _ in range(self.grid_width)] for _ in range(self.grid_height)]

        for y in range(self.grid_height):
            for x in range(self.grid_width):
                new[y][x].status = prev[y][x].status

        # Вычисляем смещение от ветра
        wind_offset_x = 0
        wind_offset_y = 0
        if self.wind_strength > 0:
            rad = math.radians(self.wind_direction)
            wind_offset_x = int(round(math.cos(rad) * self.wind_strength))
            wind_offset_y = int(round(math.sin(rad) * self.wind_strength))

        for s in self.sensors:
            s.radius += 1
            # Применяем смещение ветра к начальной точке распространения
            source_x = s.x + wind_offset_x
            source_y = s.y + wind_offset_y
            
            for dx in range(-s.radius, s.radius + 1):
                for dy in range(-s.radius, s.radius + 1):
                    if dx * dx + dy * dy > s.radius * s.radius:
                        continue
                    # Распространяем загрязнение от смещённой точки
                    nx, ny = source_x + dx, source_y + dy
                    if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                        if new[ny][nx].status is None:
                            new[ny][nx].status = "polluted" if s.polluted else "clean"

        self.steps.append(new)

    def _update_variable_wind(self):
        self.wind_strength += self.current_wind_change

        if self.wind_strength >= self.max_wind:
            self.wind_strength = self.max_wind
            self.current_wind_change = -self.wind_change_rate
        elif self.wind_strength <= self.min_wind:
            self.wind_strength = self.min_wind
            self.current_wind_change = self.wind_change_rate

    def reset(self):
        self.steps.clear()
        for s in self.sensors:
            s.radius = 0
        self.current_wind_change = self.wind_change_rate
        self._init_grid()
