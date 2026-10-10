"""Source projections authenticate bytes before executable root entitlement."""

from contextlib import asynccontextmanager
from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    SemanticContractRef,
    SemanticValueCoordinate,
)
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    DECLARATION_TARGET_INVENTORY_REF,
    PACKAGE_CONTEXT_INPUT_REF,
    decode_declaration_target_inventory,
    decode_package_context_input,
)
from aware_code_semantic_contract_runtime.semantic_candidates import (
    SEMANTIC_CANDIDATE_LISTING_REF,
    decode_semantic_candidate_listing,
)
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputContextContract,
    SemanticInputSourceCoordinate,
)
from aware_workspace_runtime import SourceObservationUnavailable
from test_declaration_scope_admission import fixture
from test_materialization_declaration_selection import _author_v3_repository


@asynccontextmanager
async def rootless_source(tmp_path, missing, *, missing_target_roots=False):
    async with fixture(tmp_path) as (root, _, observer, issuer, _, expectation):
        _author_v3_repository(root)
        module = root / "workspaces/network/modules/main/aware.module.toml"
        lines = module.read_text().splitlines()
        module.write_text("\n".join(
            f'{field}={{state="unavailable"}}'
            if (field := line.split("=", 1)[0]) in missing else line
            for line in lines
        ) + "\n")
        if missing_target_roots:
            module.write_text(module.read_text().replace(
                'dependency_targets={state="present",value=[]}',
                'dependency_targets={state="present",value=[{dependency_kind="module",'
                'dependency_ref="target",targets=[{scope={kind="dependency",'
                'workspace_handle="Kernel"},module_id="main",package_id="example"}],'
                'constraints=[]}]}',
            ))
            target_module = root / "workspaces/kernel/modules/main/aware.module.toml"
            target_module.write_text("\n".join(
                'owned_roots={state="unavailable"}' if line.startswith("owned_roots=") else line
                for line in target_module.read_text().splitlines()
            ) + "\n")
        observed = observer.observe_declarations()
        declaration = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expectation,
        )
        selected = issuer.bind_selected_package_source(
            declaration=declaration,
            selected=observer.observe_selected_package(
                declaration=observed,
                workspace_manifest_path="workspaces/network/aware.workspace.toml",
                module_id="main", package_id="example",
            ),
        )
        evidence = issuer.inspect_selected_package_evidence(selected)
        manifest = next(b for b in evidence.bodies if b.relative_path == "aware.example.toml")
        contract = SemanticContractRef("fixture.raw-source", "1", ContentDigest.of_bytes(b"raw"))
        coordinates = (SemanticInputSourceCoordinate(
            manifest.relative_path,
            SemanticValueCoordinate("raw_source", contract, manifest.body_ref,
                                    ContentDigest(manifest.content_digest), manifest.size_bytes),
        ),)
        yield root, issuer, selected, coordinates


CONTEXTS = (
    SemanticInputContextContract("package_context", PACKAGE_CONTEXT_INPUT_REF),
    SemanticInputContextContract("source_inventory", SEMANTIC_CANDIDATE_LISTING_REF),
    SemanticInputContextContract("target_inventory", DECLARATION_TARGET_INVENTORY_REF),
)


@pytest.mark.parametrize("missing", [("owned_roots",), ("namespace",), ("namespace", "owned_roots")])
async def test_source_projections_do_not_mint_execution_assignments(tmp_path, missing):
    async with rootless_source(tmp_path, missing) as (_, issuer, selected, sources):
        with issuer.original_pre_request_input(
            selected, use_ref="source-only", stage="pre_request",
            source_coordinates=sources, context_contracts=CONTEXTS,
        ) as expected:
            assert expected.operation_identity is issuer._exclusion._parent
            context = decode_package_context_input(expected.context_bodies[0].canonical_body)
            listing = decode_semantic_candidate_listing(expected.context_bodies[1].canonical_body)
            inventory = decode_declaration_target_inventory(expected.context_bodies[2].canonical_body)
            assert context.package == inventory.package == expected.package_identity.package
            assert context.source_identity_digest == listing.source_identity_digest
            assert inventory.entries == ()
            assert issuer.read_semantic_input_sources(selected, expected=expected)[0].canonical_body == b"Network"
            issuer.validate_semantic_input_context(selected, expected=expected)
            with pytest.raises(SourceObservationUnavailable, match="occurrence_evidence_unavailable"):
                issuer.inspect_inputs(selected)
        assert not issuer._pre_request_inputs
        with pytest.raises(SourceObservationUnavailable, match="original_pre_request"):
            issuer.validate_semantic_input_context(selected, expected=expected)


