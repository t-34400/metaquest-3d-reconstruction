# Reconstruction Configuration Specification

## Purpose

This document defines the structure and dependency boundaries for reconstruction configuration objects.

It owns requirements for:

* reconstruction configuration module ownership
* lightweight import behavior
* Open3D independence for configuration data objects
* compatibility exports during migration

Packaging dependency boundaries are specified in `PACKAGING.md`.
Public import stability is specified in `PUBLIC_API.md`.

---

# Configuration Ownership

Reconstruction configuration must be represented by lightweight Python data objects.

Configuration modules may describe reconstruction options, device specifications, and per-step parameter groups, but they must not construct Open3D runtime objects directly.

Open3D-backed runtime conversion belongs in reconstruction processing adapters, not configuration modules.

---

# Module Structure

Reconstruction configuration should be split by responsibility instead of accumulating unrelated configuration classes in one large module.

The package should provide focused modules for:

* device defaults and device specification aliases
* depth confidence estimation configuration
* fragment generation configuration
* fragment pose refinement configuration
* TSDF/depth integration configuration
* color optimization configuration
* color-aligned depth rendering configuration
* top-level reconstruction configuration parsing and composition

---

# Lightweight Import Requirement

Importing reconstruction configuration modules must not require Open3D.

The following imports must remain usable in the default lightweight installation profile:

```python
from mq3drecon.config import ReconstructionConfig
from mq3drecon.config.reconstruction_config import ReconstructionConfig
```

---

# Compatibility Aggregation

During migration, `mq3drecon.config.reconstruction_config` may remain as an aggregation module that re-exports reconstruction configuration classes from focused implementation modules.

This compatibility module must not become the long-term owner of unrelated configuration responsibilities.

# Reconstruction Depth Source

`ReconstructionConfig` supports selecting the depth input used for TSDF integration.

Supported values are:

| Value | Meaning |
| --- | --- |
| `quest` | Use legacy Quest raw depth descriptors and raw depth maps. This is the default compatibility behavior. |
| `color_aligned` | Use saved `.npy` color-aligned depth maps matched to the color dataset timestamps. |

The `color_aligned` source is intended for generated depth maps such as
FoundationStereo output. It must not require raw Quest depth files.

# Color-Aligned RGBD Reconstruction

When `depth_source` is `color_aligned`, reconstruction must prefer saved LEFT rectified stereo RGBD frames when they are available. If rectified stereo RGBD artifacts are absent, it must integrate the LEFT color image and LEFT color-aligned depth map as RGBD frames directly. This path
must not require RIGHT color images, raw Quest depth files, Quest depth pose
optimization, Quest depth confidence estimation, color map optimization, or
color-aligned depth rendering.

The color-aligned RGBD path must treat saved rectified stereo depth maps, or saved color-aligned depth maps when rectified stereo depth is unavailable, as the selected depth source and must not render over them as an intermediate output.

# TSDF Mesh Extraction

Reconstruction paths that extract triangle meshes from Open3D `VoxelBlockGrid`
objects should preserve the configured TSDF integration resolution by default.

When CUDA mesh extraction fails because Open3D cannot allocate the Marching
Cubes assistance mesh structure, reconstruction should retry mesh extraction on
CPU instead of requiring users to reduce reconstruction resolution first. Other
mesh extraction failures must continue to propagate to callers.
