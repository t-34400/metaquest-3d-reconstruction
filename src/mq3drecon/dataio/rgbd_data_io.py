import numpy as np
from mq3drecon.dataio.depth_data_io import DepthDataIO
from mq3drecon.dataio.image_data_io import ImageDataIO
from mq3drecon.config.project_path_config import RGBDPathConfig
from mq3drecon.models.side import Side


class RGBDDataIO:
    def __init__(self,
        image_data_io: ImageDataIO,
        depth_data_io: DepthDataIO,
        rgbd_path_config: RGBDPathConfig
    ):
        self.image_data_io = image_data_io
        self.depth_data_io = depth_data_io
        self.rgbd_path_config = rgbd_path_config

    
    def load_color_aligned_depth(self, side: Side, timestamp: int) -> np.ndarray:
        color_aligned_depth_path = self.rgbd_path_config.get_color_aligned_depth_path(side=side, timestamp=timestamp)
        
        if not color_aligned_depth_path.exists():
            raise FileNotFoundError(f"Color-aligned depth file not found: {color_aligned_depth_path}")
        
        return np.load(color_aligned_depth_path)
    

    def save_color_aligned_depth(self, depth_map: np.ndarray, side: Side, timestamp: int):
        color_aligned_depth_path = self.rgbd_path_config.get_color_aligned_depth_path(side=side, timestamp=timestamp)
        color_aligned_depth_path.parent.mkdir(parents=True, exist_ok=True)

        np.save(color_aligned_depth_path, depth_map)