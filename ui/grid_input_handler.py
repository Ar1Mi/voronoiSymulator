from PyQt6.QtCore import Qt, QObject, QTimer, QPoint
from constants import CELL_SIZE

class GridInputHandler(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window

    def eventFilter(self, src, ev):
        if src is self.mw.view.viewport() and ev.type() == ev.Type.MouseButtonRelease:
            # We need to map viewport coordinates to scene coordinates specifically
            # because the view might be scaled
            pos = self.mw.view.mapToScene(ev.position().toPoint())
            x = int(pos.x() // CELL_SIZE)
            y = int(pos.y() // CELL_SIZE)
            
            if 0 <= x < self.mw.grid_width and 0 <= y < self.mw.grid_height:
                if ev.button() == Qt.MouseButton.RightButton:
                    self._handle_right_click(x, y)
                    return True

                if ev.button() == Qt.MouseButton.LeftButton:
                    self._handle_left_click(x, y)
                    return True
            return True
        return False

    def _handle_right_click(self, x, y):
        found = next((s for s in self.mw.sensors if s.x == x and s.y == y), None)
        if found:
            QTimer.singleShot(0, lambda: self.mw._open_edit_dialog(found))

    def _handle_left_click(self, x, y):
        controls = self.mw.controls_builder.controls
        cycle_idx = controls['cycle_combo'].currentIndex()
        num_cycles = len(self.mw.sim_controller.cycle_results)
        
        # Check if showing accumulated results
        # if self.mw.sim_controller.cycle_results and cycle_idx >= num_cycles:
        #     pass 


        # Placing sensors
        if self.mw.placing_mode == "sensor":
            if self.mw.sim_controller.add_sensor(x, y, value=1.0):
                self.mw.sensors = self.mw.sim_controller.sensors
                self.mw.current_step = 0
                self.mw.slider.setMaximum(0)
                self.mw._handle_data_modification()
                self.mw._update_view()

        # Removing sensors
        if self.mw.placing_mode == "remove":
            if self.mw.sim_controller.remove_sensor(x, y):
                self.mw.sensors = self.mw.sim_controller.sensors
                self.mw.current_step = 0
                self.mw.slider.setMaximum(0)
                self.mw._handle_data_modification()
                self.mw._update_view()
