import unittest

from ruler_opacity import (
    MAX_OPACITY,
    MIN_VISIBLE_OPACITY,
    OPACITY_STEP,
    adjust_opacity,
    clamp_opacity,
)


class RulerOpacityTests(unittest.TestCase):
    def test_initial_opacity_cannot_make_ruler_invisible(self):
        self.assertEqual(clamp_opacity(0.0), MIN_VISIBLE_OPACITY)

    def test_fully_opaque_is_allowed(self):
        self.assertEqual(clamp_opacity(1.0), MAX_OPACITY)

    def test_opacity_down_stops_at_minimum_visible_value(self):
        self.assertEqual(
            adjust_opacity(MIN_VISIBLE_OPACITY, -OPACITY_STEP),
            MIN_VISIBLE_OPACITY,
        )

    def test_opacity_up_stops_at_fully_opaque(self):
        self.assertEqual(adjust_opacity(0.95, OPACITY_STEP), MAX_OPACITY)


if __name__ == "__main__":
    unittest.main()
