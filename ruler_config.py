import sys
import json
import os
from copy import deepcopy
from pathlib import Path
from PySide6.QtCore import Qt

# Detect OS for default key bindings
IS_MAC = (sys.platform == 'darwin')
APP_NAME = "Mighty Screen Ruler"
APP_DIR_NAME = APP_NAME.replace(" ", "_")
CONFIG_FILENAME = "ruler_config.json"


def get_config_path():
    if sys.platform == "darwin":
        base_path = Path.home() / "Library" / "Preferences"
    elif sys.platform == "win32":
        base_path = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base_path = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))

    return base_path / APP_DIR_NAME / CONFIG_FILENAME

DEFAULT_CONFIG = {
    "reset_on_switch": True,
    "calibration_factor": 1.0,
    "initial_opacity": 0.9,
    "units": "metric",
    "size_increment": {
        "metric_cm": 1.0,
        "imperial_in": 0.5
    },
    "angle_increment": {
        "fine_deg": 0.1,
        "fast_deg": 1.0
    },
    "branding": {
        "enabled": True,
        "color": "#1e2832",
        "brand": "Mighty Screen Ruler",
        "byline": "by chiefenne"
    },

    # Dimensions
    "ruler_rect": {
        "height_cm": 3.0,
        "width_cm": 30.0,
        "width_in": 12.0
    },
    "ruler_tri": {
        "half_width_cm": 10.0,
        "half_width_in": 5.0,
        "scales": {
            "horizontal": True,
            "edge_angles": {
                "enabled": True,
                "label_mode": "dual_continuous",
                "inner_enabled": True,
                "inner_bar_enabled": True,
                "inner_bar_color": "#ffe600",
                "inner_bar_width_px": 12,
                "inner_bar_offset_px": 38,
                "inner_bar_label_padding_px": 4,
                "inner_label_offset_px": 38,
                "top_clearance_deg": 10
            },
            "origin_guides": {
                "enabled": True,
                "color": "#25333b",
                "alpha": 120,
                "width_px": 1.2,
                "top_clearance_px": 82,
                "edge_clearance_px": 10,
                "outer_scale_clearance_px": 34,
                "inner_scale_clearance_px": 24,
                "bottom_outer_clearance_px": 58,
                "bottom_inner_clearance_px": 34
            }
        }
    },

    # Key Bindings
    "key_bindings": {
        "quit": "Esc",
        "help": "H",
        "toggle_units": "M",
        "switch_ruler": "Space",
        "cycle_pivot": "P",
        "set_pivot_value": "V",
        "reset_angle": "R",
        "set_angle": "A",
        "size_increase": "I",
        "size_decrease": "D",
        "toggle_tri_edge_angles": "E",
        "toggle_tri_inner_angle_scale": "N",
        "cycle_tri_angle_label_mode": "L",

        # Rotation
        "rotate_cw": "Right",
        "rotate_ccw": "Left",

        # Opacity
        "opacity_up": "Up",
        "opacity_down": "Down",

        # Panning
        "pan_left": "Cmd+Left" if IS_MAC else "Ctrl+Left",
        "pan_right": "Cmd+Right" if IS_MAC else "Ctrl+Right",
        "pan_up": "Cmd+Up" if IS_MAC else "Ctrl+Up",
        "pan_down": "Cmd+Down" if IS_MAC else "Ctrl+Down"
    }
}

class RulerConfig:
    def __init__(self):
        self.file_path = get_config_path()
        self.data = deepcopy(DEFAULT_CONFIG)
        self.load()

    def load(self):
        if self.file_path.exists():
            try:
                with self.file_path.open('r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self._merge(self.data, loaded)
            except Exception as e:
                print(f"Error loading config: {e}")
        else:
            self.save()

    def save(self):
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with self.file_path.open('w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def _merge(self, default, user):
        for k, v in user.items():
            if k in default and isinstance(default[k], dict) and isinstance(v, dict):
                self._merge(default[k], v)
            else:
                default[k] = v

    def is_action(self, action_name, event):
        binding = self.data["key_bindings"].get(action_name)
        if not binding:
            return False

        parts = binding.split('+')
        key_str = parts[-1].upper()

        req_mods = Qt.NoModifier
        for mod in parts[:-1]:
            m = mod.lower()
            if m in ['ctrl', 'control']: req_mods |= Qt.ControlModifier
            elif m == 'shift': req_mods |= Qt.ShiftModifier
            elif m == 'alt': req_mods |= Qt.AltModifier
            elif m in ['cmd', 'command']: req_mods |= Qt.ControlModifier if IS_MAC else Qt.MetaModifier
            elif m == 'meta': req_mods |= Qt.MetaModifier

        act_mods = event.modifiers() & (Qt.ShiftModifier | Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier)

        if (act_mods & req_mods) != req_mods:
            return False

        extra = act_mods ^ req_mods
        if extra != Qt.NoModifier:
            if extra == Qt.ShiftModifier:
                pass
            else:
                return False

        key_map = {
            "ESC": Qt.Key.Key_Escape, "SPACE": Qt.Key.Key_Space,
            "LEFT": Qt.Key.Key_Left, "RIGHT": Qt.Key.Key_Right,
            "UP": Qt.Key.Key_Up, "DOWN": Qt.Key.Key_Down,
            "M": Qt.Key.Key_M, "P": Qt.Key.Key_P,
            "V": Qt.Key.Key_V, "R": Qt.Key.Key_R,
            "A": Qt.Key.Key_A, "H": Qt.Key.Key_H
        }

        target_key = key_map.get(key_str)
        if not target_key and len(key_str) == 1:
            target_key = getattr(Qt.Key, f"Key_{key_str}", None)

        return event.key() == target_key

cfg = RulerConfig()
