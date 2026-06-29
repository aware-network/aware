"""Typed runtime loader for tree-sitter Dart language bindings."""

from __future__ import annotations

from importlib import import_module
from typing import cast

from tree_sitter import Language

_tree_sitter_dart = import_module("tree_sitter_dart.tree_sitter_language")
DART_LANGUAGE = cast(Language, _tree_sitter_dart.__dict__["DART_LANGUAGE"])

__all__ = ["DART_LANGUAGE"]
