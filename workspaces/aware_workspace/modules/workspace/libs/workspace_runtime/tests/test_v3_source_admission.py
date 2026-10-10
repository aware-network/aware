"""V3 source-to-catalog mechanics over one original Workspace command.

The Code completion reader is substituted only in this isolated unit. The
integrated Code authority execution and catalog publication are separate gates.
"""

import os
from contextlib import asynccontextmanager, closing
from dataclasses import replace
from types import SimpleNamespace

import pytest
from aware_code_retained_registry_policy_runtime import authority_execution
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    SemanticContractRef,
    SemanticInputPackageIdentity,
    SemanticInputProductionExpectation,
    SemanticInputSourceCoordinate,
    SemanticValueCoordinate,
    TerminalStatus,
    encode_semantic_candidate_listing,
)
from aware_code_semantic_contract_runtime.portable_semantic_package_authority import (
    CodeEmptySemanticMetadata,
    CodePortableCodePackage,
    CodePortableSemanticContract,
    CodePortableSemanticPackage,
    create_portable_semantic_package_authority,
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
from aware_code_semantic_contract_runtime.runtime import (
    ExecutionCompletion,
    SemanticBody,
)
from aware_code_semantic_contract_runtime.semantic_candidates import (
    SEMANTIC_CANDIDATE_LISTING_REF,
)
from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime import direct_command_composition as composition
from aware_workspace_runtime.materialization_graph_planner import (
    _validate_state_bound_head_occurrence,
)
from aware_workspace_runtime.observed_semantic_issuers import (
    WorkspacePackageContextAdmission,
)
from aware_workspace_runtime.semantic_dependency_graph import (
    WorkspaceSemanticPackageHeadObservation,
)
from aware_workspace_runtime.semantic_materialization_publication import (
    WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V4,
    WorkspaceMaterializationPackageOccurrenceV4,
)
from aware_workspace_runtime.source_admission import (
    WorkspaceOwnerDefinedSourceAdmission,
    WorkspaceV3OwnerDefinedSourceAdmissionRuntime,
)
from aware_workspace_runtime.source_admission_catalog import (
    WorkspaceV3GraphSourceCorrespondence,
    capture_v3_graph_source_correspondence,
    derive_owner_defined_catalog_entry,
)
from test_declaration_scope_admission import fixture
from test_materialization_declaration_selection import (
    _author_v3_repository,
    _selection,
)


@asynccontextmanager
async def _pre_request_source(
    tmp_path, *, ontology=False, meta=False, authored_sources=None, selected_package_kind=None,
    with_local_provider=False,
):
    async with fixture(tmp_path) as (root, parent, observer, issuer, _, expectation):
        _author_v3_repository(root)
        if with_local_provider:
            from test_observed_semantic_issuers import PROVIDER

            for scope in ("kernel", "network"):
                module = root / f"workspaces/{scope}/modules/main"
                manifest = module / "aware.module.toml"
                manifest.write_text(manifest.read_text() + PROVIDER)
                provider = module / "provider"
                provider.mkdir()
                (provider / "pyproject.toml").write_text('[project]\nname="fixture-provider"\n')
        if selected_package_kind is not None:
            module = root / "workspaces/network/modules/main/aware.module.toml"
            original = '[[packages]]\nid="example"\nkind="example"'
            assert module.read_text().count(original) == 1
            module.write_text(module.read_text().replace(
                original, f'[[packages]]\nid="example"\nkind="{selected_package_kind}"',
            ))
        package = root / "workspaces/network/modules/main/package"
        (package / "a.bin").write_bytes(b"same bytes")
        (package / "b.bin").write_bytes(b"same bytes")
        if ontology:
            (package / "aware.example.toml").write_bytes(
                b'aware_ontology = 1\n[ontology]\npackage_name = "network-example"\n'
                b'fqn_prefix = "aware_fixture"\nsource_manifest = "structure/aware.toml"\n'
            )
            (package / "structure").mkdir()
            (package / "structure/aware.toml").write_bytes(
                b'[package]\nname = "network-example"\nkind = "ontology"\n'
            )
            if meta:
                (package / "structure/aware.toml").write_bytes(
                    b'aware=1\n[package]\npackage_name="network-example"\n'
                    b'fqn_prefix="aware_fixture"\nkind="ontology"\n'
                    b'[build]\nenvironment_slug="fixture"\nsources_dir="aware"\n'
                )
                (package / "structure/aware").mkdir()
                rows = authored_sources if authored_sources is not None else (
                    ("a.aware", b"same authored bytes"),
                    ("b.aware", b"same authored bytes"),
                )
                for name, body in rows:
                    (package / "structure/aware" / name).write_bytes(body)
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
        contract = SemanticContractRef("fixture.raw-source.v1", "1", ContentDigest.of_bytes(b"raw"))
        coordinates = tuple(SemanticInputSourceCoordinate(
            body.relative_path, SemanticValueCoordinate(
                "raw_source", contract, body.body_ref, ContentDigest(body.content_digest), body.size_bytes,
            ),
        ) for body in evidence.bodies)
        yield root, parent, issuer, selected, coordinates


def _register_pre_request_producer(host, issuer, expected, producer, output):
    from aware_code_semantic_contract_runtime import (
        semantic_input_producer as producers,
    )
    from aware_code_semantic_contract_runtime.contracts import (
        SemanticConfigurationCoordinate,
        SemanticImplementationCoordinate,
    )

    return producers.register_semantic_input_producer(
        host,
        declaration=producers.SemanticInputProducerDeclaration(
            "fixture.pre-request", "fixture.pre-request.v1",
            SemanticImplementationCoordinate("fixture/producer", ContentDigest.of_bytes(b"implementation")),
            SemanticConfigurationCoordinate("fixture.configuration", ContentDigest.of_bytes(b"configuration")),
            (producers.SemanticInputSourceContract("raw_source", expected.source_coordinates[0].coordinate.contract),),
            "prepared", output.coordinate.contract,
            context_contracts=tuple(producers.SemanticInputContextContract(
                body.coordinate.role, body.coordinate.contract,
            ) for body in expected.context_bodies),
        ), producer=producer, validator=issuer,
        validator_entrance=issuer.validate_semantic_input_source,
        context_validator_entrance=issuer.validate_semantic_input_context,
        reader=issuer, reader_entrance=issuer.read_semantic_input_sources,
    )


async def test_local_read_participants_keep_original_parent_and_path_occurrences(tmp_path):
    async with _pre_request_source(tmp_path, with_local_provider=True) as (
        _, _, issuer, selected, coordinates,
    ):
        record = issuer._selected_record(selected)
        view = issuer.read_selected_participant_view(record.declaration, selected)
        assert {item.package_id for item in view.participants} == {"example", "provider"}
        with issuer.original_pre_request_input(
            selected, use_ref="local-read-parent", stage="pre_request", source_coordinates=coordinates,
        ) as expected:
            assert expected.operation_identity is issuer._exclusion._parent
            sources = issuer.read_semantic_input_sources(selected, expected=expected)
            equal = [body for body in sources if body.canonical_body == b"same bytes"]
            assert len(equal) == 2
            assert {body.source.relative_path for body in equal} == {"a.bin", "b.bin"}
            assert equal[0].source.coordinate.value_ref == equal[1].source.coordinate.value_ref
            assert equal[0].source != equal[1].source  # Paths preserve distinct occurrences.
        with pytest.raises(SourceObservationUnavailable):
            issuer.validate_semantic_input_source(selected, expected=expected)


async def test_original_pre_request_context_runs_through_code_producer(tmp_path):
    from aware_code_semantic_contract_runtime import (
        semantic_input_producer as producers,
    )
    from aware_code_semantic_contract_runtime.contracts import (
        ContractViolation,
    )
    from aware_code_semantic_contract_runtime.runtime import SemanticBody

    async with _pre_request_source(tmp_path) as (_, _, issuer, selected, sources):
        with issuer.original_pre_request_input(
            selected, use_ref="pre-request-positive", stage="pre_request",
            source_coordinates=sources,
            context_contracts=(producers.SemanticInputContextContract(
                "package_context", PACKAGE_CONTEXT_INPUT_REF,
            ), producers.SemanticInputContextContract(
                "source_inventory", SEMANTIC_CANDIDATE_LISTING_REF,
            )),
        ) as expected:
            assert expected.operation_identity is issuer._exclusion._parent
            assert expected.operation_ref == "operation"
            assert expected.package_identity.package_name == "network-example"
            seen = []
            output = SemanticBody(_coordinate("prepared", b"prepared"), b"prepared")

            async def produce(value):
                assert value.context_bodies == expected.context_bodies
                assert value.sources[0].source is not expected.source_coordinates[0]
                assert not hasattr(value, "source_identity")
                seen.append(value)
                return output

            with closing(producers.SemanticInputProducerHost()) as host:
                registration = _register_pre_request_producer(host, issuer, expected, produce, output)
                assert await producers.execute_registered_semantic_input(
                    host, registration, source_admission=selected, expected=expected,
                ) == output
                assert len(seen) == 1
                shared = [body for body in seen[0].sources if body.source.relative_path in {"a.bin", "b.bin"}]
                assert len(shared) == 2
                assert shared[0].source.coordinate.value_ref == shared[1].source.coordinate.value_ref
                with pytest.raises(ContractViolation, match="consumed"):
                    await producers.execute_registered_semantic_input(
                        host, registration, source_admission=selected, expected=expected,
                    )
        with pytest.raises(SourceObservationUnavailable, match="original_pre_request"):
            issuer.validate_semantic_input_context(selected, expected=expected)
        with (
            pytest.raises(SourceObservationUnavailable, match="replayed"),
            issuer.original_pre_request_input(
            selected, use_ref="pre-request-positive", stage="pre_request", source_coordinates=sources,
        ),
        ):
            pytest.fail("a completed association was reused")
        assert not issuer._pre_request_inputs


@pytest.mark.parametrize("change", ["source", "context", "parent", "cancel"])
async def test_pre_request_code_rejects_changes_across_awaited_producer(tmp_path, change):
    import asyncio

    from aware_code_semantic_contract_runtime import (
        semantic_input_producer as producers,
    )
    from aware_code_semantic_contract_runtime.contracts import ContractViolation
    from aware_code_semantic_contract_runtime.runtime import SemanticBody
    from aware_workspace_runtime.command_lifetime import (
        WorkspaceCommandLifetimeUnavailable,
    )

    async with _pre_request_source(tmp_path) as (root, parent, issuer, selected, sources):
        seen = []
        with (
            pytest.raises((SourceObservationUnavailable, ContractViolation, WorkspaceCommandLifetimeUnavailable, asyncio.CancelledError)),
            issuer.original_pre_request_input(
            selected, use_ref="awaited-mutation", stage="pre_request", source_coordinates=sources,
            context_contracts=(producers.SemanticInputContextContract("package_context", PACKAGE_CONTEXT_INPUT_REF),),
        ) as expected,
        ):
            output = SemanticBody(_coordinate("prepared", b"prepared"), b"prepared")

            async def produce(value):
                seen.append(value)
                await asyncio.sleep(0)
                if change == "source":
                    (root / "workspaces/network/modules/main/package/a.bin").write_bytes(b"changed")
                elif change == "context":
                    object.__setattr__(value.context_bodies[0], "canonical_body", b"changed")
                elif change == "parent":
                    parent.close()
                else:
                    raise asyncio.CancelledError
                return output

            with closing(producers.SemanticInputProducerHost()) as host:
                registration = _register_pre_request_producer(host, issuer, expected, produce, output)
                await producers.execute_registered_semantic_input(
                    host, registration, source_admission=selected, expected=expected,
                )
        assert len(seen) == 1
        assert not issuer._pre_request_inputs


async def test_pre_request_registered_rejection_cannot_be_restored(tmp_path):
    async with _pre_request_source(tmp_path) as (_, _, issuer, selected, sources):
        with (
            pytest.raises(SourceObservationUnavailable, match="original_pre_request"),
            issuer.original_pre_request_input(
            selected, use_ref="restoration", stage="pre_request", source_coordinates=sources,
        ) as expected,
        ):
            original = expected.operation_identity
            object.__setattr__(expected, "operation_identity", object())
            with pytest.raises(SourceObservationUnavailable, match="original_pre_request"):
                issuer.validate_semantic_input_context(selected, expected=expected)
            object.__setattr__(expected, "operation_identity", original)
            with pytest.raises(SourceObservationUnavailable, match="original_pre_request"):
                issuer.read_semantic_input_sources(selected, expected=expected)
        assert not issuer._pre_request_inputs


async def test_pre_request_restamped_source_retires_without_foreign_behavior(tmp_path):
    calls = []

    class HostileSource:
        __slots__ = ()

        def __hash__(self):
            calls.append("hash")
            raise AssertionError("foreign source hash invoked")

        def __eq__(self, other):
            calls.append("equality")
            raise AssertionError("foreign source equality invoked")

    async with _pre_request_source(tmp_path) as (_, _, issuer, selected, sources):
        original_type = type(selected)
        try:
            with (
                pytest.raises(SourceObservationUnavailable, match="foreign_selected_source"),
                issuer.original_pre_request_input(
                    selected, use_ref="restamped-source", stage="pre_request", source_coordinates=sources,
                ) as expected,
            ):
                object.__setattr__(selected, "__class__", HostileSource)
                issuer.validate_semantic_input_context(selected, expected=expected)
        finally:
            object.__setattr__(selected, "__class__", original_type)
        assert not calls
        assert not issuer._pre_request_inputs
        with pytest.raises(SourceObservationUnavailable, match="original_pre_request"):
            issuer.read_semantic_input_sources(selected, expected=expected)


@pytest.mark.parametrize("change", ["source", "declaration", "parent", "context", "operation", "release"])
async def test_pre_request_currentness_and_mutation_are_terminal(tmp_path, change):
    from aware_code_semantic_contract_runtime import (
        semantic_input_producer as producers,
    )

    async with _pre_request_source(tmp_path) as (root, parent, issuer, selected, sources):
        from aware_code_semantic_contract_runtime.contracts import ContractViolation
        from aware_workspace_runtime.command_lifetime import (
            WorkspaceCommandLifetimeUnavailable,
        )

        entered = False
        with (
            pytest.raises((SourceObservationUnavailable, ContractViolation, WorkspaceCommandLifetimeUnavailable)),
            issuer.original_pre_request_input(
            selected, use_ref="pre-request-mutation", stage="pre_request",
            source_coordinates=sources,
            context_contracts=(producers.SemanticInputContextContract("package_context", PACKAGE_CONTEXT_INPUT_REF),),
        ) as expected,
        ):
            entered = True
            if change == "source":
                (root / "workspaces/network/modules/main/package/a.bin").write_bytes(b"changed")
            elif change == "declaration":
                (root / "workspaces/kernel/modules/main/aware.module.toml").write_bytes(b"changed")
            elif change == "parent":
                parent.close()
            elif change == "context":
                object.__setattr__(expected.context_bodies[0], "canonical_body", b"changed")
            elif change == "operation":
                object.__setattr__(expected, "operation_identity", object())
            else:
                issuer.release_selected_package_source(selected)
            issuer.validate_semantic_input_context(selected, expected=expected)
        assert entered
        assert not issuer._pre_request_inputs


async def test_pre_request_refuses_unobserved_context_path_and_copied_expectation(tmp_path):
    from aware_code_semantic_contract_runtime import (
        semantic_input_producer as producers,
    )

    async with _pre_request_source(tmp_path) as (_, _, issuer, selected, sources):
        foreign = SemanticContractRef("fixture.owner-scope.v1", "1", ContentDigest.of_bytes(b"owner"))
        with (
            pytest.raises(SourceObservationUnavailable, match="context_unavailable"),
            issuer.original_pre_request_input(
            selected, use_ref="unobserved-context", stage="pre_request", source_coordinates=sources,
            context_contracts=(producers.SemanticInputContextContract("scope", foreign),),
        ),
        ):
            pytest.fail("portable unknown context acquired an original source")
        # Nested packages are excluded even though their files exist on disk.
        wrong = (replace(sources[0], relative_path="child/aware.example.toml"),)
        with (
            pytest.raises(SourceObservationUnavailable, match="source_differs"),
            issuer.original_pre_request_input(
            selected, use_ref="wrong-path", stage="pre_request", source_coordinates=wrong,
        ),
        ):
            pytest.fail("unobserved nested package entered the reader")
        with issuer.original_pre_request_input(
            selected, use_ref="original-expectation", stage="pre_request", source_coordinates=sources,
        ) as expected:
            with pytest.raises(SourceObservationUnavailable, match="original_pre_request"):
                issuer.validate_semantic_input_source(selected, expected=replace(expected))
            issuer.validate_semantic_input_context(selected, expected=expected)
        assert not issuer._pre_request_inputs


async def test_pre_request_cancellation_releases_input_without_closing_borrowed_parent(tmp_path):
    import asyncio

    async with _pre_request_source(tmp_path) as (_, parent, issuer, selected, sources):
        with (
            pytest.raises(asyncio.CancelledError),
            issuer.original_pre_request_input(
            selected, use_ref="cancelled", stage="pre_request", source_coordinates=sources,
        ) as expected,
        ):
            raise asyncio.CancelledError
        assert not issuer._pre_request_inputs
        issuer._exclusion.check_live()
        assert parent is issuer._exclusion._runtime
        with pytest.raises(SourceObservationUnavailable, match="original_pre_request"):
            issuer.read_semantic_input_sources(selected, expected=expected)


@asynccontextmanager
async def _original_selection(
    tmp_path, *, poison=None, ontology=False, meta=False, authored_sources=None,
    selected_package_kind=None,
):
    from contextlib import ExitStack

    from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
    from aware_code_semantic_contract_runtime.contracts import (
        SemanticConfigurationCoordinate,
        SemanticImplementationCoordinate,
    )
    from aware_code_semantic_contract_runtime.source_selection import (
        SOURCE_SELECTION_REF,
        SemanticSelectedSource,
        SemanticSourceSelection,
        source_selection_body,
    )

    async with _pre_request_source(
        tmp_path, ontology=ontology, meta=meta, authored_sources=authored_sources,
        selected_package_kind=selected_package_kind,
    ) as (
        root, parent, issuer, selected, sources,
    ):
        inner_ref = SemanticContractRef("fixture.raw-inner", "1", ContentDigest.of_bytes(b"inner"))
        if meta:
            from aware_meta_source_preparation_provider.raw_manifest import (
                RAW_META_MANIFEST_REF,
            )

            inner_ref = RAW_META_MANIFEST_REF
        contracts = (inputs.SemanticInputSourceContract("selected_raw", inner_ref),)
        with ExitStack() as stack:
            host_closed = False

            def close_host():
                nonlocal host_closed
                if not host_closed:
                    host.close()
                    host_closed = True

            if ontology:
                from aware_ontology_meta_preparation_provider import (
                    source_relation as owner,
                )
                from aware_ontology_meta_preparation_provider.profile import (
                    OntologySourcePreparation,
                )

                factory = OntologySourcePreparation(inner_ref)
                raw = next(s for s in sources if s.relative_path == "aware.example.toml")
                coordinates = (replace(raw, coordinate=replace(
                    raw.coordinate, role="outer_manifest", contract=owner.RAW_OUTER_REF,
                )),)
                before = stack.enter_context(issuer.original_pre_request_input(
                    selected, use_ref="original-relation", stage=owner.RELATION_STAGE,
                    source_coordinates=coordinates,
                    context_contracts=factory.relation_declaration.context_contracts,
                ))
                expected = stack.enter_context(issuer.original_pre_request_input(
                    selected, use_ref="original-selection", stage=owner.SELECTION_STAGE,
                    source_coordinates=coordinates,
                    context_contracts=factory.projection_declaration.ordinary.context_contracts,
                ))
                host = inputs.SemanticInputProducerHost()
                stack.callback(close_host)
                origin = {"validator": issuer, "validator_entrance": issuer.validate_semantic_input_source,
                          "reader": issuer, "reader_entrance": issuer.read_semantic_input_sources,
                          "context_validator_entrance": issuer.validate_semantic_input_context,
                          "retain_result": True}
                predecessor = inputs.register_semantic_input_producer(
                    host, declaration=factory.relation_declaration,
                    producer=factory.produce_relation, **origin,
                )
                registration = inputs.register_joined_semantic_input_producer(
                    host, declaration=factory.projection_declaration,
                    producer=factory.project_sources, **origin,
                )
                join = inputs.open_semantic_input_role_join(
                    host, joined_registration=registration, joined_expected=expected,
                    source_admission=selected,
                    predecessors=(inputs.SemanticInputRoleJoinPredecessor(predecessor, before),),
                )
                predecessor_result = await inputs.execute_registered_semantic_input(
                    host, predecessor, source_admission=selected, expected=before,
                )
                result = await inputs.execute_registered_joined_semantic_input(
                    host, registration, role_join=join, source_admission=selected, expected=expected,
                )
                contracts = (inputs.SemanticInputSourceContract("inner_manifest", inner_ref),)
            else:
                expected = stack.enter_context(issuer.original_pre_request_input(
                    selected, use_ref="original-selection", stage="fixture_selection",
                    source_coordinates=sources,
                ))
                host = inputs.SemanticInputProducerHost()
                stack.callback(close_host)
                context = issuer.inspect_inputs(selected)[0]
                selection = SemanticSourceSelection(
                    context.package, context.source_identity_digest, expected.input_digest, (),
                    tuple(SemanticSelectedSource("selected_raw", inner_ref, s.relative_path,
                                                 s.coordinate.digest)
                          for s in sources if s.relative_path in {"a.bin", "b.bin"}),
                )
                if poison is not None:
                    selection = poison(selection)

                async def produce(_):
                    return source_selection_body(selection, role="selection")

                registration = inputs.register_semantic_input_producer(
                    host, declaration=inputs.SemanticInputProducerDeclaration(
                        "fixture.selection", "fixture.selection.v1",
                        SemanticImplementationCoordinate("fixture/selection", ContentDigest.of_bytes(b"code")),
                        SemanticConfigurationCoordinate("fixture.config", ContentDigest.of_bytes(b"config")),
                        (inputs.SemanticInputSourceContract("raw_source", sources[0].coordinate.contract),),
                        "selection", SOURCE_SELECTION_REF,
                    ), producer=produce, validator=issuer,
                    validator_entrance=issuer.validate_semantic_input_source,
                    reader=issuer, reader_entrance=issuer.read_semantic_input_sources,
                    retain_result=True,
                )
                result = await inputs.execute_registered_semantic_input(
                    host, registration, source_admission=selected, expected=expected,
                )
            arguments = {"host": host, "registration": registration, "selection_expected": expected,
                         "result": result, "source_contracts": contracts}
            yield SimpleNamespace(root=root, parent=parent, issuer=issuer, selected=selected,
                                  host=host, registration=registration, expected=expected,
                                  result=result, arguments=arguments, close_host=close_host,
                                  predecessor=predecessor if ontology else None,
                                  predecessor_expected=before if ontology else None,
                                  predecessor_result=predecessor_result if ontology else None)


@pytest.mark.parametrize("ontology", [False, True])
async def test_selected_input_reads_original_owner_selection(tmp_path, ontology):
    from aware_code_semantic_contract_runtime import semantic_input_producer as inputs

    async with _original_selection(tmp_path, ontology=ontology) as f:
        with f.issuer.original_selected_source_input(
            f.selected, use_ref="inner-read", stage="fixture_inner", **f.arguments,
        ) as expected:
            bodies = f.issuer.read_semantic_input_sources(f.selected, expected=expected)
            assert expected.operation_identity is f.expected.operation_identity
            assert expected.package_identity == f.expected.package_identity
            if ontology:
                assert len(bodies) == 1
                assert bodies[0].source.relative_path == "structure/aware.toml"
                assert bodies[0].canonical_body == b'[package]\nname = "network-example"\nkind = "ontology"\n'
            else:
                assert [b.source.relative_path for b in bodies] == ["a.bin", "b.bin"]
                assert bodies[0].canonical_body == bodies[1].canonical_body == b"same bytes"
                assert bodies[0].source.coordinate.value_ref == bodies[1].source.coordinate.value_ref
                assert bodies[0].source.coordinate.digest == ContentDigest.of_bytes(b"same bytes")
                assert bodies[0].source.coordinate.size_bytes == len(b"same bytes")
        # This binding borrows the Code origin and parent; both remain live.
        inputs.validate_registered_semantic_input_result(
            f.host, f.registration, source_admission=f.selected, expected=f.expected, result=f.result,
        )
        f.issuer._exclusion.check_live()
        with pytest.raises(SourceObservationUnavailable):
            f.issuer.read_semantic_input_sources(f.selected, expected=expected)


@pytest.mark.parametrize("poison", ["epoch", "missing", "digest", "excluded", "empty", "role", "contract"])
async def test_selected_input_refuses_nonmembers_and_wrong_declared_inputs(tmp_path, poison):
    def corrupt(selection):
        if poison == "epoch":
            return replace(selection, source_identity_digest=ContentDigest.of_bytes(b"other epoch"))
        if poison == "empty":
            return replace(selection, sources=())
        source = selection.sources[0]
        if poison == "missing":
            source = replace(source, relative_path="missing.bin")
        elif poison == "excluded":
            source = replace(source, relative_path="nested/body.bin")
        elif poison == "digest":
            source = replace(source, content_digest=ContentDigest.of_bytes(b"wrong"))
        elif poison == "role":
            source = replace(source, role="other")
        else:
            source = replace(source, contract=SemanticContractRef("wrong", "1", ContentDigest.of_bytes(b"wrong")))
        return replace(selection, sources=(source,))

    async with _original_selection(tmp_path, poison=corrupt) as f:
        with pytest.raises(SourceObservationUnavailable, match="selected_input"):
            with f.issuer.original_selected_source_input(
                f.selected, use_ref="refused-inner", stage="fixture_inner", **f.arguments,
            ):
                pytest.fail("Unobserved selection reached inner consumer")


@pytest.mark.parametrize("change", ["release", "host", "registration", "predecessor", "source", "parent", "cancel"])
async def test_selected_input_origin_expiry_and_cleanup(tmp_path, change):
    import asyncio

    from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
    from aware_code_semantic_contract_runtime.contracts import ContractViolation
    from aware_workspace_runtime.command_lifetime import (
        WorkspaceCommandLifetimeUnavailable,
    )

    entered = False
    with pytest.raises((ContractViolation, SourceObservationUnavailable,
                        WorkspaceCommandLifetimeUnavailable, asyncio.CancelledError)):
        async with _original_selection(tmp_path, ontology=change == "predecessor") as f:
            with f.issuer.original_selected_source_input(
                f.selected, use_ref="expired-inner", stage="fixture_inner", **f.arguments,
            ) as expected:
                entered = True
                if change == "release":
                    inputs.release_registered_semantic_input_result(
                        f.host, f.registration, source_admission=f.selected,
                        expected=f.expected, result=f.result,
                    )
                elif change == "host":
                    f.close_host()
                elif change == "registration":
                    inputs.close_semantic_input_producer_registration(f.host, f.registration)
                elif change == "predecessor":
                    inputs.release_registered_semantic_input_result(
                        f.host, f.predecessor, source_admission=f.selected,
                        expected=f.predecessor_expected, result=f.predecessor_result,
                    )
                elif change == "source":
                    (f.root / "workspaces/network/modules/main/package/a.bin").write_bytes(b"changed")
                elif change == "parent":
                    f.parent.close()
                else:
                    raise asyncio.CancelledError
                f.issuer.read_semantic_input_sources(f.selected, expected=expected)
    assert entered
    assert not any(item.expected is expected for item in f.issuer._pre_request_inputs.values())
    with pytest.raises((ContractViolation, SourceObservationUnavailable, WorkspaceCommandLifetimeUnavailable)):
        f.issuer.read_semantic_input_sources(f.selected, expected=expected)


@pytest.mark.parametrize("copy_field", ["result", "selection_expected"])
async def test_selected_input_requires_original_return_and_expectation(tmp_path, copy_field):
    from aware_code_semantic_contract_runtime.contracts import ContractViolation

    async with _original_selection(tmp_path) as f:
        arguments = dict(f.arguments)
        arguments[copy_field] = replace(arguments[copy_field])
        with (
            pytest.raises((ContractViolation, SourceObservationUnavailable)),
            f.issuer.original_selected_source_input(
                f.selected, use_ref="copied-inner", stage="fixture_inner", **arguments,
            ),
        ):
            pytest.fail("Copied origin reached inner consumer")


@pytest.mark.parametrize("change_during_call", [False, True])
async def test_selected_input_surrounds_next_registered_owner_call(tmp_path, change_during_call):
    import asyncio

    from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
    from aware_code_semantic_contract_runtime.contracts import (
        ContractViolation,
        SemanticConfigurationCoordinate,
        SemanticImplementationCoordinate,
    )

    reached = False
    try:
        async with _original_selection(tmp_path, ontology=True) as f:
            with f.issuer.original_selected_source_input(
                f.selected, use_ref="inner-owner", stage="fixture_inner", **f.arguments,
            ) as expected:
                output = SemanticBody(_coordinate("prepared", b"prepared"), b"prepared")

                async def produce(value):
                    nonlocal reached
                    assert value.sources[0].canonical_body.startswith(b"[package]")
                    assert not hasattr(value, "source_identity")
                    assert value.package_identity == expected.package_identity
                    reached = True
                    await asyncio.sleep(0)
                    if change_during_call:
                        (f.root / "workspaces/network/modules/main/package/structure/aware.toml").write_bytes(b"changed")
                    return output

                registration = inputs.register_semantic_input_producer(
                    f.host, declaration=inputs.SemanticInputProducerDeclaration(
                        "fixture.inner-owner", "fixture.inner-owner.v1",
                        SemanticImplementationCoordinate("fixture/inner-owner", ContentDigest.of_bytes(b"code")),
                        SemanticConfigurationCoordinate("fixture.config", ContentDigest.of_bytes(b"config")),
                        f.arguments["source_contracts"], "prepared", output.coordinate.contract,
                    ), producer=produce, validator=f.issuer,
                    validator_entrance=f.issuer.validate_semantic_input_source,
                    reader=f.issuer, reader_entrance=f.issuer.read_semantic_input_sources,
                )
                result = await inputs.execute_registered_semantic_input(
                    f.host, registration, source_admission=f.selected, expected=expected,
                )
                assert result == output
                assert not change_during_call, "Changed source reached accepted owner return"
    except (SourceObservationUnavailable, ContractViolation):
        if not change_during_call:
            raise
    assert reached


async def test_selected_input_restoration_cannot_resume_and_does_not_revoke_outer(tmp_path):
    async with _original_selection(tmp_path) as f:
        with (
            pytest.raises(SourceObservationUnavailable),
            f.issuer.original_selected_source_input(
                f.selected, use_ref="restamped-inner", stage="fixture_inner", **f.arguments,
            ) as expected,
        ):
            original = expected.operation_identity
            object.__setattr__(expected, "operation_identity", object())
            with pytest.raises(SourceObservationUnavailable):
                f.issuer.validate_semantic_input_source(f.selected, expected=expected)
            object.__setattr__(expected, "operation_identity", original)
            f.issuer.read_semantic_input_sources(f.selected, expected=expected)
        f.issuer.validate_semantic_input_source(f.selected, expected=f.expected)
        f.issuer._exclusion.check_live()


async def test_selected_input_calls_code_outside_workspace_locks(tmp_path, monkeypatch):
    from aware_workspace_runtime import declaration_scope_admission as admission

    async with _original_selection(tmp_path) as f:
        original_reader = admission.read_registered_semantic_input_source_selection
        calls = []

        def checked_reader(*args, **kwargs):
            assert not f.issuer._lock._is_owned()
            assert f.parent._guard is None
            calls.append(True)
            return original_reader(*args, **kwargs)

        monkeypatch.setattr(admission, "read_registered_semantic_input_source_selection", checked_reader)
        with f.issuer.original_selected_source_input(
            f.selected, use_ref="unlocked-inner", stage="fixture_inner", **f.arguments,
        ) as expected:
            f.issuer.read_semantic_input_sources(f.selected, expected=expected)
        assert len(calls) >= 4  # construction, admission, both read checks, scope exit


class _Validator:
    def __init__(self, context, expected):
        self.context = context
        self.expected = expected

    def validate_retained_semantic_operation_context(self, context, *, expected):
        assert context is self.context
        assert expected.operation_identity is self.expected.operation_identity
        assert expected.stage == self.expected.stage
        assert expected.package == self.expected.package


def _coordinate(role, body, contract=None):
    return SemanticValueCoordinate(
        role,
        contract or SemanticContractRef(
            f"fixture.{role}", "1", ContentDigest.of_bytes(role.encode())
        ),
        f"fixture:{role}",
        ContentDigest.of_bytes(body),
        len(body),
    )



def _source_origin_contexts():
    from aware_code_semantic_contract_runtime.semantic_input_producer import (
        SemanticInputContextContract,
    )
    from aware_code_semantic_contract_runtime.source_origin import SOURCE_ORIGIN_REF
    from aware_code_semantic_contract_runtime.source_selection import (
        SOURCE_SELECTION_REF,
    )

    return (
        SemanticInputContextContract("meta_selected_sources", SOURCE_SELECTION_REF),
        SemanticInputContextContract("package_context", PACKAGE_CONTEXT_INPUT_REF),
        SemanticInputContextContract("source_origin", SOURCE_ORIGIN_REF),
    )


async def test_original_source_origin_context_is_complete_and_detached(tmp_path):
    from aware_code_semantic_contract_runtime.source_origin import decode_source_origin
    from aware_code_semantic_contract_runtime.source_selection import (
        decode_source_selection,
    )

    async with _original_selection(tmp_path) as f:
        with f.issuer.original_selected_source_input(
            f.selected, use_ref="origin-context", stage="fixture_assembly",
            context_contracts=_source_origin_contexts(), **f.arguments,
        ) as expected:
            contexts = {b.coordinate.role: b for b in expected.context_bodies}
            origin = decode_source_origin(contexts["source_origin"].canonical_body)
            selection = decode_source_selection(contexts["meta_selected_sources"].canonical_body)
            assert origin.selection_coordinate == f.result.coordinate
            assert contexts["meta_selected_sources"].canonical_body == f.result.canonical_body
            assert origin.selection_input_digest == f.expected.input_digest
            assert origin.selection_input_digest != expected.input_digest
            assert origin.package == expected.package_identity.package
            assert origin.source_identity_digest == selection.source_identity_digest
            assert origin.occurrence.scope_key == "workspaces/network/aware.workspace.toml"
            assert origin.outer_package_root == str(f.root / "workspaces/network/modules/main/package")
            assert origin.outer_manifest.relative_path == "aware.example.toml"
            assert origin.outer_manifest.coordinate.digest == expected.package_identity.package.manifest_digest
            assert tuple(row.source for row in origin.sources) == expected.source_coordinates
            assert origin.sources[0].source.coordinate.digest == origin.sources[1].source.coordinate.digest
            assert origin.sources[0].occurrence_ref != origin.sources[1].occurrence_ref
            assert [row.source.relative_path for row in origin.sources] == ["a.bin", "b.bin"]
            f.issuer.validate_semantic_input_context(f.selected, expected=expected)
        assert not any(r.expected is expected for r in f.issuer._pre_request_inputs.values())


@pytest.mark.parametrize("contract_index", [0, 2])
async def test_source_origin_context_requires_original_selection_not_portable_body(tmp_path, contract_index):
    async with _pre_request_source(tmp_path) as (_, _, issuer, selected, sources):
        with (
            pytest.raises(SourceObservationUnavailable, match="context_unavailable"),
            issuer.original_pre_request_input(
                selected, use_ref="unissued-context", stage="fixture",
                source_coordinates=sources, context_contracts=(_source_origin_contexts()[contract_index],),
            ),
        ):
            pass
        assert not issuer._pre_request_inputs


@pytest.mark.parametrize("change", ["root_binding", "source", "context", "result", "parent", "reader"])
async def test_registered_source_origin_context_rejects_mutation_around_owner_call(tmp_path, change):
    import asyncio
    from contextlib import ExitStack, suppress

    from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
    from aware_code_semantic_contract_runtime.contracts import (
        ContractViolation,
        SemanticConfigurationCoordinate,
        SemanticImplementationCoordinate,
    )

    # Source/root loss also terminally retires the borrowed selection use.
    with suppress(SourceObservationUnavailable, ContractViolation, RuntimeError):
        async with _original_selection(tmp_path) as f:
            with ExitStack() as stack:
                with (
                    pytest.raises((SourceObservationUnavailable, ContractViolation, RuntimeError)),
                    f.issuer.original_selected_source_input(
                        f.selected, use_ref="origin-mutated", stage="fixture_assembly",
                        context_contracts=_source_origin_contexts(), **f.arguments,
                    ) as expected,
                ):
                    output = SemanticBody(_coordinate("assembled", b"assembled"), b"assembled")

                    async def produce(value):
                        await asyncio.sleep(0)
                        if change == "root_binding":
                            observer = f.issuer._source
                            binding = observer._session.binding
                            observer._session.binding = replace(binding)
                            stack.callback(setattr, observer._session, "binding", binding)
                        elif change == "source":
                            path = f.root / "workspaces/network/modules/main/package/a.bin"
                            body = path.read_bytes()
                            path.write_bytes(b"changed")
                            stack.callback(path.write_bytes, body)
                        elif change == "context":
                            body = expected.context_bodies[-1]
                            original = body.canonical_body
                            object.__setattr__(body, "canonical_body", b"changed")
                            stack.callback(object.__setattr__, body, "canonical_body", original)
                        elif change == "result":
                            original = f.result.canonical_body
                            object.__setattr__(f.result, "canonical_body", b"changed")
                            stack.callback(object.__setattr__, f.result, "canonical_body", original)
                        elif change == "reader":
                            observer = f.issuer._source
                            observer.read_selected_package_location = lambda *_: "/foreign"
                            stack.callback(delattr, observer, "read_selected_package_location")
                        else:
                            f.parent.close()
                        return output

                    reg = inputs.register_semantic_input_producer(
                        f.host,
                        declaration=inputs.SemanticInputProducerDeclaration(
                            "fixture.assembly", "fixture.assembly.v1",
                            SemanticImplementationCoordinate("fixture/assembly", ContentDigest.of_bytes(b"code")),
                            SemanticConfigurationCoordinate("fixture.config", ContentDigest.of_bytes(b"config")),
                            f.arguments["source_contracts"], "assembled", output.coordinate.contract,
                            context_contracts=_source_origin_contexts(),
                        ),
                        producer=produce, validator=f.issuer,
                        validator_entrance=f.issuer.validate_semantic_input_source,
                        context_validator_entrance=f.issuer.validate_semantic_input_context,
                        reader=f.issuer, reader_entrance=f.issuer.read_semantic_input_sources,
                        retain_result=True,
                    )
                    await inputs.execute_registered_semantic_input(
                        f.host, reg, source_admission=f.selected, expected=expected,
                    )
                stack.close()
                with pytest.raises((SourceObservationUnavailable, RuntimeError)):
                    f.issuer.validate_semantic_input_context(f.selected, expected=expected)
                assert not any(r.expected is expected for r in f.issuer._pre_request_inputs.values())

async def test_real_ontology_and_meta_selection_produce_original_engine_context(tmp_path):
    from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
    from aware_code_semantic_contract_runtime.contracts import (
        ContractViolation,
        SemanticConfigurationCoordinate,
        SemanticImplementationCoordinate,
    )
    from aware_code_semantic_contract_runtime.source_origin import decode_source_origin
    from aware_meta_source_preparation_provider import MetaSourcePreparation
    from aware_meta_source_preparation_provider.raw_manifest import (
        RAW_META_MANIFEST_REF,
        RAW_META_SOURCE_REF,
    )

    async with _original_selection(tmp_path, ontology=True, meta=True) as f:
        owner = MetaSourcePreparation()
        with f.issuer.original_selected_source_input(
            f.selected, use_ref="real-meta-selection", stage="meta_authored_source_selection",
            context_contracts=owner.declaration.context_contracts, **f.arguments,
        ) as selection_expected:
            origin = {"validator": f.issuer, "validator_entrance": f.issuer.validate_semantic_input_source,
                      "reader": f.issuer, "reader_entrance": f.issuer.read_semantic_input_sources,
                      "context_validator_entrance": f.issuer.validate_semantic_input_context,
                      "retain_result": True}
            meta_reg = inputs.register_semantic_input_producer(
                f.host, declaration=owner.declaration, producer=owner.produce_sources, **origin,
            )
            selected_result = await inputs.execute_registered_semantic_input(
                f.host, meta_reg, source_admission=f.selected, expected=selection_expected,
            )
            contracts = (inputs.SemanticInputSourceContract("authored_source", RAW_META_SOURCE_REF),
                         inputs.SemanticInputSourceContract("inner_manifest", RAW_META_MANIFEST_REF))
            with f.issuer.original_selected_source_input(
                f.selected, host=f.host, registration=meta_reg,
                selection_expected=selection_expected, result=selected_result,
                source_contracts=contracts, context_contracts=_source_origin_contexts(),
                use_ref="assembled-from-originals", stage="fixture_assembly",
            ) as assembly_expected:
                seen = []
                output = SemanticBody(_coordinate("assembled", b"admitted inputs"), b"admitted inputs")

                async def assembler(value):
                    seen.append(value)
                    return output

                reg = inputs.register_semantic_input_producer(
                    f.host, declaration=inputs.SemanticInputProducerDeclaration(
                        "fixture.assembly", "fixture.assembly.v1",
                        SemanticImplementationCoordinate("fixture/assembly", ContentDigest.of_bytes(b"code")),
                        SemanticConfigurationCoordinate("fixture.config", ContentDigest.of_bytes(b"config")),
                        contracts, "assembled", output.coordinate.contract,
                        context_contracts=_source_origin_contexts(),
                    ), producer=assembler, **origin,
                )
                result = await inputs.execute_registered_semantic_input(
                    f.host, reg, source_admission=f.selected, expected=assembly_expected,
                )
                inputs.validate_registered_semantic_input_result(
                    f.host, reg, source_admission=f.selected, expected=assembly_expected, result=result,
                )
                value = seen[0]
                location = decode_source_origin(next(b.canonical_body for b in value.context_bodies
                                                     if b.coordinate.role == "source_origin"))
                assert location.outer_manifest.relative_path == "aware.example.toml"
                assert location.outer_manifest.coordinate.contract.key == "aware.ontology.raw-package-manifest.v1"
                assert location.selection_coordinate == selected_result.coordinate
                assert location.selection_input_digest == selection_expected.input_digest
                assert [row.source.relative_path for row in location.sources] == [
                    "structure/aware.toml", "structure/aware/a.aware", "structure/aware/b.aware",
                ]
                assert tuple(row.source for row in location.sources) == tuple(s.source for s in value.sources)
                assert location.sources[1].occurrence_ref != location.sources[2].occurrence_ref
                assert value.sources[1].canonical_body == value.sources[2].canonical_body == b"same authored bytes"
                assert assembly_expected.package_identity == f.expected.package_identity
                assert location.outer_package_root == str(f.root / "workspaces/network/modules/main/package")
            with pytest.raises((SourceObservationUnavailable, ContractViolation)):
                inputs.validate_registered_semantic_input_result(
                    f.host, reg, source_admission=f.selected, expected=assembly_expected, result=result,
                )


def _expected(issuer, selected):
    package, inventory = issuer.inspect_inputs(selected)
    binding = issuer.read_selected_package_source(selected)
    manifest = issuer._source.read_selected_package(
        issuer._selected_record(selected).observation,
        relative_path=package.manifest_relative_path,
    )
    return RetainedSemanticAdmissionExpectation(
        runtime=object(),
        generation_identity=object(),
        operation_identity=object(),
        process_id=os.getpid(),
        selected_provider_registration=object(),
        stage="authority_derivation",
        profile=SimpleNamespace(
            profile_ref="fixture.authority",
            operation_kinds=("materialize",),
            terminal_result_role="package_authority",
            terminal_effect_role="effect",
            terminal_output_roles=(),
        ),
        provider_declaration="fixture.provider",
        binding="fixture.binding",
        package=package.package,
        source_identity_digest=package.source_identity_digest,
        manifest_coordinate=_coordinate("manifest_source", manifest),
        candidate_coordinate=_coordinate(
            "candidate_listing", encode_semantic_candidate_listing(binding.candidates),
            SEMANTIC_CANDIDATE_LISTING_REF,
        ),
        registry_package_coordinate=_coordinate("registry_package", b"fixture"),
        package_context_coordinate=_coordinate(
            "package_context", encode_package_context_input(package),
            PACKAGE_CONTEXT_INPUT_REF,
        ),
        declaration_inventory_coordinate=_coordinate(
            "declaration_inventory", encode_declaration_target_inventory(inventory),
            DECLARATION_TARGET_INVENTORY_REF,
        ),
    )


def _authority(package, name, *, declared_source_paths=("body.bin",)):
    return create_portable_semantic_package_authority(
        manifest_contract_kind="example_toml",
        manifest_relative_path=package.manifest_relative_path,
        code_package=CodePortableCodePackage(
            name=package.code_package_name,
            language="aware",
            manifest_kind="example_toml",
            source_code_package_id=package.source_code_package_id,
            config_id=package.config_id,
            config_key=package.config_key,
            surface=None,
        ),
        semantic_provider_key="fixture.provider",
        semantic_package=CodePortableSemanticPackage("example", "example", name),
        semantic_contract=CodePortableSemanticContract(
            "example", "example", "fixture.provider", "fixture.example"
        ),
        semantic_version=package.semantic_version,
        package_ref=f"package:{name}@{package.semantic_version}",
        fqn_prefix=name,
        sources_root=".",
        declared_source_paths=declared_source_paths,
        direct_dependency_package_refs=(),
        owned_semantic_root_refs=(f"{name}.a", f"{name}.b"),
        semantic_metadata=CodeEmptySemanticMetadata(),
    )


@pytest.mark.parametrize(
    "change",
    [None, "wrong_root", "wrong_name", "foreign_admission", "foreign", "source", "close"],
)
async def test_v3_completion_requires_original_selected_occurrence(tmp_path, monkeypatch, change):
    async with fixture(tmp_path) as (root_path, _, borrowed, _, _, _):
        _author_v3_repository(root_path)
        with composition._compose_direct_workspace_command_resources(
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="workspaces/network/aware.workspace.toml",
            source_rail="declaration_v3",
        ) as command:
            sources = command.sources
            issuer = sources.declaration_scope_runtime
            runtime = sources.source_admission_runtime
            assert type(runtime) is WorkspaceV3OwnerDefinedSourceAdmissionRuntime
            with composition._compose_direct_workspace_selected_materialization_roots(
                command, selection=_selection("package", "network-example")
            ) as bound:
                root, selected = bound[0]
                package, _ = issuer.inspect_inputs(selected)
                context = object()
                expected = _expected(issuer, selected)
                planning = replace(
                    expected, stage="source_planning", operation_identity=object()
                )
                issuer._bind_original_code_validator(_Validator(object(), planning))
                issuer._bind_original_authority_validator(_Validator(context, expected))
                package_admission, inventory_admission = issuer.issue_authority_pair(
                    selected, context=context, expected=expected
                )
                authority = _authority(package, "network-example")
                if change == "wrong_name":
                    authority = _authority(package, "other-example")
                body = authority.canonical_bytes()
                coordinate = _coordinate("package_authority", body)
                completion = object.__new__(ExecutionCompletion)
                monkeypatch.setattr(
                    ExecutionCompletion, "result",
                    property(lambda self: SimpleNamespace(
                        status=TerminalStatus.CURRENT,
                        current_result=coordinate,
                    )),
                )
                monkeypatch.setattr(
                    ExecutionCompletion, "body_for",
                    lambda self, value: SimpleNamespace(canonical_body=body)
                    if value == coordinate else None,
                )
                monkeypatch.setattr(
                    authority_execution, "read_authority_completion",
                    lambda value: completion if value is context else None,
                )
                if change == "wrong_root":
                    root = replace(root, package_id="other")
                if change == "foreign_admission":
                    package_admission = object.__new__(WorkspacePackageContextAdmission)
                if change in ("wrong_root", "wrong_name", "foreign_admission"):
                    with pytest.raises((RuntimeError, SourceObservationUnavailable)):
                        runtime.issue(
                            root, selected, package_admission, inventory_admission,
                            context=context, expected=expected, completion=completion,
                        )
                    return
                admission = runtime.issue(
                    root, selected, package_admission, inventory_admission,
                    context=context, expected=expected, completion=completion,
                )
                inspection = runtime.inspect(admission)
                assert inspection.package == package.package
                occurrence = runtime.read_publication_package_occurrence(admission)
                assert occurrence == WorkspaceMaterializationPackageOccurrenceV4(
                    repository_ref=inspection.repository_ref,
                    workspace_ref=inspection.workspace_ref,
                    module_ref=inspection.module_ref,
                    package_id=inspection.package_id,
                    package_root=inspection.package_root,
                    manifest_relative_path=inspection.manifest_relative_path,
                )
                runtime.validate_publication_package_occurrence(
                    admission, occurrence=occurrence
                )
                with pytest.raises(RuntimeError, match="occurrence_differs"):
                    runtime.validate_publication_package_occurrence(
                        admission,
                        occurrence=replace(occurrence, package_id="other"),
                    )
                with pytest.raises(RuntimeError, match="foreign_or_expired"):
                    runtime.read_publication_package_occurrence(
                        object.__new__(WorkspaceOwnerDefinedSourceAdmission)
                    )
                manifest_sources = runtime.semantic_input_source_coordinates(
                    admission,
                    source_scope="manifest",
                    role="manifest_source",
                    contract=expected.manifest_coordinate.contract,
                )
                declared_sources = runtime.semantic_input_source_coordinates(
                    admission,
                    source_scope="declared",
                    role="authored_source",
                    contract=SemanticContractRef(
                        "fixture.authored-source", "1",
                        ContentDigest.of_bytes(b"fixture authored source"),
                    ),
                )
                assert tuple(source.relative_path for source in manifest_sources) == (
                    inspection.manifest_relative_path,
                )
                assert tuple(source.relative_path for source in declared_sources) == (
                    inspection.package_authority.declared_source_paths
                )
                with pytest.raises(ValueError, match="scope is unsupported"):
                    runtime.semantic_input_source_coordinates(
                        admission,
                        source_scope="candidate",
                        role="authored_source",
                        contract=declared_sources[0].coordinate.contract,
                    )
                source_expectation = SemanticInputProductionExpectation.create(
                    use_ref="fixture-v3-source-use",
                    operation_ref="fixture-v3-source-operation",
                    stage="definition_request",
                    package_identity=SemanticInputPackageIdentity(
                        inspection.package,
                        inspection.package_authority.semantic_package.name,
                    ),
                    operation_identity=object(),
                    source_identity=admission,
                    source_coordinates=manifest_sources,
                )
                runtime.validate_semantic_input_source(
                    admission, expected=source_expectation
                )
                retained = runtime.read_semantic_input_sources(
                    admission, expected=source_expectation
                )
                assert len(retained) == 1
                declared_expectation = SemanticInputProductionExpectation.create(
                    use_ref="fixture-v3-declared-use",
                    operation_ref="fixture-v3-declared-operation",
                    stage="parsed_documents",
                    package_identity=source_expectation.package_identity,
                    operation_identity=source_expectation.operation_identity,
                    source_identity=admission,
                    source_coordinates=declared_sources,
                )
                declared_bodies = runtime.read_semantic_input_sources(
                    admission, expected=declared_expectation
                )
                assert tuple(source.source for source in declared_bodies) == declared_sources
                assert (
                    ContentDigest.of_bytes(retained[0].canonical_body)
                    == expected.manifest_coordinate.digest
                )
                with pytest.raises(RuntimeError, match="source_identity_differs"):
                    runtime.validate_semantic_input_source(
                        admission,
                        expected=replace(source_expectation, source_identity=object()),
                    )
                wrong_source = SemanticInputSourceCoordinate(
                    inspection.manifest_relative_path,
                    replace(
                        expected.manifest_coordinate,
                        digest=ContentDigest.of_bytes(b"different manifest"),
                    ),
                )
                wrong_expected = SemanticInputProductionExpectation.create(
                    use_ref=source_expectation.use_ref,
                    operation_ref=source_expectation.operation_ref,
                    stage=source_expectation.stage,
                    package_identity=source_expectation.package_identity,
                    operation_identity=source_expectation.operation_identity,
                    source_identity=admission,
                    source_coordinates=(wrong_source,),
                )
                with pytest.raises(RuntimeError, match="coordinate_differs"):
                    runtime.read_semantic_input_sources(
                        admission, expected=wrong_expected
                    )
                if change is None:
                    from aware_code_semantic_contract_runtime import (
                        SemanticBody,
                        SemanticConfigurationCoordinate,
                        SemanticImplementationCoordinate,
                    )
                    from aware_code_semantic_contract_runtime.semantic_input_producer import (
                        SemanticInputProducerDeclaration,
                        SemanticInputProducerHost,
                        SemanticInputSourceContract,
                        execute_registered_semantic_input,
                        register_semantic_input_producer,
                    )

                    result_contract = SemanticContractRef(
                        "fixture.detached-v3-source", "1",
                        ContentDigest.of_bytes(b"fixture result contract"),
                    )
                    result_body = b"fixture detached v3 source result"

                    def produce(value):
                        assert value.sources == retained
                        return SemanticBody(
                            SemanticValueCoordinate(
                                "fixture_result", result_contract, "fixture:result",
                                ContentDigest.of_bytes(result_body), len(result_body),
                            ),
                            result_body,
                        )

                    host = SemanticInputProducerHost()
                    registration = register_semantic_input_producer(
                        host,
                        declaration=SemanticInputProducerDeclaration(
                            "fixture.v3-source-producer",
                            "fixture.v3-source-profile",
                            SemanticImplementationCoordinate(
                                "fixture.v3-source-implementation",
                                ContentDigest.of_bytes(b"fixture implementation"),
                            ),
                            SemanticConfigurationCoordinate(
                                "fixture.v3-source-configuration",
                                ContentDigest.of_bytes(b"fixture configuration"),
                            ),
                            (
                                SemanticInputSourceContract(
                                    "manifest_source",
                                    expected.manifest_coordinate.contract,
                                ),
                            ),
                            "fixture_result",
                            result_contract,
                        ),
                        producer=produce,
                        validator=runtime,
                        validator_entrance=runtime.validate_semantic_input_source,
                        reader=runtime,
                        reader_entrance=runtime.read_semantic_input_sources,
                    )
                    produced = await execute_registered_semantic_input(
                        host, registration,
                        source_admission=admission, expected=source_expectation,
                    )
                    assert produced.canonical_body == result_body
                    with pytest.raises(ValueError, match="already consumed"):
                        await execute_registered_semantic_input(
                            host, registration,
                            source_admission=admission, expected=source_expectation,
                        )
                entry = derive_owner_defined_catalog_entry(runtime, admission)
                correspondence = capture_v3_graph_source_correspondence(
                    runtime, admission, entry
                )
                from aware_code_semantic_contract_runtime.dependency_inputs import (
                    SemanticAuthoredDependency,
                    SemanticDependencyPlanningInput,
                )
                planning_input = SemanticDependencyPlanningInput(
                    inspection.package,
                    inspection.source_identity_digest,
                    tuple(
                        SemanticAuthoredDependency(
                            item.dependency_kind,
                            item.dependency_ref,
                            item.targets,
                            item.target_constraints,
                        )
                        for item in inspection.declaration_inventory.entries
                    ),
                )
                assert planning_input.source_identity_digest != entry.source_identity_digest
                correspondence.validate(entry, planning_input)
                assert correspondence.original_selected_source() is selected
                original_runtime, original_admission = (
                    correspondence.original_semantic_input_source(entry)
                )
                assert original_runtime is runtime
                assert original_admission is admission
                head_values = dict(
                    package=entry.package,
                    source_identity_digest=entry.source_identity_digest,
                    profile_binding_digest=ContentDigest.of_bytes(b"selected-v4-profile"),
                    state="stale",
                    predecessor_head_revision=1,
                    predecessor_head_digest=ContentDigest.of_bytes(b"retained-v4-head"),
                    historical_execution_input_closure_digest=None,
                    expected_post_revision=2,
                    expected_post_head_digest=None,
                    stored_head_contract=WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V4,
                    stored_package_occurrence=occurrence,
                )
                head = WorkspaceSemanticPackageHeadObservation.create(**head_values)
                _validate_state_bound_head_occurrence(
                    entry=entry, head=head, correspondence=correspondence
                )
                with pytest.raises(RuntimeError, match="occurrence_differs"):
                    _validate_state_bound_head_occurrence(
                        entry=entry,
                        head=WorkspaceSemanticPackageHeadObservation.create(
                            **{
                                **head_values,
                                "stored_package_occurrence": replace(
                                    occurrence, package_id="other"
                                ),
                            }
                        ),
                        correspondence=correspondence,
                    )
                composition._validate_direct_workspace_graph_source_closure(
                    bound_roots=bound,
                    selected_sources=(selected,),
                    source_correspondences=(correspondence,),
                )
                forged = object.__new__(WorkspaceV3GraphSourceCorrespondence)
                with pytest.raises(RuntimeError, match="foreign"):
                    composition._validate_direct_workspace_graph_source_closure(
                        bound_roots=bound,
                        selected_sources=(selected,),
                        source_correspondences=(forged,),
                    )
                with pytest.raises(RuntimeError, match="foreign"):
                    forged.validate(entry, planning_input)
                with pytest.raises(RuntimeError, match="foreign"):
                    forged.original_semantic_input_source(entry)
                with pytest.raises(TypeError, match="exact Workspace catalog entry"):
                    correspondence.original_semantic_input_source(object())

                with pytest.raises(RuntimeError, match="changed"):
                    correspondence.validate(
                        entry,
                        replace(
                            planning_input,
                            source_identity_digest=ContentDigest.of_bytes(b"substitute"),
                        ),
                    )
                assert entry.source_authority_digest == coordinate.digest
                assert entry.package == package.package
                with pytest.raises(RuntimeError, match="replay"):
                    runtime.issue(
                        root, selected, package_admission, inventory_admission,
                        context=context, expected=expected, completion=completion,
                    )
                if change == "foreign":
                    with pytest.raises(RuntimeError, match="foreign"):
                        runtime.inspect(object.__new__(WorkspaceOwnerDefinedSourceAdmission))
                elif change == "source":
                    (root_path / "workspaces/network/modules/main/package/body.bin").write_bytes(
                        b"changed"
                    )
                    with pytest.raises(SourceObservationUnavailable):
                        runtime.inspect(admission)
                    with pytest.raises(SourceObservationUnavailable):
                        runtime.read_semantic_input_sources(
                            admission, expected=source_expectation
                        )
                    with pytest.raises(SourceObservationUnavailable):
                        correspondence.validate(entry, planning_input)
                    with pytest.raises(SourceObservationUnavailable):
                        correspondence.original_semantic_input_source(entry)
                elif change == "close":
                    runtime.close()
                    with pytest.raises(RuntimeError, match="foreign"):
                        runtime.inspect(admission)
                    with pytest.raises(RuntimeError, match="expired"):
                        correspondence.validate(entry, planning_input)
                    with pytest.raises(RuntimeError, match="changed|expired"):
                        correspondence.original_semantic_input_source(entry)
                    with pytest.raises(RuntimeError, match="foreign"):
                        runtime.validate_semantic_input_source(
                            admission, expected=source_expectation
                        )
                elif change is None:
                    def retired_completion(_):
                        raise RuntimeError("retired completion")
                    monkeypatch.setattr(
                        authority_execution, "read_authority_completion",
                        retired_completion,
                    )
                    with pytest.raises(RuntimeError, match="retired completion"):
                        runtime.inspect(admission)
                    correspondence.validate(entry, planning_input)


async def test_original_v3_source_runs_real_language_producer(
    tmp_path, monkeypatch
):
    from aware_code_semantic_contract_runtime.semantic_input_producer import (
        SemanticInputProducerHost,
        execute_registered_semantic_input,
        register_semantic_input_producer,
    )
    from aware_language_parsed_document_contract import decode_parsed_document_batch
    from tree_sitter_aware.parsed_document import TREE_SITTER_AWARE_PARSER_PROFILE
    from tree_sitter_aware.semantic_input_provider import (
        AWARE_SOURCE_REF,
        AWARE_SOURCE_ROLE,
        aware_parsed_documents_producer_declaration,
        produce_aware_parsed_documents,
    )

    async with fixture(tmp_path) as (root_path, _, borrowed, _, _, _):
        _author_v3_repository(root_path)
        source_path = root_path / "workspaces/network/modules/main/package/body.aware"
        source_path.write_bytes(b"class Note {\n    id UUID key\n    text String\n}\n")
        with composition._compose_direct_workspace_command_resources(
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="workspaces/network/aware.workspace.toml",
            source_rail="declaration_v3",
        ) as command:
            issuer = command.sources.declaration_scope_runtime
            runtime = command.sources.source_admission_runtime
            with composition._compose_direct_workspace_selected_materialization_roots(
                command, selection=_selection("package", "network-example")
            ) as bound:
                root, selected = bound[0]
                package, _ = issuer.inspect_inputs(selected)
                context = object()
                expected = _expected(issuer, selected)
                issuer._bind_original_code_validator(
                    _Validator(object(), replace(
                        expected, stage="source_planning", operation_identity=object()
                    ))
                )
                issuer._bind_original_authority_validator(
                    _Validator(context, expected)
                )
                package_admission, inventory_admission = issuer.issue_authority_pair(
                    selected, context=context, expected=expected
                )
                authority = _authority(
                    package, "network-example",
                    declared_source_paths=("body.aware",),
                )
                body = authority.canonical_bytes()
                coordinate = _coordinate("package_authority", body)
                completion = object.__new__(ExecutionCompletion)
                monkeypatch.setattr(
                    ExecutionCompletion, "result",
                    property(lambda self: SimpleNamespace(
                        status=TerminalStatus.CURRENT,
                        current_result=coordinate,
                    )),
                )
                monkeypatch.setattr(
                    ExecutionCompletion, "body_for",
                    lambda self, value: SimpleNamespace(canonical_body=body)
                    if value == coordinate else None,
                )
                monkeypatch.setattr(
                    authority_execution, "read_authority_completion",
                    lambda value: completion if value is context else None,
                )
                admission = runtime.issue(
                    root, selected, package_admission, inventory_admission,
                    context=context, expected=expected, completion=completion,
                )
                inspection = runtime.inspect(admission)
                sources = runtime.semantic_input_source_coordinates(
                    admission, source_scope="declared",
                    role=AWARE_SOURCE_ROLE, contract=AWARE_SOURCE_REF,
                )
                assert tuple(source.relative_path for source in sources) == (
                    "body.aware",
                )
                operation_identity = object()
                production = SemanticInputProductionExpectation.create(
                    use_ref="v3-real-language-use",
                    operation_ref="v3-real-language-operation",
                    stage="parsed_documents",
                    package_identity=SemanticInputPackageIdentity(
                        inspection.package,
                        inspection.package_authority.semantic_package.name,
                    ),
                    operation_identity=operation_identity,
                    source_identity=admission,
                    source_coordinates=sources,
                )
                host = SemanticInputProducerHost()
                try:
                    registration = register_semantic_input_producer(
                        host,
                        declaration=aware_parsed_documents_producer_declaration(),
                        producer=produce_aware_parsed_documents,
                        validator=runtime,
                        validator_entrance=runtime.validate_semantic_input_source,
                        reader=runtime,
                        reader_entrance=runtime.read_semantic_input_sources,
                    )
                    result = await execute_registered_semantic_input(
                        host, registration,
                        source_admission=admission, expected=production,
                    )
                    batch = decode_parsed_document_batch(
                        result.canonical_body,
                        expected_parser_profile=TREE_SITTER_AWARE_PARSER_PROFILE,
                    )
                    assert len(batch.coordinates) == 1
                    assert batch.coordinates[0].package_ref == inspection.package.package_ref
                    source_path.write_bytes(source_path.read_bytes() + b"\n# changed\n")
                    with pytest.raises((RuntimeError, SourceObservationUnavailable)):
                        runtime.validate_semantic_input_source(
                            admission, expected=production
                        )
                finally:
                    host.close()
