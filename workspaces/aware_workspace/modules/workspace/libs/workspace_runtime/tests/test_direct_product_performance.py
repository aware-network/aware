"""Reuse admitted interpretation while preserving original byte-currentness."""

import copy
import gc
import sys
from contextlib import asynccontextmanager
from dataclasses import replace

import pytest
from test_declaration_scope_admission import fixture

# isort: split
from aware_workspace_runtime import declaration_scope_admission as admission_module
from aware_workspace_runtime import source_observation as source_module
from aware_workspace_runtime.composition import RetainedWorkspaceCompositionProvider
from aware_workspace_runtime.source_observation_io import SourceObservationUnavailable

_ORIGINAL_DECLARATION_COPY_CODE = (
    admission_module._declaration_validation.copy_retained_declaration_scope.__code__
)


def _declaration_copy_event(frame, event, projection, active):
    """Track genuine copy entry/return despite deliberate argument cleanup."""
    if frame.f_code is not _ORIGINAL_DECLARATION_COPY_CODE:
        return False
    key = id(frame)
    if event == "call" and frame.f_locals.get("value") is projection:
        active.add(key)
    matches = key in active
    if event == "return":
        active.discard(key)
    return matches


@pytest.mark.parametrize("stage", ["opening", "after_check"])
async def test_projection_error_does_not_retain_new_original_journal(
    tmp_path, monkeypatch, stage,
):
    from aware_code_semantic_contract_runtime.retained_declaration_scope_validation import (
        RetainedDeclarationScopeCoordinate,
    )
    from test_selected_input_read_node import open_read, read_fixture

    held = None
    async with read_fixture(tmp_path, monkeypatch) as value:
        issuer = value.issuer
        coordinate_id = id(issuer._checked_declaration_origin(
            issuer._selected_record(value.selected).declaration_record,
        ).projection_coordinate)
        target = (type(issuer).read_selected_package_source if stage == "opening"
                  else type(issuer)._occurrence).__code__
        projection = type(issuer)._source_projection_values.__code__
        armed = []

        def profile(frame, event, arg):
            if (event == "call" and frame.f_code is target
                and frame.f_back.f_code is projection and not armed):
                armed.append(True)
                raise RuntimeError("held projection failure")

        with open_read(value):
            previous = sys.getprofile()
            try:
                sys.setprofile(profile)
                issuer.inspect_inputs(value.selected)
            except RuntimeError as error:
                assert str(error) == "held projection failure"
                held = error
            finally:
                sys.setprofile(previous)
        assert armed and held is not None
        traceback = held.__traceback__
        checked = False
        while traceback is not None:
            if traceback.tb_frame.f_code is projection:
                checked = True
                assert traceback.tb_frame.f_locals.get("origin") is None
            traceback = traceback.tb_next
        assert checked
    # The genuine immutable journal is private to the original issuer. After
    # its natural close, retaining the error must not retain this new custody.
    gc.collect()
    assert not any(type(item) is RetainedDeclarationScopeCoordinate
                   and id(item) == coordinate_id for item in gc.get_objects())
    assert held is not None


async def test_source_projection_checks_fields_without_full_closure_digest_build(
    tmp_path, monkeypatch,
):
    from aware_code_semantic_contract_runtime.retained_declaration_scope import (
        CodeRetainedDependencyScopeClosureV3,
    )
    from test_selected_input_read_node import open_read, read_fixture

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value):
            getter = CodeRetainedDependencyScopeClosureV3.closure_digest.fget.__code__
            calls = []

            def profile(frame, event, arg):
                if event == "call" and frame.f_code is getter:
                    calls.append(True)

            previous = sys.getprofile()
            try:
                sys.setprofile(profile)
                context, inventory, manifest, _, _, _ = value.issuer._source_projection_values(value.selected)
            finally:
                sys.setprofile(previous)
            assert inventory.package == context.package
            assert context.package.manifest_digest == admission_module.ContentDigest.of_bytes(manifest)
            assert calls == []


@pytest.mark.parametrize("target", ["detached", "original", "record"])
async def test_source_projection_uses_independent_commitment_after_original_read(
    tmp_path, monkeypatch, target,
):
    from test_selected_input_read_node import open_read, read_fixture

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value):
            issuer = value.issuer
            original = issuer._checked_declaration_origin(issuer._selected_record(value.selected).declaration_record)
            read_code = type(issuer).read_declaration_scope.__code__
            projection_code = type(issuer)._source_projection_values.__code__
            changed = []
            restore = []

            def profile(frame, event, arg):
                if (event != "return" or frame.f_code is not read_code
                    or frame.f_back.f_code is not projection_code or changed):
                    return
                changed.append(True)
                if target == "record":
                    record = original.record
                    old = record.digest
                    restore.append(lambda: object.__setattr__(record, "digest", old))
                    object.__setattr__(record, "digest", admission_module.ContentDigest.of_bytes(b"restamped"))
                else:
                    projection = arg if target == "detached" else original.projection
                    old = projection.consumer_scope_key
                    restore.append(lambda: object.__setattr__(projection, "consumer_scope_key", old))
                    object.__setattr__(projection, "consumer_scope_key", "forged")

            previous = sys.getprofile()
            try:
                sys.setprofile(profile)
                with pytest.raises(SourceObservationUnavailable):
                    issuer._source_projection_values(value.selected)
            finally:
                sys.setprofile(previous)
                for action in restore:
                    action()
            assert changed


async def test_source_window_shares_one_projection_without_dropping_source_brackets(
    tmp_path, monkeypatch,
):
    from test_selected_input_read_node import open_read, read_fixture

    # isort: split
    from aware_workspace_runtime import declaration_scope_admission as admission

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            expected = node.prepare_source_expectation(
                use_ref="joint-projections", stage="pre_request",
                source_coordinates=value.coordinates,
            )
            selected_code = source_module.WorkspaceSourceObservationRuntime.revalidate_selected_package.__code__
            declaration_code = source_module.WorkspaceSourceObservationRuntime.revalidate_declarations.__code__
            closure_code = admission.WorkspaceDeclarationScopeRuntime._closure.__code__
            counts = {selected_code: 0, declaration_code: 0, closure_code: 0}

            def profile(frame, event, arg):
                if event == "call" and frame.f_code in counts:
                    counts[frame.f_code] += 1

            previous = sys.getprofile()
            try:
                sys.setprofile(profile)
                value.issuer.read_selected_package_source(value.selected)
                value.issuer.read_declaration_scope(
                    value.issuer._selected_record(value.selected).declaration,
                )
                separate = counts.copy()
                counts.update(dict.fromkeys(counts, 0))
                binding, closure = value.issuer._read_source_projection_pair(value.selected, terminal=True)
                shared = counts.copy()
            finally:
                sys.setprofile(previous)
            assert shared[selected_code] == separate[selected_code] == 2
            assert shared[declaration_code] == 4 < separate[declaration_code]
            assert shared[closure_code] == 1 < separate[closure_code]
            assert binding.expectation.closure_digest == closure.closure_digest
            value.issuer.validate_semantic_input_source(value.selected, expected=expected)


@pytest.mark.parametrize("method", ["_source_projection_pair", "_read_source_projection_pair", "_closure", "_check_declaration_projection_result"])
@pytest.mark.parametrize("location", ["instance", "class", "table"])
@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
@pytest.mark.parametrize("phase", ["entry", "return"])
async def test_shared_projection_rejects_substituted_dispatch_without_calls(
    tmp_path, monkeypatch, method, location, mode, phase,
):
    from test_selected_input_read_node import open_read, read_fixture

    # isort: split
    from aware_workspace_runtime import declaration_scope_admission as admission

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            expected = node.prepare_source_expectation(
                use_ref="joint-poison", stage="pre_request",
                source_coordinates=value.coordinates,
            )
            retained = value.issuer._pre_request_record(value.selected, expected)
            calls = []
            original = admission._GROUP_METHOD_FUNCTIONS[method]
            armed = False

            def restore():
                if location == "table":
                    admission._GROUP_METHOD_FUNCTIONS[method] = original
                elif location == "instance":
                    delattr(value.issuer, method)
                else:
                    setattr(type(value.issuer), method, original)

            def hostile(*args, **kwargs):
                calls.append(True)
                if mode == "restore":
                    restore()
                if mode == "raise":
                    raise RuntimeError("substituted projection dispatch")

            def install():
                if location == "table":
                    monkeypatch.setitem(admission._GROUP_METHOD_FUNCTIONS, method, hostile)
                else:
                    monkeypatch.setattr(value.issuer if location == "instance" else type(value.issuer), method, hostile)

            code = admission.WorkspaceDeclarationScopeRuntime._source_projection_pair.__code__

            def profile(frame, event, arg):
                nonlocal armed
                if not armed and event == "return" and frame.f_code is code:
                    armed = True
                    install()

            previous = sys.getprofile()
            try:
                if phase == "entry":
                    armed = True
                    install()
                else:
                    sys.setprofile(profile)
                with pytest.raises((SourceObservationUnavailable, BaseExceptionGroup)):
                    node.validate()
            finally:
                sys.setprofile(previous)
                monkeypatch.undo()
            assert armed and calls == []
            assert not retained.live
            assert value.issuer._semantic_source_window is None
            with pytest.raises(RuntimeError, match="terminal"):
                node.validate()


@pytest.mark.parametrize("target", ["closure", "binding", "coherent_binding", "profile", "package", "interrupt"])
async def test_shared_projection_terminal_rejects_changes_after_pair_construction(
    tmp_path, monkeypatch, target,
):
    from test_selected_input_read_node import open_read, read_fixture

    # isort: split
    from aware_workspace_runtime import declaration_scope_admission as admission

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            expected = node.prepare_source_expectation(
                use_ref="joint-terminal", stage="pre_request",
                source_coordinates=value.coordinates,
            )
            retained = value.issuer._pre_request_record(value.selected, expected)
            record = retained.selected_record
            original_expectation, original_digest = record.expectation, record.digest
            pair_code = admission.WorkspaceDeclarationScopeRuntime._source_projection_pair.__code__
            reader_code = admission.WorkspaceDeclarationScopeRuntime._read_source_projection_pair.__code__
            io_code = source_module.capture_exact_paths.__code__
            pair = None
            fired = False
            in_reader = False
            path = value.root / ("workspaces/network/modules/main/package/a.bin" if target == "package" else
                                "workspaces/kernel/semantic_contract/profiles/kernel.default/aware.semantic_contract_profile.toml")
            before = path.read_bytes()

            def profile(frame, event, arg):
                nonlocal pair, fired, in_reader
                if event == "call" and frame.f_code is reader_code:
                    in_reader = True
                if in_reader and pair is None and event == "return" and frame.f_code is pair_code:
                    pair = arg
                if in_reader and pair is not None and not fired and event == "call" and frame.f_code is io_code:
                    fired = True
                    binding, closure = pair
                    if target == "closure":
                        object.__setattr__(closure, "consumer_scope_key", "workspaces/kernel/aware.workspace.toml")
                    elif target in ("binding", "coherent_binding"):
                        object.__setattr__(binding.expectation, "package_id", "forged")
                        if target == "coherent_binding":
                            object.__setattr__(record, "expectation", binding.expectation)
                            object.__setattr__(record, "digest", binding.binding_digest)
                    elif target == "interrupt":
                        raise KeyboardInterrupt("joint terminal interruption")
                    else:
                        path.write_bytes(b"changed after projection")

            previous = sys.getprofile()
            try:
                sys.setprofile(profile)
                with pytest.raises((SourceObservationUnavailable, KeyboardInterrupt, BaseExceptionGroup)):
                    node.validate()
            finally:
                sys.setprofile(previous)
                path.write_bytes(before)
                object.__setattr__(record, "expectation", original_expectation)
                object.__setattr__(record, "digest", original_digest)
            assert fired and not retained.live
            assert value.issuer._semantic_source_window is None
            with pytest.raises(RuntimeError, match="terminal"):
                node.validate()


async def test_same_source_validation_batch_keeps_checks_and_reduces_rereads(
    tmp_path, monkeypatch
):
    from test_selected_input_read_node import open_read, read_fixture

    # isort: split
    from aware_workspace_runtime import declaration_scope_admission as admission

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            expectations = tuple(node.prepare_source_expectation(
                use_ref=f"batch-{index}", stage="pre_request",
                source_coordinates=value.coordinates,
            ) for index in range(3))
            counts = {"source": 0, "input": 0}
            source_code = source_module.WorkspaceSourceObservationRuntime.revalidate_declarations.__code__
            input_code = admission.WorkspaceDeclarationScopeRuntime._validate_semantic_input_source.__code__

            def count(frame, event, arg):
                if event == "call":
                    if frame.f_code is source_code:
                        counts["source"] += 1
                    if frame.f_code is input_code:
                        counts["input"] += 1

            previous = sys.getprofile()
            try:
                sys.setprofile(count)
                for expected in expectations:
                    value.issuer.validate_semantic_input_source(value.selected, expected=expected)
                separate = counts.copy()
                counts.update(source=0, input=0)
                value.issuer._validate_retained_semantic_inputs(
                    value.selected, expectations=expectations, results=(),
                )
                batched = counts.copy()
            finally:
                sys.setprofile(previous)
            assert batched["input"] == separate["input"] == 3
            assert 0 < batched["source"] < separate["source"]
            assert value.issuer._semantic_source_window is None
            # A later check starts from fresh source evidence, never the batch.
            path = value.root / "workspaces/network/modules/main/package/a.bin"
            path.write_bytes(b"changed after batch")
            with pytest.raises((SourceObservationUnavailable, BaseExceptionGroup)):
                node.validate()


@pytest.mark.parametrize("with_input", [False, True])
async def test_node_participant_validation_uses_only_original_input_window(
    tmp_path, monkeypatch, with_input,
):
    from test_selected_input_read_node import open_read, read_fixture

    # isort: split
    from aware_workspace_runtime import direct_command_composition as composition

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            if with_input:
                node.prepare_source_expectation(
                    use_ref="node-window", stage="pre_request",
                    source_coordinates=value.coordinates,
                )
            original = composition._read_direct_workspace_selected_participants
            observed = []

            def inspect_window(command, selected):
                observed.append(value.issuer._semantic_source_window is not None)
                return original(command, selected)

            monkeypatch.setattr(composition, "_read_direct_workspace_selected_participants", inspect_window)
            node.validate()
            assert observed == [with_input]
            assert value.issuer._semantic_source_window is None


@pytest.mark.parametrize("target", ["body", "profile", "interrupt"])
async def test_node_window_checks_currentness_after_participant_validation(
    tmp_path, monkeypatch, target,
):
    from test_selected_input_read_node import open_read, read_fixture

    # isort: split
    from aware_workspace_runtime import direct_command_composition as composition

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            expected = node.prepare_source_expectation(
                use_ref="node-window-terminal", stage="pre_request",
                source_coordinates=value.coordinates,
            )
            retained = value.issuer._pre_request_record(value.selected, expected)
            node_record = composition._selected_input_read_record(node)
            original = composition._read_direct_workspace_selected_participants
            path = value.root / (
                "workspaces/network/modules/main/package/a.bin" if target == "body"
                else "workspaces/network/aware.workspace.toml"
            )
            before = path.read_bytes()

            def mutate_after_participants(command, selected):
                result = original(command, selected)
                assert value.issuer._semantic_source_window is not None
                if target == "interrupt":
                    raise KeyboardInterrupt("node window interrupted")
                path.write_bytes(before + b"\nchanged")
                return result

            monkeypatch.setattr(composition, "_read_direct_workspace_selected_participants", mutate_after_participants)
            with pytest.raises((SourceObservationUnavailable, KeyboardInterrupt, BaseExceptionGroup)):
                node.validate()
            path.write_bytes(before)
            assert value.issuer._semantic_source_window is None
            assert not retained.live
            assert node_record.command is node_record.factory is node_record.stack is None
            assert node_record.expectations == node_record.results == ()
            with pytest.raises(RuntimeError, match="terminal"):
                node.validate()


