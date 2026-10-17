"""Actual Code product demand -> original Workspace inventory/resolution.

Factory intake is source-grade fixture admission. No store authority, public
command, semantic-owner export or fabricated staged operation is supplied.
"""

from contextlib import ExitStack, asynccontextmanager
from dataclasses import replace

import pytest
from aware_code_retained_registry_policy_runtime import (
    product_planning_source as planning,
)
from aware_code_retained_registry_policy_runtime.dependency_admission_origin import (
    assemble_dependency_admission_consumer,
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
    ContractViolation,
    SemanticValueCoordinate,
)
from aware_code_semantic_contract_runtime.dependency_input_codec import (
    SemanticDependencyProductInputCodec,
)
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputProducerHost,
    SemanticInputSourceCoordinate,
)

# isort: split

from aware_workspace_materialize_transport import WorkspaceMaterializeCommandProposalV3
from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime import direct_cli_selected_host as local
from aware_workspace_runtime import direct_command_composition as composition

# isort: split

from test_dependency_scope_admission import fixture as sources
from test_direct_cli_dependency_planning import ROOT_KEY, SUPPLIER_KEY, _repository
from test_direct_cli_dependency_planning import owners as original_owners

owners = original_owners


@asynccontextmanager
async def product_demand(tmp_path, monkeypatch, owners, *, nonempty=False):
    admitted, calls = owners
    calls.clear()
    monkeypatch.setattr(local, "admit_installed_semantic_stage_factory", lambda key: admitted[key][0])
    profiles = {key: profile for key, (_, profile) in admitted.items()}
    async with sources(tmp_path, lambda root: _repository(root, profiles)) as (root, _, _, borrowed, _, _):
        proposal = WorkspaceMaterializeCommandProposalV3.create(
            attempt_ref="proof:product-resolution", participant_checkout_root=str(root),
            workspace_manifest_name="consumer/aware.workspace.toml",
            package_address=("Consumer", "main", "consumer" if nonempty else "supplier"), plan_only=True,
        )
        with composition._compose_direct_workspace_command_source(
            session=borrowed._session, store=borrowed._store, proposal=proposal,
        ) as (command, _, selected), local.compose_direct_cli_selected_product(command, selected) as product:
            issuer, host = command.sources.declaration_scope_runtime, product.host.code_host
            contribution = product.participants[0].contribution
            declared = planning.read_product_planning_input_declaration(host, product.policy, contribution)
            evidence = issuer.inspect_selected_package_evidence(selected)
            role, = declared.source_contracts
            coordinates = tuple(SemanticInputSourceCoordinate(
                body.relative_path, SemanticValueCoordinate(role.role, role.contract, body.body_ref, ContentDigest(body.content_digest), body.size_bytes),
            ) for body in evidence.bodies)
            with ExitStack() as retained:
                expected_input = retained.enter_context(issuer.original_pre_request_input(
                    selected, use_ref="proof:product-resolution-source", stage="source_planning",
                    source_coordinates=coordinates, context_contracts=declared.context_contracts,
                ))
                input_host = SemanticInputProducerHost()
                try:
                    registration = planning.register_product_planning_input_producer(host, product.policy, contribution, input_host=input_host)
                    source = await planning.execute_product_planning_input(host, product.policy, contribution, input_host=input_host, registration=registration, expected=expected_input)
                    entry = product.host.catalog_pair.workspace.package(product.package_ref)
                    intent, result = derive_selected_root_intent(host, product.policy)
                    context = CodeSemanticPackagePlanningContext.create(
                        package=entry.package, package_family=entry.package_family, package_role=entry.package_role,
                        manifest_contract=entry.manifest_contract, code_intent=intent,
                        required_semantic_provider_keys=(ROOT_KEY if nonempty else SUPPLIER_KEY,), required_result_products=(result,),
                    )
                    operation = await execute_retained_dependency_demand(source, context=context)
                    # This is the same original validator retained by fixed composition.
                    validator = issuer._dependency_validator[0]
                    expected = validator.expectation(operation)
                    yield root, command, issuer, selected, host, source, operation, expected, calls
                finally:
                    planning.close_product_planning_sources(host)
                    input_host.close()


