"""Pure metadata composition retains Code and terminal source boundaries."""

import inspect
import sys
from contextlib import ExitStack, asynccontextmanager, nullcontext
from pathlib import Path

import pytest
from aware_code_retained_registry_policy_runtime.dependency_admission_origin import (
    assemble_dependency_admission_consumer,
)
from aware_code_semantic_contract_runtime import ContentDigest, ContractViolation
from test_product_dependency_inventory import owners as original_owners
from test_product_dependency_inventory import product_demand

# isort: split

from aware_workspace_runtime import SourceObservationUnavailable

owners = original_owners

from aware_code_retained_registry_policy_runtime import direct_host
from aware_workspace_runtime import direct_cli_product_execution as execution
from aware_workspace_runtime import direct_cli_selected_host as local
from aware_workspace_runtime import direct_command_composition as composition
from test_direct_cli_product_execution import authored
from test_direct_cli_product_execution import factory as _factory
from test_direct_cli_selected_host import _proposal, sources

factory = _factory


async def test_code_demand_validation_stays_outside_metadata_window(tmp_path, monkeypatch, owners):
    async with product_demand(tmp_path, monkeypatch, owners) as (_, _, issuer, _, _, _, operation, expected, _):
        inventory = issuer.issue_product_dependency_inventory(operation, expected=expected)
        validator = issuer._dependency_validator[1].__code__
        product = vars(type(issuer))["_validate_product_dependency_inventory"].__code__
        metadata = vars(type(issuer))["_semantic_values"].__code__
        calls, metadata_states = [], []
        previous = sys.getprofile()

        def observe(frame, event, value):
            if event == "call" and frame.f_code is validator and frame.f_back.f_code is product:
                calls.append(issuer._semantic_source_window is None)
            if event == "call" and frame.f_code is metadata and frame.f_back.f_code is product:
                metadata_states.append(issuer._semantic_source_window is not None)

        sys.setprofile(observe)
        try:
            issuer._validate_dependency_inventory(operation, inventory, expected=expected)
        finally:
            sys.setprofile(previous)
        assert len(calls) == 6 and all(calls)
        assert metadata_states == [True, True]
        assert issuer._semantic_source_window is None


@pytest.mark.parametrize("change", ["source_bytes", "closing_record"])
async def test_late_metadata_change_preserves_original_failure_boundary(tmp_path, monkeypatch, owners, change):
    fired = []
    cleanup = pytest.raises(ContractViolation, match="direct host unavailable") if change == "source_bytes" else nullcontext()
    with cleanup:
        async with product_demand(tmp_path, monkeypatch, owners) as (root, _, issuer, _, host, _, operation, expected, _):
            inventory = issuer.issue_product_dependency_inventory(operation, expected=expected)
            resolution, fulfillment, body = issuer.issue_empty_dependency_products(operation, inventory_admission=inventory, expected=expected)
            admitted = assemble_dependency_admission_consumer(host).admit_dependency_products(operation, resolution, fulfillment, body=body)
            record = issuer._semantic[inventory]
            path = root / "consumer/modules/main/supplier/source.aware"
            original_bytes = path.read_bytes()
            original_digest = record.context.source_identity_digest
            product = vars(type(issuer))["_validate_product_dependency_inventory"].__code__
            metadata = vars(type(issuer))["_semantic_values"].__code__
            closing = vars(type(issuer))["_read_source_projection_pair"].__code__
            previous = sys.getprofile()

            def mutate(frame, event, value):
                if fired or event != "return":
                    return
                if change == "source_bytes" and frame.f_code is metadata and frame.f_back.f_code is product:
                    fired.append(change)
                    path.write_bytes(b"changed during original metadata reconstruction")
                elif change == "closing_record" and frame.f_code is closing and frame.f_locals.get("closing") is not None:
                    fired.append(change)
                    object.__setattr__(record.context, "source_identity_digest", ContentDigest.of_bytes(b"late semantic record"))

            sys.setprofile(mutate)
            try:
                with pytest.raises((ContractViolation, SourceObservationUnavailable)):
                    admitted.read_products()
            finally:
                sys.setprofile(previous)
                path.write_bytes(original_bytes)
                object.__setattr__(record.context, "source_identity_digest", original_digest)
            assert fired == [change]
            assert issuer._semantic_source_window is None
            if change == "source_bytes":
                with pytest.raises((ContractViolation, SourceObservationUnavailable)):
                    admitted.read_products()
            else:
                # Baseline control also permits restoration of this private
                # metadata record. Preserve fresh verification and exact body;
                # this performance cut does not introduce a new lifecycle law.
                assert admitted.read_products().canonical_body == body.canonical_body
    assert fired == [change]


