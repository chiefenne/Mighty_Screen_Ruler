import sys
import math
from PySide6.QtCore import Qt, QPoint, QPointF, QRect
from PySide6.QtWidgets import (
    QWidget, QApplication, QInputDialog, QLabel, QVBoxLayout,
    QFrame, QGridLayout, QGraphicsDropShadowEffect
)
from PySide6.QtGui import QPainter, QColor, QFont
from ruler_config import cfg
from ruler_opacity import OPACITY_STEP, adjust_opacity, clamp_opacity

class HelpPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        if sys.platform == "darwin":
            self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow)
        # Fix: Prevent help window from stealing keyboard focus so 'H' works to close it
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        font_family = "Arial"

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(12, 12, 12, 12)

        panel = QFrame()
        panel.setObjectName("helpPanel")
        panel.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(20, 35, 50, 90))
        panel.setGraphicsEffect(shadow)

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(18, 16, 18, 16)
        panel_layout.setSpacing(10)

        title = QLabel("Mighty Ruler")
        title.setObjectName("helpTitle")
        subtitle = QLabel("Controls")
        subtitle.setObjectName("helpSubtitle")
        panel_layout.addWidget(title)
        panel_layout.addWidget(subtitle)

        def add_section(title_text, rows, columns=1):
            section_title = QLabel(title_text)
            section_title.setObjectName("sectionTitle")
            panel_layout.addWidget(section_title)

            grid = QGridLayout()
            grid.setContentsMargins(0, 0, 0, 2)
            grid.setHorizontalSpacing(10)
            grid.setVerticalSpacing(6)
            grid.setColumnStretch(1, 1)
            if columns > 1:
                grid.setColumnStretch(3, 1)
            rows_per_column = math.ceil(len(rows) / columns)

            for index, (key_text, action_text) in enumerate(rows):
                column_group = index // rows_per_column
                row = index % rows_per_column
                key_column = column_group * 2
                action_column = key_column + 1

                key_label = QLabel(key_text)
                key_label.setObjectName("keyCap")
                key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                key_label.setMinimumWidth(104)

                action_label = QLabel(action_text)
                action_label.setObjectName("actionText")

                grid.addWidget(key_label, row, key_column)
                grid.addWidget(action_label, row, action_column)

            panel_layout.addLayout(grid)

        add_section("Mouse", [
            ("Drag", "Move ruler"),
            ("Shift+Drag", "Rotate around pivot"),
        ])
        add_section("Keyboard", [
            ("Arrows", "Fine rotate"),
            ("Shift+Arrows", "Fast rotate"),
            ("Cmd/Ctrl+Arrows", "Pan"),
            ("Up/Down", "Opacity"),
            ("Space", "Switch ruler"),
            ("M", "Metric / imperial"),
            ("I / D", "Resize ruler"),
            ("P", "Cycle pivot"),
            ("V", "Set pivot value"),
            ("R", "Reset angle"),
            ("A", "Set angle"),
            ("H", "Toggle help"),
            ("Esc", "Quit"),
        ], columns=2)
        add_section("Triangle Scales", [
            ("E", "Edge angles"),
            ("N", "Inner angle scale"),
            ("L", "Angle label mode"),
        ])

        hint = QLabel("Click anywhere on this panel to close")
        hint.setObjectName("helpHint")
        panel_layout.addWidget(hint)

        outer_layout.addWidget(panel)

        self.setStyleSheet(f"""
            QFrame#helpPanel {{
                background-color: rgba(218, 235, 252, 226);
                border: 1px solid rgba(255, 255, 255, 210);
                border-radius: 12px;
            }}
            QLabel {{
                font-family: "{font_family}", "Segoe UI", sans-serif;
            }}
            QLabel#helpTitle {{
                color: rgb(18, 32, 44);
                font-size: 16px;
                font-weight: bold;
            }}
            QLabel#helpSubtitle {{
                color: rgba(43, 66, 84, 190);
                font-size: 12px;
                font-weight: bold;
                padding-bottom: 2px;
            }}
            QLabel#sectionTitle {{
                color: rgba(45, 68, 86, 205);
                font-size: 11px;
                font-weight: bold;
                padding-top: 4px;
            }}
            QLabel#keyCap {{
                background-color: rgba(255, 255, 255, 170);
                border: 1px solid rgba(92, 122, 150, 85);
                border-radius: 5px;
                color: rgb(20, 34, 46);
                font-size: 12px;
                font-weight: bold;
                padding: 3px 7px;
            }}
            QLabel#actionText {{
                color: rgb(24, 38, 50);
                font-size: 12px;
                font-weight: normal;
            }}
            QLabel#helpHint {{
                color: rgba(43, 66, 84, 150);
                font-size: 11px;
                padding-top: 3px;
            }}
        """)

    def mousePressEvent(self, event):
        self.hide()

