"""V3 semantic admissions remain on the original selected-source issuer."""

import os
from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    SemanticContractRef,
    SemanticValueCoordinate,
    encode_semantic_candidate_listing,
)
from aware_code_semantic_contract_runtime.retained_admission_interfaces import (
    RetainedSemanticAdmissionExpectation,
)
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    DECLARATION_TARGET_INVENTORY_REF,
    PACKAGE_CONTEXT_INPUT_REF,
    encode_declaration_target_inventory,
    encode_package_context_input,
)
from aware_code_semantic_contract_runtime.semantic_candidates import (
    SEMANTIC_CANDIDATE_LISTING_REF,
)
from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime.declaration_scope_admission import (
    WorkspacePackageContextAdmission,
)
from test_declaration_scope_admission import fixture
from test_observed_semantic_issuers import PROVIDER, occurrence


class _OriginalContextValidator:
    def validate_retained_semantic_operation_context(self, context, *, expected):
        if context is not expected.operation_identity:
            raise SourceObservationUnavailable("wrong_original_operation")


def _coordinate(role, body, contract=None):
    return SemanticValueCoordinate(
        role,
        contract or SemanticContractRef(
            "fixture.bytes", "1", ContentDigest.of_bytes(b"schema")
        ),
        "fixture:" + role,
        ContentDigest.of_bytes(body),
        len(body),
    )


async def test_v3_original_issuer_admissions_and_currentness(tmp_path):
    async with fixture(tmp_path) as (root, _, observer, issuer, _, expected_scope):
        module = root / "workspaces/network/modules/main/aware.module.toml"
        module.write_text(
            'aware=3\n[module]\n[[packages]]\nid="example"\nkind="example"\n'
            'manifest="package/aware.example.toml"\nvisibility="module"\n'
            + occurrence("demo").replace(
                'value={module_id=', 'value={scope={kind="local"},module_id='
            ) + PROVIDER
        )
        provider = root / "workspaces/network/modules/main/provider"
        provider.mkdir()
        (provider / "pyproject.toml").write_bytes(b"[project]\nname='provider'\n")
        observed = observer.observe_declarations()
        declaration = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expected_scope,
        )
        selected_observation = observer.observe_selected_package(
            declaration=observed,
            workspace_manifest_path="workspaces/network/aware.workspace.toml",
            module_id="main", package_id="example",
        )
        selected = issuer.bind_selected_package_source(
            declaration=declaration, selected=selected_observation
        )
        issuer._bind_original_code_validator(_OriginalContextValidator())
        issuer._bind_original_authority_validator(_OriginalContextValidator())
        package, inventory = issuer.inspect_inputs(selected)
        binding = issuer.read_selected_package_source(selected)
        manifest = observer.read_selected_package(
            selected_observation, relative_path="aware.example.toml"
        )
        operation = object()
        expected = RetainedSemanticAdmissionExpectation(
            runtime=object(), generation_identity=object(),
            operation_identity=operation, process_id=os.getpid(),
            selected_provider_registration=object(), stage="source_planning",
            profile="fixture-profile", provider_declaration="fixture-provider",
            binding="fixture-binding", package=package.package,
            source_identity_digest=package.source_identity_digest,
            manifest_coordinate=_coordinate("manifest_source", manifest),
            candidate_coordinate=_coordinate(
                "candidate_listing",
                encode_semantic_candidate_listing(binding.candidates),
                SEMANTIC_CANDIDATE_LISTING_REF,
            ),
            registry_package_coordinate=_coordinate("registry_package", b"registry"),
            package_context_coordinate=_coordinate(
                "package_context", encode_package_context_input(package),
                PACKAGE_CONTEXT_INPUT_REF,
            ),
            declaration_inventory_coordinate=_coordinate(
                "declaration_inventory", encode_declaration_target_inventory(inventory),
                DECLARATION_TARGET_INVENTORY_REF,
            ),
        )
        context, targets = issuer.issue_source_planning_pair(
            selected, context=operation, expected=expected
        )
        assert type(context) is WorkspacePackageContextAdmission
        issuer.validate_package_context_admission(context, expected=expected)
        issuer.validate_declaration_inventory_admission(targets, expected=expected)
        issuer.validate_occurrence_assignments(
            context, expected=expected, namespace="demo",
            owned_roots=("demo.a", "demo.b"),
        )
        with pytest.raises(SourceObservationUnavailable, match="replay"):
            issuer.issue_source_planning_pair(selected, context=operation, expected=expected)
        with pytest.raises(SourceObservationUnavailable, match="assignment"):
            issuer.validate_occurrence_assignments(
                context, expected=expected, namespace="other",
                owned_roots=("demo.a", "demo.b"),
            )
        with pytest.raises(SourceObservationUnavailable, match="context"):
            issuer.validate_package_context_admission(
                context, expected=replace(expected, operation_identity=object())
            )
        (root / "workspaces/network/modules/main/package/body.bin").write_bytes(
            b"changed"
        )
        with pytest.raises(SourceObservationUnavailable):
            issuer.validate_package_context_admission(context, expected=expected)
