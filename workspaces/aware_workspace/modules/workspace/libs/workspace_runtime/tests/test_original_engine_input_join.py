"""Original Workspace sources/assembler around an uninstalled local engine.

Engine dependency values and first construction are portable diagnostics, not
Workspace fulfillment, V5 genesis or installed private-stage admissions.
"""

import asyncio
import time
from contextlib import asynccontextmanager
from dataclasses import replace
from types import SimpleNamespace

import pytest
from aware_code_semantic_contract_runtime import (
    CodeSemanticMaterializationIntent,
    ContentDigest,
    ContractViolation,
    SemanticDependencyDemandSet,
)
from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
from aware_code_semantic_contract_runtime.dependency_inputs import (
    SemanticDependencyProductInput,
)
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    decode_package_context_input,
)
from aware_code_semantic_contract_runtime.source_origin import (
    decode_source_origin,
    validate_source_origin_selection,
)
from aware_code_semantic_contract_runtime.source_selection import (
    decode_source_selection,
)
from aware_meta_contract_runtime_provider.codec import (
    decode_meta_package_source_closure,
)
from aware_meta_contract_runtime_provider.profile import (
    META_PACKAGE_RESULT_V2_REF,
    meta_provider_binding_v2,
    meta_provider_profile_v2,
)
from aware_meta_contract_runtime_provider.selected_factory import (
    MetaProviderSemanticInputs,
    create_meta_engine_session_v2,
)
from aware_meta_contract_runtime_provider.source_assembly import (
    STAGE,
    MetaEngineSourcePreparation,
)
from aware_meta_ocg_projection_syntax import (
    decode_meta_aware_package_portable_result_v2,
)
from aware_meta_source_preparation_provider import MetaSourcePreparation
from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime.command_lifetime import (
    WorkspaceCommandLifetimeUnavailable,
)
from test_v3_source_admission import _original_selection

AUTHORED_SOURCES = (
    ("a.aware", b"class Alpha {}\n"),
    ("b.aware", b"class Beta {}\n"),
)
REFUSALS = (ContractViolation, SourceObservationUnavailable, TypeError, RuntimeError)


