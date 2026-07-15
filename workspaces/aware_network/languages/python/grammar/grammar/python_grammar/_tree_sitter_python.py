"""Typed runtime loader for tree-sitter Python language bindings.

Avoids static-analysis import-not-found noise on the compiled extension module while
keeping runtime behavior unchanged.
"""

from __future__ import annotations

from importlib import import_module
from typing import cast

from tree_sitter import Language

_tree_sitter_python = import_module("tree_sitter_python.tree_sitter_language")
PYTHON_LANGUAGE = cast(Language, getattr(_tree_sitter_python, "PYTHON_LANGUAGE"))

__all__ = ["PYTHON_LANGUAGE"]
