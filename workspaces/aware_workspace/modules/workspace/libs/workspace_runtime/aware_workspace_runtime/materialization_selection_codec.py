"""Strict codecs for Workspace materialization selection values."""

from __future__ import annotations

import json
from typing import Protocol, cast

from aware_code_semantic_contract_runtime import (
    CodeSemanticMaterializationIntent,
    ContentDigest,
    ContractViolation,
    SemanticConfigurationCoordinate,
    decode_code_semantic_materialization_intent,
)

from .materialization_selection import (
    WORKSPACE_ADMITTED_PACKAGE_INTENT,
    WORKSPACE_MATERIALIZATION_ROOT_INTENT_ASSOCIATION,
    WORKSPACE_MATERIALIZATION_ROOT_SELECTOR,
    WORKSPACE_MATERIALIZATION_SELECTION_PROPOSAL,
    WORKSPACE_MATERIALIZATION_SELECTION_RESOLUTION,
    WORKSPACE_SEMANTIC_MATERIALIZATION_PARTICIPATION_POLICY,
    WorkspaceAdmittedPackageIntent,
    WorkspaceMaterializationRootIntentAssociation,
    WorkspaceMaterializationRootSelector,
    WorkspaceMaterializationSelectionProposal,
    WorkspaceMaterializationSelectionResolution,
    WorkspaceSemanticMaterializationParticipationPolicy,
)

_MAX_WIRE_BYTES = 2_000_000


class _WireValue(Protocol):
    def __post_init__(self) -> None: ...

    def to_wire(self) -> object: ...


def encode_workspace_materialization_selection_proposal(
    value: WorkspaceMaterializationSelectionProposal,
) -> bytes:
    return _encode_exact(value, WorkspaceMaterializationSelectionProposal, "proposal")


def decode_workspace_materialization_selection_proposal(
    wire: bytes,
) -> WorkspaceMaterializationSelectionProposal:
    root = _decode_object(
        wire, {"contract", "proposal_digest", "selectors"}, "proposal"
    )
    _contract(root, WORKSPACE_MATERIALIZATION_SELECTION_PROPOSAL, "proposal")
    value = WorkspaceMaterializationSelectionProposal(
        selectors=tuple(
            _selector(item, f"proposal.selectors[{index}]")
            for index, item in enumerate(_list(root["selectors"], "proposal.selectors"))
        ),
        proposal_digest=_digest(root["proposal_digest"], "proposal.proposal_digest"),
    )
    return _canonical_result(wire, value, "proposal")


def encode_workspace_semantic_materialization_participation_policy(
    value: WorkspaceSemanticMaterializationParticipationPolicy,
) -> bytes:
    return _encode_exact(
        value, WorkspaceSemanticMaterializationParticipationPolicy, "policy"
    )


def decode_workspace_semantic_materialization_participation_policy(
    wire: bytes,
) -> WorkspaceSemanticMaterializationParticipationPolicy:
    root = _decode_object(
        wire,
        {
            "allow_unconfigured",
            "allowed_operation_kinds",
            "allowed_semantic_configuration_coordinates",
            "allowed_semantic_root_refs",
            "allowed_terminal_output_roles",
            "contract",
            "package_ref",
            "policy_digest",
            "policy_ref",
            "policy_revision",
        },
        "policy",
    )
    _contract(root, WORKSPACE_SEMANTIC_MATERIALIZATION_PARTICIPATION_POLICY, "policy")
    value = WorkspaceSemanticMaterializationParticipationPolicy(
        policy_ref=_text(root["policy_ref"], "policy.policy_ref"),
        policy_revision=_integer(root["policy_revision"], "policy.policy_revision"),
        package_ref=_text(root["package_ref"], "policy.package_ref"),
        allowed_operation_kinds=_text_tuple(
            root["allowed_operation_kinds"], "policy.allowed_operation_kinds"
        ),
        allowed_semantic_root_refs=_text_tuple(
            root["allowed_semantic_root_refs"], "policy.allowed_semantic_root_refs"
        ),
        allowed_terminal_output_roles=_text_tuple(
            root["allowed_terminal_output_roles"],
            "policy.allowed_terminal_output_roles",
        ),
        allow_unconfigured=_boolean(
            root["allow_unconfigured"], "policy.allow_unconfigured"
        ),
        allowed_semantic_configuration_coordinates=tuple(
            _configuration(
                item,
                f"policy.allowed_semantic_configuration_coordinates[{index}]",
            )
            for index, item in enumerate(
                _list(
                    root["allowed_semantic_configuration_coordinates"],
                    "policy.allowed_semantic_configuration_coordinates",
                )
            )
        ),
        policy_digest=_digest(root["policy_digest"], "policy.policy_digest"),
    )
    return _canonical_result(wire, value, "policy")


