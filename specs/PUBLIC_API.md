# Public API Specification

## Purpose

This document defines the intended public API boundary for the installable MQ3DRecon package.

It owns requirements for:

* package import namespace
* CLI and library separation
* public versus internal module stability
* output location expectations for package APIs
* migration compatibility for legacy scripts

Legacy filesystem layout is specified in `LEGACY_BEHAVIOR.md`.
Dataset and cache schemas are specified in `DATASETS_AND_CACHE.md`.

---

# Package Namespace

The long-term supported package namespace is:

```python
mq3drecon
```

Public imports must be exposed through `mq3drecon.*` modules.

Code outside the package must not be required to import from top-level implementation directories such as:

```python
config
models
dataio
pipeline
processing
utils
```

Those names may exist internally during migration but are not stable public APIs.

---

# Package Layout Direction

The installable package should be organized under a source package layout such as:

```text
src/mq3drecon/
```

The exact package tree may evolve, but package modules must be importable after installation and must not rely on direct execution from the repository root or `scripts/` directory.

---

# Public API Ownership

Only documented symbols exported from `mq3drecon.*` are public APIs.

A symbol is public only when at least one specification or API reference document explicitly identifies it as public.

Undocumented modules, helper functions, and legacy script internals may change without public API compatibility guarantees.

---

# Recommended Public API Areas

The package should expose focused APIs for:

* domain models
* project layout resolution
* dataset loading and saving
* color conversion workflows
* depth conversion workflows
* reconstruction workflows
* COLMAP export workflows

High-level convenience facades may exist, but they must not become the only owner of unrelated responsibilities.

---

# CLI Boundary

CLI entrypoints must handle command-line concerns only:

* argument parsing
* environment-facing messages
* process exit behavior
* conversion from CLI arguments to library configuration objects

Business logic must live in library modules and be callable without invoking a CLI process.

A CLI command may call one or more library APIs, but must not be the sole implementation of a processing workflow.

---

# Legacy Script Compatibility

Existing `scripts/*.py` entrypoints may remain as migration shims.

A legacy script shim should delegate to package APIs when the corresponding package API exists.

Legacy scripts are not the long-term public library interface.

Compatibility for legacy script command behavior must be documented in a CLI-specific specification before it is treated as stable.

---

# Output Location Policy

Package APIs must not silently write generated artifacts into input capture directories by default.

Any API that writes generated artifacts must use one of the following patterns:

1. accept an explicit `output_dir`,
2. accept an explicit layout object, or
3. use an explicitly named legacy compatibility mode.

Legacy compatibility mode may write into the project directory only when that behavior is clear from the API name, configuration, or documentation.

---

# Heavy Optional Dependencies

Public modules that only define lightweight data structures, schemas, path layouts, or configuration parsing must not require importing heavy reconstruction dependencies such as Open3D.

Open3D-dependent imports must be isolated to reconstruction-specific modules or lazily resolved where practical.

Device selection must be explicit or safely portable. CPU-compatible defaults are required for package configuration objects and tests unless a caller explicitly requests another device.

---

# Validation and Error Policy

Library APIs must report invalid inputs through exceptions that callers can catch.

Library APIs must not depend on printed messages as the only failure signal.

CLI commands may convert exceptions into user-facing messages and process exit statuses.

---

# Compatibility During Migration

During migration from `scripts/` to `mq3drecon`, compatibility may be provided through aliases or wrappers.

Aliases for misspelled legacy names may be retained only as compatibility shims.

New public API names must use correct spelling and clear ownership boundaries.
---

# Currently Documented Public Symbols

The following package-level symbols are currently documented as public during migration.

## `mq3drecon.models`

* `CameraDataset`
* `DepthDataset`
* `Side`
* `CoordinateSystem`
* `Transforms`

## `mq3drecon.config`

Lightweight configuration exports:

* `Depth2LinearConfig`
* `Yuv2RgbConfig`
* `ProjectPathConfig`

Reconstruction and pipeline configuration exports are public and must remain importable without reconstruction-specific optional dependencies such as Open3D:

* `PipelineConfigs`
* `ReconstructionConfig`
* `DepthConfidenceEstimationConfig`
* `FragmentGenerationConfig`
* `FragmentPoseRefinementConfig`
* `IntegrationConfig`
* `ColorOptimizationConfig`
* `ColorAlignedDepthRenderingConfig`

## `mq3drecon.dataio`

Data I/O facade exports are public migration APIs:

* `DataIO`
* `ImageDataIO`
* `DepthDataIO`
* `RGBDDataIO`
* `ReconstructionDataIO`

## `mq3drecon.processing.yuv_conversion`

* `convert_yuv_directory`

## `mq3drecon.processing.depth_conversion`

* `convert_depth_directory`

## `mq3drecon.workflows`

Package-backed workflow APIs for legacy-compatible commands:

* `run_yuv_to_rgb`
* `run_depth_to_linear`
* `export_colmap_project`

## `mq3drecon.pipeline`

* `PipelineProcessor`

## `mq3drecon.layouts`

Path layout exports are public migration APIs:

* `LegacyProjectLayout`
* `PackageOutputLayout`
* `ColmapExportLayout`