_PREPARATION_HOLDERS = []


@pytest.fixture(autouse=True)
def release_preparation_fixture_graph_bookkeeping():
    yield
    from aware_workspace_runtime import direct_cli_product_publication as publication

    owned = tuple(_PREPARATION_HOLDERS)
    publication._SCOPES[:] = [(holder, state) for holder, state in publication._SCOPES
                             if not any(holder is original for original in owned)]
    _PREPARATION_HOLDERS.clear()


def _original_preparation_scope():
    from contextlib import contextmanager
    from types import CellType, FunctionType

    from aware_workspace_runtime.direct_cli_product_publication import (
        validate_direct_cli_graph_scope,
    )

    template = dict(zip(validate_direct_cli_graph_scope.__code__.co_freevars,
                        (cell.cell_contents for cell in validate_direct_cli_graph_scope.__closure__), strict=True))["dependency_template"]
    code, namespace, name, defaults, keywords, cells = template
    function = FunctionType(code, namespace, name, defaults,
                            None if cells is None else tuple(CellType(value) for value in cells))
    function.__kwdefaults__ = None if keywords is None else dict(keywords)
    return contextmanager(function)


def _enter_original_preparation(holder, state, operation):
    command = state.command
    original = (command, state.source, state.planned, state.active_binding, state.prepared,
                state.product, command.sources.declaration_scope_runtime,
                command.sources.declaration_scope, state.planned.demands)
    return _original_preparation_scope()(holder, state, operation, original)


def _original_preparation_state(issuer, inventory, operation):
    import os
    from threading import get_ident
    from types import SimpleNamespace

    from aware_code_retained_registry_policy_runtime import (
        retained_demand_operation as operations,
    )
    from aware_code_semantic_contract_runtime import canonical_json_bytes

    # isort: split

    from aware_workspace_runtime import direct_cli_product_publication as publication
    from aware_workspace_runtime.direct_cli_product_demands import (
        DirectCLIProductDemands,
    )

    selected = issuer._semantic[inventory].selected
    declaration = issuer._selected_record(selected).declaration
    record = operations._OPERATIONS[operation]
    demands = DirectCLIProductDemands(((record.context.package, record.source),))
    demand = operation.read_demand()
    demands._rows[record.context.package.package_ref] = (
        operation, record.context_bytes, canonical_json_bytes(demand.to_wire()),
    )
    binding = SimpleNamespace(package=record.context.package, planning_context=record.context,
                              dependency_demand_set=demand)
    state = publication._Scope(SimpleNamespace(sources=SimpleNamespace(
        declaration_scope_runtime=issuer, declaration_scope=declaration,
    )), selected, None, SimpleNamespace(demands=demands), None, os.getpid(), get_ident(), active_binding=binding)
    holder = object.__new__(publication._DirectCLIProductGraphScope)
    publication._SCOPES.append((holder, state))
    _PREPARATION_HOLDERS.append(holder)
    return holder, state


