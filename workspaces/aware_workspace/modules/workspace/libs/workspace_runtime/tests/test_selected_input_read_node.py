"""Local read custody over real source resources; product hosting is a fixture.

These proofs do not install an inspect provider or admit a Code invocation.
"""

import asyncio
import copy
import gc
import os
import pickle
import signal
import threading
from contextlib import ExitStack, asynccontextmanager
from dataclasses import replace
from types import SimpleNamespace
from weakref import finalize, ref

import pytest
from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime import direct_command_composition as composition
from test_v3_source_admission import _pre_request_source


class _Host:
    pass


@asynccontextmanager
async def read_fixture(tmp_path, monkeypatch):
    async with _pre_request_source(tmp_path, with_local_provider=True) as (root, owner, issuer, selected, coordinates):
        original = issuer._selected_record(selected)
        sources = composition._DirectWorkspaceDeclarationSources(
            issuer._exclusion, issuer._source, original.declaration_record.observation,
            issuer, original.declaration, original.declaration_record.expectation, None,
        )
        epoch, expected_epoch = object(), object()
        catalog = SimpleNamespace(
            validate_current_catalog_epoch=lambda *_, **__: None,
            _command_parent=SimpleNamespace(records=SimpleNamespace(
                _read_current=lambda *_, **__: SimpleNamespace(preparation=epoch),
            )),
        )
        command = composition._DirectWorkspaceCommandResources(
            owner, issuer._exclusion._parent, sources, catalog,
        )
        composition._COMMAND_ASSEMBLIES[owner] = (
            command, composition._resource_references(command),
            composition._resource_references(sources),
        )
        host, registration, contribution = _Host(), object(), object()
        staged = composition._DirectWorkspaceStagedCommandResources(
            command, None, (), (contribution,), (),
        )
        factory = object.__new__(composition._DirectWorkspaceOriginFactory)
        factory._command, factory._owner, factory._joint = command, owner, catalog
        factory._epoch, factory._epoch_expected = epoch, expected_epoch
        composition._ORIGIN_FACTORIES.add(factory)
        composition._POLICY_HOSTS[host] = staged
        composition._SELECTED_INPUT_FACTORIES[host] = factory
        monkeypatch.setattr(
            composition, "read_selected_provider_product_contribution",
            lambda value: SimpleNamespace(expected=SimpleNamespace(registration=registration))
            if value is contribution else pytest.fail("foreign contribution read"),
        )
        try:
            yield SimpleNamespace(
                root=root, command=command, selected=selected, issuer=issuer,
                coordinates=coordinates, host=host, registration=registration,
                factory=factory,
            )
        finally:
            composition._COMMAND_ASSEMBLIES.pop(owner, None)
            composition._POLICY_HOSTS.pop(host, None)
            composition._SELECTED_INPUT_FACTORIES.pop(host, None)
            composition._ORIGIN_FACTORIES.discard(factory)


def open_read(value):
    return composition._command_owned_selected_input_read_session(
        value.command, host=value.host, selected_source=value.selected,
        registration=value.registration,
    )


@pytest.mark.parametrize("return_mode", ("original", "copied", "replayed"))
async def test_parent_scoped_source_survives_producer_return_until_node_close(tmp_path, monkeypatch, return_mode):
    from aware_code_semantic_contract_runtime import (
        ContentDigest,
        SemanticConfigurationCoordinate,
        SemanticImplementationCoordinate,
    )
    from aware_code_semantic_contract_runtime import (
        semantic_input_producer as producers,
    )
    from aware_code_semantic_contract_runtime.contracts import ContractViolation
    from aware_code_semantic_contract_runtime.runtime import SemanticBody
    from test_v3_source_admission import _coordinate

    async with read_fixture(tmp_path, monkeypatch) as value:
        host = producers.SemanticInputProducerHost()
        try:
            with open_read(value) as node:
                expected = node.prepare_source_expectation(
                    use_ref="read-one", stage="pre_request", source_coordinates=value.coordinates,
                )
                assert expected.operation_identity is value.command.invocation_parent
                output = SemanticBody(_coordinate("prepared", b"prepared"), b"prepared")

                async def produce(_):
                    return output

                registration = producers.register_semantic_input_producer(
                    host, declaration=producers.SemanticInputProducerDeclaration(
                        "fixture.read-producer", "fixture.read-producer.v1",
                        SemanticImplementationCoordinate("fixture/read", ContentDigest.of_bytes(b"implementation")),
                        SemanticConfigurationCoordinate("fixture/read", ContentDigest.of_bytes(b"configuration")),
                        (producers.SemanticInputSourceContract("raw_source", value.coordinates[0].coordinate.contract),),
                        "prepared", output.coordinate.contract,
                    ), producer=produce, validator=value.issuer,
                    validator_entrance=value.issuer.validate_semantic_input_source,
                    reader=value.issuer, reader_entrance=value.issuer.read_semantic_input_sources,
                    retain_result=True,
                )
                result = await producers.execute_registered_semantic_input(
                    host, registration, source_admission=value.selected, expected=expected,
                )
                if return_mode == "copied":
                    with pytest.raises(ContractViolation):
                        node.retain_source_result(host, registration, expected=expected, result=copy.deepcopy(result))
                    with pytest.raises(RuntimeError, match="terminal"):
                        node.validate()
                else:
                    node.retain_source_result(host, registration, expected=expected, result=result)
                    value.factory.validate_selected_input_node_use(node)
                    value.issuer.validate_semantic_input_source(value.selected, expected=expected)
                    if return_mode == "replayed":
                        with pytest.raises(RuntimeError, match="replayed"):
                            node.retain_source_result(host, registration, expected=expected, result=result)
                        with pytest.raises(RuntimeError, match="terminal"):
                            node.validate()
            with pytest.raises((SourceObservationUnavailable, BaseExceptionGroup)):
                value.issuer.validate_semantic_input_source(value.selected, expected=expected)
            with pytest.raises(RuntimeError, match="terminal"):
                node.validate()
            # Borrowed Code host is still live; its owner, not node.close, closes it.
            assert not host._closed
        finally:
            host.close()


