"""Original Workspace/Code source joins, independently of parser installation.

The Code codecs are consumed from their committed owner source. Fixture semantic
producers exercise the original registered executor, not public SDK generation.
"""

import asyncio
import gc
import inspect
import os
import signal
import threading
import warnings
import weakref
from contextlib import ExitStack, asynccontextmanager
from dataclasses import replace
from types import SimpleNamespace

import pytest
from aware_code_semantic_contract_runtime import (
    retained_declaration_scope_codec as declaration_codec,
)
from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    SemanticConfigurationCoordinate,
    SemanticContractRef,
    SemanticImplementationCoordinate,
    SemanticValueCoordinate,
)
from aware_code_semantic_contract_runtime.grammar_profile_join import (
    validate_grammar_source_group_input,
)
from aware_code_semantic_contract_runtime.grammar_source_group import (
    GRAMMAR_SOURCE_GROUP_REF,
    decode_grammar_source_group,
)
from aware_code_semantic_contract_runtime.retained_declaration_scope_codec import (
    RETAINED_DECLARATION_SCOPE_V3_REF,
    decode_retained_declaration_scope,
    encode_retained_declaration_scope,
)
from aware_code_semantic_contract_runtime.runtime import SemanticBody
from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime.declaration_scope_admission import (
    WorkspaceDeclarationScopeRuntime,
    WorkspaceSelectedDependencyInputV1,
    WorkspaceSelectedSourceInputV1,
)
from test_declaration_scope_admission import fixture
from test_materialization_declaration_selection import _author_v3_repository
from test_v3_source_admission import _expected, _original_selection, _Validator

CONTEXTS = (
    inputs.SemanticInputContextContract(
        "grammar_source_group", GRAMMAR_SOURCE_GROUP_REF
    ),
)
DECLARATION_CONTEXTS = (
    inputs.SemanticInputContextContract(
        "declaration_scope", RETAINED_DECLARATION_SCOPE_V3_REF
    ),
    *CONTEXTS,
)


def carrier(original):
    return WorkspaceSelectedSourceInputV1(original.selected, **original.arguments)


def scope(
    original,
    *,
    use_ref="grouped",
    root=None,
    participants=(),
    dependency_edges=(),
    contexts=CONTEXTS,
):
    return original.issuer.original_grouped_selected_source_input(
        root=carrier(original) if root is None else root,
        participants=participants,
        dependency_edges=dependency_edges,
        use_ref=use_ref,
        stage="fixture_grouped_read",
        source_contracts=original.arguments["source_contracts"],
        context_contracts=contexts,
    )


def register(original, expected, produce):
    output = SemanticContractRef(
        "fixture.grouped-result", "1", ContentDigest.of_bytes(b"result")
    )
    return inputs.register_semantic_input_producer(
        original.host,
        declaration=inputs.SemanticInputProducerDeclaration(
            "fixture.grouped-reader",
            "fixture.grouped-reader.v1",
            SemanticImplementationCoordinate(
                "fixture/grouped-reader", ContentDigest.of_bytes(b"reader")
            ),
            SemanticConfigurationCoordinate(
                "fixture.grouped-config", ContentDigest.of_bytes(b"config")
            ),
            original.arguments["source_contracts"],
            "grouped_result",
            output,
            context_contracts=tuple(
                inputs.SemanticInputContextContract(
                    body.coordinate.role,
                    body.coordinate.contract,
                )
                for body in expected.context_bodies
            ),
        ),
        producer=produce,
        validator=original.issuer,
        validator_entrance=original.issuer.validate_semantic_input_source,
        context_validator_entrance=original.issuer.validate_semantic_input_context,
        reader=original.issuer,
        reader_entrance=original.issuer.read_semantic_input_sources,
    )


def result():
    body = b"observed group"
    ref = SemanticContractRef(
        "fixture.grouped-result", "1", ContentDigest.of_bytes(b"result")
    )
    return SemanticBody(
        SemanticValueCoordinate(
            "grouped_result",
            ref,
            "fixture:grouped-result",
            ContentDigest.of_bytes(body),
            len(body),
        ),
        body,
    )


async def test_original_group_flows_through_registered_code_and_retires(tmp_path):
    async with _original_selection(tmp_path) as original:
        with scope(original) as expected:
            assert expected.source_identity is original.selected
            assert expected.operation_identity is original.expected.operation_identity
            (group_body,) = expected.context_bodies
            assert group_body.coordinate.value_ref.startswith(
                "grammar-source-group:sha256:"
            )
            group = decode_grammar_source_group(group_body.canonical_body)
            assert len(group.members) == 1
            assert group.members[0].occurrence_ref == group.root_occurrence_ref
            assert (
                len(group.members[0].sources) == len(expected.source_coordinates) == 2
            )
            calls = []

            async def produce(value):
                detached = decode_grammar_source_group(
                    value.context_bodies[0].canonical_body
                )
                assert detached == group
                assert (
                    tuple(item.source for item in value.sources)
                    == expected.source_coordinates
                )
                assert not hasattr(value, "source_identity")
                calls.append(value)
                return result()

            registration = register(original, expected, produce)
            try:
                assert (
                    await inputs.execute_registered_semantic_input(
                        original.host,
                        registration,
                        source_admission=original.selected,
                        expected=expected,
                    )
                    == result()
                )
                assert len(calls) == 1
            finally:
                inputs.close_semantic_input_producer_registration(
                    original.host, registration
                )
        with pytest.raises(SourceObservationUnavailable):
            original.issuer.validate_semantic_input_source(
                original.selected, expected=expected
            )
        with (
            pytest.raises(SourceObservationUnavailable, match="replayed"),
            scope(original),
        ):
            pytest.fail("retired grouped use replayed")
        assert all(
            record.expected is not expected
            for record in original.issuer._pre_request_inputs.values()
        )
        # Original borrowed selection remains live for an independent use.
        with scope(original, use_ref="independent") as other:
            original.issuer.validate_semantic_input_context(
                original.selected, expected=other
            )