async def test_existing_sessions_preserve_original_calls_and_terminal_freshness(tmp_path, monkeypatch, owners):
    from aware_code_retained_registry_policy_runtime import (
        retained_demand_operation as demands,
    )

    # isort: split

    from aware_workspace_runtime.source_observation import (
        WorkspaceSourceObservationRuntime,
    )

    async with product_demand(tmp_path, monkeypatch, owners) as (_, _, issuer, _, _, _, operation, expected, _):
        inventory = issuer.issue_product_dependency_inventory(operation, expected=expected)
        holder, state = _original_preparation_state(issuer, inventory, operation)
        validator = issuer._dependency_validator[1].__code__
        source = WorkspaceSourceObservationRuntime.revalidate_declarations.__code__
        calls, reads = [], []
        previous = sys.getprofile()

        def observe(frame, event, arg):
            if event == "call" and frame.f_code is validator:
                calls.append(bool(demands._ACTIVE_VALIDATIONS.get()))
            if event == "call" and frame.f_code is source:
                reads.append(True)

        try:
            sys.setprofile(observe)
            with _enter_original_preparation(holder, state, operation):
                resolution = issuer.issue_dependency_resolution(operation, inventory_admission=inventory, expected=expected)
                fulfillment = issuer.issue_dependency_fulfillment(resolution, expected=expected)
                body = issuer.read_dependency_products(fulfillment, resolution_admission=resolution, expected=expected)
        finally:
            sys.setprofile(previous)
        assert len(calls) == 312 and all(calls)
        assert len(reads) == 12
        assert body.canonical_body and not state.terminal
        assert issuer._semantic_source_window is None
        assert not demands._ACTIVE_VALIDATIONS.get()
        assert issuer.read_dependency_products(fulfillment, resolution_admission=resolution, expected=expected) == body


@pytest.mark.parametrize("target", ["source", "interrupt"])
async def test_existing_sessions_refuse_changes_and_release_windows(tmp_path, monkeypatch, owners, target):
    from aware_code_retained_registry_policy_runtime import (
        retained_demand_operation as demands,
    )

    cleanup = pytest.raises(ContractViolation, match="direct host unavailable") if target == "source" else nullcontext()
    with cleanup:
        async with product_demand(tmp_path, monkeypatch, owners) as (root, _, issuer, _, _, _, operation, expected, _):
            inventory = issuer.issue_product_dependency_inventory(operation, expected=expected)
            holder, state = _original_preparation_state(issuer, inventory, operation)
            path = root / "consumer/modules/main/supplier/source.aware"
            before = path.read_bytes()
            try:
                with pytest.raises((ContractViolation, SourceObservationUnavailable, KeyboardInterrupt)), _enter_original_preparation(holder, state, operation):
                    resolution = issuer.issue_dependency_resolution(operation, inventory_admission=inventory, expected=expected)
                    fulfillment = issuer.issue_dependency_fulfillment(resolution, expected=expected)
                    issuer.read_dependency_products(fulfillment, resolution_admission=resolution, expected=expected)
                    if target == "interrupt":
                        raise KeyboardInterrupt("during original dependency preparation")
                    path.write_bytes(before + b"\nlate mutation")
            finally:
                path.write_bytes(before)
            assert state.terminal
            assert issuer._semantic_source_window is None
            assert not demands._ACTIVE_VALIDATIONS.get()
            if target == "source":
                with pytest.raises((ContractViolation, SourceObservationUnavailable)):
                    issuer.read_dependency_products(fulfillment, resolution_admission=resolution, expected=expected)


@pytest.mark.parametrize("binding", ["code", "source"])
@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
async def test_existing_session_origins_reject_before_substitute_dispatch(tmp_path, monkeypatch, owners, binding, mode):
    from aware_code_retained_registry_policy_runtime import (
        retained_demand_operation as demands,
    )

    cleanup = nullcontext()
    with cleanup:
      async with product_demand(tmp_path, monkeypatch, owners) as (_, _, issuer, _, _, _, operation, expected, _):
        inventory = issuer.issue_product_dependency_inventory(operation, expected=expected)
        holder, state = _original_preparation_state(issuer, inventory, operation)
        owner, name = (demands, "dependency_resolution_validation_session") if binding == "code" else (type(issuer), "selected_source_validation_scope")
        original = getattr(owner, name)
        calls = []

        def hostile(*args, **kwargs):
            calls.append(True)
            if mode == "restore":
                setattr(owner, name, original)
                return original(*args, **kwargs)
            if mode == "raise":
                raise AssertionError("substituted validation scope executed")
            return iter(())

        with monkeypatch.context() as patch:
            patch.setattr(owner, name, hostile)
            with pytest.raises((ContractViolation, TypeError)), _enter_original_preparation(holder, state, operation):
                raise AssertionError("substitution must reject before body")
        assert not calls and state.terminal
        assert issuer._semantic_source_window is None
        assert not demands._ACTIVE_VALIDATIONS.get()
        with pytest.raises(ContractViolation, match="terminal"), _enter_original_preparation(holder, state, operation):
            raise AssertionError("terminal original family resumed")


