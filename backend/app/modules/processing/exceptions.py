class ProcessingJobNotFoundError(Exception):
    """Raised when a processing job cannot be found."""


class ProcessingPausedError(Exception):
    """Raised when processing is paused and cannot continue."""
