from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_foundation_stereo_example_script_uses_recommended_stereo_commands():
    script = (ROOT / "examples" / "run_foundation_stereo_pipeline.sh").read_text()

    assert "mq3drecon foundation-stereo-depth" in script
    assert "--model-path" in script
    assert "config/pipeline_config_stereo.yml" in script
    assert "mq3drecon reconstruct" in script
    assert "mq3drecon export-colmap" in script


def test_legacy_example_script_does_not_claim_to_run_foundation_stereo():
    script = (ROOT / "examples" / "run_mq3drecon_pipeline.sh").read_text()
    docs = (ROOT / "docs" / "CLI.md").read_text()

    assert "mq3drecon foundation-stereo-depth" not in script
    assert "legacy/simple export helper" in docs
    assert "It does not run `foundation-stereo-depth`" in docs