@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
async def test_existing_session_factory_cell_is_original(tmp_path, monkeypatch, owners, mode):
    from aware_code_retained_registry_policy_runtime import (
        retained_demand_operation as demands,
    )

    async with product_demand(tmp_path, monkeypatch, owners) as (_, _, issuer, _, _, _, operation, expected, _):
        inventory = issuer.issue_product_dependency_inventory(operation, expected=expected)
        holder, state = _original_preparation_state(issuer, inventory, operation)
        factory = demands.dependency_resolution_validation_session
        (cell,) = factory.__closure__
        original = cell.cell_contents
        calls = []

        def hostile(*args, **kwargs):
            calls.append(True)
            if mode == "restore":
                cell.cell_contents = original
                return original(*args, **kwargs)
            if mode == "raise":
                raise AssertionError("substituted Code factory closure executed")
            return iter(())

        try:
            cell.cell_contents = hostile
            with pytest.raises(ContractViolation, match="entrance changed"), _enter_original_preparation(holder, state, operation):
                raise AssertionError("factory substitution accepted")
        finally:
            cell.cell_contents = original
        assert not calls and state.terminal
        with pytest.raises(ContractViolation, match="terminal"), _enter_original_preparation(holder, state, operation):
            raise AssertionError("terminal family resumed")


@pytest.mark.parametrize("stage", ["before_entry", "before_exit"])
async def test_existing_session_keeps_original_graph_holder_live(tmp_path, monkeypatch, owners, stage):
    async with product_demand(tmp_path, monkeypatch, owners) as (_, _, issuer, _, _, _, operation, expected, _):
        inventory = issuer.issue_product_dependency_inventory(operation, expected=expected)
        holder, state = _original_preparation_state(issuer, inventory, operation)
        manager = _enter_original_preparation(holder, state, operation)
        if stage == "before_entry":
            state.terminal = True
        with pytest.raises(ContractViolation, match="terminal"), manager:
            state.terminal = True
        assert state.terminal and issuer._semantic_source_window is None


@pytest.mark.parametrize("target", ["source", "binding", "prepared"])
async def test_existing_session_snapshot_precedes_manager_entry(tmp_path, monkeypatch, owners, target):
    async with product_demand(tmp_path, monkeypatch, owners) as (_, _, issuer, _, _, _, operation, expected, _):
        inventory = issuer.issue_product_dependency_inventory(operation, expected=expected)
        holder, state = _original_preparation_state(issuer, inventory, operation)
        manager = _enter_original_preparation(holder, state, operation)
        name = "active_binding" if target == "binding" else target
        original = getattr(state, name)
        setattr(state, name, object())
        with pytest.raises(ContractViolation, match="association changed"), manager:
            raise AssertionError("restamped graph snapshot accepted")
        setattr(state, name, original)
        assert state.terminal
        with pytest.raises(ContractViolation, match="terminal"), _enter_original_preparation(holder, state, operation):
            raise AssertionError("restored graph resumed")