@pytest.mark.parametrize("change", ["source", "carrier", "registration", "cancel"])
async def test_grouped_changes_during_owner_execution_are_terminal(tmp_path, change):
    with pytest.raises(
        (SourceObservationUnavailable, ContractViolation, asyncio.CancelledError)
    ):
        async with _original_selection(tmp_path) as original:
            root = carrier(original)
            with scope(original, root=root) as expected:

                async def produce(_):
                    await asyncio.sleep(0)
                    if change == "source":
                        (
                            original.root
                            / "workspaces/network/modules/main/package/a.bin"
                        ).write_bytes(b"changed")
                    elif change == "carrier":
                        object.__setattr__(root, "result", replace(root.result))
                    elif change == "registration":
                        original.close_host()
                    else:
                        raise asyncio.CancelledError()
                    return result()

                registration = register(original, expected, produce)
                try:
                    await inputs.execute_registered_semantic_input(
                        original.host,
                        registration,
                        source_admission=original.selected,
                        expected=expected,
                    )
                finally:
                    inputs.close_semantic_input_producer_registration(
                        original.host, registration
                    )
    assert not original.issuer._pre_request_inputs


async def test_restored_carrier_cannot_resume_live_rejected_family(tmp_path):
    async with _original_selection(tmp_path) as original:
        root = carrier(original)
        with (
            pytest.raises(SourceObservationUnavailable),
            scope(original, root=root) as expected,
        ):
            object.__setattr__(root, "result", replace(root.result))
            with pytest.raises(SourceObservationUnavailable, match="binding_changed"):
                original.issuer.validate_semantic_input_context(
                    original.selected, expected=expected
                )
            object.__setattr__(root, "result", original.result)
            with pytest.raises(SourceObservationUnavailable):
                original.issuer.validate_semantic_input_context(
                    original.selected, expected=expected
                )


@pytest.mark.parametrize("bad", ["foreign", "duplicate", "bounds", "context"])
async def test_bad_group_preserves_unrelated_original_use(tmp_path, bad):
    async with _original_selection(tmp_path) as original:
        with scope(original, use_ref="survivor") as survivor:
            args = {"root": carrier(original)}
            if bad == "foreign":

                class Hostile:
                    def __getattribute__(self, name):
                        raise AssertionError("foreign attribute dispatched")

                args["root"] = Hostile()
            elif bad == "duplicate":
                args["participants"] = (carrier(original),)
            elif bad == "bounds":
                args["participants"] = (carrier(original),) * 128
            else:
                args["root"] = replace(carrier(original), source_contracts=())
            with (
                pytest.raises(
                    (SourceObservationUnavailable, ContractViolation, TypeError)
                ),
                scope(original, use_ref="bad", **args),
            ):
                pytest.fail("invalid group admitted")
            original.issuer.validate_semantic_input_source(
                original.selected, expected=survivor
            )


