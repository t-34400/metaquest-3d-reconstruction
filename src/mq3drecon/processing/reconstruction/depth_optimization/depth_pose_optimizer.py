from tqdm import tqdm
from mq3drecon.config.reconstruction_config import ReconstructionConfig
from mq3drecon.dataio.depth_data_io import DepthDataIO
from mq3drecon.dataio.reconstruction_data_io import ReconstructionDataIO
from mq3drecon.models.camera_dataset import DepthDataset
from mq3drecon.models.side import Side
from mq3drecon.models.transforms import CoordinateSystem
from mq3drecon.processing.reconstruction.depth_optimization.make_fragments import make_fragment_datasets
from mq3drecon.processing.reconstruction.depth_optimization.refine_fragment_poses import refine_fragment_poses
from mq3drecon.processing.reconstruction.utils.log_utils import log_step


def merge_fragment_datasets(frag_dataset_map: dict[Side, list[DepthDataset]]) -> dict[Side, DepthDataset]:
    dataset_map: dict[Side, DepthDataset] = {}

    for side, frag_datasets in frag_dataset_map.items():
        dataset_map[side] = DepthDataset.merge(frag_datasets)

    return dataset_map


class DepthPoseOptimizer:
    def __init__(self, 
        depth_data_io: DepthDataIO, 
        recon_data_io: ReconstructionDataIO, 
        config: ReconstructionConfig
    ):
        self.depth_data_io = depth_data_io
        self.recon_data_io = recon_data_io
        self.config = config


    def __call__(self) -> dict[Side, DepthDataset]:
        return self.load_or_optimize_dataset()

    
    def load_or_make_fragment_datasets(self) -> dict[Side, list[DepthDataset]]:
        if self.config.use_fragment_dataset_cache:
            frag_dataset_map = self.recon_data_io.load_fragment_datasets()

            if len(frag_dataset_map) > 0 and any([len(frag_datasets) > 0 for frag_datasets in frag_dataset_map.values()]):
                print("[Info] Fragment datasets loaded from cache.")

                for side, datasets in frag_dataset_map.items():
                    for dataset in datasets:
                        if dataset.transforms.coordinate_system != CoordinateSystem.OPEN3D:
                            dataset.transforms = dataset.transforms.convert_coordinate_system(CoordinateSystem.OPEN3D)

                return frag_dataset_map
        
        log_step("Make Fragments")
        frag_dataset_map = make_fragment_datasets(depth_data_io=self.depth_data_io, config=self.config.fragment_generation)

        print("[Info] Saving fragment datasets to cache...")
        for side, frag_datasets in frag_dataset_map.items():
            for i, frag_dataset in enumerate(tqdm(frag_datasets, desc=f"[{side.name}] Saving fragment datasets...")):
                self.recon_data_io.save_fragment_dataset(dataset=frag_dataset, side=side, index=i)
        print("[Info] Fragment datasets saved successfully.")

        return frag_dataset_map
    

    def load_or_optimize_dataset(self) -> dict[Side, DepthDataset]:
        if self.config.use_optimized_dataset_cache:
            optimized_dataset_loaded = False
            optimized_dataset: dict[Side, DepthDataset] = {}

            for side in Side:
                dataset = self.depth_data_io.load_optimized_depth_dataset(side=side)

                if dataset is not None:
                    optimized_dataset[side] = dataset
                    optimized_dataset_loaded = True

            if optimized_dataset_loaded:
                print("[Info] Optimized depth datasets loaded.")
                return optimized_dataset

        frag_dataset_map = self.load_or_make_fragment_datasets()
        
        log_step("Refine Fragment poses")

        refine_fragment_poses(
            depth_data_io=self.depth_data_io,
            recon_data_io=self.recon_data_io,
            fragment_dataset_map=frag_dataset_map,
            config=self.config.fragment_pose_refinement
        )

        optimized_dataset_map = merge_fragment_datasets(frag_dataset_map=frag_dataset_map)

        print("[Info] Saving Optimized depth datasets to cache...")
        for side, dataset in optimized_dataset_map.items():
            self.depth_data_io.save_optimized_depth_dataset(
                side=side,
                dataset=dataset
            )
        print("[Info] Optimized depth datasets saved successfully.")

        return optimized_dataset_map