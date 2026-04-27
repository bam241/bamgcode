# bamgcode
Generate a new G-code file that traces the exact outer envelope of one or more input G-code toolpaths at a configurable hover height above the workpiece.

## Features

- Parse one or more G-code files
- Supports:
    - G0, G1
    - G2, G3 arcs with I/J
    - G20, G21
    - G90, G91
- Build exact motion geometry from toolpaths
- Compute the outer envelope
- Output a new G-code file that hovers around the envelope
- Modular package structure
- CLI included

## Installation
```bash
pip install .
```

## CLI 
### Command-line options
- input_files
    - One or more input G-code files to analyze.
- o, --output
    - Output G-code filename.
    - Example: -o outline.nc
- --hover-z
    - Z height used while tracing the generated outline.
    - Default: 1.0
    - Example: --hover-z 1.0
- --clearance-z
    - Safe Z height used before rapid XY motion.
    - Default: 5.0
    - Example: --clearance-z 5.0
- --feed-rate
    - Feed rate for the generated outline path.
    - Default: 1200.0
    - Example: --feed-rate 1200
- --tool-radius
    - Radius used to compute the swept cutter envelope.
    - Use 0.0 for the programmed toolpath centerline envelope.
    - Use the actual cutter radius for the physical tool sweep envelope.
    - Default: 0.0
    - Example: --tool-radius 3.0
- --include-rapids
    - If set, includes G0 rapid moves in the envelope calculation.
    - Usually this should be left off.
    - Example: --include-rapids
- --cut-z-max
    - Includes only segments whose average Z is less than or equal to this value.
    - Useful for excluding travel moves above the stock.
    - Default: 0.0
    - Example: --cut-z-max 0.0
- --arc-segment-deg
    - Angular step in degrees used to approximate arcs (G2 / G3) as line segments.
    - Smaller values produce more accurate geometry and more points.
    - Default: 3.0
    - Example: --arc-segment-deg 2.0
- --simplify-tol
    - Simplification tolerance applied to the final outline polygon.
    - Lower values preserve more detail.
    - Higher values reduce point count.
    - Default: 0.01
    - Example: --simplify-tol 0.02
- --units
    - Output units for the generated G-code.
    - Choices: mm, inch
    - Default: mm
    - Example: 

### Usage
```bash
bamgcode input1.nc input2.nc -o outline.nc --hover-z 1.0 --clearance-z 5.0 --feed-rate 1200
```

## Example with actual cutter radius
```bash
bamgcode job.nc -o outline.nc --tool-radius 3.0
```

### Library usage
```Python
from bamgcode.gcodeio import read_multiple_gcode_files, write_outline_gcode
from bamgcode.manipulation import lines_to_envelope_polygon

lines = read_multiple_gcode_files(["job.nc"])

polygon = lines_to_envelope_polygon(
lines=lines,
tool_radius=0.0,
include_rapids=False,
cut_z_max=0.0,
arc_segment_deg=2.0,
simplify_tol=0.02,
)

write_outline_gcode(
polygon=polygon,
output_file="outline.nc",
hover_z=1.0,
clearance_z=5.0,
feed_rate=1200.0,
units="mm",
)
```

## Testing
```bash 
pip install -e . pytest
pytest
```

## AI generation note
This codebase was generated with assistance from ChatGPT and should be reviewed, tested, and validated before production or machine use.

Model used: OpenAI GPT-5.4.