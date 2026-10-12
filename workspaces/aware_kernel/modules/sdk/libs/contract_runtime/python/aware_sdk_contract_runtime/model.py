from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass

from aware_meta_type_schema import TypeSchemaSlice, canonical_json

SDK_CONTRACT = "aware.sdk.contract-manifest.v1"


def _token(value: str, field: str) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ValueError(f"{field} must be normalized nonempty text")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field} must not contain whitespace")
    return value


def _tokens(values: Iterable[str], field: str) -> tuple[str, ...]:
    result = tuple(sorted(_token(value, field) for value in values))
    if len(result) != len(set(result)):
        raise ValueError(f"{field} contains duplicates")
    return result


def _digest(value: str, field: str) -> str:
    value = _token(value, field)
    suffix = value.removeprefix("sha256:")
    if not value.startswith("sha256:") or len(suffix) != 64:
        raise ValueError(f"{field} must be a sha256 digest")
    try:
        int(suffix, 16)
    except ValueError as error:
        raise ValueError(f"{field} must be a sha256 digest") from error
    if suffix != suffix.lower():
        raise ValueError(f"{field} must use lowercase hex")
    return value


def _manifest_digest(semantic: object) -> str:
    payload = f"{SDK_CONTRACT}\n{canonical_json(semantic)}".encode()
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


@dataclass(frozen=True, slots=True)
class SdkTargetContract:
    language: str
    root_dir: str
    package_dir: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "language", _token(self.language, "language"))
        object.__setattr__(self, "root_dir", _token(self.root_dir, "root_dir"))
        object.__setattr__(self, "package_dir", _token(self.package_dir, "package_dir"))

    def to_wire(self) -> dict[str, object]:
        return {
            "language": self.language,
            "root_dir": self.root_dir,
            "package_dir": self.package_dir,
        }


@dataclass(frozen=True, slots=True)
class SdkOperationContract:
    operation_ref: str
    request_schema_digest: str
    result_schema_digest: str
    error_schema_digests: tuple[str, ...]
    provider_operation_ref: str
    endpoint_refs: tuple[str, ...] = ()
    dependency_operation_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "operation_ref", _token(self.operation_ref, "operation_ref")
        )
        object.__setattr__(
            self,
            "request_schema_digest",
            _digest(self.request_schema_digest, "request_schema_digest"),
        )
        object.__setattr__(
            self,
            "result_schema_digest",
            _digest(self.result_schema_digest, "result_schema_digest"),
        )
        errors = tuple(
            sorted(
                _digest(value, "error_schema_digest")
                for value in self.error_schema_digests
            )
        )
        if not errors or len(errors) != len(set(errors)):
            raise ValueError("error_schema_digests must be nonempty and unique")
        object.__setattr__(self, "error_schema_digests", errors)
        object.__setattr__(
            self,
            "provider_operation_ref",
            _token(self.provider_operation_ref, "provider_operation_ref"),
        )
        object.__setattr__(
            self, "endpoint_refs", _tokens(self.endpoint_refs, "endpoint_ref")
        )
        object.__setattr__(
            self,
            "dependency_operation_refs",
            _tokens(self.dependency_operation_refs, "dependency_operation_ref"),
        )

    def schema_digests(self) -> frozenset[str]:
        return frozenset(
            (
                self.request_schema_digest,
                self.result_schema_digest,
                *self.error_schema_digests,
            )
        )

    def to_wire(self) -> dict[str, object]:
        return {
            "operation_ref": self.operation_ref,
            "request_schema_digest": self.request_schema_digest,
            "result_schema_digest": self.result_schema_digest,
            "error_schema_digests": list(self.error_schema_digests),
            "provider_operation_ref": self.provider_operation_ref,
            "endpoint_refs": list(self.endpoint_refs),
            "dependency_operation_refs": list(self.dependency_operation_refs),
        }


@dataclass(frozen=True, slots=True)
class SdkMethodContract:
    method_ref: str
    operation_ref: str
    method_family: str
    effect: str
    mutation_scope: str
    confirmation_policy: str
    execution_mode: str

    def __post_init__(self) -> None:
        for field in (
            "method_ref",
            "operation_ref",
            "method_family",
            "effect",
            "mutation_scope",
            "confirmation_policy",
            "execution_mode",
        ):
            object.__setattr__(self, field, _token(getattr(self, field), field))

    def to_wire(self) -> dict[str, object]:
        return {
            "method_ref": self.method_ref,
            "operation_ref": self.operation_ref,
            "method_family": self.method_family,
            "effect": self.effect,
            "mutation_scope": self.mutation_scope,
            "confirmation_policy": self.confirmation_policy,
            "execution_mode": self.execution_mode,
        }


def _slices(values: Iterable[TypeSchemaSlice]) -> tuple[TypeSchemaSlice, ...]:
    result = tuple(sorted(values, key=lambda value: value.slice_digest))
    if not result or any(type(value) is not TypeSchemaSlice for value in result):
        raise ValueError("schema_slices must contain exact TypeSchemaSlice values")
    if len({value.slice_digest for value in result}) != len(result):
        raise ValueError("schema_slices contain duplicate slice digests")
    return result


