"""Tracked supplier publication -> original nonempty consumer fulfillment.

The neutral fixture owners supply test meaning. Original Workspace/Code source,
demand, resolution, selected execution, publication and reader checks remain live.
This is not the public dependency graph command or an API/Ontology qualification.
"""

import json
import sys
from contextlib import ExitStack
from dataclasses import replace

import pytest
from aware_code_retained_registry_policy_runtime import (
    product_planning_source as planning,
)
from aware_code_retained_registry_policy_runtime.retained_demand_operation import (
    execute_retained_dependency_demand,
)
from aware_code_retained_registry_policy_runtime.selected_root_intent import (
    derive_selected_root_intent,
)
from aware_code_semantic_contract_runtime import (
    CodeSemanticPackagePlanningContext,
    ContentDigest,
    SemanticValueCoordinate,
    TerminalStatus,
)
from aware_code_semantic_contract_runtime import selected_provider as selected_runtime
from aware_code_semantic_contract_runtime.dependency_input_codec import (
    SemanticDependencyProductInputCodec,
)
from aware_code_semantic_contract_runtime.materialization_catalog_codec import (
    decode_code_semantic_contract_match_admission,
)
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputProducerHost,
    SemanticInputSourceCoordinate,
)
from aware_local_service_state_sqlite import SqliteLocalOperationalStateStore

# isort: split

from aware_workspace_materialize_transport import WorkspaceMaterializeCommandProposalV3
from aware_workspace_runtime import declaration_product_membership as membership
from aware_workspace_runtime import dependency_fulfillment as fulfillment_runtime
from aware_workspace_runtime import direct_cli_selected_host as local
from aware_workspace_runtime import direct_command_composition as composition
from aware_workspace_runtime import source_observation as observation
from aware_workspace_runtime.declaration_product_membership import (
    read_declaration_product_correspondence_package,
)
from aware_workspace_runtime.direct_cli_product_execution import (
    DirectCLIProductDependencyAdmissions,
    execute_direct_cli_selected_product,
)
from aware_workspace_runtime.direct_cli_product_planning import (
    plan_direct_cli_selected_product,
)
from aware_workspace_runtime.direct_cli_product_publication import (
    publish_direct_cli_selected_product,
)
from aware_workspace_runtime.materialization_graph_host_composition import (
    WorkspaceMaterializationGraphBacking,
)

# isort: split

from product_supplier_fixture import supplier_factory
from test_dependency_scope_admission import fixture as sources
from test_direct_cli_dependency_planning import (
    ROOT_KEY,
    SUPPLIER_KEY,
    _owner_factory,
    _repository,
)
from test_product_dependency_inventory import product_demand


@pytest.fixture(params=[False])
def owners(request):
    calls = []
    role = "dependency_products" if request.param == "meta-role" else "semantic_dependencies"
    admitted = {ROOT_KEY: supplier_factory(calls, consumer=True, dependency_role=role) if request.param else _owner_factory(ROOT_KEY, calls),
        SUPPLIER_KEY: supplier_factory(calls)}
    try:
        yield admitted, calls
    finally:
        for original, _ in admitted.values():
            state = selected_runtime._factory_state(original)
            if selected_runtime._FACTORY_PROVIDER_KEYS.get(state.provider_key) is original:
                del selected_runtime._FACTORY_PROVIDER_KEYS[state.provider_key]
            if selected_runtime._FACTORY_REFS.get(state.factory_ref) is original:
                del selected_runtime._FACTORY_REFS[state.factory_ref]
            selected_runtime._FACTORIES.pop(id(original), None)


