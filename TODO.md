# TODO

Future enhancements for Mighty Screen Ruler.

## How To Maintain This List

- Keep one enhancement per item with a stable ID.
- Use `Open`, `In progress`, or `Done` as the status.
- Move implementation details into code or tests when work starts.
- Prefer this file for product-level ideas. Use source-code `TODO` comments only for local implementation notes.
- If the project moves to GitHub issues, convert each open item into one issue and keep this file as a short roadmap link.

## Open Enhancements

### MSR-001: Physical Screen Calibration

Status: Open

Add a calibration mode for matching the on-screen ruler to a real physical ruler placed against the display.

Current behavior should continue to use the screen-reported PPI and the configured calibration factor as the default. Calibration mode would let the user adjust the ruler resolution pixelwise, or subpixel if Qt rendering and storage make that practical, until the displayed centimeter or inch marks align with the physical ruler.

Acceptance notes:

- Show a clear calibration ruler or reference segment on screen.
- Allow fine keyboard adjustment of the effective pixels-per-unit scale.
- Persist the resulting calibration factor in `ruler_config.json`.
- Prefer per-monitor calibration if the Qt screen API exposes stable monitor identifiers.
- Include a reset option to return to screen-reported PPI.

Open questions:

- Should calibration be global at first, then per-monitor later?
- Should calibration use a fixed reference length such as 10 cm / 4 in, or let the user choose the reference length?
- How should subpixel calibration be presented without making the UI fussy?

### MSR-002: User-Defined Measurement Scale

Status: Open

Add a temporary user-defined scale for measuring screen content that is not displayed at real-world scale.

The user should be able to pinpoint two points on the screen, enter the real distance between them in centimeters or inches, and then use the ruler with that derived scale. This would allow measurements on photos, drawings, plans, screenshots, or other content where the screen pixels do not correspond to actual physical dimensions.

Acceptance notes:

- Provide a point-picking mode for two screen points.
- Ask for the known distance and unit between those points.
- Derive an active pixels-per-unit scale from the two-point distance.
- Clearly indicate when a user-defined scale is active.
- Provide a quick reset back to the calibrated physical screen scale.

Open questions:

- Should the user-defined scale be temporary only, or saved as named presets?
- Should it apply to both ruler shapes immediately?
- Should the two reference points remain visible as an overlay while the custom scale is active?

### MSR-003: App Logo And Platform Icons

Status: Open

Create a proper logo and platform icon set for Mighty Screen Ruler.

The app currently builds without a custom icon, which leaves the macOS dock, Finder, app switcher, and release bundle without a distinct visual identity. The logo should work at small sizes and still read as a screen/ruler utility.

Acceptance notes:

- Design a recognizable app logo.
- Produce a macOS `.icns` icon for the app bundle and dock.
- Add the icon to the Nuitka macOS build command.
- Prepare source artwork in an editable format.
- Consider future Windows `.ico` and Linux PNG/SVG variants.

Open questions:

- Should the logo be a literal ruler, a pixel/grid motif, or a combination?
- Should the icon use the rectangular ruler, triangular ruler, or both?
