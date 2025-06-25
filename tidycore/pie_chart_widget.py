# tidycore/pie_chart_widget.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtGui import QPainter, QColor, QBrush, QPen
from PySide6.QtCore import Qt, QRectF

class PieChartWidget(QWidget):
    """A final, robust, self-contained pie chart widget."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = {}
        self.chart_colors = [
            QColor("#7aa2f7"), QColor("#ff79c6"), QColor("#9ece6a"),
            QColor("#e0af68"), QColor("#bb9af7"), QColor("#7dcfff")
        ]
        self.setMinimumSize(250, 150)

        main_layout = QHBoxLayout(self)
        self.chart_view = ChartView(self)
        self.legend_layout = QVBoxLayout()
        self.legend_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.legend_layout.setSpacing(8)
        
        main_layout.addWidget(self.chart_view, 2)
        main_layout.addLayout(self.legend_layout, 1)

    def update_data(self, new_data: dict):
        """
        THE STATE FIX: Merges new data with existing data and redraws.
        This is the only public method to change the chart.
        """
        # Merge the new data into our internal state
        self._data = new_data
        
        # Now, rebuild everything based on this single, authoritative state
        self._rebuild_view()

    def _rebuild_view(self):
        """Rebuilds the chart and legend from the internal _data."""
        # Clear old legend
        while self.legend_layout.count():
            child = self.legend_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()

        if not self._data:
            self.chart_view.update_slices([]) # Draw empty chart
            return

        total = sum(self._data.values())
        if total == 0:
            self.chart_view.update_slices([])
            return

        sorted_data = dict(sorted(self._data.items(), key=lambda item: item[1], reverse=True))
        
        slices_to_draw = []
        cumulative_percentage = 0.0

        for i, (category, count) in enumerate(sorted_data.items()):
            percentage = count / total
            color = self.chart_colors[i % len(self.chart_colors)]
            
            # Add to legend
            self._add_legend_item(category, count, percentage, color)
            
            # THE MATH FIX: Calculate start and end points to prevent gaps
            start_angle = cumulative_percentage * 360.0
            span_angle = percentage * 360.0
            
            slices_to_draw.append({'color': color, 'start_angle': start_angle, 'span_angle': span_angle})
            
            cumulative_percentage += percentage
        
        self.chart_view.update_slices(slices_to_draw)

    def _add_legend_item(self, name, value, percentage, color):
        legend_item_layout = QHBoxLayout()
        color_box = QLabel()
        color_box.setFixedSize(12, 12)
        color_box.setStyleSheet(f"background-color: {color.name()}; border-radius: 6px;")
        
        label_text = f"{name}: {value} ({percentage:.1%})" # Use percentage formatting
        text_label = QLabel(label_text)
        
        legend_item_layout.addWidget(color_box)
        legend_item_layout.addWidget(text_label)
        legend_item_layout.addStretch()
        self.legend_layout.addLayout(legend_item_layout)


class ChartView(QWidget):
    """Stateless drawing canvas. It only knows how to draw what it's told."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.slices = []

    def update_slices(self, slices):
        self.slices = slices
        self.update()

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
            
            # Angles start from 90 degrees (top) and go clockwise
            start_angle_qt = int((90 - slice_data['start_angle']) * 16)
            span_angle_qt = int(-slice_data['span_angle'] * 16) # Negative for clockwise
            
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