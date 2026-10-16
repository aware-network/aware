"""Original Attention factory/source into the one Workspace graph planner."""

from dataclasses import replace

import pytest
from aware_code_retained_registry_policy_runtime import (
    product_planning_source as planning,
)
from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime import direct_cli_selected_host as local
from aware_workspace_runtime import direct_command_composition as composition
from aware_workspace_runtime.declaration_product_membership import (
    validate_declaration_product_planning_input,
)
from aware_workspace_runtime.direct_cli_product_planning import (
    plan_direct_cli_selected_product,
)
from aware_workspace_runtime.semantic_dependency_graph_codec import (
    decode_workspace_semantic_materialization_graph_plan_result,
)
from test_declaration_product_membership import prepared
from test_direct_cli_selected_host import _proposal, sources
from test_direct_cli_selected_host import factory as _factory
from test_single_product_command_composition import _attention_repository

factory = _factory


async def test_original_product_produces_complete_graph_plan_and_closes_input_source(
    tmp_path, factory, monkeypatch
):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setattr(local, "admit_installed_semantic_stage_factory", lambda key: factory)
    async with sources(tmp_path, _attention_repository) as (root, _, _, borrowed, _, _):
        with composition._compose_direct_workspace_command_source(  # noqa: SIM117 - original command outlives its product host
            session=borrowed._session, store=borrowed._store, proposal=_proposal(root),
        ) as (command, _, selected):
            with local.compose_direct_cli_selected_product(command, selected) as product:
                before = set(planning._SOURCES)
                result = await plan_direct_cli_selected_product(command, selected, product)
                assert set(planning._SOURCES) == before
                assert len(result.plan.graph.nodes) == 1
                assert result.plan.graph.edges == ()
                node, = result.plan.graph.nodes
                assert node.package.package_ref == "package:sample_attention@1"
                decoded = decode_workspace_semantic_materialization_graph_plan_result(
                    result.wire, expected=result.plan,
                )
                assert decoded.graph.graph_digest == result.plan.graph.graph_digest
                assert result.elapsed_ns >= 0
        assert borrowed._session.authority_admitted
    import sqlite3

    database, = (tmp_path / "state").rglob("heads.sqlite3")
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM local_operational_state").fetchone() == (0,)


async def test_owner_call_source_mutation_cannot_return_plan(tmp_path, factory, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setattr(local, "admit_installed_semantic_stage_factory", lambda key: factory)
    original = planning.execute_product_planning_input
    async with sources(tmp_path, _attention_repository) as (root, _, _, borrowed, _, _):
        async def mutate(*args, **kwargs):
            retained = await original(*args, **kwargs)
            path = root / "consumer/modules/main/attention/source.aware"
            path.write_bytes(path.read_bytes() + b"\nchanged after owner production\n")
            return retained

        monkeypatch.setattr(planning, "execute_product_planning_input", mutate)
        before = set(planning._SOURCES)
        with pytest.raises(SourceObservationUnavailable):  # noqa: SIM117 - preserve cleanup assertion after rejection
            with composition._compose_direct_workspace_command_source(
                session=borrowed._session, store=borrowed._store, proposal=_proposal(root),
            ) as (command, _, selected):
                with local.compose_direct_cli_selected_product(command, selected) as product:
                    await plan_direct_cli_selected_product(command, selected, product)
        assert set(planning._SOURCES) == before


async def test_catalog_digest_cannot_restamp_the_original_planning_source(tmp_path, factory):
    from aware_code_semantic_contract_runtime.dependency_inputs import (
        SemanticDependencyPlanningInput,
    )

    async with prepared(tmp_path, factory) as (_, command, selected, _, correspondence, entry):
        context, _ = command.sources.declaration_scope_runtime.inspect_inputs(selected)
        original = SemanticDependencyPlanningInput(context.package, context.source_identity_digest, ())
        assert original.source_identity_digest != entry.source_identity_digest
        validate_declaration_product_planning_input(correspondence, entry, original)
        changed = replace(original, source_identity_digest=entry.source_identity_digest)
        with pytest.raises(RuntimeError, match="source differs"):
            validate_declaration_product_planning_input(correspondence, entry, changed)
        with pytest.raises(RuntimeError, match="unavailable"):
            validate_declaration_product_planning_input(correspondence, entry, original)
