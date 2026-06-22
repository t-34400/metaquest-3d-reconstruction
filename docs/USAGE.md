# Usage

This document describes how to run MQ3DRecon from the package CLI and from the public Python API.

For installation details, see [INSTALLATION.md](INSTALLATION.md). For pipeline selection, see [PIPELINES.md](PIPELINES.md). For stereo model details, see [MODELS.md](MODELS.md).

## Command-line interface

The package exposes the `mq3drecon` command:

```bash
mq3drecon --help
```

Show command-specific help:

```bash
mq3drecon depth-to-linear --help
mq3drecon foundation-stereo-depth --help
mq3drecon reconstruct --help
mq3drecon export-colmap --help
mq3drecon visualize-cameras --help
mq3drecon yuv-to-rgb --help
mq3drecon rgba-to-png --help
```

Legacy scripts under `scripts/` remain available as migration shims. New automation should prefer the package-backed `mq3drecon` command.

## Configuration files

Conversion and reconstruction workflows provide built-in defaults. Use `--config` only when you need to override default settings:

```bash
mq3drecon reconstruct \
  --project-dir path/to/project \
  --config config/pipeline_config.yml
```

The CLI accepts both kebab-case and legacy underscore forms for the project and config options where migration compatibility is supported.

## Common command sequences

### Generate FoundationStereo rectified stereo depth

```bash
mq3drecon foundation-stereo-depth \
  --project-dir path/to/project \
  --model-path path/to/foundation_stereo.onnx
```

The FoundationStereo workflow reads color frames through the backend-aware color dataset API. It works with legacy Camera2 captures and MRUK captures without requiring a separate YUV or RGBA-to-PNG conversion step.

The workflow rectifies the left/right color frames before inference and writes the primary stereo outputs in rectified stereo coordinates:

```text
left_rectified_stereo_color/*.png
right_rectified_stereo_color/*.png
left_rectified_stereo_depth/*.npy
dataset/left_rectified_stereo_color_dataset.npz
dataset/right_rectified_stereo_color_dataset.npz
dataset/left_rectified_stereo_depth_dataset.npz
dataset/stereo_rectification.npz
```

For compatibility with older tooling, it also writes depth mapped back to the original LEFT color coordinate system:

```text
left_color_aligned_depth/*.npy
```

Optional config flags can also write decoded color PNGs, 16-bit metric depth PNGs, and 8-bit preview PNGs for inspecting the compatibility color-aligned depth maps. Saved compatibility `.npy` depth maps can also be exported later:

```bash
mq3drecon color-aligned-depth-to-png \
  --project-dir path/to/project
```

By default this writes 8-bit visual previews under `left_color_aligned_depth_preview_png/`. Add `--metric` to also write 16-bit scaled metric PNG files under `left_color_aligned_depth_png/`.

### Reconstruct with default Quest depth settings

```bash
mq3drecon reconstruct \
  --project-dir path/to/project
```

This uses the default reconstruction configuration.

### Reconstruct from FoundationStereo depth

First generate stereo depth, then reconstruct with `reconstruction.depth_source` set to `rectified_stereo`:

```yaml
reconstruction:
  depth_source: rectified_stereo
  render_color_aligned_depth: false
```

Then run:

```bash
mq3drecon reconstruct \
  --project-dir path/to/project \
  --config path/to/config.yml
```

When `depth_source: rectified_stereo` is selected, reconstruction first looks for LEFT rectified stereo RGBD artifacts and integrates those with rectified intrinsics. If rectified stereo artifacts are absent, it falls back to the compatibility LEFT color-aligned depth maps and original LEFT color frames. Quest depth confidence estimation, Quest depth pose optimization, and color-aligned depth rendering are skipped for this depth source. For backward compatibility, `depth_source: color_aligned` currently selects the same FoundationStereo reconstruction path and should be treated as a legacy alias.

### Export a COLMAP project

```bash
mq3drecon export-colmap \
  --project-dir path/to/project \
  --output-dir path/to/output/colmap_project \
  --use-optimized-color-dataset \
  --interval 1
```

Add `--use-colored-pointcloud` when a colored point cloud has already been generated and should be included in the COLMAP model.

### Visualize camera trajectories

```bash
mq3drecon visualize-cameras \
  --project-dir path/to/project
```

This opens the Open3D camera trajectory viewer and requires visualization-capable dependencies and runtime environment.

### Optional export commands

The following commands export backend-native color or depth inputs into derived files. They are useful for inspection, cache generation, and external tools that need PNG files. They are not required before using `load_rgb()`, `load_color_dataset()`, FoundationStereo depth generation, COLMAP export, or reconstruction.

```bash
mq3drecon yuv-to-rgb \
  --project-dir path/to/project

mq3drecon rgba-to-png \
  --project-dir path/to/project

mq3drecon depth-to-linear \
  --project-dir path/to/project

mq3drecon color-aligned-depth-to-png \
  --project-dir path/to/project
```

`yuv-to-rgb` writes legacy Camera2 RGB exports under:

```text
left_camera_rgb/
right_camera_rgb/
```

`rgba-to-png` writes MRUK PNG previews under:

```text
left_camera_mruk_rgba_png/
right_camera_mruk_rgba_png/
```

`depth-to-linear` writes linearized Quest native depth outputs from the raw depth frame layout.

`color-aligned-depth-to-png` writes saved color-aligned `.npy` depth maps as 8-bit preview PNGs by default. Use `--metric` to also write 16-bit metric PNGs.

### Run the repository example script

The repository includes a convenience script that runs package CLI commands against a capture directory and writes generated exports under a separate output root:

```bash
examples/run_mq3drecon_pipeline.sh \
  path/to/project \
  path/to/output/root
```

For MRUK captures without depth frames, the script skips YUV and depth conversion, then exports the color camera dataset to a COLMAP project. Set `RUN_RECONSTRUCT=1` to run Open3D reconstruction when usable depth inputs are available, and set `RUN_VISUALIZE=1` to open the camera trajectory viewer.

## Public Python API

Prefer imports from `mq3drecon.*` in downstream projects. Do not import from `scripts.*` in new code.

### Load a backend-aware color dataset

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

### Load RGB frames

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

### Use OpenCV/COLMAP-compatible camera poses

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

### Load Quest depth maps and confidence maps

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

### Load rectified stereo depth maps

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

### Load compatibility color-aligned depth maps

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

### Run workflows from Python

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

### Optional batch export workflows

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