@asynccontextmanager
async def dependency_group(
    tmp_path, *, source_body=b"equal authored source", module_padding=0
):
    """Original sources/results/targets with a local planning comparison fixture.

    The inventory is issued by Workspace; its comparison validator is the
    existing unit fixture, not qualified installed Code planning authority.
    """
    from aware_code_semantic_contract_runtime.source_selection import (
        SOURCE_SELECTION_REF,
        SemanticSelectedSource,
        SemanticSourceSelection,
        source_selection_body,
    )
    from aware_code_semantic_contract_runtime.target_context_interfaces import (
        RetainedTargetExpectation,
    )

    async with fixture(tmp_path) as (
        repository,
        parent,
        observer,
        issuer,
        _,
        expectation,
    ):
        _author_v3_repository(repository)
        module = repository / "workspaces/network/modules/main/aware.module.toml"
        mapping = '[{dependency_kind="module",dependency_ref="child",targets=[{scope={kind="local"},module_id="main",package_id="nested"}],constraints=[]}]'
        module.write_text(
            module.read_text().replace(
                'dependency_targets={state="present",value=[]}',
                'dependency_targets={state="present",value=' + mapping + "}",
                1,
            )
        )
        if module_padding:
            module.write_text(module.read_text() + "#" + "p" * module_padding + "\n")
        package = repository / "workspaces/network/modules/main/package"
        for directory in (package, package / "child"):
            for filename in ("a.bin", "b.bin"):
                (directory / filename).write_bytes(source_body)
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
                module_id="main",
                package_id="example",
            ),
        )
        context = object()
        planning = replace(_expected(issuer, selected), stage="source_planning")
        issuer._bind_original_code_validator(_Validator(context, planning))
        _, inventory = issuer.issue_source_planning_pair(
            selected, context=context, expected=planning
        )
        (target_record,) = issuer._selected_targets[selected]
        target = target_record.membership
        target_expected = RetainedTargetExpectation(
            planning,
            target_record.context.source_identity_digest,
            target_record.context.package,
        )
        edge = WorkspaceSelectedDependencyInputV1(
            selected, target, inventory, target_expected, "module", "child"
        )
        raw_ref = SemanticContractRef(
            "fixture.raw", "1", ContentDigest.of_bytes(b"raw")
        )
        selected_ref = SemanticContractRef(
            "fixture.selected", "1", ContentDigest.of_bytes(b"selected")
        )
        source_contracts = (
            inputs.SemanticInputSourceContract("selected_raw", selected_ref),
        )
        with ExitStack() as stack:
            host = inputs.SemanticInputProducerHost()
            stack.callback(host.close)
            members = []
            for ordinal, handle in enumerate((selected, target)):
                evidence = issuer.inspect_selected_package_evidence(handle)
                coordinates = tuple(
                    inputs.SemanticInputSourceCoordinate(
                        body.relative_path,
                        SemanticValueCoordinate(
                            "raw_source",
                            raw_ref,
                            body.body_ref,
                            ContentDigest(body.content_digest),
                            body.size_bytes,
                        ),
                    )
                    for body in evidence.bodies
                )
                expected = stack.enter_context(
                    issuer.original_pre_request_input(
                        handle,
                        use_ref=f"selection-{ordinal}",
                        stage="fixture_selection",
                        source_coordinates=coordinates,
                    )
                )
                package_context = issuer.inspect_inputs(handle)[0]

                async def produce(value, package_context=package_context):
                    return source_selection_body(
                        SemanticSourceSelection(
                            package_context.package,
                            package_context.source_identity_digest,
                            value.input_digest,
                            (),
                            tuple(
                                SemanticSelectedSource(
                                    "selected_raw",
                                    selected_ref,
                                    item.source.relative_path,
                                    item.source.coordinate.digest,
                                )
                                for item in value.sources
                                if item.source.relative_path in {"a.bin", "b.bin"}
                            ),
                        ),
                        role="selection",
                    )

                registration = inputs.register_semantic_input_producer(
                    host,
                    declaration=inputs.SemanticInputProducerDeclaration(
                        f"fixture.selector.{ordinal}",
                        f"fixture.selector.{ordinal}.v1",
                        SemanticImplementationCoordinate(
                            "fixture/selector", ContentDigest.of_bytes(b"selector")
                        ),
                        SemanticConfigurationCoordinate(
                            "fixture.select-config",
                            ContentDigest.of_bytes(b"select-config"),
                        ),
                        (inputs.SemanticInputSourceContract("raw_source", raw_ref),),
                        "selection",
                        SOURCE_SELECTION_REF,
                    ),
                    producer=produce,
                    validator=issuer,
                    validator_entrance=issuer.validate_semantic_input_source,
                    reader=issuer,
                    reader_entrance=issuer.read_semantic_input_sources,
                    retain_result=True,
                )
                selected_body = await inputs.execute_registered_semantic_input(
                    host,
                    registration,
                    source_admission=handle,
                    expected=expected,
                )
                members.append(
                    WorkspaceSelectedSourceInputV1(
                        handle,
                        host,
                        registration,
                        expected,
                        selected_body,
                        source_contracts,
                    )
                )
            root, participant = members
            original = SimpleNamespace(
                root=repository,
                parent=parent,
                issuer=issuer,
                selected=selected,
                host=host,
                expected=root.selection_expected,
                arguments={"source_contracts": source_contracts},
                observer=observer,
                observation=observed,
                declaration=declaration,
                declaration_expected=expectation,
            )
            yield original, root, participant, edge


async def test_dependency_members_remain_separate_and_inputs_root_local(tmp_path):
    async with dependency_group(tmp_path) as (original, root, participant, edge):
        with scope(
            original, root=root, participants=(participant,), dependency_edges=(edge,)
        ) as expected:
            group = decode_grammar_source_group(
                expected.context_bodies[0].canonical_body
            )
            assert len(group.members) == 2
            assert len(group.dependency_edges) == 1
            assert len({member.occurrence_ref for member in group.members}) == 2
            assert (
                group.members[0].sources[0].relative_path
                == group.members[1].sources[0].relative_path
            )
            assert (
                group.members[0].sources[0].body_hex
                == group.members[1].sources[0].body_hex
            )
            assert len(expected.source_coordinates) == 2
            assert original.issuer._semantic_source_window is None
            assert (
                len(
                    original.issuer.read_semantic_input_sources(
                        root.selected, expected=expected
                    )
                )
                == 2
            )


