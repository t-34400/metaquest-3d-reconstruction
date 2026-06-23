# Public Python API

This guide is for downstream Python projects that import MQ3DRecon as a package.

Prefer imports from `mq3drecon.*` in downstream projects. Do not import from `scripts.*` in new code. For timestamp conventions, coordinate systems, dataset schemas, MRUK frame formats, and generated artifact layouts, see [DATA_FORMAT.md](DATA_FORMAT.md).


Prefer imports from `mq3drecon.*` in downstream projects. Do not import from `scripts.*` in new code.

## Load a backend-aware color dataset

Use `load_color_dataset()` as the main entry point for per-frame timestamps, intrinsics, poses, image sizes, and backend-native frame file names. It reads legacy Camera2 captures and MRUK captures through the same API.

```python
from pathlib import Path

from mq3drecon.dataio import DataIO
from mq3drecon.models import Side

project_dir = Path("data/projects/test")
data_io = DataIO(project_dir=project_dir)
side = Side.LEFT

color_dataset = data_io.color.load_color_dataset(side)
index = 0

timestamp = int(color_dataset.timestamps[index])
K = color_dataset.get_intrinsic_matrices()[index]
T_world_to_camera = color_dataset.transforms.extrinsics_wc[index]
T_camera_to_world = color_dataset.transforms.extrinsics_cw[index]

print(timestamp)
print(K)
print(T_world_to_camera)
print(T_camera_to_world)
```

Useful dataset fields:

| Field | Meaning |
| --- | --- |
| `timestamps` | Frame timestamps. |
| `image_file_names` | Backend-native color frame file names. |
| `fx`, `fy`, `cx`, `cy` | Per-frame intrinsics. |
| `widths`, `heights` | Per-frame image sizes. |
| `transforms.positions_wc` | Camera centers in world coordinates. |
| `transforms.rotations_wc` | Camera-to-world quaternions in `(x, y, z, w)` order. |
| `transforms.extrinsics_wc` | World-to-camera `4x4` matrices. |
| `transforms.extrinsics_cw` | Camera-to-world `4x4` matrices. |

## Load RGB frames

Use `load_rgb()` when you already have a color timestamp and want a three-channel RGB array. The loader hides whether the source frame is backend-native raw data or an exported PNG.

For legacy Camera2 captures, it reads generated RGB PNG files when present and otherwise decodes raw YUV frames. For MRUK captures, it prefers raw `.rgba` frames and falls back to generated MRUK PNG files when only the exported PNG exists.

```python
from pathlib import Path

from mq3drecon.dataio import DataIO
from mq3drecon.models import Side

project_dir = Path("data/projects/test")
data_io = DataIO(project_dir=project_dir)
side = Side.LEFT

color_dataset = data_io.color.load_color_dataset(side)
timestamp = int(color_dataset.timestamps[0])
rgb = data_io.color.load_rgb(side, timestamp)

print(rgb.shape)
```

Use dataset-indexed loading when processing frames in dataset order:

```python
rgb = data_io.color.load_color_rgb_image(color_dataset, index=0)
```

Both readers return RGB `numpy.ndarray` values. Convert to BGR before passing images to OpenCV APIs that expect BGR:

```python
import cv2

bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
```

## Use OpenCV/COLMAP-compatible camera poses

```python
from pathlib import Path

from mq3drecon.dataio import DataIO
from mq3drecon.models import CoordinateSystem, Side

project_dir = Path("data/projects/test")
data_io = DataIO(project_dir=project_dir)
side = Side.LEFT

color_dataset = data_io.color.load_color_dataset(side)
opencv_dataset = color_dataset
opencv_dataset.transforms = color_dataset.transforms.convert_coordinate_system(
    target_coordinate_system=CoordinateSystem.COLMAP,
    is_camera=True,
)

index = 0
K = opencv_dataset.get_intrinsic_matrices()[index]
T_world_to_camera = opencv_dataset.transforms.extrinsics_wc[index]
T_camera_to_world = opencv_dataset.transforms.extrinsics_cw[index]
camera_center_world = opencv_dataset.transforms.positions_wc[index]
camera_rotation_xyzw = opencv_dataset.transforms.rotations_wc[index]
```

`CoordinateSystem.COLMAP` uses the camera convention commonly expected by OpenCV/COLMAP-style projection code:

```text
x: right
y: down
z: forward
```

## Load Quest depth maps and confidence maps

Use `data_io.depth` for Quest-native depth frames. These depth maps use the native depth capture layout and are separate from stereo-generated rectified stereo depth and compatibility color-aligned depth.

```python
from pathlib import Path

from mq3drecon.dataio import DataIO
from mq3drecon.models import Side

project_dir = Path("data/projects/test")
data_io = DataIO(project_dir=project_dir)
side = Side.LEFT

depth_dataset = data_io.depth.load_depth_dataset(side)
depth_map = data_io.depth.load_depth_map_by_index(
    side,
    depth_dataset,
    index=0,
)

confidence = data_io.depth.load_confidence_map(
    side,
    int(depth_dataset.timestamps[0]),
)

if confidence is not None:
    print(confidence.shape)
    print(confidence.confidence_map)
    print(confidence.valid_count)
```

