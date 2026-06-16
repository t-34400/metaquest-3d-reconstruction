# Logging and Error Handling Specification

## Purpose

This document defines error reporting and logging behavior for MQ3DRecon library modules and CLI migration shims.

It owns requirements for:

* library exception behavior
* typed project exceptions
* logging expectations
* CLI conversion of exceptions to exit status
* migration away from print-only failure reporting

CLI process behavior is specified in `CLI_BEHAVIOR.md`.
Public API boundaries are specified in `PUBLIC_API.md`.

---

# Library Error Reporting

Library APIs must signal failures with exceptions that callers can catch.

A library API must not use printed output as the only signal that processing failed.

Recoverable validation, configuration, filesystem, and processing failures should use either standard Python exceptions or typed MQ3DRecon exceptions.

---

# Typed MQ3DRecon Exceptions

The package exposes a common base exception:

```python
MQ3DReconError
```

Workflow-level processing failures may use:

```python
ProcessingError
```

Typed MQ3DRecon exceptions are public API and should be catchable by CLI shims and package callers.

---

# Logging

Library modules should use the standard `logging` module for progress, diagnostic, warning, and recoverable error details.

Library modules must not require logging output for correctness.

The default package import must not configure global logging handlers.

---

# CLI Error Conversion

Stable CLI shims should catch expected project, validation, configuration, and filesystem exceptions.

When such an exception is caught, the CLI should:

1. write a concise error message to stderr,
2. return exit status `1`, and
3. avoid printing a Python traceback for expected user-facing failures.

Argument parsing failures remain owned by `argparse` and use exit status `2`.

---

# Migration Policy

During migration, existing progress prints may remain in legacy CLI shims.

Library modules should be migrated from print-based diagnostics to logging incrementally, prioritizing paths where printed errors currently hide or downgrade failures.
