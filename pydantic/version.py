"""The `version` module holds the version information for Pydantic."""
from __future__ import annotations as _annotations
__all__ = ('VERSION', 'version_info')
VERSION = '2.8.2'
'The version of Pydantic.'

def version_short() -> str:
    """Return the `major.minor` part of Pydantic version.

    It returns '2.1' if Pydantic version is '2.1.1'.
    """
    pass

def version_info() -> str:
    """Return complete version information for Pydantic and its dependencies."""
    pass

def parse_mypy_version(version: str) -> tuple[int, ...]:
    """Parse mypy string version to tuple of ints.

    It parses normal version like `0.930` and extra info followed by a `+` sign
    like `0.940+dev.04cac4b5d911c4f9529e6ce86a27b44f28846f5d.dirty`.

    Args:
        version: The mypy version string.

    Returns:
        A tuple of ints. e.g. (0, 930).
    """
    pass