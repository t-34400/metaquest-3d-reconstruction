# COMMON_RULES.md

## Purpose

This document defines project-wide principles, specification authority,
architecture expectations, compatibility requirements, and migration rules for MQ3DRecon.

MQ3DRecon is a reconstruction toolkit for processing Meta Quest capture data,
building RGB/depth datasets, and generating 3D scene reconstructions.

The project is transitioning from a script-oriented implementation to an installable Python package.

All project-specific specifications must follow these rules.

---

# Specification Authority

When information conflicts, use the following priority:

```text
COMMON_RULES.md
    >
Other specifications
    >
Tests
    >
Implementation
```

Implementation behavior must not override written specifications.

Tests validate specifications but do not replace them.

---

# Read Before Modify

Before making changes:

1. Identify affected behavior.
2. Identify relevant specifications.
3. Identify affected tests.
4. Identify compatibility implications.

Do not begin implementation until the relevant specifications have been reviewed.

---

# Single Source of Truth

Each rule should have exactly one authoritative location.

Avoid duplicating behavioral requirements across documents.

INDEX documents are navigation documents.

INDEX documents must not define behavioral requirements.

---

# Specification-Driven Development

Implementation follows specifications.

When intentionally changing behavior:

1. Update specifications.
2. Update tests.
3. Update implementation.

Keep these changes in the same change set whenever practical.

---

# Explicit Behavior

Important behavior must be documented.

Do not rely on:

* developer assumptions
* undocumented conventions
* historical implementation quirks
* prior discussions

If behavior matters, specify it.

---

# Traceability

Important requirements should remain traceable.

Preferred chain:

```text
Requirement
    ->
Specification
    ->
Test
    ->
Implementation
```

Changes should preserve this relationship whenever practical.

---

# Specification Organization

Specifications must remain maintainable.

Prefer:

* small focused documents
* one responsibility per document
* explicit references between documents
* topic-oriented organization

Avoid:

* monolithic specifications
* duplicated requirements
* mixed responsibilities
* large unstructured documents

When a specification becomes difficult to navigate, split it into smaller specifications.

---

# Code Organization

Source code must remain maintainable.

Prefer:

* small focused modules
* explicit interfaces
* clear ownership boundaries
* responsibility-oriented structure

Avoid:

* god objects
* multi-purpose modules
* hidden coupling
* excessive file growth

Guidelines:

* keep source files near 300 lines or less when practical
* split files before 500 lines unless strongly justified
* keep functions near 50 lines or less when practical

These are guidelines, not hard limits.

---

# Complexity Management

When adding functionality:

1. Extend an existing specification if the responsibility matches.
2. Create a new specification if a new responsibility is introduced.
3. Avoid expanding unrelated specifications.

When adding code:

1. Extend an existing module if the responsibility matches.
2. Create a new module if a new responsibility is introduced.
3. Avoid accumulating unrelated responsibilities in a single file.

Prefer introducing new focused components over growing existing multi-purpose components.

---

# Architecture Principles

Unless a more specific specification states otherwise:

* prefer modular design
* prefer explicit interfaces
* prefer deterministic behavior
* prefer testable components
* separate responsibilities clearly
* avoid hidden coupling
* avoid unnecessary complexity

---

# Testing Principles

Tests verify observable behavior.

Tests should focus on:

* expected outputs
* public interfaces
* documented requirements
* regression protection

Avoid testing implementation details unless necessary.

Tests are validation artifacts, not primary specifications.

---

# Documentation Principles

Documentation should describe:

* behavior
* interfaces
* assumptions
* constraints

Avoid duplicating information maintained elsewhere.

Keep documentation synchronized with behavior changes.

---

# Compatibility Policy

The project must explicitly define compatibility requirements.

MQ3DRecon uses:

* behavioral compatibility
* data compatibility
* migration compatibility

Public API compatibility is enforced only for documented APIs.

Undocumented internal behavior may change.

---

# Decision Records

Long-term architectural decisions should be documented separately.

Decision records should explain:

* context
* decision
* consequences

Avoid embedding architectural rationale directly into behavioral specifications.

---

# Project-Specific Rules

The following sections define MQ3DRecon-specific rules.

## Project Purpose

MQ3DRecon converts Meta Quest capture outputs into reusable RGB/depth datasets,
camera trajectories, reconstruction assets, and interoperability formats such as COLMAP projects.

The project shall support both:

* library usage
* command-line usage

The installable package implementation is the long-term supported form.

Legacy scripts exist only for migration compatibility.

---

## Domain Concepts

Core domain concepts include:

* color images
* depth maps
* confidence maps
* camera trajectories
* coordinate systems
* dataset caches
* reconstruction fragments
* scene reconstruction assets
* COLMAP export assets

These concepts shall be represented as explicit domain models or explicitly owned processing components.

---

## Architecture Constraints

The project shall be organized into layers.

Recommended responsibilities:

* domain models
* data access
* processing algorithms
* reconstruction pipeline
* command-line interfaces

Business logic shall not be implemented directly in CLI entrypoints.

CLI commands shall delegate to library APIs.

File-system operations shall be isolated from reconstruction algorithms whenever practical.

Package modules must not depend on execution from the repository root.

Package modules must be importable after installation.

---

## Coding Rules

Prefer:

* explicit typing
* dataclasses for structured data
* immutable configuration objects when practical
* dependency injection over hidden globals

Avoid:

* circular imports
* hidden runtime side effects
* package-level initialization logic
* hardcoded project paths
* repository-root-relative imports

All package imports must work after installation.

No module may rely on direct script execution as its only supported execution mode.

---

## Compatibility Requirements

Legacy behavior shall be documented in `LEGACY_BEHAVIOR.md`.

The following are migration compatibility targets:

* input directory layouts
* dataset formats
* reconstruction outputs
* coordinate conversion behavior
* supported configuration files
* legacy script behavior where explicitly documented

Behavioral changes require specification updates.

Breaking changes must be explicitly documented.

---

## Testing Requirements

Every documented public API should have tests.

Every documented CLI command should have tests.

Every bug fix should include regression coverage when practical.

Tests should prioritize:

1. public APIs
2. reconstruction outputs
3. dataset serialization
4. coordinate transformations
5. CLI behavior

---

## Performance Requirements

The project processes large RGB/depth datasets.

Avoid:

* unnecessary file duplication
* repeated dataset loading
* excessive memory copies
* unbounded in-memory accumulation of large images, depth maps, or point clouds

Cache usage shall be explicitly documented.

Performance optimizations must not change documented behavior.

---

## Safety Requirements

Reconstruction results must be reproducible from identical inputs when configuration and dependencies are unchanged.

Functions must not silently modify source capture data.

Input files shall be treated as immutable.

Generated outputs shall be written to explicit output locations.

Destructive operations require explicit user intent.

---

## Data Rules

Input capture data is immutable.

Generated artifacts shall be treated as derived data.

Persistent formats must be documented.

The structure of:

* npz datasets
* cache artifacts
* reconstruction outputs
* exported projects

shall be specified in dedicated specifications.

Undocumented serialization formats are not considered stable public interfaces.
