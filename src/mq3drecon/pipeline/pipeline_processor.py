from pathlib import Path
from mq3drecon.config.pipeline_configs import PipelineConfigs
from mq3drecon.dataio.data_io import DataIO
from mq3drecon.processing.depth_conversion.convert_depth_to_linear import convert_depth_directory
from mq3drecon.processing.yuv_conversion.convert_yuv_dir import convert_yuv_directory


class PipelineProcessor:
    def __init__(self, project_dir: Path, config_yml_path: Path):
        self.data_io = DataIO(project_dir=project_dir)
        self.pipeline_configs = PipelineConfigs.parse_config_yml(config_yml_path)


    def convert_yuv_to_rgb(self):
        convert_yuv_directory(image_io=self.data_io.color, config=self.pipeline_configs.yuv_to_rgb)

    
    def convert_depth_to_linear(self):
        convert_depth_directory(depth_data_io=self.data_io.depth, depth_to_linear_config=self.pipeline_configs.depth_to_linear)


    def reconstruct_scene(self):
        from mq3drecon.processing.reconstruction.reconstruct_scene import reconstruct_scene

        reconstruct_scene(data_io=self.data_io, config=self.pipeline_configs.reconstruction)