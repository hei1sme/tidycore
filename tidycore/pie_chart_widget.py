# tidycore/pie_chart_widget.py
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QBrush, QPen
from PySide6.QtCore import Qt, QRectF

class PieChartWidget(QWidget):
    """A custom widget that draws a clean pie/donut chart using QPainter."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = {}
        self.chart_colors = [
            QColor("#7aa2f7"), QColor("#ff79c6"), QColor("#9ece6a"),
            QColor("#e0af68"), QColor("#bb9af7"), QColor("#7dcfff")
        ]
        self.setMinimumSize(150, 150)

    def set_data(self, data: dict):
        """Sets the data for the chart and triggers a repaint."""
        self._data = data
        self.update()

    def paintEvent(self, event):
        """Handles the painting of the widget."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        side = min(self.width(), self.height())
        padding = 5 
        rect = QRectF(padding, padding, side - 2*padding, side - 2*padding)

        if not self._data or sum(self._data.values()) == 0:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#3b3f51")))
            painter.drawEllipse(rect)
            return

        total = sum(self._data.values())
        
        pen = QPen(QColor("#1a1b26"), 3)
        pen.setCosmetic(True)
        painter.setPen(pen)

        # --- THE FIX: Correct angle calculation ---
        start_angle_degrees = 90.0 # Start at the top

        for i, (category, value) in enumerate(self._data.items()):
            # Calculate the sweep angle for this slice
            span_angle_degrees = (value / total) * 360.0
            
            # Convert to Qt's required 1/16th of a degree units
            start_angle_qt = int(start_angle_degrees * 16)
            span_angle_qt = int(span_angle_degrees * 16)

            color = self.chart_colors[i % len(self.chart_colors)]
            painter.setBrush(QBrush(color))
            
            painter.drawPie(rect, start_angle_qt, span_angle_qt)
            
            # Decrement the start angle for the next slice
            start_angle_degrees -= span_angle_degrees
            
        # Draw the "donut hole"
        hole_size_ratio = 0.4
        hole_size = (side - 2*padding) * hole_size_ratio
        hole_x = rect.x() + (rect.width() - hole_size) / 2
        hole_y = rect.y() + (rect.height() - hole_size) / 2
        hole_rect = QRectF(hole_x, hole_y, hole_size, hole_size)
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#24283b")))
        painter.drawEllipse(hole_rect)