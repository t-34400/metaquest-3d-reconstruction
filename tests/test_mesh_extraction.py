import pytest

from mq3drecon.processing.reconstruction.utils.mesh_extraction import extract_triangle_mesh_with_cpu_fallback


class FakeCpuVoxelGrid:
    def __init__(self):
        self.received_kwargs = None

    def extract_triangle_mesh(self, **kwargs):
        self.received_kwargs = kwargs
        return "cpu-mesh"


class FakeVoxelGrid:
    def __init__(self, error_message):
        self.error_message = error_message
        self.cpu_grid = FakeCpuVoxelGrid()
        self.cpu_called = False

    def extract_triangle_mesh(self, **kwargs):
        raise RuntimeError(self.error_message)

    def cpu(self):
        self.cpu_called = True
        return self.cpu_grid


def test_mesh_extraction_retries_on_cpu_for_open3d_cuda_assistance_allocation_error():
    vbg = FakeVoxelGrid("Unable to allocate assistance mesh structure for Marching Cubes with 1 active voxel blocks")

    mesh = extract_triangle_mesh_with_cpu_fallback(vbg, weight_threshold=3.0, estimated_vertex_number=42)

    assert mesh == "cpu-mesh"
    assert vbg.cpu_called
    assert vbg.cpu_grid.received_kwargs == {"weight_threshold": 3.0, "estimated_vertex_number": 42}


def test_mesh_extraction_reraises_unrelated_runtime_errors():
    vbg = FakeVoxelGrid("different Open3D failure")

    with pytest.raises(RuntimeError, match="different Open3D failure"):
        extract_triangle_mesh_with_cpu_fallback(vbg)

    assert not vbg.cpu_called
