from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from .builder import SdkCompilePlan
from .compile import compile_sdk_workspace


class SdkOperationDispatchContractError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class SdkOperationDispatchContract:
    sdk_name: str
    operation_name: str
    operation_ref: str
    endpoint_refs: tuple[str, ...]
    sdk_operation_dependency_refs: tuple[str, ...]
    source_path: str


def load_sdk_operation_dispatch_contracts(
    *,
    toml_path: str | Path,
    repo_root: str | Path | None = None,
) -> tuple[SdkOperationDispatchContract, ...]:
    result = compile_sdk_workspace(
        toml_path=toml_path,
        repo_root=repo_root,
    )
    if result.compile_plan is None:
        raise SdkOperationDispatchContractError(
            "SDK operation dispatch contracts require sdk_ontology compilation mode: "
            + f"toml_path={toml_path!s}"
        )
    return sdk_operation_dispatch_contracts_from_compile_plan(
        plan=result.compile_plan,
    )


def sdk_operation_dispatch_contracts_from_compile_plan(
    *,
    plan: SdkCompilePlan,
) -> tuple[SdkOperationDispatchContract, ...]:
    contracts: list[SdkOperationDispatchContract] = []
    for sdk_config in plan.sdk_configs:
        sdk_name = _normalize_sdk_name(sdk_config.name)
        for operation in sdk_config.operations:
            operation_name = _normalize_operation_name(operation.name)
            contracts.append(
                SdkOperationDispatchContract(
                    sdk_name=sdk_name,
                    operation_name=operation_name,
                    operation_ref=f"{sdk_name}.{operation_name}",
                    endpoint_refs=tuple(
                        endpoint.endpoint_ref
                        for endpoint in sorted(
                            operation.api_endpoints,
                            key=lambda item: (item.order, item.endpoint_ref),
                        )
                    ),
                    sdk_operation_dependency_refs=tuple(
                        dependency.target_operation_ref
                        for dependency in sorted(
                            operation.sdk_operation_dependencies,
                            key=lambda item: (
                                item.order,
                                item.target_operation_ref,
                            ),
                        )
                    ),
                    source_path=operation.source_path,
                )
            )
    return tuple(sorted(contracts, key=lambda item: item.operation_ref))


def assert_sdk_operation_dispatch_registry_matches_contract(
    *,
    contracts: Iterable[SdkOperationDispatchContract],
    dispatchers: Mapping[str, object],
    required_operation_refs: Iterable[str] | None = None,
) -> tuple[SdkOperationDispatchContract, ...]:
    contract_by_ref = {
        _normalize_operation_ref(contract.operation_ref): contract
        for contract in contracts
    }
    if not contract_by_ref:
        raise SdkOperationDispatchContractError(
            "SDK operation dispatch contract set is empty."
        )

    dispatcher_by_ref: dict[str, object] = {}
    for raw_ref, dispatcher in dispatchers.items():
        operation_ref = _normalize_operation_ref(raw_ref)
        if operation_ref in dispatcher_by_ref:
            raise SdkOperationDispatchContractError(
                f"Duplicate SDK dispatcher operation_ref={operation_ref!r}."
            )
        dispatcher_by_ref[operation_ref] = dispatcher

    unknown_refs = sorted(set(dispatcher_by_ref).difference(contract_by_ref))
    if unknown_refs:
        raise SdkOperationDispatchContractError(
            "SDK operation dispatcher registry contains refs not declared in "
            "SDK source: "
            + ", ".join(unknown_refs)
        )

    for operation_ref, dispatcher in sorted(dispatcher_by_ref.items()):
        if not callable(dispatcher):
            raise SdkOperationDispatchContractError(
                "SDK operation dispatcher must be callable: "
                + f"operation_ref={operation_ref!r}"
            )

    if required_operation_refs is None:
        required_refs = set(contract_by_ref)
    else:
        required_refs = {
            _normalize_operation_ref(operation_ref)
            for operation_ref in required_operation_refs
        }
        undeclared_required = sorted(required_refs.difference(contract_by_ref))
        if undeclared_required:
            raise SdkOperationDispatchContractError(
                "Required SDK operation dispatch refs are not declared in SDK "
                "source: "
                + ", ".join(undeclared_required)
            )

    missing_refs = sorted(required_refs.difference(dispatcher_by_ref))
    if missing_refs:
        raise SdkOperationDispatchContractError(
            "SDK operation dispatcher registry is missing required refs: "
            + ", ".join(missing_refs)
        )

    matched_refs = sorted(set(dispatcher_by_ref).intersection(contract_by_ref))
    return tuple(contract_by_ref[operation_ref] for operation_ref in matched_refs)


def _normalize_sdk_name(value: str) -> str:
    token = _normalize_token(value, label="sdk name")
    if "." in token:
        raise SdkOperationDispatchContractError(
            f"SDK name must not contain '.': {value!r}"
        )
    return token


def _normalize_operation_name(value: str) -> str:
    token = _normalize_token(value, label="operation name")
    if "." in token:
        raise SdkOperationDispatchContractError(
            f"SDK operation name must not contain '.': {value!r}"
        )
    return token


def _normalize_operation_ref(value: str) -> str:
    parts = [
        _normalize_token(part, label="operation ref segment")
        for part in str(value or "").split(".")
        if part.strip()
    ]
    if len(parts) != 2:
        raise SdkOperationDispatchContractError(
            "SDK operation ref must use `sdk_name.operation_name`: "
            + f"{value!r}"
        )
    return ".".join(parts)


def _normalize_token(value: str, *, label: str) -> str:
    token = str(value or "").strip()
    if not token:
        raise SdkOperationDispatchContractError(f"SDK {label} must be non-empty.")
    return token


__all__ = [
    "SdkOperationDispatchContract",
    "SdkOperationDispatchContractError",
    "assert_sdk_operation_dispatch_registry_matches_contract",
    "load_sdk_operation_dispatch_contracts",
    "sdk_operation_dispatch_contracts_from_compile_plan",
]
