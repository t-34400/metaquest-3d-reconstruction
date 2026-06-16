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

No topic-specific specifications have been added yet.

Expected future specification areas include:

* legacy project layout and compatibility
* installable package layout and public API boundaries
* command-line interface behavior
* dataset and cache file schemas
* reconstruction configuration and Open3D dependency boundaries
* COLMAP export behavior
* logging, exceptions, and validation behavior
* visualization and headless execution behavior

Add entries here when new topic-specific specifications are created.
Each entry should describe only navigation information:

* document path
* responsibility boundary
* when to read it
* related tests, if known

Do not duplicate behavioral requirements from the target specification.

---

# Current Implementation Areas

The current implementation is script-oriented and primarily organized under
`scripts/`.

Use this section only as a navigation aid while migrating toward a package
layout.

| Area | Current location | Notes |
| --- | --- | --- |
| CLI entry points | `scripts/*.py` | Thin and mixed CLI/library scripts currently coexist. |
| Configuration | `scripts/config/` | Includes pipeline, path, depth, YUV, and reconstruction configuration. |
| Data I/O | `scripts/dataio/` | Includes color, depth, RGBD, and reconstruction I/O facades. |
| Data models | `scripts/models/` | Includes datasets, transforms, camera characteristics, and enums. |
| Pipeline orchestration | `scripts/pipeline/` | Coordinates higher-level processing steps. |
| Processing implementation | `scripts/processing/` | Includes conversion and reconstruction implementation. |
| Utilities | `scripts/utils/` | Includes image, depth, and parallel helper utilities. |
| Third-party code | `scripts/third_party/` | Includes vendored COLMAP utilities. |

---

# Adding a New Specification

When adding a specification:

1. Choose a focused responsibility boundary.
2. Add the specification document under `specs/`.
3. Add a navigation entry to this index.
4. Keep behavioral requirements in the new specification, not in this index.
5. Update related tests and implementation when behavior changes.

