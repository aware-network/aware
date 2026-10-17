"""Public continuation selects original candidates; owner demand selects nodes."""

import asyncio
import json
from contextlib import contextmanager

import pytest

# isort: split

from aware_workspace_command.materialize_command import (
    _continue_direct_materialize_profile,
    handle_workspace_materialize_command,
)
from aware_workspace_materialize_transport import WorkspaceMaterializeCommandProposalV3
from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime import direct_cli_selected_host as local
from aware_workspace_runtime import direct_command_composition as composition

# isort: split

from test_dependency_scope_admission import fixture as sources
from test_direct_cli_dependency_planning import ROOT_KEY, SUPPLIER_KEY, _repository
from test_materialize_command import _args
from test_original_supplier_fulfillment import owners as original_owners

owners = original_owners


@pytest.mark.parametrize("owners", [True], indirect=True)
@pytest.mark.parametrize("used", [True, False])
def test_public_cli_plan_uses_only_owner_demanded_nodes(tmp_path, monkeypatch, capsys, owners, used):
    admitted, calls = owners
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "cli-state"))
    monkeypatch.setattr(local, "admit_installed_semantic_stage_factory", lambda key: admitted[key][0])
    profiles = {key: profile for key, (_, profile) in admitted.items()}

    async def authored():
        async with sources(tmp_path, lambda root: _repository(root, profiles, used=used)) as (root, *_):
            return root

    root = asyncio.run(authored())
    assert handle_workspace_materialize_command(args=_args(
        repo_root=str(root), workspace_toml="consumer/aware.workspace.toml",
        package=[], package_address="Consumer:main:consumer", plan=True,
    )) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["outcome"] == "succeeded" and result["terminal_stage"] == "graph_plan"
    counters = {item["counter"]: item["value"] for item in result["host_counters"]}
    assert counters["graph_node_count"] == (2 if used else 1)
    assert counters["graph_edge_count"] == (2 if used else 0)
    assert counters["graph_execution_count"] == 0
    assert not any(kind in ("execution_input", "execute") for kind, _, _ in calls)
    if not used:
        assert not any(kind == "plan" and key == SUPPLIER_KEY for kind, _, key in calls)


@pytest.mark.parametrize("owners", [True], indirect=True)
@pytest.mark.parametrize("used,execute", [(True, False), (False, False), (True, True)])
async def test_public_continuation_derives_candidates_and_runs_original_graph(
    tmp_path, monkeypatch, owners, used, execute,
):
    admitted, calls = owners
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "public-state"))
    monkeypatch.setattr(local, "admit_installed_semantic_stage_factory", lambda key: admitted[key][0])
    profiles = {key: profile for key, (_, profile) in admitted.items()}
    async with sources(tmp_path, lambda root: _repository(root, profiles, used=used)) as (root, *_):
        proposal = WorkspaceMaterializeCommandProposalV3.create(
            attempt_ref="proof:public-product-candidates", participant_checkout_root=str(root),
            workspace_manifest_name="consumer/aware.workspace.toml",
            package_address=("Consumer", "main", "consumer"), plan_only=not execute,
        )
        inspection, diagnostic, published = await _continue_direct_materialize_profile(proposal=proposal)
        assert diagnostic is None
        assert inspection.graph_node_count == (2 if used else 1)
        assert inspection.graph_edge_count == (2 if used else 0)
        if execute:
            assert published is not None
            assert len(published.result.ordered_node_results) == 2
            assert len(published.result.ordered_fulfilled_products) == 2
            assert all(item.package_head_reread_evidence.materialization_head_revision == 1
                for item in published.result.ordered_node_results)
        else:
            assert published is None
        assert [kind for kind, _, key in calls if key == ROOT_KEY] == (
            ["source", "plan", "execution_input", "execute"] if execute else ["source", "plan"])
        assert [kind for kind, _, key in calls if key == SUPPLIER_KEY] == (
            ["source", "plan", "execution_input", "execute"] if execute
            else ["source", "plan"] if used else ["source"])


@pytest.mark.parametrize("owners", [True], indirect=True)
async def test_candidate_source_change_refuses_before_factory_contact(tmp_path, monkeypatch, owners):
    admitted, calls = owners
    profiles = {key: profile for key, (_, profile) in admitted.items()}
    original = composition._compose_direct_workspace_selected_package_source
    factory_calls = []
    monkeypatch.setattr(local, "admit_installed_semantic_stage_factory", lambda key: factory_calls.append(key))
    async with sources(tmp_path, lambda root: _repository(root, profiles)) as (root, _, _, borrowed, *_):
        proposal = WorkspaceMaterializeCommandProposalV3.create(
            attempt_ref="proof:changed-candidate", participant_checkout_root=str(root),
            workspace_manifest_name="consumer/aware.workspace.toml",
            package_address=("Consumer", "main", "consumer"), plan_only=True,
        )
        with composition._compose_direct_workspace_command_source(
            session=borrowed._session, store=borrowed._store, proposal=proposal,
        ) as (command, _, selected):
            @contextmanager
            def changed(*args, **kwargs):
                with original(*args, **kwargs) as handle:
                    (root / "consumer/modules/main/supplier/source.aware").write_bytes(b"changed")
                    yield handle

            monkeypatch.setattr(composition, "_compose_direct_workspace_selected_package_source", changed)
            with pytest.raises(SourceObservationUnavailable), local.compose_direct_cli_product_candidates(command, selected):
                raise AssertionError("changed original supplier admitted")
    assert factory_calls == [] and calls == []
