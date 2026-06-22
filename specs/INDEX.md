# Specification Index

## Purpose

This document is the navigation index for MQ3DRecon specifications.

It lists specification documents, their responsibility boundaries, and when each
specification must be read before making a change.

This document must not define behavioral requirements. Behavioral requirements
belong in topic-specific specifications or `COMMON_RULES.md`.

---

# Required First Read

Before modifying specifications, tests, or implementation, read:

1. `specs/COMMON_RULES.md`
2. This document

Then read every topic-specific specification relevant to the affected behavior.

---

# Project-Wide Rules

## `COMMON_RULES.md`

Defines project-wide specification authority, architecture expectations,
complexity management rules, compatibility policy, and change-management
principles.

Read this before every specification, test, or implementation change.

---

# Topic Specifications

## `LEGACY_BEHAVIOR.md`

Navigation for legacy project layout and compatibility rules.

Read when changing:

* legacy input or output directory names
* project-relative path resolution
* generated artifact locations
* migration behavior for existing script workflows

Related tests: none currently identified.

## `RECORDING_FORMATS.md`

Navigation for capture backend detection and non-legacy recording formats.

Read when changing:

* capture backend detection
* MRUK input layout handling
* MRUK color frame, intrinsics, or metadata parsing
* color reader dispatch between legacy Camera2 and MRUK

Related tests: `tests/test_recording_format_detection.py`, `tests/test_mruk_color_dataset.py`.

## `DATASETS_AND_CACHE.md`

Navigation for persistent dataset and cache schemas.

Read when changing:

* `.npz` dataset serialization or loading
* dataset cache file names or contents
* optimized dataset compatibility
* fragment dataset cache behavior
* cache fallback or rebuild behavior

Related tests: none currently identified.

## `PUBLIC_API.md`

Navigation for installable package API boundaries.

Read when changing:

* package namespace or import paths
* CLI-to-library separation
* public module exports
* output directory behavior in package APIs
* dependency boundaries for public modules

Related tests: none currently identified.



## `PACKAGING.md`

Navigation for pip installation profiles and optional dependency boundaries.

Read when changing:

* package dependency metadata
* optional extras such as lightweight, conversion, reconstruction, or full installs
* Open3D dependency placement
* default pip installation behavior

Related tests: `tests/test_packaging_metadata.py`, `tests/test_public_api_imports.py`.


## `RECONSTRUCTION_CONFIG.md`

Navigation for reconstruction configuration structure and dependency boundaries.

Read when changing:

* reconstruction configuration classes or parsing behavior
* per-step reconstruction config module ownership
* Open3D dependency boundaries in configuration modules
* compatibility exports from `mq3drecon.config.reconstruction_config`

Related tests: `tests/test_reconstruction_config.py`.

## `CLI_BEHAVIOR.md`

Navigation for command-line interface behavior and migration shims.

Read when changing:

* `scripts/*.py` command behavior
* package-backed CLI wrappers
* command-line arguments or defaults
* CLI error messages or exit statuses
* visualization behavior exposed through commands

Related tests: none currently identified.

## `PROJECT_LAYOUT.md`

Navigation for filesystem layout abstractions and generated artifact placement.

Read when changing:

* project path helper classes or functions
* legacy output location behavior
* package output directory behavior
* COLMAP export path construction
* relative path resolution for generated artifacts

Related tests: none currently identified.


## `STEREO_DEPTH.md`

Navigation for stereo color-frame depth generation workflows.

Read when changing:

* FoundationStereo ONNX inference behavior
* stereo color frame pairing
* disparity-to-depth conversion
* rectified stereo depth output and compatibility color-aligned depth output produced from stereo images
* stereo optional dependency boundaries

Related tests: `tests/test_foundation_stereo_workflow.py`, `tests/test_packaging_metadata.py`, `tests/test_public_api_imports.py`.

## `LOGGING_AND_ERRORS.md`

Navigation for library error reporting, typed project exceptions, logging, and CLI error conversion.

Read when changing:

* library exception behavior
* project-specific exception classes
* logging behavior in package modules
* CLI handling of expected failures
* migration away from print-only error reporting

Related tests: none currently identified.

Expected future specification areas include:

* reconstruction configuration and Open3D dependency boundaries
* visualization and headless execution behavior

When adding more topic-specific specifications, each entry should describe only navigation information:

* document path
* responsibility boundary
* when to read it
* related tests, if known

Do not duplicate behavioral requirements from the target specification.

---

# Current Implementation Areas

The package implementation is primarily organized under `src/mq3drecon/`.
Legacy modules under `scripts/` are retained as command entrypoints or compatibility
wrappers while migration support is required.

Use this section only as a navigation aid.

| Area | Current location | Legacy compatibility location | Notes |
| --- | --- | --- | --- |
| CLI entry points | `scripts/*.py` | N/A | Commands delegate to package workflows when a workflow API exists. |
| Configuration | `src/mq3drecon/config/` | `scripts/config/` | Legacy imports are compatibility wrappers. |
| Data I/O | `src/mq3drecon/dataio/` | `scripts/dataio/` | Legacy imports are compatibility wrappers. |
| Data models | `src/mq3drecon/models/` | `scripts/models/` | Legacy imports are compatibility wrappers. |
| Pipeline orchestration | `src/mq3drecon/pipeline/` | `scripts/pipeline/` | Legacy imports are compatibility wrappers. |
| Processing implementation | `src/mq3drecon/processing/` | `scripts/processing/` | Legacy imports are compatibility wrappers. |
| Utilities | `src/mq3drecon/utils/` | `scripts/utils/` | Legacy imports are compatibility wrappers. |
| Third-party code | `src/mq3drecon/third_party/` | `scripts/third_party/` | Legacy imports are compatibility wrappers. |

---

# Adding a New Specification

When adding a specification:

1. Choose a focused responsibility boundary.
2. Add the specification document under `specs/`.
3. Add a navigation entry to this index.
4. Keep behavioral requirements in the new specification, not in this index.
5. Update related tests and implementation when behavior changes.