async def test_second_active_read_refuses_without_revoking_first(tmp_path, monkeypatch):
    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            with pytest.raises(RuntimeError, match="active"), open_read(value):
                pass
            node.validate()
        with open_read(value) as successor:
            successor.validate()


@pytest.mark.parametrize("action", (copy.copy, copy.deepcopy, pickle.dumps))
async def test_nonportable_node(tmp_path, monkeypatch, action):
    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            with pytest.raises(TypeError):
                action(node)
            node.validate()


async def test_changed_source_refuses_and_cannot_resume_after_restoration(tmp_path, monkeypatch):
    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            node.prepare_source_expectation(use_ref="read", stage="pre_request", source_coordinates=value.coordinates)
            path = value.root / "workspaces/network/modules/main/package/a.bin"
            original = path.read_bytes()
            path.write_bytes(b"changed")
            with pytest.raises((SourceObservationUnavailable, BaseExceptionGroup)):
                node.validate()
            path.write_bytes(original)
            with pytest.raises(RuntimeError, match="terminal"):
                node.validate()


async def test_complete_invocation_remains_closed_without_code_attachment(tmp_path, monkeypatch):
    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            with pytest.raises(RuntimeError, match="invocation_binding_unavailable"):
                value.factory.validate_selected_input_node_use(node, closure=object())
            with pytest.raises(RuntimeError, match="terminal"):
                node.validate()


async def test_locked_check_does_not_call_source_or_catalog(tmp_path, monkeypatch):
    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            def forbidden(*args, **kwargs):
                pytest.fail("full owner work under parent exclusion")

            monkeypatch.setattr(composition, "_validate_selected_input_read_record", forbidden)
            with value.command.sources.exclusion.mutation():
                value.factory.check_selected_input_node_use_locked(node)


async def test_locked_rejection_is_terminal_before_restoration(tmp_path, monkeypatch):
    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            original = value.factory._epoch
            value.factory._epoch = object()
            with value.command.sources.exclusion.mutation(), pytest.raises(RuntimeError, match="origin changed"):
                value.factory.check_selected_input_node_use_locked(node)
            value.factory._epoch = original
            with pytest.raises(RuntimeError, match="terminal"):
                node.validate()
            with pytest.raises(RuntimeError, match="active"), open_read(value):
                pass  # Terminal custody still occupies the command until disposal.


async def test_locked_check_rejects_a_moved_catalog_pair(tmp_path, monkeypatch):
    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            monkeypatch.setattr(value.command.catalog_host._command_parent.records,
                                "_read_current", lambda *_, **__: SimpleNamespace(preparation=object()))
            with value.command.sources.exclusion.mutation(), pytest.raises(RuntimeError, match="catalog pair changed"):
                value.factory.check_selected_input_node_use_locked(node)
            with pytest.raises(RuntimeError, match="terminal"):
                node.validate()


async def test_host_retirement_releases_local_sources_before_parent(tmp_path, monkeypatch):
    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            expected = node.prepare_source_expectation(use_ref="retire", stage="pre_request", source_coordinates=value.coordinates)
            composition._retire_selected_input_reads_for_host(value.host)
            with pytest.raises(RuntimeError, match="terminal"):
                node.validate()
            with pytest.raises(SourceObservationUnavailable):
                value.issuer.validate_semantic_input_source(value.selected, expected=expected)
            value.command.sources.exclusion.check_live()


async def test_known_restamped_node_is_terminal(tmp_path, monkeypatch):
    class Restamped:
        __slots__ = ("__weakref__",)

        def __hash__(self):
            raise AssertionError("foreign hash")

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            node.__class__ = Restamped
            with pytest.raises(TypeError, match="original"):
                composition._CommandOwnedSelectedInputReadSession.validate(node)
            node.__class__ = composition._CommandOwnedSelectedInputReadSession
            with pytest.raises(RuntimeError, match="terminal"):
                node.validate()


async def test_unknown_hostile_node_leaves_original_live(tmp_path, monkeypatch):
    class Foreign:
        def __getattribute__(self, name):
            pytest.fail("foreign attribute")

        def __hash__(self):
            raise AssertionError("foreign hash")

        def __eq__(self, other):
            pytest.fail("foreign equality")

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            with pytest.raises(RuntimeError, match="unknown"):
                value.factory.validate_selected_input_node_use(Foreign())
            node.validate()


async def test_host_lookup_never_hashes_foreign_input(tmp_path, monkeypatch):
    class Foreign:
        def __hash__(self):
            raise AssertionError("foreign host hash")

        def __eq__(self, other):
            raise AssertionError("foreign host equality")

    async with read_fixture(tmp_path, monkeypatch) as value:
        with pytest.raises(RuntimeError, match="original selected read host"), composition._command_owned_selected_input_read_session(
            value.command, host=Foreign(), selected_source=value.selected,
            registration=value.registration,
        ):
            pass
        with open_read(value) as node:
            node.validate()


async def test_retention_limit_refuses_without_allocating_source_bodies(tmp_path, monkeypatch):
    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            monkeypatch.setattr(composition, "_selected_input_retained_bytes", lambda _: 32 * 1024 * 1024 + 1)
            with pytest.raises(RuntimeError, match="retention budget"):
                node.prepare_source_expectation(use_ref="limit", stage="pre_request", source_coordinates=value.coordinates)
            with pytest.raises(RuntimeError, match="terminal"):
                node.validate()
        assert not value.issuer._pre_request_inputs


