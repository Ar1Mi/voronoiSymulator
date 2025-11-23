from PyQt6.QtCore import QTimer
from simulation import SimulationManager


class RealtimeController:
    def __init__(self, grid_width, grid_height, sensors, wind_direction,
                 min_wind, max_wind, wind_change_rate):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.sensors = sensors
        self.wind_direction = wind_direction
        self.min_wind = min_wind
        self.max_wind = max_wind
        self.wind_change_rate = wind_change_rate
        self.sim = None
        self.timer = QTimer()
        self.is_running = False
        self.step_callback = None

    def start(self, step_callback):
        if self.min_wind > self.max_wind:
            return False

        self.step_callback = step_callback
        self.sim = SimulationManager(
            self.grid_width, self.grid_height, self.sensors,
            self.wind_direction, self.min_wind,
            variable_wind=True, min_wind=self.min_wind,
            max_wind=self.max_wind, wind_change_rate=self.wind_change_rate
        )
        self.sim.reset()

        self.timer.timeout.connect(self._on_step)
        self.timer.start(200)
        self.is_running = True
        return True

    def stop(self):
        self.timer.stop()
        self.is_running = False

    def _on_step(self):
        if self.sim:
            self.sim.next_step()
            if self.step_callback:
                self.step_callback(self.sim)

    def cleanup(self):
        self.stop()