@asynccontextmanager
async def _original_assembly(tmp_path):
    async with _original_selection(
        tmp_path, ontology=True, meta=True, authored_sources=AUTHORED_SOURCES,
        selected_package_kind="ontology",
    ) as original:
        owner = MetaSourcePreparation()
        entrances = {
            "validator": original.issuer,
            "validator_entrance": original.issuer.validate_semantic_input_source,
            "reader": original.issuer,
            "reader_entrance": original.issuer.read_semantic_input_sources,
            "context_validator_entrance": original.issuer.validate_semantic_input_context,
            "retain_result": True,
        }
        with original.issuer.original_selected_source_input(
            original.selected, use_ref="join-meta-selection",
            stage="meta_authored_source_selection",
            context_contracts=owner.declaration.context_contracts,
            **original.arguments,
        ) as selection_expected:
            registration = inputs.register_semantic_input_producer(
                original.host, declaration=owner.declaration,
                producer=owner.produce_sources, **entrances,
            )
            try:
                selected_result = await inputs.execute_registered_semantic_input(
                    original.host, registration,
                    source_admission=original.selected, expected=selection_expected,
                )
                assembler = MetaEngineSourcePreparation()
                declaration = assembler.declaration
                with original.issuer.original_selected_source_input(
                    original.selected, host=original.host, registration=registration,
                    selection_expected=selection_expected, result=selected_result,
                    source_contracts=declaration.source_contracts,
                    context_contracts=declaration.context_contracts,
                    use_ref="join-engine-source", stage=STAGE,
                ) as expected:
                    selected_body, context_body, origin_body = expected.context_bodies
                    selection = decode_source_selection(selected_body.canonical_body)
                    origin = decode_source_origin(origin_body.canonical_body)
                    context = decode_package_context_input(context_body.canonical_body)
                    validate_source_origin_selection(
                        origin, selection=selection,
                        selection_coordinate=selected_result.coordinate,
                        source_coordinates=expected.source_coordinates,
                    )
                    assert origin.package == expected.package_identity.package
                    assert context.package == origin.package
                    assert origin.package.package_kind == "ontology"
                    assert context.source_identity_digest == origin.source_identity_digest
                    assert context.manifest_relative_path == origin.outer_manifest.relative_path
                    assert selected_body.coordinate.digest == selected_result.coordinate.digest
                    assert selected_body.coordinate.size_bytes == selected_result.coordinate.size_bytes
                    assert origin.selection_input_digest == selection_expected.input_digest
                    assert origin.selection_coordinate == selected_result.coordinate
                    assert expected.package_identity.package_name == "network-example"
                    assert context.code_package_name == "network-example-code"
                    assert context.code_package_name != expected.package_identity.package_name
                    original.issuer.validate_semantic_input_context(original.selected, expected=expected)
                    assembly_registration = inputs.register_semantic_input_producer(
                        original.host, declaration=declaration,
                        producer=assembler.produce_closure, **entrances,
                    )
                    try:
                        result = await inputs.execute_registered_semantic_input(
                            original.host, assembly_registration,
                            source_admission=original.selected, expected=expected,
                        )
                        joined = SimpleNamespace(
                            original=original, registration=assembly_registration,
                            expected=expected, result=result, source_origin=origin,
                            selection_registration=registration,
                            selection_expected=selection_expected, selected_result=selected_result,
                        )
                        _validate(joined)
                        yield joined
                    finally:
                        inputs.close_semantic_input_producer_registration(
                            original.host, assembly_registration,
                        )
                assert not any(row.expected is expected for row in original.issuer._pre_request_inputs.values())
            finally:
                inputs.close_semantic_input_producer_registration(original.host, registration)
    assert not original.issuer._pre_request_inputs


def _validate(joined, *, result=None):
    inputs.validate_registered_semantic_input_result(
        joined.original.host, joined.registration,
        source_admission=joined.original.selected, expected=joined.expected,
        result=joined.result if result is None else result,
    )


def _diagnostic_engine_input(joined):
    """Portable empty products only; original dependency admissions are separate."""
    _validate(joined)
    source = decode_meta_package_source_closure(joined.result.canonical_body)
    profile = meta_provider_profile_v2()
    configuration = meta_provider_binding_v2().configuration
    package = joined.expected.package_identity.package
    intent = CodeSemanticMaterializationIntent.create(
        operation_kind="materialize",
        requested_semantic_root_refs=(joined.expected.package_identity.package_name,),
        requested_terminal_output_roles=("meta_package_result",),
        semantic_configuration_coordinate=configuration,
    )
    demand = SemanticDependencyDemandSet.create(
        package=package, intent=intent, profile_ref=profile.profile_ref,
        profile_digest=profile.digest,
        contract_profile_binding_digest=ContentDigest.of_bytes(b"local-engine-fixture"),
        planner_implementation_ref="local-engine-fixture.no-dependencies",
        planner_implementation_digest=ContentDigest.of_bytes(b"local-engine-fixture"),
        planner_configuration=configuration, demands=(),
    )
    dependency_input = SemanticDependencyProductInput(
        package, ContentDigest.of_bytes(source.manifest_body), (), demand, (), intent,
    )
    _validate(joined)
    return MetaProviderSemanticInputs(
        source, dependency_input, joined.expected.operation_ref, joined.expected.use_ref,
    )