def _targets(values: Iterable[SdkTargetContract]) -> tuple[SdkTargetContract, ...]:
    result = tuple(sorted(values, key=lambda value: value.language))
    if not result or any(type(value) is not SdkTargetContract for value in result):
        raise ValueError("targets must contain exact SdkTargetContract values")
    if len({value.language for value in result}) != len(result):
        raise ValueError("target languages must be unique")
    return result


def _operations(
    values: Iterable[SdkOperationContract],
) -> tuple[SdkOperationContract, ...]:
    result = tuple(sorted(values, key=lambda value: value.operation_ref))
    if not result or any(type(value) is not SdkOperationContract for value in result):
        raise ValueError("operations must contain exact SdkOperationContract values")
    if len({value.operation_ref for value in result}) != len(result):
        raise ValueError("operation refs must be unique")
    return result


def _methods(values: Iterable[SdkMethodContract]) -> tuple[SdkMethodContract, ...]:
    result = tuple(sorted(values, key=lambda value: value.method_ref))
    if not result or any(type(value) is not SdkMethodContract for value in result):
        raise ValueError("methods must contain exact SdkMethodContract values")
    if len({value.method_ref for value in result}) != len(result):
        raise ValueError("method refs must be unique")
    return result


@dataclass(frozen=True, slots=True)
class SdkContractManifest:
    sdk_ref: str
    semantic_version: str
    targets: tuple[SdkTargetContract, ...]
    schema_slices: tuple[TypeSchemaSlice, ...]
    operations: tuple[SdkOperationContract, ...]
    methods: tuple[SdkMethodContract, ...]
    manifest_digest: str
    contract: str = SDK_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != SDK_CONTRACT:
            raise ValueError(f"unsupported SDK contract {self.contract!r}")
        object.__setattr__(self, "sdk_ref", _token(self.sdk_ref, "sdk_ref"))
        object.__setattr__(
            self, "semantic_version", _token(self.semantic_version, "semantic_version")
        )
        targets = _targets(self.targets)
        slices = _slices(self.schema_slices)
        operations = _operations(self.operations)
        methods = _methods(self.methods)
        object.__setattr__(self, "targets", targets)
        object.__setattr__(self, "schema_slices", slices)
        object.__setattr__(self, "operations", operations)
        object.__setattr__(self, "methods", methods)
        available_slices = {value.slice_digest for value in slices}
        for operation in operations:
            missing = operation.schema_digests() - available_slices
            if missing:
                raise ValueError(
                    f"operation {operation.operation_ref!r} uses unresolved schema slices {sorted(missing)!r}"
                )
        operation_refs = {value.operation_ref for value in operations}
        missing_operations = {value.operation_ref for value in methods} - operation_refs
        if missing_operations:
            raise ValueError(
                f"methods use unresolved operations {sorted(missing_operations)!r}"
            )
        expected = _manifest_digest(self.semantic_wire())
        if self.manifest_digest != expected:
            raise ValueError(f"manifest_digest mismatch; expected {expected}")

    @classmethod
    def create(
        cls,
        *,
        sdk_ref: str,
        semantic_version: str,
        targets: Iterable[SdkTargetContract],
        schema_slices: Iterable[TypeSchemaSlice],
        operations: Iterable[SdkOperationContract],
        methods: Iterable[SdkMethodContract],
    ) -> SdkContractManifest:
        sdk_value = _token(sdk_ref, "sdk_ref")
        version_value = _token(semantic_version, "semantic_version")
        target_values = _targets(targets)
        slice_values = _slices(schema_slices)
        operation_values = _operations(operations)
        method_values = _methods(methods)
        semantic = {
            "contract": SDK_CONTRACT,
            "sdk_ref": sdk_value,
            "semantic_version": version_value,
            "targets": [value.to_wire() for value in target_values],
            "schema_slices": [value.to_wire() for value in slice_values],
            "operations": [value.to_wire() for value in operation_values],
            "methods": [value.to_wire() for value in method_values],
        }
        return cls(
            sdk_value,
            version_value,
            target_values,
            slice_values,
            operation_values,
            method_values,
            _manifest_digest(semantic),
        )

    def semantic_wire(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "sdk_ref": self.sdk_ref,
            "semantic_version": self.semantic_version,
            "targets": [value.to_wire() for value in self.targets],
            "schema_slices": [value.to_wire() for value in self.schema_slices],
            "operations": [value.to_wire() for value in self.operations],
            "methods": [value.to_wire() for value in self.methods],
        }

    def to_wire(self) -> dict[str, object]:
        return {**self.semantic_wire(), "manifest_digest": self.manifest_digest}


__all__ = [
    "SDK_CONTRACT",
    "SdkContractManifest",
    "SdkMethodContract",
    "SdkOperationContract",
    "SdkTargetContract",
]
