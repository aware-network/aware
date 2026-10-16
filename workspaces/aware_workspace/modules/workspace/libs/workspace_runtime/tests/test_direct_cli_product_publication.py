"""Original source/factory into the existing coordinator and durable backing."""

from contextlib import ExitStack

import pytest
from aware_code_retained_registry_policy_runtime import direct_host, product_execution
from aware_code_semantic_contract_runtime import ContractViolation
from aware_local_service_state_sqlite import SqliteLocalOperationalStateStore
from test_direct_cli_product_execution import authored
from test_direct_cli_selected_host import _proposal, sources
from test_direct_cli_selected_host import factory as _factory

from aware_workspace_runtime import direct_cli_product_execution as execution
from aware_workspace_runtime import direct_cli_product_publication as publication
from aware_workspace_runtime import direct_cli_selected_host as local
from aware_workspace_runtime import direct_command_composition as composition
from aware_workspace_runtime import materialization_graph_coordinator as coordinator
from aware_workspace_runtime.direct_cli_product_planning import (
    plan_direct_cli_selected_product,
)
from aware_workspace_runtime.direct_cli_product_publication import (
    publish_direct_cli_selected_product,
    validate_direct_cli_graph_scope,
)
from aware_workspace_runtime.semantic_dependency_graph_codec import (
    decode_workspace_semantic_materialization_graph_result_v2,
)
from aware_workspace_runtime.semantic_materialization_publication import (
    DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
    WorkspaceSemanticMaterializationPublisher,
)

factory = _factory


