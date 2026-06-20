from __future__ import annotations

import logging
import traceback

import cv2
from tqdm import tqdm

from mq3drecon.dataio.mruk_image_data_io import MRUKImageDataIO
from mq3drecon.errors import ProcessingError
from mq3drecon.models.side import Side

logger = logging.getLogger(__name__)


def _timestamp_from_file_name(file_name: str) -> int:
    stem = file_name.rsplit(".", 1)[0]
    return int(stem)


def _save_rgba_png(mruk_image_io: MRUKImageDataIO, side: Side, file_name: str, width: int, height: int) -> None:
    rgba = mruk_image_io.load_rgba(side=side, file_name=file_name, width=width, height=height)
    output = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA)
    path = mruk_image_io.image_path_config.get_mruk_rgba_png_path(side=side, timestamp=_timestamp_from_file_name(file_name))
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), output):
        raise OSError(f"Failed to write MRUK RGBA PNG: {path}")


def convert_rgba_directory(mruk_image_io: MRUKImageDataIO) -> None:
    failures: list[str] = []

    for side in Side:
        metadata = mruk_image_io.load_frame_metadata(side)
        processed_count = 0

        for row in tqdm(metadata.itertuples(index=False), total=len(metadata), desc=f"Converting MRUK RGBA to PNG ({side})"):
            file_name = str(row.file_name)
            try:
                _save_rgba_png(
                    mruk_image_io=mruk_image_io,
                    side=side,
                    file_name=file_name,
                    width=int(row.width),
                    height=int(row.height),
                )
                processed_count += 1
            except Exception:
                failures.append(f"Failed in {side}/{file_name}:\n{traceback.format_exc()}")

        logger.info(
            "%s MRUK RGBA PNG images written to %s",
            processed_count,
            mruk_image_io.image_path_config.get_mruk_rgba_png_dir(side),
        )

    if failures:
        logger.error("MRUK RGBA conversion failures:\n%s", "\n".join(failures))
        raise ProcessingError(f"{len(failures)} files failed during MRUK RGBA conversion")
