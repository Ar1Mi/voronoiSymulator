from PyQt6.QtWidgets import QGraphicsRectItem
from PyQt6.QtGui import QColor, QBrush, QPen
from PyQt6.QtCore import Qt
from constants import CELL_SIZE


class GridRenderer:
    def __init__(self, scene, grid_width, grid_height):
        self.scene = scene
        self.grid_width = grid_width
        self.grid_height = grid_height

    def draw(self, sim, current_step, show_grid, sensors):
        self.scene.clear()
        self._draw_cells(sim, current_step)
        self._draw_sensors(sensors)
        if show_grid:
            self._draw_grid_lines()

    def _draw_cells(self, sim, current_step):
        if sim.steps:
            grid = sim.steps[current_step]
            for y in range(self.grid_height):
                for x in range(self.grid_width):
                    st = grid[y][x].status
                    col = QColor("lightgray") if st is None else QColor("red" if st == "polluted" else "green")
                    r = QGraphicsRectItem(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    r.setBrush(QBrush(col))
                    r.setPen(QPen(Qt.PenStyle.NoPen))
                    self.scene.addItem(r)
        else:
            for y in range(self.grid_height):
                for x in range(self.grid_width):
                    r = QGraphicsRectItem(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    r.setBrush(QBrush(QColor("lightgray")))
                    r.setPen(QPen(Qt.PenStyle.NoPen))
                    self.scene.addItem(r)

    def _draw_sensors(self, sensors):
        for s in sensors:
            cx = s.x * CELL_SIZE + CELL_SIZE / 2
            cy = s.y * CELL_SIZE + CELL_SIZE / 2
            rad = CELL_SIZE / 6
            self.scene.addEllipse(cx - rad, cy - rad, rad * 2, rad * 2,
                                  QPen(Qt.PenStyle.NoPen), QBrush(QColor("black")))

    def _draw_grid_lines(self):
        pen = QPen(QColor("black"))
        for y in range(self.grid_height + 1):
            self.scene.addLine(0, y * CELL_SIZE,
                               self.grid_width * CELL_SIZE, y * CELL_SIZE, pen)
        for x in range(self.grid_width + 1):
            self.scene.addLine(x * CELL_SIZE, 0,
                               x * CELL_SIZE, self.grid_height * CELL_SIZE, pen)

    def update_dimensions(self, grid_width, grid_height):
        self.grid_width = grid_width
        self.grid_height = grid_height
