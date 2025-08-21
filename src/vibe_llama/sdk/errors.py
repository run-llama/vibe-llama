class InstructionsUnavailableError(Exception):
    """Raised when instructions are not available"""


class FailedToWriteFileWarning(Warning):
    """Raised when one file was not written"""


class FailedToWriteFilesError(Exception):
    """Raised when all files failed to write"""
