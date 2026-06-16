from concurrent.futures import ProcessPoolExecutor, as_completed
import traceback
from typing import Callable, Optional

import numpy as np
from tqdm import tqdm
from mq3drecon.config.yuv_to_rgb_config import Yuv2RgbConfig
from mq3drecon.dataio.image_data_io import ImageDataIO
from mq3drecon.models.side import Side
from mq3drecon.utils.image_utils import convert_yuv420_888_to_bgr, is_blur_image, is_over_or_under_exposed


def process_file(
    side: Side,
    timestamp: int,
    image_io: ImageDataIO,
    filter: Optional[Callable[[np.ndarray], bool]] = None,
) -> bool:
    try:
        raw_data = image_io.load_yuv(side=side, timestamp=timestamp)
        format_info = image_io.load_image_format_info(side=side)

        bgr_img = convert_yuv420_888_to_bgr(raw_data=raw_data, format_info=format_info)

        if filter is not None:
            if not filter(bgr_img):
                return False
            
        image_io.save_bgr(bgr=bgr_img, side=side, timestamp=timestamp)

        return True

    except Exception:
        raise RuntimeError(f"Failed in {side}/{timestamp}:\n{traceback.format_exc()}")
    


class FilterFn:
    def __init__(self, config: Yuv2RgbConfig):
        self.config = config


    def __call__(self, bgr_img: np.ndarray) -> bool:
        if self.config.blur_filter and is_blur_image(bgr_img, blur_threshold=self.config.blur_threshold):
            return False
        if self.config.exposure_filter and is_over_or_under_exposed(
            bgr_img,
            low_thresh=self.config.exposure_threshold_low,
            high_thresh=self.config.exposure_threshold_high,
        ):
            return False
        return True


def convert_yuv_directory(
    image_io: ImageDataIO,
    config: Yuv2RgbConfig
):
    filter = FilterFn(config=config)

    for side in Side:
        yuv_timestamps = image_io.get_yuv_timestamps(side)

        excluded_count = 0
        processed_count = 0
        exception_count = 0

        with ProcessPoolExecutor() as executor:
            futures = [
                executor.submit(process_file, side, yuv_timestamp, image_io, filter)
                for yuv_timestamp in yuv_timestamps
            ]
            for future in tqdm(as_completed(futures), total=len(futures), desc=f"Converting YUV to PNG ({side})"):
                try:
                    result = future.result()
                    if result:
                        processed_count += 1
                    else:
                        excluded_count += 1

                except Exception as e:
                    print(f"[Exception] Worker failed: {e}")
                    exception_count += 1
                    continue            

        print(f"[Info] {processed_count} images written to {image_io.image_path_config.get_rgb_dir(side)}")

        if excluded_count > 0:
            print(f"[Info] {excluded_count} images were excluded by filtering.")

        if exception_count > 0:
            print(f"[Error] {exception_count} files failed due to exceptions.")