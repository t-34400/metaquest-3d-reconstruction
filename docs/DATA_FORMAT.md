# Data Format Reference

This document describes MQ3DRecon dataset layouts, timestamps, coordinate conventions, camera datasets, depth formats, and generated artifacts.

For command-line workflows, see [CLI.md](CLI.md). For public Python API usage, see [API.md](API.md). For pipeline selection, see [PIPELINES.md](PIPELINES.md).

## Capture backend detection

MQ3DRecon supports legacy Quest Reality Capture layouts and MRUK layouts.

The capture backend is detected from the project directory:

- `session_info.json` with `backend: "MRUK"` identifies an MRUK capture.
- Legacy Camera2-style captures are handled through the legacy layout.
- Code that consumes color frames should use backend-aware dataset and image loaders instead of reconstructing paths manually.

## Timestamp conventions

Frame filenames and dataset timestamps use integer timestamp stems. For example:

```text
1781849907379988.rgba
1781849907379988.png
1781849907379988.npy
```

For MRUK color frames, `timestamp_us_realtime` from the per-frame metadata CSV is used as the dataset timestamp. The source `.rgba` filename stem should match that timestamp.

The current documented contract is:

- timestamps are integer values;
- MRUK metadata exposes them through the `timestamp_us_realtime` column;
- generated files preserve the source timestamp stem;
- left/right stereo and RGBD matching uses these integer timestamps.

Do not assume that these values are Unix epoch timestamps unless the capture source explicitly documents that. Treat them as capture timestamps suitable for ordering, matching, and file lookup.

## Legacy project layout

Legacy captures may contain these source directories:

| Path | Description |
| --- | --- |
| `left_camera_raw/` | Left raw `YUV_420_888` frames. |
| `right_camera_raw/` | Right raw `YUV_420_888` frames. |
| `left_depth/` | Left Quest native depth frames. |
| `right_depth/` | Right Quest native depth frames. |
| `hmd_poses.csv` | HMD pose stream used by legacy workflows. |

Generated legacy RGB exports are written under:

| Path | Description |
| --- | --- |
| `left_camera_rgb/` | Left generated RGB PNG frames. |
| `right_camera_rgb/` | Right generated RGB PNG frames. |

New code should prefer `ImageDataIO.load_rgb(side, timestamp)` or `load_color_dataset()` over direct path reconstruction.

## MRUK project layout

MRUK captures use backend-specific color frame, intrinsics, metadata, and stereo-pair files:

| Path | Description |
| --- | --- |
| `left_camera_mruk_rgba/` | Left raw RGBA32 frames. |
| `right_camera_mruk_rgba/` | Right raw RGBA32 frames. |
| `left_camera_mruk_intrinsics.json` | Left MRUK camera intrinsics. |
| `right_camera_mruk_intrinsics.json` | Right MRUK camera intrinsics. |
| `left_camera_mruk_frame_metadata.csv` | Left per-frame MRUK metadata. |
| `right_camera_mruk_frame_metadata.csv` | Right per-frame MRUK metadata. |
| `mruk_stereo_pairs.csv` | Left/right frame correspondence metadata. |

Generated MRUK PNG previews are written under:

| Path | Description |
| --- | --- |
| `left_camera_mruk_rgba_png/` | Left generated PNG previews converted from MRUK RGBA frames. |
| `right_camera_mruk_rgba_png/` | Right generated PNG previews converted from MRUK RGBA frames. |

Source `.rgba` files are immutable inputs. Generated PNG filenames preserve the source timestamp stem and use the `.png` extension.

## MRUK RGBA frames

MRUK color frames are raw RGBA32 buffers with no file header.

The expected byte size is:

```text
width * height * 4
```

The raw buffer is stored in bottom-up row order. MQ3DRecon's MRUK color image loaders vertically flip the reshaped frame so downstream consumers see top-down RGB/RGBA images, matching legacy Camera2 RGB PNG orientation.

This vertical flip is MRUK-specific. It must not be applied to legacy YUV or RGB PNG readers.

When callers request RGB images, the alpha channel is hidden and only the first three channels are returned.

## MRUK intrinsics schema

MRUK intrinsics use the observed nested JSON schema:

```json
{
  "backend": "MRUK",
  "imageFormat": "RGBA32",
  "focalLength": { "x": 0.0, "y": 0.0 },
  "principalPoint": { "x": 0.0, "y": 0.0 },
  "resolution": { "width": 1280, "height": 1280 }
}
```

The dataset mapping is:

| Dataset field | MRUK source |
| --- | --- |
| `fx` | `focalLength.x` |
| `fy` | `focalLength.y` |
| `cx` | `principalPoint.x` |
| `cy` | `principalPoint.y` |
| `widths` | frame metadata width |
| `heights` | frame metadata height |

