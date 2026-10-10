from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, cast

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
type WireObject = dict[str, JsonValue]

_TOKEN = re.compile(r"^[^\s]+$")
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


class ContractViolation(ValueError):
    pass


class _AdmittedValue(Protocol):
    def __post_init__(self) -> None: ...

    def to_wire(self) -> object: ...


def _exact[T](value: object, expected: type[T], path: str) -> T:
    if type(value) is not expected:
        raise TypeError(f"{path} must be exact {expected.__name__}")
    return value


def _instance[T: _AdmittedValue](value: object, expected: type[T], path: str) -> T:
    if type(value) is not expected:
        raise TypeError(f"{path} must be exact {expected.__name__}")
    # Fresh recursive admission rejects object.__new__, copied, and restamped graphs
    # before any nested foreign method or equality operation can execute.
    value.__post_init__()
    wire = getattr(value, "to_wire", None)
    if not callable(wire):
        raise TypeError(f"{path} has no module-owned wire method")
    return value


def _token(value: object, path: str) -> str:
    item = _exact(value, str, path)
    if not item or not _TOKEN.fullmatch(item):
        raise ContractViolation(f"{path} must be a nonempty token")
    return item


def _size(value: object, path: str) -> int:
    item = _exact(value, int, path)
    if item < 0:
        raise ContractViolation(f"{path} must be nonnegative")
    return item


def _strict_tuple[T: _AdmittedValue](
    value: object, item_type: type[T], path: str
) -> tuple[T, ...]:
    items = _exact(value, tuple, path)
    checked: list[T] = []
    for index, item in enumerate(items):
        checked.append(_instance(item, item_type, f"{path}[{index}]"))
    return tuple(checked)


def _token_tuple(
    value: object, path: str, *, nonempty: bool = False
) -> tuple[str, ...]:
    items = _exact(value, tuple, path)
    result = tuple(_token(item, f"{path}[{index}]") for index, item in enumerate(items))
    if nonempty and not result:
        raise ContractViolation(f"{path} must not be empty")
    if result != tuple(sorted(set(result), key=lambda item: item.encode("utf-8"))):
        raise ContractViolation(f"{path} must be unique and UTF-8 byte ordered")
    # Canonical token validation does not normalize valid strings. Preserve the
    # exact authored tuple so repeated validation cannot silently replace a
    # nested retained identity after its enclosing graph has been admitted.
    return items


