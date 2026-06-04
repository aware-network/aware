from __future__ import annotations

from contextvars import ContextVar

from aware_orm.session.current_session_ctx import (
    current_session,
    current_session_context,
    set_session,
    switch_session_context,
    use_runtime_session_context_var,
)
from aware_orm.session.session import Session
from aware_orm.testing import TestSessionContext as _TestSessionContext


def test_current_session_context_prefers_injected_runtime_var() -> None:
    session = Session(connection=None, skip_db=True)
    runtime_ctx = _TestSessionContext(session)
    runtime_var: ContextVar[object] = ContextVar("test_runtime_ctx_var")
    token = runtime_var.set(runtime_ctx)
    try:
        with use_runtime_session_context_var(runtime_var):
            with set_session(session):
                ctx = current_session_context()
                assert ctx is runtime_ctx
    finally:
        runtime_var.reset(token)


def test_switch_session_context_uses_injected_runtime_var_without_runtime_imports() -> None:
    session_a = Session(connection=None, skip_db=True)
    session_b = Session(connection=None, skip_db=True)
    runtime_ctx = _TestSessionContext(session_a)
    runtime_var: ContextVar[object] = ContextVar("test_runtime_switch_ctx_var")
    token = runtime_var.set(runtime_ctx)
    try:
        with use_runtime_session_context_var(runtime_var):
            assert current_session() is session_a
            with switch_session_context(session_b) as switched_ctx:
                assert switched_ctx.session is session_b
                assert current_session() is session_b
            assert current_session() is session_a
    finally:
        runtime_var.reset(token)
