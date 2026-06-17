from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ENTRYPOINTS = {
    Path("scripts/__init__.py"),
    Path("scripts/_bootstrap.py"),
    Path("scripts/build_colmap_project.py"),
    Path("scripts/convert_depth_to_linear_map.py"),
    Path("scripts/convert_yuv_to_rgb.py"),
    Path("scripts/reconstruct_scene.py"),
    Path("scripts/visualize_camera_trajectories.py"),
}
LEGACY_PACKAGE_ROOTS = {
    "config",
    "dataio",
    "models",
    "pipeline",
    "processing",
    "third_party",
    "utils",
}


def _legacy_module_name(path: Path) -> str:
    relative = path.relative_to(REPO_ROOT / "scripts")
    without_suffix = relative.with_suffix("")
    parts = without_suffix.parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(("mq3drecon", *parts))


def test_legacy_package_files_are_compatibility_wrappers_with_package_owners():
    failures = []
    for path in sorted((REPO_ROOT / "scripts").rglob("*.py")):
        relative = path.relative_to(REPO_ROOT)
        if relative in SCRIPT_ENTRYPOINTS:
            continue
        if relative.parts[1] not in LEGACY_PACKAGE_ROOTS:
            continue

        module_name = _legacy_module_name(path)
        target_path = REPO_ROOT / "src" / Path(*module_name.split(".")).with_suffix(".py")
        if path.name == "__init__.py":
            target_path = REPO_ROOT / "src" / Path(*module_name.split(".")) / "__init__.py"

        content = path.read_text(encoding="utf-8")
        if "Compatibility" not in content and "compatibility" not in content:
            failures.append(f"{relative} is not documented as a compatibility wrapper")
        if module_name not in content:
            failures.append(f"{relative} does not delegate to {module_name}")
        if not target_path.exists():
            failures.append(f"{relative} delegates to missing package owner {target_path.relative_to(REPO_ROOT)}")

    assert failures == []


def test_package_root_exports_are_intentionally_minimal():
    import mq3drecon

    assert mq3drecon.__all__ == ["__version__", "MQ3DReconError", "ProcessingError"]
