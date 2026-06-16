"""Data I/O facades exposed by MQ3DRecon."""

__all__ = ["DataIO"]


def __getattr__(name: str):
    if name == "DataIO":
        from mq3drecon.dataio.data_io import DataIO

        return DataIO
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
