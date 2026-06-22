# CLI Behavior Specification

## Purpose

This document defines command-line interface behavior for MQ3DRecon during the migration from script-oriented entrypoints to package-backed commands.

It owns requirements for:

* legacy script command compatibility
* CLI and library responsibility boundaries
* argument compatibility expectations
* process exit behavior
* user-facing error reporting
* migration shim behavior

Public package API requirements are specified in `PUBLIC_API.md`.
Legacy filesystem locations are specified in `LEGACY_BEHAVIOR.md` and `PROJECT_LAYOUT.md`.
Dataset and cache schemas are specified in `DATASETS_AND_CACHE.md`.

---

# Compatibility Scope

Existing top-level scripts under `scripts/` are legacy CLI entrypoints.

These entrypoints may remain available as migration shims while package-backed CLI commands are introduced.

Legacy script compatibility covers command behavior for users who execute script files directly. It does not make the `scripts/` package or its internal imports a public library API.

---

# CLI Responsibility Boundary

CLI entrypoints must be thin adapters.

A CLI entrypoint may own:

* argument parsing
* conversion from command-line arguments to library configuration objects
* environment-facing messages
* process exit status
* formatting of recoverable errors for humans

A CLI entrypoint must not be the sole owner of a processing workflow.

Processing logic must live in library modules under the package namespace and must be callable without starting a separate command-line process.

---

# Legacy Script Shim Requirement

When a package API exists for the same workflow, the corresponding legacy script should delegate to that package API.

A legacy script shim may preserve historical argument names and defaults when required for compatibility.

New behavior should be implemented in the package API first, then exposed through CLI wrappers.

---

# Package CLI Commands

The installable package exposes a stable console command named:

```bash
mq3drecon
```

The package command must dispatch to package-backed workflows without importing legacy `scripts/` modules.

The stable package subcommands are:

| Subcommand | Responsibility |
| --- | --- |
| `yuv-to-rgb` | Convert captured YUV frames to RGB images. |
| `depth-to-linear` | Convert depth frames to linear depth maps. |
| `rgba-to-png` | Convert MRUK RGBA frames to PNG images. |
| `foundation-stereo-depth` | Generate rectified stereo depth maps from stereo color frames using a FoundationStereo ONNX model, plus compatibility color-aligned depth when supported. |
| `color-aligned-depth-to-png` | Export saved color-aligned depth maps to PNG files for inspection. |
| `reconstruct` | Run the reconstruction pipeline. |
| `export-colmap` | Export camera and image data to COLMAP-compatible output. |
| `visualize-cameras` | Visualize camera trajectories. |

Package CLI commands should prefer hyphenated option names such as `--project-dir` and `--output-dir`. Legacy underscore aliases such as `--project_dir` and `--output_dir` may remain available for migration compatibility.

Package CLI commands that operate on a legacy project directory must require `--project-dir` explicitly. Commands that write package-oriented or export artifacts must require an explicit output location unless a future specification defines a safe default.

For pipeline-backed processing commands, `--config` is optional. When it is omitted, commands must use the corresponding lightweight configuration object defaults instead of resolving a repository-relative default YAML path.

---

# Argument Compatibility

Existing CLI arguments should remain compatible unless a specification explicitly approves a breaking change.

When replacing an argument:

1. keep the old argument as an alias when practical,
2. document the preferred replacement,
3. avoid changing default behavior silently.

Arguments that select legacy output behavior must make that behavior explicit through the command name, option name, help text, or documented workflow.

---

# Output Layout Selection

CLI commands that write generated artifacts must choose output layout explicitly.

A command may write into the legacy project directory only when operating in documented legacy compatibility mode.

Package-oriented CLI commands should accept an explicit output location or layout option when they generate artifacts.

The concrete layout rules are owned by `PROJECT_LAYOUT.md`.

---

# Error Reporting

Library APIs must report failures through exceptions.

CLI entrypoints may catch expected exceptions and convert them into concise user-facing error messages.

CLI entrypoints must not use printed messages as the only failure signal.

A failed command must return a non-zero exit status.

Unexpected exceptions may propagate during development commands, but stable user-facing commands should convert known validation, filesystem, and configuration errors into clear messages.

---

# Exit Status

Stable CLI commands should use the following exit status conventions:

| Status | Meaning |
| --- | --- |
| `0` | Command completed successfully. |
| `1` | Command failed because of invalid input, invalid configuration, missing required files, or processing failure. |
| `2` | Command-line argument parsing failed. |

More specific exit statuses may be introduced by a future specification if needed.

---

# Logging and Progress Output

CLI commands may print progress and summary information for users.

Library modules must not depend on CLI progress output for correctness.

Machine-readable output must not be mixed with human progress output unless the command explicitly documents that format.

---

# Headless Safety

Commands intended for automated processing must not open visualization windows by default.

Visualization should be opt-in through a command, option, or callback-like library API.

Reconstruction commands that support visualization must remain usable in headless environments when visualization is disabled.

---

# Migration Order

When migrating a legacy script workflow:

1. define or update the relevant behavior specification,
2. create or update the package API,
3. make the legacy script delegate to the package API,
4. preserve compatible arguments where practical,
5. validate both package API importability and CLI execution behavior.
