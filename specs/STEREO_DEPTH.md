# Stereo Depth Specification

## Purpose

This document defines package behavior for generating rectified stereo depth maps and compatibility color-aligned depth maps from stereo color frames.

It owns requirements for:

* FoundationStereo ONNX workflow behavior
* stereo color frame pairing
* rectified stereo image/depth placement
* compatibility color-aligned depth placement
* disparity-to-depth conversion
* optional ONNX Runtime dependency boundaries

Public API boundaries are specified in `PUBLIC_API.md`.
Packaging dependency profiles are specified in `PACKAGING.md`.
CLI behavior is specified in `CLI_BEHAVIOR.md`.
Legacy output locations are specified in `PROJECT_LAYOUT.md`.

---

# FoundationStereo ONNX Workflow

The package exposes a FoundationStereo depth workflow through:

```python
from mq3drecon.config import FoundationStereoConfig
from mq3drecon.workflows import run_foundation_stereo_depth
```

The workflow consumes left and right color camera frames, rectifies them into a horizontal stereo pair, and writes left-view rectified stereo depth maps. It can also write left-view color-aligned depth maps as a compatibility artifact when `FoundationStereoConfig.save_color_aligned_depth` is enabled. It must not generate right-view depth by swapping model inputs because that output is not part of the supported FoundationStereo workflow contract.

---

# Model Input and Output Contract

The ONNX model must accept two tensor inputs representing the left and right images and produce a disparity tensor.

The expected static tensor layout is:

```text
left_image  [1, 3, H, W] tensor(float)
right_image [1, 3, H, W] tensor(float)
disparity   [1, 1, H, W] tensor(float)
```

The workflow must inspect the ONNX session input metadata at runtime to determine the model input height and width when those dimensions are static.

When the ONNX model uses dynamic spatial dimensions, callers must provide `input_height` and `input_width` through `FoundationStereoConfig`.

---

# Stereo Rectification

The workflow must rectify left and right color frames before stereo inference. Rectification must use the loaded left/right intrinsics and per-frame relative camera pose. When distortion coefficients are unavailable, the workflow may assume zero lens distortion. When `FoundationStereoConfig.cache_rectification_maps` is enabled, implementations may reuse rectification maps for frames with the same image size, intrinsics, and relative stereo geometry. Rectification-map caches must remain bounded and must not retain one full-resolution map set per processed frame.

When `FoundationStereoConfig.skip_existing_outputs` is enabled, the workflow must skip ONNX disparity inference for a frame whose native rectified stereo depth output already exists. The workflow may still rebuild dataset metadata, missing rectified color images, debug PNGs, or requested compatibility color-aligned outputs from existing depth maps. When the option is disabled, the workflow must recompute and overwrite generated stereo outputs.

The rectified left and right color frames must be saved as a dataset. The rectified left depth dataset must store intrinsics derived from the rectified left projection matrix, not the original left color intrinsics. The rectified left camera pose must be updated consistently with the left rectification rotation. Dataset and rectification metadata must store compact geometry arrays such as projection matrices, rectification matrices, baselines, timestamps, and intrinsics; they must not persist or accumulate full-resolution rectification maps.

The workflow must keep compatibility color-aligned depth output separate from the rectified stereo depth dataset. Color-aligned depth is a derived compatibility view and must not replace the native rectified stereo depth used for stereo reconstruction. Implementations should avoid building inverse rectification maps when compatibility color-aligned depth output and compatibility PNG output are disabled.

# Image Preprocessing

The workflow must resize rectified color frames to the model input size before inference.

When `preserve_aspect_ratio` is enabled, the workflow must preserve the original aspect ratio, pad the resized image to the model input size, and remove the padding from the output disparity before saving depth.

When disparity is resized back to the source color image resolution, the disparity values must be scaled back to the source image pixel coordinate system.

---

# Stereo Pairing

For MRUK recordings, `mruk_stereo_pairs.csv` is the preferred source of left/right frame pairing when present.