@pytest.mark.parametrize("target", ["body", "profile"])
async def test_held_node_terminal_error_releases_window_closure(tmp_path, target):
    import gc

    from test_selected_input_read_node import open_read, read_fixture

    # isort: split
    from aware_workspace_runtime import direct_command_composition as composition

    async def reject_and_release():
        patch = pytest.MonkeyPatch()
        error = None
        value = node = original = mutate = path = before = None
        captured = []
        try:
            async with read_fixture(tmp_path, patch) as value:
                with open_read(value) as node:
                    node.prepare_source_expectation(
                        use_ref="held-terminal-error", stage="pre_request",
                        source_coordinates=value.coordinates,
                    )
                    original = composition._read_direct_workspace_selected_participants
                    path = value.root / (
                        "workspaces/network/modules/main/package/a.bin" if target == "body"
                        else "workspaces/network/aware.workspace.toml"
                    )
                    before = path.read_bytes()

                    def mutate(command, selected):
                        captured.append(id(value.issuer._semantic_source_window.closure))
                        result = original(command, selected)
                        path.write_bytes(before + b"\nchanged")
                        return result

                    patch.setattr(composition, "_read_direct_workspace_selected_participants", mutate)
                    try:
                        node.validate()
                    except (SourceObservationUnavailable, BaseExceptionGroup) as caught:
                        error = caught
                    finally:
                        path.write_bytes(before)
                    assert error is not None
        finally:
            patch.undo()
            patch = value = node = original = mutate = path = before = None
        return error, captured

    error, captured = await reject_and_release()
    assert error is not None and len(captured) == 1
    gc.collect()
    assert not any(id(item) == captured[0] for item in gc.get_objects())


@pytest.mark.parametrize("target", ["body", "inventory", "profile", "expectation", "interrupt"])
async def test_batch_terminal_checks_reject_mid_validation_change(
    tmp_path, monkeypatch, target
):
    from test_selected_input_read_node import open_read, read_fixture

    # isort: split
    from aware_workspace_runtime import declaration_scope_admission as admission

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            expected = node.prepare_source_expectation(
                use_ref="batch-terminal", stage="pre_request",
                source_coordinates=value.coordinates,
            )
            record = admission.WorkspaceDeclarationScopeRuntime._pre_request_record(
                value.issuer, value.selected, expected,
            )
            code = admission.WorkspaceDeclarationScopeRuntime._validate_semantic_input_source.__code__
            path = value.root / {
                "body": "workspaces/network/modules/main/package/a.bin",
                "inventory": "workspaces/network/modules/main/package/extra.bin",
                "profile": "workspaces/kernel/semantic_contract/profiles/kernel.default/aware.semantic_contract_profile.toml",
                "expectation": "workspaces/network/modules/main/package/a.bin",
                "interrupt": "workspaces/network/modules/main/package/a.bin",
            }[target]
            before = path.read_bytes() if path.exists() else None
            original_identity = expected.operation_identity
            fired = False

            def change(frame, event, arg):
                nonlocal fired
                if not fired and frame.f_code is code and event == "return":
                    fired = True
                    if target == "interrupt":
                        raise KeyboardInterrupt("batch interruption")
                    if target == "expectation":
                        object.__setattr__(expected, "operation_identity", object())
                    else:
                        path.write_bytes(b"changed during original validation")

            previous = sys.getprofile()
            try:
                sys.setprofile(change)
                with pytest.raises((SourceObservationUnavailable, KeyboardInterrupt, BaseExceptionGroup)):
                    node.validate()
            finally:
                sys.setprofile(previous)
                object.__setattr__(expected, "operation_identity", original_identity)
                if before is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_bytes(before)
            assert fired
            assert not record.live
            assert value.issuer._semantic_source_window is None
            with pytest.raises(RuntimeError, match="terminal"):
                node.validate()


@pytest.mark.parametrize("method", ["_validate_retained_semantic_inputs", "validate_semantic_input_source", "_original_semantic_source_window", "read_selected_package_source"])
@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
async def test_batch_rejects_substituted_dispatch_without_calls(
    tmp_path, monkeypatch, method, mode
):
    from test_selected_input_read_node import open_read, read_fixture

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            node.prepare_source_expectation(
                use_ref="batch-poison", stage="pre_request",
                source_coordinates=value.coordinates,
            )
            calls = []

            def hostile(*args, **kwargs):
                calls.append(True)
                if mode == "restore":
                    delattr(value.issuer, method)
                if mode == "raise":
                    raise RuntimeError("hostile dispatch")

            monkeypatch.setattr(value.issuer, method, hostile)
            with pytest.raises((SourceObservationUnavailable, BaseExceptionGroup)):
                node.validate()
            monkeypatch.delattr(value.issuer, method)
            assert calls == []
            with pytest.raises(RuntimeError, match="terminal"):
                node.validate()


@pytest.mark.parametrize("checkpoint", [False, True])
async def test_batch_never_encloses_owner_execution_and_checks_original_result(
    tmp_path, monkeypatch, checkpoint,
):
    from contextlib import ExitStack, contextmanager

    from aware_code_semantic_contract_runtime import (
        ContentDigest,
        ContractViolation,
        SemanticConfigurationCoordinate,
        SemanticImplementationCoordinate,
    )
    from aware_code_semantic_contract_runtime import (
        semantic_input_producer as producers,
    )
    from aware_code_semantic_contract_runtime.runtime import SemanticBody
    from test_selected_input_read_node import open_read, read_fixture
    from test_v3_source_admission import _coordinate

    async with read_fixture(tmp_path, monkeypatch) as value:
        host = producers.SemanticInputProducerHost()
        output = SemanticBody(_coordinate("prepared", b"prepared"), b"prepared")
        calls = []

        async def produce(_):
            assert value.issuer._semantic_source_window is None
            calls.append(True)
            return output

        registration = producers.register_semantic_input_producer(
            host, declaration=producers.SemanticInputProducerDeclaration(
                "fixture.batch", "fixture.batch.v1",
                SemanticImplementationCoordinate("fixture/batch", ContentDigest.of_bytes(b"code")),
                SemanticConfigurationCoordinate("fixture/batch", ContentDigest.of_bytes(b"config")),
                (producers.SemanticInputSourceContract("raw_source", value.coordinates[0].coordinate.contract),),
                "prepared", output.coordinate.contract,
            ), producer=produce, validator=value.issuer,
            validator_entrance=value.issuer.validate_semantic_input_source,
            reader=value.issuer, reader_entrance=value.issuer.read_semantic_input_sources,
            retain_result=True,
            validation_scope_entrance=(
                producers.capture_semantic_input_validation_scope(value.issuer) if checkpoint else None
            ),
        )
        try:
            with open_read(value) as node:
                expected = node.prepare_source_expectation(
                    use_ref="batch-result", stage="pre_request",
                    source_coordinates=value.coordinates,
                )
                result = await producers.execute_registered_semantic_input(
                    host, registration, source_admission=value.selected, expected=expected,
                )
                node.retain_source_result(host, registration, expected=expected, result=result)
                with ExitStack() as stack:
                    if checkpoint:
                        stack.enter_context(contextmanager(producers._original_result_checkpoint_scope)(
                            host, registration, source_admission=value.selected,
                            expected=expected, result=result, expectations=(expected,),
                        ))
                        assert value.issuer._semantic_source_window is not None
                    node.validate()
                assert value.issuer._semantic_source_window is None
                assert calls == [True]
                object.__setattr__(result, "canonical_body", b"forged")
                with pytest.raises((ContractViolation, SourceObservationUnavailable, BaseExceptionGroup)):
                    node.validate()
                with pytest.raises(RuntimeError, match="terminal"):
                    node.validate()
                assert not host._closed
        finally:
            host.close()


async def test_grouped_batch_keeps_distinct_member_windows(tmp_path):
    from test_grouped_selected_source_input import dependency_group, scope

    async with dependency_group(tmp_path) as (original, root, participant, edge):
        with scope(
            original, root=root, participants=(participant,), dependency_edges=(edge,),
        ) as expected:
            original.issuer._validate_retained_semantic_inputs(
                original.selected, expectations=(expected,), results=(),
            )
            assert original.issuer._semantic_source_window is None


@pytest.mark.parametrize("binding", ["workspace_alias", "code_owner"])
@pytest.mark.parametrize("mode", ["return", "raise", "self_restore"])
@pytest.mark.parametrize("phase", ["entry", "active_window", "dispatch", "code_return"])
async def test_original_code_result_dispatch_rejects_mutable_alias(
    tmp_path, monkeypatch, binding, mode, phase
):
    import inspect

    from aware_code_semantic_contract_runtime import (
        semantic_input_producer as producers,
    )
    from test_selected_input_read_node import assembly_fixture

    # isort: split
    from aware_workspace_runtime import declaration_scope_admission as admission
    from aware_workspace_runtime import direct_command_composition as composition

    async with assembly_fixture(tmp_path, monkeypatch) as (value, node, host, _registration, expected, body):
        owner = admission if binding == "workspace_alias" else producers
        original = producers.validate_registered_semantic_input_result
        invoke = admission.WorkspaceDeclarationScopeRuntime._call_original_code_result_validator
        lines, first_line = inspect.getsourcelines(invoke)
        dispatch_line = first_line + next(i for i, line in enumerate(lines) if line.strip() == "original(")
        input_code = admission.WorkspaceDeclarationScopeRuntime._validate_semantic_input_source.__code__
        retained = value.issuer._pre_request_record(value.selected, expected)
        node_record = composition._selected_input_read_record(node)
        original_body = body.canonical_body
        # Post-return poisoning uses a genuine healthy result so it proves the
        # return binding guard, rather than only Code's scalar rejection.
        if phase != "code_return":
            object.__setattr__(body, "canonical_body", b"forged result")
        calls = []
        fired = False

        def hostile(*args, **kwargs):
            calls.append(value.issuer._semantic_source_window is not None)
            if mode == "self_restore":
                owner.validate_registered_semantic_input_result = original
            if mode == "raise":
                raise RuntimeError("hostile Code alias")

        def poison(frame, event, arg):
            nonlocal fired
            hit = (
                phase == "active_window" and event == "return" and frame.f_code is input_code
                or phase == "dispatch" and event == "line" and frame.f_code is invoke.__code__
                and frame.f_lineno == dispatch_line
                or phase == "code_return" and event == "return" and frame.f_code is original.__code__
            )
            if not fired and hit:
                assert value.issuer._semantic_source_window is not None
                fired = True
                owner.validate_registered_semantic_input_result = hostile
            return poison

        previous = sys.gettrace()
        try:
            if phase == "entry":
                fired = True
                owner.validate_registered_semantic_input_result = hostile
            else:
                sys.settrace(poison)
            with pytest.raises((SourceObservationUnavailable, producers.ContractViolation, BaseExceptionGroup)):
                node.validate()
        finally:
            sys.settrace(previous)
            owner.validate_registered_semantic_input_result = original
            object.__setattr__(body, "canonical_body", original_body)
        assert fired
        assert calls == []
        assert not retained.live
        assert value.issuer._semantic_source_window is None
        assert node_record.command is node_record.factory is node_record.stack is None
        assert node_record.expectations == node_record.results == ()
        assert not value.issuer._pre_request_inputs
        assert not host._closed
        with pytest.raises(RuntimeError, match="terminal"):
            node.validate()


@pytest.mark.parametrize("mode", ["return", "raise", "self_restore"])
async def test_original_code_dispatch_descriptor_rejects_substitution(
    tmp_path, monkeypatch, mode
):
    from test_selected_input_read_node import assembly_fixture

    async with assembly_fixture(tmp_path, monkeypatch) as (value, node, _, _, _, _):
        calls = []

        def hostile(*args, **kwargs):
            calls.append(True)
            if mode == "self_restore":
                delattr(value.issuer, "_call_original_code_result_validator")
            if mode == "raise":
                raise RuntimeError("hostile Code dispatch")

        monkeypatch.setattr(value.issuer, "_call_original_code_result_validator", hostile)
        with pytest.raises((SourceObservationUnavailable, BaseExceptionGroup)):
            node.validate()
        monkeypatch.delattr(value.issuer, "_call_original_code_result_validator")
        assert calls == []
        assert value.issuer._semantic_source_window is None
        with pytest.raises(RuntimeError, match="terminal"):
            node.validate()


async def test_admitted_projection_is_detached_and_does_not_reinterpret(
    tmp_path, monkeypatch
):
    async with fixture(tmp_path) as (_, _, observer, issuer, observed, expected):
        declaration = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expected,
        )
        selected = observer.observe_selected_package(
            declaration=observed,
            workspace_manifest_path="workspaces/network/aware.workspace.toml",
            module_id="main", package_id="example",
        )
        source = issuer.bind_selected_package_source(
            declaration=declaration, selected=selected
        )
        original = issuer.read_declaration_scope(declaration)

        def forbidden(*args, **kwargs):
            pytest.fail("unchanged admitted declaration was interpreted again")

        monkeypatch.setattr(
            RetainedWorkspaceCompositionProvider, "describe_captured_bodies", forbidden
        )
        for _ in range(3):
            current = issuer.read_declaration_scope(declaration)
            assert current == original
            assert current is not original
            assert current is not issuer._declarations[declaration].projection
            assert current.profile_associations[0].manifest is current.local_profiles[0].manifest
            issuer.read_selected_package_source(source)
        object.__setattr__(current, "consumer_scope_key", "changed")
        assert issuer.read_declaration_scope(declaration) == original


@pytest.mark.parametrize("target", ["repository", "profile", "selected", "inventory"])
async def test_projection_reuse_keeps_exact_byte_and_inventory_checks(tmp_path, target):
    async with fixture(tmp_path) as (root, _, observer, issuer, observed, expected):
        declaration = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expected,
        )
        selected = observer.observe_selected_package(
            declaration=observed,
            workspace_manifest_path="workspaces/network/aware.workspace.toml",
            module_id="main", package_id="example",
        )
        source = issuer.bind_selected_package_source(declaration=declaration, selected=selected)
        issuer.read_selected_package_source(source)
        paths = {
            "repository": "aware.repo.toml",
            "profile": "workspaces/kernel/semantic_contract/profiles/kernel.default/aware.semantic_contract_profile.toml",
            "selected": "workspaces/network/modules/main/package/body.bin",
            "inventory": "workspaces/network/modules/main/package/extra.bin",
        }
        path = root / paths[target]
        path.write_bytes(b"changed")
        with pytest.raises(SourceObservationUnavailable):
            issuer.read_selected_package_source(source)


async def test_private_projection_corruption_refuses(tmp_path):
    async with fixture(tmp_path) as (_, _, _, issuer, observed, expected):
        declaration = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expected,
        )
        original = issuer._declarations[declaration]
        corrupted = copy.deepcopy(original.projection)
        object.__setattr__(corrupted, "consumer_scope_key", "workspaces/kernel/aware.workspace.toml")
        object.__setattr__(original, "projection", corrupted)
        with pytest.raises(SourceObservationUnavailable, match="projection_changed"):
            issuer.read_declaration_scope(declaration)