def validate_json_value(value: object, path: str = "json") -> JsonValue:
    if value is None or type(value) in (str, bool, int):
        return cast(JsonValue, value)
    if type(value) is float:
        if not math.isfinite(value) or (value == 0.0 and math.copysign(1.0, value) < 0):
            raise ContractViolation(f"{path} contains a noncanonical float")
        return value
    if type(value) is list:
        return [
            validate_json_value(item, f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    if type(value) is dict:
        result: dict[str, JsonValue] = {}
        for key, item in value.items():
            name = _token(key, f"{path}.key")
            result[name] = validate_json_value(item, f"{path}.{name}")
        return result
    raise TypeError(f"{path} contains unsupported exact type {type(value).__name__}")


def canonical_json_text(value: object) -> str:
    admitted = validate_json_value(value)
    return json.dumps(
        admitted,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_json_bytes(value: object) -> bytes:
    return canonical_json_text(value).encode("utf-8")


@dataclass(frozen=True, slots=True, order=True)
class ContentDigest:
    value: str

    def __post_init__(self) -> None:
        value = _exact(self.value, str, "digest")
        if not _DIGEST.fullmatch(value):
            raise ContractViolation("digest must be sha256:<64 lowercase hex>")

    @classmethod
    def of_bytes(cls, value: bytes) -> ContentDigest:
        _exact(value, bytes, "digest input")
        return cls("sha256:" + hashlib.sha256(value).hexdigest())

    @classmethod
    def of_wire(cls, value: object, path: str = "digest") -> ContentDigest:
        return cls(_exact(value, str, path))

    def to_wire(self) -> str:
        self.__post_init__()
        return self.value


class TerminalStatus(StrEnum):
    CURRENT = "current"
    DELTA = "delta"
    BLOCKED = "blocked"
    CONFLICTED = "conflicted"
    FAILED = "failed"


@dataclass(frozen=True, slots=True, order=True)
class SemanticContractRef:
    key: str
    version: str
    schema_digest: ContentDigest

    def __post_init__(self) -> None:
        object.__setattr__(self, "key", _token(self.key, "contract.key"))
        object.__setattr__(self, "version", _token(self.version, "contract.version"))
        _instance(self.schema_digest, ContentDigest, "contract.schema_digest")

    def to_wire(self) -> WireObject:
        self.__post_init__()
        return {
            "key": self.key,
            "schema_digest": self.schema_digest.to_wire(),
            "version": self.version,
        }


@dataclass(frozen=True, slots=True, order=True)
class SemanticPackageCoordinate:
    package_ref: str
    package_kind: str
    manifest_digest: ContentDigest

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "package_ref", _token(self.package_ref, "package.package_ref")
        )
        object.__setattr__(
            self, "package_kind", _token(self.package_kind, "package.package_kind")
        )
        _instance(self.manifest_digest, ContentDigest, "package.manifest_digest")

    def to_wire(self) -> WireObject:
        self.__post_init__()
        return {
            "manifest_digest": self.manifest_digest.to_wire(),
            "package_kind": self.package_kind,
            "package_ref": self.package_ref,
        }


@dataclass(frozen=True, slots=True, order=True)
class SemanticValueCoordinate:
    role: str
    contract: SemanticContractRef
    value_ref: str
    digest: ContentDigest
    size_bytes: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "role", _token(self.role, "value.role"))
        _instance(self.contract, SemanticContractRef, "value.contract")
        object.__setattr__(self, "value_ref", _token(self.value_ref, "value.value_ref"))
        _instance(self.digest, ContentDigest, "value.digest")
        object.__setattr__(
            self, "size_bytes", _size(self.size_bytes, "value.size_bytes")
        )

    def to_wire(self) -> WireObject:
        self.__post_init__()
        return {
            "contract": self.contract.to_wire(),
            "digest": self.digest.to_wire(),
            "role": self.role,
            "size_bytes": self.size_bytes,
            "value_ref": self.value_ref,
        }


@dataclass(frozen=True, slots=True, order=True)
class SemanticImplementationCoordinate:
    implementation_ref: str
    closure_digest: ContentDigest

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "implementation_ref",
            _token(self.implementation_ref, "implementation.implementation_ref"),
        )
        _instance(self.closure_digest, ContentDigest, "implementation.closure_digest")

    def to_wire(self) -> WireObject:
        self.__post_init__()
        return {
            "closure_digest": self.closure_digest.to_wire(),
            "implementation_ref": self.implementation_ref,
        }


@dataclass(frozen=True, slots=True, order=True)
class SemanticConfigurationCoordinate:
    configuration_ref: str
    digest: ContentDigest

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "configuration_ref",
            _token(self.configuration_ref, "configuration.configuration_ref"),
        )
        _instance(self.digest, ContentDigest, "configuration.digest")

    def to_wire(self) -> WireObject:
        self.__post_init__()
        return {
            "configuration_ref": self.configuration_ref,
            "digest": self.digest.to_wire(),
        }


@dataclass(frozen=True, slots=True, order=True)
class SemanticDependencyCoordinate:
    package: SemanticPackageCoordinate
    result_contract: SemanticContractRef
    result_ref: str
    result_digest: ContentDigest

    def __post_init__(self) -> None:
        _instance(self.package, SemanticPackageCoordinate, "dependency.package")
        _instance(
            self.result_contract, SemanticContractRef, "dependency.result_contract"
        )
        object.__setattr__(
            self, "result_ref", _token(self.result_ref, "dependency.result_ref")
        )
        _instance(self.result_digest, ContentDigest, "dependency.result_digest")

    def to_wire(self) -> WireObject:
        self.__post_init__()
        return {
            "package": self.package.to_wire(),
            "result_contract": self.result_contract.to_wire(),
            "result_digest": self.result_digest.to_wire(),
            "result_ref": self.result_ref,
        }