## Load rectified stereo depth maps

Use the rectified stereo loaders for the primary FoundationStereo outputs. These datasets preserve the rectified stereo image coordinates and the rectified intrinsics used to convert disparity into metric depth.

```python
from pathlib import Path

from mq3drecon.dataio import DataIO
from mq3drecon.models import Side

project_dir = Path("data/projects/test")
data_io = DataIO(project_dir=project_dir)
side = Side.LEFT

color_dataset, depth_dataset = data_io.rgbd.build_rectified_stereo_rgbd_datasets(side=side)

index = 0
rgb = data_io.color.load_color_rgb_image(color_dataset, index=index)
depth = data_io.rgbd.load_rectified_stereo_depth_by_index(
    side=side,
    dataset=depth_dataset,
    index=index,
)
rectification = data_io.rgbd.load_stereo_rectification()

print(rgb.shape)
print(depth.shape)
print(depth.dtype)
print(rectification.left_projection.shape)
```

`load_rectified_stereo_depth_by_index()` validates that the loaded array shape matches the rectified depth dataset image size and returns finite positive metric depth as `float32`, with invalid values set to zero. `build_rectified_stereo_rgbd_datasets()` returns rectified color and depth datasets filtered to the shared timestamp set.

## Load compatibility color-aligned depth maps

Use the color-aligned loaders only when downstream code expects depth in the original LEFT color coordinate system. These maps are derived compatibility artifacts, not the primary FoundationStereo reconstruction input.

```python
source_color_dataset = data_io.color.load_color_dataset(Side.LEFT)
color_dataset, depth_dataset = data_io.rgbd.build_color_aligned_rgbd_datasets(
    side=Side.LEFT,
    color_dataset=source_color_dataset,
)

index = 0
rgb = data_io.color.load_color_rgb_image(color_dataset, index=index)
depth = data_io.rgbd.load_color_aligned_depth_by_index(
    side=Side.LEFT,
    dataset=depth_dataset,
    index=index,
)
timestamp = int(depth_dataset.timestamps[index])
same_depth = data_io.rgbd.load_color_aligned_depth(Side.LEFT, timestamp)

print(rgb.shape)
print(depth.shape)
print(same_depth.shape)
```

`load_color_aligned_depth_by_index()` validates that the loaded array shape matches the compatibility dataset image size and returns finite positive metric depth as `float32`, with invalid values set to zero.

## Run workflows from Python

```python
from pathlib import Path

from mq3drecon import ReconstructionConfig, run_foundation_stereo_depth, run_reconstruct_scene

project_dir = Path("data/projects/test")
model_path = Path(".local/models/foundationstereo.onnx")

run_foundation_stereo_depth(
    project_dir=project_dir,
    model_path=model_path,
)

run_reconstruct_scene(
    project_dir=project_dir,
    config=ReconstructionConfig(depth_source="rectified_stereo"),
)
```

Open3D-backed reconstruction requires the `reconstruction` or `full` optional dependency profile.

## Optional batch export workflows

These workflows are explicit export helpers. They are not prerequisites for the backend-aware color readers.

```python
from pathlib import Path

from mq3drecon.workflows import (
    run_color_aligned_depth_to_png,
    run_depth_to_linear,
    run_rgba_to_png,
    run_yuv_to_rgb,
)

project_dir = Path("data/projects/test")

run_yuv_to_rgb(project_dir)   # Legacy Camera2 YUV -> RGB PNG export
run_rgba_to_png(project_dir)  # MRUK RGBA -> PNG export
run_depth_to_linear(project_dir)
run_color_aligned_depth_to_png(project_dir)
```

Use typed config objects when you need non-default behavior without YAML:

```python
from mq3drecon.config import Yuv2RgbConfig
from mq3drecon.workflows import run_yuv_to_rgb

run_yuv_to_rgb(
    project_dir,
    config=Yuv2RgbConfig(
        blur_filter=True,
        blur_threshold=50.0,
    ),
)
```

Do not pass both `config` and `config_yml_path` to the same workflow call.

## Lightweight public imports

Common lightweight imports for downstream code do not require Open3D:

```python
from mq3drecon import (
    Depth2LinearConfig,
    FoundationStereoConfig,
    PipelineConfigs,
    ProjectPathConfig,
    ReconstructionConfig,
    Yuv2RgbConfig,
)
from mq3drecon.dataio import (
    CaptureBackend,
    DataIO,
    DepthDataIO,
    ImageDataIO,
    MRUKImageDataIO,
    MRUKIntrinsics,
    RGBDDataIO,
    ReconstructionDataIO,
    SessionInfo,
    load_session_info,
)
from mq3drecon.models import CameraDataset, ConfidenceMap, CoordinateSystem, DepthDataset, Side, Transforms
from mq3drecon.workflows import (
    export_colmap_project,
    get_rgb_image_status,
    has_rgb_images,
    run_color_aligned_depth_to_png,
    run_depth_to_linear,
    run_foundation_stereo_depth,
    run_reconstruct_scene,
    run_rgba_to_png,
    run_visualize_camera_trajectories,
    run_yuv_to_rgb,
)
```

