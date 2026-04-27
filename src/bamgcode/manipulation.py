from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
from shapely.geometry import LineString, Polygon, MultiPolygon
from shapely.ops import unary_union


@dataclass
class MachineState:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    absolute: bool = True
    units: str = "mm"
    motion: Optional[str] = None


@dataclass
class Segment:
    points: List[Tuple[float, float]]
    motion: str
    start_z: float
    end_z: float


def has_gcode(line: str, code: str) -> bool:
    return re.search(rf"\b{re.escape(code)}\b", line, re.IGNORECASE) is not None


def find_word(line: str, letter: str) -> Optional[float]:
    m = re.search(rf"{letter}([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", line, re.IGNORECASE)
    return float(m.group(1)) if m else None


def unit_scale(units: str) -> float:
    return 25.4 if units == "inch" else 1.0


def interpolate_arc(
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    center_x: float,
    center_y: float,
    clockwise: bool,
    arc_segment_deg: float = 3.0,
) -> List[Tuple[float, float]]:
    radius = math.hypot(start_x - center_x, start_y - center_y)
    if radius == 0:
        return [(start_x, start_y), (end_x, end_y)]

    start_ang = math.atan2(start_y - center_y, start_x - center_x)
    end_ang = math.atan2(end_y - center_y, end_x - center_x)

    if clockwise:
        if end_ang >= start_ang:
            end_ang -= 2 * math.pi
    else:
        if end_ang <= start_ang:
            end_ang += 2 * math.pi

    total = end_ang - start_ang
    step = math.radians(arc_segment_deg)
    n = max(8, int(abs(total) / step) + 1)

    pts = []
    for a in np.linspace(start_ang, end_ang, n):
        x = center_x + radius * math.cos(a)
        y = center_y + radius * math.sin(a)
        pts.append((x, y))

    pts[0] = (start_x, start_y)
    pts[-1] = (end_x, end_y)
    return pts


def parse_gcode_to_segments(
    lines: List[str],
    arc_segment_deg: float = 3.0,
) -> List[Segment]:
    segments: List[Segment] = []
    state = MachineState()

    for line in lines:
        upper = line.upper()

        if has_gcode(upper, "G20"):
            state.units = "inch"
        if has_gcode(upper, "G21"):
            state.units = "mm"
        if has_gcode(upper, "G90"):
            state.absolute = True
        if has_gcode(upper, "G91"):
            state.absolute = False

        if has_gcode(upper, "G0") or has_gcode(upper, "G00"):
            state.motion = "G0"
        elif has_gcode(upper, "G1") or has_gcode(upper, "G01"):
            state.motion = "G1"
        elif has_gcode(upper, "G2") or has_gcode(upper, "G02"):
            state.motion = "G2"
        elif has_gcode(upper, "G3") or has_gcode(upper, "G03"):
            state.motion = "G3"

        if state.motion not in ("G0", "G1", "G2", "G3"):
            continue

        scale = unit_scale(state.units)

        xw = find_word(line, "X")
        yw = find_word(line, "Y")
        zw = find_word(line, "Z")
        iw = find_word(line, "I")
        jw = find_word(line, "J")

        sx, sy, sz = state.x, state.y, state.z
        ex, ey, ez = sx, sy, sz

        if state.absolute:
            if xw is not None:
                ex = xw * scale
            if yw is not None:
                ey = yw * scale
            if zw is not None:
                ez = zw * scale
        else:
            if xw is not None:
                ex = sx + xw * scale
            if yw is not None:
                ey = sy + yw * scale
            if zw is not None:
                ez = sz + zw * scale

        if state.motion in ("G0", "G1"):
            if (sx, sy) != (ex, ey):
                segments.append(
                    Segment(
                        points=[(sx, sy), (ex, ey)],
                        motion=state.motion,
                        start_z=sz,
                        end_z=ez,
                    )
                )

        elif state.motion in ("G2", "G3"):
            if (sx, sy) != (ex, ey):
                if iw is not None and jw is not None:
                    cx = sx + iw * scale
                    cy = sy + jw * scale
                    pts = interpolate_arc(
                        start_x=sx,
                        start_y=sy,
                        end_x=ex,
                        end_y=ey,
                        center_x=cx,
                        center_y=cy,
                        clockwise=(state.motion == "G2"),
                        arc_segment_deg=arc_segment_deg,
                    )
                else:
                    pts = [(sx, sy), (ex, ey)]

                segments.append(
                    Segment(
                        points=pts,
                        motion=state.motion,
                        start_z=sz,
                        end_z=ez,
                    )
                )

        state.x, state.y, state.z = ex, ey, ez

    return segments


