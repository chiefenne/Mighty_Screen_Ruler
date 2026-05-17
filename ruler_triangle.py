import math
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QPolygonF, QBrush, QLinearGradient, QFont, QPainter
from ruler_base import BaseRuler
from ruler_config import cfg

class TriangularRuler(BaseRuler):
    def __init__(self):
        super().__init__()
        tri_cfg = cfg.data["ruler_tri"]
        self.metric_half_width_cm = tri_cfg.get("half_width_cm", tri_cfg.get("radius_cm", 10.0))
        self.imperial_half_width_in = tri_cfg.get("half_width_in", tri_cfg.get("radius_in", 5.0))
        self.plastic_overhang_cm = 0.8
        self.update_physical_size()

    def update_physical_size(self):
        px_per_cm = self.get_px_per_unit()
        if self.use_metric:
            scale_width_cm = self.metric_half_width_cm * 2.0
        else:
            scale_width_cm = (self.imperial_half_width_in * 2.0) * 2.54
        body_width_cm = scale_width_cm + (self.plastic_overhang_cm * 2)
        body_height_cm = body_width_cm / 2
        window_padding_cm = 1.0
        total_w = int((body_width_cm + window_padding_cm * 2) * px_per_cm)
        total_h = int((body_height_cm + window_padding_cm * 2) * px_per_cm)
        self.set_ruler_size(total_w, total_h)

    def apply_size_delta(self, delta):
        minimum = max(abs(delta), 0.1)
        if self.use_metric:
            new_half_width = max(minimum, self.metric_half_width_cm + delta)
            if new_half_width == self.metric_half_width_cm:
                return False
            self.metric_half_width_cm = new_half_width
            cfg.data["ruler_tri"]["half_width_cm"] = new_half_width
        else:
            new_half_width = max(minimum, self.imperial_half_width_in + delta)
            if new_half_width == self.imperial_half_width_in:
                return False
            self.imperial_half_width_in = new_half_width
            cfg.data["ruler_tri"]["half_width_in"] = new_half_width
        self.update_physical_size()
        return True

    def get_annotation_top_left(self, annotation_width, annotation_height):
        geometry = self.get_triangle_body_geometry()
        x = geometry["left_top"].x() + geometry["body_width_px"] * 0.19
        y = geometry["start_y"] + 46
        return self.clamp_left_top_band_info_position(x, y, annotation_width, annotation_height)

    def get_branding_anchor(self, text_width, text_height):
        geometry = self.get_triangle_body_geometry()
        x = geometry["left_top"].x() + geometry["body_width_px"] * 0.38
        y = geometry["start_y"] + 46
        top_left = self.clamp_left_top_band_info_position(x, y, text_width, text_height, keep_left_of_origin=False)
        return QPointF(top_left.x(), top_left.y() + text_height)

    def clamp_left_top_band_info_position(self, x, y, width, height, keep_left_of_origin=True):
        geometry = self.get_triangle_body_geometry()
        origin = self.get_origin_point_local()
        left_top = geometry["left_top"]
        start_y = geometry["start_y"]
        side_margin = 6.0

        bottom = y + height
        min_x = left_top.x() + max(0.0, bottom - start_y) + side_margin
        if keep_left_of_origin:
            max_x = origin.x() - width - 5.0
        else:
            max_x = geometry["right_top"].x() - width - 6.0
        x = min(max(x, min_x), max_x)
        return QPointF(max(0.0, x), max(start_y + 40, y))

    def get_defined_pivots(self):
        w = self.base_width
        center_x = w / 2
        start_y = 10.0
        pivots = [("Zero", QPointF(center_x, start_y))]

        px_per_cm = self.get_px_per_unit()
        if self.use_metric:
            scale_width_cm = self.metric_half_width_cm * 2.0
        else:
            scale_width_cm = (self.imperial_half_width_in * 2.0) * 2.54
        body_width_cm = scale_width_cm + (self.plastic_overhang_cm * 2)
        body_h_px = (body_width_cm * px_per_cm) / 2

        pivots.append(("Peak", QPointF(center_x, start_y + body_h_px)))
        pivots.append(("Center", QPointF(w/2, self.base_height/2)))
        return pivots

    def get_local_point_from_value(self, value):
        center_x = self.base_width / 2
        start_y = 10.0
        px_per_unit = self.get_px_per_unit()
        if not self.use_metric:
            px_per_unit *= 2.54
        x = center_x + (value * px_per_unit)
        return QPointF(x, start_y)

    def get_triangle_body_geometry(self):
        px_per_cm = self.get_px_per_unit()
        if self.use_metric:
            scale_half_width_cm = self.metric_half_width_cm
        else:
            scale_half_width_cm = self.imperial_half_width_in * 2.54

        scale_width_cm = scale_half_width_cm * 2.0
        body_width_cm = scale_width_cm + (self.plastic_overhang_cm * 2)
        body_width_px = body_width_cm * px_per_cm
        body_height_px = body_width_px / 2

        center_x = self.base_width / 2
        start_y = 10.0
        left_top = QPointF(center_x - body_width_px / 2, start_y)
        right_top = QPointF(center_x + body_width_px / 2, start_y)
        apex = QPointF(center_x, start_y + body_height_px)
        return {
            "px_per_cm": px_per_cm,
            "center_x": center_x,
            "start_y": start_y,
            "body_width_px": body_width_px,
            "body_height_px": body_height_px,
            "left_top": left_top,
            "right_top": right_top,
            "apex": apex,
        }

    def is_scale_enabled(self, name):
        scales = cfg.data["ruler_tri"].get("scales", {})
        scale = scales.get(name, True)
        if isinstance(scale, dict):
            return bool(scale.get("enabled", True))
        return bool(scale)

    def get_edge_angle_config(self):
        scales = cfg.data["ruler_tri"].setdefault("scales", {})
        edge_angles = scales.setdefault("edge_angles", {})
        if not isinstance(edge_angles, dict):
            edge_angles = {"enabled": bool(edge_angles)}
            scales["edge_angles"] = edge_angles
        edge_angles.setdefault("enabled", True)
        edge_angles.setdefault("label_mode", "dual_continuous")
        edge_angles.setdefault("inner_enabled", True)
        edge_angles.setdefault("inner_bar_enabled", True)
        edge_angles.setdefault("inner_bar_color", "#ffe600")
        edge_angles.setdefault("inner_bar_width_px", 12)
        edge_angles.setdefault("inner_bar_offset_px", 38)
        edge_angles.setdefault("inner_bar_label_padding_px", 4)
        edge_angles.setdefault("inner_label_offset_px", 38)
        edge_angles.setdefault("top_clearance_deg", 10)
        return edge_angles

    def get_origin_guides_config(self):
        scales = cfg.data["ruler_tri"].setdefault("scales", {})
        origin_guides = scales.setdefault("origin_guides", {})
        if not isinstance(origin_guides, dict):
            origin_guides = {"enabled": bool(origin_guides)}
            scales["origin_guides"] = origin_guides
        origin_guides.setdefault("enabled", True)
        origin_guides.setdefault("color", "#25333b")
        origin_guides.setdefault("alpha", 120)
        origin_guides.setdefault("width_px", 1.2)
        origin_guides.setdefault("top_clearance_px", 82)
        origin_guides.setdefault("edge_clearance_px", 10)
        origin_guides.setdefault("outer_scale_clearance_px", 34)
        origin_guides.setdefault("inner_scale_clearance_px", 24)
        origin_guides.setdefault("bottom_outer_clearance_px", 58)
        origin_guides.setdefault("bottom_inner_clearance_px", 34)
        return origin_guides

    def keyPressEvent(self, event):
        edge_angles = self.get_edge_angle_config()
        if cfg.is_action("toggle_tri_edge_angles", event):
            edge_angles["enabled"] = not bool(edge_angles.get("enabled", True))
            self.update()
        elif cfg.is_action("toggle_tri_inner_angle_scale", event):
            edge_angles["inner_enabled"] = not bool(edge_angles.get("inner_enabled", True))
            edge_angles["label_mode"] = "dual_continuous"
            self.update()
        elif cfg.is_action("cycle_tri_angle_label_mode", event):
            modes = ["dual_continuous", "edge_ascending", "edge_descending"]
            current = edge_angles.get("label_mode", "dual_continuous")
            try:
                next_index = (modes.index(current) + 1) % len(modes)
            except ValueError:
                next_index = 0
            edge_angles["label_mode"] = modes[next_index]
            self.update()
        else:
            super().keyPressEvent(event)

    def draw_ruler_content(self, painter, w, h):
        geometry = self.get_triangle_body_geometry()
        px_per_cm = geometry["px_per_cm"]
        center_x = geometry["center_x"]
        start_y = geometry["start_y"]
        p1 = geometry["left_top"]
        p2 = geometry["right_top"]
        p3 = geometry["apex"]
        triangle = QPolygonF([p1, p2, p3])

        base_color = QColor(220, 235, 255, 140)
        gradient = QLinearGradient(center_x, start_y, p3.x(), p3.y())  # ← FIXED
        gradient.setColorAt(0.0, QColor(255, 255, 255, 190))
        gradient.setColorAt(1.0, base_color)

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(triangle)

        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(255, 255, 255, 200), 1.5))
        painter.drawPolygon(triangle)
        painter.setPen(QPen(QColor(0, 0, 0, 80), 1))
        painter.drawPolygon(triangle)

        if self.is_scale_enabled("origin_guides"):
            self.draw_origin_guides(painter, p1, p2, p3, self.get_origin_guides_config())

        if self.is_scale_enabled("edge_angles"):
            self.draw_edge_angle_scales(painter, p1, p2, p3, self.get_edge_angle_config())

        if self.is_scale_enabled("horizontal"):
            self.draw_ticks(painter, center_x, start_y, px_per_cm)

    def draw_origin_guides(self, painter, left_top, right_top, apex, config):
        origin = self.get_origin_point_local()
        edge_angles = self.get_edge_angle_config()
        color = QColor(str(config.get("color", "#25333b")))
        if not color.isValid():
            color = QColor("#25333b")
        try:
            color.setAlpha(max(0, min(255, int(config.get("alpha", 120)))))
        except (TypeError, ValueError):
            color.setAlpha(120)
        try:
            width = max(0.1, float(config.get("width_px", 1.2)))
        except (TypeError, ValueError):
            width = 1.2

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(color, width)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(pen)

        for angle_degrees, edge_start, edge_end, mirrored in (
            (135, left_top, apex, True),
            (90, left_top, apex, None),
            (45, right_top, apex, False),
        ):
            segment = self.get_origin_guide_segment(
                origin, angle_degrees, edge_start, edge_end, mirrored, apex, config, edge_angles
            )
            if segment is None:
                continue
            start, end = segment
            painter.drawLine(start, end)

        painter.restore()

    def get_origin_guide_segment(self, origin, angle_degrees, edge_start, edge_end, mirrored, apex, config, edge_angles):
        direction = self.get_unit_vector_for_angle(angle_degrees)
        if direction.y() <= 1e-6:
            return None

        top_clearance = self.get_edge_angle_float_config(config, "top_clearance_px", 82)
        start_distance = top_clearance / direction.y()
        start = QPointF(
            origin.x() + direction.x() * start_distance,
            origin.y() + direction.y() * start_distance
        )

        if angle_degrees == 90:
            target, clearance = self.get_vertical_origin_guide_target(origin, apex, config, edge_angles)
        else:
            target, clearance = self.get_side_origin_guide_target(
                origin, edge_start, edge_end, mirrored, 45, config, edge_angles
            )
        if target is None:
            return None

        end = QPointF(
            target.x() - direction.x() * clearance,
            target.y() - direction.y() * clearance
        )
        if self.distance_between_points(start, end) <= 4:
            return None
        return start, end

    def get_side_origin_guide_target(self, origin, edge_start, edge_end, mirrored, angle, config, edge_angles):
        edge_angles_visible = self.is_scale_enabled("edge_angles") and bool(edge_angles.get("enabled", True))
        inner_visible = (
            edge_angles_visible
            and edge_angles.get("label_mode", "dual_continuous") == "dual_continuous"
            and bool(edge_angles.get("inner_enabled", True))
        )
        if inner_visible:
            inner_label_offset = self.get_edge_angle_float_config(edge_angles, "inner_label_offset_px", 38)
            inner_bar_offset = self.get_edge_angle_float_config(edge_angles, "inner_bar_offset_px", 38)
            target = self.get_angle_point_on_offset_edge(
                edge_start, edge_end, origin, mirrored, angle, max(inner_label_offset, inner_bar_offset)
            )
            clearance = self.get_edge_angle_float_config(config, "inner_scale_clearance_px", 24)
            return target, clearance

        edge_point = self.get_edge_point_for_angle(edge_start, edge_end, origin, mirrored, angle)
        if not edge_angles_visible:
            clearance = self.get_edge_angle_float_config(config, "edge_clearance_px", 10)
            return edge_point, clearance

        clearance = self.get_edge_angle_float_config(config, "outer_scale_clearance_px", 34)
        return edge_point, clearance

    def get_vertical_origin_guide_target(self, origin, apex, config, edge_angles):
        edge_angles_visible = self.is_scale_enabled("edge_angles") and bool(edge_angles.get("enabled", True))
        inner_visible = (
            edge_angles_visible
            and edge_angles.get("label_mode", "dual_continuous") == "dual_continuous"
            and bool(edge_angles.get("inner_enabled", True))
        )
        if inner_visible:
            offset = self.get_edge_angle_float_config(edge_angles, "inner_label_offset_px", 38)
            geometry = self.get_triangle_body_geometry()
            target = self.get_angle_point_on_offset_edge(
                geometry["right_top"], apex, origin, mirrored=False, angle=90, offset=offset
            )
            clearance = self.get_edge_angle_float_config(config, "bottom_inner_clearance_px", 34)
            return target, clearance

        if edge_angles_visible:
            clearance = self.get_edge_angle_float_config(config, "bottom_outer_clearance_px", 58)
        else:
            clearance = self.get_edge_angle_float_config(config, "edge_clearance_px", 10)
        return apex, clearance

    def get_unit_vector_for_angle(self, angle_degrees):
        rad = math.radians(angle_degrees)
        return QPointF(math.cos(rad), math.sin(rad))

    def distance_between_points(self, first, second):
        return math.hypot(first.x() - second.x(), first.y() - second.y())

    def draw_edge_angle_scales(self, painter, left_top, right_top, apex, config):
        origin = self.get_origin_point_local()
        mode = config.get("label_mode", "dual_continuous")
        if mode == "dual_continuous":
            inner_label_offset = self.get_edge_angle_float_config(config, "inner_label_offset_px", 38)
            top_clearance_deg = self.get_edge_angle_float_config(config, "top_clearance_deg", 10)
            if config.get("inner_enabled", True):
                self.draw_inner_angle_bars(painter, left_top, right_top, apex, origin, config)
            self.draw_edge_angle_scale(painter, left_top, apex, origin, mirrored=True, label_mode="outer_continuous", radial_offset=0, include_apex_label=False, min_angle=1)
            self.draw_edge_angle_scale(painter, right_top, apex, origin, mirrored=False, label_mode="outer_continuous", radial_offset=0, include_apex_label=True, min_angle=1)
            if config.get("inner_enabled", True):
                self.draw_inner_edge_angle_labels(painter, left_top, apex, origin, mirrored=True, offset=inner_label_offset, include_apex_label=False, min_angle=top_clearance_deg)
                self.draw_inner_edge_angle_labels(painter, right_top, apex, origin, mirrored=False, offset=inner_label_offset, include_apex_label=True, min_angle=top_clearance_deg)
        elif mode == "edge_descending":
            self.draw_edge_angle_scale(painter, left_top, apex, origin, mirrored=True, label_mode="edge_descending", radial_offset=0, include_apex_label=False, min_angle=1)
            self.draw_edge_angle_scale(painter, right_top, apex, origin, mirrored=False, label_mode="edge_descending", radial_offset=0, include_apex_label=False, min_angle=1)
        else:
            self.draw_edge_angle_scale(painter, left_top, apex, origin, mirrored=True, label_mode="edge_ascending", radial_offset=0, include_apex_label=False, min_angle=1)
            self.draw_edge_angle_scale(painter, right_top, apex, origin, mirrored=False, label_mode="edge_ascending", radial_offset=0, include_apex_label=False, min_angle=1)

    def draw_edge_angle_scale(self, painter, edge_start, edge_end, origin, mirrored, label_mode, radial_offset, include_apex_label, draw_ticks=True, min_angle=0):
        dx = edge_end.x() - edge_start.x()
        dy = edge_end.y() - edge_start.y()
        length = math.hypot(dx, dy)
        if length <= 0:
            return

        tangent = QPointF(dx / length, dy / length)
        text_angle = math.degrees(math.atan2(tangent.y(), tangent.x()))
        if text_angle > 90:
            text_angle -= 180
        elif text_angle < -90:
            text_angle += 180

        painter.save()
        painter.setFont(QFont("Arial", 7, QFont.Weight.Bold))
        label_metrics = painter.fontMetrics()
        label_color = QColor(30, 30, 30, 220)
        tick_color = QColor(30, 30, 30)

        start_angle = max(0, int(math.ceil(min_angle)))
        for angle in range(start_angle, 91):
            absolute_angle = 180 - angle if mirrored else angle
            point = self.intersect_angle_ray_with_edge(origin, absolute_angle, edge_start, edge_end)
            if point is None:
                continue

            if angle % 10 == 0:
                tick_len = 15 if radial_offset else 17
                pen = QPen(QColor(tick_color.red(), tick_color.green(), tick_color.blue(), 210), 1.2)
            elif angle % 5 == 0:
                tick_len = 9 if radial_offset else 11
                pen = QPen(QColor(tick_color.red(), tick_color.green(), tick_color.blue(), 165), 1)
            else:
                tick_len = 5 if radial_offset else 6
                pen = QPen(QColor(tick_color.red(), tick_color.green(), tick_color.blue(), 115), 1)

            to_origin = QPointF(origin.x() - point.x(), origin.y() - point.y())
            to_origin_len = math.hypot(to_origin.x(), to_origin.y())
            if to_origin_len <= 0:
                continue
            tick_dir = QPointF(to_origin.x() / to_origin_len, to_origin.y() / to_origin_len)
            tick_start = QPointF(point.x() + tick_dir.x() * radial_offset, point.y() + tick_dir.y() * radial_offset)
            if draw_ticks:
                tick_end = QPointF(tick_start.x() + tick_dir.x() * tick_len, tick_start.y() + tick_dir.y() * tick_len)
                painter.setPen(pen)
                painter.drawLine(tick_start, tick_end)

            should_label = angle % 10 == 0 and 0 < angle < 90
            if include_apex_label and angle == 90:
                should_label = True
            if should_label:
                text = str(self.get_edge_angle_label(angle, mirrored, label_mode))
                text_width = label_metrics.horizontalAdvance(text)
                text_height = label_metrics.height()
                label_extra_offset = tick_len + 11 if draw_ticks else 0
                label_center = QPointF(
                    tick_start.x() + tick_dir.x() * label_extra_offset,
                    tick_start.y() + tick_dir.y() * label_extra_offset
                )
                painter.save()
                painter.translate(label_center)
                painter.rotate(text_angle)
                painter.setPen(label_color)
                painter.drawText(QRectF(-text_width / 2, -text_height / 2, text_width, text_height), Qt.AlignmentFlag.AlignCenter, text)
                painter.restore()

        painter.restore()

    def draw_inner_angle_bars(self, painter, left_top, right_top, apex, origin, config):
        if not config.get("inner_bar_enabled", True):
            return

        color = QColor(str(config.get("inner_bar_color", "#ffe600")))
        if not color.isValid():
            color = QColor("#ffe600")
        try:
            width = max(0.0, float(config.get("inner_bar_width_px", 12)))
        except (TypeError, ValueError):
            width = 13
        if width <= 0:
            return

        offset = self.get_edge_angle_float_config(config, "inner_bar_offset_px", 38)
        top_clearance_deg = self.get_edge_angle_float_config(config, "top_clearance_deg", 10)

        left_line_point, left_tangent = self.get_offset_edge_line(left_top, apex, origin, offset)
        right_line_point, right_tangent = self.get_offset_edge_line(right_top, apex, origin, offset)
        left_normal = self.get_edge_inward_normal(left_top, apex, origin)
        right_normal = self.get_edge_inward_normal(right_top, apex, origin)
        half_width = width / 2.0
        left_lower_line_point = QPointF(
            left_line_point.x() - left_normal.x() * half_width,
            left_line_point.y() - left_normal.y() * half_width
        )
        right_lower_line_point = QPointF(
            right_line_point.x() - right_normal.x() * half_width,
            right_line_point.y() - right_normal.y() * half_width
        )
        lower_tip_point = self.intersect_lines(left_lower_line_point, left_tangent, right_lower_line_point, right_tangent)
        if lower_tip_point is None:
            return

        left_start = self.get_angle_point_on_offset_edge(left_top, apex, origin, mirrored=True, angle=top_clearance_deg, offset=offset)
        right_start = self.get_angle_point_on_offset_edge(right_top, apex, origin, mirrored=False, angle=top_clearance_deg, offset=offset)
        if left_start is None or right_start is None:
            return

        left_start_extension = self.get_inner_bar_start_extension(painter, top_clearance_deg, mirrored=True, config=config)
        right_start_extension = self.get_inner_bar_start_extension(painter, top_clearance_deg, mirrored=False, config=config)
        left_start = QPointF(
            left_start.x() - left_tangent.x() * left_start_extension,
            left_start.y() - left_tangent.y() * left_start_extension
        )
        right_start = QPointF(
            right_start.x() - right_tangent.x() * right_start_extension,
            right_start.y() - right_tangent.y() * right_start_extension
        )
        left_tip = QPointF(
            lower_tip_point.x() + left_normal.x() * half_width,
            lower_tip_point.y() + left_normal.y() * half_width
        )
        right_tip = QPointF(
            lower_tip_point.x() + right_normal.x() * half_width,
            lower_tip_point.y() + right_normal.y() * half_width
        )

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(color, width)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(pen)
        painter.drawLine(left_start, left_tip)
        painter.drawLine(right_start, right_tip)
        painter.restore()

    def get_inner_bar_start_extension(self, painter, top_clearance_deg, mirrored, config):
        label_angle = max(10, int(math.ceil(top_clearance_deg / 10.0) * 10))
        label_angle = min(label_angle, 80)
        text = str(self.get_edge_angle_label(label_angle, mirrored, "inner_continuous"))
        padding = self.get_edge_angle_float_config(config, "inner_bar_label_padding_px", 4)

        painter.save()
        painter.setFont(QFont("Arial", 7, QFont.Weight.Bold))
        text_width = painter.fontMetrics().horizontalAdvance(text)
        painter.restore()
        return max(0.0, text_width / 2.0 + padding)

    def draw_inner_edge_angle_labels(self, painter, edge_start, edge_end, origin, mirrored, offset, include_apex_label, min_angle):
        tangent = QPointF(edge_end.x() - edge_start.x(), edge_end.y() - edge_start.y())
        text_angle = math.degrees(math.atan2(tangent.y(), tangent.x()))
        if text_angle > 90:
            text_angle -= 180
        elif text_angle < -90:
            text_angle += 180

        painter.save()
        painter.setFont(QFont("Arial", 7, QFont.Weight.Bold))
        metrics = painter.fontMetrics()
        painter.setPen(QColor(30, 30, 30, 220))

        start_angle = max(0, int(math.ceil(min_angle)))
        for angle in range(start_angle, 91):
            should_label = angle % 10 == 0 and 0 < angle < 90
            if include_apex_label and angle == 90:
                should_label = True
            if not should_label:
                continue

            label_center = self.get_angle_point_on_offset_edge(edge_start, edge_end, origin, mirrored, angle, offset)
            if label_center is None:
                continue

            text = str(self.get_edge_angle_label(angle, mirrored, "inner_continuous"))
            text_width = metrics.horizontalAdvance(text)
            text_height = metrics.height()
            painter.save()
            painter.translate(label_center)
            painter.rotate(text_angle)
            painter.drawText(QRectF(-text_width / 2, -text_height / 2, text_width, text_height), Qt.AlignmentFlag.AlignCenter, text)
            painter.restore()

        painter.restore()

    def get_offset_edge_line(self, edge_start, edge_end, origin, offset):
        dx = edge_end.x() - edge_start.x()
        dy = edge_end.y() - edge_start.y()
        length = math.hypot(dx, dy)
        if length <= 0:
            return edge_start, QPointF(0, 0)
        tangent = QPointF(dx / length, dy / length)
        normal = self.get_edge_inward_normal(edge_start, edge_end, origin)
        line_point = QPointF(edge_start.x() + normal.x() * offset, edge_start.y() + normal.y() * offset)
        return line_point, tangent

    def get_angle_point_on_offset_edge(self, edge_start, edge_end, origin, mirrored, angle, offset):
        line_point, tangent = self.get_offset_edge_line(edge_start, edge_end, origin, offset)
        absolute_angle = 180 - angle if mirrored else angle
        return self.intersect_angle_ray_with_line(origin, absolute_angle, line_point, tangent)

    def get_edge_inward_normal(self, edge_start, edge_end, origin):
        dx = edge_end.x() - edge_start.x()
        dy = edge_end.y() - edge_start.y()
        length = math.hypot(dx, dy)
        if length <= 0:
            return QPointF(0, 0)
        tangent = QPointF(dx / length, dy / length)
        normal = QPointF(-tangent.y(), tangent.x())
        midpoint = QPointF((edge_start.x() + edge_end.x()) / 2, (edge_start.y() + edge_end.y()) / 2)
        to_origin = QPointF(origin.x() - midpoint.x(), origin.y() - midpoint.y())
        if QPointF.dotProduct(normal, to_origin) < 0:
            normal = QPointF(-normal.x(), -normal.y())
        return normal

    def get_edge_point_for_angle(self, edge_start, edge_end, origin, mirrored, angle):
        absolute_angle = 180 - angle if mirrored else angle
        return self.intersect_angle_ray_with_edge(origin, absolute_angle, edge_start, edge_end)

    def get_edge_angle_float_config(self, config, key, fallback):
        try:
            return float(config.get(key, fallback))
        except (TypeError, ValueError):
            return fallback

    def get_edge_angle_label(self, angle, mirrored, label_mode):
        if label_mode == "outer_continuous":
            return 180 - angle if mirrored else angle
        if label_mode == "inner_continuous":
            return angle if mirrored else 180 - angle
        if label_mode == "edge_descending":
            return 90 - angle
        return angle

    def intersect_angle_ray_with_edge(self, origin, angle_degrees, edge_start, edge_end):
        rad = math.radians(angle_degrees)
        ray = QPointF(math.cos(rad), math.sin(rad))
        edge = QPointF(edge_end.x() - edge_start.x(), edge_end.y() - edge_start.y())
        offset = QPointF(edge_start.x() - origin.x(), edge_start.y() - origin.y())
        denominator = ray.x() * edge.y() - ray.y() * edge.x()
        if abs(denominator) < 1e-9:
            return None

        ray_distance = (offset.x() * edge.y() - offset.y() * edge.x()) / denominator
        edge_position = (offset.x() * ray.y() - offset.y() * ray.x()) / denominator
        if ray_distance < -1e-6 or edge_position < -1e-6 or edge_position > 1.0 + 1e-6:
            return None

        return QPointF(origin.x() + ray.x() * ray_distance, origin.y() + ray.y() * ray_distance)

    def intersect_angle_ray_with_line(self, origin, angle_degrees, line_point, line_direction):
        rad = math.radians(angle_degrees)
        ray = QPointF(math.cos(rad), math.sin(rad))
        offset = QPointF(line_point.x() - origin.x(), line_point.y() - origin.y())
        denominator = ray.x() * line_direction.y() - ray.y() * line_direction.x()
        if abs(denominator) < 1e-9:
            return None

        ray_distance = (offset.x() * line_direction.y() - offset.y() * line_direction.x()) / denominator
        if ray_distance < -1e-6:
            return None

        return QPointF(origin.x() + ray.x() * ray_distance, origin.y() + ray.y() * ray_distance)

    def intersect_lines(self, first_point, first_direction, second_point, second_direction):
        offset = QPointF(second_point.x() - first_point.x(), second_point.y() - first_point.y())
        denominator = first_direction.x() * second_direction.y() - first_direction.y() * second_direction.x()
        if abs(denominator) < 1e-9:
            return None

        distance = (offset.x() * second_direction.y() - offset.y() * second_direction.x()) / denominator
        return QPointF(first_point.x() + first_direction.x() * distance, first_point.y() + first_direction.y() * distance)

    def draw_ticks(self, painter, center_x, start_y, px_per_cm):
        painter.setPen(QPen(QColor(30, 30, 30, 220), 1))
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))

        tick_y_base = start_y + 1

        if self.use_metric:
            max_cm = int(self.metric_half_width_cm)
            for i in range(max_cm * 10 + 1):
                offset_px = (i / 10.0) * px_per_cm
                x_positions = [center_x + offset_px]
                if i > 0: x_positions.append(center_x - offset_px)
                for x in x_positions:
                    tick_len = 0
                    if i % 10 == 0:
                        tick_len = 15
                        val = str(i // 10)
                        tw = painter.fontMetrics().horizontalAdvance(val)
                        painter.drawText(int(x - tw/2), int(tick_y_base + 28), val)
                    elif i % 5 == 0: tick_len = 10
                    else: tick_len = 5
                    painter.drawLine(int(x), int(tick_y_base), int(x), int(tick_y_base + tick_len))
        else:
            px_per_inch = px_per_cm * 2.54
            max_inches = int(self.imperial_half_width_in)
            for i in range(max_inches * 16 + 1):
                offset_px = (i / 16.0) * px_per_inch
                x_positions = [center_x + offset_px]
                if i > 0: x_positions.append(center_x - offset_px)
                for x in x_positions:
                    tick_len = 0
                    if i % 16 == 0:
                        tick_len = 15
                        val = str(i // 16)
                        tw = painter.fontMetrics().horizontalAdvance(val)
                        painter.drawText(int(x - tw/2), int(tick_y_base + 28), val)
                    elif i % 8 == 0: tick_len = 12
                    elif i % 4 == 0: tick_len = 8
                    else: tick_len = 5
                    painter.drawLine(int(x), int(tick_y_base), int(x), int(tick_y_base + tick_len))
