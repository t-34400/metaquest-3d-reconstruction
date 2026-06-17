"""Dataset readiness helpers for package workflows."""

from dataclasses import dataclass
from pathlib import Path

from mq3drecon.layouts import LegacyProjectLayout
from mq3drecon.models import Side


@dataclass(frozen=True)
class RgbImageStatus:
    """Summary of RGB images available in a legacy project layout."""

    project_dir: Path
    left_dir: Path
    right_dir: Path
    left_count: int
    right_count: int

    @property
    def has_left(self) -> bool:
        return self.left_count > 0

    @property
    def has_right(self) -> bool:
        return self.right_count > 0

    @property
    def is_complete(self) -> bool:
        return self.has_left and self.has_right

    @property
    def is_balanced(self) -> bool:
        return self.left_count == self.right_count

    def count_for(self, side: Side) -> int:
        if side == Side.LEFT:
            return self.left_count
        if side == Side.RIGHT:
            return self.right_count
        raise ValueError(f"Unsupported side: {side!r}")

    def directory_for(self, side: Side) -> Path:
        if side == Side.LEFT:
            return self.left_dir
        if side == Side.RIGHT:
            return self.right_dir
        raise ValueError(f"Unsupported side: {side!r}")


def get_rgb_image_status(project_dir: Path) -> RgbImageStatus:
    layout = LegacyProjectLayout(project_dir=project_dir)
    left_dir = layout.image.get_rgb_dir(Side.LEFT)
    right_dir = layout.image.get_rgb_dir(Side.RIGHT)

    return RgbImageStatus(
        project_dir=Path(project_dir),
        left_dir=left_dir,
        right_dir=right_dir,
        left_count=len(layout.image.get_rgb_image_paths(Side.LEFT)),
        right_count=len(layout.image.get_rgb_image_paths(Side.RIGHT)),
    )


def has_rgb_images(project_dir: Path) -> bool:
    return get_rgb_image_status(project_dir).is_complete