async def test_original_selected_source_chain_uses_owned_parent_expectations(tmp_path, monkeypatch):
    from aware_code_semantic_contract_runtime import (
        ContentDigest,
        SemanticConfigurationCoordinate,
        SemanticImplementationCoordinate,
    )
    from aware_code_semantic_contract_runtime import (
        semantic_input_producer as producers,
    )
    from aware_code_semantic_contract_runtime.source_selection import (
        SOURCE_SELECTION_REF,
        SemanticSelectedSource,
        SemanticSourceSelection,
        source_selection_body,
    )

    async with read_fixture(tmp_path, monkeypatch) as value:
        host = producers.SemanticInputProducerHost()
        try:
            with open_read(value) as node:
                expected = node.prepare_source_expectation(
                    use_ref="select-raw", stage="pre_request", source_coordinates=value.coordinates,
                )
                package, _ = value.issuer.inspect_inputs(value.selected)
                inner = value.coordinates[0].coordinate.contract
                selection = SemanticSourceSelection(
                    package.package, package.source_identity_digest, expected.input_digest, (),
                    tuple(SemanticSelectedSource("selected_raw", inner, source.relative_path, source.coordinate.digest)
                          for source in value.coordinates if source.relative_path in {"a.bin", "b.bin"}),
                )

                async def produce(_):
                    return source_selection_body(selection, role="selection")

                registration = producers.register_semantic_input_producer(
                    host, declaration=producers.SemanticInputProducerDeclaration(
                        "fixture.read-selection", "fixture.read-selection.v1",
                        SemanticImplementationCoordinate("fixture/selection", ContentDigest.of_bytes(b"code")),
                        SemanticConfigurationCoordinate("fixture/selection", ContentDigest.of_bytes(b"config")),
                        (producers.SemanticInputSourceContract("raw_source", inner),),
                        "selection", SOURCE_SELECTION_REF,
                    ), producer=produce, validator=value.issuer,
                    validator_entrance=value.issuer.validate_semantic_input_source,
                    reader=value.issuer, reader_entrance=value.issuer.read_semantic_input_sources,
                    retain_result=True,
                )
                result = await producers.execute_registered_semantic_input(
                    host, registration, source_admission=value.selected, expected=expected,
                )
                node.retain_source_result(host, registration, expected=expected, result=result)
                selected = node.prepare_selected_source_expectation(
                    host, registration, selection_expected=expected, result=result,
                    use_ref="selected-child", stage="selected_input",
                    source_contracts=(producers.SemanticInputSourceContract("selected_raw", inner),),
                )
                assert selected.operation_identity is expected.operation_identity is value.command.invocation_parent
                assert {source.relative_path for source in selected.source_coordinates} == {"a.bin", "b.bin"}
                from aware_code_semantic_contract_runtime.runtime import SemanticBody
                from test_v3_source_admission import _coordinate

                selected_body = SemanticBody(_coordinate("prepared", b"prepared"), b"prepared")

                async def prepare(_):
                    return selected_body

                selected_registration = producers.register_semantic_input_producer(
                    host, declaration=producers.SemanticInputProducerDeclaration(
                        "fixture.read-preparation", "fixture.read-preparation.v1",
                        SemanticImplementationCoordinate("fixture/preparation", ContentDigest.of_bytes(b"code")),
                        SemanticConfigurationCoordinate("fixture/preparation", ContentDigest.of_bytes(b"config")),
                        (producers.SemanticInputSourceContract("selected_raw", inner),),
                        "prepared", selected_body.coordinate.contract,
                    ), producer=prepare, validator=value.issuer,
                    validator_entrance=value.issuer.validate_semantic_input_source,
                    reader=value.issuer, reader_entrance=value.issuer.read_semantic_input_sources,
                    retain_result=True,
                )
                selected_result = await producers.execute_registered_semantic_input(
                    host, selected_registration, source_admission=value.selected, expected=selected,
                )
                node.retain_source_result(host, selected_registration, expected=selected, result=selected_result)
                assembly = node.assemble_inputs(
                    _Host(), (selected_result,), source_input_roles=(("prepared", 1),),
                )
                assert len(assembly.source_results) == 2
                assert assembly.source_results[0].result is result
                assert assembly.source_results[1].expected is selected
                value.factory.validate_selected_input_node_use(node, assembly=assembly, closure=make_closure(assembly))
                node.validate()
            assert not value.issuer._pre_request_inputs
            assert not host._closed
        finally:
            host.close()


async def test_foreign_selection_predecessor_refuses_before_reader(tmp_path, monkeypatch):
    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            with pytest.raises(RuntimeError, match="original node predecessor"):
                node.prepare_selected_source_expectation(
                    object(), object(), selection_expected=object(), result=object(),
                    use_ref="foreign", stage="selected_input", source_contracts=(),
                )
            assert not value.issuer._pre_request_inputs


async def test_held_rejection_clears_registered_custody(tmp_path, monkeypatch):
    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            record = composition._selected_input_read_record(node)
            with pytest.raises(RuntimeError, match="invocation_binding_unavailable") as caught:
                value.factory.validate_selected_input_node_use(node, closure=object())
            assert caught.value is not None
            assert record.command is record.factory is record.stack is None
            assert record.expectations == record.results == ()
            assert not any(item is record for _, item in composition._SELECTED_INPUT_NODES)