@pytest.mark.parametrize("target", ["factory_cell", "source_code"])
@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
async def test_existing_sessions_freeze_dispatch_before_guard_return(tmp_path, monkeypatch, owners, target, mode):
    from aware_code_retained_registry_policy_runtime import (
        retained_demand_operation as demands,
    )

    cleanup = pytest.raises(ContractViolation, match="direct host unavailable") if target == "source_code" else nullcontext()
    with cleanup:
      async with product_demand(tmp_path, monkeypatch, owners) as (_, _, issuer, _, _, _, operation, expected, _):
        inventory = issuer.issue_product_dependency_inventory(operation, expected=expected)
        holder, state = _original_preparation_state(issuer, inventory, operation)
        factory_cell, = demands.dependency_resolution_validation_session.__closure__
        source = type(issuer).selected_source_validation_scope
        original_cell, original_code = factory_cell.cell_contents, source.__code__
        calls, fired = [], []

        def hostile(*args, **kwargs):
            calls.append(True)
            if mode == "restore":
                factory_cell.cell_contents = original_cell
                return original_cell(*args, **kwargs)
            if mode == "raise":
                raise AssertionError("late session factory executed")
            return iter(())

        # Match the native source's sole closure cell without calling it.
        def make_code(value):
            def changed(self, declaration, selected):
                value.append(True)
                if False:
                    yield None
            return changed.__code__

        poisoned_code = make_code(calls)
        assert len(poisoned_code.co_freevars) == len(source.__closure__)

        def at_guard_return(frame, event, arg):
            if not fired and event == "return" and frame.f_code.co_name == "association" and frame.f_back.f_code.co_name == "dependency_scope":
                fired.append(True)
                if target == "factory_cell":
                    factory_cell.cell_contents = hostile
                else:
                    source.__code__ = poisoned_code

        previous = sys.getprofile()
        try:
            sys.setprofile(at_guard_return)
            with pytest.raises((ContractViolation, SourceObservationUnavailable)), _enter_original_preparation(holder, state, operation):
                raise AssertionError("late substitution reached body")
        finally:
            sys.setprofile(previous)
            factory_cell.cell_contents = original_cell
            source.__code__ = original_code
        assert fired and not calls and state.terminal
        assert issuer._semantic_source_window is None


@asynccontextmanager
async def original_product(tmp_path, factory, monkeypatch):
    monkeypatch.setattr(local, "admit_installed_semantic_stage_factory", lambda key: factory)
    async with sources(tmp_path, authored) as (root, _, _, borrowed, _, _):
        with composition._compose_direct_workspace_command_source(
            session=borrowed._session, store=borrowed._store, proposal=_proposal(root),
        ) as (command, _, source):
            stack = ExitStack()
            product = stack.enter_context(local.compose_direct_cli_selected_product(command, source))
            try:
                yield root, command, source, product
            finally:
                try:
                    stack.__exit__(*sys.exc_info())
                except ContractViolation as error:
                    # The original composer performs a success-only policy
                    # reread on normal exit. A deliberately revoked host must
                    # refuse it; its original finally cleanup still runs.
                    if (str(error) != "foreign or closed host"
                        or composition._selected_input_identity_lookup(direct_host._HOSTS, product.host.code_host) is not None):
                        raise


def target(command, name):
    if name == "scope":
        return type(command.sources.declaration_scope_runtime), "selected_source_validation_scope"
    if name == "dispatch":
        return composition, "_original_group_method"
    if name == "command":
        return composition, "_require_live_direct_workspace_command"
    if name == "owner_policy":
        return direct_host, "validate_admitted_registry_policy"
    return execution, name


@pytest.mark.parametrize("name", ["scope", "dispatch", "command", "owner_policy", "_read_original_policy", "_read_original_contribution", "validate_direct_cli_selected_host"])
@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
async def test_participant_group_preentry_alias_refuses_zero_calls_and_restoration(
    tmp_path, factory, monkeypatch, name, mode,
):
    calls = []
    async with original_product(tmp_path, factory, monkeypatch) as (_, command, source, product):
        owner, attribute = target(command, name)
        original = inspect.getattr_static(owner, attribute)

        def hostile(*args, **kwargs):
            calls.append(True)
            if mode == "restore":
                setattr(owner, attribute, original)
            if mode == "raise":
                raise AssertionError("substituted participant entrance ran")

        monkeypatch.setattr(owner, attribute, hostile)
        with pytest.raises((ContractViolation, RuntimeError, BaseExceptionGroup)):
            execution._execution_participant(command, source, product)
        assert calls == []
        monkeypatch.setattr(owner, attribute, original)
        with pytest.raises((ContractViolation, RuntimeError)):
            execution._execution_participant(command, source, product)