def encode_workspace_admitted_package_intent(
    value: WorkspaceAdmittedPackageIntent,
    *,
    code_intent: CodeSemanticMaterializationIntent,
    participation_policy: WorkspaceSemanticMaterializationParticipationPolicy,
    catalog_root_digest: ContentDigest,
    catalog_generation: int,
) -> bytes:
    _validate_admission_context(
        value,
        code_intent=code_intent,
        participation_policy=participation_policy,
        catalog_root_digest=catalog_root_digest,
        catalog_generation=catalog_generation,
    )
    return _encode_admitted_wire(value.to_wire())


def decode_workspace_admitted_package_intent(
    wire: bytes,
    *,
    code_intent: CodeSemanticMaterializationIntent,
    participation_policy: WorkspaceSemanticMaterializationParticipationPolicy,
    catalog_root_digest: ContentDigest,
    catalog_generation: int,
) -> WorkspaceAdmittedPackageIntent:
    root = _decode_object(
        wire,
        {
            "admission_digest",
            "catalog_generation",
            "catalog_root_digest",
            "code_intent_body",
            "code_intent_digest",
            "contract",
            "package_ref",
            "participation_policy_body",
            "participation_policy_digest",
        },
        "admission",
    )
    _contract(root, WORKSPACE_ADMITTED_PACKAGE_INTENT, "admission")
    parsed_intent = decode_code_semantic_materialization_intent(
        _encode_admitted_wire(root["code_intent_body"])
    )
    parsed_policy = decode_workspace_semantic_materialization_participation_policy(
        _encode_admitted_wire(root["participation_policy_body"])
    )
    value = WorkspaceAdmittedPackageIntent(
        package_ref=_text(root["package_ref"], "admission.package_ref"),
        code_intent_body=parsed_intent,
        code_intent_digest=_digest(
            root["code_intent_digest"], "admission.code_intent_digest"
        ),
        catalog_root_digest=_digest(
            root["catalog_root_digest"], "admission.catalog_root_digest"
        ),
        catalog_generation=_integer(
            root["catalog_generation"], "admission.catalog_generation"
        ),
        participation_policy_body=parsed_policy,
        participation_policy_digest=_digest(
            root["participation_policy_digest"],
            "admission.participation_policy_digest",
        ),
        admission_digest=_digest(
            root["admission_digest"], "admission.admission_digest"
        ),
    )
    _validate_admission_context(
        value,
        code_intent=code_intent,
        participation_policy=participation_policy,
        catalog_root_digest=catalog_root_digest,
        catalog_generation=catalog_generation,
    )
    if (
        encode_workspace_admitted_package_intent(
            value,
            code_intent=code_intent,
            participation_policy=participation_policy,
            catalog_root_digest=catalog_root_digest,
            catalog_generation=catalog_generation,
        )
        != wire
    ):
        raise ContractViolation("admission wire is not canonical")
    return value


def encode_workspace_materialization_selection_resolution(
    value: WorkspaceMaterializationSelectionResolution,
    *,
    proposal: WorkspaceMaterializationSelectionProposal,
) -> bytes:
    if type(value) is not WorkspaceMaterializationSelectionResolution:
        raise TypeError("resolution must be exact")
    _validate_resolution_context(value, proposal=proposal)
    return _encode_admitted_wire(value.to_wire())


