"""Utilities related to attribute docstring extraction."""
from __future__ import annotations
import ast
import inspect
import textwrap
from typing import Any

class DocstringVisitor(ast.NodeVisitor):

    def __init__(self) -> None:
        super().__init__()
        self.target: str | None = None
        self.attrs: dict[str, str] = {}
        self.previous_node_type: type[ast.AST] | None = None

def extract_docstrings_from_cls(cls: type[Any], use_inspect: bool=False) -> dict[str, str]:
    """Map model attributes and their corresponding docstring.

    Args:
        cls: The class of the Pydantic model to inspect.
        use_inspect: Whether to skip usage of frames to find the object and use
            the `inspect` module instead.

    Returns:
        A mapping containing attribute names and their corresponding docstring.
    """
    pass