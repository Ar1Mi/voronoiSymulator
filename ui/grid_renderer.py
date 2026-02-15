from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsSimpleTextItem
from PyQt6.QtGui import QColor, QBrush, QPen, QFont
from PyQt6.QtCore import Qt
from constants import CELL_SIZE


class GridRenderer:
    def __init__(self, scene, grid_width, grid_height):
        self.scene = scene
        self.grid_width = grid_width
        self.grid_height = grid_height

    def draw(self, grid_data, show_grid, sensors, is_accumulated=False, show_values=False, csv_grid=None, used_csv_indices=None, max_source_pos=None, true_source_pos=None, predicted_pos=None):
        self.scene.clear()
        if is_accumulated:
            self._draw_accumulated(grid_data)
        else:
            self._draw_cells(grid_data)
        
        if csv_grid:
            self._draw_data_coverage(csv_grid, used_csv_indices, max_source_pos)
            
        if true_source_pos:
            self._draw_true_source(true_source_pos)
            if predicted_pos:
                self._draw_error_vector(true_source_pos, predicted_pos)

        
        self._draw_sensors(sensors, show_values)
        if show_grid:
            self._draw_grid_lines()

    def _draw_cells(self, grid):
        # Dark theme colors
        empty_color = QColor("#222222")
        polluted_color = QColor("#d32f2f")  # Darker red
        clean_color = QColor("#388e3c")     # Darker green

        if grid:
            for y in range(self.grid_height):
                for x in range(self.grid_width):
                    st = grid[y][x].status
                    col = empty_color if st is None else (polluted_color if st == "polluted" else clean_color)
                    r = QGraphicsRectItem(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    r.setBrush(QBrush(col))
                    r.setPen(QPen(Qt.PenStyle.NoPen))
                    self.scene.addItem(r)
        else:
            for y in range(self.grid_height):
                for x in range(self.grid_width):
                    r = QGraphicsRectItem(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    r.setBrush(QBrush(empty_color))
                    r.setPen(QPen(Qt.PenStyle.NoPen))
                    self.scene.addItem(r)

    def _draw_accumulated(self, grid):
        import math
        
        # Find min (>0) and max values for normalization
        max_val = 0
        min_val = float('inf')
        has_positive = False
        
        for row in grid:
            for val in row:
                if val > 0:
                    max_val = max(max_val, val)
                    min_val = min(min_val, val)
                    has_positive = True
        
        # If no positive values, just draw white
        if not has_positive:
            min_val = 0
        
        # Gradient Colors
        # Start: Light Yellow (255, 255, 224)
        start_r, start_g, start_b = 255, 255, 224
        # End: Dark Red (139, 0, 0)
        end_r, end_g, end_b = 139, 0, 0
        
        # Pre-calculate log values if possible
        log_min = 0
        log_max = 0
        if has_positive and max_val > 0:
            log_min = math.log10(min_val)
            log_max = math.log10(max_val)
        
        log_range = log_max - log_min
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                val = grid[y][x]
                if val <= 0:
                    col = QColor("#FFFFFF")
                else:
                    # Logarithmic scaling
                    if log_range == 0:
                        ratio = 1.0 # If all values are the same and > 0
                    else:
                        log_val = math.log10(val)
                        ratio = (log_val - log_min) / log_range
                    
                    ratio = max(0, min(1, ratio))
                    
                    # Linear interpolation
                    r_val = int(start_r + (end_r - start_r) * ratio)
                    g_val = int(start_g + (end_g - start_g) * ratio)
                    b_val = int(start_b + (end_b - start_b) * ratio)
                    
                    col = QColor(r_val, g_val, b_val)
                
                r = QGraphicsRectItem(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                r.setBrush(QBrush(col))
                r.setPen(QPen(Qt.PenStyle.NoPen))
                self.scene.addItem(r)

    def _draw_sensors(self, sensors, show_values=False):
        if not sensors:
            return

        # Find max pollution value to highlight the sensor
        max_pollution = -1
        for s in sensors:
            if s.pollution_value > max_pollution:
                max_pollution = s.pollution_value
        
        for s in sensors:
            cx = s.x * CELL_SIZE + CELL_SIZE / 2
            cy = s.y * CELL_SIZE + CELL_SIZE / 2
            rad = CELL_SIZE / 6
            
            # Highlight the sensor with max pollution
            if s.pollution_value == max_pollution and max_pollution > 0:
                # Max pollution sensor: Red with thicker border
                brush_color = QColor("#ff1744") # Bright Red / Pinkish
                pen = QPen(QColor("#FFFFFF"))
                pen.setWidth(2)
            else:
                # Normal sensor: Cyan
                brush_color = QColor("#00e5ff")
                pen = QPen(QColor("#000000"))
                pen.setWidth(1)

            self.scene.addEllipse(cx - rad, cy - rad, rad * 2, rad * 2,
                                  pen, QBrush(brush_color))

            # Draw value badge if enabled
            if show_values:
                # Format value
                val_str = f"{s.pollution_value:g}"
                
                text_item = QGraphicsSimpleTextItem(val_str)
                font = QFont("Arial")
                # Font size logic: make it legible relative to cell size
                # 0.4 * CELL_SIZE seems reasonable
                font.setPixelSize(max(1, int(CELL_SIZE * 1.0)))
                text_item.setFont(font)
                
                # Center text
                rect = text_item.boundingRect()
                text_w = rect.width()
                text_h = rect.height()
                
                # Position above the sensor
                # cx, cy is center of cell
                t_x = cx - text_w / 2
                t_y = cy - rad - text_h - 2 # slightly above
                
                text_item.setPos(t_x, t_y)
                text_item.setBrush(QBrush(QColor("#ffffff"))) # White text
                
                # Background Badge
                bg_rect = QGraphicsRectItem(t_x - 2, t_y - 1, text_w + 4, text_h + 2)
                bg_rect.setBrush(QBrush(QColor(0, 0, 0, 180))) # Semi-transparent black
                bg_rect.setPen(QPen(Qt.PenStyle.NoPen))
                
                self.scene.addItem(bg_rect)
                self.scene.addItem(text_item)

    def _draw_grid_lines(self):
        pen = QPen(QColor("#444444"))
        for y in range(self.grid_height + 1):
            self.scene.addLine(0, y * CELL_SIZE,
                               self.grid_width * CELL_SIZE, y * CELL_SIZE, pen)
        for x in range(self.grid_width + 1):
            self.scene.addLine(x * CELL_SIZE, 0,
                               x * CELL_SIZE, self.grid_height * CELL_SIZE, pen)

    def _draw_data_coverage(self, csv_grid, used_indices, max_source_pos=None):
        if not csv_grid:
            return
            
        csv_height = len(csv_grid)
        csv_width = len(csv_grid[0]) if csv_height > 0 else 0
        if csv_width == 0 or csv_height == 0:
            return

        # Calculate logical cell dimensions for the CSV grid overlay
        # Entire grid logical size in pixels:
        total_w = self.grid_width * CELL_SIZE
        total_h = self.grid_height * CELL_SIZE
        
        w_step = total_w / csv_width
        h_step = total_h / csv_height
        
        for y in range(csv_height):
            for x in range(csv_width):
                # Check usage
                is_used = (used_indices and (x, y) in used_indices)
                is_max = (max_source_pos and (x, y) == max_source_pos)
                
                # Colors
                if is_used:
                     # Greenish transparent
                     col = QColor(0, 255, 0, 80)
                     border_col = QColor(0, 255, 0, 200)
                else:
                     # Reddish transparent
                     col = QColor(255, 0, 0, 80)
                     border_col = QColor(255, 0, 0, 200)

                # Special Highlight for True Max
                border_width = 2
                if is_max:
                     # Gold/Yellow border, thicker
                     border_col = QColor("#FFD700")
                     border_width = 4
                     # Maybe slightly different fill?
                     col = QColor(255, 215, 0, 80)

                # Draw rect
                r = QGraphicsRectItem(x * w_step, y * h_step, w_step, h_step)
                r.setBrush(QBrush(col))
                r.setPen(QPen(border_col, border_width))
                self.scene.addItem(r)
                
                # Draw value
                val = csv_grid[y][x]
                val_str = f"{val:g}"
                
                text_item = QGraphicsSimpleTextItem(val_str)
                font = QFont("Arial")
                # Scale font to fit in the overlay cell
                # Rough estimate: 20% of smallest dimension
                font_size = max(1, int(min(w_step, h_step) * 0.2))
                font.setPixelSize(font_size)
                # Make it bold
                font.setBold(True)
                text_item.setFont(font)
                
                # Center text
                rect = text_item.boundingRect()
                t_x = (x * w_step) + (w_step - rect.width()) / 2
                t_y = (y * h_step) + (h_step - rect.height()) / 2
                
                text_item.setPos(t_x, t_y)
                text_item.setBrush(QBrush(QColor("#ffffff")))
                 # Add shadow effect (simple duplication)? Or just assume it's visible. 
                 # Let's add a small background or stroke if needed? 
                 # Given the bg is semi-transparent, white text should be okay-ish.
                self.scene.addItem(text_item)
                
    def _draw_true_source(self, pos):
        """Draw a marker at the true source position (x, y) in grid coordinates (float)."""
        tx, ty = pos
        
        # Calculate pixel position
        px = tx * CELL_SIZE
        py = ty * CELL_SIZE
        
        # Draw a yellow 'X' or Star
        # Size similar to sensor radius
        size = CELL_SIZE * 0.8
        
        pen = QPen(QColor("#FFD700")) # Gold
        pen.setWidth(3)
        
        # Line 1: \
        self.scene.addLine(px - size/2, py - size/2, px + size/2, py + size/2, pen)
        # Line 2: /
        self.scene.addLine(px - size/2, py + size/2, px + size/2, py - size/2, pen)

    def _draw_error_vector(self, start_pos, end_pos):
        """Draw an arrow from start_pos (True Source) to end_pos (Predicted Centroid)."""
        sx, sy = start_pos
        ex, ey = end_pos
        
        # Convert to pixels
        px_start = sx * CELL_SIZE
        py_start = sy * CELL_SIZE
        px_end = ex * CELL_SIZE
        py_end = ey * CELL_SIZE
        
        pen = QPen(QColor("#FF4081")) # Pinkish/Magenta accent
        pen.setWidth(2)
        pen.setStyle(Qt.PenStyle.DashLine)
        
        # Draw Line
        from PyQt6.QtCore import QLineF
        line = QLineF(px_start, py_start, px_end, py_end)
        self.scene.addLine(line, pen)
        
        # Draw Arrowhead
        # Calculate angle
        angle = line.angle() # Returns degrees 0-360
        
        import math
        # QLineF angle 0 is East, 90 is North (inverted Y).
        # We need standard trig to draw arrow manually or use rotation
        
        arrow_size = 10
        # Arrowhead points back from end
        
        # Simple cross at end? Arrow is better.
        # Arrow head at px_end, py_end
        
        # Create a polygon for arrow head
        from PyQt6.QtWidgets import QGraphicsPolygonItem
        from PyQt6.QtGui import QPolygonF
        from PyQt6.QtCore import QPointF
        
        head = QPolygonF()
        head.append(QPointF(px_end, py_end))
        
        # Back angles
        rad = math.radians(angle)
        # QLineF angle: 0 is right. Increases counter-clockwise (math standard).
        # Scene Y is down. QLineF might handle this ? 
        # Actually simplest is just simple trig with atan2
        
        dx = px_end - px_start
        dy = py_end - py_start
        angle_rad = math.atan2(dy, dx) # y grows down, so this is correct for visual
        
        # Arrow wings
        wing_angle = math.radians(30)
        
        x1 = px_end - arrow_size * math.cos(angle_rad - wing_angle)
        y1 = py_end - arrow_size * math.sin(angle_rad - wing_angle)
        
        x2 = px_end - arrow_size * math.cos(angle_rad + wing_angle)
        y2 = py_end - arrow_size * math.sin(angle_rad + wing_angle)
        
        head.append(QPointF(x1, y1))
        head.append(QPointF(x2, y2))
        
        poly_item = QGraphicsPolygonItem(head)
        poly_item.setBrush(QBrush(QColor("#FF4081")))
        poly_item.setPen(QPen(Qt.PenStyle.NoPen))
        self.scene.addItem(poly_item)


    def update_dimensions(self, grid_width, grid_height):
        self.grid_width = grid_width
        self.grid_height = grid_height
