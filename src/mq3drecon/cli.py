"""Command-line entrypoint for package-backed MQ3DRecon workflows."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from mq3drecon.errors import MQ3DReconError
from mq3drecon.models.side import Side
from mq3drecon.workflows import (
    export_colmap_project,
    run_color_aligned_depth_to_png,
    run_foundation_stereo_depth,
    run_depth_to_linear,
    run_reconstruct_scene,
    run_rgba_to_png,
    run_visualize_camera_trajectories,
    run_yuv_to_rgb,
)

_EXPECTED_ERRORS = (MQ3DReconError, FileNotFoundError, ValueError, OSError)



def _parse_side(value: str) -> Side:
    try:
        return Side[str(value).upper()]
    except KeyError as exc:
        raise argparse.ArgumentTypeError("side must be one of: left, right") from exc

def _existing_project_dir(value: str) -> Path:
    path = Path(value)
    if not path.is_dir():
        raise argparse.ArgumentTypeError(f"Input directory does not exist: {path}")
    return path


def _add_project_and_config_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--project-dir",
        "--project_dir",
        "-p",
        type=_existing_project_dir,
        required=True,
        help="Path to the project directory containing QRC data.",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=None,
        help="Optional path to the YAML config file for the pipeline. Uses built-in defaults when omitted.",
    )


def _run_yuv_to_rgb(args: argparse.Namespace) -> int:
    run_yuv_to_rgb(project_dir=args.project_dir, config_yml_path=args.config)
    return 0


def _run_depth_to_linear(args: argparse.Namespace) -> int:
    run_depth_to_linear(project_dir=args.project_dir, config_yml_path=args.config)
    return 0


def _run_rgba_to_png(args: argparse.Namespace) -> int:
    run_rgba_to_png(project_dir=args.project_dir)
    return 0


def _run_foundation_stereo_depth(args: argparse.Namespace) -> int:
    run_foundation_stereo_depth(
        project_dir=args.project_dir,
        model_path=args.model_path,
        config_yml_path=args.config,
    )
    return 0



def _run_color_aligned_depth_to_png(args: argparse.Namespace) -> int:
    result = run_color_aligned_depth_to_png(
        project_dir=args.project_dir,
        side=args.side,
        write_metric_png=args.metric,
        write_preview_png=not args.no_preview,
        depth_png_scale=args.depth_png_scale,
        depth_preview_min_m=args.depth_preview_min_m,
        depth_preview_max_m=args.depth_preview_max_m,
    )
    print(
        f"[Info] Exported {result.preview_png_count} preview PNG(s) "
        f"and {result.metric_png_count} metric PNG(s) for {result.side.name}."
    )
    return 0

def _run_reconstruct(args: argparse.Namespace) -> int:
    run_reconstruct_scene(project_dir=args.project_dir, config_yml_path=args.config)
    return 0


def _run_export_colmap(args: argparse.Namespace) -> int:
    export_colmap_project(
        project_dir=args.project_dir,
        output_dir=args.output_dir,
        use_colored_pointcloud=args.use_colored_pointcloud,
        use_optimized_color_dataset=args.use_optimized_color_dataset,
        interval=args.interval,
    )
    return 0


def _run_visualize_cameras(args: argparse.Namespace) -> int:
    run_visualize_camera_trajectories(project_dir=args.project_dir)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mq3drecon", description="Meta Quest 3D reconstruction toolkit.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    yuv_parser = subparsers.add_parser("yuv-to-rgb", help="Convert captured YUV frames to RGB images.")
    _add_project_and_config_arguments(yuv_parser)
    yuv_parser.set_defaults(handler=_run_yuv_to_rgb)

    depth_parser = subparsers.add_parser("depth-to-linear", help="Convert depth frames to linear depth maps.")
    _add_project_and_config_arguments(depth_parser)
    depth_parser.set_defaults(handler=_run_depth_to_linear)

    rgba_parser = subparsers.add_parser("rgba-to-png", help="Convert MRUK RGBA frames to PNG images.")
    rgba_parser.add_argument(
        "--project-dir",
        "--project_dir",
        "-p",
        type=_existing_project_dir,
        required=True,
        help="Path to the project directory containing MRUK RGBA data.",
    )
    rgba_parser.set_defaults(handler=_run_rgba_to_png)

    stereo_parser = subparsers.add_parser(
        "foundation-stereo-depth",
        help="Generate rectified stereo depth maps with a FoundationStereo ONNX model.",
    )
    _add_project_and_config_arguments(stereo_parser)
    stereo_parser.add_argument(
        "--model-path",
        "--model_path",
        type=Path,
        default=None,
        help="Path to the FoundationStereo ONNX model. Required unless supplied by config.",
    )
    stereo_parser.set_defaults(handler=_run_foundation_stereo_depth)


    color_aligned_depth_parser = subparsers.add_parser(
        "color-aligned-depth-to-png",
        help="Export saved color-aligned depth .npy maps to PNG files for inspection.",
    )
    color_aligned_depth_parser.add_argument(
        "--project-dir",
        "--project_dir",
        "-p",
        type=_existing_project_dir,
        required=True,
        help="Path to the project directory containing color-aligned depth maps.",
    )
    color_aligned_depth_parser.add_argument(
        "--side",
        type=_parse_side,
        default=Side.LEFT,
        help="Camera side to export. Defaults to left.",
    )
    color_aligned_depth_parser.add_argument(
        "--metric",
        action="store_true",
        help="Also write 16-bit metric depth PNG files using --depth-png-scale units per meter.",
    )
    color_aligned_depth_parser.add_argument(
        "--no-preview",
        action="store_true",
        help="Disable 8-bit visual preview PNG output.",
    )
    color_aligned_depth_parser.add_argument(
        "--depth-png-scale",
        type=float,
        default=1000.0,
        help="Scale factor for 16-bit metric PNG output. Defaults to millimeters.",
    )
    color_aligned_depth_parser.add_argument(
        "--depth-preview-min-m",
        type=float,
        default=0.1,
        help="Minimum depth in meters mapped to black for preview PNG output.",
    )
    color_aligned_depth_parser.add_argument(
        "--depth-preview-max-m",
        type=float,
        default=None,
        help="Maximum depth in meters mapped to white for preview PNG output. Defaults to a deterministic percentile.",
    )
    color_aligned_depth_parser.set_defaults(handler=_run_color_aligned_depth_to_png)

    reconstruct_parser = subparsers.add_parser("reconstruct", help="Run the reconstruction pipeline.")
    _add_project_and_config_arguments(reconstruct_parser)
    reconstruct_parser.set_defaults(handler=_run_reconstruct)

    colmap_parser = subparsers.add_parser("export-colmap", help="Export camera and image data to COLMAP format.")
    colmap_parser.add_argument(
        "--project-dir",
        "--project_dir",
        "-p",
        type=_existing_project_dir,
        required=True,
        help="Path to the project directory containing QRC data.",
    )
    colmap_parser.add_argument(
        "--output-dir",
        "--output_dir",
        "-o",
        type=Path,
        required=True,
        help="Path to the output directory where COLMAP model files will be saved.",
    )
    colmap_parser.add_argument(
        "--use-colored-pointcloud",
        "--use_colored_pointcloud",
        action="store_true",
        help="Include colored 3D point cloud if available.",
    )
    colmap_parser.add_argument(
        "--use-optimized-color-dataset",
        "--use_optimized_color_dataset",
        action="store_true",
        help="Use optimized color datasets if available.",
    )
    colmap_parser.add_argument(
        "--interval",
        type=int,
        default=1,
        help="Sampling interval for image export. Use every N-th image.",
    )
    colmap_parser.set_defaults(handler=_run_export_colmap)

    visualize_parser = subparsers.add_parser("visualize-cameras", help="Visualize camera trajectories.")
    visualize_parser.add_argument(
        "--project-dir",
        "--project_dir",
        "-p",
        type=_existing_project_dir,
        required=True,
        help="Path to the project directory containing QRC data.",
    )
    visualize_parser.set_defaults(handler=_run_visualize_cameras)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler: Callable[[argparse.Namespace], int] = args.handler

    try:
        return handler(args)
    except _EXPECTED_ERRORS as exc:
        print(f"[Error] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
