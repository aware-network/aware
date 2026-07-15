import sys
from contextlib import contextmanager
from copy import deepcopy
import copy
import pickle

from .logging import logger


def safe_deep_copy(obj):
    try:
        return pickle.loads(pickle.dumps(obj, protocol=-1))
    except (TypeError, pickle.PicklingError) as e:
        logger.warning(f"Pickle failed, falling back to deepcopy: {e}")
        with deep_copy_context():
            return deepcopy(obj)


@contextmanager
def deep_copy_context(stacklimit: int = 20000):
    """Temporarily raise recursion limit so copy.deepcopy can finish."""
    old = sys.getrecursionlimit()
    if stacklimit > old:
        sys.setrecursionlimit(stacklimit)
    try:
        yield
    finally:
        sys.setrecursionlimit(old)


@contextmanager
def treesitter_atomic():
    """Temporarily treat tree_sitter.Node instances as atomic during deepcopy operations."""
    try:
        from tree_sitter import Node as TreeSitterNode  # type: ignore
    except Exception:  # pragma: no cover - tree_sitter optional
        TreeSitterNode = None  # type: ignore

    if TreeSitterNode is None:
        yield
        return

    original = copy._deepcopy_dispatch.get(TreeSitterNode)
    copy._deepcopy_dispatch[TreeSitterNode] = copy._deepcopy_atomic
    try:
        yield
    finally:
        if original is None:
            copy._deepcopy_dispatch.pop(TreeSitterNode, None)
        else:
            copy._deepcopy_dispatch[TreeSitterNode] = original
