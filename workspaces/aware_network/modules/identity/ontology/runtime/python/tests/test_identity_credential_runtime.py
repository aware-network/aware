from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

import pytest

from aware_identity_ontology.credential.credential_profile import CredentialProfile
from aware_identity_ontology.credential.credential_readiness_receipt import (
    CredentialReadinessReceipt,
)
from aware_identity_ontology.credential.credential_secret_material_ref import (
    CredentialSecretMaterialRef,
)
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
    def __init__(
        self,
        *,
        credential_profile_id: UUID,
        secret_material_ref_id: UUID | None = None,
        readiness_receipt_id: UUID | None = None,
    ) -> None:
        self.credential_profile_id = credential_profile_id
        self.secret_material_ref_id = secret_material_ref_id
        self.readiness_receipt_id = readiness_receipt_id
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
        return self.binder.binds[-1]["branch_id"]

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

    async def invoke_instance(
        self,
        *,
        orm_model: ORMModel,
        function_name: str,
        payload: Mapping[str, Any],
    ) -> Any:
        self.binder.invocations.append(
            _RecordedInvocation(
                call_target="instance",
                class_name=type(orm_model).__name__,
                function_name=function_name,
                object_id=orm_model.id if isinstance(orm_model.id, UUID) else None,
                payload=dict(payload),
            )
        )
        if (
            isinstance(orm_model, Identity)
            and function_name == "create_credential_profile"
        ):
            return {
                "value": CredentialProfile.model_construct(
                    id=self.binder.credential_profile_id,
                    identity_id=orm_model.id,
                    profile_key=payload["profile_key"],
                    target_kind=payload["target_kind"],
                )
            }
        if (
            isinstance(orm_model, CredentialProfile)
            and function_name == "attach_secret_material_ref"
        ):
            if self.binder.secret_material_ref_id is None:
                raise AssertionError("secret material ref id was not configured")
            return {
                "value": CredentialSecretMaterialRef.model_construct(
                    id=self.binder.secret_material_ref_id,
                    credential_profile_id=orm_model.id,
                )
            }
        if (
            isinstance(orm_model, CredentialProfile)
            and function_name == "record_readiness"
        ):
            if self.binder.readiness_receipt_id is None:
                raise AssertionError("readiness receipt id was not configured")
            return {
                "value": CredentialReadinessReceipt.model_construct(
                    id=self.binder.readiness_receipt_id,
                    credential_profile_id=orm_model.id,
                )
            }
        raise AssertionError(
            f"unexpected instance invocation: {orm_model}.{function_name}"
        )

    async def invoke_constructor(
        self,
        *,
        orm_class: type[ORMModel],
        function_name: str,
        payload: Mapping[str, Any],
    ) -> Any:
        raise AssertionError(
            f"unexpected constructor invocation: {orm_class}.{function_name}"
        )