@pytest.mark.parametrize(
    "change", ["kind", "ref", "target", "inventory", "missing_edge"]
)
async def test_edge_must_bind_original_owner_target_and_declared_labels(
    tmp_path, change
):
    async with dependency_group(tmp_path) as (original, root, participant, edge):
        if change == "kind":
            edge = replace(edge, dependency_kind="invented")
        elif change == "ref":
            edge = replace(edge, dependency_ref="invented")
        elif change == "target":
            edge = replace(edge, target=root.selected)
        elif change == "inventory":
            edge = replace(edge, inventory_admission=object())
        edges = () if change == "missing_edge" else (edge,)
        with (
            pytest.raises((SourceObservationUnavailable, ContractViolation, TypeError)),
            scope(
                original, root=root, participants=(participant,), dependency_edges=edges
            ),
        ):
            pytest.fail("unauthenticated edge admitted")
        assert (
            len(original.issuer._pre_request_inputs) == 2
        )  # Only borrowed selections remain.


async def test_participant_mutation_is_terminal_even_when_root_unchanged(tmp_path):
    with pytest.raises((SourceObservationUnavailable, ContractViolation)):
        async with dependency_group(tmp_path) as (original, root, participant, edge):
            with scope(
                original,
                root=root,
                participants=(participant,),
                dependency_edges=(edge,),
            ) as expected:
                changed = (
                    original.root
                    / "workspaces/network/modules/main/package/child/a.bin"
                )
                changed.write_bytes(b"mutated participant")
                with pytest.raises((SourceObservationUnavailable, ContractViolation)):
                    original.issuer.validate_semantic_input_context(
                        root.selected, expected=expected
                    )
                changed.write_bytes(b"equal authored source")
                with pytest.raises(SourceObservationUnavailable):
                    original.issuer.validate_semantic_input_context(
                        root.selected, expected=expected
                    )
    assert not original.issuer._pre_request_inputs


@pytest.mark.parametrize(
    "method",
    [
        "_check_origin",
        "_grouped_selected_values",
        "_check_group_source_contracts",
        "_selected_input_values",
        "_selection_context_values",
        "_validate_semantic_input_source",
    ],
)
@pytest.mark.parametrize("behavior", ["return", "raise", "restore"])
@pytest.mark.parametrize("phase", ["prepare", "validate"])
async def test_group_helper_substitution_never_dispatches_and_restoration_refuses(
    tmp_path,
    monkeypatch,
    method,
    behavior,
    phase,
):
    async with _original_selection(tmp_path) as original:
        issuer_type = type(original.issuer)
        genuine = inspect.getattr_static(issuer_type, method)
        calls = []

        def hostile(*args, **kwargs):
            calls.append((args, kwargs))
            if behavior == "restore":
                setattr(issuer_type, method, genuine)
            if behavior == "raise":
                raise AssertionError("substituted helper executed")

        if phase == "prepare":
            with monkeypatch.context() as patch:
                patch.setattr(issuer_type, method, hostile)
                with (
                    pytest.raises(
                        SourceObservationUnavailable, match="method_substituted"
                    ),
                    scope(original),
                ):
                    pytest.fail("substituted issuer prepared a group")
            with scope(original, use_ref="survivor") as survivor:
                original.issuer.validate_semantic_input_context(
                    original.selected, expected=survivor
                )
        else:
            with (
                pytest.raises(SourceObservationUnavailable),
                scope(original) as expected,
            ):
                with monkeypatch.context() as patch:
                    patch.setattr(issuer_type, method, hostile)
                    with pytest.raises(
                        SourceObservationUnavailable, match="method_substituted"
                    ):
                        original.issuer.validate_semantic_input_context(
                            original.selected, expected=expected
                        )
                with pytest.raises(SourceObservationUnavailable):
                    original.issuer.validate_semantic_input_context(
                        original.selected, expected=expected
                    )
            # The failed group never owned the borrowed predecessor selection.
            with scope(original, use_ref="survivor") as survivor:
                original.issuer.validate_semantic_input_context(
                    original.selected, expected=survivor
                )
        assert calls == []


async def test_unknown_group_source_does_not_dispatch_or_retire_original(tmp_path):
    async with _original_selection(tmp_path) as original:
        with scope(original) as expected:

            class Hostile:
                def __getattribute__(self, name):
                    raise AssertionError("foreign source dispatched")

            with pytest.raises(SourceObservationUnavailable):
                original.issuer.validate_semantic_input_source(
                    Hostile(), expected=expected
                )
            original.issuer.validate_semantic_input_context(
                original.selected, expected=expected
            )


async def test_wrong_thread_retires_only_group_not_borrowed_selection(tmp_path):
    async with _original_selection(tmp_path) as original:
        errors = []
        with (
            pytest.raises(SourceObservationUnavailable),
            scope(original) as expected,
        ):

            def verify():
                try:
                    original.issuer.validate_semantic_input_context(
                        original.selected, expected=expected
                    )
                except SourceObservationUnavailable as error:
                    errors.append(error)

            worker = threading.Thread(target=verify)
            worker.start()
            worker.join(timeout=2)
            assert not worker.is_alive()
            assert len(errors) == 1 and type(errors[0]) is SourceObservationUnavailable
            with pytest.raises(SourceObservationUnavailable):
                original.issuer.validate_semantic_input_context(
                    original.selected, expected=expected
                )
        with scope(original, use_ref="same-borrowed-origin") as survivor:
            original.issuer.validate_semantic_input_context(
                original.selected, expected=survivor
            )