@dataclass(frozen=True, slots=True, order=True)
class TypedEmptyCoordinate:
    contract: SemanticContractRef

    def __post_init__(self) -> None:
        _instance(self.contract, SemanticContractRef, "typed_empty.contract")

    def to_wire(self) -> WireObject:
        self.__post_init__()
        return {"contract": self.contract.to_wire(), "kind": "typed_empty"}


type PredecessorCoordinate = TypedEmptyCoordinate | SemanticValueCoordinate


def _predecessor(value: object, path: str) -> PredecessorCoordinate:
    if type(value) is TypedEmptyCoordinate:
        return _instance(value, TypedEmptyCoordinate, path)
    if type(value) is SemanticValueCoordinate:
        return _instance(value, SemanticValueCoordinate, path)
    raise TypeError(f"{path} must be TypedEmptyCoordinate or SemanticValueCoordinate")


def predecessor_wire(value: PredecessorCoordinate) -> WireObject:
    return _predecessor(value, "predecessor").to_wire()


@dataclass(frozen=True, slots=True, order=True)
class SemanticImpactCoordinate:
    namespace: str
    kind: str
    identifier: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "namespace", _token(self.namespace, "impact.namespace")
        )
        object.__setattr__(self, "kind", _token(self.kind, "impact.kind"))
        object.__setattr__(
            self, "identifier", _token(self.identifier, "impact.identifier")
        )

    def to_wire(self) -> WireObject:
        self.__post_init__()
        return {
            "identifier": self.identifier,
            "kind": self.kind,
            "namespace": self.namespace,
        }


@dataclass(frozen=True, slots=True, order=True)
class ConsumedRoleDeclaration:
    role: str
    accepted_contracts: tuple[SemanticContractRef, ...]
    required: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "role", _token(self.role, "consumed_role.role"))
        contracts = _strict_tuple(
            self.accepted_contracts,
            SemanticContractRef,
            "consumed_role.accepted_contracts",
        )
        if not contracts:
            raise ContractViolation(
                "consumed_role.accepted_contracts must not be empty"
            )
        ordered = tuple(
            sorted(
                set(contracts), key=lambda item: canonical_json_bytes(item.to_wire())
            )
        )
        if contracts != ordered:
            raise ContractViolation(
                "consumed_role.accepted_contracts must be unique and ordered"
            )
        _exact(self.required, bool, "consumed_role.required")

    def to_wire(self) -> WireObject:
        self.__post_init__()
        return {
            "accepted_contracts": [item.to_wire() for item in self.accepted_contracts],
            "required": self.required,
            "role": self.role,
        }


@dataclass(frozen=True, slots=True, order=True)
class ProducedRoleDeclaration:
    role: str
    contract: SemanticContractRef

    def __post_init__(self) -> None:
        object.__setattr__(self, "role", _token(self.role, "produced_role.role"))
        _instance(self.contract, SemanticContractRef, "produced_role.contract")

    def to_wire(self) -> WireObject:
        self.__post_init__()
        return {"contract": self.contract.to_wire(), "role": self.role}


