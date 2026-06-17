# Legacy Behavior Specification

## Purpose

This document defines legacy compatibility requirements for the current script-oriented MQ3DRecon project layout.

It exists to preserve intentionally supported behavior while the project migrates toward an installable package.

This specification owns requirements for:

* legacy input directory names
* legacy generated artifact locations
* legacy project-relative path conventions
* compatibility expectations for existing script workflows

Dataset and cache file schemas are specified in `DATASETS_AND_CACHE.md`.
Public package and import boundaries are specified in `PUBLIC_API.md`.

---

# Compatibility Scope

Legacy behavior covers project directories consumed by the current `scripts/` implementation.

A legacy project directory is a filesystem directory containing Meta Quest capture inputs and generated outputs using the historical directory names documented here.

Legacy compatibility does not make `scripts/` a stable package API. Script import behavior is a migration concern, not a long-term public interface.

---

# Input Data Immutability

Source capture inputs must be treated as immutable.

Processing code must not modify, rewrite, delete, or rename source capture files unless a command explicitly documents destructive behavior and requires explicit user intent.

Generated artifacts may be written to legacy output locations only when the caller explicitly chooses legacy project layout behavior.

---

# Legacy Camera Sides

Legacy layout uses two camera sides:

| Side | Meaning |
| --- | --- |
| `LEFT` | Left camera or left depth stream. |
| `RIGHT` | Right camera or right depth stream. |

Legacy filenames and cache keys that include side names must use the enum name spelling `LEFT` or `RIGHT` when the existing implementation already does so.

Legacy directory names that include side names use lowercase `left` and `right` as documented below.

---

# Legacy Color Input Layout

The following paths are legacy color inputs, relative to the project directory:

| Path | Owner | Description |
| --- | --- | --- |
| `left_camera_raw/` | input | Left camera raw YUV frames. |
| `right_camera_raw/` | input | Right camera raw YUV frames. |
| `left_camera_characteristics.json` | input | Left camera intrinsic and pose metadata. |
| `right_camera_characteristics.json` | input | Right camera intrinsic and pose metadata. |
| `left_camera_image_format.json` | input | Left camera image format metadata. |
| `right_camera_image_format.json` | input | Right camera image format metadata. |
| `hmd_poses.csv` | input | HMD pose timeline used for color frame pose interpolation. |

Raw YUV frame filenames are timestamp stems with `.yuv` extension.

---

# Legacy Color Output Layout

The following paths are legacy generated color outputs, relative to the project directory:

| Path | Owner | Description |
| --- | --- | --- |
| `left_camera_rgb/` | generated | Left RGB PNG frames converted from YUV input. |
| `right_camera_rgb/` | generated | Right RGB PNG frames converted from YUV input. |

RGB frame filenames are timestamp stems with `.png` extension.

Dataset files derived from these outputs are specified in `DATASETS_AND_CACHE.md`.

---

# Legacy Depth Input Layout

The following paths are legacy depth inputs, relative to the project directory:

| Path | Owner | Description |
| --- | --- | --- |
| `left_depth/` | input | Left raw depth maps. |
| `right_depth/` | input | Right raw depth maps. |
| `left_depth_descriptors.csv` | input | Left depth frame metadata. |
| `right_depth_descriptors.csv` | input | Right depth frame metadata. |

Raw depth map filenames are timestamp stems with `.raw` extension.

---

# Legacy Depth Output Layout

The following paths are legacy generated depth outputs, relative to the project directory:

| Path | Owner | Description |
| --- | --- | --- |
| `left_depth_linear/` | generated | Left linearized depth PNG maps. |
| `right_depth_linear/` | generated | Right linearized depth PNG maps. |
| `left_depth_confidence/` | generated | Left per-frame depth confidence maps. |
| `right_depth_confidence/` | generated | Right per-frame depth confidence maps. |
| `left_color_aligned_depth/` | generated | Left color-aligned depth arrays. |
| `right_color_aligned_depth/` | generated | Right color-aligned depth arrays. |

Linear depth filenames are timestamp stems with `.png` extension.
Color-aligned depth filenames are timestamp stems with `.npy` extension.
Depth confidence filenames are timestamp stems with `.npz` extension.

---

# Legacy Dataset and Cache Locations

The following legacy dataset and cache locations are stable compatibility targets:

| Path | Owner | Description |
| --- | --- | --- |
| `dataset/left_camera_dataset.npz` | generated | Left color dataset cache. |
| `dataset/right_camera_dataset.npz` | generated | Right color dataset cache. |
| `dataset/left_camera_dataset_optimized.npz` | generated | Left optimized color dataset cache. |
| `dataset/right_camera_dataset_optimized.npz` | generated | Right optimized color dataset cache. |
| `dataset/left_depth_dataset.npz` | generated | Left depth dataset cache. |
| `dataset/right_depth_dataset.npz` | generated | Right depth dataset cache. |
| `dataset/left_depth_dataset_optimized.npz` | generated | Left optimized depth dataset cache. |
| `dataset/right_depth_dataset_optimized.npz` | generated | Right optimized depth dataset cache. |
| `cache/dataset/` | generated | Fragment depth dataset cache directory. |
| `cache/pcd/` | generated | Fragment point-cloud cache directory. |

Dataset file contents are specified in `DATASETS_AND_CACHE.md`.

---

# Legacy Reconstruction Output Layout

The following legacy reconstruction outputs are stable compatibility targets:

| Path | Owner | Description |
| --- | --- | --- |
| `reconstruction/colorless_vbg.npz` | generated | Colorless voxel block grid cache. |
| `reconstruction/color_mesh.ply` | generated | Colored reconstructed mesh. |
| `reconstruction/color.ply` | generated | Colored reconstructed point cloud. |

Open3D-specific object serialization details are owned by reconstruction-specific specifications when added.

---

# Legacy Relative Path Convention

Legacy dataset records store frame directories as paths relative to the project directory.

Examples:

* `left_camera_rgb`
* `right_camera_rgb`
* `left_depth`
* `right_depth`

Consumers must resolve these paths against the project directory or an explicitly documented dataset root.

---

# Package Migration Requirement

New package APIs must not assume legacy output-in-input behavior by default.

Package APIs that generate artifacts must accept an explicit output location or an explicit layout object before writing derived data.

Legacy-compatible APIs may still write into the project directory when their names, options, or documentation make that behavior explicit.