@pytest.mark.skipif(not hasattr(os, "fork"), reason="POSIX fork is required")
async def test_fork_refuses_before_inherited_lock_and_preserves_parent(tmp_path):
    async with _original_selection(tmp_path) as original:
        with scope(original) as expected:
            locked = threading.Event()
            release = threading.Event()

            def hold_lock():
                with original.issuer._lock:
                    locked.set()
                    release.wait(timeout=5)

            holder = threading.Thread(target=hold_lock)
            holder.start()
            assert locked.wait(timeout=2)
            read_fd, write_fd = os.pipe()
            # This intentionally reproduces the inherited-lock failure mode.
            # Warning emission is process/platform dependent; unlike a warns
            # assertion this recorder cannot unwind the child before _exit.
            with warnings.catch_warnings(record=True) as fork_warnings:
                child = os.fork()
            if child == 0:
                os.close(read_fd)
                signal.alarm(2)
                try:
                    original.issuer.validate_semantic_input_context(
                        original.selected, expected=expected
                    )
                except SourceObservationUnavailable:
                    os.write(write_fd, b"refused")
                    os._exit(0)
                except BaseException:  # noqa: BLE001 - child must not unwind borrowed owners.
                    os._exit(2)
                os._exit(3)
            os.close(write_fd)
            try:
                assert all(
                    item.category is DeprecationWarning
                    and "multi-threaded" in str(item.message)
                    for item in fork_warnings
                )
                _, status = os.waitpid(child, 0)  # noqa: ASYNC222 - child alarm bounds this lock probe.
                assert os.waitstatus_to_exitcode(status) == 0
                assert os.read(read_fd, 32) == b"refused"
            finally:
                os.close(read_fd)
                release.set()
                holder.join(timeout=2)
            assert not holder.is_alive()
            original.issuer.validate_semantic_input_context(
                original.selected, expected=expected
            )


@pytest.mark.parametrize("behavior", ["return", "raise", "restore"])
async def test_original_reader_substitution_is_zero_call_terminal(
    tmp_path, monkeypatch, behavior
):
    async with _original_selection(tmp_path) as original:
        source = original.issuer._source
        source_type = type(source)
        genuine = inspect.getattr_static(source_type, "read_selected_package")
        calls = []

        def hostile(*args, **kwargs):
            calls.append((args, kwargs))
            if behavior == "restore":
                source_type.read_selected_package = genuine
            if behavior == "raise":
                raise AssertionError("foreign source reader executed")
            return b"copied source"

        with (
            pytest.raises(SourceObservationUnavailable),
            scope(original) as expected,
        ):
            with monkeypatch.context() as patch:
                patch.setattr(source_type, "read_selected_package", hostile)
                with pytest.raises(SourceObservationUnavailable):
                    original.issuer.validate_semantic_input_context(
                        original.selected, expected=expected
                    )
            with pytest.raises(SourceObservationUnavailable):
                original.issuer.validate_semantic_input_context(
                    original.selected, expected=expected
                )
        assert calls == []
        # A group-local binding failure need not expire the borrowed result.
        with scope(original, use_ref="survivor") as survivor:
            original.issuer.validate_semantic_input_context(
                original.selected, expected=survivor
            )


@pytest.mark.parametrize("behavior", ["return", "raise", "restore"])
async def test_substituted_carrier_slot_never_invokes_foreign_descriptor(
    tmp_path, monkeypatch, behavior
):
    async with _original_selection(tmp_path) as original:
        root = carrier(original)
        genuine = inspect.getattr_static(WorkspaceSelectedSourceInputV1, "result")
        calls = []

        def hostile(instance):
            calls.append(instance)
            if behavior == "restore":
                WorkspaceSelectedSourceInputV1.result = genuine
            if behavior == "raise":
                raise AssertionError("foreign slot executed")
            return original.result

        with (
            pytest.raises(SourceObservationUnavailable),
            scope(original, root=root) as expected,
        ):
            with monkeypatch.context() as patch:
                patch.setattr(
                    WorkspaceSelectedSourceInputV1, "result", property(hostile)
                )
                with pytest.raises(
                    SourceObservationUnavailable, match="exact_type_required"
                ):
                    original.issuer.validate_semantic_input_context(
                        original.selected, expected=expected
                    )
            with pytest.raises(SourceObservationUnavailable):
                original.issuer.validate_semantic_input_context(
                    original.selected, expected=expected
                )
        assert calls == []


async def test_foreign_issuer_rejects_without_accessing_attributes(tmp_path):
    async with _original_selection(tmp_path) as original:

        class Hostile:
            def __getattribute__(self, name):
                raise AssertionError("foreign issuer dispatched")

        with (
            pytest.raises(
                SourceObservationUnavailable, match="original_grouped_issuer"
            ),
            WorkspaceDeclarationScopeRuntime.original_grouped_selected_source_input(
                Hostile(),
                root=carrier(original),
                participants=(),
                dependency_edges=(),
                use_ref="foreign",
                stage="fixture",
                source_contracts=original.arguments["source_contracts"],
                context_contracts=CONTEXTS,
            ),
        ):
            pytest.fail("foreign issuer admitted a group")
        with scope(original, use_ref="survivor") as expected:
            original.issuer.validate_semantic_input_context(
                original.selected, expected=expected
            )


