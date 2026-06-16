# Reconstruction Configuration Specification

## Purpose

This document defines the structure and dependency boundaries for reconstruction configuration objects.

It owns requirements for:

* reconstruction configuration module ownership
* lightweight import behavior
* Open3D independence for configuration data objects
* compatibility exports during migration

Packaging dependency boundaries are specified in `PACKAGING.md`.
Public import stability is specified in `PUBLIC_API.md`.

---

# Configuration Ownership

Reconstruction configuration must be represented by lightweight Python data objects.

Configuration modules may describe reconstruction options, device specifications, and per-step parameter groups, but they must not construct Open3D runtime objects directly.

Open3D-backed runtime conversion belongs in reconstruction processing adapters, not configuration modules.

---

# Module Structure

Reconstruction configuration should be split by responsibility instead of accumulating unrelated configuration classes in one large module.

The package should provide focused modules for:

* device defaults and device specification aliases
* depth confidence estimation configuration
* fragment generation configuration
* fragment pose refinement configuration
* TSDF/depth integration configuration
* color optimization configuration
* color-aligned depth rendering configuration
* top-level reconstruction configuration parsing and composition

---

# Lightweight Import Requirement

Importing reconstruction configuration modules must not require Open3D.

The following imports must remain usable in the default lightweight installation profile:

```python
from mq3drecon.config import ReconstructionConfig
from mq3drecon.config.reconstruction_config import ReconstructionConfig
```

---

# Compatibility Aggregation

During migration, `mq3drecon.config.reconstruction_config` may remain as an aggregation module that re-exports reconstruction configuration classes from focused implementation modules.

This compatibility module must not become the long-term owner of unrelated configuration responsibilities.
