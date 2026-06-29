"""Shared Tree-sitter language loader for the SQL grammar."""

from __future__ import annotations

import ctypes
from functools import lru_cache

from tree_sitter import Language
import tree_sitter_sql as _tssql

_CAPSULE_NAME = b"tree_sitter.Language"
_pycapsule_new = ctypes.pythonapi.PyCapsule_New
_pycapsule_new.restype = ctypes.py_object
_pycapsule_new.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p]


def _language_capsule() -> object:
    """Return a PyCapsule wrapping the SQL ``TSLanguage`` pointer."""
    ptr = _tssql.language()
    if isinstance(ptr, int):
        return _pycapsule_new(ctypes.c_void_p(ptr), _CAPSULE_NAME, None)
    return ptr


@lru_cache(maxsize=1)
def get_sql_language() -> Language:
    """Return a cached :class:`Language` instance for the SQL grammar."""
    return Language(_language_capsule())


SQL_LANGUAGE: Language = get_sql_language()