@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
async def test_participant_group_late_alias_refuses_zero_calls(
    tmp_path, factory, monkeypatch, mode,
):
    calls = []
    async with original_product(tmp_path, factory, monkeypatch) as (_, command, source, product):
        original = execution._read_original_policy
        fired = False

        def hostile(*args, **kwargs):
            calls.append(True)
            if mode == "restore":
                execution._read_original_policy = original
            if mode == "raise":
                raise AssertionError("late substituted policy reader ran")

        def trace(frame, event, arg):
            nonlocal fired
            if (not fired and event == "line"
                and frame.f_code is execution._execution_participant.__code__
                and "granted = original_policy" in lines[frame.f_lineno - 1]):
                fired = True
                monkeypatch.setattr(execution, "_read_original_policy", hostile)
            return trace

        lines = Path(execution.__file__).read_text().splitlines()
        previous = sys.gettrace()
        try:
            sys.settrace(trace)
            with pytest.raises((ContractViolation, RuntimeError, BaseExceptionGroup)):
                execution._execution_participant(command, source, product)
        finally:
            sys.settrace(previous)
            monkeypatch.setattr(execution, "_read_original_policy", original)
        assert fired and calls == []
        with pytest.raises((ContractViolation, RuntimeError)):
            execution._execution_participant(command, source, product)


@pytest.mark.parametrize("what", ["declaration", "source", "journal", "interrupt"])
async def test_participant_group_terminal_change_rejects_and_cannot_resume(
    tmp_path, factory, monkeypatch, what,
):
    async with original_product(tmp_path, factory, monkeypatch) as (root, command, source, product):
        fired = False
        if what == "declaration":
            path = root / "consumer/aware.workspace.toml"
        else:
            path = root / "consumer/modules/main/attention/aware.attention.toml"
        before = path.read_bytes()
        issuer = command.sources.declaration_scope_runtime
        record = issuer._declarations[command.sources.declaration_scope]
        digest = record.digest
        lines = Path(execution.__file__).read_text().splitlines()

        def trace(frame, event, arg):
            nonlocal fired
            if (not fired and event == "line"
                and frame.f_code is execution._execution_participant.__code__
                and "granted = original_policy" in lines[frame.f_lineno - 1]):
                fired = True
                if what == "interrupt":
                    raise KeyboardInterrupt("participant grouping interrupted")
                if what == "journal":
                    object.__setattr__(record, "digest", type(digest).of_bytes(b"changed original journal"))
                else:
                    path.write_bytes(before + b"\n# changed during original closed reader\n")
            return trace

        previous = sys.gettrace()
        try:
            sys.settrace(trace)
            with pytest.raises((ValueError, RuntimeError, KeyboardInterrupt, BaseExceptionGroup)):
                execution._execution_participant(command, source, product)
        finally:
            sys.settrace(previous)
            path.write_bytes(before)
            if what == "journal":
                object.__setattr__(record, "digest", digest)
        assert fired and issuer._semantic_source_window is None
        with pytest.raises((ContractViolation, RuntimeError)):
            execution._execution_participant(command, source, product)


async def test_participant_group_foreign_rejection_preserves_original_family(tmp_path, factory, monkeypatch):
    async with original_product(tmp_path, factory, monkeypatch) as (_, command, source, product):
        with pytest.raises(TypeError):
            execution._execution_participant(object(), source, product)
        with pytest.raises(TypeError):
            execution._execution_participant(command, source, object())
        participants, member, registration = execution._execution_participant(command, source, product)
        assert participants is product.participants and member[0] is source
        assert registration.registration is not None


