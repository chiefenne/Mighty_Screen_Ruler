from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPen, QColor, QFont, QLinearGradient, QBrush
from ruler_base import BaseRuler
from ruler_config import cfg

class RectangularRuler(BaseRuler):
    def __init__(self):
        super().__init__()
        self.metric_width_cm = cfg.data["ruler_rect"]["width_cm"]
        self.imperial_width_in = cfg.data["ruler_rect"]["width_in"]
        self.ruler_height_cm = cfg.data["ruler_rect"]["height_cm"]
        self.update_physical_size()

    def update_physical_size(self):
        px_per_cm = self.get_px_per_unit()
        if self.use_metric:
            length = self.metric_width_cm
            self.padding_left = 0.5 * px_per_cm
            self.scale_len = length * px_per_cm
            total_width = (length + 1.0) * px_per_cm
        else:
            length = self.imperial_width_in
            px_per_inch = px_per_cm * 2.54
            self.padding_left = 0.25 * px_per_inch
            self.scale_len = length * px_per_inch
            total_width = (length + 0.5) * px_per_inch

        w = int(total_width)
        h = int(self.ruler_height_cm * px_per_cm)
        self.set_ruler_size(w, h)

    def apply_size_delta(self, delta):
        minimum = max(abs(delta), 0.1)
        if self.use_metric:
            new_width = max(minimum, self.metric_width_cm + delta)
            if new_width == self.metric_width_cm:
                return False
            self.metric_width_cm = new_width
            cfg.data["ruler_rect"]["width_cm"] = new_width
        else:
            new_width = max(minimum, self.imperial_width_in + delta)
            if new_width == self.imperial_width_in:
                return False
            self.imperial_width_in = new_width
            cfg.data["ruler_rect"]["width_in"] = new_width
        self.update_physical_size()
        return True

    def get_defined_pivots(self):
        w = self.base_width
        h = self.base_height
        pivots = [("Zero", QPointF(self.padding_left, 0))]
        pivots.append(("Center", QPointF(w/2, h/2)))
        pivots.append(("End", QPointF(self.padding_left + self.scale_len, 0)))
        return pivots

    def get_local_point_from_value(self, value):
        px_per_unit = self.get_px_per_unit()
        if not self.use_metric:
             px_per_unit *= 2.54
        x = self.padding_left + (value * px_per_unit)
        return QPointF(x, 0)

    def draw_ruler_content(self, painter, w, h):
        self.draw_acrylic_body(painter, w, h)
        self.draw_ticks(painter, w, h)

    def draw_acrylic_body(self, p, w, h):
        base_color = QColor(220, 235, 255, 140)
        gradient = QLinearGradient(0, 0, 0, h)
        gradient.setColorAt(0.0, QColor(255, 255, 255, 180))
        gradient.setColorAt(0.5, base_color)
        gradient.setColorAt(1.0, QColor(200, 210, 230, 140))
        p.setBrush(QBrush(gradient))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, w, h, 10, 10)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(255, 255, 255, 200), 1))
        p.drawRoundedRect(1, 1, w-2, h-2, 10, 10)
        p.setPen(QPen(QColor(0, 0, 0, 50), 1))
        p.drawRoundedRect(0, 0, w, h, 10, 10)

    def draw_ticks(self, p, w, h):
        px_per_cm = self.get_px_per_unit()
        pen = QPen(QColor(30, 30, 30, 220), 1)
        p.setPen(pen)
        p.setFont(QFont("Arial", 10, QFont.Weight.Bold))

        limit = int(self.scale_len / px_per_cm * 10) if self.use_metric else int(self.scale_len / (px_per_cm*2.54) * 16)
        px_per_inch = px_per_cm * 2.54

        if self.use_metric:
            start_x = 0.5 * px_per_cm
            for i in range(limit + 1):
                x = start_x + (i * px_per_cm / 10)
                if i % 10 == 0:
                    p.drawLine(int(x), 0, int(x), 25)
                    val = str(i // 10)
                    text_w = p.fontMetrics().horizontalAdvance(val)
                    p.drawText(int(x - text_w/2), 40, val)
                elif i % 5 == 0: p.drawLine(int(x), 0, int(x), 18)
                else: p.drawLine(int(x), 0, int(x), 10)
        else:
            start_x = 0.25 * px_per_inch
            for i in range(limit + 1):
                x = start_x + (i * px_per_inch / 16)
                if i % 16 == 0:
                    p.drawLine(int(x), 0, int(x), 25)
                    val = str(i // 16)
                    text_w = p.fontMetrics().horizontalAdvance(val)
                    p.drawText(int(x - text_w/2), 40, val)
                elif i % 8 == 0: p.drawLine(int(x), 0, int(x), 20)
                elif i % 4 == 0: p.drawLine(int(x), 0, int(x), 15)
                else: p.drawLine(int(x), 0, int(x), 8)
