"""Portable private-stage plan meaning; decoding never issues execution authority."""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from typing import Protocol

from .contracts import (
    ContentDigest,
    ContractViolation,
    SemanticConfigurationCoordinate,
    SemanticContractRef,
    SemanticImplementationCoordinate,
    canonical_json_bytes,
)

MAX_PLAN_BYTES = 65_536
MAX_STAGE_INPUTS = 64
MAX_TOKEN_BYTES = 192


class PrivateStageInputValidationPort(Protocol):
    """Code-owned shape for the original host's selected-input checks.

    Implementing this Protocol grants no authority. Code retains the exact
    original host receiver and all method entrances before using them.
    The host keeps approvals, source evidence, and predecessor state locally;
    Code supplies only its operation use and the selected semantic input.
    """

    def validate_private_stage_input_use(
        self, operation_use: object, semantic_input: object
    ) -> None: ...

    def check_private_stage_input_use_locked(
        self, operation_use: object, semantic_input: object
    ) -> None: ...

    def prepare_private_stage_read_input(
        self, operation_use: object, semantic_input: object
    ) -> None: ...

    def spend_private_stage_read_input_locked(
        self, operation_use: object, semantic_input: object, guard: object
    ) -> None: ...

    def abort_private_stage_read_input(self, operation_use: object) -> None: ...


def _token(value: object, field: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{field} must be an exact string")
    if (
        not value
        or len(value.encode("utf-8")) > MAX_TOKEN_BYTES
        or unicodedata.normalize("NFC", value) != value
        or any(character.isspace() for character in value)
    ):
        raise ContractViolation(f"{field} must be a bounded NFC token")
    return value


def _coordinate(value: object, expected: type[object], field: str) -> None:
    if type(value) is not expected:
        raise TypeError(f"{field} must be exact {expected.__name__}")
    value.__post_init__()  # type: ignore[attr-defined]


def _contract(value: object, field: str) -> None:
    _coordinate(value, SemanticContractRef, field)
    _token(value.key, f"{field}.key")  # type: ignore[attr-defined]
    _token(value.version, f"{field}.version")  # type: ignore[attr-defined]


@dataclass(frozen=True, slots=True)
class PrivateStageProfileIdentity:
    profile_ref: str
    version: str
    digest: ContentDigest

    def __post_init__(self) -> None:
        _token(self.profile_ref, "profile_ref")
        _token(self.version, "profile version")
        _coordinate(self.digest, ContentDigest, "profile digest")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "profile_ref": self.profile_ref,
            "version": self.version,
            "digest": self.digest.to_wire(),
        }


@dataclass(frozen=True, slots=True)
class PrivateStageRoleContract:
    role: str
    contract: SemanticContractRef

    def __post_init__(self) -> None:
        _token(self.role, "role")
        _contract(self.contract, "role contract")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {"role": self.role, "contract": self.contract.to_wire()}


@dataclass(frozen=True, slots=True)
class PrivateStageEntry:
    stage_key: str
    access: str
    provider_key: str
    profile: PrivateStageProfileIdentity
    implementation: SemanticImplementationCoordinate
    configuration: SemanticConfigurationCoordinate
    inputs: tuple[PrivateStageRoleContract, ...]
    terminal: PrivateStageRoleContract

    def __post_init__(self) -> None:
        _token(self.stage_key, "stage_key")
        if type(self.access) is not str or self.access not in (
            "private",
            "public_terminal",
        ):
            raise ContractViolation("stage access must be private or public_terminal")
        _token(self.provider_key, "provider_key")
        _coordinate(self.profile, PrivateStageProfileIdentity, "profile")
        _coordinate(
            self.implementation, SemanticImplementationCoordinate, "implementation"
        )
        _token(self.implementation.implementation_ref, "implementation_ref")
        _coordinate(
            self.configuration, SemanticConfigurationCoordinate, "configuration"
        )
        _token(self.configuration.configuration_ref, "configuration_ref")
        if type(self.inputs) is not tuple or len(self.inputs) > MAX_STAGE_INPUTS:
            raise ContractViolation("stage inputs must be a bounded exact tuple")
        for item in self.inputs:
            _coordinate(item, PrivateStageRoleContract, "stage input")
        roles = tuple(item.role for item in self.inputs)
        if roles != tuple(sorted(set(roles), key=str.encode)):
            raise ContractViolation("stage input roles must be unique and ordered")
        _coordinate(self.terminal, PrivateStageRoleContract, "stage terminal")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "stage_key": self.stage_key,
            "access": self.access,
            "provider_key": self.provider_key,
            "profile": self.profile.to_wire(),
            "implementation": self.implementation.to_wire(),
            "configuration": self.configuration.to_wire(),
            "inputs": [item.to_wire() for item in self.inputs],
            "terminal": self.terminal.to_wire(),
        }


