from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt6.QtCore import Qt
from constants import CELL_SIZE

class GridViewport(QGraphicsView):
    def __init__(self, renderer):
        self.scene = QGraphicsScene()
        super().__init__(self.scene)
        self.renderer = renderer
        self.renderer.scene = self.scene
        
        self.setRenderHint(self.renderHints().Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        # Mouse tracking is not strictly needed if we intercept events in view/viewport
        # self.setMouseTracking(True) 
        
        self._setup_style()
        
    def _setup_style(self):
        self.setStyleSheet("""
            QGraphicsView {
                border: none;
                background-color: #121212;
            }
        """)

    def fit_to_grid(self, grid_width, grid_height):
        # Calculate scene rect based on grid dimensions
        scene_width = grid_width * CELL_SIZE
        scene_height = grid_height * CELL_SIZE
        self.scene.setSceneRect(0, 0, scene_width, scene_height)
        self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def update_view(self, grid, show_grid, sensors, is_accumulated=False, show_values=False, csv_grid=None, used_csv_indices=None, max_source_pos=None, true_source_pos=None, predicted_pos=None, highlight_sensors=False):
        self.renderer.draw(
            grid, show_grid, sensors, is_accumulated=is_accumulated, show_values=show_values,
            csv_grid=csv_grid, used_csv_indices=used_csv_indices, max_source_pos=max_source_pos,
            true_source_pos=true_source_pos,
            predicted_pos=predicted_pos,
            highlight_sensors=highlight_sensors
        )