def test_held_unknown_error_does_not_retain_unrelated_records():
    nodes = [object.__new__(composition._CommandOwnedSelectedInputReadSession) for _ in range(2)]
    records = [composition._SelectedInputReadRecord(
        None, None, None, None, None, None, None, None, threading.current_thread(), ExitStack(),
    ) for _ in nodes]
    weak_nodes = [ref(node) for node in nodes]
    for node, record in zip(nodes, records):
        composition._SELECTED_INPUT_NODES.append((ref(node), record))
    try:
        with pytest.raises(RuntimeError, match="unknown") as caught:
            composition._selected_input_read_record(object())
        del nodes, node, record
        gc.collect()
        assert all(item() is None for item in weak_nodes)
        assert caught.value is not None
    finally:
        composition._SELECTED_INPUT_NODES[:] = [
            (key, item) for key, item in composition._SELECTED_INPUT_NODES
            if not any(item is record for record in records)
        ]


@pytest.mark.skipif(not hasattr(os, "fork"), reason="fork unavailable")
def test_fork_refuses_before_inherited_registry_lock():
    held, release = threading.Event(), threading.Event()
    node = object.__new__(composition._CommandOwnedSelectedInputReadSession)
    cleanup_calls = []
    stack = ExitStack()
    stack.callback(lambda: cleanup_calls.append("owned cleanup"))
    record = composition._SelectedInputReadRecord(
        object(), None, None, None, None, None, None, None, threading.current_thread(), stack,
    )
    composition._SELECTED_INPUT_NODES.append((ref(node), record))

    def holder():
        with composition._SELECTED_INPUT_NODES_LOCK:
            held.set()
            release.wait(5)

    thread = threading.Thread(target=holder)
    thread.start()
    assert held.wait(2)
    child = os.fork()
    if child == 0:
        signal.alarm(2)
        try:
            composition._selected_input_read_record(node)
        except RuntimeError:
            os._exit(0 if record.live and not cleanup_calls else 1)
        os._exit(1)
    try:
        _, status = os.waitpid(child, 0)
        assert os.waitstatus_to_exitcode(status) == 0
    finally:
        release.set()
        thread.join(5)
        assert record.live and not cleanup_calls
        composition._SELECTED_INPUT_NODES[:] = [
            (key, item) for key, item in composition._SELECTED_INPUT_NODES if item is not record
        ]
        stack.close()


@pytest.mark.parametrize("failure", (RuntimeError, asyncio.CancelledError))
async def test_failed_body_releases_source_context(tmp_path, monkeypatch, failure):
    async with read_fixture(tmp_path, monkeypatch) as value:
        with pytest.raises(failure), open_read(value) as node:
            expected = node.prepare_source_expectation(use_ref="body", stage="pre_request", source_coordinates=value.coordinates)
            raise failure("owner failed")
        with pytest.raises((SourceObservationUnavailable, BaseExceptionGroup)):
            value.issuer.validate_semantic_input_source(value.selected, expected=expected)
        with open_read(value) as next_node:
            next_node.validate()


@asynccontextmanager
async def assembly_fixture(tmp_path, monkeypatch):
    from aware_code_semantic_contract_runtime import (
        ContentDigest,
        SemanticConfigurationCoordinate,
        SemanticImplementationCoordinate,
    )
    from aware_code_semantic_contract_runtime import (
        semantic_input_producer as producers,
    )
    from aware_code_semantic_contract_runtime.runtime import SemanticBody
    from test_v3_source_admission import _coordinate

    async with read_fixture(tmp_path, monkeypatch) as value:
        host = producers.SemanticInputProducerHost()
        try:
            with open_read(value) as node:
                expected = node.prepare_source_expectation(
                    use_ref="assembled-read", stage="pre_request", source_coordinates=value.coordinates,
                )
                body = SemanticBody(_coordinate("prepared", b"prepared"), b"prepared")

                async def produce(_):
                    return body

                registration = producers.register_semantic_input_producer(
                    host, declaration=producers.SemanticInputProducerDeclaration(
                        "fixture.assembly", "fixture.assembly.v1",
                        SemanticImplementationCoordinate("fixture/assembly", ContentDigest.of_bytes(b"implementation")),
                        SemanticConfigurationCoordinate("fixture/assembly", ContentDigest.of_bytes(b"configuration")),
                        (producers.SemanticInputSourceContract("raw_source", value.coordinates[0].coordinate.contract),),
                        "prepared", body.coordinate.contract,
                    ), producer=produce, validator=value.issuer,
                    validator_entrance=value.issuer.validate_semantic_input_source,
                    reader=value.issuer, reader_entrance=value.issuer.read_semantic_input_sources,
                    retain_result=True,
                )
                result = await producers.execute_registered_semantic_input(
                    host, registration, source_admission=value.selected, expected=expected,
                )
                node.retain_source_result(host, registration, expected=expected, result=result)
                yield value, node, host, registration, expected, result
        finally:
            host.close()


def make_assembly(node, body, *, semantic_input=None):
    return node.assemble_inputs(
        _Host() if semantic_input is None else semantic_input,
        (body,), source_input_roles=((body.coordinate.role, 0),),
    )


def make_closure(assembly):
    from aware_code_semantic_contract_runtime import (
        ContentDigest,
        SemanticContractInvocation,
        SemanticPackageCoordinate,
        TypedEmptyCoordinate,
    )
    from aware_code_semantic_contract_runtime.selected_provider import (
        SelectedProviderInvocationClosure,
    )

    return SelectedProviderInvocationClosure(
        SemanticContractInvocation(
            "fixture-read", "fixture-idempotency", "fixture-read-profile",
            ContentDigest.of_bytes(b"profile"),
            SemanticPackageCoordinate("fixture-package", "ontology", ContentDigest.of_bytes(b"package")),
            "inspect", tuple(body.coordinate for body in assembly.input_bodies),
            TypedEmptyCoordinate(assembly.input_bodies[0].coordinate.contract), (), (), (),
        ),
        assembly.input_bodies,
    )