@dataclass(frozen=True, slots=True)
class SemanticContractProviderDeclaration:
    provider_key: str
    provider_contract: SemanticContractRef
    package_kinds: tuple[str, ...]
    operation_kinds: tuple[str, ...]
    consumed_roles: tuple[ConsumedRoleDeclaration, ...]
    result_role: ProducedRoleDeclaration
    transition_contract: SemanticContractRef
    effect_role: ProducedRoleDeclaration
    effect_contract: SemanticContractRef
    output_roles: tuple[ProducedRoleDeclaration, ...] = ()
    allows_typed_empty: bool = False
    predecessor_required: bool = True
    terminal_statuses: tuple[str, ...] = tuple(
        sorted(item.value for item in TerminalStatus)
    )
    counter_keys: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "provider_key", _token(self.provider_key, "provider.provider_key")
        )
        _instance(
            self.provider_contract, SemanticContractRef, "provider.provider_contract"
        )
        object.__setattr__(
            self,
            "package_kinds",
            _token_tuple(self.package_kinds, "provider.package_kinds", nonempty=True),
        )
        object.__setattr__(
            self,
            "operation_kinds",
            _token_tuple(
                self.operation_kinds, "provider.operation_kinds", nonempty=True
            ),
        )
        consumed = _strict_tuple(
            self.consumed_roles, ConsumedRoleDeclaration, "provider.consumed_roles"
        )
        if tuple(item.role for item in consumed) != tuple(
            sorted(
                {item.role for item in consumed}, key=lambda item: item.encode("utf-8")
            )
        ):
            raise ContractViolation(
                "provider.consumed_roles must be role-unique and ordered"
            )
        _instance(self.result_role, ProducedRoleDeclaration, "provider.result_role")
        _instance(
            self.transition_contract,
            SemanticContractRef,
            "provider.transition_contract",
        )
        _instance(self.effect_role, ProducedRoleDeclaration, "provider.effect_role")
        _instance(self.effect_contract, SemanticContractRef, "provider.effect_contract")
        if self.effect_role.contract != self.effect_contract:
            raise ContractViolation("provider effect role and effect contract differ")
        outputs = _strict_tuple(
            self.output_roles, ProducedRoleDeclaration, "provider.output_roles"
        )
        if tuple(item.role for item in outputs) != tuple(
            sorted(
                {item.role for item in outputs}, key=lambda item: item.encode("utf-8")
            )
        ):
            raise ContractViolation(
                "provider.output_roles must be role-unique and ordered"
            )
        produced_roles = (
            self.result_role.role,
            self.effect_role.role,
            *(item.role for item in outputs),
        )
        if len(set(produced_roles)) != len(produced_roles):
            raise ContractViolation("provider produced roles must be distinct")
        _exact(self.allows_typed_empty, bool, "provider.allows_typed_empty")
        _exact(self.predecessor_required, bool, "provider.predecessor_required")
        statuses = _token_tuple(
            self.terminal_statuses, "provider.terminal_statuses", nonempty=True
        )
        if any(
            item not in {status.value for status in TerminalStatus} for item in statuses
        ):
            raise ContractViolation(
                "provider.terminal_statuses contains an unknown status"
            )
        object.__setattr__(self, "terminal_statuses", statuses)
        object.__setattr__(
            self,
            "counter_keys",
            _token_tuple(self.counter_keys, "provider.counter_keys"),
        )

    @property
    def digest(self) -> ContentDigest:
        self.__post_init__()
        return ContentDigest.of_bytes(canonical_json_bytes(self._wire_without_digest()))

    def _wire_without_digest(self) -> WireObject:
        return {
            "allows_typed_empty": self.allows_typed_empty,
            "consumed_roles": [item.to_wire() for item in self.consumed_roles],
            "counter_keys": list(self.counter_keys),
            "effect_contract": self.effect_contract.to_wire(),
            "effect_role": self.effect_role.to_wire(),
            "operation_kinds": list(self.operation_kinds),
            "output_roles": [item.to_wire() for item in self.output_roles],
            "package_kinds": list(self.package_kinds),
            "predecessor_required": self.predecessor_required,
            "provider_contract": self.provider_contract.to_wire(),
            "provider_key": self.provider_key,
            "result_role": self.result_role.to_wire(),
            "schema": "aware.code.semantic-provider-declaration.v1",
            "terminal_statuses": list(self.terminal_statuses),
            "transition_contract": self.transition_contract.to_wire(),
        }

    def to_wire(self) -> WireObject:
        self.__post_init__()
        return {**self._wire_without_digest(), "digest": self.digest.to_wire()}


@dataclass(frozen=True, slots=True, order=True)
class ProviderExecutionBinding:
    provider_key: str
    implementation: SemanticImplementationCoordinate
    configuration: SemanticConfigurationCoordinate

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "provider_key", _token(self.provider_key, "binding.provider_key")
        )
        _instance(
            self.implementation,
            SemanticImplementationCoordinate,
            "binding.implementation",
        )
        _instance(
            self.configuration, SemanticConfigurationCoordinate, "binding.configuration"
        )

    def to_wire(self) -> WireObject:
        self.__post_init__()
        return {
            "configuration": self.configuration.to_wire(),
            "implementation": self.implementation.to_wire(),
            "provider_key": self.provider_key,
        }


