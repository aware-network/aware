"""Input-only retained-source projections. Portable agreement is not admission."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Protocol, cast

from .contracts import (
    ContentDigest,
    ContractViolation,
    ProviderExecutionBinding,
    SemanticPackageCoordinate,
    canonical_json_bytes,
)
from .dependency_inputs import (
    SemanticAuthoredDependency,
    SemanticDependencyPlanningInput,
    SemanticDependencyTarget,
)
from .materialization_planning import SemanticDependencyTargetConstraint
from .portable_semantic_package_authority import (
    CodePortableSemanticContract,
    _nullable_uuid,
    _package_name,
    _semantic_version,
)
from .semantic_candidates import _path

MAX_PROJECTION_BODY_BYTES = 8_388_608
MAX_PROJECTION_TEXT_BYTES = 4_096
MAX_PROJECTION_ITEMS = 16_384


class _Validated(Protocol):
    def __post_init__(self) -> None: ...


def _text(value: object) -> str:
    if type(value) is not str:
        raise ContractViolation("projection text must be exact str")
    try:
        raw = value.encode("utf-8")
    except UnicodeError as exc:
        raise ContractViolation("projection text must be UTF-8") from exc
    if (
        not 1 <= len(raw) <= MAX_PROJECTION_TEXT_BYTES
        or unicodedata.normalize("NFC", value) != value
        or any(c.isspace() for c in value)
    ):
        raise ContractViolation("projection text must be bounded NFC token")
    return value


def _strings(value: tuple[str, ...], *, nonempty: bool = False) -> None:
    _tuple(value)
    for item in value:
        _text(item)
    if (nonempty and not value) or tuple(sorted(set(value), key=str.encode)) != value:
        raise ContractViolation("projection tokens must be unique UTF-8 ordered")


def _tuple(value: object) -> None:
    if type(value) is not tuple or len(value) > MAX_PROJECTION_ITEMS:
        raise ContractViolation("projection tuple exceeds bounds or is not exact")


def _exact(value: object, expected: type) -> None:
    if type(value) is not expected:
        raise ContractViolation(f"exact {expected.__name__} required")
    cast(_Validated, value).__post_init__()


def _bound(wire: dict[str, object]) -> None:
    if len(canonical_json_bytes(wire)) > MAX_PROJECTION_BODY_BYTES:
        raise ContractViolation("projection body exceeds bound")


def _target_wire(value: SemanticDependencyTarget) -> dict[str, object]:
    _exact(value, SemanticDependencyTarget)
    _exact(value.package, SemanticPackageCoordinate)
    _strings(value.semantic_root_refs, nonempty=True)
    for item in value.package.to_wire().values():
        _text(item)
    return {
        "package": value.package.to_wire(),
        "semantic_root_refs": list(value.semantic_root_refs),
    }


def _dependency_wire(
    value: SemanticAuthoredDependency | CodeSemanticDeclarationTarget,
) -> dict[str, object]:
    _text(value.dependency_kind)
    _text(value.dependency_ref)
    _tuple(value.targets)
    _tuple(value.target_constraints)
    constraints = []
    for c in value.target_constraints:
        _exact(c, SemanticDependencyTargetConstraint)
        _text(c.constraint_kind)
        _text(c.constraint_value)
        constraints.append(c.to_wire())
    return {
        "dependency_kind": value.dependency_kind,
        "dependency_ref": value.dependency_ref,
        "targets": [_target_wire(t) for t in value.targets],
        "target_constraints": constraints,
    }


@dataclass(frozen=True, slots=True)
class CodeSemanticRegistryPackageInput:
    manifest_contract_kind: str
    manifest_filename: str
    semantic_provider_key: str
    semantic_package_family: str
    semantic_package_kind: str
    semantic_contract: CodePortableSemanticContract
    supported_languages: tuple[str, ...]
    code_package_surface: str | None
    fqn_prefix: str
    owned_semantic_root_refs: tuple[str, ...]
    profile_ref: str
    profile_version: str
    profile_digest: ContentDigest
    binding: ProviderExecutionBinding

    def __post_init__(self) -> None:
        for value in (
            self.manifest_contract_kind,
            self.semantic_provider_key,
            self.semantic_package_family,
            self.semantic_package_kind,
            self.fqn_prefix,
            self.profile_ref,
            self.profile_version,
        ):
            _text(value)
        _path(self.manifest_filename)
        if "/" in self.manifest_filename:
            raise ContractViolation("registry manifest filename must be basename")
        _exact(self.semantic_contract, CodePortableSemanticContract)
        for value in (
            self.semantic_contract.role,
            self.semantic_contract.name,
            self.semantic_contract.provider_key,
            self.semantic_contract.coordinate,
        ):
            _text(value)
        _strings(self.supported_languages, nonempty=True)
        _strings(self.owned_semantic_root_refs)
        if self.code_package_surface is not None:
            _text(self.code_package_surface)
        _exact(self.profile_digest, ContentDigest)
        _exact(self.binding, ProviderExecutionBinding)
        for value in (
            self.binding.provider_key,
            self.binding.implementation.implementation_ref,
            self.binding.configuration.configuration_ref,
        ):
            _text(value)
        if (
            not self.semantic_provider_key
            == self.semantic_contract.provider_key
            == self.binding.provider_key
        ):
            raise ContractViolation(
                "registry semantic and execution provider keys differ"
            )
        # This validates portable correspondence, not the missing nominal registry issuer.
        _bound(self.to_wire())

    def to_wire(self) -> dict[str, object]:
        return {
            "contract": "aware.code.semantic-registry-package-input.v1",
            "manifest_contract_kind": self.manifest_contract_kind,
            "manifest_filename": self.manifest_filename,
            "semantic_provider_key": self.semantic_provider_key,
            "semantic_package_family": self.semantic_package_family,
            "semantic_package_kind": self.semantic_package_kind,
            "semantic_contract": {
                "role": self.semantic_contract.role,
                "name": self.semantic_contract.name,
                "provider_key": self.semantic_contract.provider_key,
                "coordinate": self.semantic_contract.coordinate,
            },
            "supported_languages": list(self.supported_languages),
            "code_package_surface": self.code_package_surface,
            "fqn_prefix": self.fqn_prefix,
            "owned_semantic_root_refs": list(self.owned_semantic_root_refs),
            "profile_ref": self.profile_ref,
            "profile_version": self.profile_version,
            "profile_digest": self.profile_digest.to_wire(),
            "binding": self.binding.to_wire(),
        }


@dataclass(frozen=True, slots=True)
class CodeSemanticPackageContextInput:
    package: SemanticPackageCoordinate
    source_identity_digest: ContentDigest
    manifest_relative_path: str
    code_package_name: str
    semantic_version: str
    source_code_package_id: str | None
    config_id: str | None
    config_key: str | None

    def __post_init__(self) -> None:
        _exact(self.package, SemanticPackageCoordinate)
        for value in self.package.to_wire().values():
            _text(value)
        _exact(self.source_identity_digest, ContentDigest)
        _path(self.manifest_relative_path)
        _text(self.code_package_name)
        _text(self.semantic_version)
        _package_name(self.code_package_name, "code_package_name")
        _semantic_version(self.semantic_version, "semantic_version")
        _nullable_uuid(self.source_code_package_id, "source_code_package_id")
        _nullable_uuid(self.config_id, "config_id")
        for value in (self.source_code_package_id, self.config_id, self.config_key):
            if value is not None:
                _text(value)
        _bound(self.to_wire())

    def to_wire(self) -> dict[str, object]:
        return {
            "contract": "aware.code.semantic-package-context-input.v1",
            "package": self.package.to_wire(),
            "source_identity_digest": self.source_identity_digest.to_wire(),
            "manifest_relative_path": self.manifest_relative_path,
            "code_package_name": self.code_package_name,
            "semantic_version": self.semantic_version,
            "source_code_package_id": self.source_code_package_id,
            "config_id": self.config_id,
            "config_key": self.config_key,
        }


@dataclass(frozen=True, slots=True)
class CodeSemanticDeclarationTarget:
    dependency_kind: str
    dependency_ref: str
    targets: tuple[SemanticDependencyTarget, ...]
    target_constraints: tuple[SemanticDependencyTargetConstraint, ...] = ()

    def __post_init__(self) -> None:
        # Reuse existing declaration laws without relabeling inventory as authored intent.
        SemanticAuthoredDependency(
            self.dependency_kind,
            self.dependency_ref,
            self.targets,
            self.target_constraints,
        )
        _bound(_dependency_wire(self))

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return _dependency_wire(self)


@dataclass(frozen=True, slots=True)
class CodeSemanticDeclarationTargetInventory:
    package: SemanticPackageCoordinate
    source_identity_digest: ContentDigest
    entries: tuple[CodeSemanticDeclarationTarget, ...]

    def __post_init__(self) -> None:
        _exact(self.package, SemanticPackageCoordinate)
        for value in self.package.to_wire().values():
            _text(value)
        _exact(self.source_identity_digest, ContentDigest)
        _tuple(self.entries)
        keys = []
        for entry in self.entries:
            _exact(entry, CodeSemanticDeclarationTarget)
            keys.append((entry.dependency_kind.encode(), entry.dependency_ref.encode()))
        if keys != sorted(set(keys)):
            raise ContractViolation(
                "inventory selector keys must be unique UTF-8 ordered"
            )
        _bound(self.to_wire())

    def to_wire(self) -> dict[str, object]:
        return {
            "contract": "aware.code.semantic-declaration-target-inventory.v1",
            "package": self.package.to_wire(),
            "source_identity_digest": self.source_identity_digest.to_wire(),
            "entries": [e.to_wire() for e in self.entries],
        }


def planning_input_wire(value: SemanticDependencyPlanningInput) -> dict[str, object]:
    _exact(value, SemanticDependencyPlanningInput)
    _tuple(value.dependencies)
    for item in value.package.to_wire().values():
        _text(item)
    wire = {
        "contract": "aware.code.semantic-dependency-planning-input.v1",
        "package": value.package.to_wire(),
        "source_identity_digest": value.source_identity_digest.to_wire(),
        "dependencies": [_dependency_wire(d) for d in value.dependencies],
    }
    _bound(wire)
    return wire
