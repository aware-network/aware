"""Typed runtime loader for tree-sitter SQL language bindings.

Avoids static-analysis import-not-found noise on the compiled extension module while
keeping runtime behavior unchanged.
"""

from __future__ import annotations

from importlib import import_module
from typing import cast

from tree_sitter import Language

_tree_sitter_sql = import_module("tree_sitter_sql.tree_sitter_language")
SQL_LANGUAGE = cast(Language, _tree_sitter_sql.__dict__["SQL_LANGUAGE"])

__all__ = ["SQL_LANGUAGE"]