@dataclass(frozen=True, slots=True, order=True)
class SemanticBodyCodecBinding:
    contract: SemanticContractRef
    implementation: SemanticImplementationCoordinate

    def __post_init__(self) -> None:
        _instance(self.contract, SemanticContractRef, "codec_binding.contract")
        _instance(
            self.implementation,
            SemanticImplementationCoordinate,
            "codec_binding.implementation",
        )

    def to_wire(self) -> WireObject:
        self.__post_init__()
        return {
            "contract": self.contract.to_wire(),
            "implementation": self.implementation.to_wire(),
        }


@dataclass(frozen=True, slots=True)
class SemanticContractInvocation:
    invocation_ref: str
    idempotency_key: str
    profile_ref: str
    profile_digest: ContentDigest
    target_package: SemanticPackageCoordinate
    operation_kind: str
    inputs: tuple[SemanticValueCoordinate, ...]
    predecessor: PredecessorCoordinate
    dependencies: tuple[SemanticDependencyCoordinate, ...]
    body_codec_bindings: tuple[SemanticBodyCodecBinding, ...]
    provider_bindings: tuple[ProviderExecutionBinding, ...]
    requested_output_roles: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "invocation_ref",
            _token(self.invocation_ref, "invocation.invocation_ref"),
        )
        object.__setattr__(
            self,
            "idempotency_key",
            _token(self.idempotency_key, "invocation.idempotency_key"),
        )
        object.__setattr__(
            self, "profile_ref", _token(self.profile_ref, "invocation.profile_ref")
        )
        _instance(self.profile_digest, ContentDigest, "invocation.profile_digest")
        _instance(
            self.target_package, SemanticPackageCoordinate, "invocation.target_package"
        )
        object.__setattr__(
            self,
            "operation_kind",
            _token(self.operation_kind, "invocation.operation_kind"),
        )
        inputs = _strict_tuple(
            self.inputs, SemanticValueCoordinate, "invocation.inputs"
        )
        if tuple(item.role for item in inputs) != tuple(
            sorted(
                {item.role for item in inputs}, key=lambda item: item.encode("utf-8")
            )
        ):
            raise ContractViolation("invocation.inputs must be role-unique and ordered")
        _predecessor(self.predecessor, "invocation.predecessor")
        dependencies = _strict_tuple(
            self.dependencies, SemanticDependencyCoordinate, "invocation.dependencies"
        )
        dependency_order = tuple(
            sorted(
                set(dependencies), key=lambda item: canonical_json_bytes(item.to_wire())
            )
        )
        if dependencies != dependency_order:
            raise ContractViolation(
                "invocation.dependencies must be unique and ordered"
            )
        codec_bindings = _strict_tuple(
            self.body_codec_bindings,
            SemanticBodyCodecBinding,
            "invocation.body_codec_bindings",
        )
        codec_order = tuple(
            sorted(
                set(codec_bindings),
                key=lambda item: canonical_json_bytes(item.contract.to_wire()),
            )
        )
        if codec_bindings != codec_order or len(
            {item.contract for item in codec_bindings}
        ) != len(codec_bindings):
            raise ContractViolation(
                "invocation.body_codec_bindings must be contract-unique and ordered"
            )
        bindings = _strict_tuple(
            self.provider_bindings,
            ProviderExecutionBinding,
            "invocation.provider_bindings",
        )
        if tuple(item.provider_key for item in bindings) != tuple(
            sorted(
                {item.provider_key for item in bindings},
                key=lambda item: item.encode("utf-8"),
            )
        ):
            raise ContractViolation(
                "invocation.provider_bindings must be provider-unique and ordered"
            )
        requested_output_roles = _token_tuple(
            self.requested_output_roles, "invocation.requested_output_roles"
        )
        # Validation/serialization must not replace an already canonical tuple:
        # original selected-execution snapshots retain its exact object identity.
        if requested_output_roles != self.requested_output_roles:
            object.__setattr__(self, "requested_output_roles", requested_output_roles)

    @property
    def digest(self) -> ContentDigest:
        self.__post_init__()
        return ContentDigest.of_bytes(canonical_json_bytes(self._wire_without_digest()))

    def _wire_without_digest(self) -> WireObject:
        return {
            "body_codec_bindings": [
                item.to_wire() for item in self.body_codec_bindings
            ],
            "dependencies": [item.to_wire() for item in self.dependencies],
            "idempotency_key": self.idempotency_key,
            "inputs": [item.to_wire() for item in self.inputs],
            "invocation_ref": self.invocation_ref,
            "operation_kind": self.operation_kind,
            "predecessor": predecessor_wire(self.predecessor),
            "profile_digest": self.profile_digest.to_wire(),
            "profile_ref": self.profile_ref,
            "provider_bindings": [item.to_wire() for item in self.provider_bindings],
            "requested_output_roles": list(self.requested_output_roles),
            "schema": "aware.code.semantic-contract-invocation.v1",
            "target_package": self.target_package.to_wire(),
        }

    def to_wire(self) -> WireObject:
        self.__post_init__()
        return {**self._wire_without_digest(), "digest": self.digest.to_wire()}


