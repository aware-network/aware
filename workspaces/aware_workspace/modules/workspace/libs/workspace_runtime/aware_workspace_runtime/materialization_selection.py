"""Workspace-owned portable materialization selection and intent admission."""

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from typing import Protocol

from aware_code_semantic_contract_runtime import (
    CodeSemanticMaterializationIntent,
    ContentDigest,
    ContractViolation,
    SemanticConfigurationCoordinate,
)

WORKSPACE_MATERIALIZATION_ROOT_SELECTOR = (
    "aware.workspace.materialization-root-selector.v1"
)
WORKSPACE_MATERIALIZATION_SELECTION_PROPOSAL = (
    "aware.workspace.materialization-selection-proposal.v1"
)
WORKSPACE_SEMANTIC_MATERIALIZATION_PARTICIPATION_POLICY = (
    "aware.workspace.semantic-materialization-participation-policy.v1"
)
WORKSPACE_ADMITTED_PACKAGE_INTENT = "aware.workspace.admitted-package-intent.v1"
WORKSPACE_MATERIALIZATION_ROOT_INTENT_ASSOCIATION = (
    "aware.workspace.materialization-root-intent-association.v1"
)
WORKSPACE_MATERIALIZATION_SELECTION_RESOLUTION = (
    "aware.workspace.materialization-selection-resolution.v1"
)

WORKSPACE_MATERIALIZATION_SELECTOR_KINDS = (
    "module",
    "package",
    "repository",
    "workspace",
)
_INTERNAL_JSON_ENCODER = json.JSONEncoder(
    ensure_ascii=False,
    allow_nan=False,
    sort_keys=True,
    separators=(",", ":"),
)


class _WireValue(Protocol):
    def __post_init__(self) -> None: ...

    def to_wire(self) -> object: ...


def _digest(contract: str, payload: dict[str, object]) -> ContentDigest:
    value = (
        "sha256:"
        + hashlib.sha256(
            _internal_canonical_bytes({"contract": contract, **payload})
        ).hexdigest()
    )
    result = object.__new__(ContentDigest)
    object.__setattr__(result, "value", value)
    return result


def _internal_canonical_bytes(value: object) -> bytes:
    """Encode an already recursively admitted internal body without a second walk."""
    return _INTERNAL_JSON_ENCODER.encode(value).encode("utf-8")


def _frozen_value[T](expected: type[T], **fields: object) -> T:
    result = object.__new__(expected)
    for name, value in fields.items():
        object.__setattr__(result, name, value)
    return result


def _token(value: object, path: str) -> str:
    if type(value) is not str or not value or any(char.isspace() for char in value):
        raise TypeError(f"{path} must be nonempty token text")
    return value


def _nonnegative(value: object, path: str) -> int:
    if type(value) is not int or value < 0:
        raise TypeError(f"{path} must be exact nonnegative integer")
    return value


def _content_digest(value: object, path: str) -> ContentDigest:
    if type(value) is not ContentDigest:
        raise TypeError(f"{path} must be exact ContentDigest")
    value.__post_init__()
    return value


def _preflight_exact[T](value: object, expected: type[T], path: str) -> T:
    if type(value) is not expected:
        raise TypeError(f"{path} must be exact {expected.__name__}")
    return value