async def test_original_source_assembly_joins_exact_closure_and_fresh_reads(tmp_path, monkeypatch):
    async with assembly_fixture(tmp_path, monkeypatch) as (value, node, host, registration, expected, body):
        assembly = make_assembly(node, body)
        source = assembly.source_results[0]
        assert source.host is host and source.registration is registration
        assert source.source_admission is value.selected and source.expected is expected and source.result is body
        assert expected.operation_identity is value.command.invocation_parent
        closure = make_closure(assembly)
        value.factory.validate_selected_input_node_use(node, assembly=assembly, closure=closure)
        value.factory.validate_selected_input_node_use(node, assembly=assembly, closure=closure)
        with value.command.sources.exclusion.mutation():
            value.factory.check_selected_input_node_use_locked(node)
        assert not host._closed


@pytest.mark.parametrize("poison", ("copy-assembly", "input-tuple", "source-result", "source-admission", "copy-closure"))
async def test_equal_assembly_and_nested_substitutions_are_terminal(tmp_path, monkeypatch, poison):
    from aware_code_semantic_contract_runtime.selected_input_verification import (
        SelectedInputSourceResult,
    )

    async with assembly_fixture(tmp_path, monkeypatch) as (value, node, host, registration, expected, body):
        assembly = make_assembly(node, body)
        closure = make_closure(assembly)
        value.factory.validate_selected_input_node_use(node, assembly=assembly, closure=closure)
        if poison == "copy-assembly":
            supplied = replace(assembly)
        else:
            supplied = assembly
            if poison == "input-tuple":
                object.__setattr__(assembly, "input_bodies", tuple(item for item in assembly.input_bodies))
            elif poison == "source-result":
                object.__setattr__(assembly, "source_results", (
                    SelectedInputSourceResult(host, registration, value.selected, expected, body),
                ))
            elif poison == "source-admission":
                object.__setattr__(assembly.source_results[0], "source_admission", object())
            else:
                closure = replace(closure)
        with pytest.raises(RuntimeError, match="assembly|association|closure"):
            value.factory.validate_selected_input_node_use(node, assembly=supplied, closure=closure)
        with pytest.raises(RuntimeError, match="terminal"):
            node.validate()
        assert not host._closed


async def test_locked_assembly_check_uses_no_owner_reads(tmp_path, monkeypatch):
    async with assembly_fixture(tmp_path, monkeypatch) as (value, node, _, _, _, body):
        assembly = make_assembly(node, body)
        closure = make_closure(assembly)
        value.factory.validate_selected_input_node_use(node, assembly=assembly, closure=closure)

        def forbidden(*args, **kwargs):
            pytest.fail("owner work under parent guard")

        monkeypatch.setattr(composition, "_validate_selected_input_read_record", forbidden)
        with value.command.sources.exclusion.mutation():
            value.factory.check_selected_input_node_use_locked(node)
            object.__setattr__(assembly, "semantic_input", object())
            with pytest.raises(RuntimeError, match="field changed"):
                value.factory.check_selected_input_node_use_locked(node)
        with pytest.raises(RuntimeError, match="terminal"):
            node.validate()


async def test_assembly_currentness_failure_cannot_resume_after_source_restore(tmp_path, monkeypatch):
    async with assembly_fixture(tmp_path, monkeypatch) as (value, node, _, _, _, body):
        assembly = make_assembly(node, body)
        value.factory.validate_selected_input_node_use(node, assembly=assembly)
        path = value.root / "workspaces/network/modules/main/package/a.bin"
        original = path.read_bytes()
        path.write_bytes(b"changed")
        with pytest.raises((SourceObservationUnavailable, BaseExceptionGroup)):
            value.factory.validate_selected_input_node_use(node, assembly=assembly)
        path.write_bytes(original)
        with pytest.raises(RuntimeError, match="terminal"):
            node.validate()


async def test_checkpoint_budget_is_terminal(tmp_path, monkeypatch):
    async with assembly_fixture(tmp_path, monkeypatch) as (value, node, _, _, _, body):
        assembly = make_assembly(node, body)
        for _ in range(32):
            value.factory.validate_selected_input_node_use(node, assembly=assembly)
        with pytest.raises(RuntimeError, match="checkpoint limit"):
            value.factory.validate_selected_input_node_use(node, assembly=assembly)
        with pytest.raises(RuntimeError, match="terminal"):
            node.validate()


@pytest.mark.parametrize("action", ("second-assembly", "more-source", "incomplete"))
async def test_assembly_freeze_refuses_replay_or_incomplete_chain(tmp_path, monkeypatch, action):
    async with assembly_fixture(tmp_path, monkeypatch) as (value, node, _, _, _, body):
        if action == "incomplete":
            node.prepare_source_expectation(use_ref="unreturned", stage="pre_request", source_coordinates=value.coordinates)
        else:
            make_assembly(node, body)
        with pytest.raises(RuntimeError, match="replay|frozen|incomplete"):
            if action == "more-source":
                node.prepare_source_expectation(use_ref="late", stage="pre_request", source_coordinates=value.coordinates)
            else:
                make_assembly(node, body)
        with pytest.raises(RuntimeError, match="terminal"):
            node.validate()


