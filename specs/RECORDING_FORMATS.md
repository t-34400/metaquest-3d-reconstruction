# Recording Formats Specification

## Purpose

This document defines capture recording format detection and non-legacy recording
format requirements.

Legacy Camera2 path names remain specified in `LEGACY_BEHAVIOR.md`. Dataset cache
schemas remain specified in `DATASETS_AND_CACHE.md`.

---

# Capture Backend Detection

Readers that select a color processing path must inspect `session_info.json` when
it exists in the project directory.

Supported values are:

| `captureBackend` | Behavior |
| --- | --- |
| `NativeCamera2` | Use the legacy Camera2 color path. |
| `MRUK` | Use the MRUK color path. |

When `session_info.json` is absent, readers must treat the recording as a legacy
Camera2 recording for backward compatibility.

Unsupported `captureBackend` values must raise an explicit error.

---

# MRUK Color Input Layout

MRUK color recordings use the following paths relative to the project directory:

| Path | Description |
| --- | --- |
| `session_info.json` | Capture backend and session format metadata. |
| `left_camera_mruk_rgba/` | Left raw RGBA32 frames. |
| `right_camera_mruk_rgba/` | Right raw RGBA32 frames. |
| `left_camera_mruk_intrinsics.json` | Left MRUK camera intrinsics. |
| `right_camera_mruk_intrinsics.json` | Right MRUK camera intrinsics. |
| `left_camera_mruk_frame_metadata.csv` | Left per-frame MRUK metadata. |
| `right_camera_mruk_frame_metadata.csv` | Right per-frame MRUK metadata. |
| `mruk_stereo_pairs.csv` | Left/right frame correspondence metadata. |

MRUK frame filenames are timestamp stems with `.rgba` extension.

---

# MRUK RGBA Frames

MRUK color frames are raw RGBA32 buffers with no file header.

The expected byte size for each frame is:

```text
width * height * 4
```

MRUK readers must validate the on-disk byte size before reshaping an RGBA frame.

---

# MRUK Intrinsics Schema

The MRUK intrinsics reader must support the observed nested schema:

```json
{
  "backend": "MRUK",
  "imageFormat": "RGBA32",
  "focalLength": { "x": 0.0, "y": 0.0 },
  "principalPoint": { "x": 0.0, "y": 0.0 },
  "resolution": { "width": 1280, "height": 1280 }
}
```

The resulting dataset fields must map as:

| Dataset field | MRUK source |
| --- | --- |
| `fx` | `focalLength.x` |
| `fy` | `focalLength.y` |
| `cx` | `principalPoint.x` |
| `cy` | `principalPoint.y` |
| `widths` | frame metadata width |
| `heights` | frame metadata height |

---

# MRUK Frame Metadata Schema

MRUK color dataset construction must use `timestamp_us_realtime` as the dataset
timestamp and `file_name` as the image filename.

Per-frame camera pose must come directly from these frame metadata columns:

```text
pose_pos_x, pose_pos_y, pose_pos_z
pose_rot_x, pose_rot_y, pose_rot_z, pose_rot_w
```

The pose is a camera-to-world pose in Unity coordinates and must be stored in the
existing `CameraDataset` transform schema with `CoordinateSystem.UNITY`.

MRUK color dataset construction must not interpolate color camera poses from
`hmd_poses.csv`.

Frames with any of the following false values must be skipped:

```text
pose_ok
get_texture_ok
get_colors_ok
```

If no valid MRUK color frames remain, dataset construction must raise an explicit
error.

---

# Depth Optionality

MRUK color dataset construction must not require depth inputs.

Recordings made with depth disabled may contain no depth files, or may contain
empty depth directories. This must not prevent MRUK color dataset construction.

---

# MRUK COLMAP Export

COLMAP export must consume color images through the format-aware color image
loader instead of assuming legacy `left_camera_rgb/` or `right_camera_rgb/` PNG
paths.

When exporting MRUK RGBA frames, the exporter must write COLMAP image outputs as
PNG files under the selected COLMAP export image directory. Source `.rgba` files
must remain immutable.
