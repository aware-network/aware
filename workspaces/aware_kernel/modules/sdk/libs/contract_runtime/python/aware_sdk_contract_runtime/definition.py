from __future__ import annotations

import hashlib
from dataclasses import dataclass

from aware_meta_type_schema import canonical_json

from .model import SdkContractManifest

SDK_CONTRACT_INVENTORY = "aware.sdk.contract-inventory.v1"
SDK_DEFINITION_STATE = "aware.sdk.definition-state.v1"


def _token(value: object, field: str) -> str:
    if (
        type(value) is not str
        or not value
        or value.strip() != value
        or any(character.isspace() for character in value)
    ):
        raise ValueError(f"{field} must be an exact normalized nonempty token")
    return value


def _optional_token(value: object, field: str) -> str | None:
    return None if value is None else _token(value, field)


def _token_tuple(value: object, field: str) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field} must be an exact tuple")
    result = tuple(_token(item, f"{field}[{index}]") for index, item in enumerate(value))
    if len(result) != len(set(result)):
        raise ValueError(f"{field} contains duplicates")
    return result


def _digest(contract: str, semantic: object) -> str:
    body = f"{contract}\n{canonical_json(semantic)}".encode("utf-8")
    return f"sha256:{hashlib.sha256(body).hexdigest()}"


def _sha256(value: object, field: str) -> str:
    item = _token(value, field)
    suffix = item.removeprefix("sha256:")
    if not item.startswith("sha256:") or len(suffix) != 64:
        raise ValueError(f"{field} must be a sha256 digest")
    try:
        int(suffix, 16)
    except ValueError as error:
        raise ValueError(f"{field} must be a sha256 digest") from error
    if suffix != suffix.lower():
        raise ValueError(f"{field} must use lowercase hex")
    return item


@dataclass(frozen=True, slots=True)
class SdkOperationInventoryEntry:
    operation_ref: str
    contract_posture: str
    request_type_ref: str | None
    result_type_ref: str | None
    error_type_refs: tuple[str, ...]
    provider_operation_ref: str | None
    endpoint_refs: tuple[str, ...]
    dependency_operation_refs: tuple[str, ...]
    method_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "operation_ref", _token(self.operation_ref, "operation_ref"))
        posture = _token(self.contract_posture, "contract_posture")
        if posture not in {"contracted", "legacy"}:
            raise ValueError("contract_posture must be contracted or legacy")
        object.__setattr__(self, "contract_posture", posture)
        object.__setattr__(self, "request_type_ref", _optional_token(self.request_type_ref, "request_type_ref"))
        object.__setattr__(self, "result_type_ref", _optional_token(self.result_type_ref, "result_type_ref"))
        object.__setattr__(self, "error_type_refs", _token_tuple(self.error_type_refs, "error_type_refs"))
        object.__setattr__(self, "provider_operation_ref", _optional_token(self.provider_operation_ref, "provider_operation_ref"))
        object.__setattr__(self, "endpoint_refs", _token_tuple(self.endpoint_refs, "endpoint_refs"))
        object.__setattr__(self, "dependency_operation_refs", _token_tuple(self.dependency_operation_refs, "dependency_operation_refs"))
        object.__setattr__(self, "method_refs", _token_tuple(self.method_refs, "method_refs"))
        complete = (
            self.request_type_ref is not None
            and self.result_type_ref is not None
            and bool(self.error_type_refs)
            and self.provider_operation_ref is not None
        )
        if (posture == "contracted") != complete:
            raise ValueError("contract posture must equal complete portable operation shape")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "operation_ref": self.operation_ref,
            "contract_posture": self.contract_posture,
            "request_type_ref": self.request_type_ref,
            "result_type_ref": self.result_type_ref,
            "error_type_refs": list(self.error_type_refs),
            "provider_operation_ref": self.provider_operation_ref,
            "endpoint_refs": list(self.endpoint_refs),
            "dependency_operation_refs": list(self.dependency_operation_refs),
            "method_refs": list(self.method_refs),
        }


@dataclass(frozen=True, slots=True)
class SdkMethodInventoryEntry:
    method_ref: str
    operation_ref: str
    method_family: str
    effect: str
    mutation_scope: str
    confirmation_policy: str
    execution_mode: str
    runtime_binding_kind: str

    def __post_init__(self) -> None:
        for field in (
            "method_ref",
            "operation_ref",
            "method_family",
            "effect",
            "mutation_scope",
            "confirmation_policy",
            "execution_mode",
            "runtime_binding_kind",
        ):
            object.__setattr__(self, field, _token(getattr(self, field), field))

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "method_ref": self.method_ref,
            "operation_ref": self.operation_ref,
            "method_family": self.method_family,
            "effect": self.effect,
            "mutation_scope": self.mutation_scope,
            "confirmation_policy": self.confirmation_policy,
            "execution_mode": self.execution_mode,
            "runtime_binding_kind": self.runtime_binding_kind,
        }