async def test_original_local_graph_executes_publishes_and_rereads(
    tmp_path, factory, monkeypatch
):
    import os

    from aware_attention_definition_contract_runtime_provider.selected_factory import (
        AttentionSelectedDefinitionProvider,
    )
    from aware_code_semantic_contract_runtime.semantic_input_producer import (
        validate_registered_semantic_input_result,
    )
    # isort: split
    from aware_workspace_runtime import materialization_operation as operation
    from aware_workspace_runtime import materialization_session as journal
    from aware_workspace_runtime.declaration_scope_admission import (
        WorkspaceDeclarationScopeRuntime,
    )
    # isort: split
    from materialization_latency_report import BoundaryTimings, LatencyReport

    destination = os.environ.get("AWARE_MATERIALIZATION_BENCHMARK_REPORT")
    trace = LatencyReport(enabled=destination is not None)
    succeeded = False
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setattr(
        local, "admit_installed_semantic_stage_factory", lambda key: factory
    )
    try:
        marker = trace.start("fixture_source_setup")
        async with sources(tmp_path, authored) as (root, _, _, borrowed, _, _):
            trace.stop(marker)
            marker = trace.start("command_source_admission")
            with composition._compose_direct_workspace_command_source(
                session=borrowed._session,
                store=borrowed._store,
                proposal=_proposal(root),
            ) as (command, _, source):
                trace.stop(marker)
                marker = trace.start("selected_factory_catalog_composition")
                with (
                    ExitStack() as retained,
                    local.compose_direct_cli_selected_product(command, source) as product,
                ):
                    trace.stop(marker)
                    trace.attach("selection", {
                        "provider_key": product.provider_key,
                        "requested_role": product.requested_role,
                        "package_ref": product.package_ref,
                    })
                    marker = trace.start("graph_planning_and_plan_encoding")
                    planned = await plan_direct_cli_selected_product(
                        command, source, product
                    )
                    trace.stop(marker)
                    trace.attach("planning_reported_timings", [
                        {"stage": item.stage, "elapsed_ns": item.elapsed_ns}
                        for item in planned.plan.timing_entries
                    ])
                    trace.attach("planning_counters", [
                        {"counter": item.counter, "value": item.value}
                        for item in planned.plan.counter_entries
                    ])
                    marker = trace.start("input_preparation_execution_publication_encoding")
                    with BoundaryTimings(trace, marker, (
                        ("input_preparation", execution.prepare_direct_cli_selected_product_inputs),
                        ("graph_scope_validation", publication.validate_direct_cli_graph_scope),
                        ("graph_execution_admission", publication._issue_workspace_direct_command_graph_execution),
                        ("graph_coordinator", coordinator.WorkspaceSemanticMaterializationGraphCoordinator.execute),
                        ("node_operation", operation.WorkspaceMaterializeOperation._execute_graph_v2),
                        ("code_execution_admission", operation.issue_selected_provider_execution),
                        ("tracked_code_execution", operation.execute_selected_provider),
                        ("owner_receiver_execution", AttentionSelectedDefinitionProvider.execute_selected),
                        ("source_input_validation", WorkspaceDeclarationScopeRuntime.validate_semantic_input_source),
                        ("code_source_result_validation", validate_registered_semantic_input_result),
                        ("graph_result_encoding", publication.encode_workspace_semantic_materialization_graph_result_v2),
                        ("package_publication", WorkspaceSemanticMaterializationPublisher._publish_graph_v2),
                        ("package_head_reread", WorkspaceSemanticMaterializationPublisher._read_graph_v2_head),
                        ("session_append", journal.WorkspaceMaterializationSessionJournal._append_graph_v2),
                    ), enabled=destination is not None and os.environ.get(
                        "AWARE_MATERIALIZATION_BENCHMARK_BOUNDARIES"
                    ) == "1"):
                        published = await publish_direct_cli_selected_product(
                            command, source, product, planned, retention=retained
                        )
                    trace.stop(marker)
                    trace.attach("publication_reported_timings", {
                        "total_before_disposal_ns": published.elapsed_ns,
                        "graph_admission_ns": published.admission_ns,
                        "accounting": "nested aggregates, not separate owner/publication spans",
                    })
                    marker = trace.start("result_decode_and_assertions")
                    result = decode_workspace_semantic_materialization_graph_result_v2(
                        published.wire,
                        plan_result=planned.plan,
                        expected=published.result,
                    )
                    assert result.status == "succeeded"
                    (node,) = result.ordered_node_results
                    assert node.outcome == "executed"
                    assert node.result_head_revision == 1
                    assert node.result_coordinate.role == "attention_definition_manifest"
                    assert node.publication_receipt.head_advanced
                    assert (
                        node.package_head_reread_evidence.materialization_head_digest
                        == node.result_head_digest
                    )
                    trace.stop(marker)
                    trace.attach("result", {
                        "status": result.status,
                        "node_count": len(result.ordered_node_results),
                        "head_revision": node.result_head_revision,
                        "body_bytes": node.result_coordinate.size_bytes,
                        "body_digest": node.result_coordinate.digest.value,
                        "canonical_graph_result_bytes": len(published.wire),
                        "head_positive_reread": True,
                    })
                    marker = trace.start("selected_product_and_inputs_cleanup")
                trace.stop(marker)
                marker = trace.start("post_cleanup_command_currentness")
                composition._require_live_direct_workspace_command(command)
                trace.stop(marker)
                marker = trace.start("command_source_cleanup")
            trace.stop(marker)
            marker = trace.start("fixture_source_cleanup")
        trace.stop(marker)
        succeeded = True
    finally:
        if destination is not None:
            trace.write(trace.finish(succeeded=succeeded), destination)


def test_unknown_scope_cannot_issue_direct_graph_authority():
    with pytest.raises(TypeError, match="original direct graph scope"):
        validate_direct_cli_graph_scope(object())


