import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import QPointF
    from PySide6.QtWidgets import QApplication

    from ruler_base import BaseRuler
except ModuleNotFoundError as exc:
    if exc.name != "PySide6":
        raise
    QPointF = None
    QApplication = None
    BaseRuler = object


class TestRuler(BaseRuler):
    def __init__(self):
        super().__init__()
        self.set_ruler_size(100, 40)

    def get_defined_pivots(self):
        return [
            ("Origin", QPointF(10, 5)),
            ("Pivot", QPointF(80, 30)),
        ]

    def get_local_point_from_value(self, value):
        return QPointF(10 + value, 5)


@unittest.skipIf(QPointF is None, "PySide6 is not installed")
class RulerPivotScreenPositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_pivot_position_uses_pivot_point_in_screen_coordinates(self):
        ruler = TestRuler()
        ruler.current_pivot_index = 1
        ruler.precise_pos = QPointF(123.25, 56.5)

        pivot = ruler.get_pivot_point_screen()

        self.assertAlmostEqual(pivot.x(), 203.25)
        self.assertAlmostEqual(pivot.y(), 86.5)

    def test_pivot_position_updates_when_ruler_is_panned(self):
        ruler = TestRuler()
        ruler.current_pivot_index = 1
        ruler.precise_pos = QPointF(123.25, 56.5)
        before = ruler.get_pivot_point_screen()

        ruler.pan_ruler(12, -7)

        after = ruler.get_pivot_point_screen()
        self.assertAlmostEqual(after.x() - before.x(), 12)
        self.assertAlmostEqual(after.y() - before.y(), -7)


if __name__ == "__main__":
    unittest.main()