def _preflight_tuple[T](value: object, expected: type[T], path: str) -> tuple[T, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{path} must be exact tuple")
    result: list[T] = []
    for index, item in enumerate(value):
        result.append(_preflight_exact(item, expected, f"{path}[{index}]"))
    return tuple(result)


def _token_tuple(
    value: object, path: str, *, nonempty: bool = False
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{path} must be exact tuple")
    result = tuple(_token(item, f"{path}[{index}]") for index, item in enumerate(value))
    if nonempty and not result:
        raise ContractViolation(f"{path} must not be empty")
    if result != tuple(sorted(set(result), key=lambda item: item.encode())):
        raise ContractViolation(f"{path} must be unique and UTF-8 byte ordered")
    return result


def _exact_tuple[T](value: object, item_type: type[T], path: str) -> tuple[T, ...]:
    result = _preflight_tuple(value, item_type, path)
    for index, item in enumerate(result):
        post_init = getattr(item, "__post_init__", None)
        if not callable(post_init):
            raise TypeError(f"{path}[{index}] has no module-owned validator")
        post_init()
    return result


def _ordered_tuple[T: _WireValue](
    value: object, item_type: type[T], path: str
) -> tuple[T, ...]:
    result = _exact_tuple(value, item_type, path)
    wires = tuple(_internal_canonical_bytes(item.to_wire()) for item in result)
    if wires != tuple(sorted(set(wires))):
        raise ContractViolation(f"{path} must be unique and canonical-byte ordered")
    return result


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializationRootSelector:
    selector_kind: str
    selector_ref: str
    selector_digest: ContentDigest

    @classmethod
    def create(
        cls, *, selector_kind: str, selector_ref: str
    ) -> WorkspaceMaterializationRootSelector:
        payload = _selector_payload(
            selector_kind=selector_kind, selector_ref=selector_ref
        )
        return _frozen_value(
            cls,
            selector_kind=selector_kind,
            selector_ref=selector_ref,
            selector_digest=_digest(WORKSPACE_MATERIALIZATION_ROOT_SELECTOR, payload),
        )

    def __post_init__(self) -> None:
        payload = _selector_payload(
            selector_kind=self.selector_kind, selector_ref=self.selector_ref
        )
        if _content_digest(self.selector_digest, "selector.selector_digest") != _digest(
            WORKSPACE_MATERIALIZATION_ROOT_SELECTOR, payload
        ):
            raise ContractViolation("selector digest mismatched")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_MATERIALIZATION_ROOT_SELECTOR,
            **_selector_payload(
                selector_kind=self.selector_kind, selector_ref=self.selector_ref
            ),
            "selector_digest": self.selector_digest.to_wire(),
        }


def _selector_payload(
    *, selector_kind: object, selector_ref: object
) -> dict[str, object]:
    kind = _token(selector_kind, "selector.selector_kind")
    if kind not in WORKSPACE_MATERIALIZATION_SELECTOR_KINDS:
        raise ContractViolation("selector kind unsupported")
    return {
        "selector_kind": kind,
        "selector_ref": _token(selector_ref, "selector.selector_ref"),
    }


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializationSelectionProposal:
    selectors: tuple[WorkspaceMaterializationRootSelector, ...]
    proposal_digest: ContentDigest

    @classmethod
    def create(
        cls, *, selectors: tuple[WorkspaceMaterializationRootSelector, ...]
    ) -> WorkspaceMaterializationSelectionProposal:
        _preflight_tuple(
            selectors,
            WorkspaceMaterializationRootSelector,
            "proposal.selectors",
        )
        payload = _proposal_payload(selectors=selectors)
        return _frozen_value(
            cls,
            selectors=selectors,
            proposal_digest=_digest(
                WORKSPACE_MATERIALIZATION_SELECTION_PROPOSAL, payload
            ),
        )

    def __post_init__(self) -> None:
        payload = _proposal_payload(selectors=self.selectors)
        if _content_digest(self.proposal_digest, "proposal.proposal_digest") != _digest(
            WORKSPACE_MATERIALIZATION_SELECTION_PROPOSAL, payload
        ):
            raise ContractViolation("selection proposal digest mismatched")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_MATERIALIZATION_SELECTION_PROPOSAL,
            **_proposal_payload(selectors=self.selectors),
            "proposal_digest": self.proposal_digest.to_wire(),
        }