def decode_workspace_materialization_selection_resolution(
    wire: bytes,
    *,
    proposal: WorkspaceMaterializationSelectionProposal,
) -> WorkspaceMaterializationSelectionResolution:
    root = _decode_object(
        wire,
        {
            "catalog_generation",
            "catalog_root_digest",
            "contract",
            "expanded_package_refs",
            "proposal_digest",
            "resolution_digest",
            "root_intent_associations",
        },
        "resolution",
    )
    _contract(root, WORKSPACE_MATERIALIZATION_SELECTION_RESOLUTION, "resolution")
    value = _unchecked_value(
        WorkspaceMaterializationSelectionResolution,
        proposal_digest=_digest(root["proposal_digest"], "resolution.proposal_digest"),
        catalog_root_digest=_digest(
            root["catalog_root_digest"], "resolution.catalog_root_digest"
        ),
        catalog_generation=_integer(
            root["catalog_generation"], "resolution.catalog_generation"
        ),
        expanded_package_refs=_text_tuple(
            root["expanded_package_refs"], "resolution.expanded_package_refs"
        ),
        root_intent_associations=tuple(
            _association(item, f"resolution.root_intent_associations[{index}]")
            for index, item in enumerate(
                _list(
                    root["root_intent_associations"],
                    "resolution.root_intent_associations",
                )
            )
        ),
        resolution_digest=_digest(
            root["resolution_digest"], "resolution.resolution_digest"
        ),
    )
    if (
        encode_workspace_materialization_selection_resolution(value, proposal=proposal)
        != wire
    ):
        raise ContractViolation("resolution wire is not canonical")
    return value


def _validate_admission_context(
    value: object,
    *,
    code_intent: object,
    participation_policy: object,
    catalog_root_digest: object,
    catalog_generation: object,
) -> WorkspaceAdmittedPackageIntent:
    if type(value) is not WorkspaceAdmittedPackageIntent:
        raise TypeError("admission must be exact WorkspaceAdmittedPackageIntent")
    if type(code_intent) is not CodeSemanticMaterializationIntent:
        raise TypeError("code_intent must be exact")
    if (
        type(participation_policy)
        is not WorkspaceSemanticMaterializationParticipationPolicy
    ):
        raise TypeError("participation_policy must be exact")
    if type(catalog_root_digest) is not ContentDigest:
        raise TypeError("catalog_root_digest must be exact ContentDigest")
    code_intent.__post_init__()
    participation_policy.__post_init__()
    catalog_root_digest.__post_init__()
    value.__post_init__()
    if (
        value.code_intent_body != code_intent
        or value.code_intent_digest != code_intent.intent_digest
        or value.participation_policy_body != participation_policy
        or value.participation_policy_digest != participation_policy.policy_digest
        or value.catalog_root_digest != catalog_root_digest
        or value.catalog_generation
        != _integer(catalog_generation, "catalog_generation")
    ):
        raise ContractViolation("admission differs from exact context")
    return value


def _validate_resolution_context(
    value: object, *, proposal: object
) -> WorkspaceMaterializationSelectionResolution:
    if type(value) is not WorkspaceMaterializationSelectionResolution:
        raise TypeError("resolution must be exact")
    if type(proposal) is not WorkspaceMaterializationSelectionProposal:
        raise TypeError("proposal must be exact")
    proposal.__post_init__()
    if value.proposal_digest != proposal.proposal_digest:
        raise ContractViolation("resolution differs from proposal context")
    return value


def _selector(value: object, path: str) -> WorkspaceMaterializationRootSelector:
    root = _object(
        value,
        {"contract", "selector_digest", "selector_kind", "selector_ref"},
        path,
    )
    _contract(root, WORKSPACE_MATERIALIZATION_ROOT_SELECTOR, path)
    return WorkspaceMaterializationRootSelector(
        selector_kind=_text(root["selector_kind"], f"{path}.selector_kind"),
        selector_ref=_text(root["selector_ref"], f"{path}.selector_ref"),
        selector_digest=_digest(root["selector_digest"], f"{path}.selector_digest"),
    )


