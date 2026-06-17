import argparse
from pathlib import Path
import sys

from _bootstrap import add_src_to_path

add_src_to_path()

from mq3drecon.errors import MQ3DReconError
from mq3drecon.workflows import run_yuv_to_rgb


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project_dir", "-p",
        type=Path,
        required=True,
        help="Path to the project directory containing QRC data."
    )
    parser.add_argument(
        "--config", "-c",
        type=Path,
        default=Path("config/pipeline_config.yml"),
        help="Path to the YAML config file for the pipeline"
    )
    args = parser.parse_args()

    if not args.project_dir.is_dir():
        parser.error(f"Input directory does not exist: {args.project_dir}")

    return args


def main(args) -> int:
    try:
        print("[Info] Converting YUV to RGB...")
        run_yuv_to_rgb(project_dir=args.project_dir, config_yml_path=args.config)
        print("[Info] Conversion completed.")
        return 0
    except (MQ3DReconError, FileNotFoundError, ValueError, OSError) as exc:
        print(f"[Error] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    args = parse_args()

    print(f"[Info] Project Directory: {args.project_dir}")
    raise SystemExit(main(args))
