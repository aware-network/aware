"""Reuse admitted interpretation while preserving original byte-currentness."""

import copy
import sys
from dataclasses import replace

import pytest
from test_declaration_scope_admission import fixture

# isort: split
from aware_workspace_runtime import declaration_scope_admission as admission_module
from aware_workspace_runtime import source_observation as source_module
from aware_workspace_runtime.composition import RetainedWorkspaceCompositionProvider
from aware_workspace_runtime.source_observation_io import SourceObservationUnavailable


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
                binding, closure = value.issuer._read_source_projection_pair(value.selected)
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


async def test_batch_never_encloses_owner_execution_and_checks_original_result(
    tmp_path, monkeypatch
):
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

        def profile(frame, event, result):
            # Observe the genuine function; do not replace deepcopy or its
            # dispatchers. Mutate after entry checks, while it is running.
            if frame.f_code is genuine_copy.__code__ and frame.f_locals.get("x") is projection:
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

        def profile(frame, event, result):
            if (
                event == "return" and frame.f_code is genuine_copy.__code__
                and frame.f_locals.get("x") is record.projection
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

        def profile(frame, event, value):
            if (phase == "after_copy" and event == "return"
                and frame.f_code is copy.deepcopy.__code__ and frame.f_locals.get("x") is projection):
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