@pytest.mark.parametrize("name", ["scope", "dispatch", "_read_original_policy"])
@pytest.mark.parametrize("phase", ["before", "late"])
@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
async def test_participant_group_original_code_restamp_never_executes(
    tmp_path, factory, monkeypatch, name, phase, mode,
):
    calls = []
    async with original_product(tmp_path, factory, monkeypatch) as (_, command, source, product):
        owner, attribute = target(command, name)
        function = inspect.getattr_static(owner, attribute)
        original = function.__code__
        free_names = ["cell_" + str(i) for i in range(len(original.co_freevars))]
        setup = "".join("    " + value + " = None\n" for value in free_names)
        use = "        unused = (" + ",".join(free_names) + ("," if free_names else "") + ")\n"
        effect = "        _PARTICIPANT_POISON_CALLS.append(True)\n"
        if mode == "restore":
            effect += "        _PARTICIPANT_POISON_RESTORE()\n"
        elif mode == "raise":
            effect += "        raise AssertionError('restamped code executed')\n"
        effect += "        yield None\n" if original.co_flags & inspect.CO_GENERATOR else "        return None\n"
        sandbox = {}
        exec("def outer():\n" + setup + "    def poison(*args, **kwargs):\n" + use + effect + "    return poison\n", sandbox)  # noqa: S102 - fixed local closure-arity poison, no external input
        poison_code = sandbox["outer"]().__code__
        monkeypatch.setitem(function.__globals__, "_PARTICIPANT_POISON_CALLS", calls)
        monkeypatch.setitem(function.__globals__, "_PARTICIPANT_POISON_RESTORE", lambda: setattr(function, "__code__", original))
        lines = Path(execution.__file__).read_text().splitlines()
        fired = False

        def trace(frame, event, arg):
            nonlocal fired
            marker = "granted = original_policy" if name == "_read_original_policy" else "with manager:"
            if (not fired and event == "line"
                and frame.f_code is execution._execution_participant.__code__
                and marker in lines[frame.f_lineno - 1]):
                fired = True
                function.__code__ = poison_code
            return trace

        previous = sys.gettrace()
        try:
            if phase == "before":
                fired = True
                function.__code__ = poison_code
            else:
                sys.settrace(trace)
            with pytest.raises((ContractViolation, RuntimeError, ValueError, BaseExceptionGroup)):
                execution._execution_participant(command, source, product)
        finally:
            sys.settrace(previous)
            function.__code__ = original
        assert fired and calls == []
        with pytest.raises((ContractViolation, RuntimeError)):
            execution._execution_participant(command, source, product)


async def test_source_window_binding_uses_original_commitment_without_rehash(tmp_path, monkeypatch, owners):
    from aware_code_semantic_contract_runtime.retained_declaration_scope import (
        CodeSelectedPackageSourceBinding,
    )

    async with product_demand(tmp_path, monkeypatch, owners) as (_, _, issuer, _, _, _, operation, expected, _):
        inventory = issuer.issue_product_dependency_inventory(operation, expected=expected)
        selected = issuer._semantic[inventory].selected
        declaration = issuer._selected_record(selected).declaration
        digest_code = CodeSelectedPackageSourceBinding.binding_digest.fget.__code__
        calls = []
        previous = sys.getprofile()
        with issuer._original_participant_source_window(declaration, selected):
            binding = issuer._semantic_source_window.binding
            def count(frame, event, value):
                if event == "call" and frame.f_code is digest_code:
                    calls.append(True)
            try:
                sys.setprofile(count)
                for _ in range(3):
                    detached = issuer.read_selected_package_source(selected)
                    assert detached == binding and detached is not binding
                    assert detached.expectation is not binding.expectation
            finally:
                sys.setprofile(previous)
        assert not calls and issuer._semantic_source_window is None