@dataclass(frozen=True, slots=True)
class SemanticTransitionEnvelope:
    provider_key: str
    result_contract: SemanticContractRef
    transition_contract: SemanticContractRef
    predecessor: PredecessorCoordinate
    result: SemanticValueCoordinate
    transition_body: SemanticValueCoordinate
    impacts: tuple[SemanticImpactCoordinate, ...]
    input_closure_digest: ContentDigest

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "provider_key", _token(self.provider_key, "transition.provider_key")
        )
        _instance(
            self.result_contract, SemanticContractRef, "transition.result_contract"
        )
        _instance(
            self.transition_contract,
            SemanticContractRef,
            "transition.transition_contract",
        )
        _predecessor(self.predecessor, "transition.predecessor")
        _instance(self.result, SemanticValueCoordinate, "transition.result")
        _instance(
            self.transition_body, SemanticValueCoordinate, "transition.transition_body"
        )
        if self.result.contract != self.result_contract:
            raise ContractViolation("transition result contract differs")
        if self.transition_body.contract != self.transition_contract:
            raise ContractViolation("transition body contract differs")
        impacts = _strict_tuple(
            self.impacts, SemanticImpactCoordinate, "transition.impacts"
        )
        ordered = tuple(
            sorted(set(impacts), key=lambda item: canonical_json_bytes(item.to_wire()))
        )
        if not impacts or impacts != ordered:
            raise ContractViolation(
                "transition impacts must be nonempty, unique and ordered"
            )
        _instance(
            self.input_closure_digest, ContentDigest, "transition.input_closure_digest"
        )

    @property
    def digest(self) -> ContentDigest:
        self.__post_init__()
        return ContentDigest.of_bytes(canonical_json_bytes(self._wire_without_digest()))

    def _wire_without_digest(self) -> WireObject:
        return {
            "impacts": [item.to_wire() for item in self.impacts],
            "input_closure_digest": self.input_closure_digest.to_wire(),
            "predecessor": predecessor_wire(self.predecessor),
            "provider_key": self.provider_key,
            "result": self.result.to_wire(),
            "result_contract": self.result_contract.to_wire(),
            "schema": "aware.code.semantic-transition-envelope.v1",
            "transition_body": self.transition_body.to_wire(),
            "transition_contract": self.transition_contract.to_wire(),
        }

    def to_wire(self) -> WireObject:
        self.__post_init__()
        return {**self._wire_without_digest(), "digest": self.digest.to_wire()}


