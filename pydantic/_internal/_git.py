"""Git utilities, adopted from mypy's git utilities (https://github.com/python/mypy/blob/master/mypy/git.py)."""
from __future__ import annotations
import os
import subprocess

def is_git_repo(dir: str) -> bool:
    """Is the given directory version-controlled with git?"""
    pass

def have_git() -> bool:
    """Can we run the git executable?"""
    pass

def git_revision(dir: str) -> str:
    """Get the SHA-1 of the HEAD of a git repository."""
    pass