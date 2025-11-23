from PyQt6.QtWidgets import (
    QMainWindow, QGraphicsScene, QGraphicsView, QVBoxLayout, QWidget, QMessageBox
)
from PyQt6.QtCore import Qt
from constants import CELL_SIZE, DEFAULT_GRID_SIZE
from .controls_builder import ControlsBuilder
from .grid_renderer import GridRenderer
from .simulation_controller import SimulationController
from .realtime_controller import RealtimeController


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Symulator voronoi z wiatrem")

        self.grid_width = DEFAULT_GRID_SIZE
        self.grid_height = DEFAULT_GRID_SIZE
        self.sensors = []
        self.wind_direction = 0
        self.wind_strength = 0
        self.variable_wind = False
        self.show_grid = True

        self.sim_controller = SimulationController(
            self.grid_width, self.grid_height, self.sensors,
            self.wind_direction, self.wind_strength
        )
        self.realtime_controller = RealtimeController(
            self.grid_width, self.grid_height, self.sensors,
            self.wind_direction, 0, 5, 0.5
        )

        self.controls_builder = ControlsBuilder()
        self.grid_renderer = GridRenderer(
            None, self.grid_width, self.grid_height
        )

        self.current_step = 0
        self.placing_mode = None

        self._init_ui()
        self._connect_signals()
        self._update_view()

    def _init_ui(self):
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setFixedSize(
            self.grid_width * CELL_SIZE + 2,
            self.grid_height * CELL_SIZE + 2
        )
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.viewport().installEventFilter(self)

        self.grid_renderer.scene = self.scene

        controls_layout = self.controls_builder.build_all()
        slider, label = self.controls_builder.build_slider_and_label()

        self.slider = slider
        self.label = label

        layout = QVBoxLayout()
        layout.addLayout(controls_layout)
        layout.addWidget(self.view)
        layout.addWidget(label)
        layout.addWidget(slider)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def _connect_signals(self):
        controls = self.controls_builder.controls

        controls['checkbox_grid'].stateChanged.connect(self._on_toggle_grid)
        controls['set_size_btn'].clicked.connect(self._on_set_grid_size)
        controls['clean_btn'].clicked.connect(lambda: self._on_set_place_mode("clean"))
        controls['polluted_btn'].clicked.connect(lambda: self._on_set_place_mode("polluted"))
        controls['auto_place_btn'].clicked.connect(self._on_auto_place)
        controls['wind_dir_combo'].currentIndexChanged.connect(self._on_wind_changed)
        controls['wind_strength_spin'].valueChanged.connect(self._on_wind_changed)
        controls['run_sim_btn'].clicked.connect(self._on_run_sim)
        controls['clear_btn'].clicked.connect(self._on_clear_all)
        controls['checkbox_var_wind'].stateChanged.connect(self._on_toggle_variable_wind)
        controls['run_realtime_btn'].clicked.connect(self._on_run_realtime)
        controls['stop_realtime_btn'].clicked.connect(self._on_stop_realtime)
        controls['slider'].valueChanged.connect(self._on_slider_changed)

    def _update_view(self):
        self.grid_renderer.draw(
            self.sim_controller.sim, self.current_step,
            self.show_grid, self.sensors
        )

    def _on_toggle_grid(self, state):
        self.show_grid = self.controls_builder.controls['checkbox_grid'].isChecked()
        self._update_view()

    def _on_set_place_mode(self, mode):
        self.placing_mode = mode

    def _on_auto_place(self):
        self.sim_controller.auto_place_sensors()
        self.sensors = self.sim_controller.sensors
        self.realtime_controller.sensors = self.sensors
        self.current_step = 0
        self.slider.setMaximum(0)
        self.slider.setValue(0)
        self._update_view()

    def _on_wind_changed(self):
        directions = [0, 45, 90, 135, 180, 225, 270, 315]
        self.wind_direction = directions[self.controls_builder.controls['wind_dir_combo'].currentIndex()]
        self.wind_strength = self.controls_builder.controls['wind_strength_spin'].value()
        self.sim_controller.update_wind(self.wind_direction, self.wind_strength)

    def _on_toggle_variable_wind(self, state):
        self.variable_wind = (state == 2)
        controls = self.controls_builder.controls
        controls['min_wind_spin'].setEnabled(self.variable_wind)
        controls['max_wind_spin'].setEnabled(self.variable_wind)
        controls['change_rate_spin'].setEnabled(self.variable_wind)
        controls['run_realtime_btn'].setEnabled(self.variable_wind)

    def _on_run_sim(self):
        self.realtime_controller.stop()
        max_step = self.sim_controller.run()
        self.slider.setMaximum(max_step)
        self.current_step = 0
        self.slider.setValue(0)
        self.controls_builder.controls['stop_realtime_btn'].setEnabled(False)
        self.controls_builder.controls['run_realtime_btn'].setEnabled(self.variable_wind)
        self._update_view()

    def _on_clear_all(self):
        self.realtime_controller.stop()
        self.sim_controller.clear_sensors()
        self.current_step = 0
        self.slider.setMaximum(0)
        self.slider.setValue(0)
        self.controls_builder.controls['run_realtime_btn'].setEnabled(self.variable_wind)
        self.controls_builder.controls['stop_realtime_btn'].setEnabled(False)
        self.controls_builder.controls['slider'].setEnabled(True)
        self.controls_builder.controls['wind_dir_combo'].setEnabled(True)
        self.controls_builder.controls['wind_strength_spin'].setEnabled(True)
        self._update_view()

    def _on_run_realtime(self):
        if not self.variable_wind:
            QMessageBox.warning(self, "Error", "Włącz tryb zmiennego wiatru!")
            return

        min_wind = self.controls_builder.controls['min_wind_spin'].value()
        max_wind = self.controls_builder.controls['max_wind_spin'].value()
        wind_change_rate = self.controls_builder.controls['change_rate_spin'].value()

        if min_wind > max_wind:
            QMessageBox.warning(self, "Error", "Min nie może być większy niż Max!")
            return

        self.realtime_controller.grid_width = self.grid_width
        self.realtime_controller.grid_height = self.grid_height
        self.realtime_controller.sensors = self.sensors
        self.realtime_controller.wind_direction = self.wind_direction
        self.realtime_controller.min_wind = min_wind
        self.realtime_controller.max_wind = max_wind
        self.realtime_controller.wind_change_rate = wind_change_rate

        if self.realtime_controller.start(self._on_realtime_step):
            self.controls_builder.controls['run_realtime_btn'].setEnabled(False)
            self.controls_builder.controls['stop_realtime_btn'].setEnabled(True)
            self.controls_builder.controls['slider'].setEnabled(False)
            self.controls_builder.controls['wind_dir_combo'].setEnabled(False)
            self.controls_builder.controls['wind_strength_spin'].setEnabled(False)

    def _on_stop_realtime(self):
        self.realtime_controller.stop()
        self.controls_builder.controls['run_realtime_btn'].setEnabled(True)
        self.controls_builder.controls['stop_realtime_btn'].setEnabled(False)
        self.controls_builder.controls['slider'].setEnabled(True)
        self.controls_builder.controls['wind_dir_combo'].setEnabled(True)
        self.controls_builder.controls['wind_strength_spin'].setEnabled(True)

    def _on_realtime_step(self, sim):
        self.current_step = len(sim.steps) - 1
        wind_str = f"{sim.wind_strength:.1f}"
        self.label.setText(f"Krok: {self.current_step} | Wiatr: {wind_str}")
        self.grid_renderer.draw(sim, self.current_step, self.show_grid, self.sensors)

    def _on_slider_changed(self, v):
        self.current_step = v
        wind_str = f"{self.sim_controller.sim.wind_strength:.1f}" if hasattr(self.sim_controller.sim, 'wind_strength') else "0"
        self.label.setText(f"Poziom: {v} | Wiatr: {wind_str}")
        self._update_view()

    def _on_set_grid_size(self):
        try:
            controls = self.controls_builder.controls
            w = int(controls['w_in'].text())
            h = int(controls['h_in'].text())
            assert 1 <= w <= 50 and 1 <= h <= 50
            self.grid_width, self.grid_height = w, h
            self.realtime_controller.stop()
            self.sim_controller.set_grid_size(w, h)
            self.sensors = self.sim_controller.sensors
            self.grid_renderer.update_dimensions(w, h)
            self.view.setFixedSize(w * CELL_SIZE + 2, h * CELL_SIZE + 2)
            self.slider.setMaximum(0)
            self.slider.setValue(0)
            self.current_step = 0
            self.controls_builder.controls['run_realtime_btn'].setEnabled(self.variable_wind)
            self.controls_builder.controls['stop_realtime_btn'].setEnabled(False)
            self.controls_builder.controls['slider'].setEnabled(True)
            self.controls_builder.controls['wind_dir_combo'].setEnabled(True)
            self.controls_builder.controls['wind_strength_spin'].setEnabled(True)
            self._update_view()
        except ValueError:
            QMessageBox.warning(self, "Error", "Liczby muszą byc od 1–50.")

    def eventFilter(self, src, ev):
        if src is self.view.viewport() and ev.type() == ev.Type.MouseButtonPress:
            x = int(ev.position().x() // CELL_SIZE)
            y = int(ev.position().y() // CELL_SIZE)
            if 0 <= x < self.grid_width and 0 <= y < self.grid_height and self.placing_mode:
                if self.sim_controller.add_sensor(x, y, self.placing_mode == "polluted"):
                    self.sensors = self.sim_controller.sensors
                    self.realtime_controller.sensors = self.sensors
                    self.current_step = 0
                    self.slider.setMaximum(0)
                    self._update_view()
            return True
        return super().eventFilter(src, ev)

    def closeEvent(self, event):
        self.realtime_controller.cleanup()
        super().closeEvent(event)