@pytest.mark.parametrize("case", ["valid", "relabel", "foreign_issuer", "missing", "duplicate", "substitute"])
async def test_original_source_commitment_bridge(tmp_path, monkeypatch, owners, case):
    async with product_demand(tmp_path, monkeypatch, owners) as (_, command, issuer, _, _, _, _, expected, _):
        pair = command.catalog_host._result
        correspondence, = pair.source_correspondences
        entry = pair.workspace.package(expected.source_planning.package.package_ref)
        pairs = ((correspondence, entry),)
        if case == "duplicate":
            with pytest.raises(RuntimeError, match="duplicate_dependency_source"):
                fulfillment_runtime._original_source_reader(issuer, pairs + pairs)
            return
        reader = fulfillment_runtime._original_source_reader(object() if case == "foreign_issuer" else issuer, pairs)
        source = expected.source_planning.source_identity_digest
        assert entry.source_identity_digest != source
        if case == "valid":
            assert reader.digest(entry.package, source) == entry.source_identity_digest
        elif case == "relabel":
            with pytest.raises(RuntimeError, match="selected source differs"):
                reader.digest(entry.package, entry.source_identity_digest)
        elif case == "foreign_issuer":
            with pytest.raises(RuntimeError, match="original declaration product source"):
                reader.digest(entry.package, source)
        elif case == "missing":
            with pytest.raises(RuntimeError, match="correspondence_unavailable"):
                reader.digest(replace(entry.package, package_ref="package:foreign@1"), source)
        else:
            calls = []

            def hostile(*args, **kwargs):
                calls.append(True)

            monkeypatch.setattr(fulfillment_runtime._product_sources, "validate_declaration_product_source", hostile)
            with pytest.raises(RuntimeError, match="correspondence_changed"):
                reader.digest(entry.package, source)
            assert not calls


async def test_tracked_supplier_head_fulfills_two_original_demands(tmp_path, monkeypatch, owners):
    await _supplier_consumer_join(tmp_path, monkeypatch, owners)


async def test_supplier_metadata_keeps_consumer_window_and_fresh_source_checks(tmp_path, monkeypatch, owners):
    async with product_demand(tmp_path, monkeypatch, owners) as (_, command, issuer, supplier, _, _, _, expected, _):
        pair = command.catalog_host._result
        correspondence, = pair.source_correspondences
        entry = pair.workspace.package(expected.source_planning.package.package_ref)
        declaration = membership._state(correspondence).declaration
        with composition._compose_direct_workspace_selected_package_source(command,
            workspace_manifest_path="consumer/aware.workspace.toml", module_id="main", package_id="consumer") as consumer:
            supplier_observation = issuer._selected_record(supplier).observation
            code = observation.WorkspaceSourceObservationRuntime.revalidate_selected_package.__code__
            calls = []

            def profile(frame, event, _):
                if event == "call" and frame.f_code is code and frame.f_locals["handle"] is supplier_observation:
                    calls.append(True)

            with issuer._original_participant_source_window(declaration, consumer):
                current = issuer._semantic_source_window
                previous = sys.getprofile()
                try:
                    sys.setprofile(profile)
                    membership.validate_declaration_product_correspondence(correspondence, entry)
                finally:
                    sys.setprofile(previous)
                assert calls
                assert issuer._semantic_source_window is current and current.selected is consumer
            assert issuer._semantic_source_window is None


@pytest.mark.parametrize("owners", [True], indirect=True)
async def test_consumer_executes_with_original_published_supplier(tmp_path, monkeypatch, owners):
    await _supplier_consumer_join(tmp_path, monkeypatch, owners, execute_consumer=True)


@pytest.mark.parametrize("owners", ["meta-role"], indirect=True)
async def test_original_fulfillment_and_code_intake_preserve_meta_profile_role(tmp_path, monkeypatch, owners):
    # Original supplier execution and publication, original consumer source,
    # demand/resolution/fulfillment and Code product intake. Neutral fixture
    # semantics do NOT become a real Meta export or a consumer execution proof.
    await _supplier_consumer_join(tmp_path, monkeypatch, owners,
                                  expected_dependency_role="dependency_products")