## MRUK frame metadata schema

MRUK color dataset construction uses `timestamp_us_realtime` as the dataset timestamp and `file_name` as the image filename.

Per-frame camera pose comes from:

```text
pose_pos_x, pose_pos_y, pose_pos_z
pose_rot_x, pose_rot_y, pose_rot_z, pose_rot_w
```

Frames are skipped when any of these flags are false:

```text
pose_ok
get_texture_ok
get_colors_ok
```

If no valid MRUK color frames remain, dataset construction fails with an explicit error.

## Pose and coordinate conventions

MRUK per-frame poses are camera-to-world poses in Unity coordinates.

Quaternion values are stored in this order:

```text
x, y, z, w
```

`CameraDataset` stores poses through the shared transform schema:

| Field | Meaning |
| --- | --- |
| `positions` | Camera positions, shape `(N, 3)`. |
| `rotations` | Camera rotations as quaternions, shape `(N, 4)`, ordered `(x, y, z, w)`. |
| `coordinate_system` | Coordinate system enum name for the stored poses. |

Public transform helpers expose both camera-to-world and world-to-camera matrices:

| Field | Meaning |
| --- | --- |
| `extrinsics_cw` | Camera-to-world transforms. |
| `extrinsics_wc` | World-to-camera transforms. |

OpenCV and COLMAP-style consumers usually need world-to-camera transforms. Use the public transform helpers instead of inverting pose matrices manually in downstream code.

## Camera dataset `.npz` schema

Camera dataset caches are persistent compatibility artifacts. A camera dataset `.npz` contains:

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

All per-frame arrays must have the same first dimension `N`.

Legacy color dataset cache files are:

```text
dataset/left_camera_dataset.npz
dataset/right_camera_dataset.npz
dataset/left_camera_dataset_optimized.npz
dataset/right_camera_dataset_optimized.npz
```

## Depth dataset `.npz` schema

Depth datasets use the camera dataset schema and additionally contain:

| Key | Type | Shape | Description |
| --- | --- | --- | --- |
| `nears` | numeric array | `(N,)` | Per-frame near clipping plane used for depth conversion. |
| `fars` | numeric array | `(N,)` | Per-frame far clipping plane used for depth conversion. |

Legacy depth dataset cache files are:

```text
dataset/left_depth_dataset.npz
dataset/right_depth_dataset.npz
dataset/left_depth_dataset_optimized.npz
dataset/right_depth_dataset_optimized.npz
```

## Depth formats

MQ3DRecon uses multiple depth representations depending on the workflow.

| Depth source | Typical path | Coordinate frame |
| --- | --- | --- |
| Quest native depth | `left_depth/`, `right_depth/` and derived linear outputs | Quest depth camera frame. |
| Rectified stereo depth | `left_rectified_stereo_depth/*.npy` | Rectified left stereo image frame. |
| Compatibility color-aligned depth | `left_color_aligned_depth/*.npy` | Original LEFT color image frame. |

Compatibility color-aligned depth maps are derived from stereo depth and expressed in the original LEFT color coordinate system. New geometry code should prefer rectified stereo RGBD artifacts when using FoundationStereo depth.

Public color-aligned depth loaders return finite positive metric depth as `float32` and replace invalid or non-positive values with zero.

## FoundationStereo generated artifacts

FoundationStereo depth generation writes primary rectified stereo outputs:

```text
left_rectified_stereo_color/*.png
right_rectified_stereo_color/*.png
left_rectified_stereo_depth/*.npy
dataset/left_rectified_stereo_color_dataset.npz
dataset/right_rectified_stereo_color_dataset.npz
dataset/left_rectified_stereo_depth_dataset.npz
dataset/stereo_rectification.npz
```

When compatibility color-aligned depth output is enabled, it also writes:

```text
left_color_aligned_depth/*.npy
```

Optional PNG exports are:

```text
left_color_aligned_depth_preview_png/  # 8-bit visual previews
left_color_aligned_depth_png/          # 16-bit metric PNGs when --metric is used
```

Saved depth map timestamps match the paired left color frame timestamp.

## COLMAP export format

COLMAP export consumes color images through the format-aware color image loader. It must not assume legacy `left_camera_rgb/` or `right_camera_rgb/` PNG paths.

When exporting MRUK RGBA frames, the exporter writes PNG images into the selected COLMAP export image directory and leaves source `.rgba` files unchanged.

## MRUK map data

MRUK map, anchor, plane, volume, or mesh files are not currently documented as a stable MQ3DRecon input schema in this package. If these files are added to the public contract later, this document should define:

- file paths and filenames;
- JSON or binary schemas;
- units;
- coordinate frame;
- anchor, plane, volume, and mesh semantics;
- compatibility guarantees.
