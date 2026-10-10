from __future__ import annotations

import json
from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime import (
    CodeSemanticMaterializationIntent,
    ContentDigest,
    ContractViolation,
    SemanticConfigurationCoordinate,
    canonical_json_bytes,
)
from aware_workspace_runtime import (
    WorkspaceAdmittedPackageIntent,
    WorkspaceMaterializationRootIntentAssociation,
    WorkspaceMaterializationRootSelector,
    WorkspaceMaterializationSelectionProposal,
    WorkspaceMaterializationSelectionResolution,
    WorkspaceSemanticMaterializationParticipationPolicy,
    decode_workspace_admitted_package_intent,
    decode_workspace_materialization_selection_proposal,
    decode_workspace_materialization_selection_resolution,
    decode_workspace_semantic_materialization_participation_policy,
    encode_workspace_admitted_package_intent,
    encode_workspace_materialization_selection_proposal,
    encode_workspace_materialization_selection_resolution,
    encode_workspace_semantic_materialization_participation_policy,
)


def _digest(value: str) -> ContentDigest:
    return ContentDigest.of_bytes(value.encode())


def _intent(root: str = "api.public") -> CodeSemanticMaterializationIntent:
    return CodeSemanticMaterializationIntent.create(
        operation_kind="materialize",
        requested_semantic_root_refs=(root,),
        requested_terminal_output_roles=("python_sdk",),
        semantic_configuration_coordinate=SemanticConfigurationCoordinate(
            configuration_ref="python.3",
            digest=_digest("python-3"),
        ),
    )


def _policy(
    package_ref: str = "package:api",
) -> WorkspaceSemanticMaterializationParticipationPolicy:
    return WorkspaceSemanticMaterializationParticipationPolicy.create(
        policy_ref=f"policy:{package_ref}",
        policy_revision=3,
        package_ref=package_ref,
        allowed_operation_kinds=("materialize",),
        allowed_semantic_root_refs=("api.public", "sdk.public"),
        allowed_terminal_output_roles=("python_sdk",),
        allow_unconfigured=False,
        allowed_semantic_configuration_coordinates=(
            SemanticConfigurationCoordinate(
                configuration_ref="python.3",
                digest=_digest("python-3"),
            ),
        ),
    )


def _admission(
    package_ref: str = "package:api",
    *,
    intent: CodeSemanticMaterializationIntent | None = None,
) -> WorkspaceAdmittedPackageIntent:
    selected_intent = intent or _intent()
    return WorkspaceAdmittedPackageIntent.create(
        package_ref=package_ref,
        code_intent_body=selected_intent,
        catalog_root_digest=_digest("catalog"),
        catalog_generation=7,
        participation_policy_body=_policy(package_ref),
    )


def _selection() -> tuple[
    WorkspaceMaterializationSelectionProposal,
    WorkspaceMaterializationSelectionResolution,
]:
    selectors = (
        WorkspaceMaterializationRootSelector.create(
            selector_kind="package", selector_ref="package:api"
        ),
        WorkspaceMaterializationRootSelector.create(
            selector_kind="workspace", selector_ref="aware_kernel"
        ),
    )
    proposal = WorkspaceMaterializationSelectionProposal.create(
        selectors=tuple(
            sorted(selectors, key=lambda item: canonical_json_bytes(item.to_wire()))
        )
    )
    packages = ("package:api", "package:sdk")
    associations = []
    for package_ref, root in zip(packages, ("api.public", "sdk.public"), strict=True):
        intent = _intent(root)
        associations.append(
            WorkspaceMaterializationRootIntentAssociation.create(
                package_ref=package_ref,
                intent=intent,
                admission=_admission(package_ref, intent=intent),
            )
        )
    resolution = WorkspaceMaterializationSelectionResolution.create(
        proposal=proposal,
        catalog_root_digest=_digest("catalog"),
        catalog_generation=7,
        expanded_package_refs=packages,
        root_intent_associations=tuple(associations),
    )
    return proposal, resolution


def test_selection_policy_admission_and_resolution_round_trip() -> None:
    proposal, resolution = _selection()
    proposal_wire = encode_workspace_materialization_selection_proposal(proposal)
    assert (
        decode_workspace_materialization_selection_proposal(proposal_wire) == proposal
    )

    policy = _policy()
    policy_wire = encode_workspace_semantic_materialization_participation_policy(policy)
    assert (
        decode_workspace_semantic_materialization_participation_policy(policy_wire)
        == policy
    )

    intent = _intent()
    admission = _admission(intent=intent)
    context = {
        "code_intent": intent,
        "participation_policy": policy,
        "catalog_root_digest": _digest("catalog"),
        "catalog_generation": 7,
    }
    admission_wire = encode_workspace_admitted_package_intent(admission, **context)
    assert (
        decode_workspace_admitted_package_intent(admission_wire, **context) == admission
    )

    resolution_wire = encode_workspace_materialization_selection_resolution(
        resolution, proposal=proposal
    )
    assert (
        decode_workspace_materialization_selection_resolution(
            resolution_wire, proposal=proposal
        )
        == resolution
    )


