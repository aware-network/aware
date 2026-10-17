"""Original source/factory into the existing coordinator and durable backing."""

from contextlib import ExitStack, asynccontextmanager

import pytest
from aware_code_retained_registry_policy_runtime import direct_host, product_execution
from aware_code_semantic_contract_runtime import ContractViolation
from aware_local_service_state_sqlite import SqliteLocalOperationalStateStore
from test_direct_cli_product_execution import authored
from test_direct_cli_selected_host import _proposal, sources
from test_direct_cli_selected_host import factory as _factory

# isort: split
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


@asynccontextmanager
async def _local_graph_source_scope(tmp_path, monkeypatch, *, with_input=True):
    """Real Workspace source/input lifetime; graph metadata is a local fixture."""
    import os
    from threading import get_ident
    from types import SimpleNamespace

    from test_selected_input_read_node import open_read, read_fixture

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            if with_input:
                node.prepare_source_expectation(
                    use_ref="graph-window", stage="pre_request",
                    source_coordinates=value.coordinates,
                )
            entry, intent, required = object(), object(), object()
            pair = SimpleNamespace(workspace=SimpleNamespace(package=lambda _: entry))
            value.command.catalog_host._result = pair
            product = SimpleNamespace(
                host=SimpleNamespace(code_host=value.host, catalog_pair=pair),
                policy=object(), package_ref="local-graph-fixture",
            )
            binding = SimpleNamespace(package_entry=entry, code_intent=intent,
                                      required_result_products=(required,))
            planned = SimpleNamespace(plan=SimpleNamespace(
                graph=SimpleNamespace(edges=()),
                graph_execution_binding=SimpleNamespace(ordered_node_bindings=(binding,)),
            ))
            state = publication._Scope(
                value.command, value.selected, product, planned, None, os.getpid(), get_ident(),
                prepared=SimpleNamespace(node=node),
            )
            holder = object.__new__(publication._DirectCLIProductGraphScope)
            publication._SCOPES.append((holder, state))
            observed = []

            def host_check(original):
                assert original is product
                observed.append(value.issuer._semantic_source_window is not None)

            monkeypatch.setattr(publication, "validate_direct_cli_selected_host", host_check)
            monkeypatch.setattr(publication, "derive_selected_root_intent", lambda *args: (intent, required))
            try:
                yield value, holder, state, observed
            finally:
                publication._SCOPES[:] = [(key, record) for key, record in publication._SCOPES if key is not holder]


@pytest.mark.parametrize("with_input", [False, True])
async def test_graph_window_reuses_original_source_or_registered_input(tmp_path, monkeypatch, with_input):
    async with _local_graph_source_scope(tmp_path, monkeypatch, with_input=with_input) as (value, holder, state, observed):
        validate_direct_cli_graph_scope(holder)
        assert observed == [True]
        assert value.issuer._semantic_source_window is None
        assert not state.terminal


@pytest.mark.parametrize("target", ["body", "declaration", "interrupt"])
async def test_graph_window_terminal_checks_reject_and_cannot_resume(tmp_path, monkeypatch, target):
    async with _local_graph_source_scope(tmp_path, monkeypatch) as (value, holder, state, _):
        original = publication.derive_selected_root_intent
        path = value.root / (
            "workspaces/network/modules/main/package/a.bin" if target == "body"
            else "workspaces/network/aware.workspace.toml"
        )
        before = path.read_bytes()

        def poison(*args):
            result = original(*args)
            if target == "interrupt":
                raise KeyboardInterrupt("graph-window interruption")
            path.write_bytes(before + b"\nchanged")
            return result

        with monkeypatch.context() as patch:
            patch.setattr(publication, "derive_selected_root_intent", poison)
            with pytest.raises((RuntimeError, ValueError, BaseExceptionGroup, KeyboardInterrupt)):
                validate_direct_cli_graph_scope(holder)
        path.write_bytes(before)
        assert value.issuer._semantic_source_window is None
        assert state.terminal
        with pytest.raises(ContractViolation, match="terminal"):
            validate_direct_cli_graph_scope(holder)


