# Mighty Screen Ruler

Mighty Screen Ruler is a transparent on-screen ruler which stays on top of othe windows. It provides a rectangular ruler and a triangular drafting ruler with metric and imperial scales, keyboard control, pivot-based rotation, configurable sizing, and angle annotations.

## Features

- Always-on-top ruler
- Rectangular and triangular ruler modes
- Metric and imperial units
- Pivot-based rotation with fine and fast keyboard increments
- Keyboard resizing with configurable increments
- Window-position and current-angle annotation
- Highly configurable through a JSON config file
- Triangle edge angle scales with optional secondary inner scale
- Triangle origin guide lines

## Requirements

- Python 3.12 or newer
- PySide6

Install the dependency:

```bash
python3 -m pip install PySide6
```

## Run

```bash
python3 Mighty_Screen_Ruler.py
```

Press `H` in the app to open the help popup.

## Configuration

Most behavior can be adjusted in the per-user `ruler_config.json`, stored at:

- macOS: `~/Library/Preferences/Mighty_Screen_Ruler/ruler_config.json`
- Windows: `%APPDATA%\Mighty_Screen_Ruler\ruler_config.json`
- Linux: `${XDG_CONFIG_HOME:-~/.config}/Mighty_Screen_Ruler/ruler_config.json`

Configurable behavior includes:

- default units
- size increments
- angle increments
- ruler dimensions
- branding text and color
- triangle angle scales
- triangle origin guide lines
- keyboard bindings

An example config is available at `examples/ruler_config.example.json`.

## License

MIT License. See `LICENSE`.