@pytest.mark.parametrize("target", ["consumer", "workspace", "package", "combined"])
@pytest.mark.parametrize("restamp", ["replace_digest", "mutate_digest"])
@pytest.mark.parametrize("entrance", ["declaration", "selected_source"])
async def test_coherently_restamped_projection_refuses(
    tmp_path, monkeypatch, target, restamp, entrance
):
    async with fixture(tmp_path) as (_, _, observer, issuer, observed, expected):
        declaration = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expected,
        )
        selected = observer.observe_selected_package(
            declaration=observed,
            workspace_manifest_path="workspaces/network/aware.workspace.toml",
            module_id="main", package_id="example",
        )
        source = issuer.bind_selected_package_source(declaration=declaration, selected=selected)
        original = issuer._declarations[declaration]
        before = observer.read_declarations(observed)

        def forbidden(*args, **kwargs):
            pytest.fail("restamping must not cause declaration reinterpretation")

        monkeypatch.setattr(
            RetainedWorkspaceCompositionProvider, "describe_captured_bodies", forbidden
        )
        projection = original.projection
        network = next(scope for scope in projection.scopes if scope.workspace_handle == "Network")
        if target in ("consumer", "combined"):
            object.__setattr__(projection, "consumer_scope_key", "workspaces/kernel/aware.workspace.toml")
            # Restamp the record's consumer too: cache selection must not fall
            # back to interpreting the attacker's newly chosen consumer.
            object.__setattr__(original, "consumer_scope_key", projection.consumer_scope_key)
        if target in ("workspace", "combined"):
            object.__setattr__(network, "workspace_handle", "ForgedNetwork")
        if target in ("package", "combined"):
            object.__setattr__(network.projection.packages[0], "package_kind", "ontology")
        forged_digest = projection.closure_digest
        if restamp == "replace_digest":
            object.__setattr__(original, "digest", forged_digest)
        else:
            object.__setattr__(original.digest, "value", forged_digest.value)
        assert projection.closure_digest == original.digest
        assert observer.read_declarations(observed) == before
        with pytest.raises(SourceObservationUnavailable, match="projection_changed"):
            if entrance == "declaration":
                issuer.read_declaration_scope(declaration)
            else:
                issuer.read_selected_package_source(source)


@pytest.mark.parametrize("field", ["parent_identity", "operation_identity", "epoch_identity"])
async def test_original_command_expectation_cannot_be_restamped(tmp_path, field):
    async with fixture(tmp_path) as (_, _, _, issuer, observed, expected):
        declaration = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expected,
        )
        object.__setattr__(expected, field, "substituted")
        with pytest.raises(SourceObservationUnavailable, match="projection_changed"):
            issuer.read_declaration_scope(declaration)


async def test_coherent_record_replacement_refuses(tmp_path):
    async with fixture(tmp_path) as (_, _, _, issuer, observed, expected):
        declaration = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expected,
        )
        original = issuer._declarations[declaration]
        issuer._declarations[declaration] = replace(
            original, projection=copy.deepcopy(original.projection)
        )
        with pytest.raises(SourceObservationUnavailable, match="projection_changed"):
            issuer.read_declaration_scope(declaration)


async def test_other_admitted_consumer_cannot_replace_original_record(tmp_path):
    async with fixture(tmp_path) as (_, _, _, issuer, observed, expected):
        network = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expected,
        )
        kernel = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/kernel/aware.workspace.toml",
            expectation=expected,
        )
        authentic_kernel = issuer.read_declaration_scope(kernel)
        issuer._declarations[network] = issuer._declarations[kernel]
        with pytest.raises(SourceObservationUnavailable, match="projection_changed"):
            issuer.read_declaration_scope(network)
        assert issuer.read_declaration_scope(kernel) == authentic_kernel


async def test_original_nested_projection_mutation_without_restamp_refuses(tmp_path):
    async with fixture(tmp_path) as (_, _, _, issuer, observed, expected):
        declaration = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expected,
        )
        original = issuer._declarations[declaration]
        network = next(scope for scope in original.projection.scopes if scope.workspace_handle == "Network")
        object.__setattr__(network.projection.packages[0], "package_kind", "ontology")
        with pytest.raises(SourceObservationUnavailable, match="projection_changed"):
            issuer.read_declaration_scope(declaration)


async def test_retained_source_digest_cannot_be_restamped(tmp_path):
    async with fixture(tmp_path) as (_, _, _, issuer, observed, expected):
        declaration = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expected,
        )
        original = issuer._declarations[declaration]
        object.__setattr__(original.source_record, "observation_digest", "sha256:" + "f" * 64)
        with pytest.raises(SourceObservationUnavailable, match="projection_changed"):
            issuer.read_declaration_scope(declaration)


@pytest.mark.parametrize("entrance", ["declaration", "selected_source"])
@pytest.mark.parametrize("target", ["consumer", "package"])
@pytest.mark.parametrize("phase", ["copy_entry", "copy_restore", "copy_return", "terminal_io"])
async def test_genuine_copy_and_terminal_io_restamping_refuses(
    tmp_path, monkeypatch, entrance, target, phase
):
    async with fixture(tmp_path) as (_, _, observer, issuer, observed, expected):
        declaration = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expected,
        )
        selected = observer.observe_selected_package(
            declaration=observed,
            workspace_manifest_path="workspaces/network/aware.workspace.toml",
            module_id="main", package_id="example",
        )
        source = issuer.bind_selected_package_source(declaration=declaration, selected=selected)
        record = issuer._declarations[declaration]
        projection = record.projection
        before = observer.read_declarations(observed)
        original_digest = record.digest
        if target == "consumer":
            changed_object, field = projection, "consumer_scope_key"
            changed_value = "workspaces/kernel/aware.workspace.toml"
        else:
            network = next(scope for scope in projection.scopes if scope.workspace_handle == "Network")
            changed_object, field = network.projection.packages[0], "package_kind"
            changed_value = "ontology"
        original_value = getattr(changed_object, field)
        genuine_copy = copy.deepcopy
        revalidate = issuer._methods[
            "revalidate_declarations" if entrance == "declaration" else "revalidate_selected_package"
        ][1].__func__
        state = {"mutated": False, "copied": False, "restored": False, "forged_copy": False}

        def mutate():
            object.__setattr__(changed_object, field, changed_value)
            object.__setattr__(record, "digest", projection.closure_digest)
            state["mutated"] = True

        copy_frames = set()

        def profile(frame, event, result):
            copy_event = _declaration_copy_event(frame, event, projection, copy_frames)
            # Observe the genuine function; do not replace deepcopy or its
            # dispatchers. Mutate after entry checks, while it is running.
            if copy_event:
                if event == "call" and phase in ("copy_entry", "copy_restore"):
                    mutate()
                if event == "return":
                    state["copied"] = True
                    state["forged_copy"] = result.closure_digest != original_digest
                    if phase == "copy_restore":
                        object.__setattr__(changed_object, field, original_value)
                        object.__setattr__(record, "digest", original_digest)
                        state["restored"] = True
                    elif phase == "copy_return":
                        mutate()
            elif (
                phase == "terminal_io" and state["copied"] and not state["mutated"]
                and frame.f_code is revalidate.__code__ and event == "return"
                and frame.f_locals.get("self") is observer
            ):
                mutate()

        def forbidden(*args, **kwargs):
            pytest.fail("copy-window rejection must preserve interpretation-once")

        monkeypatch.setattr(
            RetainedWorkspaceCompositionProvider, "describe_captured_bodies", forbidden
        )
        previous = sys.getprofile()
        try:
            sys.setprofile(profile)
            with pytest.raises(SourceObservationUnavailable, match="projection_changed"):
                if entrance == "declaration":
                    issuer.read_declaration_scope(declaration)
                else:
                    issuer.read_selected_package_source(source)
        finally:
            sys.setprofile(previous)
        assert copy.deepcopy is genuine_copy
        assert state["mutated"] and state["copied"]
        if phase == "copy_restore":
            assert state["restored"] and state["forged_copy"]
            assert record.digest is original_digest
            assert getattr(changed_object, field) == original_value
        assert observer.read_declarations(observed) == before


@pytest.mark.parametrize("entrance", ["declaration", "selected_source"])
async def test_original_association_replaced_at_genuine_copy_return_refuses(tmp_path, entrance):
    async with fixture(tmp_path) as (_, _, observer, issuer, observed, expected):
        declaration = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expected,
        )
        selected = observer.observe_selected_package(
            declaration=observed,
            workspace_manifest_path="workspaces/network/aware.workspace.toml",
            module_id="main", package_id="example",
        )
        source = issuer.bind_selected_package_source(declaration=declaration, selected=selected)
        record = issuer._declarations[declaration]
        genuine_copy = copy.deepcopy
        replaced = []

        copy_frames = set()

        def profile(frame, event, result):
            copy_event = _declaration_copy_event(frame, event, record.projection, copy_frames)
            if (
                event == "return" and copy_event
            ):
                issuer._declarations[declaration] = replace(record)
                replaced.append(True)

        previous = sys.getprofile()
        try:
            sys.setprofile(profile)
            with pytest.raises(SourceObservationUnavailable, match="projection_changed"):
                if entrance == "declaration":
                    issuer.read_declaration_scope(declaration)
                else:
                    issuer.read_selected_package_source(source)
        finally:
            sys.setprofile(previous)
        assert replaced == [True]
        assert copy.deepcopy is genuine_copy


async def test_projection_reuse_checks_parent_after_live_capture(tmp_path, monkeypatch):
    async with fixture(tmp_path) as (_, parent, _, issuer, observed, expected):
        declaration = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expected,
        )
        issuer.read_declaration_scope(declaration)
        capture = source_module.capture_exact_paths

        def lose_parent(*args, **kwargs):
            rows = capture(*args, **kwargs)
            parent.close()
            return rows

        monkeypatch.setattr(source_module, "capture_exact_paths", lose_parent)
        with pytest.raises(RuntimeError):
            issuer.read_declaration_scope(declaration)


@pytest.mark.parametrize("action", ["return", "raise", "restore"])
@pytest.mark.parametrize("phase", ["entry", "after_copy"])
@pytest.mark.parametrize("entrance", ["validate_retained_declaration_scope_coordinate", "validate_detached_declaration_scope_coordinate"])
async def test_original_coordinate_validator_substitution_is_zero_call_and_terminal(
    tmp_path, monkeypatch, action, phase, entrance,
):
    from aware_code_semantic_contract_runtime import (
        retained_declaration_scope_validation as validation,
    )

    async with fixture(tmp_path) as (_, _, _, issuer, observed, expected):
        declaration = issuer.capture_declaration_scope(
            observation=observed, consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expected,
        )
        unrelated = issuer.capture_declaration_scope(
            observation=observed, consumer_scope_key="workspaces/kernel/aware.workspace.toml",
            expectation=expected,
        )
        original = getattr(validation, entrance)
        projection = issuer._declarations[declaration].projection
        calls = []

        def poison(*args):
            calls.append(True)
            if action == "raise":
                raise RuntimeError("substituted coordinate validator")
            if action == "restore":
                monkeypatch.setattr(validation, entrance, original)

        copy_frames = set()

        def profile(frame, event, value):
            copy_event = _declaration_copy_event(frame, event, projection, copy_frames)
            if (phase == "after_copy" and event == "return" and copy_event):
                monkeypatch.setattr(validation, entrance, poison)

        if phase == "entry":
            monkeypatch.setattr(validation, entrance, poison)
        previous = sys.getprofile()
        try:
            sys.setprofile(profile)
            with pytest.raises(SourceObservationUnavailable, match="coordinate_validator_changed"):
                issuer.read_declaration_scope(declaration)
        finally:
            sys.setprofile(previous)
            monkeypatch.setattr(validation, entrance, original)
        assert calls == []
        with pytest.raises(SourceObservationUnavailable, match="projection_changed"):
            issuer.read_declaration_scope(declaration)
        assert issuer.read_declaration_scope(unrelated).consumer_scope_key == "workspaces/kernel/aware.workspace.toml"


async def test_private_original_coordinate_replaces_only_original_digest_rebuild(tmp_path, monkeypatch):
    from aware_code_semantic_contract_runtime import (
        retained_declaration_scope_codec as codec,
    )

    async with fixture(tmp_path) as (_, _, _, issuer, observed, expected):
        declaration = issuer.capture_declaration_scope(
            observation=observed, consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expected,
        )
        record = issuer._declarations[declaration]
        captured = codec.declaration_closure_payload_bytes
        original_calls, detached_calls = [], []

        def count(value):
            (original_calls if value is record.projection else detached_calls).append(True)
            return captured(value)

        monkeypatch.setattr(codec, "declaration_closure_payload_bytes", count)
        result = issuer.read_declaration_scope(declaration)
        assert result is not record.projection
        assert original_calls == []
        # Both immutable commitments now receive complete closed field checks;
        # the ordinary portable digest remains available to every consumer.
        assert detached_calls == []
        assert result.closure_digest.value == record.digest.value


@pytest.mark.parametrize("entrance", ["boundary", "declaration", "selected_source"])
@pytest.mark.parametrize("phase", ["call", "return"])
@pytest.mark.parametrize("field", ["package_kind", "workspace_handle"])
@pytest.mark.parametrize("restamp", [False, True])
async def test_original_journal_rechecked_after_genuine_detached_comparison(
    tmp_path, entrance, phase, field, restamp,
):
    from aware_code_semantic_contract_runtime import (
        retained_declaration_scope_validation as validation,
    )

    async with fixture(tmp_path) as (_, _, observer, issuer, observed, expected):
        declaration = issuer.capture_declaration_scope(
            observation=observed, consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expected,
        )
        unrelated = issuer.capture_declaration_scope(
            observation=observed, consumer_scope_key="workspaces/kernel/aware.workspace.toml",
            expectation=expected,
        )
        selected = observer.observe_selected_package(
            declaration=observed, workspace_manifest_path="workspaces/network/aware.workspace.toml",
            module_id="main", package_id="example",
        )
        source = issuer.bind_selected_package_source(declaration=declaration, selected=selected)
        record = issuer._declarations[declaration]
        origin = issuer._checked_declaration_origin(record)
        detached = copy.deepcopy(record.projection)
        network = next(item for item in record.projection.scopes if item.workspace_handle == "Network")
        target = network.projection.packages[0] if field == "package_kind" else network
        original_field = getattr(target, field)
        original_digest = record.digest
        genuine = validation.validate_detached_declaration_scope_coordinate
        state = {"calls": 0, "mutated": False}
        # Public readers perform a copy check and a terminal check. Poison the
        # latter so another earlier validation cannot hide the returned gap.
        selected_call = 1 if entrance == "boundary" else 2

        def profile(frame, event, value):
            if (frame.f_code is genuine.__code__
                and frame.f_locals.get("coordinate") is origin.projection_coordinate):
                if event == "call":
                    state["calls"] += 1
                if event == phase and state["calls"] == selected_call and not state["mutated"]:
                    object.__setattr__(target, field, "ontology" if field == "package_kind" else "OtherNetwork")
                    if restamp:
                        object.__setattr__(record, "digest", record.projection.closure_digest)
                    state["mutated"] = True

        previous = sys.getprofile()
        try:
            sys.setprofile(profile)
            with pytest.raises(SourceObservationUnavailable, match="projection_changed"):
                if entrance == "boundary":
                    issuer._check_declaration_projection_result(origin, detached)
                elif entrance == "declaration":
                    issuer.read_declaration_scope(declaration)
                else:
                    issuer.read_selected_package_source(source)
        finally:
            sys.setprofile(previous)
            object.__setattr__(target, field, original_field)
            object.__setattr__(record, "digest", original_digest)
        assert state["mutated"] and state["calls"] == selected_call
        assert validation.validate_detached_declaration_scope_coordinate is genuine
        assert any(item is record for item in issuer._retired_declaration_records)
        # Complete restoration cannot revive the rejected family or its source.
        for read in (
            lambda: issuer.read_declaration_scope(declaration),
            lambda: issuer.read_selected_package_source(source),
        ):
            with pytest.raises(SourceObservationUnavailable, match="projection_changed"):
                read()
        assert issuer.read_declaration_scope(unrelated).consumer_scope_key == "workspaces/kernel/aware.workspace.toml"