def _proposal_payload(*, selectors: object) -> dict[str, object]:
    values = _ordered_tuple(
        selectors, WorkspaceMaterializationRootSelector, "proposal.selectors"
    )
    if not values:
        raise ContractViolation("proposal selectors must not be empty")
    return {"selectors": [item.to_wire() for item in values]}


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationParticipationPolicy:
    policy_ref: str
    policy_revision: int
    package_ref: str
    allowed_operation_kinds: tuple[str, ...]
    allowed_semantic_root_refs: tuple[str, ...]
    allowed_terminal_output_roles: tuple[str, ...]
    allow_unconfigured: bool
    allowed_semantic_configuration_coordinates: tuple[
        SemanticConfigurationCoordinate, ...
    ]
    policy_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        policy_ref: str,
        policy_revision: int,
        package_ref: str,
        allowed_operation_kinds: tuple[str, ...],
        allowed_semantic_root_refs: tuple[str, ...],
        allowed_terminal_output_roles: tuple[str, ...],
        allow_unconfigured: bool,
        allowed_semantic_configuration_coordinates: tuple[
            SemanticConfigurationCoordinate, ...
        ],
    ) -> WorkspaceSemanticMaterializationParticipationPolicy:
        _preflight_tuple(
            allowed_semantic_configuration_coordinates,
            SemanticConfigurationCoordinate,
            "policy.allowed_semantic_configuration_coordinates",
        )
        payload = _policy_payload(
            policy_ref=policy_ref,
            policy_revision=policy_revision,
            package_ref=package_ref,
            allowed_operation_kinds=allowed_operation_kinds,
            allowed_semantic_root_refs=allowed_semantic_root_refs,
            allowed_terminal_output_roles=allowed_terminal_output_roles,
            allow_unconfigured=allow_unconfigured,
            allowed_semantic_configuration_coordinates=(
                allowed_semantic_configuration_coordinates
            ),
        )
        return _frozen_value(
            cls,
            policy_ref=policy_ref,
            policy_revision=policy_revision,
            package_ref=package_ref,
            allowed_operation_kinds=allowed_operation_kinds,
            allowed_semantic_root_refs=allowed_semantic_root_refs,
            allowed_terminal_output_roles=allowed_terminal_output_roles,
            allow_unconfigured=allow_unconfigured,
            allowed_semantic_configuration_coordinates=(
                allowed_semantic_configuration_coordinates
            ),
            policy_digest=_digest(
                WORKSPACE_SEMANTIC_MATERIALIZATION_PARTICIPATION_POLICY, payload
            ),
        )

    def __post_init__(self) -> None:
        payload = _policy_payload(
            policy_ref=self.policy_ref,
            policy_revision=self.policy_revision,
            package_ref=self.package_ref,
            allowed_operation_kinds=self.allowed_operation_kinds,
            allowed_semantic_root_refs=self.allowed_semantic_root_refs,
            allowed_terminal_output_roles=self.allowed_terminal_output_roles,
            allow_unconfigured=self.allow_unconfigured,
            allowed_semantic_configuration_coordinates=(
                self.allowed_semantic_configuration_coordinates
            ),
        )
        if _content_digest(self.policy_digest, "policy.policy_digest") != _digest(
            WORKSPACE_SEMANTIC_MATERIALIZATION_PARTICIPATION_POLICY, payload
        ):
            raise ContractViolation("participation policy digest mismatched")

    def admits(self, intent: CodeSemanticMaterializationIntent) -> bool:
        if type(intent) is not CodeSemanticMaterializationIntent:
            return False
        intent.__post_init__()
        configuration = intent.semantic_configuration_coordinate
        configuration_admitted = (
            self.allow_unconfigured
            if configuration is None
            else configuration in self.allowed_semantic_configuration_coordinates
        )
        return (
            intent.operation_kind in self.allowed_operation_kinds
            and set(intent.requested_semantic_root_refs)
            <= set(self.allowed_semantic_root_refs)
            and set(intent.requested_terminal_output_roles)
            <= set(self.allowed_terminal_output_roles)
            and configuration_admitted
        )

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_PARTICIPATION_POLICY,
            **_policy_payload(
                policy_ref=self.policy_ref,
                policy_revision=self.policy_revision,
                package_ref=self.package_ref,
                allowed_operation_kinds=self.allowed_operation_kinds,
                allowed_semantic_root_refs=self.allowed_semantic_root_refs,
                allowed_terminal_output_roles=self.allowed_terminal_output_roles,
                allow_unconfigured=self.allow_unconfigured,
                allowed_semantic_configuration_coordinates=(
                    self.allowed_semantic_configuration_coordinates
                ),
            ),
            "policy_digest": self.policy_digest.to_wire(),
        }


def _policy_payload(
    *,
    policy_ref: object,
    policy_revision: object,
    package_ref: object,
    allowed_operation_kinds: object,
    allowed_semantic_root_refs: object,
    allowed_terminal_output_roles: object,
    allow_unconfigured: object,
    allowed_semantic_configuration_coordinates: object,
) -> dict[str, object]:
    if type(allow_unconfigured) is not bool:
        raise TypeError("policy.allow_unconfigured must be exact bool")
    configurations = _ordered_tuple(
        allowed_semantic_configuration_coordinates,
        SemanticConfigurationCoordinate,
        "policy.allowed_semantic_configuration_coordinates",
    )
    return {
        "allow_unconfigured": allow_unconfigured,
        "allowed_operation_kinds": list(
            _token_tuple(
                allowed_operation_kinds,
                "policy.allowed_operation_kinds",
                nonempty=True,
            )
        ),
        "allowed_semantic_configuration_coordinates": [
            item.to_wire() for item in configurations
        ],
        "allowed_semantic_root_refs": list(
            _token_tuple(
                allowed_semantic_root_refs,
                "policy.allowed_semantic_root_refs",
                nonempty=True,
            )
        ),
        "allowed_terminal_output_roles": list(
            _token_tuple(
                allowed_terminal_output_roles,
                "policy.allowed_terminal_output_roles",
                nonempty=True,
            )
        ),
        "package_ref": _token(package_ref, "policy.package_ref"),
        "policy_ref": _token(policy_ref, "policy.policy_ref"),
        "policy_revision": _nonnegative(policy_revision, "policy.policy_revision"),
    }