@pytest.mark.parametrize("when", ["before", "after_copy", "transient_copy"])
async def test_source_window_binding_rejects_coherent_original_mutation(tmp_path, monkeypatch, owners, when):
    from aware_code_semantic_contract_runtime import (
        retained_declaration_scope_validation as values,
    )

    copier_code = values.copy_selected_source_binding.__code__

    async with product_demand(tmp_path, monkeypatch, owners) as (_, _, issuer, _, _, _, operation, expected, _):
        inventory = issuer.issue_product_dependency_inventory(operation, expected=expected)
        selected = issuer._semantic[inventory].selected
        record = issuer._selected_record(selected)
        declaration = record.declaration
        digest = record.digest
        saved = binding = None
        fired = []
        previous = sys.getprofile()
        try:
            with (
                pytest.raises((ContractViolation, SourceObservationUnavailable)),
                issuer._original_participant_source_window(declaration, selected),
            ):
                binding = issuer._semantic_source_window.binding
                candidate = binding.candidates.candidates[-1]
                saved = candidate.content_digest
                def change():
                    fired.append(True)
                    object.__setattr__(candidate, "content_digest", ContentDigest.of_bytes(b"coherent replacement"))
                    object.__setattr__(record, "digest", binding.binding_digest)
                copy_frames = []
                def late(frame, event, value):
                    if frame.f_code is not copier_code:
                        return
                    if event == "call" and frame.f_locals.get("value") is binding:
                        copy_frames.append(id(frame))
                        if when == "transient_copy":
                            change()
                    elif event == "return" and id(frame) in copy_frames:
                        if not fired:
                            change()
                        elif when == "transient_copy":
                            object.__setattr__(candidate, "content_digest", saved)
                            object.__setattr__(record, "digest", digest)
                if when == "before":
                    change()
                else:
                    sys.setprofile(late)
                issuer.read_selected_package_source(selected)
        finally:
            sys.setprofile(previous)
            if saved is not None:
                object.__setattr__(binding.candidates.candidates[-1], "content_digest", saved)
            object.__setattr__(record, "digest", digest)
        assert fired == [True] and issuer._semantic_source_window is None
        method = vars(type(issuer))["read_selected_package_source"]
        private = dict(zip(method.__code__.co_freevars,
                           (cell.cell_contents for cell in method.__closure__), strict=True))
        assert not private["source_window_bindings"]


async def test_source_window_binding_commitment_releases_on_interruption(tmp_path, monkeypatch, owners):
    async with product_demand(tmp_path, monkeypatch, owners) as (_, _, issuer, _, _, _, operation, expected, _):
        inventory = issuer.issue_product_dependency_inventory(operation, expected=expected)
        selected = issuer._semantic[inventory].selected
        declaration = issuer._selected_record(selected).declaration
        with (
            pytest.raises(KeyboardInterrupt),
            issuer._original_participant_source_window(declaration, selected),
        ):
            issuer.read_selected_package_source(selected)
            raise KeyboardInterrupt("bounded binding-copy interruption")
        assert issuer._semantic_source_window is None
        method = vars(type(issuer))["read_selected_package_source"]
        private = dict(zip(method.__code__.co_freevars,
                           (cell.cell_contents for cell in method.__closure__), strict=True))
        assert not private["source_window_bindings"]
        assert issuer.read_selected_package_source(selected).expectation.package_id


@pytest.mark.parametrize("kind", ["participant", "semantic"])
async def test_source_window_binding_setup_interruption_releases_commitment(tmp_path, monkeypatch, owners, kind):
    async with product_demand(tmp_path, monkeypatch, owners) as (_, _, issuer, _, _, _, operation, expected, _):
        inventory = issuer.issue_product_dependency_inventory(operation, expected=expected)
        selected = issuer._semantic[inventory].selected
        declaration = issuer._selected_record(selected).declaration
        if kind == "participant":
            name = "_original_participant_source_window"
            arguments = (declaration, selected)
        else:
            name = "_original_semantic_source_window"
            original_input = issuer._original_product_dependency_source_input(expected.source_planning)
            arguments = (selected, original_input)
        method = vars(type(issuer))[name]
        target_code = method.__wrapped__.__code__
        lines = Path(inspect.getsourcefile(method.__wrapped__)).read_text().splitlines()
        read = vars(type(issuer))["read_selected_package_source"]
        private = dict(zip(read.__code__.co_freevars,
                           (cell.cell_contents for cell in read.__closure__), strict=True))
        registry = private["source_window_bindings"]
        fired = []
        previous = sys.gettrace()
        def interrupt(frame, event, value):
            if (not fired and event == "line" and frame.f_code is target_code
                and lines[frame.f_lineno - 1].strip() == "self._semantic_source_window = current"):
                assert len(registry) == 1
                fired.append(True)
                raise KeyboardInterrupt("after original commitment registration")
            return interrupt
        try:
            sys.settrace(interrupt)
            with pytest.raises(KeyboardInterrupt), getattr(issuer, name)(*arguments):
                pytest.fail("interrupted setup must not yield")
        finally:
            sys.settrace(previous)
        assert fired == [True] and not registry
        assert issuer._semantic_source_window is None
        assert issuer.read_selected_package_source(selected).expectation.package_id
