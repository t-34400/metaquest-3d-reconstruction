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
mq3drecon yuv-to-rgb --help
mq3drecon rgba-to-png --help
mq3drecon depth-to-linear --help
mq3drecon foundation-stereo-depth --help
mq3drecon reconstruct --help
mq3drecon export-colmap --help
mq3drecon visualize-cameras --help
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

### Convert legacy YUV frames to RGB

```bash
mq3drecon yuv-to-rgb \
  --project-dir path/to/project
```

This writes converted color frames into the legacy RGB directories:

```text
left_camera_rgb/
right_camera_rgb/
```

### Convert MRUK RGBA frames to PNG previews

```bash
mq3drecon rgba-to-png \
  --project-dir path/to/project
```

This writes decoded MRUK color previews while leaving source `.rgba` files unchanged:

```text
left_camera_mruk_rgba_png/
right_camera_mruk_rgba_png/
```

The MRUK color dataset reader can load `.rgba` frames directly. This conversion is mainly for inspection and custom tools that expect ordinary PNG files.

### Convert raw Quest depth to linear depth

```bash
mq3drecon depth-to-linear \
  --project-dir path/to/project
```

This is a standalone conversion step for Quest native depth frames.

### Generate FoundationStereo color-aligned depth

```bash
mq3drecon foundation-stereo-depth \
  --project-dir path/to/project \
  --model-path path/to/foundation_stereo.onnx
```

The FoundationStereo workflow writes left-view color-aligned depth maps:

```text
left_color_aligned_depth/*.npy
```

Optional config flags can also write decoded RGBA PNGs, 16-bit metric depth PNGs, and 8-bit preview PNGs for inspection.

### Reconstruct with default Quest depth settings

```bash
mq3drecon reconstruct \
  --project-dir path/to/project
```

This uses the default reconstruction configuration.

### Reconstruct from FoundationStereo depth

First generate stereo depth, then reconstruct with `reconstruction.depth_source` set to `color_aligned`:

```yaml
reconstruction:
  depth_source: color_aligned
  render_color_aligned_depth: false
```

Then run:

```bash
mq3drecon reconstruct \
  --project-dir path/to/project \
  --config path/to/config.yml
```

When `depth_source: color_aligned` is selected, reconstruction integrates LEFT RGB frames with LEFT color-aligned depth maps directly. Quest depth confidence estimation, Quest depth pose optimization, and color-aligned depth rendering are skipped for this depth source.

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

### Run conversion workflows

```python
from pathlib import Path

from mq3drecon.workflows import run_depth_to_linear, run_rgba_to_png, run_yuv_to_rgb

project_dir = Path("data/projects/test")

run_yuv_to_rgb(project_dir)
run_rgba_to_png(project_dir)
run_depth_to_linear(project_dir)
```

### Load RGB frames by timestamp

Use `load_rgb()` when you already have a color timestamp and want a three-channel RGB array. The loader uses the capture backend recorded in `session_info.json` when available. Legacy captures read generated RGB PNG files; MRUK captures read generated MRUK PNG files when present and otherwise fall back to the MRUK color dataset source frame.

```python
from pathlib import Path

from mq3drecon.dataio import DataIO
from mq3drecon.models import Side
from mq3drecon.workflows import has_rgb_images, run_yuv_to_rgb

project_dir = Path("data/projects/test")
data_io = DataIO(project_dir=project_dir)
side = Side.LEFT

if data_io.color.get_capture_backend().value == "NativeCamera2" and not has_rgb_images(project_dir):
    run_yuv_to_rgb(project_dir)

color_dataset = data_io.color.load_color_dataset(side)
timestamp = int(color_dataset.timestamps[0])
rgb = data_io.color.load_rgb(side, timestamp)

print(rgb.shape)
```

For MRUK captures, `run_rgba_to_png(project_dir)` remains optional. It is useful for inspection or external tools that need PNG files, but `load_rgb()` can read raw MRUK `.rgba` frames through the color dataset when PNG files have not been generated.

### Load color images across legacy and MRUK captures

Use dataset-indexed color loading when code should process the dataset in order instead of looking up frames by timestamp. For MRUK, this reads `.rgba` frames directly and returns top-down RGB arrays.