async def test_source_mutation_is_terminal_even_without_root_assignments(tmp_path):
    async with rootless_source(tmp_path, ("owned_roots",)) as (root, issuer, selected, sources):
        with (
            pytest.raises(SourceObservationUnavailable),
            issuer.original_pre_request_input(
                selected, use_ref="source-mutation", stage="pre_request",
                source_coordinates=sources, context_contracts=CONTEXTS,
            ) as expected,
        ):
            manifest = root / "workspaces/network/modules/main/package/aware.example.toml"
            original = manifest.read_bytes()
            manifest.write_bytes(b"changed")
            with pytest.raises(SourceObservationUnavailable):
                issuer.read_semantic_input_sources(selected, expected=expected)
            manifest.write_bytes(original)
            with pytest.raises(SourceObservationUnavailable, match="original_pre_request"):
                issuer.read_semantic_input_sources(selected, expected=expected)
        assert not issuer._pre_request_inputs


async def test_wrong_source_coordinate_refuses_without_root_assignments(tmp_path):
    async with rootless_source(tmp_path, ("owned_roots",)) as (_, issuer, selected, sources):
        changed = replace(sources[0], coordinate=replace(sources[0].coordinate, value_ref="foreign:body"))
        with (
            pytest.raises(SourceObservationUnavailable, match="pre_request_source_differs"),
            issuer.original_pre_request_input(
                selected, use_ref="wrong-body", stage="pre_request",
                source_coordinates=(changed,), context_contracts=CONTEXTS,
            ),
        ):
            pytest.fail("foreign source coordinate admitted")
        assert not issuer._pre_request_inputs


async def test_dependency_inventory_still_requires_actual_target_roots(tmp_path):
    async with rootless_source(tmp_path, ("owned_roots",), missing_target_roots=True) as (
        _, issuer, selected, sources,
    ):
        with (
            pytest.raises(SourceObservationUnavailable, match="occurrence_evidence_unavailable"),
            issuer.original_pre_request_input(
                selected, use_ref="missing-target-roots", stage="pre_request",
                source_coordinates=sources, context_contracts=CONTEXTS,
            ),
        ):
            pytest.fail("dependency inventory invented target roots")
        assert not issuer._pre_request_inputs


async def test_original_selection_and_meta_assembler_keep_roots_unavailable(tmp_path, monkeypatch):
    import test_v3_source_admission as original_source
    from aware_meta_contract_runtime_provider.codec import (
        decode_meta_package_source_closure,
    )
    from test_original_engine_input_join import _original_assembly, _validate

    author = original_source._author_v3_repository

    def author_without_execution_assignments(root):
        author(root)
        module = root / "workspaces/network/modules/main/aware.module.toml"
        module.write_text("\n".join(
            f'{field}={{state="unavailable"}}'
            if (field := line.split("=", 1)[0]) in ("namespace", "owned_roots") else line
            for line in module.read_text().splitlines()
        ) + "\n")

    monkeypatch.setattr(original_source, "_author_v3_repository", author_without_execution_assignments)
    async with _original_assembly(tmp_path) as joined:
        closure = decode_meta_package_source_closure(joined.result.canonical_body)
        assert [row.relative_path for row in closure.sources] == ["a.aware", "b.aware"]
        _validate(joined)
        with pytest.raises(SourceObservationUnavailable, match="occurrence_evidence_unavailable"):
            joined.original.issuer.inspect_inputs(joined.original.selected)
    assert not joined.original.issuer._pre_request_inputs