@pytest.mark.parametrize("binding", ["scope", "input_reader", "dispatch"])
@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
async def test_graph_window_rejects_substituted_entrances_without_calls(tmp_path, monkeypatch, binding, mode):
    async with _local_graph_source_scope(tmp_path, monkeypatch) as (value, holder, state, _):
        owner, name = ((publication, "_scope") if binding == "scope" else
                       (composition, "_selected_input_read_record" if binding == "input_reader" else "_original_group_method"))
        original = getattr(owner, name)
        calls = []

        def hostile(*args, **kwargs):
            calls.append(True)
            if mode == "restore":
                setattr(owner, name, original)
                return original(*args, **kwargs)
            if mode == "raise":
                raise AssertionError("substituted entrance executed")
            return None

        with monkeypatch.context() as patch:
            patch.setattr(owner, name, hostile)
            with pytest.raises(ContractViolation, match="entrance changed"):
                validate_direct_cli_graph_scope(holder)
        assert not calls
        assert state.terminal
        assert value.issuer._semantic_source_window is None
        with pytest.raises(ContractViolation, match="terminal"):
            validate_direct_cli_graph_scope(holder)


@pytest.mark.parametrize("target", ["initial_descriptor", "terminal_input_alias", "terminal_input_code", "terminal_read_return"])
@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
async def test_graph_window_rejects_late_dispatch_substitution(tmp_path, monkeypatch, target, mode):
    import sys

    async with _local_graph_source_scope(tmp_path, monkeypatch) as (value, holder, state, _):
        scope_code = publication._scope.__code__
        original_scope = publication._scope
        input_reader = composition._selected_input_read_record
        input_code = input_reader.__code__
        original_descriptor = publication.inspect.getattr_static
        calls = []
        probe = {"calls": calls, "mode": mode, "original": input_reader, "code": input_code}
        reached = []

        def hostile(*args, **kwargs):
            calls.append(True)
            if mode == "raise":
                raise AssertionError("late substituted dispatch executed")
            if mode == "restore":
                if target == "initial_descriptor":
                    publication.inspect.getattr_static = original_descriptor
                    return original_descriptor(*args, **kwargs)
                if target == "terminal_read_return":
                    publication._scope = original_scope
                    return original_scope(*args, **kwargs)
                composition._selected_input_read_record = input_reader
                return input_reader(*args, **kwargs)
            return None

        # A closure-free replacement exercises mutation of the captured function
        # itself, rather than replacing only the module's alias.
        def poison(*args, **kwargs):
            current_probe = globals()["_graph_window_probe"]
            current_probe["calls"].append(True)
            if current_probe["mode"] == "raise":
                raise AssertionError("late substituted function code executed")
            if current_probe["mode"] == "restore":
                current_probe["original"].__code__ = current_probe["code"]
                return current_probe["original"](*args, **kwargs)
            return None

        poisoned_code = poison.__code__

        def at_original_return(frame, event, result):
            if (
                target == "terminal_read_return" and len(reached) == 2
                and event == "return" and frame.f_code is input_code
            ):
                publication._scope = hostile
            if event == "return" and frame.f_code is scope_code:
                reached.append(True)
                desired = 1 if target == "initial_descriptor" else 2
                if len(reached) == desired:
                    if target == "initial_descriptor":
                        publication.inspect.getattr_static = hostile
                    elif target == "terminal_input_alias":
                        composition._selected_input_read_record = hostile
                    elif target == "terminal_input_code":
                        input_reader.__code__ = poisoned_code

        prior = sys.getprofile()
        with monkeypatch.context() as patch:
            patch.setitem(input_reader.__globals__, "_graph_window_probe", probe)
            try:
                sys.setprofile(at_original_return)
                with pytest.raises(ContractViolation, match="entrance changed"):
                    validate_direct_cli_graph_scope(holder)
            finally:
                sys.setprofile(prior)
                publication.inspect.getattr_static = original_descriptor
                publication._scope = original_scope
                composition._selected_input_read_record = input_reader
                input_reader.__code__ = input_code
        assert len(reached) == (1 if target == "initial_descriptor" else 2)
        assert calls == []
        assert state.terminal
        assert value.issuer._semantic_source_window is None
        with pytest.raises(ContractViolation, match="terminal"):
            validate_direct_cli_graph_scope(holder)