@pytest.mark.parametrize("name", [name for name, _ in admission_module._GROUP_METHOD_DESCRIPTORS])
@pytest.mark.parametrize("location", ["class", "instance"])
def test_fast_original_method_checks_do_not_dispatch_substitutions(name, location, monkeypatch):
    from aware_workspace_runtime import declaration_scope_admission as admission

    kind = admission.WorkspaceDeclarationScopeRuntime
    issuer = object.__new__(kind)
    calls = []

    def hostile(*args, **kwargs):
        calls.append(True)
        raise AssertionError("substituted method executed")

    if location == "class":
        monkeypatch.setattr(kind, name, property(hostile))
    else:
        monkeypatch.setitem(vars(issuer), name, hostile)
    with pytest.raises(SourceObservationUnavailable, match="method_substituted"):
        admission._check_group_methods(issuer)
    assert calls == []
    monkeypatch.undo()
    admission._check_group_methods(issuer)


def test_fast_original_method_check_uses_native_dictionary_access():
    from aware_workspace_runtime import declaration_scope_admission as admission

    calls = []

    class ForeignDictionary(dict):
        def get(self, *args):
            calls.append(True)
            raise AssertionError("foreign dictionary lookup executed")

    issuer = object.__new__(admission.WorkspaceDeclarationScopeRuntime)
    issuer.__dict__ = ForeignDictionary()
    admission._check_group_methods(issuer)
    assert calls == []


@pytest.mark.parametrize("owner", ["composition", "admission"])
@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
@pytest.mark.parametrize("phase", ["entry", "late"])
async def test_original_group_dispatch_alias_cannot_run_or_resume(tmp_path, monkeypatch, owner, mode, phase):
    from test_selected_input_read_node import open_read, read_fixture

    # isort: split
    from aware_workspace_runtime import direct_command_composition as composition

    namespace = composition if owner == "composition" else admission_module
    original = namespace._original_group_method
    calls = []
    fired = False

    def hostile(*args, **kwargs):
        calls.append(True)
        if mode == "restore":
            monkeypatch.setattr(namespace, "_original_group_method", original)
        if mode == "raise":
            raise RuntimeError("substituted dispatcher executed")

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            expected = node.prepare_source_expectation(
                use_ref="original-alias", stage="pre_request", source_coordinates=value.coordinates,
            )
            retained = value.issuer._pre_request_record(value.selected, expected)
            code = admission_module.WorkspaceDeclarationScopeRuntime._source_projection_pair.__code__

            def observe(frame, event, result):
                nonlocal fired
                if not fired and event == "return" and frame.f_code is code:
                    fired = True
                    monkeypatch.setattr(namespace, "_original_group_method", hostile)

            previous = sys.getprofile()
            try:
                if phase == "entry":
                    fired = True
                    monkeypatch.setattr(namespace, "_original_group_method", hostile)
                else:
                    sys.setprofile(observe)
                with pytest.raises((RuntimeError, SourceObservationUnavailable, BaseExceptionGroup)):
                    node.validate()
            finally:
                sys.setprofile(previous)
                monkeypatch.setattr(namespace, "_original_group_method", original)
            assert fired and calls == []
            assert not retained.live
            with pytest.raises(RuntimeError, match="terminal"):
                node.validate()


@pytest.mark.parametrize("owner", ["issuer", "source"])
@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
async def test_native_dictionary_guard_rejects_hidden_method_substitution(tmp_path, monkeypatch, owner, mode):
    from test_selected_input_read_node import open_read, read_fixture

    calls = []

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            expected = node.prepare_source_expectation(
                use_ref="dictionary-alias", stage="pre_request", source_coordinates=value.coordinates,
            )
            retained = value.issuer._pre_request_record(value.selected, expected)
            target = value.issuer if owner == "issuer" else value.issuer._source
            original_dictionary = target.__dict__

            def hostile(*args, **kwargs):
                calls.append("method")
                raise AssertionError("substituted method executed")

            class ForeignDictionary(dict):
                def get(self, *args):
                    calls.append("dictionary")
                    if mode == "restore":
                        target.__dict__ = original_dictionary
                    if mode == "raise":
                        raise AssertionError("substituted lookup executed")
                    return args[-1]

            changed = ForeignDictionary(original_dictionary)
            changed["_closure" if owner == "issuer" else "read_declarations"] = hostile
            target.__dict__ = changed
            try:
                with pytest.raises((SourceObservationUnavailable, BaseExceptionGroup)):
                    node.validate()
            finally:
                target.__dict__ = original_dictionary
            assert calls == []
            assert not retained.live
            with pytest.raises(RuntimeError, match="terminal"):
                node.validate()


@pytest.mark.parametrize("mutation", ["release", "binding", "owner", "runtime", "foreign_binding"])
def test_scalar_retention_checks_original_owner_return_before_store_access(tmp_path, mutation):
    from aware_workspace_fs_adapter.repository_delta_retention import (
        FilesystemDeltaRetentionFactory,
        FilesystemDeltaRetentionOwner,
    )
    from aware_workspace_fs_adapter.repository_delta_store import (
        WorkspaceRepositoryDeltaStore,
    )

    # isort: split
    from aware_workspace_runtime.repository_delta_retention import (
        WorkspaceRepositoryDeltaRetentionRefusal,
        WorkspaceRepositoryDeltaRetentionRuntime,
    )

    factory = FilesystemDeltaRetentionFactory.filesystem(state_root=tmp_path)
    runtime = WorkspaceRepositoryDeltaRetentionRuntime(physical_factory=factory)
    state = runtime.allocate()
    runtime.initialize(state, repository_binding_ref="binding:scalar")
    body = runtime.record_body(state, b"unchanged original bytes")
    owner, binding, physical = state.owner, state.binding, runtime._physical
    owner_code = FilesystemDeltaRetentionOwner.verify_original_owner.__code__
    store_code = WorkspaceRepositoryDeltaStore.resolve_body.__code__
    changed = False
    reads = []
    hostile = []

    class ForeignBinding:
        def __eq__(self, other):
            hostile.append(True)
            return True

        def __ne__(self, other):
            hostile.append(True)
            return False

    def observe(frame, event, result):
        nonlocal changed
        if event == "call" and frame.f_code is store_code:
            reads.append(True)
        if not changed and event == "return" and frame.f_code is owner_code:
            changed = True
            if mutation == "release":
                runtime.release(state)
            elif mutation == "binding":
                state.binding = "binding:changed"
            elif mutation == "owner":
                state.owner = object()
            elif mutation == "foreign_binding":
                state.binding = ForeignBinding()
            else:
                runtime._physical = object()

    previous = sys.getprofile()
    try:
        sys.setprofile(observe)
        with pytest.raises(WorkspaceRepositoryDeltaRetentionRefusal):
            runtime.resolve_body(state, body)
        assert changed and reads == [] and hostile == []
    finally:
        sys.setprofile(previous)
        runtime._physical = physical
        state.owner, state.binding = owner, binding
        runtime.release(state)
    assert runtime.observe(state).phase == "released"


async def test_semantic_window_preserves_original_entry_and_terminal_source_checks(
    tmp_path, monkeypatch,
):
    from test_selected_input_read_node import open_read, read_fixture

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            expected = node.prepare_source_expectation(
                use_ref="window-owned-close", stage="pre_request",
                source_coordinates=value.coordinates,
            )
            source_code = source_module.WorkspaceSourceObservationRuntime.revalidate_selected_package.__code__
            declaration_code = source_module.WorkspaceSourceObservationRuntime.revalidate_declarations.__code__
            validator_code = admission_module.WorkspaceDeclarationScopeRuntime._validate_semantic_input_source.__code__
            counts = {source_code: 0, declaration_code: 0, validator_code: 0}

            def profile(frame, event, _arg):
                if event == "call" and frame.f_code in counts:
                    counts[frame.f_code] += 1

            previous = sys.getprofile()
            try:
                sys.setprofile(profile)
                with value.issuer._original_semantic_source_window(value.selected, expected):
                    assert counts[source_code] == 1
                    assert counts[declaration_code] == 2
                    value.issuer.validate_semantic_input_source(value.selected, expected=expected)
                    assert counts[source_code] == 1
                assert counts[source_code] == 2
                assert counts[declaration_code] == 4
                assert counts[validator_code] == 1
            finally:
                sys.setprofile(previous)
            assert value.issuer._semantic_source_window is None


@pytest.mark.parametrize("target", ["binding", "closure", "binding_restored"])
async def test_provisional_window_checks_captured_projection_after_closing_io(
    tmp_path, monkeypatch, target,
):
    from test_selected_input_read_node import open_read, read_fixture

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            expected = node.prepare_source_expectation(
                use_ref="window-provisional-poison", stage="pre_request",
                source_coordinates=value.coordinates,
            )
            retained = value.issuer._pre_request_record(value.selected, expected)
            pair_code = admission_module.WorkspaceDeclarationScopeRuntime._read_source_projection_pair.__code__
            window_code = admission_module.WorkspaceDeclarationScopeRuntime._original_semantic_source_window.__wrapped__.__code__
            poisoned = None
            original = None
            fired = restored = False

            def profile(frame, event, arg):
                nonlocal poisoned, original, fired, restored
                if not fired and event == "return" and frame.f_code is pair_code:
                    fired = True
                    binding, closure = arg
                    poisoned = closure if target == "closure" else binding.expectation
                    field = "consumer_scope_key" if target == "closure" else "package_id"
                    original = getattr(poisoned, field)
                    object.__setattr__(poisoned, field, "forged")
                elif (target == "binding_restored" and fired and not restored
                      and event == "return" and frame.f_code is window_code):
                    object.__setattr__(poisoned, "package_id", original)
                    restored = True

            previous = sys.getprofile()
            try:
                sys.setprofile(profile)
                with pytest.raises((SourceObservationUnavailable, BaseExceptionGroup)):
                    node.validate()
            finally:
                sys.setprofile(previous)
                if poisoned is not None:
                    field = "consumer_scope_key" if target == "closure" else "package_id"
                    object.__setattr__(poisoned, field, original)
            assert fired
            assert restored == (target == "binding_restored")
            assert not retained.live
            assert value.issuer._semantic_source_window is None
            with pytest.raises(RuntimeError, match="terminal"):
                node.validate()


@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
async def test_closing_window_never_dispatches_late_binding_digest_property(
    tmp_path, monkeypatch, mode,
):
    from test_selected_input_read_node import open_read, read_fixture

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            expected = node.prepare_source_expectation(
                use_ref="late-binding-property", stage="pre_request",
                source_coordinates=value.coordinates,
            )
            code = admission_module.WorkspaceDeclarationScopeRuntime._read_source_projection_pair.__code__
            kind = admission_module.CodeSelectedPackageSourceBinding
            original = vars(kind)["binding_digest"]
            calls = []
            fired = False

            def hostile(_self):
                calls.append(True)
                if mode == "restore":
                    monkeypatch.setattr(kind, "binding_digest", original)
                if mode == "raise":
                    raise AssertionError("late binding property executed")
                return None

            def profile(frame, event, _arg):
                nonlocal fired
                if (not fired and event == "return" and frame.f_code is code
                    and frame.f_locals.get("closing") is not None):
                    fired = True
                    monkeypatch.setattr(kind, "binding_digest", property(hostile))

            previous = sys.getprofile()
            try:
                sys.setprofile(profile)
                with value.issuer._original_semantic_source_window(value.selected, expected):
                    value.issuer.validate_semantic_input_source(value.selected, expected=expected)
            finally:
                sys.setprofile(previous)
                monkeypatch.setattr(kind, "binding_digest", original)
            assert fired and calls == []
            assert value.issuer._semantic_source_window is None


@pytest.mark.parametrize("entrance", ["capture_selected_source_binding_coordinate", "validate_selected_source_binding_coordinate"])
@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
@pytest.mark.parametrize("phase", ["entry", "closing"])
async def test_binding_coordinate_dispatch_rejects_substituted_code_entrance(
    tmp_path, monkeypatch, entrance, mode, phase,
):
    from test_selected_input_read_node import open_read, read_fixture

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            expected = node.prepare_source_expectation(
                use_ref="binding-coordinate-origin", stage="pre_request",
                source_coordinates=value.coordinates,
            )
            retained = value.issuer._pre_request_record(value.selected, expected)
            module = admission_module._declaration_validation
            original = getattr(module, entrance)
            code = admission_module.WorkspaceDeclarationScopeRuntime._read_source_projection_pair.__code__
            calls = []
            fired = False

            def hostile(*args, **kwargs):
                calls.append(True)
                if mode == "restore":
                    monkeypatch.setattr(module, entrance, original)
                if mode == "raise":
                    raise AssertionError("substituted binding coordinate entrance")

            def install():
                nonlocal fired
                fired = True
                monkeypatch.setattr(module, entrance, hostile)

            def profile(frame, event, _arg):
                if (not fired and event == "return" and frame.f_code is code
                    and frame.f_locals.get("closing") is not None):
                    install()

            previous = sys.getprofile()
            try:
                if phase == "entry":
                    install()
                else:
                    sys.setprofile(profile)
                with pytest.raises((SourceObservationUnavailable, BaseExceptionGroup)):
                    node.validate()
            finally:
                sys.setprofile(previous)
                monkeypatch.setattr(module, entrance, original)
            assert fired and calls == []
            assert not retained.live
            assert value.issuer._semantic_source_window is None
            with pytest.raises(RuntimeError, match="terminal"):
                node.validate()


@pytest.mark.parametrize("action", ["read", "validate"])
async def test_participant_window_keeps_complete_opening_and_closing_checks(
    tmp_path, monkeypatch, action,
):
    from test_selected_input_read_node import read_fixture

    async with read_fixture(tmp_path, monkeypatch) as value:
        declaration = value.issuer._selected_record(value.selected).declaration
        view = value.issuer.read_selected_participant_view(declaration, value.selected)
        selected_code = source_module.WorkspaceSourceObservationRuntime.revalidate_selected_package.__code__
        declaration_code = source_module.WorkspaceSourceObservationRuntime.revalidate_declarations.__code__
        closure_code = admission_module.WorkspaceDeclarationScopeRuntime._closure.__code__
        counts = {selected_code: 0, declaration_code: 0, closure_code: 0}

        def profile(frame, event, _arg):
            if event == "call" and frame.f_code in counts:
                counts[frame.f_code] += 1

        previous = sys.getprofile()
        try:
            sys.setprofile(profile)
            if action == "read":
                returned = value.issuer.read_selected_participant_view(declaration, value.selected)
                assert returned == view
            else:
                value.issuer.validate_selected_participant_view(declaration, value.selected, view=view)
        finally:
            sys.setprofile(previous)
        assert counts == {selected_code: 2, declaration_code: 4, closure_code: 2}
        assert value.issuer._semantic_source_window is None