async def test_grouped_source_does_not_infer_unavailable_semantic_roots(
    tmp_path, monkeypatch
):
    import test_v3_source_admission as original_source

    author = original_source._author_v3_repository

    def rootless_author(root):
        author(root)
        module = root / "workspaces/network/modules/main/aware.module.toml"
        module.write_text(
            "\n".join(
                f'{field}={{state="unavailable"}}'
                if (field := line.split("=", 1)[0]) in ("namespace", "owned_roots")
                else line
                for line in module.read_text().splitlines()
            )
            + "\n"
        )

    monkeypatch.setattr(original_source, "_author_v3_repository", rootless_author)
    async with _original_selection(tmp_path, ontology=True) as original:
        with scope(original) as expected:
            group = decode_grammar_source_group(
                expected.context_bodies[0].canonical_body
            )
            assert len(group.members) == 1
            assert (
                len(
                    original.issuer.read_semantic_input_sources(
                        original.selected, expected=expected
                    )
                )
                == 1
            )
            with pytest.raises(
                SourceObservationUnavailable, match="occurrence_evidence_unavailable"
            ):
                original.issuer.inspect_inputs(original.selected)


@pytest.mark.parametrize("known", [False, True])
@pytest.mark.parametrize(
    "contexts", [CONTEXTS, DECLARATION_CONTEXTS], ids=["group", "declaration-and-group"]
)
async def test_held_group_rejection_does_not_keep_issuer_alive(
    tmp_path, known, contexts
):
    async def reject():
        held = None
        async with _original_selection(tmp_path) as original:
            reference = weakref.ref(original.issuer)
            root = carrier(original)
            try:
                with (
                    scope(original, root=root, contexts=contexts) as expected,
                    scope(
                        original, use_ref="unrelated", contexts=contexts
                    ) as unrelated,
                ):
                    if known:
                        object.__setattr__(root, "result", replace(root.result))
                    try:
                        original.issuer.validate_semantic_input_context(
                            original.selected if known else object(),
                            expected=expected,
                        )
                    except SourceObservationUnavailable as error:
                        held = error
                    assert held is not None
                    original.issuer.validate_semantic_input_context(
                        original.selected,
                        expected=unrelated,
                    )
            except SourceObservationUnavailable:
                # The known group is terminal; scope exit independently refuses.
                assert known
        del original, root, expected, unrelated
        return reference, held

    reference, held = await reject()
    gc.collect()
    assert held is not None
    assert reference() is None


async def test_declaration_context_uses_original_enclosing_module_in_code_execution(
    tmp_path,
):
    async with dependency_group(tmp_path) as (original, root, participant, edge):
        with scope(
            original,
            root=root,
            participants=(participant,),
            dependency_edges=(edge,),
            contexts=DECLARATION_CONTEXTS,
        ) as expected:
            contexts = {body.coordinate.role: body for body in expected.context_bodies}
            declared = contexts["declaration_scope"]
            closure = decode_retained_declaration_scope(declared.canonical_body)
            assert declared.canonical_body == encode_retained_declaration_scope(
                original.issuer.read_declaration_scope(original.declaration),
            )
            module = next(
                item
                for item in next(
                    item
                    for item in closure.scopes
                    if item.scope_key == "workspaces/network/aware.workspace.toml"
                ).projection.modules
                if item.module_id == "main"
            )
            assert (
                module.manifest.body
                == (original.root / module.manifest.relative_path).read_bytes()
            )
            assert (
                module.manifest.relative_path
                == "workspaces/network/modules/main/aware.module.toml"
            )
            assert all(
                item.relative_path != "../aware.module.toml"
                for item in expected.source_coordinates
            )
            assert (
                len(
                    {
                        declared.coordinate.digest,
                        closure.closure_digest,
                        RETAINED_DECLARATION_SCOPE_V3_REF.schema_digest,
                    }
                )
                == 3
            )
            assert (
                declared.coordinate.value_ref
                == "workspace-context:" + declared.coordinate.digest.value
            )
            assert closure.local_profiles and closure.profile_associations
            assert len(expected.source_coordinates) == 2
            calls = []

            async def produce(value):
                delivered = {
                    item.coordinate.role: item for item in value.context_bodies
                }
                group = decode_grammar_source_group(
                    delivered["grammar_source_group"].canonical_body
                )
                validate_grammar_source_group_input(group, input=value)
                assert (
                    decode_retained_declaration_scope(
                        delivered["declaration_scope"].canonical_body
                    )
                    == closure
                )
                assert value.input_digest == expected.input_digest
                assert not hasattr(value, "declaration_handle")
                calls.append(value.input_digest)
                return result()

            registration = register(original, expected, produce)
            try:
                assert (
                    await inputs.execute_registered_semantic_input(
                        original.host,
                        registration,
                        source_admission=original.selected,
                        expected=expected,
                    )
                    == result()
                )
                assert len(calls) == 1
                assert original.issuer._semantic_source_window is None
            finally:
                inputs.close_semantic_input_producer_registration(
                    original.host, registration
                )
        with pytest.raises(SourceObservationUnavailable):
            original.issuer.validate_semantic_input_context(
                original.selected, expected=expected
            )
        assert (
            len(original.issuer._pre_request_inputs) == 2
        )  # Borrowed selections remain.


