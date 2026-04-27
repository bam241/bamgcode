from gcode_envelope.manipulation import (
    parse_gcode_to_segments,
    lines_to_envelope_polygon,
)


def test_parse_simple_lines():
    lines = [
        "G21",
        "G90",
        "G0 X0 Y0",
        "G1 Z-1.0",
        "G1 X10 Y0",
        "G1 X10 Y10",
    ]
    segments = parse_gcode_to_segments(lines)
    assert len(segments) >= 2
    assert segments[-1].points[-1] == (10.0, 10.0)


def test_incremental_mode():
    lines = [
        "G21",
        "G91",
        "G1 X10 Y0",
        "G1 X0 Y5",
    ]
    segments = parse_gcode_to_segments(lines)
    assert segments[0].points[-1] == (10.0, 0.0)
    assert segments[1].points[-1] == (10.0, 5.0)


def test_envelope_polygon_exists():
    lines = [
        "G21",
        "G90",
        "G1 Z-1",
        "G1 X0 Y0",
        "G1 X10 Y0",
        "G1 X10 Y10",
        "G1 X0 Y10",
        "G1 X0 Y0",
    ]
    poly = lines_to_envelope_polygon(
        lines=lines,
        tool_radius=0.5,
        include_rapids=False,
        cut_z_max=0.0,
    )
    assert poly.area > 0