@pytest.mark.parametrize("target", ["body", "profile", "interrupt"])
async def test_participant_window_finishes_source_checks_and_node_cleanup(
    tmp_path, monkeypatch, target,
):
    from test_selected_input_read_node import open_read, read_fixture

    # isort: split
    from aware_code_retained_registry_policy_runtime.selected_participant_calculation import (
        validate_selected_participant_view,
    )

    # isort: split
    from aware_workspace_runtime import direct_command_composition as composition

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            original_record = composition._selected_input_read_record(node)
            path = value.root / (
                "workspaces/network/modules/main/package/a.bin" if target == "body"
                else "workspaces/network/aware.workspace.toml"
            )
            before = path.read_bytes()
            fired = False

            def profile(frame, event, _arg):
                nonlocal fired
                if (not fired and event == "return"
                    and frame.f_code is validate_selected_participant_view.__code__):
                    fired = True
                    if target == "interrupt":
                        raise KeyboardInterrupt("participant computation interrupted")
                    path.write_bytes(before + b"\nchanged")

            previous = sys.getprofile()
            try:
                sys.setprofile(profile)
                with pytest.raises((SourceObservationUnavailable, KeyboardInterrupt, BaseExceptionGroup)):
                    node.validate()
            finally:
                sys.setprofile(previous)
                path.write_bytes(before)
            assert fired
            assert value.issuer._semantic_source_window is None
            assert original_record.command is original_record.factory is original_record.stack is None
            assert original_record.expectations == original_record.results == ()
            with pytest.raises(RuntimeError, match="terminal"):
                node.validate()


@pytest.mark.parametrize("target", ["binding", "closure"])
async def test_participant_window_checks_provisional_values_after_closing_io(
    tmp_path, monkeypatch, target,
):
    from test_selected_input_read_node import open_read, read_fixture

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            pair_code = admission_module.WorkspaceDeclarationScopeRuntime._read_source_projection_pair.__code__
            read_code = admission_module.WorkspaceDeclarationScopeRuntime._read_source_projection_pair.__code__
            provisional = original = None
            fired = False

            def profile(frame, event, arg):
                nonlocal provisional, original, fired
                if event == "return" and frame.f_code is pair_code and provisional is None:
                    binding, closure = arg
                    provisional = binding.expectation if target == "binding" else closure
                    original = getattr(provisional, "package_id" if target == "binding" else "consumer_scope_key")
                elif (not fired and provisional is not None and event == "return"
                      and frame.f_code is read_code and frame.f_locals.get("closing") is not None):
                    fired = True
                    object.__setattr__(provisional, "package_id" if target == "binding" else "consumer_scope_key", "forged")

            previous = sys.getprofile()
            try:
                sys.setprofile(profile)
                with pytest.raises((SourceObservationUnavailable, BaseExceptionGroup)):
                    node.validate()
            finally:
                sys.setprofile(previous)
                if provisional is not None:
                    object.__setattr__(provisional, "package_id" if target == "binding" else "consumer_scope_key", original)
            assert fired
            assert value.issuer._semantic_source_window is None
            with pytest.raises(RuntimeError, match="terminal"):
                node.validate()


@pytest.mark.parametrize("location", ["instance", "class", "table"])
@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
async def test_participant_window_uses_guarded_original_dispatch(
    tmp_path, monkeypatch, location, mode,
):
    from test_selected_input_read_node import open_read, read_fixture

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            name = "_original_participant_source_window"
            original = admission_module._GROUP_METHOD_FUNCTIONS[name]
            calls = []

            def restore():
                if location == "table":
                    admission_module._GROUP_METHOD_FUNCTIONS[name] = original
                elif location == "instance":
                    delattr(value.issuer, name)
                else:
                    setattr(type(value.issuer), name, original)

            def hostile(*args, **kwargs):
                calls.append(True)
                if mode == "restore":
                    restore()
                if mode == "raise":
                    raise AssertionError("substituted participant window")

            if location == "table":
                monkeypatch.setitem(admission_module._GROUP_METHOD_FUNCTIONS, name, hostile)
            elif location == "instance":
                monkeypatch.setattr(value.issuer, name, hostile)
            else:
                monkeypatch.setattr(type(value.issuer), name, hostile)
            try:
                with pytest.raises((SourceObservationUnavailable, BaseExceptionGroup)):
                    node.validate()
            finally:
                restore()
            assert calls == []
            assert value.issuer._semantic_source_window is None
            with pytest.raises(RuntimeError, match="terminal"):
                node.validate()


async def test_participant_window_releases_publication_interruption_before_yield(
    tmp_path, monkeypatch,
):
    from test_selected_input_read_node import open_read, read_fixture

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            code = admission_module.WorkspaceDeclarationScopeRuntime._original_participant_source_window.__wrapped__.__code__
            fired = False

            def trace(frame, event, _arg):
                nonlocal fired
                if (not fired and event == "line" and frame.f_code is code
                    and value.issuer._semantic_source_window is not None):
                    fired = True
                    raise KeyboardInterrupt("participant window publication interrupted")
                return trace

            previous = sys.gettrace()
            try:
                sys.settrace(trace)
                with pytest.raises((KeyboardInterrupt, BaseExceptionGroup)):
                    node.validate()
            finally:
                sys.settrace(previous)
            assert fired
            assert value.issuer._semantic_source_window is None
            with pytest.raises(RuntimeError, match="terminal"):
                node.validate()


@asynccontextmanager
async def _original_scoped_result(tmp_path, monkeypatch):
    from test_selected_input_read_node import open_read, read_fixture
    from test_v3_source_admission import _coordinate

    # isort: split
    from aware_code_semantic_contract_runtime import (
        ContentDigest,
        SemanticConfigurationCoordinate,
        SemanticImplementationCoordinate,
    )
    from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
    from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
        PACKAGE_CONTEXT_INPUT_REF,
    )
    from aware_code_semantic_contract_runtime.runtime import SemanticBody

    async with read_fixture(tmp_path, monkeypatch) as value:
        host = inputs.SemanticInputProducerHost()
        contexts = (inputs.SemanticInputContextContract("package_context", PACKAGE_CONTEXT_INPUT_REF),)
        output = SemanticBody(_coordinate("prepared", b"prepared"), b"prepared")

        async def produce(_):
            assert value.issuer._semantic_source_window is None
            return output

        registration = inputs.register_semantic_input_producer(
            host, declaration=inputs.SemanticInputProducerDeclaration(
                "fixture.original-scope", "fixture.original-scope.v1",
                SemanticImplementationCoordinate("fixture/scope", ContentDigest.of_bytes(b"code")),
                SemanticConfigurationCoordinate("fixture/scope", ContentDigest.of_bytes(b"config")),
                (inputs.SemanticInputSourceContract("raw_source", value.coordinates[0].coordinate.contract),),
                "prepared", output.coordinate.contract, context_contracts=contexts,
            ), producer=produce, validator=value.issuer,
            validator_entrance=value.issuer.validate_semantic_input_source,
            reader=value.issuer, reader_entrance=value.issuer.read_semantic_input_sources,
            context_validator_entrance=value.issuer.validate_semantic_input_context,
            retain_result=True,
            validation_scope_entrance=inputs.capture_semantic_input_validation_scope(value.issuer),
        )
        try:
            session = open_read(value)
            node = session.__enter__()
            try:
                expected = node.prepare_source_expectation(
                    use_ref="original-result-scope", stage="pre_request",
                    source_coordinates=value.coordinates, context_contracts=contexts,
                )
                result = await inputs.execute_registered_semantic_input(
                    host, registration, source_admission=value.selected, expected=expected,
                )
                yield value, host, registration, expected, result
            finally:
                try:
                    session.__exit__(None, None, None)
                except BaseExceptionGroup as error:
                    # Expected source-family retirement is also reported at close.
                    _, unexpected = error.split(SourceObservationUnavailable)
                    if unexpected is not None:
                        raise unexpected
        finally:
            host.close()


def _verify_scoped_result(values):
    from aware_code_semantic_contract_runtime import semantic_input_producer as inputs

    value, host, registration, expected, result = values
    inputs.validate_registered_semantic_input_result(
        host, registration, source_admission=value.selected, expected=expected, result=result,
    )


async def test_original_result_scope_shares_source_context_but_keeps_callbacks(tmp_path, monkeypatch):
    async with _original_scoped_result(tmp_path, monkeypatch) as values:
        value = values[0]
        cls = type(value.issuer)
        codes = {
            "capture": source_module.WorkspaceSourceObservationRuntime.revalidate_selected_package.__code__,
            "source": cls.validate_semantic_input_source.__code__,
            "context": cls.validate_semantic_input_context.__code__,
        }
        counts = dict.fromkeys(codes, 0)

        def profile(frame, event, _):
            if event == "call":
                for name, code in codes.items():
                    if frame.f_code is code:
                        counts[name] += 1

        previous = sys.getprofile()
        try:
            sys.setprofile(profile)
            _verify_scoped_result(values)
        finally:
            sys.setprofile(previous)
        assert counts == {"capture": 2, "source": 4, "context": 2}
        assert value.issuer._semantic_source_window is None
        assert values[1]._results


@pytest.mark.parametrize("phase", ["source", "context", "closing"])
@pytest.mark.parametrize("mutation", ["result", "expected", "closure"])
async def test_original_result_scope_rejects_late_mutation_and_restoration(
    tmp_path, monkeypatch, phase, mutation,
):
    from aware_code_semantic_contract_runtime import ContractViolation

    async with _original_scoped_result(tmp_path, monkeypatch) as values:
        value, host, _, expected, result = values
        cls = type(value.issuer)
        code = {
            "source": cls._validate_semantic_input_source.__code__,
            "context": cls.validate_semantic_input_context.__code__,
            "closing": cls._read_source_projection_pair.__code__,
        }[phase]
        target = original = None
        changed = False
        provisional = None

        def profile(frame, event, _):
            nonlocal target, original, changed, provisional
            if not changed and event == "return" and frame.f_code is code:
                window = value.issuer._semantic_source_window
                if window is not None:
                    provisional = window.closure
                if phase == "closing":
                    closing = frame.f_locals.get("closing")
                    if closing is None:
                        return
                    provisional = closing.closure
                changed = True
                target = result if mutation == "result" else expected if mutation == "expected" else window.closure if window else provisional
                if target is None:
                    changed = False
                    return
                field = "canonical_body" if mutation == "result" else "use_ref" if mutation == "expected" else "consumer_scope_key"
                original = getattr(target, field)
                object.__setattr__(target, field, b"forged" if mutation == "result" else "forged")

        previous = sys.getprofile()
        try:
            sys.setprofile(profile)
            with pytest.raises((ContractViolation, SourceObservationUnavailable, BaseExceptionGroup)):
                _verify_scoped_result(values)
        finally:
            sys.setprofile(previous)
            if target is not None:
                field = "canonical_body" if mutation == "result" else "use_ref" if mutation == "expected" else "consumer_scope_key"
                object.__setattr__(target, field, original)
        assert changed and not host._results
        assert value.issuer._semantic_source_window is None
        with pytest.raises((ContractViolation, SourceObservationUnavailable)):
            _verify_scoped_result(values)
        # Code owns result retirement; borrowed source-family cleanup is separate.


async def test_original_result_scope_interrupted_publication_releases_window(tmp_path, monkeypatch):
    async with _original_scoped_result(tmp_path, monkeypatch) as values:
        value, host, _, _, _ = values
        code = type(value.issuer)._original_semantic_source_window.__wrapped__.__code__
        fired = False

        def trace(frame, event, _):
            nonlocal fired
            if (not fired and event == "line" and frame.f_code is code
                and value.issuer._semantic_source_window is not None):
                fired = True
                raise KeyboardInterrupt("interrupted scope publication")
            return trace

        previous = sys.gettrace()
        try:
            sys.settrace(trace)
            with pytest.raises(KeyboardInterrupt, match="scope publication"):
                _verify_scoped_result(values)
        finally:
            sys.settrace(previous)
        assert fired and not host._results
        assert value.issuer._semantic_source_window is None


@pytest.mark.parametrize("location", ["instance", "class"])
@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
async def test_original_result_scope_rejects_substituted_scope_without_calls(
    tmp_path, monkeypatch, location, mode,
):
    from aware_code_semantic_contract_runtime import ContractViolation

    async with _original_scoped_result(tmp_path, monkeypatch) as values:
        value, host, _, _, _ = values
        name = "semantic_input_validation_scope"
        genuine = admission_module._GROUP_METHOD_FUNCTIONS[name]
        calls = []

        def restore():
            if location == "instance":
                delattr(value.issuer, name)
            elif location == "class":
                setattr(type(value.issuer), name, genuine)
            else:
                admission_module._GROUP_METHOD_FUNCTIONS[name] = genuine

        def poison(*args, **kwargs):
            calls.append(True)
            if mode == "restore":
                restore()
            if mode == "raise":
                raise RuntimeError("foreign scope")

        if location == "table":
            monkeypatch.setitem(admission_module._GROUP_METHOD_FUNCTIONS, name, poison)
        else:
            monkeypatch.setattr(value.issuer if location == "instance" else type(value.issuer), name, poison)
        try:
            with pytest.raises((ContractViolation, SourceObservationUnavailable)):
                _verify_scoped_result(values)
        finally:
            restore()
        assert not calls and not host._results
        assert value.issuer._semantic_source_window is None
        with pytest.raises((ContractViolation, SourceObservationUnavailable)):
            _verify_scoped_result(values)


async def test_original_result_scope_rejects_source_edit_before_terminal_return(tmp_path, monkeypatch):
    from aware_code_semantic_contract_runtime import ContractViolation

    async with _original_scoped_result(tmp_path, monkeypatch) as values:
        value, host, _, _, _ = values
        target = value.root / "workspaces/network/modules/main/package/a.bin"
        original = target.read_bytes()
        code = type(value.issuer)._validate_semantic_input_source.__code__
        changed = False

        def profile(frame, event, _):
            nonlocal changed
            if not changed and event == "return" and frame.f_code is code:
                changed = True
                target.write_bytes(b"changed during synchronous original checks")

        previous = sys.getprofile()
        try:
            sys.setprofile(profile)
            with pytest.raises((ContractViolation, SourceObservationUnavailable, BaseExceptionGroup)):
                _verify_scoped_result(values)
        finally:
            sys.setprofile(previous)
            target.write_bytes(original)
        assert changed and not host._results
        assert value.issuer._semantic_source_window is None
        with pytest.raises((ContractViolation, SourceObservationUnavailable)):
            _verify_scoped_result(values)


@pytest.mark.parametrize("target", ["code", "closure"])
@pytest.mark.parametrize("phase", ["entry", "dispatch", "yield"])
async def test_original_result_scope_native_origin_rejects_restamping(
    tmp_path, monkeypatch, target, phase,
):
    import inspect

    from aware_code_semantic_contract_runtime import ContractViolation
    from aware_code_semantic_contract_runtime import semantic_input_producer as inputs

    async with _original_scoped_result(tmp_path, monkeypatch) as values:
        value, host, _, _, _ = values
        function = type(value.issuer).semantic_input_validation_scope
        original_code = function.__code__
        cell = function.__closure__[0]
        original_cell = cell.cell_contents
        calls = []
        changed = False

        def make_poison():
            captured = None

            def poison(self, source_admission, *, expected):
                if captured:
                    raise AssertionError("replacement scope executed")

            return poison

        poison = make_poison()

        def install():
            nonlocal changed
            changed = True
            if target == "code":
                function.__code__ = poison.__code__
            else:
                cell.cell_contents = poison

        helper = inputs._original_result_validation_scope.__wrapped__
        lines, first = inspect.getsourcelines(helper)
        dispatch_line = first + next(i for i, text in enumerate(lines) if text.strip() == "function = type(origin[0])(")

        def trace(frame, event, _):
            if event == "call" and frame.f_code is poison.__code__:
                calls.append(True)
            if not changed and (
                (
                    phase == "dispatch" and event == "line"
                    and frame.f_code is helper.__code__ and frame.f_lineno == dispatch_line
                ) or (
                    phase == "yield" and event == "return" and frame.f_code is original_code
                )
            ):
                install()
            return trace

        if phase == "entry":
            install()
        previous = sys.gettrace()
        try:
            sys.settrace(trace)
            with pytest.raises((ContractViolation, SourceObservationUnavailable, BaseExceptionGroup)):
                _verify_scoped_result(values)
        finally:
            sys.settrace(previous)
            function.__code__ = original_code
            cell.cell_contents = original_cell
        assert changed and not calls and not host._results
        assert value.issuer._semantic_source_window is None
        with pytest.raises((ContractViolation, SourceObservationUnavailable)):
            _verify_scoped_result(values)