async def test_foreign_products_refuse_without_foreign_behavior(tmp_path, monkeypatch):
    class Foreign:
        def __hash__(self):
            raise AssertionError("foreign hash")

        def __eq__(self, other):
            pytest.fail("foreign equality")

        def __getattribute__(self, name):
            pytest.fail("foreign attribute")

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            with pytest.raises(RuntimeError, match="original dependency admissions"):
                node.admit_dependency_products(Foreign(), Foreign(), Foreign(), body=Foreign())
            with pytest.raises(RuntimeError, match="terminal"):
                node.validate()


async def test_unissued_nominal_products_are_not_admitted(tmp_path, monkeypatch):
    from aware_workspace_runtime.dependency_fulfillment import (
        WorkspaceDependencyFulfillmentAdmission,
    )
    from aware_workspace_runtime.dependency_resolution import (
        WorkspaceDependencyResolutionAdmission,
    )

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            with pytest.raises(RuntimeError, match="issuer unavailable|admission retired"):
                node.admit_dependency_products(
                    object(), object.__new__(WorkspaceDependencyResolutionAdmission),
                    object.__new__(WorkspaceDependencyFulfillmentAdmission), body=object(),
                )
            with pytest.raises(RuntimeError, match="terminal"):
                node.validate()


async def test_failed_guard_release_defers_context_disposal(tmp_path, monkeypatch):
    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            expected = node.prepare_source_expectation(use_ref="pending", stage="pre_request", source_coordinates=value.coordinates)
            record = composition._selected_input_read_record(node)
            with value.command.sources.exclusion.mutation():
                node.close()
                assert not record.live and record.command is value.command and record.stack is not None
                assert record.expectations[0] is expected
                with pytest.raises(RuntimeError, match="terminal"):
                    node.validate()
            node.close()
            assert record.command is None and record.stack is None and not record.expectations
        assert not value.issuer._pre_request_inputs


async def test_host_disposes_code_delivery_before_owned_sources(tmp_path, monkeypatch):
    from aware_code_retained_registry_policy_runtime import product_execution

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            node.prepare_source_expectation(use_ref="teardown", stage="pre_request", source_coordinates=value.coordinates)
            record = composition._selected_input_read_record(node)
            events = []

            def retire(host, **kwargs):
                assert host is value.host and value.command.lifetime_runtime._guard is not None
                events.append("code-retire")

            def dispose(host):
                assert host is value.host and value.command.lifetime_runtime._guard is None
                assert record.stack is not None and record.expectations
                events.append("code-dispose")

            monkeypatch.setattr(product_execution, "_retire_selected_input_host", retire)
            monkeypatch.setattr(product_execution, "_dispose_retired_selected_inputs", dispose)
            composition._retire_selected_input_reads_for_host(value.host)
            assert events == ["code-retire", "code-dispose"]
            assert record.stack is None and not value.issuer._pre_request_inputs


async def test_held_assembly_rejection_does_not_pin_borrowed_input(tmp_path, monkeypatch):
    async with assembly_fixture(tmp_path, monkeypatch) as (value, node, _, _, _, body):
        semantic_input = _Host()
        weak_input = ref(semantic_input)
        assembly = make_assembly(node, body, semantic_input=semantic_input)
        object.__setattr__(assembly, "semantic_input", object())
        held = None
        try:
            value.factory.validate_selected_input_node_use(node, assembly=assembly)
        except RuntimeError as error:
            held = error
        assert held is not None
        del assembly, semantic_input
        gc.collect()
        assert weak_input() is None
        # Keep the error alive through collection; original producer is borrowed.
        assert held.__traceback__ is not None


async def test_host_guard_uncertainty_does_not_dispose_code_or_sources(tmp_path, monkeypatch):
    from aware_code_retained_registry_policy_runtime import product_execution

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            node.prepare_source_expectation(use_ref="uncertain-host", stage="pre_request", source_coordinates=value.coordinates)
            record = composition._selected_input_read_record(node)
            events = []

            def retire(host, **kwargs):
                assert host is value.host and kwargs == {"exclusion_pending": True}
                events.append("retired-pending")

            def forbidden(host):
                pytest.fail("Code disposal under uncertain guard")

            monkeypatch.setattr(product_execution, "_retire_selected_input_host", retire)
            monkeypatch.setattr(product_execution, "_dispose_retired_selected_inputs", forbidden)
            with value.command.sources.exclusion.mutation():
                with pytest.raises(RuntimeError, match="awaits original guard release"):
                    composition._retire_selected_input_reads_for_host(value.host)
                assert events == ["retired-pending"] and record.stack is not None
                assert not record.live and value.issuer._pre_request_inputs
            node.close()
            assert not value.issuer._pre_request_inputs


@pytest.mark.parametrize("phase", ("construct", "full", "locked"))
async def test_substituted_value_descriptor_never_runs(tmp_path, monkeypatch, phase):
    class ForeignDescriptor:
        def __get__(self, instance, owner=None):
            pytest.fail("foreign descriptor get")

        def __set__(self, instance, value):
            pytest.fail("foreign descriptor set")

    async with assembly_fixture(tmp_path, monkeypatch) as (value, node, _, _, _, body):
        assembly = None if phase == "construct" else make_assembly(node, body)
        with monkeypatch.context() as patch:
            patch.setattr(composition._INPUT_SOURCE_KIND, "source_admission", ForeignDescriptor())
            if phase == "construct":
                with pytest.raises(RuntimeError, match="descriptor changed"):
                    make_assembly(node, body)
            elif phase == "full":
                with pytest.raises(RuntimeError, match="descriptor changed"):
                    value.factory.validate_selected_input_node_use(node, assembly=assembly)
            else:
                with (
                    value.command.sources.exclusion.mutation(),
                    pytest.raises(RuntimeError, match="descriptor changed"),
                ):
                    value.factory.check_selected_input_node_use_locked(node)
        with pytest.raises(RuntimeError, match="terminal"):
            node.validate()