class BaseRuler(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        if sys.platform == "darwin":
            self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow)

        self.dragging = False
        self.rotating_mouse = False
        self.drag_position = QPoint()

        self.calibration_factor = cfg.data["calibration_factor"]
        self.use_metric = (cfg.data["units"] == "metric")
        self.opacity = clamp_opacity(cfg.data["initial_opacity"])
        self.setWindowOpacity(self.opacity)

        self.precise_pos = QPointF(-1000, -1000)
        self.rotation_angle = 0.0

        self.base_width = 100
        self.base_height = 100

        self.current_pivot_index = 0
        self.pivot_label = "Zero"
        self.custom_pivot_value = 0.0

        self.start_mouse_angle = 0.0
        self.start_ruler_angle = 0.0

        self.help_window = HelpPopup()

    def showEvent(self, event):
        if self.precise_pos.x() < -9000:
            self.precise_pos = QPointF(self.pos())
        super().showEvent(event)

    def center_on_screen(self):
        screen = QApplication.primaryScreen()
        geo = screen.availableGeometry()
        cx = geo.x() + geo.width() / 2
        cy = geo.y() + geo.height() / 2
        x = cx - self.width() / 2
        y = cy - self.height() / 2

        self.move(int(x), int(y))
        self.precise_pos = QPointF(x, y)

    def sync_position(self):
        current_pos = QPointF(self.pos())
        diff = (self.precise_pos - current_pos).manhattanLength()
        # Only sync if deviation is large (manual drag), otherwise trust float math
        if diff > 2.0:
            self.precise_pos = current_pos

    def get_px_per_unit(self):
        screen = QApplication.primaryScreen()
        dpi = screen.physicalDotsPerInch() if hasattr(screen, "physicalDotsPerInch") else 96.0
        effective_dpi = dpi * self.calibration_factor
        return effective_dpi / 2.54

    def set_ruler_size(self, w, h):
        self.base_width = w
        self.base_height = h
        self.update_geometry(rotation_changed=False)

    def get_pivot_point_local(self):
        if self.current_pivot_index == -1:
            return self.get_local_point_from_value(self.custom_pivot_value)
        points = self.get_defined_pivots()
        if points and 0 <= self.current_pivot_index < len(points):
            return points[self.current_pivot_index][1]
        return QPointF(self.base_width / 2, self.base_height / 2)

    def get_defined_pivots(self):
        return [("Center", QPointF(self.base_width / 2, self.base_height / 2))]

    def get_local_point_from_value(self, value):
        return QPointF(0, 0)

    def get_origin_point_local(self):
        return self.get_local_point_from_value(0.0)

    # --- Geometry Helpers ---
    def get_bounding_box_float(self, angle):
        """Returns accurate float width/height of the rotated ruler."""
        angle_rad = math.radians(angle)
        w = self.base_width
        h = self.base_height
        new_w = w * abs(math.cos(angle_rad)) + h * abs(math.sin(angle_rad))
        new_h = w * abs(math.sin(angle_rad)) + h * abs(math.cos(angle_rad))
        return new_w, new_h

    def transform_point_local_to_window(self, local_pt, angle, win_w_float, win_h_float):
        # We use float dimensions for the window to avoid rounding jitter
        cx, cy = win_w_float / 2.0, win_h_float / 2.0
        rcx, rcy = self.base_width / 2.0, self.base_height / 2.0

        vx = local_pt.x() - rcx
        vy = local_pt.y() - rcy

        rad = math.radians(angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        rot_x = vx * cos_a - vy * sin_a
        rot_y = vx * sin_a + vy * cos_a
        return QPointF(cx + rot_x, cy + rot_y)

    def get_point_screen_position(self, local_pt):
        fw, fh = self.get_bounding_box_float(self.rotation_angle)
        window_pt = self.transform_point_local_to_window(
            local_pt, self.rotation_angle, fw, fh
        )
        return self.precise_pos + window_pt

    def get_pivot_point_screen(self):
        return self.get_point_screen_position(self.get_pivot_point_local())

    def get_annotation_top_left(self, annotation_width, annotation_height):
        margin = 8
        x = margin
        y = self.base_height - annotation_height - margin
        if annotation_width + margin * 2 > self.base_width:
            x = max(0, (self.base_width - annotation_width) / 2)
        return QPointF(x, max(margin, y))

    def get_branding_anchor(self, text_width, text_height):
        return QPointF(
            (self.base_width - text_width) / 2,
            max(text_height + 6, self.base_height - 8)
        )

    def calculate_window_size_int(self, angle):
        fw, fh = self.get_bounding_box_float(angle)
        return int(math.ceil(fw)) + 2, int(math.ceil(fh)) + 2

    def update_geometry(self, rotation_changed=True):
        new_w, new_h = self.calculate_window_size_int(self.rotation_angle)
        if not rotation_changed:
            self.resize(new_w, new_h)
            self.update()

    def set_rotation_angle(self, new_angle):
        # NO sync_position(). Trust precise_pos for stability.

        pivot_local = self.get_pivot_point_local()

        # 1. Calculate theoretical float dimensions of CURRENT angle
        # (Fixes wobble by avoiding self.width() which is integer rounded)
        cur_float_w, cur_float_h = self.get_bounding_box_float(self.rotation_angle)

        current_win_pt = self.transform_point_local_to_window(
            pivot_local, self.rotation_angle, cur_float_w, cur_float_h
        )
        global_pivot_x = self.precise_pos.x() + current_win_pt.x()
        global_pivot_y = self.precise_pos.y() + current_win_pt.y()

        # 2. Calculate dimensions for NEW angle
        new_float_w, new_float_h = self.get_bounding_box_float(new_angle)
        new_w_int = int(math.ceil(new_float_w)) + 2
        new_h_int = int(math.ceil(new_float_h)) + 2

        new_win_pt = self.transform_point_local_to_window(
            pivot_local, new_angle, new_float_w, new_float_h
        )

        target_x = global_pivot_x - new_win_pt.x()
        target_y = global_pivot_y - new_win_pt.y()

        self.setGeometry(int(round(target_x)), int(round(target_y)), new_w_int, new_h_int)
        self.rotation_angle = new_angle
        self.precise_pos = QPointF(target_x, target_y)
        self.update()

    def pan_ruler(self, dx, dy):
        """Move the ruler by dx, dy pixels."""
        self.precise_pos += QPointF(dx, dy)
        self.move(int(round(self.precise_pos.x())), int(round(self.precise_pos.y())))
        self.update()

    def set_ruler_opacity(self, opacity):
        self.opacity = clamp_opacity(opacity)
        self.setWindowOpacity(self.opacity)

    def get_size_increment(self):
        increments = cfg.data.get("size_increment", {})
        key = "metric_cm" if self.use_metric else "imperial_in"
        fallback = 1.0 if self.use_metric else 0.5
        try:
            return max(0.0, float(increments.get(key, fallback)))
        except (TypeError, ValueError):
            return fallback

    def get_angle_increment(self, fast=False):
        increments = cfg.data.get("angle_increment", {})
        key = "fast_deg" if fast else "fine_deg"
        fallback = 1.0 if fast else 0.1
        try:
            return max(0.0, float(increments.get(key, fallback)))
        except (TypeError, ValueError):
            return fallback

    def apply_size_delta(self, delta):
        return False

    def resize_around_pivot(self, resize_func):
        pivot_local = self.get_pivot_point_local()
        old_float_w, old_float_h = self.get_bounding_box_float(self.rotation_angle)
        old_win_pt = self.transform_point_local_to_window(
            pivot_local, self.rotation_angle, old_float_w, old_float_h
        )
        global_pivot_x = self.precise_pos.x() + old_win_pt.x()
        global_pivot_y = self.precise_pos.y() + old_win_pt.y()

        if not resize_func():
            return

        new_pivot_local = self.get_pivot_point_local()
        new_float_w, new_float_h = self.get_bounding_box_float(self.rotation_angle)
        new_win_pt = self.transform_point_local_to_window(
            new_pivot_local, self.rotation_angle, new_float_w, new_float_h
        )
        new_w_int, new_h_int = self.calculate_window_size_int(self.rotation_angle)
        target_x = global_pivot_x - new_win_pt.x()
        target_y = global_pivot_y - new_win_pt.y()

        self.setGeometry(int(round(target_x)), int(round(target_y)), new_w_int, new_h_int)
        self.precise_pos = QPointF(target_x, target_y)
        self.update()

    def adjust_ruler_size(self, direction):
        increment = self.get_size_increment()
        if increment <= 0:
            return
        self.resize_around_pivot(lambda: self.apply_size_delta(direction * increment))

    def get_mouse_angle_to_pivot(self, global_mouse_pos):
        pivot_local = self.get_pivot_point_local()
        # Use float math for mouse angle too
        fw, fh = self.get_bounding_box_float(self.rotation_angle)
        win_pt = self.transform_point_local_to_window(
            pivot_local, self.rotation_angle, fw, fh
        )
        global_pivot_x = self.precise_pos.x() + win_pt.x()
        global_pivot_y = self.precise_pos.y() + win_pt.y()
        dx = global_mouse_pos.x() - global_pivot_x
        dy = global_mouse_pos.y() - global_pivot_y
        return math.degrees(math.atan2(dy, dx))

    # --- Events ---
    def mousePressEvent(self, event):
        self.sync_position()
        if event.button() == Qt.MouseButton.LeftButton:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.rotating_mouse = True
                self.start_ruler_angle = self.rotation_angle
                self.start_mouse_angle = self.get_mouse_angle_to_pivot(event.globalPosition())
            else:
                self.dragging = True
                self.drag_position = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        if self.rotating_mouse:
            current_mouse_angle = self.get_mouse_angle_to_pivot(event.globalPosition())
            delta = current_mouse_angle - self.start_mouse_angle
            self.set_rotation_angle(self.start_ruler_angle + delta)
        elif self.dragging:
            new_pos = event.globalPosition().toPoint() - self.drag_position
            self.move(new_pos)
            self.precise_pos = QPointF(new_pos)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.rotating_mouse = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        if self.opacity <= 0.01:
            return

        pos_int = QPointF(self.pos())
        delta = self.precise_pos - pos_int
        painter.save()
        painter.translate(delta)

        # Center using float dimensions of bounding box to match logic
        fw, fh = self.get_bounding_box_float(self.rotation_angle)

        # NOTE: Painter translation must center visually.
        # Using self.width() (integer) here is correct because
        # setGeometry set the integer width.
        # But for perfect sub-pixel pivot alignment, we follow our math:

        # We calculated 'precise_pos' based on 'fw/2'.
        # If we draw, we must move to fw/2.

        cx_float = fw / 2.0
        cy_float = fh / 2.0

        # Because we used ceil()+2 for the window, there is extra space.
        # We need to center the drawing in that calculated space?
        # No, transform_point_local_to_window assumes center is center.

        # To match exactly:
        painter.translate(cx_float, cy_float)
        painter.rotate(self.rotation_angle)
        painter.translate(-self.base_width / 2.0, -self.base_height / 2.0)

        self.draw_ruler_content(painter, self.base_width, self.base_height)

        pivot = self.get_pivot_point_local()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 0, 0, 200))
        painter.drawEllipse(pivot, 3, 3)
        self.draw_status_annotation(painter)
        self.draw_branding(painter)
        painter.restore()

    def draw_branding(self, painter):
        branding = cfg.data.get("branding", {})
        if not branding.get("enabled", True):
            return

        title = str(branding.get("brand", "Mighty Screen Ruler")).strip()
        credit = str(branding.get("byline", "by chiefenne")).strip()
        if not title and not credit:
            return

        color = QColor(str(branding.get("color", "#1e2832")))
        if not color.isValid():
            color = QColor("#1e2832")

        painter.save()
        gap = 4
        title_width = 0
        credit_width = 0
        title_height = 0
        credit_height = 0

        if title:
            painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            title_metrics = painter.fontMetrics()
            title_width = title_metrics.horizontalAdvance(title)
            title_height = title_metrics.height()

        if credit:
            painter.setFont(QFont("Arial", 8))
            credit_metrics = painter.fontMetrics()
            credit_width = credit_metrics.horizontalAdvance(credit)
            credit_height = credit_metrics.height()

        width = max(title_width, credit_width)
        height = title_height + credit_height
        if title and credit:
            height += gap
        anchor = self.get_branding_anchor(width, height)
        x = anchor.x()
        y = anchor.y() - height

        painter.setPen(color)
        text_y = y
        if title:
            painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            title_metrics = painter.fontMetrics()
            text_y += title_metrics.ascent()
            painter.drawText(int(round(x + (width - title_width) / 2)), int(round(text_y)), title)
            text_y += title_metrics.descent()

        if title and credit:
            text_y += gap

        if credit:
            painter.setFont(QFont("Arial", 8))
            credit_metrics = painter.fontMetrics()
            text_y += credit_metrics.ascent()
            painter.drawText(int(round(x + (width - credit_width) / 2)), int(round(text_y)), credit)
        painter.restore()

    def draw_status_annotation(self, painter):
        pivot = self.get_pivot_point_screen()
        lines = [
            f"Angle: {self.rotation_angle:.1f} deg",
            f"Pivot: {round(pivot.x())}, {round(pivot.y())} px",
        ]

        painter.save()
        painter.setFont(QFont("Arial", 9))
        metrics = painter.fontMetrics()
        padding_x = 6
        padding_y = 5
        width = max(metrics.horizontalAdvance(line) for line in lines) + padding_x * 2
        height = metrics.lineSpacing() * len(lines) + padding_y * 2
        top_left = self.get_annotation_top_left(width, height)
        x = int(round(top_left.x()))
        y = int(round(top_left.y()))
        rect = QRect(x, y, width, height)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 145))
        painter.drawRoundedRect(rect, 5, 5)
        painter.setPen(QColor(255, 255, 255, 230))

        text_y = y + padding_y + metrics.ascent()
        for line in lines:
            painter.drawText(x + padding_x, text_y, line)
            text_y += metrics.lineSpacing()
        painter.restore()

    def keyPressEvent(self, event):
        if cfg.is_action("help", event):
            if self.help_window.isVisible():
                self.help_window.hide()
            else:
                self.help_window.move(self.pos() + QPoint(20, 20))
                self.help_window.show()
                # Restore focus to Ruler so keyboard still works
                self.activateWindow()
                self.setFocus()

        elif cfg.is_action("quit", event):
            QApplication.quit()
        elif cfg.is_action("toggle_units", event):
            self.use_metric = not self.use_metric
            if hasattr(self, 'update_physical_size'):
                self.update_physical_size()

        elif cfg.is_action("rotate_cw", event):
            mod = self.get_angle_increment(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
            self.set_rotation_angle(self.rotation_angle + mod)
        elif cfg.is_action("rotate_ccw", event):
            mod = self.get_angle_increment(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
            self.set_rotation_angle(self.rotation_angle - mod)
        elif cfg.is_action("reset_angle", event):
            self.set_rotation_angle(0.0)
        elif cfg.is_action("set_angle", event):
            val, ok = QInputDialog.getDouble(self, "Set Angle", "Enter angle:", self.rotation_angle, -360, 360, 2)
            if ok: self.set_rotation_angle(val)
        elif cfg.is_action("size_increase", event):
            self.adjust_ruler_size(1)
        elif cfg.is_action("size_decrease", event):
            self.adjust_ruler_size(-1)

        # Pan
        elif cfg.is_action("pan_right", event):
            self.pan_ruler(10 if event.modifiers() & Qt.ShiftModifier else 1, 0)
        elif cfg.is_action("pan_left", event):
            self.pan_ruler(-10 if event.modifiers() & Qt.ShiftModifier else -1, 0)
        elif cfg.is_action("pan_up", event):
            # FIXED: typo with 3 args removed
            self.pan_ruler(0, -10 if event.modifiers() & Qt.ShiftModifier else -1)
        elif cfg.is_action("pan_down", event):
            self.pan_ruler(0, 10 if event.modifiers() & Qt.ShiftModifier else 1)

        elif cfg.is_action("cycle_pivot", event):
            points = self.get_defined_pivots()
            if self.current_pivot_index == -1: self.current_pivot_index = 0
            else: self.current_pivot_index = (self.current_pivot_index + 1) % len(points)
            self.update()
        elif cfg.is_action("set_pivot_value", event):
            unit = "cm" if self.use_metric else "in"
            val, ok = QInputDialog.getDouble(self, "Set Pivot", f"Pos ({unit}):", self.custom_pivot_value, -100, 100, 2)
            if ok:
                self.custom_pivot_value = val
                self.current_pivot_index = -1
                self.update()

        elif cfg.is_action("opacity_up", event):
            self.set_ruler_opacity(adjust_opacity(self.opacity, OPACITY_STEP))
        elif cfg.is_action("opacity_down", event):
            self.set_ruler_opacity(adjust_opacity(self.opacity, -OPACITY_STEP))
