# tidycore/pie_chart_widget.py
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QBrush, QPen
from PySide6.QtCore import Qt, QRectF

class PieChartWidget(QWidget):
    """A stateless drawing canvas for the pie chart."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.slices = []
        self.setMinimumSize(150, 150)

    def update_slices(self, slices_to_draw):
        """Receives a list of pre-calculated slice data and schedules a repaint."""
        self.slices = slices_to_draw
        self.update() # Triggers paintEvent

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        side = min(self.width(), self.height())
        padding = 10 
        rect = QRectF(padding, padding, side - 2*padding, side - 2*padding)

        if not self.slices:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#3b3f51")))
            painter.drawEllipse(rect)
            return
        
        pen = QPen(QColor("#1a1b26"), 3)
        pen.setCosmetic(True)

        for slice_data in self.slices:
            painter.setPen(pen)
            painter.setBrush(QBrush(slice_data['color']))
            
            start_angle_qt = int(slice_data['start_angle'] * 16)
            span_angle_qt = int(slice_data['span_angle'] * 16)
            
            painter.drawPie(rect, start_angle_qt, span_angle_qt)
            
        # Draw the donut hole
        hole_size_ratio = 0.4
        hole_size = (side - 2*padding) * hole_size_ratio
        hole_rect = rect.adjusted(
            (rect.width() - hole_size) / 2, (rect.height() - hole_size) / 2,
            -(rect.width() - hole_size) / 2, -(rect.height() - hole_size) / 2
        )
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#24283b")))
        painter.drawEllipse(hole_rect)