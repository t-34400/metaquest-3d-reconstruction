import argparse
from pathlib import Path

from _bootstrap import add_src_to_path

add_src_to_path()

from mq3drecon.workflows import run_depth_to_linear


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


def main(args) -> None:
    print("[Info] Converting depth to linear map...")
    run_depth_to_linear(project_dir=args.project_dir, config_yml_path=args.config)
    print("[Info] Conversion completed.")


if __name__ == "__main__":
    args = parse_args()

    print(f"[Info] Project Directory: {args.project_dir}")
    main(args)