```python
from pathlib import Path

from mq3drecon.dataio import DataIO
from mq3drecon.models import Side

project_dir = Path("data/projects/test")
data_io = DataIO(project_dir=project_dir)
side = Side.LEFT

color_dataset = data_io.color.load_color_dataset(side)
rgb = data_io.color.load_color_rgb_image(color_dataset, index=0)

print(rgb.shape)
```

`load_color_rgb_image()` returns an RGB `numpy.ndarray`. Convert it to BGR before passing it to OpenCV APIs that expect BGR images:

```python
import cv2

bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
```

### Pass typed config objects

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

### Override the FoundationStereo model path

Pass `model_path` to select an ONNX model without editing YAML:

```python
from pathlib import Path

from mq3drecon import run_foundation_stereo_depth

project_dir = Path("data/projects/test")
model_path = Path(".local/models/foundationstereo.onnx")

run_foundation_stereo_depth(
    project_dir=project_dir,
    model_path=model_path,
)
```

### Run reconstruction from Python

```python
from pathlib import Path

from mq3drecon import ReconstructionConfig, run_reconstruct_scene

project_dir = Path("data/projects/test")

run_reconstruct_scene(
    project_dir=project_dir,
    config=ReconstructionConfig(depth_source="color_aligned"),
)
```

Open3D-backed reconstruction requires the `reconstruction` or `full` optional dependency profile.

## Custom processing examples

### Load camera calibration and capture format metadata

```python
from pathlib import Path

from mq3drecon.dataio import DataIO
from mq3drecon.models import Side

project_dir = Path("data/projects/test")
data_io = DataIO(project_dir=project_dir)
side = Side.LEFT

camera = data_io.color.load_camera_characteristics(side)
format_info = data_io.color.load_image_format_info(side)

print(camera.width, camera.height)
print(camera.fx, camera.fy)
print(camera.cx, camera.cy)
print(camera.transl)
print(camera.rot_quat)

print(format_info.width, format_info.height)
print(format_info.format)
print(format_info.base_time.unix_time_ns)
for plane in format_info.planes:
    print(plane.buffer_size, plane.row_stride, plane.pixel_stride)
```

Use `CameraDataset.get_intrinsic_matrices()` when you only need per-frame intrinsic matrices. Use `load_camera_characteristics()` when you also need the camera-local offset stored in QRC metadata.

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

Useful dataset fields:

| Field | Meaning |
| --- | --- |
| `timestamps` | Frame timestamps. |
| `image_file_names` | RGB file names. |
| `fx`, `fy`, `cx`, `cy` | Per-frame intrinsics. |
| `widths`, `heights` | Per-frame image sizes. |
| `transforms.positions_wc` | Camera centers in world coordinates. |
| `transforms.rotations_wc` | Camera-to-world quaternions in `(x, y, z, w)` order. |
| `transforms.extrinsics_wc` | World-to-camera `4x4` matrices. |
| `transforms.extrinsics_cw` | Camera-to-world `4x4` matrices. |

### Load depth maps and confidence maps

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

## Lightweight public imports

The lightweight package profile exposes public data models and helpers without requiring Open3D:

```python
from mq3drecon import (
    Depth2LinearConfig,
    FoundationStereoConfig,
    PipelineConfigs,
    ProjectPathConfig,
    ReconstructionConfig,
    Yuv2RgbConfig,
)
from mq3drecon.dataio import DataIO, DepthDataIO, ImageDataIO, RGBDDataIO, ReconstructionDataIO
from mq3drecon.models import (
    BaseTime,
    CameraCharacteristics,
    CameraDataset,
    ConfidenceMap,
    CoordinateSystem,
    DepthDataset,
    ImageFormatInfo,
    ImagePlaneInfo,
    Side,
    Transforms,
)
from mq3drecon.workflows import (
    RgbImageStatus,
    export_colmap_project,
    get_rgb_image_status,
    has_rgb_images,
    run_depth_to_linear,
    run_foundation_stereo_depth,
    run_reconstruct_scene,
    run_rgba_to_png,
    run_yuv_to_rgb,
)
```
