# Public API Specification

## Purpose

This document defines public import boundaries for the installable MQ3DRecon package.

It owns requirements for:

* package namespace stability
* lightweight public imports
* migration exports from legacy script modules
* CLI-to-library separation
* optional dependency visibility from public modules

Packaging dependency profiles are specified in `PACKAGING.md`.
CLI behavior is specified in `CLI_BEHAVIOR.md`.
Project layout behavior is specified in `PROJECT_LAYOUT.md`.
Dataset schemas are specified in `DATASETS_AND_CACHE.md`.

---

# Package Namespace

The installable package namespace is:

```python
mq3drecon
```

New library APIs must live under the package namespace rather than under `scripts/`.
Legacy script modules may remain as compatibility wrappers during migration, but they are not long-term public package APIs.

---

# Lightweight Import Boundary

The default lightweight installation profile must support importing public package modules that do not execute Open3D-backed reconstruction behavior.

The following imports are part of the lightweight public boundary:

```python
import mq3drecon
from mq3drecon import Depth2LinearConfig, FoundationStereoConfig, MQ3DReconError, PipelineConfigs, ProcessingError, ProjectPathConfig, ReconstructionConfig, Yuv2RgbConfig
from mq3drecon import run_depth_to_linear, run_foundation_stereo_depth, run_reconstruct_scene, run_rgba_to_png, run_yuv_to_rgb
from mq3drecon.config import Depth2LinearConfig, FoundationStereoConfig, PipelineConfigs, ProjectPathConfig, ReconstructionConfig, Yuv2RgbConfig
from mq3drecon.dataio import DataIO, DepthDataIO, ImageDataIO, RGBDDataIO, ReconstructionDataIO
from mq3drecon.layouts import ColmapExportLayout, LegacyProjectLayout, PackageOutputLayout
from mq3drecon.models import BaseTime, CameraCharacteristics, CameraDataset, ConfidenceMap, CoordinateSystem, DepthDataset, ImageFormatInfo, ImagePlaneInfo, Side, Transforms
from mq3drecon.pipeline import PipelineProcessor
from mq3drecon.processing.depth_conversion import convert_depth_directory
from mq3drecon.processing.visualization import get_camera_visualization_lines, visualize_camera_trajectories
from mq3drecon.processing.rgba_conversion import convert_rgba_directory
from mq3drecon.processing.yuv_conversion import convert_yuv_directory
from mq3drecon.workflows import RgbImageStatus, export_colmap_project, get_rgb_image_status, has_rgb_images, run_depth_to_linear, run_foundation_stereo_depth, run_rgba_to_png, run_yuv_to_rgb
```

Importing these modules must not require Open3D.

---

# RGB Image Status Helpers

The workflow public API includes lightweight helpers for checking whether
three-channel RGB frames are loadable for both sides of a project directory.

```python
from mq3drecon.workflows import get_rgb_image_status, has_rgb_images

status = get_rgb_image_status(project_dir)
status.left_count
status.right_count
status.is_complete
status.is_balanced

has_rgb_images(project_dir)
```

These helpers must inspect loadable color-frame timestamps without running
conversion workflows or requiring Open3D. For legacy Camera2 recordings, raw
YUV timestamps and generated RGB PNG timestamps are both loadable. For MRUK
recordings, raw RGBA timestamps and generated RGBA PNG timestamps are both
loadable.


# Format-Aware RGB Loading

`ImageDataIO.load_rgb(side, timestamp)` is the public color-frame reader for
callers that need a three-channel RGB array for a specific timestamp. It must
hide whether the underlying capture frame is stored as a generated PNG or as a
backend-native raw frame.

Legacy Camera2 recordings must read `left/right_camera_rgb/*.png` when present
and otherwise decode `left/right_camera_raw/*.yuv`. MRUK recordings must prefer
raw `left/right_camera_mruk_rgba/*.rgba` frames and otherwise read generated
`left/right_camera_mruk_rgba_png/*.png` exports.

The explicit conversion workflows `run_yuv_to_rgb()` and `run_rgba_to_png()`
remain available for batch PNG export, cache generation, inspection, and tools
that require PNG files. They are not required before calling `load_rgb()`.

# Conversion Workflow Configuration

The public conversion workflows support lightweight typed configuration objects and internal defaults.

```python
from mq3drecon.config import Depth2LinearConfig, Yuv2RgbConfig
from mq3drecon.workflows import run_depth_to_linear, run_rgba_to_png, run_yuv_to_rgb

run_yuv_to_rgb(project_dir)
run_yuv_to_rgb(project_dir, config=Yuv2RgbConfig())
run_yuv_to_rgb(project_dir, config_yml_path=config_yml_path)

run_rgba_to_png(project_dir)

run_depth_to_linear(project_dir)
run_depth_to_linear(project_dir, config=Depth2LinearConfig())
run_depth_to_linear(project_dir, config_yml_path=config_yml_path)
```

Reconstruction workflows support direct typed reconstruction configuration:

```python
from mq3drecon.config import ReconstructionConfig
from mq3drecon.workflows import run_reconstruct_scene

run_reconstruct_scene(project_dir)
run_reconstruct_scene(project_dir, config=ReconstructionConfig())
run_reconstruct_scene(project_dir, config_yml_path=config_yml_path)
```

Pipeline-level configuration is also default-constructible for workflows that execute multiple processing stages:

```python
from mq3drecon.config import PipelineConfigs
from mq3drecon.pipeline import PipelineProcessor
from mq3drecon.workflows import run_reconstruct_scene

PipelineConfigs()
PipelineProcessor(project_dir)
run_reconstruct_scene(project_dir)
```

`Yuv2RgbConfig()`, `Depth2LinearConfig()`, `FoundationStereoConfig()`, `ReconstructionConfig()`, and `PipelineConfigs()` must be default-constructible.
When both `config` and `config_yml_path` are passed to the same conversion or reconstruction workflow, the workflow must reject the ambiguous input with `ValueError`.

CLI defaults are specified separately in `CLI_BEHAVIOR.md`; this section defines Python public API behavior.

# Reconstruction Public Boundary

Open3D-backed reconstruction functionality is public only when the reconstruction optional dependency profile is installed.

Modules that execute reconstruction behavior may import Open3D at module load or when the operation is called, provided those imports are not required by the lightweight public boundary.

Configuration objects for reconstruction remain lightweight public API and must not construct Open3D runtime objects directly.

---

# Explicit Exports

Public migration modules should expose their supported API with explicit imports and `__all__` lists.

Public modules should not depend on dynamic `__getattr__`-based lazy migration shims unless a future specification documents the compatibility reason.

---

# CLI and Library Boundary

Library workflows must be callable without launching a separate command-line process.

CLI entrypoints may parse arguments and convert expected exceptions into process exit statuses, but processing behavior must be owned by package modules.

---

# Legacy Import Compatibility

Legacy modules under `scripts/` may re-export package APIs to preserve existing script-oriented workflows during migration.

Compatibility wrappers must not introduce new behavior that is unavailable from the package namespace.

Misspelled legacy module names may remain as compatibility aliases, but new public package names must use corrected spelling.
