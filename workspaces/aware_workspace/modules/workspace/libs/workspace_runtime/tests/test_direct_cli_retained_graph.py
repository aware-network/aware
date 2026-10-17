"""First-dispatch demand retention under one original graph command."""

from contextlib import ExitStack

import pytest
from aware_code_semantic_contract_runtime import ContractViolation

# isort: split

from aware_workspace_materialize_transport import WorkspaceMaterializeCommandProposalV3
from aware_workspace_runtime import direct_cli_selected_host as local
from aware_workspace_runtime import direct_command_composition as composition
from aware_workspace_runtime.direct_cli_product_planning import (
    plan_direct_cli_selected_product,
)
from aware_workspace_runtime.direct_cli_product_publication import (
    publish_direct_cli_selected_product,
)

# isort: split

from test_dependency_scope_admission import fixture as sources
from test_direct_cli_dependency_planning import ROOT_KEY, SUPPLIER_KEY, _repository
from test_original_supplier_fulfillment import owners as original_owners

owners = original_owners


@pytest.mark.parametrize("owners", [True], indirect=True)
@pytest.mark.parametrize("publish", [False, True])
async def test_first_graph_dispatch_retains_both_original_operations(tmp_path, monkeypatch, owners, publish):
    admitted, calls = owners
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setattr(local, "admit_installed_semantic_stage_factory", lambda key: admitted[key][0])
    profiles = {key: profile for key, (_, profile) in admitted.items()}
    async with sources(tmp_path, lambda root: _repository(root, profiles)) as (root, _, _, borrowed, _, _):
        proposal = WorkspaceMaterializeCommandProposalV3.create(attempt_ref="proof:retained-graph",
            participant_checkout_root=str(root), workspace_manifest_name="consumer/aware.workspace.toml",
            package_address=("Consumer", "main", "consumer"), plan_only=False)
        with composition._compose_direct_workspace_command_source(
            session=borrowed._session, store=borrowed._store, proposal=proposal,
        ) as (command, _, consumer), ExitStack() as resources:
            supplier = resources.enter_context(composition._compose_direct_workspace_selected_package_source(
                command, workspace_manifest_path="consumer/aware.workspace.toml", module_id="main", package_id="supplier"))
            with local.compose_direct_cli_selected_product(command, consumer,
                participating_sources=(consumer, supplier)) as product, ExitStack() as retained:
                planned = await plan_direct_cli_selected_product(command, consumer, product, retention=retained)
                assert len(planned.plan.graph.nodes) == 2 and len(planned.plan.graph.edges) == 2
                assert planned.demands is not None
                if publish:
                    with ExitStack() as execution_retained:
                        result = await publish_direct_cli_selected_product(command, consumer, product, planned,
                            retention=execution_retained)
                        assert len(result.result.ordered_node_results) == 2
                        assert all(item.package_head_reread_evidence.materialization_head_revision == 1
                            for item in result.result.ordered_node_results)
                        assert len(result.result.ordered_fulfilled_products) == 2
                else:
                    for binding in planned.plan.graph_execution_binding.ordered_node_bindings:
                        operation = planned.demands.operation(binding)
                        issuer = command.sources.declaration_scope_runtime
                        expected = issuer._dependency_validator[0].expectation(operation)
                        inventory = issuer.issue_product_dependency_inventory(operation, expected=expected)
                        resolution = issuer.issue_dependency_resolution(operation, inventory_admission=inventory, expected=expected)
                        issuer.validate_dependency_resolution_admission(resolution, expected=expected)
                for key in (ROOT_KEY, SUPPLIER_KEY):
                    assert [kind for kind, _, owner in calls if owner == key] == (
                        ["source", "plan", "execution_input", "execute"] if publish else ["source", "plan"])
            with pytest.raises(ContractViolation, match="terminal"):
                planned.demands.operation(planned.plan.graph_execution_binding.ordered_node_bindings[0])
