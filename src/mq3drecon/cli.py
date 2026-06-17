"""Command-line entrypoint for package-backed MQ3DRecon workflows."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from mq3drecon.errors import MQ3DReconError
from mq3drecon.workflows import (
    export_colmap_project,
    run_depth_to_linear,
    run_reconstruct_scene,
    run_visualize_camera_trajectories,
    run_yuv_to_rgb,
)

_EXPECTED_ERRORS = (MQ3DReconError, FileNotFoundError, ValueError, OSError)


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