async def test_dependency_association_scan_is_bounded_before_code_contact(tmp_path, monkeypatch):
    from aware_code_retained_registry_policy_runtime import dependency_admission_origin
    from aware_workspace_runtime.dependency_fulfillment import (
        WorkspaceDependencyFulfillmentAdmission,
        _WorkspaceEmptyDependencyFulfillmentRuntime,
    )
    from aware_workspace_runtime.dependency_resolution import (
        WorkspaceDependencyResolutionAdmission,
        _WorkspaceDependencyResolutionRuntime,
    )

    def forbidden(*args, **kwargs):
        pytest.fail("Code contact before Workspace record bound")

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            resolutions = object.__new__(_WorkspaceDependencyResolutionRuntime)
            fulfillments = object.__new__(_WorkspaceEmptyDependencyFulfillmentRuntime)
            # Negative fixture only: nominal runtime shape cannot supply issuance.
            resolutions.records = {object(): None for _ in range(2_049)}
            fulfillments.records = {}
            with monkeypatch.context() as patch:
                patch.setattr(value.issuer, "_dependency_resolution", resolutions)
                patch.setattr(value.issuer, "_dependency_fulfillment", fulfillments)
                patch.setattr(dependency_admission_origin, "assemble_dependency_admission_consumer", forbidden)
                with pytest.raises(RuntimeError, match="association work bound"):
                    node.admit_dependency_products(
                        object(), object.__new__(WorkspaceDependencyResolutionAdmission),
                        object.__new__(WorkspaceDependencyFulfillmentAdmission), body=object(),
                    )
                with pytest.raises(RuntimeError, match="terminal"):
                    node.validate()


@pytest.mark.parametrize("release_mode", ("before-unlock", "after-unlock"))
@pytest.mark.parametrize("parent_expired", (False, True))
async def test_retirement_release_failure_preserves_terminal_family_until_retry(
    tmp_path, monkeypatch, release_mode, parent_expired,
):
    async with assembly_fixture(tmp_path, monkeypatch) as (value, node, host, _, expected, body):
        owner = value.command.lifetime_runtime
        semantic_input = _Host()
        weak_input = ref(semantic_input)
        finalized, disposed = [], []
        finalizer = finalize(semantic_input, lambda: finalized.append(owner._guard is not None))
        assembly = make_assembly(node, body, semantic_input=semantic_input)
        closure = make_closure(assembly)
        value.factory.validate_selected_input_node_use(node, assembly=assembly, closure=closure)
        record = composition._selected_input_read_record(node)
        stack = record.stack
        stack.callback(lambda: disposed.append(owner._guard is not None))
        original_release = type(owner).release_catalog_epoch_exclusion

        def fail_release(runtime, guard):
            if release_mode == "after-unlock":
                original_release(runtime, guard)
            raise RuntimeError("retirement release failed")

        with monkeypatch.context() as patch:
            patch.setattr(type(owner), "release_catalog_epoch_exclusion", fail_release)
            try:
                with pytest.raises(BaseExceptionGroup, match="retirement") as held:
                    node.close()
                assert not record.live
                assert record.command is value.command and record.stack is stack
                assert record.assembly_binding.assembly is assembly and record.closure is closure
                assert record.expectations[0] is expected and record.results[0][3] is body
                assert any(retained is record for _, retained in composition._SELECTED_INPUT_NODES)
                assert disposed == [] and finalized == []
                del semantic_input, assembly, closure
                gc.collect()
                assert weak_input() is not None and finalizer.alive
                assert (owner._guard is not None) == (release_mode == "before-unlock")
                with pytest.raises(RuntimeError, match="terminal"):
                    node.validate()
            finally:
                patch.undo()
                if owner._guard is not None:
                    original_release(owner, owner._guard)
        # Keep the failed close exception alive through actual deferred disposal.
        assert held.value.__traceback__ is not None
        if parent_expired:
            owner.close()
            with pytest.raises(BaseExceptionGroup) as cleanup_error:
                node.close()
            assert "command_parent_not_live" in str(cleanup_error.value.exceptions[0])
        else:
            node.close()
        node.close()
        assert disposed == [False]
        assert record.command is record.stack is record.assembly_binding is record.closure is None
        assert record.expectations == record.results == ()
        assert not any(retained is record for _, retained in composition._SELECTED_INPUT_NODES)
        assert not value.issuer._pre_request_inputs
        gc.collect()
        assert weak_input() is None and finalized == [False]
        assert not finalizer.alive and not host._closed