@dataclass(frozen=True, slots=True)
class PrivateStageBarrier:
    kind: str
    after_stage: str
    before_stage: str
    candidate: PrivateStageRoleContract
    committed_product: PrivateStageRoleContract
    consumer_input_role: str

    def __post_init__(self) -> None:
        if type(self.kind) is not str or self.kind != "committed_product":
            raise ContractViolation("barrier must require a committed product")
        _token(self.after_stage, "after_stage")
        _token(self.before_stage, "before_stage")
        _coordinate(self.candidate, PrivateStageRoleContract, "candidate")
        _coordinate(
            self.committed_product, PrivateStageRoleContract, "committed_product"
        )
        _token(self.consumer_input_role, "consumer_input_role")
        if self.candidate.role == self.committed_product.role:
            raise ContractViolation("candidate and committed roles must differ")
        if self.candidate.contract == self.committed_product.contract:
            raise ContractViolation("candidate and committed contracts must differ")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "kind": self.kind,
            "after_stage": self.after_stage,
            "before_stage": self.before_stage,
            "candidate": self.candidate.to_wire(),
            "committed_product": self.committed_product.to_wire(),
            "consumer_input_role": self.consumer_input_role,
        }


@dataclass(frozen=True, slots=True)
class CodePrivateStagePlanV1:
    version: int
    public_profile: PrivateStageProfileIdentity
    stages: tuple[PrivateStageEntry, PrivateStageEntry]
    barrier: PrivateStageBarrier

    def __post_init__(self) -> None:
        if type(self.version) is not int or self.version != 1:
            raise ContractViolation("private-stage plan version must be exact integer 1")
        _coordinate(self.public_profile, PrivateStageProfileIdentity, "public_profile")
        if type(self.stages) is not tuple or len(self.stages) != 2:
            raise ContractViolation("private-stage plan requires exactly two stages")
        private, terminal = self.stages
        _coordinate(private, PrivateStageEntry, "private stage")
        _coordinate(terminal, PrivateStageEntry, "terminal stage")
        _coordinate(self.barrier, PrivateStageBarrier, "barrier")
        if private.access != "private" or terminal.access != "public_terminal":
            raise ContractViolation("private stage must precede public terminal")
        if private.stage_key == terminal.stage_key:
            raise ContractViolation("stage keys must differ")
        if private.provider_key == terminal.provider_key:
            raise ContractViolation("private and public providers must differ")
        if terminal.profile != self.public_profile:
            raise ContractViolation("terminal profile must be public profile")
        if (
            self.barrier.after_stage != private.stage_key
            or self.barrier.before_stage != terminal.stage_key
            or self.barrier.candidate != private.terminal
        ):
            raise ContractViolation("barrier must bind exact private completion")
        matches = tuple(
            item
            for item in terminal.inputs
            if item.role == self.barrier.consumer_input_role
        )
        if len(matches) != 1 or matches[0].contract != self.barrier.committed_product.contract:
            raise ContractViolation("committed product must match terminal input")
        if len(canonical_json_bytes(self._wire_unchecked())) > MAX_PLAN_BYTES:
            raise ContractViolation("private-stage plan exceeds canonical byte bound")

    def _wire_unchecked(self) -> dict[str, object]:
        return {
            "version": self.version,
            "public_profile": self.public_profile.to_wire(),
            "stages": [stage.to_wire() for stage in self.stages],
            "barrier": self.barrier.to_wire(),
        }

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return self._wire_unchecked()

    @property
    def digest(self) -> ContentDigest:
        return ContentDigest.of_bytes(encode_private_stage_plan(self))


def encode_private_stage_plan(value: CodePrivateStagePlanV1) -> bytes:
    if type(value) is not CodePrivateStagePlanV1:
        raise TypeError("exact CodePrivateStagePlanV1 required")
    return canonical_json_bytes(value.to_wire())


