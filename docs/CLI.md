# Command-Line Usage

This guide is for users who run MQ3DRecon through the `mq3drecon` command.

For installation details, see [INSTALLATION.md](INSTALLATION.md). For pipeline selection, see [PIPELINES.md](PIPELINES.md). For stereo model details, see [MODELS.md](MODELS.md). For dataset conventions and file formats, see [DATA_FORMAT.md](DATA_FORMAT.md).

## Command-line interface

The package exposes the `mq3drecon` command:

```bash
mq3drecon --help
```

Show command-specific help:

```bash
mq3drecon depth-to-linear --help
mq3drecon foundation-stereo-depth --help
mq3drecon reconstruct --help
mq3drecon export-colmap --help
mq3drecon visualize-cameras --help
mq3drecon yuv-to-rgb --help
mq3drecon rgba-to-png --help
```

Legacy scripts under `scripts/` remain available as migration shims. New automation should prefer the package-backed `mq3drecon` command.

## Configuration files

Conversion, stereo depth generation, and reconstruction workflows provide built-in defaults. Use `--config` only when you need to override default settings. Example pipeline configs are organized by depth source:

```text
config/pipeline_config.yml          # Quest raw depth pipeline
config/pipeline_config_stereo.yml   # FoundationStereo depth plus rectified-stereo reconstruction
```

```bash
mq3drecon reconstruct \
  --project-dir path/to/project \
  --config config/pipeline_config.yml
```

The stereo example config intentionally contains only `foundation_stereo` and `reconstruction` sections. Quest raw-depth conversion, confidence estimation, depth pose optimization, and color-aligned depth rendering settings belong in the Quest pipeline config.

The CLI accepts both kebab-case and legacy underscore forms for the project and config options where migration compatibility is supported.

## Common command sequences

### Generate FoundationStereo rectified stereo depth

```bash
mq3drecon foundation-stereo-depth \
  --project-dir path/to/project \
  --config config/pipeline_config_stereo.yml \
  --model-path path/to/foundation_stereo.onnx
```

The FoundationStereo workflow reads color frames through the backend-aware color dataset API. It works with legacy Camera2 captures and MRUK captures without requiring a separate YUV or RGBA-to-PNG conversion step.

The workflow rectifies the left/right color frames before inference and writes the primary stereo outputs in rectified stereo coordinates:

```text
left_rectified_stereo_color/*.png
right_rectified_stereo_color/*.png
left_rectified_stereo_depth/*.npy
dataset/left_rectified_stereo_color_dataset.npz
dataset/right_rectified_stereo_color_dataset.npz
dataset/left_rectified_stereo_depth_dataset.npz
dataset/stereo_rectification.npz
```

For compatibility with older tooling, it also writes depth mapped back to the original LEFT color coordinate system:

```text
left_color_aligned_depth/*.npy
```

Optional config flags can also write decoded color PNGs and compatibility color-aligned depth maps. Compatibility color-aligned depth is useful for legacy tools, but disabling it avoids the inverse-rectification and extra I/O cost when reconstruction uses rectified stereo RGBD directly. Metric and preview PNG export require compatibility color-aligned depth output. For rectified reconstruction-only runs, prefer:

```yaml
foundation_stereo:
  save_color_aligned_depth: false
  cache_rectification_maps: true
  skip_existing_outputs: true
```

Saved compatibility `.npy` depth maps can also be exported later:

```bash
mq3drecon color-aligned-depth-to-png \
  --project-dir path/to/project
```

By default this writes 8-bit visual previews under `left_color_aligned_depth_preview_png/`. Add `--metric` to also write 16-bit scaled metric PNG files under `left_color_aligned_depth_png/`.

### Reconstruct with default Quest depth settings

```bash
mq3drecon reconstruct \
  --project-dir path/to/project
```

This uses the default reconstruction configuration.

### Reconstruct from FoundationStereo depth

First generate stereo depth, then reconstruct with `reconstruction.depth_source` set to `rectified_stereo`:

```yaml
reconstruction:
  depth_source: rectified_stereo
  render_color_aligned_depth: false
```

Then run the reconstruction step with the same stereo pipeline config:

```bash
mq3drecon reconstruct \
  --project-dir path/to/project \
  --config config/pipeline_config_stereo.yml
```

When `depth_source: rectified_stereo` is selected, reconstruction first looks for LEFT rectified stereo RGBD artifacts and integrates those with rectified intrinsics. If rectified stereo artifacts are absent, it falls back to the compatibility LEFT color-aligned depth maps and original LEFT color frames. Quest depth confidence estimation, Quest depth pose optimization, and color-aligned depth rendering are skipped for this depth source. For backward compatibility, `depth_source: color_aligned` currently selects the same FoundationStereo reconstruction path and should be treated as a legacy alias.

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

### Optional export commands

The following commands export backend-native color or depth inputs into derived files. They are useful for inspection, cache generation, and external tools that need PNG files. They are not required before using `load_rgb()`, `load_color_dataset()`, FoundationStereo depth generation, COLMAP export, or reconstruction.

```bash
mq3drecon yuv-to-rgb \
  --project-dir path/to/project

mq3drecon rgba-to-png \
  --project-dir path/to/project

mq3drecon depth-to-linear \
  --project-dir path/to/project

mq3drecon color-aligned-depth-to-png \
  --project-dir path/to/project
```

`yuv-to-rgb` writes legacy Camera2 RGB exports under:

```text
left_camera_rgb/
right_camera_rgb/
```

`rgba-to-png` writes MRUK PNG previews under:

```text
left_camera_mruk_rgba_png/
right_camera_mruk_rgba_png/
```

`depth-to-linear` writes linearized Quest native depth outputs from the raw depth frame layout.

`color-aligned-depth-to-png` writes saved color-aligned `.npy` depth maps as 8-bit preview PNGs by default. Use `--metric` to also write 16-bit metric PNGs.

### Run the repository example script

The repository includes a convenience script that runs package CLI commands against a capture directory and writes generated exports under a separate output root:

```bash
examples/run_mq3drecon_pipeline.sh \
  path/to/project \
  path/to/output/root
```

For MRUK captures without depth frames, the script skips YUV and depth conversion, then exports the color camera dataset to a COLMAP project. Set `RUN_RECONSTRUCT=1` to run Open3D reconstruction when usable depth inputs are available, and set `RUN_VISUALIZE=1` to open the camera trajectory viewer.


## High-resolution rectified-stereo TSDF

For FoundationStereo / rectified-stereo reconstruction, set `reconstruction.depth_integration.mode` to `tiled` when a smaller `voxel_size` does not fit in GPU memory as a single Open3D `VoxelBlockGrid`. Tile size is configured in voxel units so that per-tile memory remains approximately stable when `voxel_size` changes.

```yaml
reconstruction:
  depth_source: "rectified_stereo"
  depth_integration:
    mode: "tiled"
    voxel_size: 0.005
    tile_size_voxels: 256
    tile_overlap_voxels: 24
```

Tiled mode writes intermediate tile meshes under `reconstruction/tiles/` and writes the merged mesh to the normal `reconstruction/color_mesh.ply` output.