@dataclass(frozen=True, slots=True)
class SdkContractInventory:
    sdk_ref: str
    operation_refs: tuple[str, ...]
    contracted_operation_refs: tuple[str, ...]
    legacy_operation_refs: tuple[str, ...]
    method_refs: tuple[str, ...]
    operations: tuple[SdkOperationInventoryEntry, ...]
    methods: tuple[SdkMethodInventoryEntry, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "sdk_ref", _token(self.sdk_ref, "sdk_ref"))
        for field in (
            "operation_refs",
            "contracted_operation_refs",
            "legacy_operation_refs",
            "method_refs",
        ):
            object.__setattr__(self, field, _token_tuple(getattr(self, field), field))
        if type(self.operations) is not tuple or any(
            type(value) is not SdkOperationInventoryEntry for value in self.operations
        ):
            raise TypeError("operations must be an exact tuple of SdkOperationInventoryEntry")
        if type(self.methods) is not tuple or any(
            type(value) is not SdkMethodInventoryEntry for value in self.methods
        ):
            raise TypeError("methods must be an exact tuple of SdkMethodInventoryEntry")
        for value in self.operations:
            value.__post_init__()
        for value in self.methods:
            value.__post_init__()
        operation_refs = tuple(value.operation_ref for value in self.operations)
        method_refs = tuple(value.method_ref for value in self.methods)
        if operation_refs != self.operation_refs or operation_refs != tuple(sorted(operation_refs, key=str.encode)):
            raise ValueError("inventory operations must exactly match ordered operation_refs")
        if method_refs != self.method_refs or method_refs != tuple(sorted(method_refs, key=str.encode)):
            raise ValueError("inventory methods must exactly match ordered method_refs")
        contracted = tuple(value.operation_ref for value in self.operations if value.contract_posture == "contracted")
        legacy = tuple(value.operation_ref for value in self.operations if value.contract_posture == "legacy")
        if contracted != self.contracted_operation_refs or legacy != self.legacy_operation_refs:
            raise ValueError("inventory posture partitions must exactly match operation entries")
        if set(contracted) & set(legacy) or set(contracted) | set(legacy) != set(operation_refs):
            raise ValueError("inventory posture partitions must be disjoint and complete")
        if any(value.operation_ref not in self.operation_refs for value in self.methods):
            raise ValueError("inventory method references an unknown operation")
        methods_by_operation: dict[str, list[str]] = {ref: [] for ref in operation_refs}
        for value in self.methods:
            methods_by_operation[value.operation_ref].append(value.method_ref)
        for value in self.operations:
            if value.method_refs != tuple(methods_by_operation[value.operation_ref]):
                raise ValueError("operation method_refs differ from complete method inventory")

    @property
    def inventory_digest(self) -> str:
        self.__post_init__()
        return _digest(SDK_CONTRACT_INVENTORY, self.to_wire())

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "sdk_ref": self.sdk_ref,
            "operation_count": len(self.operation_refs),
            "contracted_operation_count": len(self.contracted_operation_refs),
            "legacy_operation_count": len(self.legacy_operation_refs),
            "method_count": len(self.method_refs),
            "operations": [value.to_wire() for value in self.operations],
            "methods": [value.to_wire() for value in self.methods],
        }


@dataclass(frozen=True, slots=True)
class SdkDefinitionState:
    manifest: SdkContractManifest
    inventory: SdkContractInventory
    definition_digest: str
    contract: str = SDK_DEFINITION_STATE

    def __post_init__(self) -> None:
        from .validation import validate_sdk_definition_state_graph

        validate_sdk_definition_state_graph(self)
        expected = _digest(SDK_DEFINITION_STATE, self.semantic_wire())
        if self.definition_digest != expected:
            raise ValueError(f"definition_digest mismatch; expected {expected}")

    @classmethod
    def create(
        cls, manifest: SdkContractManifest, inventory: SdkContractInventory
    ) -> SdkDefinitionState:
        provisional = object.__new__(cls)
        object.__setattr__(provisional, "manifest", manifest)
        object.__setattr__(provisional, "inventory", inventory)
        object.__setattr__(provisional, "definition_digest", "sha256:" + "0" * 64)
        object.__setattr__(provisional, "contract", SDK_DEFINITION_STATE)
        from .validation import validate_sdk_definition_state_graph

        validate_sdk_definition_state_graph(provisional, check_digest=False)
        digest = _digest(SDK_DEFINITION_STATE, provisional.semantic_wire())
        return cls(manifest, inventory, digest)

    def semantic_wire(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "manifest": self.manifest.to_wire(),
            "inventory": {
                **self.inventory.to_wire(),
                "inventory_digest": self.inventory.inventory_digest,
            },
        }

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {**self.semantic_wire(), "definition_digest": self.definition_digest}


__all__ = [
    "SDK_CONTRACT_INVENTORY",
    "SDK_DEFINITION_STATE",
    "SdkContractInventory",
    "SdkDefinitionState",
    "SdkMethodInventoryEntry",
    "SdkOperationInventoryEntry",
]