@dataclass(frozen=True, slots=True)
class PreparedSemanticEffectEnvelope:
    provider_key: str
    effect_contract: SemanticContractRef
    transition_digest: ContentDigest
    base_state: PredecessorCoordinate
    candidate_state: SemanticValueCoordinate
    effect_body: SemanticValueCoordinate
    renderer_inputs: tuple[SemanticValueCoordinate, ...]
    impacts: tuple[SemanticImpactCoordinate, ...]
    work_counters: tuple[tuple[str, int], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "provider_key", _token(self.provider_key, "effect.provider_key")
        )
        _instance(self.effect_contract, SemanticContractRef, "effect.effect_contract")
        _instance(self.transition_digest, ContentDigest, "effect.transition_digest")
        _predecessor(self.base_state, "effect.base_state")
        _instance(
            self.candidate_state, SemanticValueCoordinate, "effect.candidate_state"
        )
        _instance(self.effect_body, SemanticValueCoordinate, "effect.effect_body")
        if self.effect_body.contract != self.effect_contract:
            raise ContractViolation("effect body contract differs")
        renderer_inputs = _strict_tuple(
            self.renderer_inputs, SemanticValueCoordinate, "effect.renderer_inputs"
        )
        renderer_order = tuple(
            sorted(
                set(renderer_inputs),
                key=lambda item: canonical_json_bytes(item.to_wire()),
            )
        )
        if renderer_inputs != renderer_order:
            raise ContractViolation("effect renderer_inputs must be unique and ordered")
        impacts = _strict_tuple(
            self.impacts, SemanticImpactCoordinate, "effect.impacts"
        )
        impact_order = tuple(
            sorted(set(impacts), key=lambda item: canonical_json_bytes(item.to_wire()))
        )
        if not impacts or impacts != impact_order:
            raise ContractViolation(
                "effect impacts must be nonempty, unique and ordered"
            )
        counters = _exact(self.work_counters, tuple, "effect.work_counters")
        checked: list[tuple[str, int]] = []
        for index, pair in enumerate(counters):
            pair_value = _exact(pair, tuple, f"effect.work_counters[{index}]")
            if len(pair_value) != 2:
                raise ContractViolation("work counter pair must contain key and value")
            checked.append(
                (
                    _token(pair_value[0], "work counter key"),
                    _size(pair_value[1], "work counter value"),
                )
            )
        if tuple(checked) != tuple(
            sorted(set(checked), key=lambda item: item[0].encode("utf-8"))
        ):
            raise ContractViolation("work counters must be key-unique and ordered")

    @property
    def digest(self) -> ContentDigest:
        self.__post_init__()
        return ContentDigest.of_bytes(canonical_json_bytes(self._wire_without_digest()))

    def _wire_without_digest(self) -> WireObject:
        return {
            "base_state": predecessor_wire(self.base_state),
            "candidate_state": self.candidate_state.to_wire(),
            "effect_body": self.effect_body.to_wire(),
            "effect_contract": self.effect_contract.to_wire(),
            "impacts": [item.to_wire() for item in self.impacts],
            "provider_key": self.provider_key,
            "renderer_inputs": [item.to_wire() for item in self.renderer_inputs],
            "schema": "aware.code.prepared-semantic-effect-envelope.v1",
            "transition_digest": self.transition_digest.to_wire(),
            "work_counters": [[key, value] for key, value in self.work_counters],
        }

    def to_wire(self) -> WireObject:
        self.__post_init__()
        return {**self._wire_without_digest(), "digest": self.digest.to_wire()}


@dataclass(frozen=True, slots=True)
class SemanticOutputEnvelope:
    provider_key: str
    output: SemanticValueCoordinate
    prepared_effect_digest: ContentDigest

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "provider_key", _token(self.provider_key, "output.provider_key")
        )
        _instance(self.output, SemanticValueCoordinate, "output.output")
        _instance(
            self.prepared_effect_digest, ContentDigest, "output.prepared_effect_digest"
        )

    @property
    def digest(self) -> ContentDigest:
        self.__post_init__()
        return ContentDigest.of_bytes(canonical_json_bytes(self._wire_without_digest()))

    def _wire_without_digest(self) -> WireObject:
        return {
            "output": self.output.to_wire(),
            "prepared_effect_digest": self.prepared_effect_digest.to_wire(),
            "provider_key": self.provider_key,
            "schema": "aware.code.semantic-output-envelope.v1",
        }

    def to_wire(self) -> WireObject:
        self.__post_init__()
        return {**self._wire_without_digest(), "digest": self.digest.to_wire()}