@pytest.mark.parametrize("target", ["input_return", "first_retained_return", "window_return"])
@pytest.mark.parametrize("binding", ["alias", "code"])
@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
async def test_graph_window_checks_each_original_dispatch(tmp_path, monkeypatch, target, binding, mode):
    import sys

    async with _local_graph_source_scope(tmp_path, monkeypatch) as (value, holder, state, _):
        state.prepared.node.prepare_source_expectation(
            use_ref="graph-window-second", stage="pre_request", source_coordinates=value.coordinates,
        )
        original = composition._original_group_method
        owner = original.__globals__
        code = original.__code__
        input_code = composition._selected_input_read_record.__code__
        calls, triggered = [], []
        probe = {"calls": calls, "mode": mode, "original": original, "code": code}

        def hostile(*args, **kwargs):
            calls.append(True)
            if mode == "raise":
                raise AssertionError("substituted graph dispatcher executed")
            if mode == "restore":
                composition._original_group_method = original
                return original(*args, **kwargs)
            return None

        def poison_code():
            # Preserve the exact attack with the implementation's actual
            # closure arity; the private dispatcher's shape is not an ABI.
            names = ["cell_" + str(index) for index in range(len(code.co_freevars))]
            declaration = "".join("    " + name + " = None\n" for name in names)
            body = (
                "    def poison(*args, **kwargs):\n"
                "        _ = (" + ",".join(names) + ("," if names else "") + ")\n"
                "        current_probe = globals()[\"_graph_dispatch_probe\"]\n"
                "        current_probe[\"calls\"].append(True)\n"
                "        if current_probe[\"mode\"] == \"raise\":\n"
                "            raise AssertionError(\"substituted dispatcher code executed\")\n"
                "        if current_probe[\"mode\"] == \"restore\":\n"
                "            current_probe[\"original\"].__code__ = current_probe[\"code\"]\n"
                "            return current_probe[\"original\"](*args, **kwargs)\n"
                "        return None\n"
            )
            namespace = {}
            exec("def factory():\n" + declaration + body + "    return poison\n", namespace)  # noqa: S102 - fixed local code-restamp proof, no external input
            return namespace["factory"]().__code__

        replacement_code = poison_code()
        assert len(replacement_code.co_freevars) == len(code.co_freevars)

        def at_original_return(frame, event, result):
            if event != "return" or triggered:
                return
            selected = (
                target == "input_return" and frame.f_code is input_code
            ) or (
                frame.f_code is code and frame.f_locals.get("name") == (
                    "_pre_request_record" if target == "first_retained_return"
                    else "_original_semantic_source_window" if target == "window_return"
                    else None
                )
            )
            if selected:
                triggered.append(True)
                if binding == "alias":
                    composition._original_group_method = hostile
                else:
                    original.__code__ = replacement_code

        prior = sys.getprofile()
        with monkeypatch.context() as patch:
            patch.setitem(owner, "_graph_dispatch_probe", probe)
            try:
                sys.setprofile(at_original_return)
                with pytest.raises(ContractViolation, match="entrance changed"):
                    validate_direct_cli_graph_scope(holder)
            finally:
                sys.setprofile(prior)
                composition._original_group_method = original
                original.__code__ = code
        assert triggered == [True]
        assert calls == []
        assert state.terminal
        assert value.issuer._semantic_source_window is None
        with pytest.raises(ContractViolation, match="terminal"):
            validate_direct_cli_graph_scope(holder)


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
                    # Graph/input scopes have already closed. Delivery is
                    # through the actual publisher's original outer lifetime.
                    from aware_code_retained_registry_policy_runtime import (
                        product_execution_inputs,
                    )
                    from aware_code_semantic_contract_runtime import ContentDigest

                    context = publication.read_direct_cli_product_execution_context(
                        command, product, planned, node_digest=node.node_digest)
                    completion = product_execution_inputs.read_product_execution_input_completion(
                        product.host.code_host, context)
                    with pytest.raises(ContractViolation):
                        publication.read_direct_cli_product_execution_context(command, product, planned,
                            node_digest=ContentDigest.of_bytes(b"unknown node"))
                    assert publication.read_direct_cli_product_execution_context(
                        command, product, planned, node_digest=node.node_digest) is context
                    assert product_execution_inputs.read_product_execution_input_completion(
                        product.host.code_host, context) is completion
                    source_calls = []
                    with monkeypatch.context() as no_source_read:
                        no_source_read.setattr(publication, "_execution_participant",
                            lambda *args: source_calls.append(True))
                        assert publication.read_direct_cli_product_execution_context(
                            command, product, planned, node_digest=node.node_digest) is context
                    assert source_calls == []
                    wire = planned.wire
                    object.__setattr__(planned, "wire", wire + b"\n")
                    with pytest.raises(ContractViolation, match="plan changed"):
                        publication.read_direct_cli_product_execution_context(
                            command, product, planned, node_digest=node.node_digest)
                    object.__setattr__(planned, "wire", wire)
                    with pytest.raises(ContractViolation, match="unavailable"):
                        publication.read_direct_cli_product_execution_context(
                            command, product, planned, node_digest=node.node_digest)
                    assert product_execution_inputs.read_product_execution_input_completion(
                        product.host.code_host, context) is completion
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
        pytest.raises(ContractViolation, match="identity behavior substituted|foreign or closed host"),
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
                record = direct_host._identity_registry_get(direct_host._HOSTS, host)
                assert record is None or record.closed
                # Code may dispose immediately or retain a closed record for
                # composer cleanup. Both are terminal; restoration cannot resume.
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