async def test_selected_policy_scope_shares_projections_keeps_callbacks_and_closes(tmp_path, monkeypatch):
    from contextlib import contextmanager

    from test_selected_input_read_node import read_fixture

    async with read_fixture(tmp_path, monkeypatch) as value:
        issuer, source = value.issuer, value.selected
        declaration = issuer._selected_record(source).declaration
        expected = issuer._declarations[declaration].expectation
        binding = issuer.read_selected_package_source(source)
        view = issuer.read_selected_participant_view(declaration, source)
        kind = type(issuer)
        names = ("validate_declaration_scope", "validate_selected_package_source",
                 "validate_selected_participant_view")
        codes = {name: getattr(kind, name).__code__ for name in names}
        capture = source_module.WorkspaceSourceObservationRuntime.revalidate_declarations.__code__
        counts = {code: 0 for code in (*codes.values(), capture)}

        def profile(frame, event, arg):
            if event == "call" and frame.f_code in counts:
                counts[frame.f_code] += 1

        def original_checks():
            issuer.validate_declaration_scope(declaration, expectation=expected)
            issuer.read_declaration_scope(declaration)
            issuer.validate_declaration_scope(declaration, expectation=expected)
            issuer.read_selected_package_source(source)
            issuer.validate_selected_package_source(source, expectation=binding.expectation)
            issuer.validate_selected_participant_view(declaration, source, view=view)

        previous = sys.getprofile()
        try:
            sys.setprofile(profile)
            original_checks()
            separate = counts.copy()
            counts.update(dict.fromkeys(counts, 0))
            with contextmanager(issuer.selected_source_validation_scope)(declaration, source):
                original_checks()
            shared = counts.copy()
        finally:
            sys.setprofile(previous)
        assert issuer._semantic_source_window is None
        assert all(shared[code] == separate[code] > 0 for code in codes.values())
        assert shared[capture] == 4 and separate[capture] == 18


@pytest.mark.parametrize("change", ["source", "declaration", "projection", "interrupt"])
async def test_selected_policy_scope_performs_terminal_original_checks(tmp_path, change):
    from contextlib import contextmanager

    async with fixture(tmp_path) as (root, _, observer, issuer, observed, expected):
        declaration = issuer.capture_declaration_scope(
            observation=observed, consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expected,
        )
        selected = observer.observe_selected_package(
            declaration=observed, workspace_manifest_path="workspaces/network/aware.workspace.toml",
            module_id="main", package_id="example",
        )
        source = issuer.bind_selected_package_source(declaration=declaration, selected=selected)
        with (
            pytest.raises(KeyboardInterrupt if change == "interrupt" else SourceObservationUnavailable),
            contextmanager(issuer.selected_source_validation_scope)(declaration, source),
        ):
            issuer.read_declaration_scope(declaration)
            if change == "source":
                (root / "workspaces/network/modules/main/package/body.bin").write_bytes(b"changed")
            elif change == "declaration":
                (root / "workspaces/network/aware.workspace.toml").write_text("changed")
            elif change == "projection":
                record = issuer._declarations[declaration]
                object.__setattr__(record.projection, "consumer_scope_key", "forged")
            else:
                raise KeyboardInterrupt("original policy validation interrupted")
        assert issuer._semantic_source_window is None

@pytest.mark.parametrize("consumer", ["execution", "planning", "root", "catalog"])
@pytest.mark.parametrize("change", [None, "source", "projection", "interrupt"])
async def test_pure_consumer_verification_uses_original_scope_and_terminal_checks(
    tmp_path, monkeypatch, change, consumer,
):
    import inspect
    from contextlib import contextmanager
    from pathlib import Path

    import test_direct_cli_product_publication as qualification

    # isort: split
    from aware_code_retained_registry_policy_runtime import direct_host
    from aware_code_retained_registry_policy_runtime import (
        product_execution_inputs as recipe,
    )
    from aware_code_retained_registry_policy_runtime import (
        product_planning_source as planning,
    )
    from aware_code_retained_registry_policy_runtime import (
        selected_catalog_eligibility as catalog,
    )
    from aware_code_retained_registry_policy_runtime import (
        selected_root_intent as root,
    )
    from aware_code_retained_registry_policy_runtime.declaration_host import (
        _selected_policy_source,
    )
    from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
    from aware_code_semantic_contract_runtime.contracts import ContractViolation

    validation_code = {
        "execution": recipe.validate_execution_input_assembly,
        "planning": planning.RetainedProductPlanningDependencySource.read_dependencies,
        "root": root._derive_selected_root_intent,
        "catalog": catalog._derive,
    }[consumer].__code__
    result_code = inputs.validate_registered_semantic_input_result.__code__
    selected_code = source_module.WorkspaceSourceObservationRuntime.revalidate_selected_package.__code__
    source_code = admission_module.WorkspaceDeclarationScopeRuntime._original_participant_source_window.__wrapped__.__code__
    active = []
    outcomes = []
    holder = {}

    def profile(frame, event, _arg):
        if event == "call" and frame.f_code is validation_code:
            source_state = planning._SOURCES[frame.f_locals["self"]] if consumer == "planning" else None
            host = source_state.host if source_state is not None else frame.f_locals["host"]
            policy = source_state.policy if source_state is not None else frame.f_locals["policy"]
            issuer = direct_host._HOSTS[host].methods["scope"].receiver
            borrowed = issuer._semantic_source_window
            if borrowed is not None:
                assert borrowed.selected is direct_host._POLICIES[policy][1]
            active.append({
                "selected": 0, "results": 0, "borrowed": borrowed is not None,
                "required": len(frame.f_locals["assembly"].source_results) if consumer == "execution" else None,
            })
            holder["host"] = host
        elif event == "call" and active and frame.f_code is selected_code:
            active[-1]["selected"] += 1
        elif event == "call" and active and frame.f_code is source_code:
            holder["issuer"] = frame.f_locals["self"]
        elif (event == "return" and active and frame.f_code is result_code
              and frame.f_back.f_code is validation_code):
            active[-1]["results"] += 1
        elif event == "return" and active and frame.f_code is validation_code:
            row = active.pop()
            row["returned"] = _arg is not None or consumer == "execution"
            outcomes.append(row)

    scope_function = _selected_policy_source.__wrapped__
    scope_lines, scope_first = inspect.getsourcelines(scope_function)
    close_line = scope_first + [i for i, line in enumerate(scope_lines)
                                if line.strip() == "if not _verification_only:"][1]

    def trace(frame, event, _arg):
        if frame.f_code is not scope_function.__code__:
            return None
        if (event == "line" and frame.f_lineno == close_line and active
                and change is not None and "changed" not in holder):
            holder["changed"] = True
            issuer = holder["issuer"]
            assert issuer._semantic_source_window is not None
            if change == "source":
                selected = issuer._semantic_source_window.record
                evidence = selected.source_record[2]
                relative = next(item.relative_path for item in evidence.bodies if item.relative_path.endswith(".aware"))
                path = Path(issuer._source._session.binding.root_path) / evidence.package_root / relative
                holder["path"], holder["bytes"] = path, path.read_bytes()
                path.write_bytes(holder["bytes"] + b"\nchanged during pure verification\n")
            elif change == "projection":
                closure = issuer._semantic_source_window.closure
                holder["closure"], holder["consumer"] = closure, closure.consumer_scope_key
                object.__setattr__(closure, "consumer_scope_key", "forged")
            else:
                raise KeyboardInterrupt("pure consumer verification interrupted")
        return trace

    previous_trace = sys.gettrace()
    previous = sys.getprofile()
    try:
        with contextmanager(qualification.factory.__wrapped__)() as factory:
            sys.setprofile(profile)
            if change is not None:
                sys.settrace(trace)
            if change is None:
                await qualification.test_original_local_graph_executes_publishes_and_rereads(
                    tmp_path, factory, monkeypatch,
                )
            else:
                with pytest.raises((ContractViolation, SourceObservationUnavailable, RuntimeError, KeyboardInterrupt, BaseExceptionGroup)):
                    await qualification.test_original_local_graph_executes_publishes_and_rereads(
                        tmp_path, factory, monkeypatch,
                    )
    finally:
        sys.setprofile(previous)
        sys.settrace(previous_trace)
        if "path" in holder:
            holder["path"].write_bytes(holder["bytes"])
        if "closure" in holder:
            object.__setattr__(holder["closure"], "consumer_scope_key", holder["consumer"])
    if change is None:
        successful = [row for row in outcomes if row["returned"]]
        assert successful
        assert all(row["selected"] == (0 if row["borrowed"] else 2) and (row["required"] is None or row["results"] == row["required"]) for row in successful), (consumer, outcomes)
    else:
        assert holder["changed"]
        with pytest.raises(ContractViolation):
            direct_host._state(holder["host"])
    assert holder["issuer"]._semantic_source_window is None
    holder.clear()


@pytest.mark.parametrize("phase", ["entry", "after_copy"])
@pytest.mark.parametrize("entrance", ["validate_retained_declaration_scope_coordinate", "validate_detached_declaration_scope_coordinate"])
async def test_native_delegation_cell_substitution_is_zero_call_and_terminal(tmp_path, phase, entrance):
    from aware_code_semantic_contract_runtime import (
        retained_declaration_scope_validation as validation,
    )

    async with fixture(tmp_path) as (_, _, _, issuer, observed, expected):
        declaration = issuer.capture_declaration_scope(
            observation=observed, consumer_scope_key="workspaces/network/aware.workspace.toml", expectation=expected,
        )
        unrelated = issuer.capture_declaration_scope(
            observation=observed, consumer_scope_key="workspaces/kernel/aware.workspace.toml", expectation=expected,
        )
        function = getattr(validation, entrance)
        cells = dict(zip(function.__code__.co_freevars, function.__closure__, strict=True))
        cell = cells["native"]
        original = cell.cell_contents
        projection = issuer._declarations[declaration].projection
        calls = []

        class Foreign:
            def __getattribute__(self, name):
                calls.append(name)
                raise AssertionError("foreign native delegation")

        substitute = (Foreign(), Foreign(), Foreign())

        copy_frames = set()

        def profile(frame, event, value):
            copy_event = _declaration_copy_event(frame, event, projection, copy_frames)
            if (phase == "after_copy" and event == "return" and copy_event):
                cell.cell_contents = substitute

        previous = sys.getprofile()
        try:
            if phase == "entry":
                cell.cell_contents = substitute
            sys.setprofile(profile)
            with pytest.raises(SourceObservationUnavailable, match="coordinate_validator_changed"):
                issuer.read_declaration_scope(declaration)
        finally:
            sys.setprofile(previous)
            cell.cell_contents = original
        assert calls == []
        with pytest.raises(SourceObservationUnavailable, match="projection_changed"):
            issuer.read_declaration_scope(declaration)
        assert issuer.read_declaration_scope(unrelated).consumer_scope_key == "workspaces/kernel/aware.workspace.toml"


@pytest.mark.parametrize("phase", ["entry", "after_copy"])
@pytest.mark.parametrize("action", ["return", "raise", "restore"])
async def test_fresh_copy_original_binding_rejects_before_foreign_dispatch(
    tmp_path, monkeypatch, phase, action,
):
    validation = admission_module._declaration_validation
    async with fixture(tmp_path) as (_, _, _, issuer, observed, expected):
        handle = issuer.capture_declaration_scope(
            observation=observed, consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expected,
        )
        unrelated = issuer.capture_declaration_scope(
            observation=observed, consumer_scope_key="workspaces/kernel/aware.workspace.toml",
            expectation=expected,
        )
        original = validation.copy_retained_declaration_scope
        projection = issuer._declarations[handle].projection
        calls = []
        copy_frames = set()

        def poison(*args):
            calls.append(True)
            if action == "raise":
                raise RuntimeError("foreign copier")
            if action == "restore":
                monkeypatch.setattr(validation, "copy_retained_declaration_scope", original)
            return projection

        def profile(frame, event, result):
            copying = _declaration_copy_event(frame, event, projection, copy_frames)
            if phase == "after_copy" and event == "return" and copying:
                monkeypatch.setattr(validation, "copy_retained_declaration_scope", poison)

        previous = sys.getprofile()
        try:
            if phase == "entry":
                monkeypatch.setattr(validation, "copy_retained_declaration_scope", poison)
            sys.setprofile(profile)
            with pytest.raises(SourceObservationUnavailable, match="coordinate_validator_changed"):
                issuer.read_declaration_scope(handle)
        finally:
            sys.setprofile(previous)
            monkeypatch.setattr(validation, "copy_retained_declaration_scope", original)
        assert calls == []
        with pytest.raises(SourceObservationUnavailable, match="projection_changed"):
            issuer.read_declaration_scope(handle)
        assert issuer.read_declaration_scope(unrelated).consumer_scope_key == "workspaces/kernel/aware.workspace.toml"


@pytest.mark.parametrize("phase", ["entry", "after_copy"])
@pytest.mark.parametrize("target", ["code", "schema", "builtin"])
async def test_fresh_copy_origin_restoration_never_resumes_retired_family(
    tmp_path, phase, target,
):
    validation = admission_module._declaration_validation
    async with fixture(tmp_path) as (_, _, _, issuer, observed, expected):
        handle = issuer.capture_declaration_scope(
            observation=observed, consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expected,
        )
        unrelated = issuer.capture_declaration_scope(
            observation=observed, consumer_scope_key="workspaces/kernel/aware.workspace.toml",
            expectation=expected,
        )
        function = validation.copy_retained_declaration_scope
        projection = issuer._declarations[handle].projection
        cells = dict(zip(function.__code__.co_freevars, function.__closure__, strict=True))
        key = "copy_schema" if target == "schema" else "kind_of"
        cell = cells.get(key)
        original = function.__code__ if target == "code" else cell.cell_contents
        calls = []
        copy_frames = set()

        def hostile(*args):
            calls.append(True)
            raise AssertionError("foreign copy origin")

        def change():
            if target == "code":
                # The same function object cannot smuggle changed executable code.
                function.__code__ = function.__code__.replace(co_name="substituted_copy")
            else:
                cell.cell_contents = hostile

        def profile(frame, event, result):
            copying = _declaration_copy_event(frame, event, projection, copy_frames)
            if phase == "after_copy" and event == "return" and copying:
                change()

        previous = sys.getprofile()
        try:
            if phase == "entry":
                change()
            sys.setprofile(profile)
            with pytest.raises(SourceObservationUnavailable, match="coordinate_validator_changed"):
                issuer.read_declaration_scope(handle)
        finally:
            sys.setprofile(previous)
            if target == "code":
                function.__code__ = original
            else:
                cell.cell_contents = original
        assert calls == []
        with pytest.raises(SourceObservationUnavailable, match="projection_changed"):
            issuer.read_declaration_scope(handle)
        assert issuer.read_declaration_scope(unrelated).consumer_scope_key == "workspaces/kernel/aware.workspace.toml"


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
async def test_fresh_copy_interruption_retires_only_original_family(tmp_path, error_type):
    async with fixture(tmp_path) as (_, _, _, issuer, observed, expected):
        handle = issuer.capture_declaration_scope(
            observation=observed, consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expected,
        )
        unrelated = issuer.capture_declaration_scope(
            observation=observed, consumer_scope_key="workspaces/kernel/aware.workspace.toml",
            expectation=expected,
        )
        projection = issuer._declarations[handle].projection
        active = set()
        raised = []
        previous = sys.getprofile()

        def profile(frame, event, result):
            if frame.f_code is _ORIGINAL_DECLARATION_COPY_CODE:
                if event == "call" and frame.f_locals.get("value") is projection:
                    active.add(id(frame))
                return
            if (active and event == "return" and frame.f_code.co_name == "visit"
                and frame.f_back is not None and not raised):
                raised.append(True)
                raise error_type("copy interrupted")

        held = None
        try:
            sys.setprofile(profile)
            issuer.read_declaration_scope(handle)
        except error_type as error:
            held = error
        finally:
            sys.setprofile(previous)
        assert held is not None and raised == [True]
        trace = held.__traceback__
        while trace:
            frame = trace.tb_frame
            if frame.f_code.co_name == "copy_value":
                assert "value" not in frame.f_locals
                assert frame.f_locals["memo"] == {}
            if frame.f_code.co_name == "copy_declaration":
                assert not {"self", "origin", "value", "result"} & frame.f_locals.keys()
            trace = trace.tb_next
        with pytest.raises(SourceObservationUnavailable, match="projection_changed"):
            issuer.read_declaration_scope(handle)
        assert issuer.read_declaration_scope(unrelated).consumer_scope_key == "workspaces/kernel/aware.workspace.toml"