def _pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in items:
        if key in result:
            raise ContractViolation("duplicate private-stage plan field")
        result[key] = value
    return result


def _object(value: object, keys: tuple[str, ...]) -> dict[str, object]:
    if type(value) is not dict or set(value) != set(keys):
        raise ContractViolation("private-stage plan object fields differ")
    return value


def _digest(value: object) -> ContentDigest:
    return ContentDigest.of_wire(value)


def _version(value: object) -> int:
    if type(value) is not int:
        raise ContractViolation("private-stage plan version must be exact integer")
    return value


def _profile(value: object) -> PrivateStageProfileIdentity:
    row = _object(value, ("profile_ref", "version", "digest"))
    return PrivateStageProfileIdentity(
        _token(row["profile_ref"], "profile_ref"),
        _token(row["version"], "profile version"),
        _digest(row["digest"]),
    )


def _contract_from_wire(value: object) -> SemanticContractRef:
    row = _object(value, ("key", "version", "schema_digest"))
    return SemanticContractRef(
        _token(row["key"], "contract key"),
        _token(row["version"], "contract version"),
        _digest(row["schema_digest"]),
    )


def _binding(value: object) -> PrivateStageRoleContract:
    row = _object(value, ("role", "contract"))
    return PrivateStageRoleContract(
        _token(row["role"], "role"), _contract_from_wire(row["contract"])
    )


def _stage(value: object) -> PrivateStageEntry:
    row = _object(
        value,
        (
            "stage_key", "access", "provider_key", "profile", "implementation",
            "configuration", "inputs", "terminal",
        ),
    )
    implementation = _object(row["implementation"], ("implementation_ref", "closure_digest"))
    configuration = _object(row["configuration"], ("configuration_ref", "digest"))
    inputs = row["inputs"]
    if type(inputs) is not list or len(inputs) > MAX_STAGE_INPUTS:
        raise ContractViolation("bounded stage input array required")
    return PrivateStageEntry(
        _token(row["stage_key"], "stage_key"),
        _token(row["access"], "stage access"),
        _token(row["provider_key"], "provider_key"),
        _profile(row["profile"]),
        SemanticImplementationCoordinate(
            _token(implementation["implementation_ref"], "implementation_ref"),
            _digest(implementation["closure_digest"]),
        ),
        SemanticConfigurationCoordinate(
            _token(configuration["configuration_ref"], "configuration_ref"),
            _digest(configuration["digest"]),
        ),
        tuple(_binding(item) for item in inputs),
        _binding(row["terminal"]),
    )


def decode_private_stage_plan(body: bytes) -> CodePrivateStagePlanV1:
    if type(body) is not bytes or len(body) > MAX_PLAN_BYTES:
        raise ContractViolation("bounded exact private-stage plan bytes required")
    try:
        wire = _object(json.loads(body.decode("utf-8"), object_pairs_hook=_pairs), (
            "version", "public_profile", "stages", "barrier"
        ))
        stages = wire["stages"]
        if type(stages) is not list or len(stages) != 2:
            raise ContractViolation("exact two-stage array required")
        barrier = _object(wire["barrier"], (
            "kind", "after_stage", "before_stage", "candidate",
            "committed_product", "consumer_input_role"
        ))
        result = CodePrivateStagePlanV1(
            _version(wire["version"]),
            _profile(wire["public_profile"]),
            (_stage(stages[0]), _stage(stages[1])),
            PrivateStageBarrier(
                _token(barrier["kind"], "barrier kind"),
                _token(barrier["after_stage"], "after_stage"),
                _token(barrier["before_stage"], "before_stage"),
                _binding(barrier["candidate"]),
                _binding(barrier["committed_product"]),
                _token(barrier["consumer_input_role"], "consumer_input_role"),
            ),
        )
        if encode_private_stage_plan(result) != body:
            raise ContractViolation("private-stage plan bytes are not canonical")
        return result
    except (UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        raise ContractViolation("invalid private-stage plan body") from error


__all__ = [
    "CodePrivateStagePlanV1",
    "PrivateStageBarrier",
    "PrivateStageEntry",
    "PrivateStageInputValidationPort",
    "PrivateStageProfileIdentity",
    "PrivateStageRoleContract",
    "MAX_PLAN_BYTES",
    "decode_private_stage_plan",
    "encode_private_stage_plan",
]
