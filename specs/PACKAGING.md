# Packaging Specification

## Purpose

This document defines MQ3DRecon installation profiles and optional dependency boundaries.

It owns requirements for:

* default package dependencies
* optional dependency extras
* lightweight versus full installation behavior
* dependency placement for Open3D and reconstruction-specific features

Public API boundaries are specified in `PUBLIC_API.md`.
CLI behavior is specified in `CLI_BEHAVIOR.md`.
Project layout behavior is specified in `PROJECT_LAYOUT.md`.

---

# Installation Profiles

MQ3DRecon must support a default lightweight installation and optional feature-specific extras.

The default installation is the lightweight package profile. It should support importing and using package APIs for:

* configuration parsing
* project layout resolution
* domain models
* dataset and image/depth data I/O that does not execute reconstruction-only Open3D operations
* YUV-to-RGB conversion
* depth-to-linear conversion
* COLMAP export module importability

The default installation must not require Open3D.

---

# Optional Extras

The package should define extras with the following responsibilities:

| Extra | Responsibility |
| --- | --- |
| `io` | Dependencies needed by public data I/O APIs. |
| `convert` | Dependencies needed by color and depth conversion workflows. |
| `reconstruction` | Dependencies needed by reconstruction workflows and Open3D-backed reconstruction data operations. |
| `full` | All supported optional runtime dependencies for the complete toolkit. |

`full` must include the dependencies required by `reconstruction`.

When an extra name overlaps with dependencies already included by the default lightweight profile, the extra may be retained as an explicit stable installation target even if it adds no new dependencies.

---

# Open3D Dependency Boundary

Open3D is a reconstruction-specific dependency.

Open3D must not be required to import lightweight public modules, including:

* `mq3drecon`
* `mq3drecon.config`
* `mq3drecon.layouts`
* `mq3drecon.models`
* `mq3drecon.dataio`
* `mq3drecon.processing.yuv_conversion`
* `mq3drecon.processing.depth_conversion`
* `mq3drecon.workflows`

Modules that execute Open3D-backed reconstruction behavior may import Open3D when that behavior is used.

If an Open3D-backed method is called without Open3D installed, the method may fail with Python's normal import error for the missing dependency.

---

# Version Pinning Policy

Heavy optional dependencies may be version-pinned when compatibility is known to be narrow.

Default lightweight dependencies should avoid unnecessary strict pins unless a documented compatibility issue requires them.

---

# Packaging Metadata

Packaging metadata must keep dependency boundaries explicit.

`pyproject.toml` should define the default lightweight runtime dependencies under the project dependency list and optional feature dependencies under `project.optional-dependencies`.

The conda development environment may include the full dependency set for contributor convenience, but it must not be treated as the default pip installation profile.

---

# Console Scripts

Packaging metadata must expose the package-backed CLI command `mq3drecon` through `project.scripts`.

The console script must point to a package module under `mq3drecon` and must not point to a legacy file under `scripts/`.
