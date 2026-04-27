from __future__ import annotations

import re
from pathlib import Path
from typing import List

from shapely.geometry import Polygon


def strip_comments(line: str) -> str:
    line = line.split(";")[0]
    line = re.sub(r"\(.*?\)", "", line)
    return line.strip()


def read_gcode_file(path: str | Path) -> List[str]:
    path = Path(path)
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        return [clean for raw in f if (clean := strip_comments(raw))]


def read_multiple_gcode_files(paths: List[str | Path]) -> List[str]:
    lines: List[str] = []
    for path in paths:
        lines.extend(read_gcode_file(path))
    return lines


def _fmt(v: float) -> str:
    return f"{v:.4f}".rstrip("0").rstrip(".")


def write_outline_gcode(
    polygon: Polygon,
    output_file: str | Path,
    hover_z: float = 1.0,
    clearance_z: float = 5.0,
    feed_rate: float = 1200.0,
    units: str = "mm",
    spindle_off: bool = True,
    program_end: str = "M30",
) -> None:
    coords = list(polygon.exterior.coords)
    if len(coords) < 2:
        raise ValueError("Polygon has too few exterior coordinates to write G-code.")

    lines = []
    lines.append("%")
    lines.append("(Generated exact toolpath envelope)")
    lines.append("G21" if units.lower() == "mm" else "G20")
    lines.append("G90")
    lines.append("G17")

    if spindle_off:
        lines.append("M5")

    sx, sy = coords[0]
    lines.append(f"G0 Z{_fmt(clearance_z)}")
    lines.append(f"G0 X{_fmt(sx)} Y{_fmt(sy)}")
    lines.append(f"G1 Z{_fmt(hover_z)} F{_fmt(feed_rate)}")

    first_feed = True
    for x, y in coords[1:]:
        if first_feed:
            lines.append(f"G1 X{_fmt(x)} Y{_fmt(y)} F{_fmt(feed_rate)}")
            first_feed = False
        else:
            lines.append(f"G1 X{_fmt(x)} Y{_fmt(y)}")

    if coords[0] != coords[-1]:
        lines.append(f"G1 X{_fmt(sx)} Y{_fmt(sy)}")

    lines.append(f"G0 Z{_fmt(clearance_z)}")
    lines.append(program_end)
    lines.append("%")

    output_file = Path(output_file)
    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
