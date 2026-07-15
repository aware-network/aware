from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import pytest

from aware_identity_ontology.identity.identity import Identity
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    reset_invocation_provider,
    set_invocation_provider,
)


@dataclass(frozen=True, slots=True)
class _RecordedInvocation:
    call_target: str
    class_name: str
    function_name: str
    object_id: UUID | None
    payload: dict[str, Any]


class _RecordingLaneBinder:
    def __init__(self, *, identity_id: UUID) -> None:
        self.identity_id = identity_id
        self.binds: list[dict[str, Any]] = []
        self.invocations: list[_RecordedInvocation] = []

    def bind(
        self,
        *,
        projection: str,
        branch_id: UUID,
        actor_id: UUID | None = None,
    ) -> _RecordingLane:
        self.binds.append(
            {
                "projection": projection,
                "branch_id": branch_id,
                "actor_id": actor_id,
            }
        )
        return _RecordingLane(binder=self)


@dataclass(frozen=True, slots=True)
class _RecordingLane:
    binder: _RecordingLaneBinder

    @property
    def branch_id(self) -> UUID:
        return self.binder.identity_id

    @contextmanager
    def activate(
        self,
        *,
        commit: bool = True,
        publish: bool = False,
    ) -> Iterator[object]:
        _ = commit, publish
        token = set_invocation_provider(_RecordingProvider(binder=self.binder))
        try:
            yield self
        finally:
            reset_invocation_provider(token)


@dataclass(frozen=True, slots=True)
class _RecordingProvider:
    binder: _RecordingLaneBinder

    async def invoke_constructor(
        self,
        *,
        orm_class: type[ORMModel],
        function_name: str,
        payload: Mapping[str, Any],
    ) -> Any:
        self.binder.invocations.append(
            _RecordedInvocation(
                call_target="constructor",
                class_name=orm_class.__name__,
                function_name=function_name,
                object_id=None,
                payload=dict(payload),
            )
        )
        if orm_class is Identity and function_name == "signup_via_profile":
            return {"value": Identity.model_construct(id=self.binder.identity_id)}
        raise AssertionError(
            f"unexpected constructor invocation: {orm_class}.{function_name}"
        )

    async def invoke_instance(
        self,
        *,
        orm_model: ORMModel,
        function_name: str,
        payload: Mapping[str, Any],
    ) -> Any:
        raise AssertionError(
            f"unexpected instance invocation: {orm_model}.{function_name}"
        )


@pytest.mark.asyncio
async def test_identity_admission_runtime_uses_bound_orm_facade() -> None:
    from aware_identity.admission import (
        IdentityAdmissionOperationContext,
        IdentityAdmissionRuntimeRequest,
        admit_identity_via_profile,
        resolve_identity_admission_runtime_context,
    )
    from aware_identity_ontology.identity.create_profile_request import (
        CreateProfileRequest,
    )
    from aware_identity_ontology.identity.identity_enums import IdentityType
    from aware_identity_ontology.stable_ids import (
        stable_actor_id,
        stable_identity_id,
        stable_identity_profile_id,
    )

    public_key = f"ed25519:{'66' * 32}"
    expected_identity_id = stable_identity_id(
        public_key=public_key,
        type="organization",
    )
    expected_actor_id = stable_actor_id(identity_id=expected_identity_id)
    binder = _RecordingLaneBinder(identity_id=expected_identity_id)
    runtime_context = resolve_identity_admission_runtime_context(
        lane_binder=binder,
    )
    profile_request = CreateProfileRequest(
        display_name="Aware Taiwan",
        public_handle="aware-taiwan",
        full_name="Aware Taiwan",
        country_code="TW",
        language_code="en",
        bio=None,
        identity_type=IdentityType.organization,
    )

    receipt = await admit_identity_via_profile(
        runtime_context=runtime_context,
        operation_context=IdentityAdmissionOperationContext(
            actor_id=expected_actor_id,
        ),
        request=IdentityAdmissionRuntimeRequest(
            public_key=public_key,
            create_profile_request=profile_request,
        ),
    )

    assert receipt.identity_id == expected_identity_id
    assert receipt.actor_id == expected_actor_id
    assert receipt.identity_profile_id == stable_identity_profile_id(
        public_handle="aware-taiwan"
    )
    assert receipt.public_handle == "aware-taiwan"
    assert binder.binds == [
        {
            "projection": "Identity",
            "branch_id": expected_identity_id,
            "actor_id": expected_actor_id,
        }
    ]
    assert len(binder.invocations) == 1
    invocation = binder.invocations[0]
    assert invocation.call_target == "constructor"
    assert invocation.class_name == "Identity"
    assert invocation.function_name == "signup_via_profile"
    assert invocation.payload["public_key"] == public_key
    assert invocation.payload["type"] is IdentityType.organization
    assert invocation.payload["create_profile_request"] is profile_request