@pytest.mark.parametrize("change", ["source", "declaration", "original", "detached", "binding", "interrupt"])
async def test_owned_closing_reconstructs_before_freshness_and_retires_on_failure(
    tmp_path, monkeypatch, change,
):
    from aware_code_semantic_contract_runtime import ContractViolation

    async with _original_scoped_result(tmp_path, monkeypatch) as values:
        value, host, _, _, _ = values
        issuer = value.issuer
        code = type(issuer)._source_projection_pair.__code__
        reader_code = type(issuer)._read_source_projection_pair.__code__
        changed = False
        restore = []

        def profile(frame, event, result):
            nonlocal changed
            if changed or event != "return" or frame.f_code is not code:
                return
            parent = frame.f_back
            while parent is not None and parent.f_code is not reader_code:
                parent = parent.f_back
            closing = parent is not None and parent.f_locals.get("closing") is not None
            parent = None
            if closing:
                changed = True
                assert issuer._semantic_source_window is None
                if change in {"source", "declaration"}:
                    path = value.root / (
                        "workspaces/network/modules/main/package/a.bin"
                        if change == "source" else "workspaces/network/aware.workspace.toml"
                    )
                    original = path.read_bytes()
                    restore.append(lambda: path.write_bytes(original))
                    path.write_bytes(original + b"\nchanged during closing reconstruction\n")
                elif change == "interrupt":
                    raise KeyboardInterrupt("closing reconstruction interrupted")
                else:
                    binding, closure = result
                    target = (
                        issuer._selected_record(value.selected).declaration_record.projection
                        if change == "original" else closure if change == "detached"
                        else binding.expectation
                    )
                    field = "scope_key" if change == "binding" else "consumer_scope_key"
                    original = getattr(target, field)
                    restore.append(lambda: object.__setattr__(target, field, original))
                    object.__setattr__(target, field, "forged")

        previous = sys.getprofile()
        try:
            sys.setprofile(profile)
            with pytest.raises((ContractViolation, SourceObservationUnavailable, KeyboardInterrupt, BaseExceptionGroup)):
                _verify_scoped_result(values)
        finally:
            sys.setprofile(previous)
            for action in reversed(restore):
                action()
        assert changed and not host._results
        assert issuer._semantic_source_window is None
        with pytest.raises((ContractViolation, SourceObservationUnavailable)):
            _verify_scoped_result(values)


@pytest.mark.parametrize("foreign", ["unknown", "copied", "nonterminal"])
async def test_owned_closing_requires_exact_current_window_without_source_dispatch(
    tmp_path, monkeypatch, foreign,
):
    import copy

    async with _original_scoped_result(tmp_path, monkeypatch) as values:
        value, _, _, expected, _ = values
        issuer = value.issuer
        source_code = source_module.WorkspaceSourceObservationRuntime.revalidate_selected_package.__code__
        calls = []

        def profile(frame, event, _):
            if event == "call" and frame.f_code is source_code:
                calls.append(True)

        with issuer._original_semantic_source_window(value.selected, expected):
            current = issuer._semantic_source_window
            closing = object() if foreign == "unknown" else copy.copy(current) if foreign == "copied" else current
            previous = sys.getprofile()
            try:
                sys.setprofile(profile)
                with pytest.raises(SourceObservationUnavailable, match="semantic_source_window_origin_changed"):
                    issuer._read_source_projection_pair(
                        value.selected, terminal=foreign != "nonterminal", closing=closing,
                    )
            finally:
                sys.setprofile(previous)
            assert not calls and issuer._semantic_source_window is current
        assert issuer._semantic_source_window is None
        _verify_scoped_result(values)


async def test_owned_closing_rechecks_declarations_after_final_retained_body_reread(
    tmp_path, monkeypatch,
):
    from aware_code_semantic_contract_runtime import ContractViolation

    async with _original_scoped_result(tmp_path, monkeypatch) as values:
        value, host, _, _, _ = values
        issuer = value.issuer
        code = source_module.WorkspaceSourceObservationRuntime._reread.__code__
        selected_code = source_module.WorkspaceSourceObservationRuntime.revalidate_selected_package.__code__
        reader_code = type(issuer)._read_source_projection_pair.__code__
        path = value.root / "workspaces/network/aware.workspace.toml"
        original = path.read_bytes()
        changed = False

        def profile(frame, event, _):
            nonlocal changed
            if (changed or event != "return" or frame.f_code is not code
                or frame.f_back.f_code is not selected_code
                or "started" not in frame.f_back.f_locals):
                return
            parent = frame.f_back
            while parent is not None and parent.f_code is not reader_code:
                parent = parent.f_back
            closing = parent is not None and parent.f_locals.get("closing") is not None
            parent = None
            if closing:
                changed = True
                path.write_bytes(original + b"\nchanged after final retained body read\n")

        previous = sys.getprofile()
        try:
            sys.setprofile(profile)
            with pytest.raises((ContractViolation, SourceObservationUnavailable, BaseExceptionGroup)):
                _verify_scoped_result(values)
        finally:
            sys.setprofile(previous)
            path.write_bytes(original)
        assert changed and not host._results
        assert issuer._semantic_source_window is None
        with pytest.raises((ContractViolation, SourceObservationUnavailable)):
            _verify_scoped_result(values)


@pytest.mark.parametrize("field", ["thread_id", "selected", "record"])
@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
async def test_owned_closing_does_not_dispatch_unused_window_metadata(
    tmp_path, monkeypatch, field, mode,
):
    import inspect

    async with _original_scoped_result(tmp_path, monkeypatch) as values:
        issuer = values[0].issuer
        kind = admission_module._SemanticSourceValidationWindow
        descriptor = vars(kind)[field]
        function = type(issuer)._original_semantic_source_window.__wrapped__
        lines, start = inspect.getsourcelines(function)
        point = start + next(i for i, line in enumerate(lines)
                             if "fresh_binding = _original_group_method(" in line)
        calls = []
        installed = False

        def hostile(value):
            calls.append(True)
            if mode == "restore":
                setattr(kind, field, descriptor)
            if mode == "raise":
                raise AssertionError("unused window metadata dispatched")
            return descriptor.__get__(value, kind)

        def trace(frame, event, _):
            nonlocal installed
            if (not installed and event == "line" and frame.f_code is function.__code__
                and frame.f_lineno == point):
                installed = True
                setattr(kind, field, property(hostile))
            return trace

        previous = sys.gettrace()
        try:
            sys.settrace(trace)
            _verify_scoped_result(values)
        finally:
            sys.settrace(previous)
            setattr(kind, field, descriptor)
        assert installed and not calls and values[1]._results
        assert issuer._semantic_source_window is None
        _verify_scoped_result(values)


async def test_another_original_handle_cannot_spend_the_owning_context_success(
    tmp_path, monkeypatch,
):
    import inspect

    from aware_code_semantic_contract_runtime import ContractViolation

    async with _original_scoped_result(tmp_path, monkeypatch) as values:
        value, host, _, _, _ = values
        issuer = value.issuer
        record = issuer._selected_record(value.selected)
        another = issuer.bind_selected_package_source(
            declaration=record.declaration, selected=record.observation,
        )
        original_binding = issuer.read_selected_package_source(value.selected)
        assert issuer.read_selected_package_source(another) == original_binding
        function = type(issuer)._original_semantic_source_window.__wrapped__
        lines, start = inspect.getsourcelines(function)
        point = start + next(i for i, line in enumerate(lines)
                             if "fresh_binding = _original_group_method(" in line)
        spent = False

        def trace(frame, event, _):
            nonlocal spent
            if (not spent and event == "line" and frame.f_code is function.__code__
                and frame.f_lineno == point):
                spent = True
                # This private reconstruction returns consistent, non-authorizing
                # metadata. It cannot substitute for the owner's original close.
                result = issuer._read_source_projection_pair(
                    another, terminal=True, closing=issuer._semantic_source_window,
                )
                assert result[0] == original_binding
            return trace

        previous = sys.gettrace()
        try:
            sys.settrace(trace)
            with pytest.raises((ContractViolation, SourceObservationUnavailable, BaseExceptionGroup)):
                _verify_scoped_result(values)
        finally:
            sys.settrace(previous)
        assert spent and not host._results and issuer._semantic_source_window is None
        with pytest.raises((ContractViolation, SourceObservationUnavailable)):
            _verify_scoped_result(values)
        # A genuine unrelated handle remains a valid source; no approval or
        # authority was obtained from the detached reconstruction.
        assert issuer.read_selected_package_source(another) == original_binding
        issuer.release_selected_package_source(another)


@pytest.mark.parametrize("entrance", ["declaration", "selected", "pair"])
async def test_bracketed_reconstruction_does_not_redeliver_discarded_bodies(
    tmp_path, monkeypatch, entrance,
):
    from test_selected_input_read_node import read_fixture

    async with read_fixture(tmp_path, monkeypatch) as value:
        issuer = value.issuer
        declaration = issuer._selected_record(value.selected).declaration
        functions = {
            "delivery": source_module.WorkspaceSourceObservationRuntime.read_declarations,
            "broad": source_module.WorkspaceSourceObservationRuntime.revalidate_declarations,
            "selected": source_module.WorkspaceSourceObservationRuntime.revalidate_selected_package,
            "copy": type(issuer)._copy_original_declaration_scope,
        }
        codes = {function.__code__: name for name, function in functions.items()}
        counts = dict.fromkeys(functions, 0)

        def profile(frame, event, arg):
            if event == "call" and frame.f_code in codes:
                counts[codes[frame.f_code]] += 1

        previous = sys.getprofile()
        try:
            sys.setprofile(profile)
            if entrance == "declaration":
                result = issuer.read_declaration_scope(declaration)
            elif entrance == "selected":
                result = issuer.read_selected_package_source(value.selected)
            else:
                result = issuer._read_source_projection_pair(value.selected, terminal=True)
        finally:
            sys.setprofile(previous)
        assert result is not None
        assert counts == {
            "delivery": 0,
            "broad": 2 if entrance == "declaration" else 4,
            "selected": 0 if entrance == "declaration" else 2,
            "copy": 1,
        }
        # The original delivery remains available and verifies actual bytes.
        original = issuer._declaration_record(declaration)
        rows = issuer._source.read_declarations(original.observation)
        assert rows and all(type(body) is bytes for _, body in rows)


@pytest.mark.parametrize("phase", ["copy_entry", "copy_return"])
@pytest.mark.parametrize("target", ["declaration", "selected", "retained_declaration"])
async def test_reconstruction_preserves_terminal_byte_checks_and_node_retirement(
    tmp_path, monkeypatch, phase, target,
):
    from hashlib import sha256

    from test_selected_input_read_node import open_read, read_fixture

    async with read_fixture(tmp_path, monkeypatch) as value:
        issuer = value.issuer
        record = issuer._selected_record(value.selected).declaration_record
        projection = issuer._checked_declaration_origin(record).projection
        path = value.root / (
            "workspaces/network/modules/main/package/a.bin" if target == "selected"
            else "workspaces/network/aware.workspace.toml"
        )
        before = path.read_bytes()
        if target == "retained_declaration":
            digest = sha256(before).hexdigest()
            path, = tmp_path.rglob(digest + ".blob")
            assert path.read_bytes() == before
        with open_read(value) as node:
            node.prepare_source_expectation(
                use_ref="discarded-delivery-bytes", stage="pre_request",
                source_coordinates=value.coordinates,
            )
            frames = set()
            changed = []

            def profile(frame, event, result):
                if (_declaration_copy_event(frame, event, projection, frames)
                    and event == ("call" if phase == "copy_entry" else "return")
                    and not changed):
                    changed.append(True)
                    path.write_bytes(before + b"\nchanged")

            previous = sys.getprofile()
            try:
                sys.setprofile(profile)
                with pytest.raises((RuntimeError, ValueError, BaseExceptionGroup)):
                    node.validate()
            finally:
                sys.setprofile(previous)
                path.write_bytes(before)
            assert changed
            assert issuer._semantic_source_window is None
            with pytest.raises(RuntimeError, match="terminal"):
                node.validate()
            # A failed read does not dispose its borrowed Source owner.
            assert not issuer._source._closed


@pytest.mark.parametrize("phase", ["copy_entry", "copy_return"])
async def test_reconstruction_interruption_retires_node_and_releases_window(
    tmp_path, monkeypatch, phase,
):
    from test_selected_input_read_node import open_read, read_fixture

    async with read_fixture(tmp_path, monkeypatch) as value:
        issuer = value.issuer
        record = issuer._selected_record(value.selected).declaration_record
        projection = issuer._checked_declaration_origin(record).projection
        with open_read(value) as node:
            node.prepare_source_expectation(
                use_ref="discarded-delivery-interrupt", stage="pre_request",
                source_coordinates=value.coordinates,
            )
            frames = set()
            raised = []

            def profile(frame, event, result):
                if (_declaration_copy_event(frame, event, projection, frames)
                    and event == ("call" if phase == "copy_entry" else "return")
                    and not raised):
                    raised.append(True)
                    raise KeyboardInterrupt("reconstruction interrupted")

            previous = sys.getprofile()
            try:
                sys.setprofile(profile)
                with pytest.raises((KeyboardInterrupt, BaseExceptionGroup)):
                    node.validate()
            finally:
                sys.setprofile(previous)
            assert raised
            assert issuer._semantic_source_window is None
            with pytest.raises(RuntimeError, match="terminal"):
                node.validate()


@pytest.mark.parametrize("foreign", ["unknown", "copied"])
async def test_bracketed_copy_requires_exact_private_origin_without_foreign_behavior(
    tmp_path, monkeypatch, foreign,
):
    from test_selected_input_read_node import read_fixture

    calls = []

    class Foreign:
        def __eq__(self, other):
            calls.append("equality")
            raise AssertionError("foreign equality dispatched")

        def __hash__(self):
            calls.append("hash")
            raise AssertionError("foreign hash dispatched")

        def __getattribute__(self, name):
            calls.append("attribute")
            raise AssertionError("foreign attribute dispatched")

    async with read_fixture(tmp_path, monkeypatch) as value:
        issuer = value.issuer
        record = issuer._selected_record(value.selected).declaration_record
        origin = issuer._checked_declaration_origin(record)
        substituted = Foreign() if foreign == "unknown" else copy.copy(origin)
        with pytest.raises(SourceObservationUnavailable, match="copy_origin_differs"):
            issuer._closure(
                record.observation, record.consumer_scope_key,
                _bracketed_origin=substituted,
            )
        assert calls == []
        # Neither foreign nor copied metadata may retire the genuine family.
        issuer.read_selected_package_source(value.selected)
        issuer.read_declaration_scope(origin.handle)