def segment_is_included(
    seg: Segment,
    include_rapids: bool,
    cut_z_max: Optional[float],
) -> bool:
    if not include_rapids and seg.motion == "G0":
        return False

    if cut_z_max is not None:
        avg_z = 0.5 * (seg.start_z + seg.end_z)
        if avg_z > cut_z_max:
            return False

    return True


def _sort_polygons(polygons: List[Polygon]) -> List[Polygon]:
    def key(poly: Polygon):
        minx, miny, maxx, maxy = poly.bounds
        return (miny, minx, -poly.area)

    return sorted(polygons, key=key)


def build_toolpath_envelopes(
    segments: List[Segment],
    tool_radius: float = 0.0,
    include_rapids: bool = False,
    cut_z_max: Optional[float] = 0.0,
    simplify_tol: float = 0.01,
    round_joins: bool = True,
) -> List[Polygon]:
    geoms = []

    for seg in segments:
        if not segment_is_included(seg, include_rapids, cut_z_max):
            continue
        if len(seg.points) < 2:
            continue
        geoms.append(LineString(seg.points))

    if not geoms:
        raise ValueError("No matching motion segments found for envelope construction.")

    merged = unary_union(geoms)

    eps = 0.001
    radius = max(tool_radius, eps)

    join_style = 1 if round_joins else 2
    cap_style = 1

    envelope = merged.buffer(
        radius,
        resolution=24,
        join_style=join_style,
        cap_style=cap_style,
    )

    envelope = unary_union(envelope)

    if simplify_tol > 0:
        envelope = envelope.simplify(simplify_tol, preserve_topology=True)

    if isinstance(envelope, Polygon):
        polygons = [envelope]
    elif isinstance(envelope, MultiPolygon):
        polygons = list(envelope.geoms)
    else:
        raise ValueError("Envelope geometry did not resolve to Polygon/MultiPolygon.")

    polygons = [p for p in polygons if not p.is_empty and p.area > 0]
    if not polygons:
        raise ValueError("No valid envelope polygons were produced.")

    polygons = _remove_contained_polygons(polygons)

    return polygons


def lines_to_envelope_polygons(
    lines: List[str],
    tool_radius: float = 0.0,
    include_rapids: bool = False,
    cut_z_max: Optional[float] = 0.0,
    arc_segment_deg: float = 3.0,
    simplify_tol: float = 0.01,
    round_joins: bool = True,
) -> List[Polygon]:
    segments = parse_gcode_to_segments(lines, arc_segment_deg=arc_segment_deg)
    return build_toolpath_envelopes(
        segments=segments,
        tool_radius=tool_radius,
        include_rapids=include_rapids,
        cut_z_max=cut_z_max,
        simplify_tol=simplify_tol,
        round_joins=round_joins,
    )


def _polygon_shell(poly: Polygon) -> Polygon:
    return Polygon(poly.exterior)


def _remove_contained_polygons(
    polygons: List[Polygon], containment_tol: float = 0.001
) -> List[Polygon]:
    """
    Remove polygons that are contained within a larger polygon.
    Keeps only top-level outer shells.
    """
    shells = [_polygon_shell(p) for p in polygons]
    shells.sort(key=lambda p: p.area, reverse=True)

    kept: List[Polygon] = []
    for poly in shells:
        representative = poly.representative_point()
        is_contained = False
        for bigger in kept:
            if bigger.buffer(containment_tol).contains(representative):
                is_contained = True
                break
        if not is_contained:
            kept.append(poly)

    return _sort_polygons(kept)
