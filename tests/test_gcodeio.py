from pathlib import Path

from shapely.geometry import Polygon

from gcode_envelope.gcodeio import strip_comments, read_gcode_file, write_outline_gcode


def test_strip_comments():
    assert strip_comments("G1 X1 Y2 ; hello") == "G1 X1 Y2"
    assert strip_comments("G1 X1 Y2 (comment)") == "G1 X1 Y2"
    assert strip_comments("   ") == ""


def test_read_gcode_file(tmp_path: Path):
    p = tmp_path / "sample.nc"
    p.write_text("G1 X1 Y2 ; comment\n\n(comment only)\nG0 Z5\n", encoding="utf-8")

    lines = read_gcode_file(p)
    assert lines == ["G1 X1 Y2", "G0 Z5"]


def test_write_outline_gcode(tmp_path: Path):
    poly = Polygon([(0, 0), (10, 0), (10, 5), (0, 5), (0, 0)])
    out = tmp_path / "outline.nc"

    write_outline_gcode(poly, out, hover_z=1.0, clearance_z=5.0, feed_rate=1000.0)

    text = out.read_text(encoding="utf-8")
    assert "G0 Z5" in text
    assert "G1 Z1 F1000" in text
    assert "M30" in text