async def test_head_race_refuses_before_owner_inputs(tmp_path, factory, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setattr(
        local, "admit_installed_semantic_stage_factory", lambda key: factory
    )
    calls = []

    async def forbidden(*args, **kwargs):
        calls.append(True)
        pytest.fail("changed HEAD reached owner input production")

    monkeypatch.setattr(
        publication, "prepare_direct_cli_selected_product_inputs", forbidden
    )
    async with sources(tmp_path, authored) as (root, _, _, borrowed, _, _):
        with (
            composition._compose_direct_workspace_command_source(
                session=borrowed._session,
                store=borrowed._store,
                proposal=_proposal(root),
            ) as (command, _, source),
            ExitStack() as retained,
            local.compose_direct_cli_selected_product(command, source) as product,
        ):
            planned = await plan_direct_cli_selected_product(command, source, product)
            (database,) = (tmp_path / "state").rglob("heads.sqlite3")
            state_store = SqliteLocalOperationalStateStore(database)
            state_store.compare_and_set(
                DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
                product.package_ref,
                expected_revision=0,
                value={"race": True},
            )
            with pytest.raises(ContractViolation, match="head moved"):
                await publish_direct_cli_selected_product(
                    command, source, product, planned, retention=retained
                )
    assert not calls


async def test_post_cas_source_failure_preserves_durable_head(
    tmp_path, factory, monkeypatch
):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setattr(
        local, "admit_installed_semantic_stage_factory", lambda key: factory
    )
    original = WorkspaceSemanticMaterializationPublisher._publish_graph_v2
    committed = []
    async with sources(tmp_path, authored) as (root, _, _, borrowed, _, _):

        def mutate(publisher, **kwargs):
            result = original(publisher, **kwargs)
            committed.append(result)
            path = root / "consumer/modules/main/attention/aware.attention.toml"
            path.write_bytes(path.read_bytes() + b"\n# changed after CAS\n")
            return result

        monkeypatch.setattr(
            WorkspaceSemanticMaterializationPublisher, "_publish_graph_v2", mutate
        )
        with pytest.raises((RuntimeError, BaseExceptionGroup)) as rejected:  # noqa: SIM117 - independently inspect committed evidence after unwind
            with composition._compose_direct_workspace_command_source(
                session=borrowed._session,
                store=borrowed._store,
                proposal=_proposal(root),
            ) as (command, _, source):
                with (
                    ExitStack() as retained,
                    local.compose_direct_cli_selected_product(
                        command, source
                    ) as product,
                ):
                    planned = await plan_direct_cli_selected_product(
                        command, source, product
                    )
                    await publish_direct_cli_selected_product(
                        command, source, product, planned, retention=retained
                    )
        assert committed
        assert "reconciliation" in str(rejected.value) or "unwind" in str(
            rejected.value
        )
        (database,) = (tmp_path / "state").rglob("heads.sqlite3")
        record = SqliteLocalOperationalStateStore(database).read(
            DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
            committed[0][0].head.package.package_ref,
        )
        assert record.revision == 1
        assert record.value["head_digest"] == committed[0][0].head.head_digest.value
        assert not publication._SCOPES


@pytest.mark.parametrize("entrance", ["inputs", "publication"])
@pytest.mark.parametrize("attribute", ["__hash__", "__eq__"])
@pytest.mark.parametrize("behavior", ["returns", "raises", "restores"])
async def test_host_identity_substitution_is_terminal_without_behavior(
    tmp_path, factory, monkeypatch, entrance, attribute, behavior
):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setattr(
        local, "admit_installed_semantic_stage_factory", lambda key: factory
    )
    calls = []

    def hostile(*args):
        calls.append(attribute)
        if behavior == "restores":
            delattr(direct_host.DirectValidationHost, attribute)
        if behavior == "raises":
            raise RuntimeError("host identity behavior executed")
        return 1

    def forbidden_publish(*args, **kwargs):
        calls.append("HEAD write")
        pytest.fail("rejected host reached publication")

    monkeypatch.setattr(
        WorkspaceSemanticMaterializationPublisher, "_publish_graph_v2", forbidden_publish
    )
    with (
        monkeypatch.context() as poison,
        pytest.raises(ContractViolation, match="identity behavior substituted"),
    ):
        async with sources(tmp_path, authored) as (root, _, _, borrowed, _, _):
            with (
                composition._compose_direct_workspace_command_source(
                    session=borrowed._session,
                    store=borrowed._store,
                    proposal=_proposal(root),
                ) as (command, _, source),
                ExitStack() as retained,
                local.compose_direct_cli_selected_product(command, source) as product,
            ):
                host = product.host.code_host
                planned = (
                    await plan_direct_cli_selected_product(command, source, product)
                    if entrance == "publication"
                    else None
                )
                poison.setattr(direct_host.DirectValidationHost, attribute, hostile)
                with pytest.raises(ContractViolation, match="identity behavior substituted"):
                    if entrance == "inputs":
                        await execution.prepare_direct_cli_selected_product_inputs(
                            command, source, product, retention=retained
                        )
                    else:
                        await publish_direct_cli_selected_product(
                            command, source, product, planned, retention=retained
                        )
                assert not calls
                assert direct_host._identity_registry_get(direct_host._HOSTS, host).closed
                # Restore while the original host is still retained: rejection is final.
                delattr(direct_host.DirectValidationHost, attribute)
                with pytest.raises(ContractViolation, match="unavailable|closed"):
                    execution.validate_direct_cli_selected_host(product)
                # Persistent substitution must also be harmless during original cleanup.
                setattr(direct_host.DirectValidationHost, attribute, hostile)
    assert direct_host._identity_registry_get(direct_host._HOSTS, host) is None
    assert composition._selected_input_identity_lookup(
        composition._POLICY_HOSTS, host
    ) is None
    assert not calls
    assert not publication._SCOPES
    assert not any(record.host is host for record in product_execution._READ_ORIGINS.values())
    for database in (tmp_path / "state").rglob("heads.sqlite3"):
        assert SqliteLocalOperationalStateStore(database).read(
            DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
            product.package_ref,
            include_deleted=True,
        ) is None


@pytest.mark.parametrize("committed", [False, True])
@pytest.mark.parametrize("cleanup_failure", [False, True])
async def test_interruption_retires_scope_and_preserves_original_failure(
    tmp_path, factory, monkeypatch, committed, cleanup_failure
):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setattr(
        local, "admit_installed_semantic_stage_factory", lambda key: factory
    )
    interruption = KeyboardInterrupt("original graph interruption")
    scopes, admissions, receipts = [], [], []
    original_prepare = publication.prepare_direct_cli_selected_product_inputs
    original_publish = WorkspaceSemanticMaterializationPublisher._publish_graph_v2
    original_dispose = publication._dispose_workspace_direct_command_graph_execution

    async def prepare(*args, **kwargs):
        scopes.append(publication._SCOPES[-1][1])
        return await original_prepare(*args, **kwargs)

    def interrupt(*args, **kwargs):
        raise interruption

    def publish_then_interrupt(publisher, **kwargs):
        receipts.append(original_publish(publisher, **kwargs))
        raise interruption

    def dispose(admission, *, scope):
        admissions.append(admission)
        assert coordinator._EXECUTIONS[admission].status == "interrupted_resumable"
        original_dispose(admission, scope=scope)
        if cleanup_failure:
            raise RuntimeError("disposal also failed")

    monkeypatch.setattr(publication, "prepare_direct_cli_selected_product_inputs", prepare)
    monkeypatch.setattr(publication, "_dispose_workspace_direct_command_graph_execution", dispose)
    if committed:
        monkeypatch.setattr(
            WorkspaceSemanticMaterializationPublisher, "_publish_graph_v2", publish_then_interrupt
        )
    else:
        monkeypatch.setattr(publication, "_selected_input", interrupt)
    async with sources(tmp_path, authored) as (root, _, _, borrowed, _, _):
        with (
            composition._compose_direct_workspace_command_source(
                session=borrowed._session,
                store=borrowed._store,
                proposal=_proposal(root),
            ) as (command, _, source),
            ExitStack() as retained,
            local.compose_direct_cli_selected_product(command, source) as product,
        ):
            host = product.host.code_host
            planned = await plan_direct_cli_selected_product(command, source, product)
            with pytest.raises(KeyboardInterrupt) as rejected:
                await publish_direct_cli_selected_product(
                    command, source, product, planned, retention=retained
                )
            assert rejected.value is interruption
            assert not publication._SCOPES
            assert all(admission not in coordinator._EXECUTIONS for admission in admissions)
            (retired,) = scopes
            assert retired.terminal
            assert retired.command is retired.prepared is retired.product is None
            assert retired.operation is retired.ports is retired.backing is None
            (database,) = (tmp_path / "state").rglob("heads.sqlite3")
            record = SqliteLocalOperationalStateStore(database).read(
                DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
                product.package_ref,
                include_deleted=True,
            )
            if committed:
                assert record.revision == 1
                assert record.value["head_digest"] == receipts[0][0].head.head_digest.value
            else:
                assert record is None
        assert not any(record.host is host for record in product_execution._READ_ORIGINS.values())
        assert not any(record.host is host for _, record in composition._SELECTED_INPUT_NODES)
