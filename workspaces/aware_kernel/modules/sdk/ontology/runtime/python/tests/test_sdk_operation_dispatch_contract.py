from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest

from aware_sdk_runtime.operation_dispatch_contract import (
    SdkOperationDispatchContract,
    SdkOperationDispatchContractError,
    assert_sdk_operation_dispatch_registry_matches_contract,
    load_sdk_operation_dispatch_contracts,
)
from _sdk_runtime_test_paths import REPO_ROOT


def _contract(
    operation_ref: str,
    *,
    endpoint_refs: tuple[str, ...] = ("demo.capability.endpoint",),
) -> SdkOperationDispatchContract:
    sdk_name, operation_name = operation_ref.split(".", 1)
    return SdkOperationDispatchContract(
        sdk_name=sdk_name,
        operation_name=operation_name,
        operation_ref=operation_ref,
        endpoint_refs=endpoint_refs,
        sdk_operation_dependency_refs=(),
        source_path="demo_sdk.aware",
    )


def _dispatcher(**kwargs: object) -> object:
    return kwargs


def test_sdk_operation_dispatch_registry_rejects_unknown_operation_ref() -> None:
    with pytest.raises(
        SdkOperationDispatchContractError,
        match="not declared in SDK source",
    ):
        assert_sdk_operation_dispatch_registry_matches_contract(
            contracts=(_contract("demo_sdk.run"),),
            dispatchers={"demo_sdk.other": _dispatcher},
        )


def test_sdk_operation_dispatch_registry_requires_declared_refs() -> None:
    with pytest.raises(
        SdkOperationDispatchContractError,
        match="missing required refs",
    ):
        assert_sdk_operation_dispatch_registry_matches_contract(
            contracts=(_contract("demo_sdk.run"),),
            dispatchers={},
            required_operation_refs=("demo_sdk.run",),
        )


def test_sdk_operation_dispatch_registry_requires_callables() -> None:
    with pytest.raises(
        SdkOperationDispatchContractError,
        match="must be callable",
    ):
        assert_sdk_operation_dispatch_registry_matches_contract(
            contracts=(_contract("demo_sdk.run"),),
            dispatchers={"demo_sdk.run": object()},
            required_operation_refs=("demo_sdk.run",),
        )


def test_sdk_operation_dispatch_registry_accepts_partial_declared_registry() -> None:
    matched = assert_sdk_operation_dispatch_registry_matches_contract(
        contracts=(
            _contract("demo_sdk.run"),
            _contract("demo_sdk.check"),
        ),
        dispatchers={"demo_sdk.run": _dispatcher},
        required_operation_refs=("demo_sdk.run",),
    )

    assert tuple(contract.operation_ref for contract in matched) == ("demo_sdk.run",)


def test_identity_sdk_operation_dispatch_registry_matches_authored_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    _prepend_identity_sdk_import_roots(monkeypatch=monkeypatch, repo_root=repo_root)

    from aware_identity_sdk.operation_dispatchers import (  # noqa: WPS433
        IDENTITY_SDK_ADMIT_IDENTITY_OPERATION_REF,
        SDK_OPERATION_DISPATCHERS,
    )

    contracts = load_sdk_operation_dispatch_contracts(
        toml_path=repo_root / "sdks" / "identity" / "aware" / "aware.sdk.toml",
        repo_root=repo_root,
    )

    matched = assert_sdk_operation_dispatch_registry_matches_contract(
        contracts=contracts,
        dispatchers=SDK_OPERATION_DISPATCHERS,
        required_operation_refs=(IDENTITY_SDK_ADMIT_IDENTITY_OPERATION_REF,),
    )

    assert tuple(contract.operation_ref for contract in matched) == (
        "identity_sdk.admit_identity",
    )
    assert matched[0].endpoint_refs == (
        "identity.signup_via_profile.signup_via_profile",
    )
    contract_by_ref = {contract.operation_ref: contract for contract in contracts}
    assert {
        "identity_sdk.setup_credential_profile",
        "identity_sdk.check_credential_readiness",
        "identity_sdk.signup_via_profile",
        "identity_sdk.resolve_role_assignments",
        "identity_sdk.admit_identity",
    } <= set(contract_by_ref)


def _prepend_identity_sdk_import_roots(
    *,
    monkeypatch: pytest.MonkeyPatch,
    repo_root: Path,
) -> None:
    syspath_prepend = getattr(monkeypatch, "syspath_prepend")
    for path in (
        repo_root / "sdks" / "identity" / "python",
        repo_root / "apis" / "identity" / "python" / "aware_identity_service_api",
        repo_root / "modules" / "api" / "structure" / "api" / "python",
        repo_root / "modules" / "service" / "structure" / "api" / "python",
    ):
        syspath_prepend(str(path.resolve()))


def test_dispatcher_helper_type_signature_is_callable() -> None:
    typed: Callable[..., object] = _dispatcher
    assert callable(typed)
