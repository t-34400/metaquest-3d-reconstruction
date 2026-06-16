"""Pipeline orchestration APIs exposed by MQ3DRecon."""

__all__ = ["PipelineProcessor"]


def __getattr__(name: str):
    if name == "PipelineProcessor":
        from mq3drecon.pipeline.pipeline_processor import PipelineProcessor

        return PipelineProcessor
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
