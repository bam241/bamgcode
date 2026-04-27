from __future__ import annotations

import argparse

from .gcodeio import read_multiple_gcode_files, write_outline_gcode
from .manipulation import lines_to_envelope_polygon


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gcode-envelope",
        description="Generate a hover G-code file following the exact outer toolpath envelope.",
    )
    parser.add_argument("input_files", nargs="+", help="Input G-code files")
    parser.add_argument("-o", "--output", required=True, help="Output G-code file")
    parser.add_argument(
        "--hover-z", type=float, default=1.0, help="Outline hover Z height"
    )
    parser.add_argument(
        "--clearance-z", type=float, default=5.0, help="Safe travel Z height"
    )
    parser.add_argument(
        "--feed-rate", type=float, default=1200.0, help="Feed rate for outline"
    )
    parser.add_argument(
        "--tool-radius", type=float, default=0.0, help="Tool radius for swept envelope"
    )
    parser.add_argument(
        "--include-rapids",
        action="store_true",
        help="Include G0 moves in the envelope",
    )
    parser.add_argument(
        "--cut-z-max",
        type=float,
        default=0.0,
        help="Include only segments whose average Z is <= this value; use a large number to include more",
    )
    parser.add_argument(
        "--arc-segment-deg",
        type=float,
        default=3.0,
        help="Arc interpolation angular step in degrees",
    )
    parser.add_argument(
        "--simplify-tol",
        type=float,
        default=0.01,
        help="Simplification tolerance for final polygon",
    )
    parser.add_argument(
        "--units",
        choices=["mm", "inch"],
        default="mm",
        help="Output units",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    lines = read_multiple_gcode_files(args.input_files)

    polygon = lines_to_envelope_polygon(
        lines=lines,
        tool_radius=args.tool_radius,
        include_rapids=args.include_rapids,
        cut_z_max=args.cut_z_max,
        arc_segment_deg=args.arc_segment_deg,
        simplify_tol=args.simplify_tol,
    )

    write_outline_gcode(
        polygon=polygon,
        output_file=args.output,
        hover_z=args.hover_z,
        clearance_z=args.clearance_z,
        feed_rate=args.feed_rate,
        units=args.units,
    )


if __name__ == "__main__":
    main()
