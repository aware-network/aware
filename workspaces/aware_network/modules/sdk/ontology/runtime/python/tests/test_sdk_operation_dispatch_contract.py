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


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(text, encoding="utf-8")


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


def test_sdk_operation_dispatch_registry_matches_authored_contract(
    tmp_path: Path,
) -> None:
    package_root = tmp_path / "sdks" / "identity" / "aware"
    _write(
        package_root / "aware.sdk.toml",
        """
aware_sdk = 1

[sdk]
package_name = "identity-sdk"
fqn_prefix = "aware_identity_sdk"

[build]
sources_dir = "."
compilation_mode = "sdk_ontology"
""",
    )
    _write(
        package_root / "identity_sdk.aware",
        """\
sdk identity_sdk {
    api identity

    operation setup_credential_profile {
        endpoint identity.setup_credential_profile.setup_credential_profile
    }

    operation check_credential_readiness {
        endpoint identity.check_credential_readiness.check_credential_readiness
    }

    operation signup_via_profile {
        endpoint identity.signup_via_profile.signup_via_profile
        view identity.identity_admission
    }

    operation resolve_role_assignments {
        endpoint identity.resolve_role_assignments.resolve_role_assignments
        view identity.actor_roles
    }

    operation admit_identity {
        endpoint identity.signup_via_profile.signup_via_profile
        view identity.identity_admission
    }
}
""",
    )

    contracts = load_sdk_operation_dispatch_contracts(
        toml_path=package_root / "aware.sdk.toml",
        repo_root=tmp_path,
    )

    matched = assert_sdk_operation_dispatch_registry_matches_contract(
        contracts=contracts,
        dispatchers={"identity_sdk.admit_identity": _dispatcher},
        required_operation_refs=("identity_sdk.admit_identity",),
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


def test_dispatcher_helper_type_signature_is_callable() -> None:
    typed: Callable[..., object] = _dispatcher
    assert callable(typed)
