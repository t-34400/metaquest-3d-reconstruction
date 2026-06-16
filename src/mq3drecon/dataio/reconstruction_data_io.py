from typing import Optional
import open3d as o3d

from mq3drecon.config.project_path_config import ReconstructionPathConfig
from mq3drecon.models.camera_dataset import DepthDataset
from mq3drecon.models.side import Side


class ReconstructionDataIO:
    def __init__(self, reconstruction_path_config: ReconstructionPathConfig):
        self.reconstruction_path_config = reconstruction_path_config


    def load_fragment_datasets(self) -> dict[Side, list[DepthDataset]]:
        fragment_path_map = self.reconstruction_path_config.get_fragment_dataset_paths()

        fragment_datasets: dict[Side, list[DepthDataset]] = {}

        for side, paths in fragment_path_map.items():
            fragment_datasets[side] = [DepthDataset.load(path) for path in paths]

        return fragment_datasets    

    
    def save_fragment_dataset(self, dataset: DepthDataset, side: Side, index: int):
        path = self.reconstruction_path_config.get_fragment_dataset_path(side=side, index=index)
        path.parent.mkdir(parents=True, exist_ok=True)
        dataset.save(path)

    
    def load_fragment_pcd(self, side: Side, index: int) -> o3d.t.geometry.PointCloud:
        path = self.reconstruction_path_config.get_fragment_pcd_path(side=side, index=index)
        return o3d.t.io.read_point_cloud(str(path))
    

    def save_fragment_pcd(self, pcd: o3d.t.geometry.PointCloud, side: Side, index: int):
        path = self.reconstruction_path_config.get_fragment_pcd_path(side=side, index=index)
        path.parent.mkdir(parents=True, exist_ok=True)
        o3d.t.io.write_point_cloud(str(path), pcd, write_ascii=False, compressed=True)


    def load_colorless_vbg(self) -> Optional[o3d.t.geometry.VoxelBlockGrid]:
        colorless_vbg_path = self.reconstruction_path_config.get_colorless_vbg_path()

        if not colorless_vbg_path.exists():
            return None
        
        return o3d.t.geometry.VoxelBlockGrid.load(str(colorless_vbg_path))
    

    def save_colorless_vbg(self, vbg: o3d.t.geometry.VoxelBlockGrid):
        colorless_vbg_path = self.reconstruction_path_config.get_colorless_vbg_path()
        colorless_vbg_path.parent.mkdir(parents=True, exist_ok=True)

        vbg.save(str(colorless_vbg_path))


    def load_colored_mesh(self) -> Optional[o3d.t.geometry.TriangleMesh]:
        color_mesh_path = self.reconstruction_path_config.get_colored_mesh_path()

        if not color_mesh_path.exists():
            return None
        
        return o3d.t.io.read_triangle_mesh(str(color_mesh_path))
    

    def save_colored_mesh_legacy(self, mesh: o3d.geometry.TriangleMesh):
        color_mesh_path = self.reconstruction_path_config.get_colored_mesh_path()
        color_mesh_path.parent.mkdir(parents=True, exist_ok=True)

        o3d.io.write_triangle_mesh(str(color_mesh_path), mesh)
    

    def save_colored_mesh(self, mesh: o3d.t.geometry.TriangleMesh):
        color_mesh_path = self.reconstruction_path_config.get_colored_mesh_path()
        color_mesh_path.parent.mkdir(parents=True, exist_ok=True)

        o3d.t.io.write_triangle_mesh(str(color_mesh_path), mesh)


    def load_colored_pcd(self, device: o3d.core.Device = o3d.core.Device("CPU:0"), print_progress: bool = True) -> Optional[o3d.t.geometry.PointCloud]:
        color_pcd_path = self.reconstruction_path_config.get_colored_pcd_path()

        if not color_pcd_path.exists():
            return None

        # TODO: remove_nan_points and remove_infinite_points are currently unimplemented in Open3D Tensor API.
        #       Once Open3D adds support, restore the options below to clean up invalid points on load.
        #       See: https://github.com/isl-org/Open3D/issues (check for future support)
        #
        # return o3d.t.io.read_point_cloud(
        #     filename=str(color_pcd_path),
        #     remove_nan_points=True,
        #     remove_infinite_points=True,
        # ).to(device=device)

        # Temporary workaround: load without options, and filter manually if needed
        return o3d.t.io.read_point_cloud(filename=str(color_pcd_path), print_progress=print_progress).to(device=device)
    

    def save_colored_pcd(self, pcd: o3d.t.geometry.PointCloud):
        color_pcd_path = self.reconstruction_path_config.get_colored_pcd_path()
        color_pcd_path.parent.mkdir(parents=True, exist_ok=True)

        o3d.t.io.write_point_cloud(
            filename=str(color_pcd_path),
            pointcloud=pcd,
            write_ascii=False,
            compressed=True
        )


    def save_colored_pcd_legacy(self, pcd: o3d.geometry.PointCloud):
        color_pcd_path = self.reconstruction_path_config.get_colored_pcd_path()
        color_pcd_path.parent.mkdir(parents=True, exist_ok=True)

        o3d.io.write_point_cloud(
            filename=str(color_pcd_path),
            pointcloud=pcd,
            write_ascii=False,
            compressed=True
        )