@pytest.mark.asyncio
async def test_identity_credential_runtime_uses_orm_facades_without_secret_material() -> (
    None
):
    from aware_identity.credential import (
        CredentialProfileSetupRuntimeRequest,
        IdentityCredentialOperationContext,
        resolve_identity_credential_runtime_context,
        setup_credential_profile,
    )
    from aware_identity_ontology.stable_ids import (
        stable_credential_profile_id,
        stable_credential_secret_material_ref_id,
    )

    identity_id = uuid4()
    actor_id = uuid4()
    expected_profile_id = stable_credential_profile_id(
        identity_id=identity_id,
        profile_key="pypi.publish",
        target_kind="test_pypi",
    )
    expected_secret_ref_id = stable_credential_secret_material_ref_id(
        credential_profile_id=expected_profile_id,
        secret_ref_key="twine-password",
        resolver_kind="env_var",
    )
    binder = _RecordingLaneBinder(
        credential_profile_id=expected_profile_id,
        secret_material_ref_id=expected_secret_ref_id,
    )
    runtime_context = resolve_identity_credential_runtime_context(lane_binder=binder)

    receipt = await setup_credential_profile(
        runtime_context=runtime_context,
        operation_context=IdentityCredentialOperationContext(actor_id=actor_id),
        request=CredentialProfileSetupRuntimeRequest(
            identity_id=identity_id,
            profile_key="pypi.publish",
            target_kind="test_pypi",
            credential_kind="api_key",
            status="planned",
            display_name="TestPyPI publisher",
            target_name="aware-api-client",
            secret_ref_key="twine-password",
            resolver_kind="env_var",
            secret_name="TWINE_PASSWORD",
            username_hint="__token__",
        ),
    )

    assert receipt.identity_id == identity_id
    assert receipt.credential_profile_id == expected_profile_id
    assert receipt.secret_material_ref_id == expected_secret_ref_id
    assert receipt.raw_secret_stored is False
    assert binder.binds == [
        {
            "projection": "Identity",
            "branch_id": identity_id,
            "actor_id": actor_id,
        }
    ]
    assert [call.function_name for call in binder.invocations] == [
        "create_credential_profile",
        "attach_secret_material_ref",
    ]
    create_call, attach_call = binder.invocations
    assert create_call.class_name == "Identity"
    assert create_call.object_id == identity_id
    assert create_call.payload["profile_key"] == "pypi.publish"
    assert create_call.payload["target_kind"] == "test_pypi"
    assert attach_call.class_name == "CredentialProfile"
    assert attach_call.object_id == expected_profile_id
    assert attach_call.payload["secret_ref_key"] == "twine-password"
    assert attach_call.payload["secret_name"] == "TWINE_PASSWORD"
    assert "secret_value" not in attach_call.payload


@pytest.mark.asyncio
async def test_identity_credential_runtime_records_readiness_without_secret_material(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from aware_identity.credential import (
        CredentialReadinessCheckRuntimeRequest,
        IdentityCredentialOperationContext,
        check_credential_readiness,
        resolve_identity_credential_runtime_context,
    )
    from aware_identity_ontology.stable_ids import (
        stable_credential_profile_id,
        stable_credential_readiness_receipt_id,
    )

    identity_id = uuid4()
    actor_id = uuid4()
    secret_value = "pypi-token-secret"
    monkeypatch.setenv("TWINE_PASSWORD", secret_value)
    expected_profile_id = stable_credential_profile_id(
        identity_id=identity_id,
        profile_key="pypi.publish",
        target_kind="test_pypi",
    )
    expected_readiness_id = stable_credential_readiness_receipt_id(
        credential_profile_id=expected_profile_id,
        receipt_key="testpypi-local",
    )
    binder = _RecordingLaneBinder(
        credential_profile_id=expected_profile_id,
        readiness_receipt_id=expected_readiness_id,
    )
    runtime_context = resolve_identity_credential_runtime_context(lane_binder=binder)

    receipt = await check_credential_readiness(
        runtime_context=runtime_context,
        operation_context=IdentityCredentialOperationContext(actor_id=actor_id),
        request=CredentialReadinessCheckRuntimeRequest(
            identity_id=identity_id,
            profile_key="pypi.publish",
            target_kind="test_pypi",
            receipt_key="testpypi-local",
            resolver_kind="env_var",
            secret_ref_key="twine-password",
            secret_name="TWINE_PASSWORD",
            checked_at_utc="2026-04-30T07:58:00Z",
        ),
    )

    assert receipt.identity_id == identity_id
    assert receipt.credential_profile_id == expected_profile_id
    assert receipt.readiness_receipt_id == expected_readiness_id
    assert receipt.status == "ready"
    assert receipt.available is True
    assert receipt.missing_requirements == []
    assert receipt.raw_secret_returned is False
    assert secret_value not in str(receipt.credential_handle)
    assert binder.binds == [
        {
            "projection": "Identity",
            "branch_id": identity_id,
            "actor_id": actor_id,
        }
    ]
    assert len(binder.invocations) == 1
    record_call = binder.invocations[0]
    assert record_call.class_name == "CredentialProfile"
    assert record_call.function_name == "record_readiness"
    assert record_call.object_id == expected_profile_id
    assert record_call.payload["receipt_key"] == "testpypi-local"
    assert record_call.payload["status"] == "ready"
    assert record_call.payload["secret_ref_key"] == "twine-password"
    assert record_call.payload["missing_requirements"] == []
    assert secret_value not in str(record_call.payload)
