# Meta Quest 3D Reconstruction

<p align="center">
  <img src="docs/overview.png" alt="Meta Quest 3D Reconstruction" width="480"/>
</p>

**Reconstruct 3D scenes from image and depth data captured using [Quest Reality Capture (QRC)](https://github.com/t-34400/QuestRealityCapture/).**

---

## Overview

Meta Quest 3D Reconstruction provides:

* RGB image conversion from Quest passthrough captures
* Depth map processing
* Open3D-based scene reconstruction
* Camera trajectory visualization
* COLMAP project export
* Python APIs for custom processing workflows

---

## Installation

### Lightweight Installation

Installs configuration, models, data I/O, conversion workflows, and COLMAP export support.

```bash
uv venv --python 3.10
source .venv/bin/activate

uv pip install -e .
```

### Full Installation

Installs Open3D-based reconstruction and visualization dependencies.

```bash
uv pip install -e ".[full]"
```

---

## Command Line Usage

Show all available commands:

```bash
mq3drecon --help
```

Show command-specific help:

```bash
mq3drecon reconstruct --help
mq3drecon export-colmap --help
```

Available commands:

```text
yuv-to-rgb
depth-to-linear
reconstruct
export-colmap
visualize-cameras
```

---

## Processing Pipeline

### Step 1: Convert Passthrough Images to RGB

```bash
mq3drecon yuv-to-rgb \
    --project-dir path/to/project \
    --config config/pipeline_config.yml
```

Outputs:

```text
left_camera_rgb/
right_camera_rgb/
```

---

### Step 2: Convert Raw Depth to Linear Depth Maps (Optional)

```bash
mq3drecon depth-to-linear \
    --project-dir path/to/project \
    --config config/pipeline_config.yml
```

Outputs:

```text
left_depth_linear/
right_depth_linear/
```

This step is standalone and is not required for reconstruction.

---

### Step 3: Reconstruct Scene

```bash
mq3drecon reconstruct \
    --project-dir path/to/project \
    --config config/pipeline_config.yml
```

Typical outputs:

```text
reconstruction/
├── tsdf/
├── mesh/
├── point_cloud/
└── aligned_depth/
```

Depending on the reconstruction configuration, additional outputs may be generated.

| Configuration Option                   | Description                                                    |
| -------------------------------------- | -------------------------------------------------------------- |
| `estimate_depth_confidences`           | Generate confidence maps by comparing neighboring depth frames |
| `optimize_depth_pose`                  | Optimize depth camera trajectories                             |
| `optimize_color_pose`                  | Optimize RGB camera trajectories                               |
| `sample_point_cloud_from_colored_mesh` | Export colored point clouds                                    |
| `render_color_aligned_depth`           | Render depth maps aligned to RGB images                        |

---

### Step 4: Export COLMAP Project

```bash
mq3drecon export-colmap \
    --project-dir path/to/project \
    --output-dir path/to/colmap_export
```

Additional options:

```bash
mq3drecon export-colmap \
    --project-dir path/to/project \
    --output-dir path/to/colmap_export \
    --use-colored-pointcloud \
    --use-optimized-color-dataset \
    --interval 1
```

Outputs:

```text
colmap_export/
```

---

### Step 5: Visualize Camera Trajectories

```bash
mq3drecon visualize-cameras \
    --project-dir path/to/project
```

---

## Python API

You can build custom processing pipelines using the public API.

```python
from pathlib import Path

from mq3drecon.dataio import DataIO
from mq3drecon.models import CoordinateSystem, Side

data_io = DataIO(project_dir=Path("data/projects/test"))

dataset = data_io.depth.load_depth_dataset(Side.LEFT)

depth_map = data_io.depth.load_depth_map_by_index(
    Side.LEFT,
    dataset,
    index=0,
)

color_dataset = data_io.color.load_color_dataset(Side.LEFT)

timestamp = color_dataset.timestamps[0]

rgb = data_io.color.load_rgb(
    Side.LEFT,
    timestamp,
)

color_dataset.transforms = (
    color_dataset.transforms.convert_coordinate_system(
        target_coordinate_system=CoordinateSystem.OPEN3D,
        is_camera=True,
    )
)
```

Public modules:

```python
mq3drecon.dataio
mq3drecon.models
mq3drecon.config
mq3drecon.workflows
```

---

## Legacy Script Compatibility

Legacy scripts remain available:

```bash
python scripts/convert_yuv_to_rgb.py
python scripts/convert_depth_to_linear_map.py
python scripts/reconstruct_scene.py
python scripts/build_colmap_project.py
python scripts/visualize_camera_trajectories.py
```

New automation should prefer the `mq3drecon` command.

---

## Directory Structure

After a typical reconstruction workflow:

```text
project/
├── left_camera_raw/
├── right_camera_raw/
├── left_depth/
├── right_depth/
├── left_camera_rgb/
├── right_camera_rgb/
├── reconstruction/
│   ├── tsdf/
│   ├── mesh/
│   ├── point_cloud/
│   └── aligned_depth/
└── colmap_export/
```

---

## Important Notes

### Quest Reality Capture v1.1.0+

As of Quest Reality Capture v1.1.0, camera poses are stored directly from the Android Camera2 API.

For older captures (v1.0.x), apply:

* Translation: `(x, y, z)` → `(x, y, -z)`
* Quaternion: `(x, y, z, w)` → `(-x, -y, z, w)`

---

## Third-Party Code

This project includes components derived from COLMAP.

See:

```text
scripts/third_party/colmap/COPYING.txt
```

for licensing details.

---

## License

MIT License.

See `LICENSE` for details.
# Meta Quest 3D Reconstruction

<p align="center">
  <img src="docs/overview.png" alt="QuestRealityCapture" width="480"/>
</p>

**Reconstruct 3D scenes from image and depth data captured using [Quest Reality Capture (QRC)](https://github.com/t-34400/QuestRealityCapture/).**

---

## 🧭 Overview

This project provides a complete pipeline for generating 3D reconstructions using passthrough images and depth data captured on Meta Quest devices.

The system supports:

* RGB image conversion from passthrough captures
* Depth map processing
* Open3D-based volumetric reconstruction
* Camera trajectory visualization
* COLMAP project export
* Python APIs for custom processing workflows

---

## 🚀 Installation

### Lightweight Installation

The default installation provides:

* configuration management
* public models
* data I/O APIs
* image/depth conversion workflows
* COLMAP export support

```bash
uv venv --python 3.10
source .venv/bin/activate

uv pip install -e .
```

### Full Installation

Install Open3D-backed reconstruction and visualization support:

```bash
uv pip install -e ".[full]"
```

---

## 💻 Command Line Usage

Show available commands:

```bash
mq3drecon --help
```

Show command-specific help:

```bash
mq3drecon yuv-to-rgb --help
mq3drecon depth-to-linear --help
mq3drecon reconstruct --help
mq3drecon export-colmap --help
mq3drecon visualize-cameras --help
```

Available commands:

```text
yuv-to-rgb
depth-to-linear
reconstruct
export-colmap
visualize-cameras
```

---

## 🔧 Processing Pipeline

### Step 1: Convert Passthrough Images to RGB

```bash
mq3drecon yuv-to-rgb \
    --project-dir path/to/your/project \
    --config config/pipeline_config.yml
```

Legacy equivalent:

```bash
python scripts/convert_yuv_to_rgb.py \
    --project_dir path/to/your/project \
    --config config/pipeline_config.yml
```

This generates:

* `left_camera_rgb/`
* `right_camera_rgb/`

**Note:** After conversion, manually remove any unnecessary or corrupted images.

---

### Step 2: Reconstruct 3D Scene

```bash
mq3drecon reconstruct \
    --project-dir path/to/your/project \
    --config config/pipeline_config.yml
```

Legacy equivalent:

```bash
python scripts/reconstruct_scene.py \
    --project_dir path/to/your/project \
    --config config/pipeline_config.yml
```

This produces:

* TSDF-based voxel grid
* Textured mesh model

Depending on your YAML configuration (`reconstruction:` section), additional outputs may be generated:

| Option                                                           | Output                                                                     |
| ---------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `estimate_depth_confidences: true`                               | Confidence maps generated by comparing each depth frame with nearby frames |
| `optimize_depth_pose: true`                                      | Optimized depth dataset                                                    |
| `optimize_color_pose: true`                                      | Optimized color dataset                                                    |
| `sample_point_cloud_from_colored_mesh: true`                     | Colored point cloud                                                        |
| `render_color_aligned_depth: true`                               | Depth images aligned to RGB frames                                         |
| `color_aligned_depth_rendering.only_use_optimized_dataset: true` | Align only optimized color datasets                                        |

---

### Step 3: Export COLMAP Project (Optional)

```bash
mq3drecon export-colmap \
    --project-dir path/to/your/project \
    --output-dir path/to/output/colmap_project
```

Legacy equivalent:

```bash
python scripts/build_colmap_project.py \
    --project_dir path/to/your/project \
    --output_dir path/to/output/colmap_project
```

Additional options:

```bash
mq3drecon export-colmap \
    --project-dir path/to/your/project \
    --output-dir path/to/output/colmap_project \
    --use-colored-pointcloud \
    --use-optimized-color-dataset \
    --interval 1
```

**Options:**

* `--use-colored-pointcloud` : Include colored point cloud if available.
* `--use-optimized-color-dataset` : Use optimized color dataset.
* `--interval` : Export every N-th frame.

---

### Optional: Convert Raw Depth to Linear Depth Maps

```bash
mq3drecon depth-to-linear \
    --project-dir path/to/your/project \
    --config config/pipeline_config.yml
```

Legacy equivalent:

```bash
python scripts/convert_depth_to_linear_map.py \
    --project_dir path/to/your/project \
    --config config/pipeline_config.yml
```

This generates:

* `left_depth_linear/`
* `right_depth_linear/`

This step is standalone and not required for other workflows.

---

### Optional: Visualize Camera Trajectories

```bash
mq3drecon visualize-cameras \
    --project-dir path/to/your/project
```

Legacy equivalent:

```bash
python scripts/visualize_camera_trajectories.py \
    --project_dir path/to/your/project
```

---

## 🛠️ Custom Data Processing

You can build custom processing workflows using the public Python API.

```python
from pathlib import Path

from mq3drecon.dataio import DataIO
from mq3drecon.models import CoordinateSystem, Side

data_io = DataIO(project_dir=Path("data/projects/test"))

# Load depth maps
dataset = data_io.depth.load_depth_dataset(Side.LEFT)

depth_map = data_io.depth.load_depth_map_by_index(
    Side.LEFT,
    dataset,
    index=0,
)

# Load RGB frames
color_dataset = data_io.color.load_color_dataset(Side.LEFT)

timestamp = color_dataset.timestamps[0]

rgb = data_io.color.load_rgb(
    Side.LEFT,
    timestamp,
)

# Convert coordinate systems
color_dataset.transforms = (
    color_dataset.transforms.convert_coordinate_system(
        target_coordinate_system=CoordinateSystem.OPEN3D,
        is_camera=True,
    )
)
```

Public APIs:

* `mq3drecon.dataio`
* `mq3drecon.models`
* `mq3drecon.config`
* `mq3drecon.workflows`

---

## 📁 Directory Structure (after full pipeline)

```text
your_project/
├── left_camera_raw/
├── right_camera_raw/
├── left_depth/
├── right_depth/
├── left_camera_rgb/
├── right_camera_rgb/
├── reconstruction/
│   ├── tsdf/
│   ├── mesh/
│   ├── point_cloud/
│   └── aligned_depth/
├── colmap_export/
├── config/
│   └── pipeline_config.yml
```

---

## 📢 NOTICE (v1.1.0+)

As of **Quest Reality Capture v1.1.0**, camera poses are stored as raw values directly from the Android Camera2 API.

If you're using older logs (v1.0.x), apply the following transformation:

* Translation: `(x, y, z)` → `(x, y, -z)`
* Rotation (quaternion): `(x, y, z, w)` → `(-x, -y, z, w)`

---

## 🧩 Third-Party Code

This project includes components from [COLMAP](https://github.com/colmap/colmap), licensed under the 3-clause BSD License.

See [`scripts/third_party/colmap/COPYING.txt`](./scripts/third_party/colmap/COPYING.txt) for details.

---

## 📝 License

This project is licensed under the MIT License.

See the [LICENSE](LICENSE) file for full text.

---

## 📌 TODO

* [ ] Implement carving to remove free-space artifacts
* [ ] Add Nerfstudio export instructions