@pytest.mark.parametrize("poison", ["role", "version", "schema"])
async def test_declaration_context_requires_complete_original_contract(
    tmp_path, poison
):
    reference = RETAINED_DECLARATION_SCOPE_V3_REF
    role = "declaration_scope"
    if poison == "role":
        role = "copied_declaration"
    elif poison == "version":
        reference = replace(reference, version="4")
    else:
        reference = replace(
            reference, schema_digest=ContentDigest.of_bytes(b"foreign schema")
        )
    async with _original_selection(tmp_path) as original:
        with (
            pytest.raises(
                SourceObservationUnavailable,
                match="original_declaration_context_required",
            ),
            scope(
                original,
                contexts=(
                    inputs.SemanticInputContextContract(role, reference),
                    *CONTEXTS,
                ),
            ),
        ):
            pytest.fail("foreign declaration contract admitted")
        with scope(original, use_ref="unrelated-survivor") as expected:
            original.issuer.validate_semantic_input_context(
                original.selected, expected=expected
            )


@pytest.mark.parametrize(
    "method", ["read_declaration_scope", "_grouped_declaration_body"]
)
@pytest.mark.parametrize("behavior", ["return", "raise", "restore"])
@pytest.mark.parametrize("phase", ["prepare", "validate"])
async def test_declaration_reader_substitution_is_zero_call_and_terminal(
    tmp_path,
    monkeypatch,
    method,
    behavior,
    phase,
):
    async with _original_selection(tmp_path) as original:
        issuer_type = type(original.issuer)
        genuine = inspect.getattr_static(issuer_type, method)
        calls = []

        def hostile(*args, **kwargs):
            calls.append((args, kwargs))
            if behavior == "restore":
                setattr(issuer_type, method, genuine)
            if behavior == "raise":
                raise AssertionError("foreign declaration reader executed")

        if phase == "prepare":
            with monkeypatch.context() as patch:
                patch.setattr(issuer_type, method, hostile)
                with (
                    pytest.raises(SourceObservationUnavailable),
                    scope(original, contexts=DECLARATION_CONTEXTS),
                ):
                    pytest.fail("foreign declaration reader admitted")
        else:
            with (
                pytest.raises(SourceObservationUnavailable),
                scope(original, contexts=DECLARATION_CONTEXTS) as expected,
            ):
                with monkeypatch.context() as patch:
                    patch.setattr(issuer_type, method, hostile)
                    with pytest.raises(SourceObservationUnavailable):
                        original.issuer.validate_semantic_input_context(
                            original.selected, expected=expected
                        )
                with pytest.raises(SourceObservationUnavailable):
                    original.issuer.validate_semantic_input_context(
                        original.selected, expected=expected
                    )
        assert calls == []
        with scope(
            original,
            use_ref="borrowed-selection-survivor",
            contexts=DECLARATION_CONTEXTS,
        ) as survivor:
            original.issuer.validate_semantic_input_context(
                original.selected, expected=survivor
            )


@pytest.mark.parametrize("behavior", ["return", "raise", "restore"])
async def test_declaration_encoder_substitution_never_dispatches(
    tmp_path, monkeypatch, behavior
):
    async with _original_selection(tmp_path) as original:
        genuine = declaration_codec.encode_retained_declaration_scope
        calls = []

        def hostile(*args, **kwargs):
            calls.append((args, kwargs))
            if behavior == "restore":
                declaration_codec.encode_retained_declaration_scope = genuine
            if behavior == "raise":
                raise AssertionError("foreign encoder executed")
            return b"copied closure"

        with (
            pytest.raises(SourceObservationUnavailable),
            scope(original, contexts=DECLARATION_CONTEXTS) as expected,
        ):
            with monkeypatch.context() as patch:
                patch.setattr(
                    declaration_codec, "encode_retained_declaration_scope", hostile
                )
                with pytest.raises(SourceObservationUnavailable):
                    original.issuer.validate_semantic_input_context(
                        original.selected, expected=expected
                    )
            with pytest.raises(SourceObservationUnavailable):
                original.issuer.validate_semantic_input_context(
                    original.selected, expected=expected
                )
        assert calls == []
        with scope(
            original, use_ref="restored-codec-survivor", contexts=DECLARATION_CONTEXTS
        ) as survivor:
            original.issuer.validate_semantic_input_context(
                original.selected, expected=survivor
            )


