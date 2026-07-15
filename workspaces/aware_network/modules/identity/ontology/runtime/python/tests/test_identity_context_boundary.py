from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from aware_identity.context import (
    IdentityInvocationContext,
    current_invocation_context,
    scoped_identity_invocation_context,
    switch_identity_session,
)
from aware_orm.session.current_session_ctx import current_session


def test_identity_invocation_context_can_be_scoped_without_runtime() -> None:
    context = IdentityInvocationContext(
        actor_id=uuid4(),
        branch_id=uuid4(),
        object_instance_graph_branch_id=uuid4(),
    )

    with scoped_identity_invocation_context(context):
        assert current_invocation_context() == context

    with pytest.raises(RuntimeError, match="scoped_identity_invocation_context"):
        current_invocation_context()


def test_identity_session_switch_scopes_orm_session_without_runtime() -> None:
    session = SimpleNamespace(branch_id=uuid4())

    with switch_identity_session(session):
        assert current_session() is session