@dataclass(frozen=True, slots=True)
class WorkspaceAdmittedPackageIntent:
    package_ref: str
    code_intent_body: CodeSemanticMaterializationIntent
    code_intent_digest: ContentDigest
    catalog_root_digest: ContentDigest
    catalog_generation: int
    participation_policy_body: WorkspaceSemanticMaterializationParticipationPolicy
    participation_policy_digest: ContentDigest
    admission_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        package_ref: str,
        code_intent_body: CodeSemanticMaterializationIntent,
        catalog_root_digest: ContentDigest,
        catalog_generation: int,
        participation_policy_body: WorkspaceSemanticMaterializationParticipationPolicy,
    ) -> WorkspaceAdmittedPackageIntent:
        _preflight_exact(
            code_intent_body,
            CodeSemanticMaterializationIntent,
            "admission.code_intent_body",
        )
        _preflight_exact(
            catalog_root_digest,
            ContentDigest,
            "admission.catalog_root_digest",
        )
        _preflight_exact(
            participation_policy_body,
            WorkspaceSemanticMaterializationParticipationPolicy,
            "admission.participation_policy_body",
        )
        payload = _admission_payload(
            package_ref=package_ref,
            code_intent_body=code_intent_body,
            code_intent_digest=code_intent_body.intent_digest,
            catalog_root_digest=catalog_root_digest,
            catalog_generation=catalog_generation,
            participation_policy_body=participation_policy_body,
            participation_policy_digest=participation_policy_body.policy_digest,
        )
        return _frozen_value(
            cls,
            package_ref=package_ref,
            code_intent_body=code_intent_body,
            code_intent_digest=code_intent_body.intent_digest,
            catalog_root_digest=catalog_root_digest,
            catalog_generation=catalog_generation,
            participation_policy_body=participation_policy_body,
            participation_policy_digest=participation_policy_body.policy_digest,
            admission_digest=_digest(WORKSPACE_ADMITTED_PACKAGE_INTENT, payload),
        )

    def __post_init__(self) -> None:
        payload = _admission_payload(
            package_ref=self.package_ref,
            code_intent_body=self.code_intent_body,
            code_intent_digest=self.code_intent_digest,
            catalog_root_digest=self.catalog_root_digest,
            catalog_generation=self.catalog_generation,
            participation_policy_body=self.participation_policy_body,
            participation_policy_digest=self.participation_policy_digest,
        )
        if _content_digest(
            self.admission_digest, "admission.admission_digest"
        ) != _digest(WORKSPACE_ADMITTED_PACKAGE_INTENT, payload):
            raise ContractViolation("package intent admission digest mismatched")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_ADMITTED_PACKAGE_INTENT,
            **_admission_payload(
                package_ref=self.package_ref,
                code_intent_body=self.code_intent_body,
                code_intent_digest=self.code_intent_digest,
                catalog_root_digest=self.catalog_root_digest,
                catalog_generation=self.catalog_generation,
                participation_policy_body=self.participation_policy_body,
                participation_policy_digest=self.participation_policy_digest,
            ),
            "admission_digest": self.admission_digest.to_wire(),
        }


