import argparse
from pathlib import Path
import sys

from _bootstrap import add_src_to_path

add_src_to_path()

from mq3drecon.errors import MQ3DReconError
from mq3drecon.workflows import export_colmap_project


def parse_args():
    parser = argparse.ArgumentParser(description="Export camera and image data to COLMAP format.")

    parser.add_argument(
        "--project_dir", "-p",
        type=Path,
        required=True,
        help="Path to the project directory containing QRC data.",
    )
    parser.add_argument(
        "--output_dir", "-o",
        type=Path,
        required=True,
        help="Path to the output directory where COLMAP model files will be saved.",
    )
    parser.add_argument(
        "--use_colored_pointcloud",
        action="store_true",
        help="Include colored 3D point cloud if available.",
    )
    parser.add_argument(
        "--use_optimized_color_dataset",
        action="store_true",
        help="Use optimized color datasets if available.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=1,
        help="Sampling interval for image export. Use every N-th image.",
    )

    return parser.parse_args()


def main(args) -> int:
    try:
        if not args.output_dir.exists():
            print(f"[Info] Output directory does not exist. Creating: {args.output_dir}")

        print(f"[Info] Project directory: {args.project_dir}")
        print(f"[Info] Output COLMAP project will be saved to: {args.output_dir}")

        export_colmap_project(
            project_dir=args.project_dir,
            output_dir=args.output_dir,
            use_colored_pointcloud=args.use_colored_pointcloud,
            use_optimized_color_dataset=args.use_optimized_color_dataset,
            interval=args.interval,
        )
        return 0
    except (MQ3DReconError, FileNotFoundError, ValueError, OSError) as exc:
        print(f"[Error] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(parse_args()))