@pytest.mark.parametrize("phase", ["unprepared", "empty_inputs"])
@pytest.mark.parametrize("target", ["body", "declaration", "journal", "interrupt", "association"])
async def test_graph_fallback_window_terminal_failure_is_irreversible(tmp_path, monkeypatch, phase, target):
    async with _local_graph_source_scope(tmp_path, monkeypatch, with_input=False) as (value, holder, state, observed):
        if phase == "unprepared":
            state.prepared = None
        original = publication.derive_selected_root_intent
        path = value.root / (
            "workspaces/network/modules/main/package/a.bin" if target == "body"
            else "workspaces/network/aware.workspace.toml"
        )
        before = path.read_bytes()
        selected_record = value.issuer._selected_record(value.selected)
        digest = selected_record.digest
        selected = state.source
        def poison(*args):
            result = original(*args)
            assert value.issuer._semantic_source_window is not None
            if target == "interrupt":
                raise KeyboardInterrupt("original fallback interrupted")
            if target == "journal":
                object.__setattr__(selected_record, "digest", type(digest).of_bytes(b"changed original binding"))
            elif target == "association":
                state.source = object()
            else:
                path.write_bytes(before + b"changed")
            return result
        try:
            with monkeypatch.context() as patch:
                patch.setattr(publication, "derive_selected_root_intent", poison)
                with pytest.raises((RuntimeError, ValueError, BaseExceptionGroup, KeyboardInterrupt)):
                    validate_direct_cli_graph_scope(holder)
        finally:
            path.write_bytes(before)
            object.__setattr__(selected_record, "digest", digest)
            state.source = selected
        assert observed == [True]
        assert value.issuer._semantic_source_window is None and state.terminal
        with pytest.raises(ContractViolation, match="terminal"):
            validate_direct_cli_graph_scope(holder)


@pytest.mark.parametrize("phase", ["entry", "inside_window"])
@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
@pytest.mark.parametrize("binding", ["alias", "code"])
async def test_graph_fallback_original_port_is_never_dispatched(tmp_path, monkeypatch, phase, mode, binding):
    async with _local_graph_source_scope(tmp_path, monkeypatch, with_input=False) as (value, holder, state, _):
        state.prepared = None
        kind = type(value.issuer)
        original = vars(kind)["selected_source_validation_scope"]
        host_check = publication.validate_direct_cli_selected_host
        original_code = original.__code__
        calls = []
        count = len(original.__closure__ or ())
        setup = "".join(f"    capture_{i} = None\n" for i in range(count))
        use = "".join(f"        _ = capture_{i}\n" for i in range(count))
        sandbox = {}
        exec("def outer():\n" + setup + "    def hostile(*args, **kwargs):\n" + use  # noqa: S102 -- fixed closure-arity poison, no external input
             + "        probe = globals()['_graph_fallback_probe']\n"
             + "        probe['calls'].append(True)\n"
             + "        if probe['mode'] == 'restore': probe['function'].__code__ = probe['code']\n"
             + "        if probe['mode'] == 'raise': raise RuntimeError('hostile source code')\n"
             + "        return None\n    return hostile\n", sandbox)
        poison_code = sandbox["outer"]().__code__
        def hostile(*args, **kwargs):
            calls.append(True)
            if mode == "restore":
                kind.selected_source_validation_scope = original
            if mode == "raise":
                raise RuntimeError("hostile source port")
        def replace(patch):
            if binding == "alias":
                patch.setattr(kind, "selected_source_validation_scope", hostile)
            else:
                patch.setattr(original, "__code__", poison_code)
        def change(product):
            host_check(product)
            assert value.issuer._semantic_source_window is not None
            replace(monkeypatch)
        with monkeypatch.context() as patch:
            patch.setitem(original.__globals__, "_graph_fallback_probe",
                          {"function": original, "code": original_code, "mode": mode, "calls": calls})
            if phase == "entry":
                replace(patch)
            else:
                patch.setattr(publication, "validate_direct_cli_selected_host", change)
            with pytest.raises((RuntimeError, ValueError, BaseExceptionGroup)):
                validate_direct_cli_graph_scope(holder)
        monkeypatch.undo()
        assert calls == [] and state.terminal
        assert value.issuer._semantic_source_window is None
        with pytest.raises(ContractViolation, match="terminal"):
            validate_direct_cli_graph_scope(holder)