async def test_original_product_demand_resolves_and_fulfills_without_stage(tmp_path, monkeypatch, owners):
    async with product_demand(tmp_path, monkeypatch, owners) as (_, command, issuer, selected, host, _, operation, expected, calls):
        inventory = issuer.issue_product_dependency_inventory(operation, expected=expected)
        assert issuer._semantic[inventory].selected is selected
        assert issuer._contexts[inventory] is operation
        original_input, = (item.expected for item in issuer._pre_request_inputs.values() if item.live)
        assert expected.source_planning.source_input is not original_input
        assert expected.source_planning.source_input.source_identity is original_input.source_identity
        with pytest.raises(SourceObservationUnavailable, match="replay"):
            issuer.issue_product_dependency_inventory(operation, expected=expected)
        resolution, fulfillment, body = issuer.issue_empty_dependency_products(operation, inventory_admission=inventory, expected=expected)
        admitted = assemble_dependency_admission_consumer(host).admit_dependency_products(operation, resolution, fulfillment, body=body)
        assert admitted.read_products() == body
        assert admitted.read_products() == body
        value = SemanticDependencyProductInputCodec().decode(body.canonical_body)
        assert value.products == value.demand_set.demands == value.declared_dependencies == ()
        with composition._command_owned_selected_input_read_session(
            command, host=host, selected_source=selected,
            registration=expected.source_planning.selected_provider_registration,
        ) as node:
            node_products = node.admit_dependency_products(operation, resolution, fulfillment, body=body)
            assert node_products.read_products() == body
            node.validate()
        assert [kind for kind, *_ in calls] == ["source", "plan"]


@pytest.mark.parametrize("change", ["package", "source", "parent", "epoch", "foreign_operation"])
async def test_product_inventory_refuses_changed_original_evidence(tmp_path, monkeypatch, owners, change):
    async with product_demand(tmp_path, monkeypatch, owners) as (_, _, issuer, _, _, _, operation, expected, calls):
        changed = {
            "package": replace(expected, source_planning=replace(expected.source_planning, package=replace(expected.source_planning.package, package_ref="package:foreign@1"))),
            "source": replace(expected, source_planning=replace(expected.source_planning, source_identity_digest=ContentDigest.of_bytes(b"foreign"))),
            "parent": replace(expected, parent_identity=object()),
            "epoch": replace(expected, epoch_identity=object()),
            "foreign_operation": replace(expected, demand_operation_identity=object()),
        }[change]
        before = dict(issuer._semantic)
        with pytest.raises((ContractViolation, SourceObservationUnavailable)):
            issuer.issue_product_dependency_inventory(operation, expected=changed)
        assert issuer._semantic == before
        inventory = issuer.issue_product_dependency_inventory(operation, expected=expected)
        assert issuer._contexts[inventory] is operation
        assert [kind for kind, *_ in calls] == ["source", "plan"]


async def test_source_drift_retires_original_product_fulfillment(tmp_path, monkeypatch, owners):
    with pytest.raises(ContractViolation, match="direct host unavailable"):
        async with product_demand(tmp_path, monkeypatch, owners) as (root, _, issuer, _, host, _, operation, expected, _):
            inventory = issuer.issue_product_dependency_inventory(operation, expected=expected)
            resolution, fulfillment, body = issuer.issue_empty_dependency_products(operation, inventory_admission=inventory, expected=expected)
            admitted = assemble_dependency_admission_consumer(host).admit_dependency_products(operation, resolution, fulfillment, body=body)
            path = root / "consumer/modules/main/supplier/source.aware"
            original = path.read_bytes()
            path.write_bytes(b"changed original supplier")
            with pytest.raises((ContractViolation, SourceObservationUnavailable)):
                admitted.read_products()
            path.write_bytes(original)
            with pytest.raises((ContractViolation, SourceObservationUnavailable)):
                admitted.read_products()


async def test_nonempty_product_inventory_requires_live_supplier_catalog(tmp_path, monkeypatch, owners):
    checked = []
    with pytest.raises(ContractViolation, match="direct host unavailable"):
        async with product_demand(tmp_path, monkeypatch, owners, nonempty=True) as (_, _, issuer, _, _, _, operation, expected, calls):
            assert len(operation.read_demand().demands) == 2
            inventory = issuer.issue_product_dependency_inventory(operation, expected=expected)
            assert len(issuer._semantic[inventory].targets) == 1
            with pytest.raises(ContractViolation) as caught:
                issuer.issue_dependency_resolution(operation, inventory_admission=inventory, expected=expected)
            messages, error = [], caught.value
            while error is not None:
                messages.append(str(error))
                error = error.__context__
            assert any("catalog profile unavailable" in message for message in messages)
            assert not issuer._dependency_resolution.records
            assert not issuer._dependency_fulfillment.records
            assert [kind for kind, *_ in calls] == ["source", "plan"]
            checked.append(True)
    assert checked == [True]
