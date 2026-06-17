import argparse
import sys
from pathlib import Path

from _bootstrap import add_src_to_path

add_src_to_path()

from mq3drecon.workflows import run_visualize_camera_trajectories


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project_dir", "-p",
        type=Path,
        required=True,
        help="Path to the project directory containing QRC data."
    )
    args = parser.parse_args()

    if not args.project_dir.is_dir():
        parser.error(f"Input directory does not exist: {args.project_dir}")

    return args


def main(args):
    run_visualize_camera_trajectories(project_dir=args.project_dir)


if __name__ == "__main__":
    args = parse_args()

    print(f"[Info] Project Directory: {args.project_dir}")
    try:
        main(args)
    except (OSError, ValueError) as exc:
        print(f"[Error] {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
