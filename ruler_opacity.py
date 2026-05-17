import math

MIN_VISIBLE_OPACITY = 0.1
MAX_OPACITY = 1.0
DEFAULT_OPACITY = 0.9
OPACITY_STEP = 0.1


def clamp_opacity(value, fallback=DEFAULT_OPACITY):
    """Clamp Qt window opacity while keeping the ruler visible."""
    try:
        opacity = float(value)
    except (TypeError, ValueError):
        opacity = fallback

    if not math.isfinite(opacity):
        opacity = fallback

    return max(MIN_VISIBLE_OPACITY, min(MAX_OPACITY, opacity))


def adjust_opacity(current, delta):
    return clamp_opacity(clamp_opacity(current) + delta)
