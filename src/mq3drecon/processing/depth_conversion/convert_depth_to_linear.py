from tqdm import tqdm
import numpy as np
from mq3drecon.config.depth_to_linear_config import Depth2LinearConfig
from mq3drecon.dataio.depth_data_io import DepthDataIO
from mq3drecon.models.side import Side


def convert_depth_directory(
    depth_data_io: DepthDataIO,
    depth_to_linear_config: Depth2LinearConfig
):
    for side in Side:
        dataset = depth_data_io.load_depth_dataset(side=side, use_cache=depth_to_linear_config.use_cache)

        num_frames = len(dataset.timestamps)

        for i in tqdm(range(num_frames), total=num_frames, desc="Converting depth images"):
            timestamp = dataset.timestamps[i]
            width = dataset.widths[i]
            height = dataset.heights[i]
            near = dataset.nears[i]
            far = dataset.fars[i]

            depth_map = depth_data_io.load_depth_map(
                side=side,
                timestamp=timestamp,
                width=width,
                height=height,
                near=near,
                far=far,
            )

            if depth_map is None:
                continue

            clip_near = depth_to_linear_config.clip_near_m
            clip_far = depth_to_linear_config.clip_far_m
            linear_depth_map = np.clip((depth_map - clip_near) / (clip_far - clip_near), 0, 1) * 255.0

            depth_data_io.save_linear_depth_map(
                depth_map=linear_depth_map,
                side=side,
                timestamp=timestamp
            )

        print(f"[Info] Converted depth images for {side} camera to linear format.")