def _admission_payload(
    *,
    package_ref: object,
    code_intent_body: object,
    code_intent_digest: object,
    catalog_root_digest: object,
    catalog_generation: object,
    participation_policy_body: object,
    participation_policy_digest: object,
) -> dict[str, object]:
    package = _token(package_ref, "admission.package_ref")
    if type(code_intent_body) is not CodeSemanticMaterializationIntent:
        raise TypeError("admission.code_intent_body must be exact Code intent")
    code_intent_body.__post_init__()
    intent_digest = _content_digest(code_intent_digest, "admission.code_intent_digest")
    if intent_digest != code_intent_body.intent_digest:
        raise ContractViolation("admission Code intent digest differs from body")
    if (
        type(participation_policy_body)
        is not WorkspaceSemanticMaterializationParticipationPolicy
    ):
        raise TypeError("admission participation policy must be exact")
    participation_policy_body.__post_init__()
    policy_digest = _content_digest(
        participation_policy_digest, "admission.participation_policy_digest"
    )
    if policy_digest != participation_policy_body.policy_digest:
        raise ContractViolation("admission policy digest differs from body")
    if participation_policy_body.package_ref != package:
        raise ContractViolation("admission package differs from policy")
    if not participation_policy_body.admits(code_intent_body):
        raise ContractViolation("participation policy does not admit Code intent")
    return {
        "catalog_generation": _nonnegative(
            catalog_generation, "admission.catalog_generation"
        ),
        "catalog_root_digest": _content_digest(
            catalog_root_digest, "admission.catalog_root_digest"
        ).to_wire(),
        "code_intent_body": code_intent_body.to_wire(),
        "code_intent_digest": intent_digest.to_wire(),
        "package_ref": package,
        "participation_policy_body": participation_policy_body.to_wire(),
        "participation_policy_digest": policy_digest.to_wire(),
    }


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializationRootIntentAssociation:
    package_ref: str
    code_intent_digest: ContentDigest
    workspace_intent_admission_digest: ContentDigest
    association_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        package_ref: str,
        intent: CodeSemanticMaterializationIntent,
        admission: WorkspaceAdmittedPackageIntent,
    ) -> WorkspaceMaterializationRootIntentAssociation:
        _preflight_exact(
            admission,
            WorkspaceAdmittedPackageIntent,
            "association.admission",
        )
        _preflight_exact(
            intent,
            CodeSemanticMaterializationIntent,
            "association.intent",
        )
        admission.__post_init__()
        intent.__post_init__()
        payload = _association_payload(
            package_ref=package_ref,
            code_intent_digest=intent.intent_digest,
            workspace_intent_admission_digest=admission.admission_digest,
        )
        if (
            admission.package_ref != package_ref
            or admission.code_intent_digest != intent.intent_digest
        ):
            raise ContractViolation("association context differs")
        return _frozen_value(
            cls,
            package_ref=package_ref,
            code_intent_digest=intent.intent_digest,
            workspace_intent_admission_digest=admission.admission_digest,
            association_digest=_digest(
                WORKSPACE_MATERIALIZATION_ROOT_INTENT_ASSOCIATION, payload
            ),
        )

    def __post_init__(self) -> None:
        payload = _association_payload(
            package_ref=self.package_ref,
            code_intent_digest=self.code_intent_digest,
            workspace_intent_admission_digest=self.workspace_intent_admission_digest,
        )
        if _content_digest(
            self.association_digest, "association.association_digest"
        ) != _digest(WORKSPACE_MATERIALIZATION_ROOT_INTENT_ASSOCIATION, payload):
            raise ContractViolation("root intent association digest mismatched")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_MATERIALIZATION_ROOT_INTENT_ASSOCIATION,
            **_association_payload(
                package_ref=self.package_ref,
                code_intent_digest=self.code_intent_digest,
                workspace_intent_admission_digest=(
                    self.workspace_intent_admission_digest
                ),
            ),
            "association_digest": self.association_digest.to_wire(),
        }


