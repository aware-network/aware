"""Shared Tree-sitter language loader for the Dart grammar.

The generated ``tree_sitter_dart.language()`` API still returns a raw pointer
as an ``int``. Tree-sitter 0.24+ prefers receiving a ``PyCapsule`` when
constructing :class:`tree_sitter.Language`, so we wrap the pointer with the
canonical capsule name before instantiating and cache the result.
"""

from __future__ import annotations

import ctypes
from functools import lru_cache

from tree_sitter import Language
import tree_sitter_dart as _tsdart

_CAPSULE_NAME = b"tree_sitter.Language"
_pycapsule_new = ctypes.pythonapi.PyCapsule_New
_pycapsule_new.restype = ctypes.py_object
_pycapsule_new.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p]


def _language_capsule() -> object:
    """Return a PyCapsule wrapping the Dart ``TSLanguage`` pointer."""
    ptr = _tsdart.language()
    if isinstance(ptr, int):
        return _pycapsule_new(ctypes.c_void_p(ptr), _CAPSULE_NAME, None)
    return ptr


@lru_cache(maxsize=1)
def get_dart_language() -> Language:
    """Return a cached :class:`Language` instance for the Dart grammar."""
    return Language(_language_capsule())


# Convenience constant for modules that prefer attribute access
DART_LANGUAGE: Language = get_dart_language()
