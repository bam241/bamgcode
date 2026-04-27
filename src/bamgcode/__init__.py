from .gcodeio import read_gcode_file, read_multiple_gcode_files, write_outline_gcode
from .manipulation import (
    MachineState,
    Segment,
    parse_gcode_to_segments,
    build_toolpath_envelopes,
    lines_to_envelope_polygons,
)

__all__ = [
    "read_gcode_file",
    "read_multiple_gcode_files",
    "write_outline_gcode",
    "MachineState",
    "Segment",
    "parse_gcode_to_segments",
    "build_toolpath_envelopes",
    "lines_to_envelope_polygons",
]

__version__ = "0.1.0"
