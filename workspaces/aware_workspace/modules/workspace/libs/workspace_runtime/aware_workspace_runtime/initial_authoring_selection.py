"""Original owner dispatch for read-only retained initial request selection.

Historical data cannot restore a live admission, choose another profile, or
authorize redispatch. Filesystem ownership and original verification stay in FS.
"""

from __future__ import annotations


def observe_initial_authoring_request(owner, kind):
    if type(kind) is not str or kind not in {
        "configuration",
        "project",
        "goal",
        "membership",
    }:
        raise ValueError("initial_retained_request_kind_unsupported")
    owner._current()
    result = owner._physical.observe_initial_authoring_request(
        kind, execution_id=owner._execution
    )
    owner._current()
    return result