@dataclass(frozen=True, slots=True)
class SemanticContractResult:
    status: TerminalStatus
    invocation_digest: ContentDigest
    current_result: SemanticValueCoordinate | None = None
    transition: SemanticTransitionEnvelope | None = None
    effect: PreparedSemanticEffectEnvelope | None = None
    outputs: tuple[SemanticOutputEnvelope, ...] = ()
    reason: str | None = None

    def __post_init__(self) -> None:
        if type(self.status) is not TerminalStatus:
            raise TypeError("result.status must be exact TerminalStatus")
        _instance(self.invocation_digest, ContentDigest, "result.invocation_digest")
        if self.current_result is not None:
            _instance(
                self.current_result, SemanticValueCoordinate, "result.current_result"
            )
        if self.transition is not None:
            _instance(self.transition, SemanticTransitionEnvelope, "result.transition")
        if self.effect is not None:
            _instance(self.effect, PreparedSemanticEffectEnvelope, "result.effect")
        outputs = _strict_tuple(self.outputs, SemanticOutputEnvelope, "result.outputs")
        output_order = tuple(
            sorted(set(outputs), key=lambda item: canonical_json_bytes(item.to_wire()))
        )
        if outputs != output_order:
            raise ContractViolation("result.outputs must be unique and ordered")
        if self.reason is not None:
            object.__setattr__(self, "reason", _token(self.reason, "result.reason"))
        if self.status is TerminalStatus.CURRENT:
            if (
                self.current_result is None
                or self.transition is not None
                or self.effect is None
                or outputs
                or self.reason is not None
            ):
                raise ContractViolation(
                    "current result requires current_result/effect only"
                )
            if self.effect.candidate_state != self.current_result:
                raise ContractViolation(
                    "current effect candidate differs from current result"
                )
        elif self.status is TerminalStatus.DELTA:
            if (
                self.current_result is not None
                or self.transition is None
                or self.effect is None
                or self.reason is not None
            ):
                raise ContractViolation(
                    "delta result requires transition/effect and no reason"
                )
            if self.effect.transition_digest != self.transition.digest:
                raise ContractViolation("effect does not bind transition digest")
            if self.effect.candidate_state != self.transition.result:
                raise ContractViolation(
                    "effect candidate state differs from transition result"
                )
            if predecessor_wire(self.effect.base_state) != predecessor_wire(
                self.transition.predecessor
            ):
                raise ContractViolation(
                    "effect base state differs from transition predecessor"
                )
            if self.effect.provider_key != self.transition.provider_key:
                raise ContractViolation(
                    "effect provider differs from transition provider"
                )
            if self.effect.impacts != self.transition.impacts:
                raise ContractViolation("effect impacts differ from transition impacts")
            if any(
                item.prepared_effect_digest != self.effect.digest for item in outputs
            ):
                raise ContractViolation("output does not bind prepared effect")
        else:
            if (
                self.current_result is not None
                or self.transition is not None
                or self.effect is not None
                or outputs
                or self.reason is None
            ):
                raise ContractViolation(
                    "non-success result requires reason and no publishable values"
                )

    @property
    def digest(self) -> ContentDigest:
        self.__post_init__()
        return ContentDigest.of_bytes(canonical_json_bytes(self._wire_without_digest()))

    def _wire_without_digest(self) -> WireObject:
        return {
            "current_result": self.current_result.to_wire()
            if self.current_result
            else None,
            "effect": self.effect.to_wire() if self.effect else None,
            "invocation_digest": self.invocation_digest.to_wire(),
            "outputs": [item.to_wire() for item in self.outputs],
            "reason": self.reason,
            "schema": "aware.code.semantic-contract-result.v1",
            "status": self.status.value,
            "transition": self.transition.to_wire() if self.transition else None,
        }

    def to_wire(self) -> WireObject:
        self.__post_init__()
        return {**self._wire_without_digest(), "digest": self.digest.to_wire()}


__all__ = [
    "ConsumedRoleDeclaration",
    "ContentDigest",
    "ContractViolation",
    "JsonValue",
    "PreparedSemanticEffectEnvelope",
    "ProducedRoleDeclaration",
    "ProviderExecutionBinding",
    "SemanticBodyCodecBinding",
    "SemanticConfigurationCoordinate",
    "SemanticContractInvocation",
    "SemanticContractProviderDeclaration",
    "SemanticContractRef",
    "SemanticContractResult",
    "SemanticDependencyCoordinate",
    "SemanticImpactCoordinate",
    "SemanticImplementationCoordinate",
    "SemanticOutputEnvelope",
    "SemanticPackageCoordinate",
    "SemanticTransitionEnvelope",
    "SemanticValueCoordinate",
    "TerminalStatus",
    "TypedEmptyCoordinate",
    "WireObject",
    "canonical_json_bytes",
    "canonical_json_text",
    "predecessor_wire",
    "validate_json_value",
]
