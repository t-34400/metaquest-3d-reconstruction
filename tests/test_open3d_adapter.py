import sys
from types import SimpleNamespace

from mq3drecon.config import FragmentPoseRefinementConfig
from mq3drecon.processing.reconstruction.adapters.open3d_adapter import make_icp_criteria_list, to_open3d_device


class FakeDevice:
    def __init__(self, name):
        self.name = name


class FakeICPConvergenceCriteria:
    def __init__(self, max_iteration, relative_fitness, relative_rmse):
        self.max_iteration = max_iteration
        self.relative_fitness = relative_fitness
        self.relative_rmse = relative_rmse


def install_fake_open3d(monkeypatch):
    fake_open3d = SimpleNamespace(
        core=SimpleNamespace(Device=FakeDevice),
        t=SimpleNamespace(
            pipelines=SimpleNamespace(
                registration=SimpleNamespace(ICPConvergenceCriteria=FakeICPConvergenceCriteria)
            )
        ),
    )
    monkeypatch.setitem(sys.modules, "open3d", fake_open3d)


def test_to_open3d_device_converts_string_in_adapter(monkeypatch):
    install_fake_open3d(monkeypatch)

    device = to_open3d_device("CPU:0")

    assert isinstance(device, FakeDevice)
    assert device.name == "CPU:0"


def test_make_icp_criteria_list_builds_open3d_objects_in_adapter(monkeypatch):
    install_fake_open3d(monkeypatch)
    config = FragmentPoseRefinementConfig(device="CPU:0")

    criteria = make_icp_criteria_list(config)

    assert [item.max_iteration for item in criteria] == config.max_iterations
    assert [item.relative_fitness for item in criteria] == config.relative_fitnesses
    assert [item.relative_rmse for item in criteria] == config.relative_rmses