def _association_payload(
    *,
    package_ref: object,
    code_intent_digest: object,
    workspace_intent_admission_digest: object,
) -> dict[str, object]:
    return {
        "code_intent_digest": _content_digest(
            code_intent_digest, "association.code_intent_digest"
        ).to_wire(),
        "package_ref": _token(package_ref, "association.package_ref"),
        "workspace_intent_admission_digest": _content_digest(
            workspace_intent_admission_digest,
            "association.workspace_intent_admission_digest",
        ).to_wire(),
    }


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializationSelectionResolution:
    proposal_digest: ContentDigest
    catalog_root_digest: ContentDigest
    catalog_generation: int
    expanded_package_refs: tuple[str, ...]
    root_intent_associations: tuple[WorkspaceMaterializationRootIntentAssociation, ...]
    resolution_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        proposal: WorkspaceMaterializationSelectionProposal,
        catalog_root_digest: ContentDigest,
        catalog_generation: int,
        expanded_package_refs: tuple[str, ...],
        root_intent_associations: tuple[
            WorkspaceMaterializationRootIntentAssociation, ...
        ],
    ) -> WorkspaceMaterializationSelectionResolution:
        _preflight_exact(
            proposal,
            WorkspaceMaterializationSelectionProposal,
            "resolution.proposal",
        )
        _preflight_exact(
            catalog_root_digest,
            ContentDigest,
            "resolution.catalog_root_digest",
        )
        _preflight_tuple(
            root_intent_associations,
            WorkspaceMaterializationRootIntentAssociation,
            "resolution.root_intent_associations",
        )
        proposal.__post_init__()
        payload = _resolution_payload(
            proposal_digest=proposal.proposal_digest,
            catalog_root_digest=catalog_root_digest,
            catalog_generation=catalog_generation,
            expanded_package_refs=expanded_package_refs,
            root_intent_associations=root_intent_associations,
        )
        return _frozen_value(
            cls,
            proposal_digest=proposal.proposal_digest,
            catalog_root_digest=catalog_root_digest,
            catalog_generation=catalog_generation,
            expanded_package_refs=expanded_package_refs,
            root_intent_associations=root_intent_associations,
            resolution_digest=_digest(
                WORKSPACE_MATERIALIZATION_SELECTION_RESOLUTION, payload
            ),
        )

    def __post_init__(self) -> None:
        payload = _resolution_payload(
            proposal_digest=self.proposal_digest,
            catalog_root_digest=self.catalog_root_digest,
            catalog_generation=self.catalog_generation,
            expanded_package_refs=self.expanded_package_refs,
            root_intent_associations=self.root_intent_associations,
        )
        if _content_digest(
            self.resolution_digest, "resolution.resolution_digest"
        ) != _digest(WORKSPACE_MATERIALIZATION_SELECTION_RESOLUTION, payload):
            raise ContractViolation("selection resolution digest mismatched")

    def to_wire(self) -> dict[str, object]:
        payload = _resolution_payload(
            proposal_digest=self.proposal_digest,
            catalog_root_digest=self.catalog_root_digest,
            catalog_generation=self.catalog_generation,
            expanded_package_refs=self.expanded_package_refs,
            root_intent_associations=self.root_intent_associations,
        )
        if _content_digest(
            self.resolution_digest, "resolution.resolution_digest"
        ) != _digest(WORKSPACE_MATERIALIZATION_SELECTION_RESOLUTION, payload):
            raise ContractViolation("selection resolution digest mismatched")
        return {
            "contract": WORKSPACE_MATERIALIZATION_SELECTION_RESOLUTION,
            **payload,
            "resolution_digest": self.resolution_digest.to_wire(),
        }


def _resolution_payload(
    *,
    proposal_digest: object,
    catalog_root_digest: object,
    catalog_generation: object,
    expanded_package_refs: object,
    root_intent_associations: object,
) -> dict[str, object]:
    packages = _token_tuple(
        expanded_package_refs, "resolution.expanded_package_refs", nonempty=True
    )
    associations = _exact_tuple(
        root_intent_associations,
        WorkspaceMaterializationRootIntentAssociation,
        "resolution.root_intent_associations",
    )
    if len(packages) != len(associations) or any(
        package != association.package_ref
        for package, association in zip(packages, associations, strict=True)
    ):
        raise ContractViolation("resolution package/association alignment differs")
    if tuple(association.package_ref for association in associations) != packages:
        raise ContractViolation("resolution associations are not package ordered")
    return {
        "catalog_generation": _nonnegative(
            catalog_generation, "resolution.catalog_generation"
        ),
        "catalog_root_digest": _content_digest(
            catalog_root_digest, "resolution.catalog_root_digest"
        ).to_wire(),
        "expanded_package_refs": list(packages),
        "proposal_digest": _content_digest(
            proposal_digest, "resolution.proposal_digest"
        ).to_wire(),
        "root_intent_associations": [item.to_wire() for item in associations],
    }


__all__ = [
    "WORKSPACE_ADMITTED_PACKAGE_INTENT",
    "WORKSPACE_MATERIALIZATION_ROOT_INTENT_ASSOCIATION",
    "WORKSPACE_MATERIALIZATION_ROOT_SELECTOR",
    "WORKSPACE_MATERIALIZATION_SELECTION_PROPOSAL",
    "WORKSPACE_MATERIALIZATION_SELECTION_RESOLUTION",
    "WORKSPACE_MATERIALIZATION_SELECTOR_KINDS",
    "WORKSPACE_SEMANTIC_MATERIALIZATION_PARTICIPATION_POLICY",
    "WorkspaceAdmittedPackageIntent",
    "WorkspaceMaterializationRootIntentAssociation",
    "WorkspaceMaterializationRootSelector",
    "WorkspaceMaterializationSelectionProposal",
    "WorkspaceMaterializationSelectionResolution",
    "WorkspaceSemanticMaterializationParticipationPolicy",
]
