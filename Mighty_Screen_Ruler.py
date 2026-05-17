import sys
from PySide6.QtWidgets import QApplication
from ruler_rect import RectangularRuler
from ruler_triangle import TriangularRuler
from ruler_config import cfg

rulers = []
current_index = 0

def switch_ruler():
    global current_index

    old_ruler = rulers[current_index]
    old_ruler.hide()

    current_index = (current_index + 1) % len(rulers)
    new_ruler = rulers[current_index]

    new_ruler.use_metric = old_ruler.use_metric
    new_ruler.update_physical_size()

    if cfg.data["reset_on_switch"]:
        new_ruler.rotation_angle = 0.0
        new_ruler.update_geometry(rotation_changed=False)
        new_ruler.current_pivot_index = 0
        new_ruler.center_on_screen()
    else:
        new_ruler.rotation_angle = old_ruler.rotation_angle
        new_ruler.precise_pos = old_ruler.precise_pos
        new_ruler.current_pivot_index = old_ruler.current_pivot_index
        new_ruler.custom_pivot_value = old_ruler.custom_pivot_value
        new_ruler.update_geometry(rotation_changed=True)
        new_ruler.move(int(old_ruler.precise_pos.x()), int(old_ruler.precise_pos.y()))

    new_ruler.show()

def main():
    app = QApplication(sys.argv)

    rect_ruler = RectangularRuler()
    tri_ruler = TriangularRuler()

    global rulers
    rulers = [rect_ruler, tri_ruler]

    rect_orig = rect_ruler.keyPressEvent
    tri_orig = tri_ruler.keyPressEvent

    def make_handler(original):
        def handler(event):
            if cfg.is_action("switch_ruler", event):
                switch_ruler()
            else:
                original(event)
        return handler

    rect_ruler.keyPressEvent = make_handler(rect_orig)
    tri_ruler.keyPressEvent = make_handler(tri_orig)

    rect_ruler.show()
    rect_ruler.center_on_screen()

    print("Mighty Ruler — FINAL")
    print(f"Configuration loaded from {cfg.file_path}")
    print("Press H for help")

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