async def _supplier_consumer_join(tmp_path, monkeypatch, owners, *, execute_consumer=False,
                                expected_dependency_role=None):
    admitted, calls = owners
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setattr(local, "admit_installed_semantic_stage_factory", lambda key: admitted[key][0])
    profiles = {key: profile for key, (_, profile) in admitted.items()}
    async with sources(tmp_path, lambda root: _repository(root, profiles)) as (root, _, _, borrowed, _, _):
        proposal = WorkspaceMaterializeCommandProposalV3.create(
            attempt_ref="proof:original-supplier", participant_checkout_root=str(root),
            workspace_manifest_name="consumer/aware.workspace.toml",
            package_address=("Consumer", "main", "consumer"), plan_only=False,
        )
        with composition._compose_direct_workspace_command_source(
            session=borrowed._session, store=borrowed._store, proposal=proposal,
        ) as (command, _, consumer), ExitStack() as resources:
            supplier = resources.enter_context(composition._compose_direct_workspace_selected_package_source(
                command, workspace_manifest_path="consumer/aware.workspace.toml", module_id="main", package_id="supplier"))
            with ExitStack() as inputs_retained, local.compose_direct_cli_selected_product(
                command, consumer, participating_sources=(consumer, supplier),
            ) as product:
                issuer, host = command.sources.declaration_scope_runtime, product.host.code_host
                consumer_part, supplier_part = product.participants
                _, required = derive_selected_root_intent(host, supplier_part.policy)
                # Borrowed selection metadata only. The same original host,
                # source and policy are verified by planning and publication.
                supplier_view = replace(product, provider_key=supplier_part.provider_key,
                    requested_role=required.role, package_ref=supplier_part.package_ref,
                    policy=supplier_part.policy, participants=(supplier_part,))
                planned = await plan_direct_cli_selected_product(command, supplier, supplier_view)
                published = await publish_direct_cli_selected_product(command, supplier, supplier_view, planned, retention=inputs_retained)
                assert len(planned.plan.graph.nodes) == 1 and not planned.plan.graph.edges
                assert published.wire and len(published.result.ordered_node_results) == 1
                # Finish the supplier's original node read before opening the
                # consumer node. The command and Code host remain the same.
                inputs_retained.close()

                # The reader uses the same ordinary filesystem backing as the
                # original publisher; no head/body value is fabricated.
                evidence = issuer.inspect_selected_package_evidence(supplier)
                state_root = composition._direct_workspace_cli_state_root(borrowed._session.binding.root_path) / "materialization"
                backing = WorkspaceMaterializationGraphBacking(state_root=state_root,
                    repository_binding_ref=evidence.repository_binding_ref,
                    state_store=SqliteLocalOperationalStateStore(state_root / "heads.sqlite3"))
                source_pairs = tuple((handle, product.host.catalog_pair.workspace.package(
                    read_declaration_product_correspondence_package(handle).package_ref))
                    for handle in product.host.catalog_pair.source_correspondences)
                issuer._bind_original_dependency_product_publisher(backing.publisher, source_correspondences=source_pairs)
                declared = planning.read_product_planning_input_declaration(host, consumer_part.policy, consumer_part.contribution)
                role, = declared.source_contracts
                evidence = issuer.inspect_selected_package_evidence(consumer)
                coordinates = tuple(SemanticInputSourceCoordinate(item.relative_path, SemanticValueCoordinate(
                    role.role, role.contract, item.body_ref, ContentDigest(item.content_digest), item.size_bytes)) for item in evidence.bodies)
                with ExitStack() as demand_retained:
                    expected_input = demand_retained.enter_context(issuer.original_pre_request_input(consumer,
                        use_ref="proof:consumer-demand", stage="source_planning", source_coordinates=coordinates,
                        context_contracts=declared.context_contracts))
                    input_host = SemanticInputProducerHost()
                    try:
                        registration = planning.register_product_planning_input_producer(host, consumer_part.policy, consumer_part.contribution, input_host=input_host)
                        source = await planning.execute_product_planning_input(host, consumer_part.policy, consumer_part.contribution,
                            input_host=input_host, registration=registration, expected=expected_input)
                        entry = product.host.catalog_pair.workspace.package(product.package_ref)
                        intent, required = derive_selected_root_intent(host, product.policy)
                        context = CodeSemanticPackagePlanningContext.create(package=entry.package, package_family=entry.package_family,
                            package_role=entry.package_role, manifest_contract=entry.manifest_contract, code_intent=intent,
                            required_semantic_provider_keys=(ROOT_KEY,), required_result_products=(required,))
                        operation = await execute_retained_dependency_demand(source, context=context)
                        expected = issuer._dependency_validator[0].expectation(operation)
                        inventory = issuer.issue_product_dependency_inventory(operation, expected=expected)
                        resolution = issuer.issue_dependency_resolution(operation, inventory_admission=inventory, expected=expected)
                        assert len(issuer._dependency_resolution.records[resolution].targets) == 2
                        head = published.result.ordered_node_results[0].package_head_reread_evidence.head
                        for _, target, _, target_context, wire in issuer._dependency_resolution.records[resolution].targets:
                            match = decode_code_semantic_contract_match_admission(wire, context=target_context, resolver=issuer._dependency_resolution.resolver)
                            target_source = issuer._target_source(target).context
                            assert {
                                "package": head.package,
                                "source": head.source_identity_digest,
                                "intent": head.code_intent_digest,
                                "match": head.code_match_digest,
                                "role": head.result_coordinate.role,
                                "contract": head.result_coordinate.contract,
                            } == {
                                "package": target_context.package,
                                "source": product.host.catalog_pair.workspace.package(target_context.package.package_ref).source_identity_digest,
                                "intent": target_context.code_intent.intent_digest,
                                "match": match.match_digest,
                                "role": target_context.required_result_products[0].role,
                                "contract": target_context.required_result_products[0].contract,
                            }
                            assert head.source_identity_digest != target_source.source_identity_digest
                        fulfillment = issuer.issue_dependency_fulfillment(resolution, expected=expected)
                        body = issuer.read_dependency_products(fulfillment, resolution_admission=resolution, expected=expected)
                        if expected_dependency_role is not None:
                            assert body.coordinate.role == expected_dependency_role
                        value = SemanticDependencyProductInputCodec().decode(body.canonical_body)
                        assert len(value.products) == 2
                        if execute_consumer:
                            result = await execute_direct_cli_selected_product(command, consumer, product,
                                retention=inputs_retained, dependency_admissions=DirectCLIProductDependencyAdmissions(
                                    operation, resolution, fulfillment, body))
                            assert result.snapshot.result.status is TerminalStatus.DELTA
                            result_body = next(item for item in result.snapshot.bodies if item.coordinate.role == "result")
                            assert json.loads(result_body.canonical_body)["dependencies"] == [
                                item.body.coordinate.digest.value for item in value.products]
                            inputs_retained.close()
                        else:
                            with composition._command_owned_selected_input_read_session(command, host=host, selected_source=consumer,
                                registration=expected.source_planning.selected_provider_registration) as node:
                                products = node.admit_dependency_products(operation, resolution, fulfillment, body=body)
                                assert products.read_products() == body
                                if expected_dependency_role is not None:
                                    assert products.read_products().coordinate.role == expected_dependency_role
                                node.validate()
                        assert [kind for kind, _, key in calls if key == ROOT_KEY] == (
                            ["source", "plan", "execution_input", "execute"] if execute_consumer else ["source", "plan"])
                        assert [kind for kind, _, key in calls if key == SUPPLIER_KEY] == ["source", "plan", "execution_input", "execute"]
                    finally:
                        planning.close_product_planning_sources(host)
                        input_host.close()
