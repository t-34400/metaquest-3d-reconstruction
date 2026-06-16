import tomllib
from pathlib import Path


def load_pyproject() -> dict:
    return tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))


def test_default_dependencies_do_not_include_open3d():
    project = load_pyproject()["project"]

    dependencies = {dependency.lower() for dependency in project.get("dependencies", [])}

    assert "open3d" not in dependencies


def test_optional_extras_define_reconstruction_and_full_profiles():
    optional_dependencies = load_pyproject()["project"]["optional-dependencies"]

    assert {"io", "convert", "reconstruction", "full"}.issubset(optional_dependencies)
    assert "open3d==0.19.0" in optional_dependencies["reconstruction"]
    assert set(optional_dependencies["reconstruction"]).issubset(optional_dependencies["full"])

def test_full_profile_includes_all_feature_dependencies():
    optional_dependencies = load_pyproject()["project"]["optional-dependencies"]

    feature_dependencies = set()
    for extra_name, dependencies in optional_dependencies.items():
        if extra_name != "full":
            feature_dependencies.update(dependencies)

    assert feature_dependencies.issubset(optional_dependencies["full"])


def test_readme_documents_lightweight_and_full_pip_installs():
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "pip install mq3drecon" in readme
    assert "pip install 'mq3drecon[full]'" in readme