def _association(
    value: object, path: str
) -> WorkspaceMaterializationRootIntentAssociation:
    root = _object(
        value,
        {
            "association_digest",
            "code_intent_digest",
            "contract",
            "package_ref",
            "workspace_intent_admission_digest",
        },
        path,
    )
    _contract(root, WORKSPACE_MATERIALIZATION_ROOT_INTENT_ASSOCIATION, path)
    return _unchecked_value(
        WorkspaceMaterializationRootIntentAssociation,
        package_ref=_text(root["package_ref"], f"{path}.package_ref"),
        code_intent_digest=_digest(
            root["code_intent_digest"], f"{path}.code_intent_digest"
        ),
        workspace_intent_admission_digest=_digest(
            root["workspace_intent_admission_digest"],
            f"{path}.workspace_intent_admission_digest",
        ),
        association_digest=_digest(
            root["association_digest"], f"{path}.association_digest"
        ),
    )


def _configuration(value: object, path: str) -> SemanticConfigurationCoordinate:
    root = _object(value, {"configuration_ref", "digest"}, path)
    return SemanticConfigurationCoordinate(
        configuration_ref=_text(root["configuration_ref"], f"{path}.configuration_ref"),
        digest=_digest(root["digest"], f"{path}.digest"),
    )


def _encode_exact[T: _WireValue](value: object, expected: type[T], path: str) -> bytes:
    if type(value) is not expected:
        raise TypeError(f"{path} must be exact {expected.__name__}")
    admitted = cast(T, value)
    admitted.__post_init__()
    return _encode_admitted_wire(admitted.to_wire())


def _canonical_result[T: _WireValue](wire: bytes, value: T, path: str) -> T:
    if _encode_admitted_wire(value.to_wire()) != wire:
        raise ContractViolation(f"{path} wire is not canonical")
    return value


def _encode_admitted_wire(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _unchecked_value[T](expected: type[T], **fields: object) -> T:
    result = object.__new__(expected)
    for name, value in fields.items():
        object.__setattr__(result, name, value)
    return result


def _decode_object(wire: bytes, keys: set[str], path: str) -> dict[str, object]:
    if type(wire) is not bytes:
        raise TypeError("wire must be exact bytes")
    if not wire or len(wire) > _MAX_WIRE_BYTES:
        raise ContractViolation("wire size unsupported")
    try:
        parsed = json.loads(wire.decode())
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractViolation("wire is not JSON") from error
    return _object(parsed, keys, path)


def _object(value: object, keys: set[str], path: str) -> dict[str, object]:
    if type(value) is not dict:
        raise TypeError(f"{path} must be exact object")
    result = cast(dict[object, object], value)
    if any(type(key) is not str for key in result) or set(result) != keys:
        raise ContractViolation(f"{path} fields differ")
    return cast(dict[str, object], result)


def _contract(root: dict[str, object], expected: str, path: str) -> None:
    if _text(root["contract"], f"{path}.contract") != expected:
        raise ContractViolation(f"{path} contract unsupported")


def _list(value: object, path: str) -> list[object]:
    if type(value) is not list:
        raise TypeError(f"{path} must be exact list")
    return cast(list[object], value)


def _text(value: object, path: str) -> str:
    if type(value) is not str or not value or any(char.isspace() for char in value):
        raise TypeError(f"{path} must be nonempty token text")
    return value


def _text_tuple(value: object, path: str) -> tuple[str, ...]:
    return tuple(
        _text(item, f"{path}[{index}]") for index, item in enumerate(_list(value, path))
    )


def _integer(value: object, path: str) -> int:
    if type(value) is not int or value < 0:
        raise TypeError(f"{path} must be exact nonnegative integer")
    return value


def _boolean(value: object, path: str) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{path} must be exact boolean")
    return value


def _digest(value: object, path: str) -> ContentDigest:
    return ContentDigest.of_wire(value, path)


__all__ = [
    "decode_workspace_admitted_package_intent",
    "decode_workspace_materialization_selection_proposal",
    "decode_workspace_materialization_selection_resolution",
    "decode_workspace_semantic_materialization_participation_policy",
    "encode_workspace_admitted_package_intent",
    "encode_workspace_materialization_selection_proposal",
    "encode_workspace_materialization_selection_resolution",
    "encode_workspace_semantic_materialization_participation_policy",
]
