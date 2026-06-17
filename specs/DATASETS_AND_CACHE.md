# Datasets and Cache Specification

## Purpose

This document defines persistent dataset and cache schemas for MQ3DRecon.

It owns requirements for:

* camera dataset `.npz` files
* depth dataset `.npz` files
* optimized dataset cache compatibility
* fragment dataset cache naming
* cache validity expectations

Legacy path locations are specified in `LEGACY_BEHAVIOR.md`.
Public API ownership is specified in `PUBLIC_API.md`.

---

# General Dataset Requirements

Dataset `.npz` files are persistent compatibility artifacts.

Code that writes dataset `.npz` files must preserve documented keys, value meanings, and shape compatibility unless the schema version is explicitly changed in a future specification.

Current legacy dataset files do not contain an explicit schema version. Until a versioned format is introduced, readers must treat the documented key set as the legacy schema.

Dataset readers must fail with a clear exception when required keys are missing, arrays have incompatible lengths, or scalar metadata is inconsistent.

Input validation must not rely on Python `assert` statements because optimized Python execution can disable them.

---

# Shared Camera Dataset Schema

A camera dataset `.npz` file must contain the following keys:

| Key | Type | Shape | Description |
| --- | --- | --- | --- |
| `directory_relative_path` | string-compatible scalar | scalar | Frame directory relative to the dataset root or legacy project directory. |
| `image_file_names` | string array | `(N,)` | Frame filenames relative to `directory_relative_path`. |
| `timestamps` | integer array | `(N,)` | Frame timestamps. |
| `fx` | numeric array | `(N,)` | Focal length in x direction. |
| `fy` | numeric array | `(N,)` | Focal length in y direction. |
| `cx` | numeric array | `(N,)` | Principal point x coordinate. |
| `cy` | numeric array | `(N,)` | Principal point y coordinate. |
| `coordinate_system` | string-compatible scalar | scalar | Coordinate system enum name for poses. |
| `positions` | numeric array | `(N, 3)` | Camera positions. |
| `rotations` | numeric array | `(N, 4)` | Camera rotations as quaternions. |
| `widths` | integer array | `(N,)` | Frame widths in pixels. |
| `heights` | integer array | `(N,)` | Frame heights in pixels. |

`N` is the number of frames in the dataset.

All per-frame arrays must have the same first dimension `N`.

---

# Color Dataset Schema

A color dataset uses the shared camera dataset schema without additional required keys.

Legacy color dataset cache files are:

* `dataset/left_camera_dataset.npz`
* `dataset/right_camera_dataset.npz`
* `dataset/left_camera_dataset_optimized.npz`
* `dataset/right_camera_dataset_optimized.npz`

---

# Depth Dataset Schema

A depth dataset uses the shared camera dataset schema and must also contain:

| Key | Type | Shape | Description |
| --- | --- | --- | --- |
| `nears` | numeric array | `(N,)` | Per-frame near clipping plane used for depth conversion. |
| `fars` | numeric array | `(N,)` | Per-frame far clipping plane used for depth conversion. |

Legacy depth dataset cache files are:

* `dataset/left_depth_dataset.npz`
* `dataset/right_depth_dataset.npz`
* `dataset/left_depth_dataset_optimized.npz`
* `dataset/right_depth_dataset_optimized.npz`

---

# Optimized Dataset Compatibility

Optimized dataset files must use the same schema as their non-optimized source dataset type.

An optimized color dataset remains a color dataset.
An optimized depth dataset remains a depth dataset.

Optimization may change frame order, frame count, poses, or other per-frame values only when the optimization behavior is documented by the relevant processing specification.

---

# Fragment Dataset Cache Schema

Fragment dataset cache files must use the depth dataset schema.

Legacy fragment dataset filenames are stored under `cache/dataset/` and follow this pattern:

```text
{SIDE}_fragment_{index}_dataset.npz
```

Where:

* `{SIDE}` is `LEFT` or `RIGHT`.
* `{index}` is a zero-based integer fragment index.

Fragment dataset readers must not require both sides to be present unless the calling reconstruction workflow explicitly requires both sides.

---

# Depth Confidence Cache Files

Depth confidence cache files are stored as per-frame `.npz` files under the side-specific confidence directory documented in `LEGACY_BEHAVIOR.md`.

A future confidence-map specification must define the stable key schema before these files are treated as public compatibility artifacts.

Until that specification exists, depth confidence `.npz` files are implementation-owned cache artifacts.

---

# Cache Rebuild Behavior

Cache use must be explicit in configuration or API options.

When a cache file is missing and cache rebuilding is supported, the implementation may rebuild it from immutable source inputs and write the rebuilt artifact to the configured output layout.

When a cache file exists but is invalid, library APIs must raise a clear exception unless the API explicitly documents fallback rebuild behavior.

CLI commands may present user-friendly warnings, but must still return failure status when required output cannot be produced.

---

# Serialization Safety

Dataset `.npz` readers must not require pickle-enabled loading for the documented schema.

Object arrays must not be introduced into stable dataset schemas unless a future specification explicitly allows them and documents the security implications.
