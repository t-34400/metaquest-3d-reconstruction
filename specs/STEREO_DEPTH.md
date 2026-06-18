# Stereo Depth Specification

## Purpose

This document defines package behavior for generating color-aligned depth maps from stereo color frames.

It owns requirements for:

* FoundationStereo ONNX workflow behavior
* stereo color frame pairing
* generated color-aligned depth placement
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

The workflow consumes left and right color camera frames and writes color-aligned depth maps to the legacy color-aligned depth directories when operating through `LegacyProjectLayout`.

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

# Image Preprocessing

The workflow must resize color frames to the model input size before inference.

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

`fx_px` must come from the color dataset for the output side. `baseline_m` may be supplied explicitly through configuration. When it is not supplied, the workflow may compute the baseline from paired camera positions in the loaded color datasets.

Disparity values less than or equal to `min_disparity` must not produce finite depth values.

When `max_depth_m` is configured, values greater than that depth must not produce finite depth values.

---

# Output Artifacts

The workflow writes `.npy` depth maps through `RGBDDataIO.save_color_aligned_depth`.

Legacy output directories are:

```text
left_color_aligned_depth/
right_color_aligned_depth/
```

The saved depth map timestamp must match the color frame timestamp for the side being written.

---

# Dependency Boundary

`onnxruntime` is an optional stereo dependency.

Importing lightweight public modules must not require `onnxruntime`. The workflow may require `onnxruntime` only when an ONNX model runner is constructed for actual inference.