@asynccontextmanager
async def dependency_association_fixture(tmp_path, monkeypatch):
    """Structural/refusal fixture only; it cannot issue admitted Code products.

    Genuine nonempty admission is tested in test_original_upstream_fulfillment.
    These private rows exercise the attachment's rejection before Code dispatch.
    """
    from aware_code_semantic_contract_runtime import SemanticBody
    from aware_code_semantic_contract_runtime.dependency_admission_interfaces import (
        RetainedDependencyResolutionExpectation,
    )
    from aware_workspace_runtime.declaration_scope_admission import _SemanticRecord
    from aware_workspace_runtime.dependency_fulfillment import (
        WorkspaceDependencyFulfillmentAdmission,
        _Fulfillment,
        _WorkspaceEmptyDependencyFulfillmentRuntime,
    )
    from aware_workspace_runtime.dependency_resolution import (
        WorkspaceDependencyResolutionAdmission,
        _Resolution,
        _WorkspaceDependencyResolutionRuntime,
    )
    from test_v3_source_admission import _coordinate

    async with read_fixture(tmp_path, monkeypatch) as value:
        with open_read(value) as node:
            record = composition._selected_input_read_record(node)
            operation, inventory = object(), object()
            expected = object.__new__(RetainedDependencyResolutionExpectation)
            object.__setattr__(expected, "parent_identity", value.command.invocation_parent)
            object.__setattr__(expected, "epoch_identity", value.factory._epoch)
            source = object.__new__(_SemanticRecord)
            object.__setattr__(source, "selected", value.selected)
            resolution = object.__new__(WorkspaceDependencyResolutionAdmission)
            fulfillment = object.__new__(WorkspaceDependencyFulfillmentAdmission)
            resolutions = object.__new__(_WorkspaceDependencyResolutionRuntime)
            fulfillments = object.__new__(_WorkspaceEmptyDependencyFulfillmentRuntime)
            resolved = _Resolution(operation, inventory, expected, (), ())
            body = SemanticBody(_coordinate("products", b"products"), b"products")
            original = _Fulfillment(resolution, body, (object(),))
            resolutions.records = {resolution: resolved}
            fulfillments.records = {fulfillment: original}
            with monkeypatch.context() as patch:
                patch.setattr(value.issuer, "_dependency_resolution", resolutions)
                patch.setattr(value.issuer, "_dependency_fulfillment", fulfillments)
                patch.setattr(value.issuer, "_semantic", {inventory: source})
                yield SimpleNamespace(
                    value=value, node=node, record=record, operation=operation,
                    resolution=resolution, fulfillment=fulfillment, original=original,
                    body=body, source=source, expected=expected,
                    resolutions=resolutions, fulfillments=fulfillments,
                )


@pytest.mark.parametrize("change", (
    "terminal", "body", "heads", "resolution", "legacy-tuple", "wrong-source",
    "wrong-parent", "wrong-epoch", "wrong-operation", "missing-record", "restamp",
    "descriptor",
))
async def test_invalid_original_fulfillment_refuses_before_code_contact(tmp_path, monkeypatch, change):
    from aware_code_retained_registry_policy_runtime import dependency_admission_origin
    from aware_workspace_runtime.dependency_fulfillment import _Fulfillment

    class Hostile:
        def __getattribute__(self, name):
            pytest.fail("foreign fulfillment dispatch")

        def __eq__(self, other):
            pytest.fail("foreign fulfillment equality")

        def __get__(self, obj, owner=None):
            pytest.fail("foreign fulfillment descriptor")

    class HostileDescriptor:
        def __get__(self, obj, owner=None):
            pytest.fail("foreign fulfillment descriptor")

    def forbidden(*args, **kwargs):
        pytest.fail("Code contact before exact original record association")

    async with dependency_association_fixture(tmp_path, monkeypatch) as f:
        with monkeypatch.context() as patch:
            patch.setattr(dependency_admission_origin, "assemble_dependency_admission_consumer", forbidden)
            if change == "terminal":
                f.original.terminal = True
            elif change == "body":
                f.original.body = None
            elif change == "heads":
                f.original.heads = []
            elif change == "resolution":
                f.original.resolution = Hostile()
            elif change == "legacy-tuple":
                f.fulfillments.records[f.fulfillment] = (f.resolution, f.body)
            elif change == "wrong-source":
                object.__setattr__(f.source, "selected", Hostile())
            elif change == "wrong-parent":
                object.__setattr__(f.expected, "parent_identity", Hostile())
            elif change == "wrong-epoch":
                object.__setattr__(f.expected, "epoch_identity", Hostile())
            elif change == "wrong-operation":
                f.operation = Hostile()
            elif change == "missing-record":
                del f.fulfillments.records[f.fulfillment]
            elif change == "restamp":
                f.original.__class__ = Hostile
            elif change == "descriptor":
                patch.setattr(_Fulfillment, "body", HostileDescriptor(), raising=False)
            with pytest.raises(RuntimeError, match="admission retired|association differs"):
                f.node.admit_dependency_products(
                    f.operation, f.resolution, f.fulfillment, body=f.body,
                )
            if change == "restamp":
                object.__setattr__(f.original, "__class__", _Fulfillment)
        with pytest.raises(RuntimeError, match="terminal"):
            f.node.validate()
        assert f.record.dependency_binding is None


@pytest.mark.parametrize("change", ("terminal", "body", "heads", "family", "resolution"))
async def test_changed_retained_fulfillment_is_terminal_before_assembly(tmp_path, monkeypatch, change):
    async with dependency_association_fixture(tmp_path, monkeypatch) as f:
        originals = composition._selected_input_dependency_records(
            f.record, f.operation, f.resolution, f.fulfillment,
        )
        binding = composition._SelectedInputDependencyBinding(
            None, None, f.operation, f.resolution, f.fulfillment, originals,
        )
        f.record.dependency_binding = binding
        f.node.validate()
        original_fields = dict(f.original.__dict__)
        if change == "terminal":
            f.original.terminal = True
        elif change == "body":
            f.original.body = replace(f.body)
        elif change == "heads":
            f.original.heads = tuple(list(f.original.heads))  # noqa: C414 - intentional equal copy
        elif change == "family":
            f.fulfillments.records[f.fulfillment] = replace(f.original)
        elif change == "resolution":
            f.original.resolution = object()
        with pytest.raises(RuntimeError, match="admission retired|association differs|records changed"):
            f.node.validate()
        f.original.__dict__.clear()
        f.original.__dict__.update(original_fields)
        f.fulfillments.records[f.fulfillment] = f.original
        with pytest.raises(RuntimeError, match="terminal"):
            f.node.validate()
        assert f.record.dependency_binding is None
        assert not f.original.terminal and f.original.body is f.body