For recordings without an MRUK stereo pair CSV, the workflow may pair frames by nearest timestamp. If `max_pair_timestamp_delta_us` is configured, pairs whose timestamp delta exceeds that limit must be skipped.

If no stereo pairs remain, the workflow must raise an explicit error.

---

# Disparity to Depth

The workflow converts disparity to metric depth with:

```text
depth_m = fx_px * baseline_m / disparity_px
```

`fx_px` must come from the rectified left projection matrix. `baseline_m` may be supplied explicitly through configuration. When it is not supplied, the workflow must use the rectified stereo baseline derived from the projection matrices when available, or the per-frame relative camera translation as a fallback.

Disparity values less than or equal to `min_disparity` must not produce finite depth values.

When `max_depth_m` is configured, values greater than that depth must not produce finite depth values.

---

# Output Artifacts

The workflow supports only left-view FoundationStereo depth output. Configuration must reject requests to generate right-view FoundationStereo depth.

The workflow writes native rectified `.npy` depth maps through `RGBDDataIO.save_rectified_stereo_depth`. When `FoundationStereoConfig.save_color_aligned_depth` is enabled, it also writes compatibility `.npy` color-aligned depth maps through `RGBDDataIO.save_color_aligned_depth`.

When `FoundationStereoConfig.save_rgba_png` is enabled, the workflow also writes decoded color-frame PNG files for inspection. For MRUK `.rgba` inputs, these PNG files must reflect the same decoded and vertically oriented image array used by stereo inference.

When `FoundationStereoConfig.save_depth_png` is enabled, `FoundationStereoConfig.save_color_aligned_depth` must also be enabled, and the workflow writes generated compatibility color-aligned depth as 16-bit PNG files using `depth_png_scale` units per meter. Invalid or non-positive depth values must be written as zero.

When `FoundationStereoConfig.save_depth_preview_png` is enabled, `FoundationStereoConfig.save_color_aligned_depth` must also be enabled, and the workflow writes generated compatibility color-aligned depth as 8-bit preview PNG files for visual inspection. Preview values must be normalized linearly from `depth_preview_min_m` to `depth_preview_max_m` when a maximum is configured. If the preview maximum is not configured, the workflow may use a finite positive depth percentile or another deterministic fallback suitable for visualization. Invalid or non-positive depth values must be written as zero.

Saved `.npy` compatibility color-aligned depth maps may also be exported to PNG files after generation through the package workflow `run_color_aligned_depth_to_png` or the CLI command `color-aligned-depth-to-png`. Post-hoc metric PNG export must use the same 16-bit scaling rule as generated metric PNG output. Post-hoc preview export must use the same 8-bit normalization and invalid-depth handling as generated preview PNG output.

Legacy output directories are:

```text
left_rectified_stereo_color/
right_rectified_stereo_color/
left_rectified_stereo_depth/
dataset/left_rectified_stereo_color_dataset.npz
dataset/right_rectified_stereo_color_dataset.npz
dataset/left_rectified_stereo_depth_dataset.npz
dataset/stereo_rectification.npz
left_color_aligned_depth/              # only when compatibility color-aligned depth output is enabled
left_camera_mruk_rgba_png/
right_camera_mruk_rgba_png/
left_color_aligned_depth_png/
left_color_aligned_depth_preview_png/
```

The saved depth map timestamp must match the paired left color frame timestamp.

---


# Example Pipeline Configuration

The FoundationStereo example pipeline config may combine `foundation_stereo` and
`reconstruction` sections because stereo depth generation and rectified-stereo
reconstruction are the common offline pipeline pair. That example should not
include Quest raw-depth conversion, Quest depth confidence estimation, Quest depth
pose optimization, or color-aligned depth rendering settings unless those steps
become part of a documented stereo workflow.

# Dependency Boundary

`onnxruntime` is an optional stereo dependency.

Importing lightweight public modules must not require `onnxruntime`. The workflow may require `onnxruntime` only when an ONNX model runner is constructed for actual inference.