def test_policy_is_exact_and_never_rewrites_code_intent() -> None:
    policy = _policy()
    intent = _intent()
    assert policy.admits(intent)
    assert _admission(intent=intent).code_intent_body == intent

    with pytest.raises(ContractViolation, match="does not admit"):
        WorkspaceAdmittedPackageIntent.create(
            package_ref="package:api",
            code_intent_body=_intent("unknown.root"),
            catalog_root_digest=_digest("catalog"),
            catalog_generation=7,
            participation_policy_body=policy,
        )
    with pytest.raises(TypeError, match="exact bool"):
        replace(policy, allow_unconfigured=1)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="integer"):
        replace(policy, policy_revision=True)  # type: ignore[arg-type]


def test_selector_and_package_association_order_fail_closed() -> None:
    proposal, resolution = _selection()
    with pytest.raises(ContractViolation, match="canonical-byte ordered"):
        WorkspaceMaterializationSelectionProposal.create(
            selectors=tuple(reversed(proposal.selectors))
        )
    with pytest.raises(ContractViolation, match="alignment"):
        replace(
            resolution,
            root_intent_associations=tuple(
                reversed(resolution.root_intent_associations)
            ),
        )
    with pytest.raises(ContractViolation, match="kind unsupported"):
        WorkspaceMaterializationRootSelector.create(
            selector_kind="provider", selector_ref="forbidden"
        )


def test_context_substitution_and_retained_digest_wire_fail() -> None:
    intent = _intent()
    policy = _policy()
    admission = _admission(intent=intent)
    context = {
        "code_intent": intent,
        "participation_policy": policy,
        "catalog_root_digest": _digest("catalog"),
        "catalog_generation": 7,
    }
    wire = encode_workspace_admitted_package_intent(admission, **context)
    with pytest.raises(ContractViolation, match="exact context"):
        decode_workspace_admitted_package_intent(
            wire,
            **{**context, "catalog_root_digest": _digest("other-catalog")},
        )

    payload = json.loads(wire)
    payload["participation_policy_body"]["allow_unconfigured"] = 1
    with pytest.raises((TypeError, ContractViolation)):
        decode_workspace_admitted_package_intent(
            canonical_json_bytes(payload), **context
        )

    with pytest.raises(ContractViolation, match="admission digest"):
        replace(admission, admission_digest=_digest("forged"))


def test_foreign_selector_rejected_before_foreign_behavior() -> None:
    calls: list[str] = []

    class ForeignSelector(WorkspaceMaterializationRootSelector):
        def to_wire(self) -> dict[str, object]:
            calls.append("foreign")
            return super().to_wire()

    exact = WorkspaceMaterializationRootSelector.create(
        selector_kind="package", selector_ref="package:api"
    )
    foreign = ForeignSelector(
        selector_kind=exact.selector_kind,
        selector_ref=exact.selector_ref,
        selector_digest=exact.selector_digest,
    )
    with pytest.raises(TypeError, match="exact WorkspaceMaterializationRootSelector"):
        WorkspaceMaterializationSelectionProposal.create(selectors=(foreign,))
    assert calls == []


def test_admission_rejects_foreign_context_before_property_access() -> None:
    calls: list[str] = []

    class ForeignIntent(CodeSemanticMaterializationIntent):
        def __getattribute__(self, name: str) -> object:
            if name == "intent_digest":
                calls.append("intent_digest")
            return super().__getattribute__(name)

    exact_intent = _intent()
    foreign_intent = ForeignIntent(
        operation_kind=exact_intent.operation_kind,
        requested_semantic_root_refs=exact_intent.requested_semantic_root_refs,
        requested_terminal_output_roles=(exact_intent.requested_terminal_output_roles),
        semantic_configuration_coordinate=(
            exact_intent.semantic_configuration_coordinate
        ),
        intent_digest=exact_intent.intent_digest,
    )
    calls.clear()
    with pytest.raises(TypeError, match="exact CodeSemanticMaterializationIntent"):
        WorkspaceAdmittedPackageIntent.create(
            package_ref="package:api",
            code_intent_body=foreign_intent,
            catalog_root_digest=_digest("catalog"),
            catalog_generation=7,
            participation_policy_body=_policy(),
        )
    assert calls == []

    class ForeignPolicy(WorkspaceSemanticMaterializationParticipationPolicy):
        def __getattribute__(self, name: str) -> object:
            if name == "policy_digest":
                calls.append("policy_digest")
            return super().__getattribute__(name)

    exact_policy = _policy()
    foreign_policy = ForeignPolicy(
        policy_ref=exact_policy.policy_ref,
        policy_revision=exact_policy.policy_revision,
        package_ref=exact_policy.package_ref,
        allowed_operation_kinds=exact_policy.allowed_operation_kinds,
        allowed_semantic_root_refs=exact_policy.allowed_semantic_root_refs,
        allowed_terminal_output_roles=exact_policy.allowed_terminal_output_roles,
        allow_unconfigured=exact_policy.allow_unconfigured,
        allowed_semantic_configuration_coordinates=(
            exact_policy.allowed_semantic_configuration_coordinates
        ),
        policy_digest=exact_policy.policy_digest,
    )
    calls.clear()
    with pytest.raises(
        TypeError, match="exact WorkspaceSemanticMaterializationParticipationPolicy"
    ):
        WorkspaceAdmittedPackageIntent.create(
            package_ref="package:api",
            code_intent_body=exact_intent,
            catalog_root_digest=_digest("catalog"),
            catalog_generation=7,
            participation_policy_body=foreign_policy,
        )
    assert calls == []
