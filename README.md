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

## CLI usage
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