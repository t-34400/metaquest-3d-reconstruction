class MQ3DReconError(Exception):
    """Base class for catchable MQ3DRecon library errors."""


class ProcessingError(MQ3DReconError):
    """Raised when a processing workflow cannot complete successfully."""
