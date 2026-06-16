from pathlib import Path
import sys


def add_src_to_path() -> None:
    src_dir = Path(__file__).resolve().parents[1] / "src"
    if src_dir.exists():
        sys.path.insert(0, str(src_dir))
