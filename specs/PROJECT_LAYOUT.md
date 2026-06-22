# Project Layout Specification

## Purpose

This document defines filesystem layout responsibilities for MQ3DRecon.

It owns requirements for:

* project layout abstraction boundaries
* legacy project layout behavior
* package output layout behavior
* COLMAP export layout behavior
* path resolution responsibilities
* generated artifact placement policy

Legacy path names are specified in `LEGACY_BEHAVIOR.md`.
Dataset and cache file schemas are specified in `DATASETS_AND_CACHE.md`.
Public package API requirements are specified in `PUBLIC_API.md`.
CLI layout selection behavior is specified in `CLI_BEHAVIOR.md`.

---

# Layout Abstraction Requirement

Path construction for generated artifacts must be centralized behind layout-focused components instead of being scattered across processing code.

Processing workflows should receive resolved paths or explicit layout objects.

Processing code must not infer output locations from unrelated input paths unless operating through a documented legacy layout object.

---

# Required Layout Roles

MQ3DRecon should distinguish at least the following layout roles:

| Layout | Responsibility |
| --- | --- |
| `LegacyProjectLayout` | Resolve historical project-relative input and generated output paths. |
| `PackageOutputLayout` | Resolve package API output paths outside immutable input capture directories. |
| `ColmapExportLayout` | Resolve files and directories produced for COLMAP-compatible exports. |

The concrete class names may evolve, but implementations must preserve these responsibility boundaries.

---

# LegacyProjectLayout

`LegacyProjectLayout` represents the historical project directory layout documented in `LEGACY_BEHAVIOR.md`.

It may resolve both immutable input paths and legacy generated output paths under the same project directory.

Using this layout means the caller has explicitly selected legacy-compatible behavior.

Legacy layout resolution must preserve documented directory and file names unless a future specification defines a migration path.

---

# PackageOutputLayout

`PackageOutputLayout` represents package-oriented generated output storage.

It must not silently write generated artifacts into immutable input capture directories.

It should be rooted at an explicit output directory supplied by the caller.

Package APIs that generate artifacts should accept either an explicit output directory or a package output layout object.

---

# ColmapExportLayout

`ColmapExportLayout` represents generated files intended for COLMAP-compatible workflows.

COLMAP export paths should be owned by this layout rather than mixed into generic dataset or reconstruction path helpers.

A future COLMAP-specific specification must define the stable exported file set before those files are treated as compatibility artifacts.

Until that specification exists, this layout owns only the separation of responsibility, not a finalized export schema.

---

# Input Path Policy

Source capture inputs are immutable.

Layout objects may resolve input paths, but they must not modify source capture files.

Commands or APIs that perform destructive operations must be explicitly documented separately and require explicit user intent.

---

# Generated Artifact Policy

Generated artifacts must be written to paths selected by the active layout.

Legacy-compatible workflows may write generated artifacts under the project directory through `LegacyProjectLayout`.

Package-oriented workflows must write generated artifacts under an explicit output root through `PackageOutputLayout` or another documented output layout.

---

# Relative Path Policy

Legacy dataset records may store frame directories as paths relative to the legacy project directory, as specified in `LEGACY_BEHAVIOR.md`.

Package-oriented dataset records should resolve relative paths against an explicitly documented dataset root.

Readers must not guess between unrelated possible roots when a dataset cannot be resolved unambiguously.

---

# Path Naming Compatibility

Existing legacy names that are compatibility targets must remain available through the legacy layout.

New package-oriented names should be clear, correctly spelled, and grouped by responsibility.

Misspelled legacy path helper names may remain as aliases only when needed for compatibility. New public names must use correct spelling.

---

# Implementation Guidance

Layout components should be lightweight and must not import heavy reconstruction dependencies such as Open3D.

Layout components should be deterministic, testable, and safe to instantiate in environments without GPU or visualization support.


# Rectified Stereo Artifacts

FoundationStereo rectification writes native rectified stereo artifacts into the legacy project directory:

```text
left_rectified_stereo_color/
right_rectified_stereo_color/
left_rectified_stereo_depth/
dataset/left_rectified_stereo_color_dataset.npz
dataset/right_rectified_stereo_color_dataset.npz
dataset/left_rectified_stereo_depth_dataset.npz
dataset/stereo_rectification.npz
```

The existing `left_color_aligned_depth/` directory remains the compatibility output for depth mapped back to the original left color coordinate system.