async def test_original_distinct_names_assembler_to_local_engine(tmp_path, record_property):
    started = time.perf_counter()
    async with _original_assembly(tmp_path) as joined:
        assembly_elapsed = time.perf_counter() - started
        payload = _diagnostic_engine_input(joined)
        outer_root = joined.original.root / "workspaces/network/modules/main/package"
        source = payload.source_closure
        assert source.package_root == str(outer_root / "structure")
        assert tuple((row.relative_path, row.canonical_body) for row in source.sources) == AUTHORED_SOURCES
        assert source.source_epoch_ref == joined.source_origin.source_identity_digest.value
        assert tuple(row.source_occurrence_ref for row in source.sources) == tuple(
            row.occurrence_ref for row in joined.source_origin.sources
            if row.source.coordinate.role == "authored_source"
        )
        engine_started = time.perf_counter()
        engine = create_meta_engine_session_v2()
        try:
            _validate(joined)
            head = await engine.execute(payload)
            _validate(joined)
            completion = engine.completion(head)
            _validate(joined)
            assert completion.result.transition is not None
            body = completion.body_for(completion.result.transition.result)
            assert body.coordinate.contract == META_PACKAGE_RESULT_V2_REF
            value = decode_meta_aware_package_portable_result_v2(body.canonical_body)
            assert value.package_name == joined.expected.package_identity.package_name
            assert value.direct_dependencies == ()
            assert any(row.canonical_body == joined.result.canonical_body for row in completion.bodies)
            _validate(joined)
        finally:
            engine.close()
        engine_elapsed = time.perf_counter() - engine_started
        _validate(joined)
        joined.original.issuer._exclusion.check_live()
        inputs.validate_registered_semantic_input_result(
            joined.original.host, joined.selection_registration,
            source_admission=joined.original.selected, expected=joined.selection_expected,
            result=joined.selected_result,
        )
    with pytest.raises(REFUSALS):
        _validate(joined)
    elapsed = time.perf_counter() - started
    for key, value in (
        ("original_assembly_seconds", assembly_elapsed),
        ("local_engine_and_validation_seconds", engine_elapsed),
        ("original_source_to_local_engine_seconds", elapsed),
    ):
        record_property(key, value)
        print(f"{key}={value:.6f}")


@pytest.mark.parametrize("poison", ["result_copy", "source", "selection_release", "parent", "cancel"])
async def test_original_assembly_lifetime_refusal(tmp_path, poison):
    joined = None
    refused = False
    terminal_exit = False
    try:
        async with _original_assembly(tmp_path) as joined:
            if poison == "result_copy":
                with pytest.raises(REFUSALS):
                    _validate(joined, result=replace(joined.result))
            elif poison == "source":
                path = joined.original.root / "workspaces/network/modules/main/package/structure/aware/a.aware"
                before = path.read_bytes()
                path.write_bytes(b"class Changed {}\n")
                try:
                    with pytest.raises(REFUSALS):
                        _diagnostic_engine_input(joined)
                finally:
                    path.write_bytes(before)
                with pytest.raises(REFUSALS):
                    _validate(joined)
            elif poison == "selection_release":
                inputs.release_registered_semantic_input_result(
                    joined.original.host, joined.selection_registration,
                    source_admission=joined.original.selected,
                    expected=joined.selection_expected, result=joined.selected_result,
                )
                with pytest.raises(REFUSALS):
                    _diagnostic_engine_input(joined)
            elif poison == "parent":
                joined.original.parent.close()
                with pytest.raises(REFUSALS):
                    _diagnostic_engine_input(joined)
            else:
                raise asyncio.CancelledError
            refused = True
    except asyncio.CancelledError:
        assert poison == "cancel"
    except (SourceObservationUnavailable, WorkspaceCommandLifetimeUnavailable):
        # The original input scopes revalidate on normal exit. A known
        # terminal rejection must propagate there too, after releasing inputs.
        assert refused
        assert poison in {"source", "selection_release", "parent"}
        terminal_exit = True
    assert joined is not None
    assert terminal_exit == (poison in {"source", "selection_release", "parent"})
    assert not joined.original.issuer._pre_request_inputs
    with pytest.raises(REFUSALS):
        _validate(joined)