async def test_input_metadata_operation_closes_source_window_before_return(tmp_path, monkeypatch):
    from test_selected_input_read_node import open_read, read_fixture

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            expected = node.prepare_source_expectation(
                use_ref='scoped-input-preparation',stage='pre_request',source_coordinates=value.coordinates,
            )
            assert expected.source_identity is value.selected
            assert value.issuer._semantic_source_window is None
            node.validate()
            assert value.issuer._semantic_source_window is None


@pytest.mark.parametrize('target',['selected','declaration','retained_declaration'])
async def test_input_metadata_operation_rejects_late_source_change(tmp_path, monkeypatch, target):
    from hashlib import sha256

    from aware_code_semantic_contract_runtime.semantic_input_producer import (
        SemanticInputProductionExpectation,
    )
    from test_selected_input_read_node import open_read, read_fixture

    async with read_fixture(tmp_path, monkeypatch) as value:
        path=value.root/('workspaces/network/modules/main/package/a.bin' if target=='selected' else 'workspaces/network/aware.workspace.toml')
        before=path.read_bytes()
        if target=='retained_declaration':
            path,=tmp_path.rglob(sha256(before).hexdigest()+'.blob')
        target_code=SemanticInputProductionExpectation.create.__func__.__code__
        armed=[]

        def profile(frame,event,arg):
            if event=='return' and frame.f_code is target_code and not armed:
                assert value.issuer._semantic_source_window is not None
                armed.append(True);path.write_bytes(before+b'\nchanged')

        with open_read(value) as node:
            old=sys.getprofile()
            try:
                sys.setprofile(profile)
                with pytest.raises((RuntimeError,ValueError,BaseExceptionGroup)):
                    node.prepare_source_expectation(use_ref='scoped-input-late-change',stage='pre_request',source_coordinates=value.coordinates)
            finally:
                sys.setprofile(old);path.write_bytes(before)
            assert armed
            assert value.issuer._semantic_source_window is None
            with pytest.raises(RuntimeError,match='terminal'):
                node.validate()
            assert not value.issuer._source._closed


async def test_input_metadata_operation_source_counts(tmp_path, monkeypatch):
    from test_selected_input_read_node import open_read, read_fixture

    async with read_fixture(tmp_path, monkeypatch) as value:
        functions=(source_module.WorkspaceSourceObservationRuntime.revalidate_declarations,source_module.WorkspaceSourceObservationRuntime.revalidate_selected_package,source_module.WorkspaceSourceObservationRuntime.read_declarations)
        codes={f.__code__:f.__name__ for f in functions};counts=dict.fromkeys(codes.values(),0)

        def profile(frame,event,arg):
            if event=='call' and frame.f_code in codes:counts[codes[frame.f_code]]+=1

        with open_read(value) as node:
            old=sys.getprofile()
            try:
                sys.setprofile(profile)
                node.prepare_source_expectation(use_ref='source-operation-counts',stage='pre_request',source_coordinates=value.coordinates)
            finally:
                sys.setprofile(old)
            print('SOURCE_OPERATION_COUNTS',counts)
            assert value.issuer._semantic_source_window is None


@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
@pytest.mark.parametrize("phase", ["entry", "late"])
async def test_input_metadata_operation_original_dispatch(tmp_path, monkeypatch, mode, phase):
    from aware_code_semantic_contract_runtime.semantic_input_producer import (
        SemanticInputProductionExpectation,
    )
    from test_selected_input_read_node import open_read, read_fixture

    # isort: split
    from aware_workspace_runtime import direct_command_composition as composition

    original = composition._original_group_method
    target = SemanticInputProductionExpectation.create.__func__.__code__
    calls, armed = [], []

    def hostile(*args, **kwargs):
        calls.append(True)
        if mode == "restore":
            monkeypatch.setattr(composition, "_original_group_method", original)
        if mode == "raise":
            raise RuntimeError("foreign dispatcher executed")

    def profile(frame, event, result):
        if event == "return" and frame.f_code is target and not armed:
            armed.append(True)
            monkeypatch.setattr(composition, "_original_group_method", hostile)

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            previous = sys.getprofile()
            try:
                if phase == "entry":
                    armed.append(True)
                    monkeypatch.setattr(composition, "_original_group_method", hostile)
                else:
                    sys.setprofile(profile)
                with pytest.raises((RuntimeError, SourceObservationUnavailable, BaseExceptionGroup)):
                    node.prepare_source_expectation(
                        use_ref="source-operation-dispatch", stage="pre_request",
                        source_coordinates=value.coordinates,
                    )
            finally:
                sys.setprofile(previous)
                monkeypatch.setattr(composition, "_original_group_method", original)
            assert armed and calls == []
            assert value.issuer._semantic_source_window is None
            with pytest.raises(RuntimeError, match="terminal"):
                node.validate()
            assert not value.issuer._source._closed


@pytest.mark.parametrize("change", ["original", "restamped", "interrupt"])
async def test_input_metadata_operation_terminal_original_and_interruption(
    tmp_path, monkeypatch, change,
):
    from aware_code_semantic_contract_runtime.semantic_input_producer import (
        SemanticInputProductionExpectation,
    )
    from test_selected_input_read_node import open_read, read_fixture

    target = SemanticInputProductionExpectation.create.__func__.__code__
    async with read_fixture(tmp_path, monkeypatch) as value:
        original = value.issuer._selected_record(value.selected).declaration_record
        before = original.projection.consumer_scope_key
        digest = original.digest
        armed = []
        restamped = []

        def profile(frame, event, result):
            if event == "return" and frame.f_code is target and not armed:
                armed.append(True)
                assert value.issuer._semantic_source_window is not None
                if change == "interrupt":
                    raise KeyboardInterrupt("source-operation interruption")
                object.__setattr__(original.projection, "consumer_scope_key", "workspaces/kernel/aware.workspace.toml")
                if change == "restamped":
                    object.__setattr__(original, "digest", original.projection.closure_digest)
                    restamped.append(True)

        with open_read(value) as node:
            previous = sys.getprofile()
            held = None
            try:
                sys.setprofile(profile)
                try:
                    node.prepare_source_expectation(
                        use_ref="source-operation-terminal", stage="pre_request",
                        source_coordinates=value.coordinates,
                    )
                except BaseException as error:  # noqa: BLE001 - inspect retained rejection and interruption custody
                    held = error
            finally:
                sys.setprofile(previous)
                object.__setattr__(original.projection, "consumer_scope_key", before)
                object.__setattr__(original, "digest", digest)
            assert held is not None and armed
            if change == "restamped":
                assert restamped, "canonical changed projection must restamp successfully"
            assert value.issuer._semantic_source_window is None
            assert not value.issuer._pre_request_inputs
            with pytest.raises(RuntimeError, match="terminal"):
                node.validate()
            assert not value.issuer._source._closed
            # The held exception must not preserve Workspace's command/read custody.
            traceback = held.__traceback__
            while traceback is not None:
                if traceback.tb_frame.f_code.co_filename.endswith("direct_command_composition.py"):
                    assert traceback.tb_frame.f_locals.get("record") is None
                traceback = traceback.tb_next



async def test_provider_resolution_operation_original_counts(tmp_path, monkeypatch):
    from test_selected_input_read_node import read_fixture

    # isort: split
    from aware_workspace_runtime import direct_command_composition as composition

    async with read_fixture(tmp_path, monkeypatch) as value:
        counts = {"broad": 0, "selected": 0}
        codes = {
            source_module.WorkspaceSourceObservationRuntime.revalidate_declarations.__code__: "broad",
            source_module.WorkspaceSourceObservationRuntime.revalidate_selected_package.__code__: "selected",
        }

        def observe(frame, event, result):
            if event == "call" and frame.f_code in codes:
                counts[codes[frame.f_code]] += 1

        previous = sys.getprofile()
        try:
            sys.setprofile(observe)
            key = composition._resolve_direct_workspace_exact_provider_key(value.command, value.selected)
        finally:
            sys.setprofile(previous)
        assert type(key) is str and key
        assert value.issuer._semantic_source_window is None
        print("PROVIDER_RESOLUTION_COUNTS", counts)



@pytest.mark.parametrize("target", ["source", "declaration", "retained", "original", "restamped", "interrupt"])
async def test_provider_resolution_operation_terminal_protection(tmp_path, monkeypatch, target):
    from aware_code_retained_registry_policy_runtime.declaration_eligibility import (
        calculate_declaration_eligibility,
    )
    from test_selected_input_read_node import read_fixture

    # isort: split
    from aware_workspace_runtime import direct_command_composition as composition

    async with read_fixture(tmp_path, monkeypatch) as value:
        record = value.issuer._selected_record(value.selected).declaration_record
        projection = record.projection
        old_scope, old_digest = projection.consumer_scope_key, record.digest
        path = value.root / (
            "workspaces/network/modules/main/package/a.bin" if target == "source"
            else "workspaces/network/aware.workspace.toml"
        )
        before = path.read_bytes()
        if target == "retained":
            from hashlib import sha256

            path, = tmp_path.rglob(sha256(before).hexdigest() + ".blob")
        armed, restamped = [], []

        def observe(frame, event, result):
            if event == "return" and frame.f_code is calculate_declaration_eligibility.__code__ and not armed:
                armed.append(True)
                assert value.issuer._semantic_source_window is not None
                if target == "interrupt":
                    raise KeyboardInterrupt("provider resolution interrupted")
                if target in {"source", "declaration", "retained"}:
                    path.write_bytes(before + b"\nchanged")
                else:
                    object.__setattr__(projection, "consumer_scope_key", "workspaces/kernel/aware.workspace.toml")
                    if target == "restamped":
                        object.__setattr__(record, "digest", projection.closure_digest)
                        restamped.append(True)

        previous = sys.getprofile()
        try:
            sys.setprofile(observe)
            with pytest.raises((RuntimeError, ValueError, KeyboardInterrupt, BaseExceptionGroup)):
                composition._resolve_direct_workspace_exact_provider_key(value.command, value.selected)
        finally:
            sys.setprofile(previous)
            path.write_bytes(before)
            object.__setattr__(projection, "consumer_scope_key", old_scope)
            object.__setattr__(record, "digest", old_digest)
        assert armed
        if target == "restamped":
            assert restamped
        assert value.issuer._semantic_source_window is None
        # This read owns its bracket, not the borrowed command or Source issuer.
        assert not value.issuer._source._closed


@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
@pytest.mark.parametrize("phase", ["entry", "late"])
async def test_provider_resolution_operation_original_dispatch(tmp_path, monkeypatch, mode, phase):
    from aware_code_retained_registry_policy_runtime.declaration_eligibility import (
        calculate_declaration_eligibility,
    )
    from test_selected_input_read_node import read_fixture

    # isort: split
    from aware_workspace_runtime import direct_command_composition as composition

    original = composition._original_group_method
    calls, armed = [], []

    def hostile(*args, **kwargs):
        calls.append(True)
        if mode == "restore":
            monkeypatch.setattr(composition, "_original_group_method", original)
        if mode == "raise":
            raise RuntimeError("foreign dispatcher executed")

    def observe(frame, event, result):
        if event == "return" and frame.f_code is calculate_declaration_eligibility.__code__ and not armed:
            armed.append(True)
            monkeypatch.setattr(composition, "_original_group_method", hostile)

    async with read_fixture(tmp_path, monkeypatch) as value:
        previous = sys.getprofile()
        try:
            if phase == "entry":
                armed.append(True)
                monkeypatch.setattr(composition, "_original_group_method", hostile)
            else:
                sys.setprofile(observe)
            with pytest.raises((RuntimeError, ValueError, BaseExceptionGroup)):
                composition._resolve_direct_workspace_exact_provider_key(value.command, value.selected)
        finally:
            sys.setprofile(previous)
            monkeypatch.setattr(composition, "_original_group_method", original)
        assert armed and calls == []
        assert value.issuer._semantic_source_window is None


async def test_checkpoint_mixed_grouped_batch_preserves_distinct_original_windows(tmp_path):
    from contextlib import contextmanager

    from test_grouped_selected_source_input import dependency_group, scope

    async with dependency_group(tmp_path) as (original, root, participant, edge):
        with scope(original, root=root, participants=(participant,), dependency_edges=(edge,)) as grouped:
            expectations = (root.selection_expected, grouped)
            with contextmanager(original.issuer.semantic_input_checkpoint_validation_scope)(
                original.selected, expected=root.selection_expected, expectations=expectations,
            ) as enabled:
                assert enabled is False
                assert original.issuer._semantic_source_window is None
                original.issuer._validate_retained_semantic_inputs(
                    original.selected, expectations=expectations, results=(),
                )
            assert original.issuer._semantic_source_window is None


async def test_checkpoint_same_source_uses_original_terminal_bracket(tmp_path, monkeypatch):
    from contextlib import contextmanager

    from test_selected_input_read_node import read_fixture

    async with read_fixture(tmp_path, monkeypatch) as value:
        issuer = value.issuer
        with issuer.original_pre_request_input(
            value.selected, use_ref="checkpoint-source", stage="pre_request", source_coordinates=value.coordinates,
        ) as expected:
            with contextmanager(issuer.semantic_input_checkpoint_validation_scope)(
                value.selected, expected=expected, expectations=(expected,),
            ) as enabled:
                assert enabled is True and issuer._semantic_source_window is not None
                issuer.validate_semantic_input_source(value.selected, expected=expected)
            assert issuer._semantic_source_window is None


@pytest.mark.parametrize("restore", [False, True, "late"])
async def test_selected_identity_comparison_rechecks_original_expectation(tmp_path, restore):
    from contextlib import nullcontext

    from aware_code_semantic_contract_runtime import ContractViolation
    from test_v3_source_admission import _original_selection

    cleanup = (pytest.raises(SourceObservationUnavailable, match="original_pre_request_input_required")
               if not restore else nullcontext())
    with cleanup:
        async with _original_selection(tmp_path, ontology=True) as value:
            # The producer result is genuine. Mutate only after its original Code
            # reader and the next original input check have completed.
            issuer = value.issuer
            member = type(issuer)._selected_input_values.__code__
            record_check = type(issuer)._pre_request_record.__code__
            source_check = type(issuer).validate_selected_package_source.__code__
            call_check = type(issuer)._call.__code__
            expected_package = value.expected.package_identity.package
            prior = expected_package.package_ref
            changed = []
            restored = []
            detached = []

            def mutate(frame, event, result):
                if event != "return" or frame.f_back is None or frame.f_back.f_code is not member:
                    return
                if frame.f_code is record_check and not changed and "selection" in frame.f_back.f_locals:
                    selection = frame.f_back.f_locals["selection"]
                    detached.append(selection.package)
                    object.__setattr__(expected_package, "package_ref", "package:forged@1")
                    object.__setattr__(selection.package, "package_ref", "package:forged@1")
                    changed.append(True)
                elif changed and (restore is True and frame.f_code is source_check
                                  or restore == "late" and frame.f_code is call_check
                                  and frame.f_locals.get("name") == "selected_package_evidence"):
                    object.__setattr__(expected_package, "package_ref", prior)
                    restored.append(True)

            before = sys.getprofile()
            sys.setprofile(mutate)
            try:
                with (
                    pytest.raises((ContractViolation, SourceObservationUnavailable, BaseExceptionGroup)),
                    issuer.original_selected_source_input(
                        value.selected, use_ref="selected-identity-mutation", stage="fixture_inner", **value.arguments,
                    ),
                ):
                    pytest.fail("changed original identity must not escape")
            finally:
                sys.setprofile(before)
                object.__setattr__(expected_package, "package_ref", prior)
            assert changed
            if restore:
                assert restored