@pytest.mark.parametrize("replace_root", [False, True])
async def test_equal_detached_declaration_cannot_replace_nominal_group_origin(
    tmp_path, replace_root
):
    async with dependency_group(tmp_path) as (original, root, participant, edge):
        other = original.issuer.capture_declaration_scope(
            observation=original.observation,
            consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=original.declaration_expected,
        )
        assert other is not original.declaration
        assert encode_retained_declaration_scope(
            original.issuer.read_declaration_scope(other)
        ) == encode_retained_declaration_scope(
            original.issuer.read_declaration_scope(original.declaration)
        )
        other_record = original.issuer._declaration_record(other)
        poisoned = [original.issuer._selected_record(participant.selected)]
        if replace_root:
            poisoned.append(original.issuer._selected_record(root.selected))
        saved = [(record.declaration, record.declaration_record) for record in poisoned]
        with (
            pytest.raises(SourceObservationUnavailable),
            scope(
                original,
                root=root,
                participants=(participant,),
                dependency_edges=(edge,),
                contexts=DECLARATION_CONTEXTS,
            ) as expected,
        ):
            try:
                for record in poisoned:
                    object.__setattr__(record, "declaration", other)
                    object.__setattr__(record, "declaration_record", other_record)
                with pytest.raises(SourceObservationUnavailable):
                    original.issuer.validate_semantic_input_context(
                        original.selected, expected=expected
                    )
            finally:
                for record, (handle, retained) in zip(poisoned, saved, strict=True):
                    object.__setattr__(record, "declaration", handle)
                    object.__setattr__(record, "declaration_record", retained)
            with pytest.raises(SourceObservationUnavailable):
                original.issuer.validate_semantic_input_context(
                    original.selected, expected=expected
                )
        original.issuer.read_declaration_scope(other)
        original.issuer.read_declaration_scope(original.declaration)


@pytest.mark.parametrize("member", ["module", "profile"])
async def test_declaration_mutation_during_registered_owner_rejects_after_return(
    tmp_path,
    member,
):
    calls = []
    # Mutation also invalidates the fixture's borrowed selection owners on exit.
    with pytest.raises(SourceObservationUnavailable):
        async with dependency_group(tmp_path) as (original, root, participant, edge):
            module = original.root / "workspaces/network/modules/main/aware.module.toml"
            if member == "profile":
                closure = original.issuer.read_declaration_scope(original.declaration)
                module = (
                    original.root / closure.local_profiles[0].manifest.relative_path
                )
            genuine = module.read_bytes()
            with (
                pytest.raises(SourceObservationUnavailable),
                scope(
                    original,
                    root=root,
                    participants=(participant,),
                    dependency_edges=(edge,),
                    contexts=DECLARATION_CONTEXTS,
                ) as expected,
            ):

                async def produce(value):
                    calls.append(value.input_digest)
                    module.write_bytes(genuine + b"\n# changed during owner await\n")
                    await asyncio.sleep(0)
                    return result()

                registration = register(original, expected, produce)
                try:
                    with pytest.raises(
                        (SourceObservationUnavailable, ContractViolation)
                    ):
                        await inputs.execute_registered_semantic_input(
                            original.host,
                            registration,
                            source_admission=original.selected,
                            expected=expected,
                        )
                    module.write_bytes(genuine)
                    with pytest.raises(SourceObservationUnavailable):
                        original.issuer.validate_semantic_input_context(
                            original.selected, expected=expected
                        )
                finally:
                    module.write_bytes(genuine)
                    inputs.close_semantic_input_producer_registration(
                        original.host, registration
                    )
    assert len(calls) == 1


async def test_declaration_body_copy_with_valid_digest_cannot_replace_retained_input(
    tmp_path,
):
    async with _original_selection(tmp_path) as original:
        with (
            pytest.raises(SourceObservationUnavailable),
            scope(original, contexts=DECLARATION_CONTEXTS) as expected,
        ):
            retained = expected.context_bodies
            declaration, group = retained
            copied = declaration.canonical_body + b" "
            altered = SemanticBody(
                replace(
                    declaration.coordinate,
                    digest=ContentDigest.of_bytes(copied),
                    size_bytes=len(copied),
                ),
                copied,
            )
            try:
                object.__setattr__(expected, "context_bodies", (altered, group))
                with pytest.raises((SourceObservationUnavailable, ContractViolation)):
                    original.issuer.validate_semantic_input_context(
                        original.selected, expected=expected
                    )
            finally:
                object.__setattr__(expected, "context_bodies", retained)
            with pytest.raises(SourceObservationUnavailable):
                original.issuer.validate_semantic_input_context(
                    original.selected, expected=expected
                )
        with scope(
            original,
            use_ref="unchanged-borrowed-selection",
            contexts=DECLARATION_CONTEXTS,
        ) as survivor:
            original.issuer.validate_semantic_input_context(
                original.selected, expected=survivor
            )


async def test_declaration_and_group_use_one_complete_context_budget(tmp_path):
    async with dependency_group(
        tmp_path,
        source_body=b"s" * (7 * 1024 * 1024 // 4),
        module_padding=900 * 1024,
    ) as (original, root, _, _):
        raw = encode_retained_declaration_scope(
            original.issuer.read_declaration_scope(original.declaration)
        )
        with scope(original, root=root) as expected:
            group_raw = expected.context_bodies[0].canonical_body
        assert len(raw) < inputs.MAX_CONTEXT_BYTES
        assert len(group_raw) < inputs.MAX_CONTEXT_BYTES
        assert len(raw) + len(group_raw) > inputs.MAX_CONTEXT_BYTES
        retained = len(original.issuer._pre_request_inputs)
        with (
            pytest.raises(ContractViolation, match="context body budget"),
            scope(
                original,
                root=root,
                contexts=DECLARATION_CONTEXTS,
            ),
        ):
            pytest.fail("independent context budgets silently combined")
        assert len(original.issuer._pre_request_inputs) == retained
        original.issuer.validate_semantic_input_source(
            root.selected, expected=root.selection_expected
        )
