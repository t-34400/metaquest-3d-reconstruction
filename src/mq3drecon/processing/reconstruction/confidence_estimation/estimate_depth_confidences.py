
from typing import Optional
import numpy as np
from mq3drecon.config.reconstruction_config import DepthConfidenceEstimationConfig
from mq3drecon.dataio.depth_data_io import DepthDataIO
from mq3drecon.models.camera_dataset import DepthDataset
from mq3drecon.models.confidence_map import ConfidenceMap
from mq3drecon.models.side import Side
from mq3drecon.models.transforms import CoordinateSystem
from mq3drecon.processing.reconstruction.confidence_estimation.compute_pixel_error_map import compute_pixel_error_map
from mq3drecon.processing.reconstruction.utils.o3d_utils import compute_o3d_intrinsic_matrices
from mq3drecon.utils.paralell_utils import parallel_map


def build_confidence_map(
    depth_data_io: DepthDataIO,
    dataset: DepthDataset,
    intrinsic_matrices: np.ndarray,
    extrinsic_matrices: np.ndarray,
    extrinsic_matrices_inv: np.ndarray,
    side: Side,
    ref_frame_idx: int,
    target_frame_range: int = 10,
    depth_max: float = 3.0,
    error_threshold: float = 0.05
) -> Optional[ConfidenceMap]:
    ref_depth_map = depth_data_io.load_depth_map_by_index(
        side=side,
        dataset=dataset,
        index=ref_frame_idx    
    )
    if ref_depth_map is None:
        return None

    min_index_inclusive = max(0, ref_frame_idx - target_frame_range)
    max_index_exclusive = min(len(dataset), ref_frame_idx + target_frame_range + 1)
    target_frame_indices = sorted(
        [i for i in range(min_index_inclusive, max_index_exclusive) if i != ref_frame_idx]
    )

    h, w = ref_depth_map.shape
    consistent_count = np.zeros((h, w), dtype=np.int32)
    valid_count = np.zeros((h, w), dtype=np.int32)

    for target_frame_idx in target_frame_indices:
        target_depth_map = depth_data_io.load_depth_map_by_index(
            side=side,
            dataset=dataset,
            index=target_frame_idx
        )

        if target_depth_map is None:
            continue

        error_map = compute_pixel_error_map(
            intrinsic_matrices=intrinsic_matrices,
            extrinsic_matrices=extrinsic_matrices,
            extrinsic_matrices_inv=extrinsic_matrices_inv,
            ref_frame_idx=ref_frame_idx,
            ref_depth_map=ref_depth_map,
            target_frame_idx=target_frame_idx,
            target_depth_map=target_depth_map,
            depth_max=depth_max
        )

        valid_mask = ~np.isnan(error_map)
        consistent_mask = valid_mask & (error_map <= error_threshold)

        valid_count += valid_mask.astype(np.int32)
        consistent_count += consistent_mask.astype(np.int32)

    with np.errstate(divide='ignore', invalid='ignore'):
        confidence_map = np.true_divide(consistent_count, valid_count)
        confidence_map[valid_count == 0] = 0.0  # Avoid division by zero

    return ConfidenceMap(
        confidence_map=confidence_map,
        valid_count=valid_count
    )


def build_and_save_confidence_map(
    depth_data_io: DepthDataIO,
    dataset: DepthDataset,
    intrinsic_matrices: np.ndarray,
    extrinsic_matrices: np.ndarray,
    extrinsic_matrices_inv: np.ndarray,
    side: Side,
    ref_frame_idx: int,
    config: DepthConfidenceEstimationConfig
):
    timestamp = dataset.timestamps[ref_frame_idx]

    confidence_map = depth_data_io.load_confidence_map(side=side, timestamp=timestamp)
    if confidence_map is not None:
        return

    confidence_map = build_confidence_map(
        depth_data_io=depth_data_io,
        dataset=dataset,
        intrinsic_matrices=intrinsic_matrices,
        extrinsic_matrices=extrinsic_matrices,
        extrinsic_matrices_inv=extrinsic_matrices_inv,
        side=side,
        ref_frame_idx=ref_frame_idx,
        target_frame_range=config.target_frame_range,
        depth_max=config.depth_max,
        error_threshold=config.error_threshold
    )

    if confidence_map is not None:
        depth_data_io.save_confidence_map(side=side, timestamp=timestamp, confidence_map=confidence_map)


def estimate_depth_confidences(
    depth_data_io: DepthDataIO,
    config: DepthConfidenceEstimationConfig,
):
    for side in Side:
        if config.skip_if_output_dir_exists and depth_data_io.exists_depth_confidence_map_dir(side=side):
            print(f"[{side.name}] Skipping confidence map estimation: output directory already exists. Set skip_if_output_dir_exists = False to force re-estimation.")
            continue

        dataset = depth_data_io.load_depth_dataset(side=side)

        intrinsic_matrices = compute_o3d_intrinsic_matrices(dataset=dataset)
        extrinsic_matrices = dataset.transforms.convert_coordinate_system(
            target_coordinate_system=CoordinateSystem.OPEN3D,
            is_camera=True
        ).extrinsics_cw
        extrinsic_matrices_inv = np.linalg.inv(extrinsic_matrices)

        args_list = [
            (
                depth_data_io, dataset, 
                intrinsic_matrices, extrinsic_matrices, extrinsic_matrices_inv, 
                side, ref_frame_idx, config
            )
            for ref_frame_idx in range(len(dataset))
        ]

        parallel_map(
            build_and_save_confidence_map,
            args_list=args_list,
            max_workers=None,
            use_multiprocessing=config.use_multi_threading,
            show_progress=True,
            desc=f"[{side.name}] Estimating depth confidence maps ..."
        )