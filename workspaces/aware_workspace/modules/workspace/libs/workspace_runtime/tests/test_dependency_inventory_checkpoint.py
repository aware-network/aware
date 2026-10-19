"""Actual Code product demand -> original Workspace inventory/resolution.

Factory intake is source-grade fixture admission. No store authority, public
command, semantic-owner export or fabricated staged operation is supplied.
"""

from contextlib import ExitStack, asynccontextmanager, contextmanager
from dataclasses import dataclass

import pytest
from aware_code_retained_registry_policy_runtime import (
    product_planning_source as planning,
)
from aware_code_retained_registry_policy_runtime.retained_demand_operation import (
    execute_retained_dependency_demand,
)
from aware_code_retained_registry_policy_runtime.selected_root_intent import (
    derive_selected_root_intent,
)
from aware_code_semantic_contract_runtime import (
    CodeSemanticPackagePlanningContext,
    ContentDigest,
    ContractViolation,
    SemanticValueCoordinate,
)
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputProducerHost,
    SemanticInputSourceCoordinate,
)

# isort: split

from aware_workspace_materialize_transport import WorkspaceMaterializeCommandProposalV3
from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime import direct_cli_selected_host as local
from aware_workspace_runtime import direct_command_composition as composition

# isort: split

from test_dependency_scope_admission import fixture as sources
from test_direct_cli_dependency_planning import ROOT_KEY, SUPPLIER_KEY, _repository
from test_direct_cli_dependency_planning import owners as original_owners

owners = original_owners


from aware_code_semantic_contract_runtime import semantic_input_producer as code
from aware_code_semantic_contract_runtime.contracts import (
    SemanticConfigurationCoordinate,
    SemanticImplementationCoordinate,
)
from aware_code_semantic_contract_runtime.source_selection import (
    SOURCE_SELECTION_REF,
    SemanticSelectedSource,
    SemanticSourceSelection,
    source_selection_body,
)
from aware_workspace_runtime import dependency_resolution as resolver_module


@asynccontextmanager
async def selected_product_demand(tmp_path, monkeypatch, owners, *, nonempty=False):
    admitted, calls = owners
    calls.clear()
    monkeypatch.setattr(local, "admit_installed_semantic_stage_factory", lambda key: admitted[key][0])
    profiles = {key: profile for key, (_, profile) in admitted.items()}
    async with sources(tmp_path, lambda root: _repository(root, profiles)) as (root, _, _, borrowed, _, _):
        proposal = WorkspaceMaterializeCommandProposalV3.create(
            attempt_ref="proof:product-resolution", participant_checkout_root=str(root),
            workspace_manifest_name="consumer/aware.workspace.toml",
            package_address=("Consumer", "main", "consumer" if nonempty else "supplier"), plan_only=True,
        )
        with composition._compose_direct_workspace_command_source(
            session=borrowed._session, store=borrowed._store, proposal=proposal,
        ) as (command, _, selected), local.compose_direct_cli_selected_product(command, selected) as product:
            issuer, host = command.sources.declaration_scope_runtime, product.host.code_host
            contribution = product.participants[0].contribution
            declared = planning.read_product_planning_input_declaration(host, product.policy, contribution)
            evidence = issuer.inspect_selected_package_evidence(selected)
            role, = declared.source_contracts
            coordinates = tuple(SemanticInputSourceCoordinate(
                body.relative_path, SemanticValueCoordinate(role.role, role.contract, body.body_ref, ContentDigest(body.content_digest), body.size_bytes),
            ) for body in evidence.bodies)
            with ExitStack() as retained:
                input_host = SemanticInputProducerHost()
                retained.callback(input_host.close)
                selection_expected = retained.enter_context(issuer.original_pre_request_input(
                    selected, use_ref="proof:product-resolution-source", stage="source_planning",
                    source_coordinates=coordinates, context_contracts=declared.context_contracts,
                ))
                context_value = issuer.inspect_inputs(selected)[0]
                selection = SemanticSourceSelection(
                    context_value.package, context_value.source_identity_digest,
                    selection_expected.input_digest, (), tuple(
                        SemanticSelectedSource(row.coordinate.role, row.coordinate.contract,
                            row.relative_path, row.coordinate.digest) for row in coordinates),
                )
                selection_registration = code.register_semantic_input_producer(
                    input_host, declaration=code.SemanticInputProducerDeclaration(
                        "fixture.source-selection", "fixture.source-selection.v1",
                        SemanticImplementationCoordinate("fixture/selection", ContentDigest.of_bytes(b"selection")),
                        SemanticConfigurationCoordinate("fixture.selection", ContentDigest.of_bytes(b"selection-config")),
                        declared.source_contracts, "selection", SOURCE_SELECTION_REF,
                        context_contracts=declared.context_contracts,
                    ), producer=lambda value: source_selection_body(selection, role="selection"),
                    validator=issuer, validator_entrance=issuer.validate_semantic_input_source,
                    reader=issuer, reader_entrance=issuer.read_semantic_input_sources,
                    context_validator_entrance=issuer.validate_semantic_input_context,
                    retain_result=True,
                    validation_scope_entrance=code.capture_semantic_input_validation_scope(issuer),
                )
                selection_result = await code.execute_registered_semantic_input(
                    input_host, selection_registration, source_admission=selected, expected=selection_expected,
                )
                expected_input = retained.enter_context(issuer.original_selected_source_input(
                    selected, host=input_host, registration=selection_registration,
                    selection_expected=selection_expected, result=selection_result,
                    source_contracts=declared.source_contracts,
                    use_ref="proof:selected-product-resolution-source", stage="source_planning",
                    context_contracts=declared.context_contracts,
                ))
                try:
                    registration = planning.register_product_planning_input_producer(host, product.policy, contribution, input_host=input_host)
                    source = await planning.execute_product_planning_input(host, product.policy, contribution, input_host=input_host, registration=registration, expected=expected_input)
                    entry = product.host.catalog_pair.workspace.package(product.package_ref)
                    intent, result = derive_selected_root_intent(host, product.policy)
                    context = CodeSemanticPackagePlanningContext.create(
                        package=entry.package, package_family=entry.package_family, package_role=entry.package_role,
                        manifest_contract=entry.manifest_contract, code_intent=intent,
                        required_semantic_provider_keys=(ROOT_KEY if nonempty else SUPPLIER_KEY,), required_result_products=(result,),
                    )
                    operation = await execute_retained_dependency_demand(source, context=context)
                    # This is the same original validator retained by fixed composition.
                    validator = issuer._dependency_validator[0]
                    expected = validator.expectation(operation)
                    yield root, command, issuer, selected, host, source, operation, expected, calls
                finally:
                    planning.close_product_planning_sources(host)


async def test_original_selected_source_resolves_with_existing_code_checkpoint(tmp_path, monkeypatch, owners):
    async with selected_product_demand(tmp_path, monkeypatch, owners) as (_, _, issuer, _, _, _, operation, expected, _):
        inventory = issuer.issue_product_dependency_inventory(operation, expected=expected)
        with issuer._dependency_inventory_checkpoint(operation, inventory, expected):
            assert code._result_validation_state() is not None
        resolution = issuer.issue_dependency_resolution(operation, inventory_admission=inventory, expected=expected)
        issuer.validate_dependency_resolution_admission(resolution, expected=expected)
        assert resolution in issuer._dependency_resolution.records
        assert code._result_validation_state() is None


# The following controls isolate resolver custody/factory mechanics. Their
# fixture admissions do not establish original Workspace or Code authority.
@pytest.fixture
def mechanics(monkeypatch):
    from types import SimpleNamespace

    from aware_code_semantic_contract_runtime.materialization_catalog import (
        _issue_code_semantic_contract_catalog,
        _revoke_code_semantic_contract_catalog,
    )
    from test_materialization_catalog import _binding, _catalog, _execution_closure
    catalog = _catalog(_binding())
    providers, planners = _execution_closure(catalog)
    admitted = _issue_code_semantic_contract_catalog(catalog=catalog,
        provider_executable_bindings=providers, dependency_planner_bindings=planners,
        host_liveness=lambda: True)
    operation, inventory = object(), object()
    @dataclass(frozen=True)
    class Expected:
        planning_input: object
        demand_set: object
    expected = Expected(SimpleNamespace(dependencies=()), SimpleNamespace(demands=()))
    class Issuer:
        def __init__(self):
            self._contexts = {inventory: object()}
        active = False
        failure = None
        def _dependency_inventory_checkpoint(self, operation, inventory, expected):
            @contextmanager
            def scope():
                self.active = True
                try:
                    yield
                    if self.failure:
                        raise self.failure
                finally:
                    self.active = False
            return scope()
    class Targets:
        def issue(self, *args, **kwargs):
            raise AssertionError('empty fixture cannot issue a target')
        read = issue_source = read_source = issue
    issuer = Issuer()
    runtime = resolver_module._WorkspaceDependencyResolutionRuntime(issuer, Targets(), admitted)
    monkeypatch.setattr(runtime, '_inventory', lambda *a: (SimpleNamespace(targets=()), ()))
    try:
        yield runtime, issuer, operation, inventory, expected
    finally:
        runtime.close()
        _revoke_code_semantic_contract_catalog(admitted)


@pytest.mark.parametrize('target', ['factory', 'checker', 'opener', 'record'])
@pytest.mark.parametrize('mode', ['return', 'raise', 'restore'])
def test_registered_resolution_substitution_is_terminal_without_calls(mechanics, monkeypatch, target, mode):
    runtime, issuer, operation, inventory, expected = mechanics
    resolution = runtime.issue(operation, inventory, expected)
    calls = []
    name = {'factory': '_dependency_inventory_checkpoint', 'checker': '_check_checkpoint_factory', 'opener': '_inventory_checkpoint'}.get(target)
    receiver = issuer if target == 'factory' else runtime
    original = getattr(receiver, name) if name else runtime._checkpoint_factory
    def hostile(*args, **kwargs):
        calls.append(True)
        if mode == 'restore':
            delattr(receiver, name)
        if mode == 'raise':
            raise RuntimeError('foreign scope factory')
    if target == 'record':
        runtime._checkpoint_factory = tuple(value for value in runtime._checkpoint_factory)
    else:
        monkeypatch.setattr(receiver, name, hostile)
    try:
        with pytest.raises((SourceObservationUnavailable, ContractViolation)):
            runtime.validate(resolution, expected)
    finally:
        if target == 'record':
            runtime._checkpoint_factory = original
        else:
            delattr(receiver, name)
    assert calls == []
    assert resolution not in runtime.records
    with pytest.raises((SourceObservationUnavailable, ContractViolation)):
        runtime.validate(resolution, expected)
    with pytest.raises((SourceObservationUnavailable, ContractViolation)):
        runtime.issue(operation, inventory, expected)
    assert not issuer.active


@pytest.mark.parametrize('interruption', [False, True])
def test_failed_terminal_issue_never_exposes_handle_or_loses_replay_tombstone(mechanics, interruption):
    runtime, issuer, operation, inventory, expected = mechanics
    issuer.failure = KeyboardInterrupt('terminal') if interruption else RuntimeError('terminal')
    with pytest.raises((RuntimeError, KeyboardInterrupt)):
        runtime.issue(operation, inventory, expected)
    assert not runtime.records
    assert any(value is operation for value in runtime.issued_operations)
    assert not issuer.active
    issuer.failure = None
    with pytest.raises(SourceObservationUnavailable):
        runtime.issue(operation, inventory, expected)


@pytest.mark.parametrize('target', ['factory', 'checker', 'opener', 'record'])
def test_first_issue_preparation_rejection_preserves_replay_tombstone(mechanics, monkeypatch, target):
    runtime, issuer, operation, inventory, expected = mechanics
    calls = []
    name = {'factory': '_dependency_inventory_checkpoint', 'checker': '_check_checkpoint_factory', 'opener': '_inventory_checkpoint'}.get(target)
    receiver = issuer if target == 'factory' else runtime
    original = runtime._checkpoint_factory
    def hostile(*args, **kwargs):
        calls.append(True)
        raise AssertionError('substituted preparation called')
    if target == 'record':
        runtime._checkpoint_factory = tuple(value for value in original)
    else:
        monkeypatch.setattr(receiver, name, hostile)
    try:
        with pytest.raises((SourceObservationUnavailable, ContractViolation)):
            runtime.issue(operation, inventory, expected)
    finally:
        if target == 'record':
            runtime._checkpoint_factory = original
        else:
            delattr(receiver, name)
    assert not calls and not issuer.active and not runtime.records
    assert any(value is operation for value in runtime.issued_operations)
    with pytest.raises(SourceObservationUnavailable):
        runtime.issue(operation, inventory, expected)
    unrelated = runtime.issue(object(), inventory, expected)
    runtime.validate(unrelated, expected)


def test_failed_terminal_validation_preserves_unrelated_and_unknown_rejection(mechanics):
    runtime, issuer, operation, inventory, expected = mechanics
    first = runtime.issue(operation, inventory, expected)
    other = runtime.issue(object(), inventory, expected)
    with pytest.raises(ContractViolation):
        runtime.validate(object(), expected)
    assert set(runtime.records) == {first, other}
    issuer.failure = RuntimeError('terminal')
    with pytest.raises(RuntimeError):
        runtime.validate(first, expected)
    issuer.failure = None
    assert first not in runtime.records and other in runtime.records
    runtime.validate(other, expected)


@pytest.fixture
def coordinate_runtime(mechanics):
    """Real admitted Code catalog; fixture-only Source inventory, no body delivery."""
    from types import SimpleNamespace
    runtime, issuer, operation, inventory, _ = mechanics
    del runtime._inventory
    coordinate = runtime.resolver.read_catalog_coordinate()
    @dataclass(frozen=True)
    class Expected:
        planning_input: object
        demand_set: object
        catalog_match_admission: object
    context = SimpleNamespace(package="fixture-package", source_identity_digest="fixture-source")
    record = SimpleNamespace(source=SimpleNamespace(context=context),
                             inventory=SimpleNamespace(entries=()), targets=())
    expected = Expected(SimpleNamespace(package=context.package,
        source_identity_digest=context.source_identity_digest, dependencies=()),
        SimpleNamespace(demands=()), SimpleNamespace(catalog_ref=coordinate[0],
            catalog_generation=coordinate[1], catalog_root_digest=coordinate[2]))
    issuer._validate_dependency_inventory = lambda *args, **kwargs: record
    yield runtime, issuer, operation, inventory, expected


@pytest.mark.parametrize("target", ["instance", "class", "resolver", "admission"])
@pytest.mark.parametrize("stage", ["issue", "validate"])
@pytest.mark.parametrize("late", [False, True])
def test_original_catalog_reader_binding_rejects_before_foreign_dispatch(coordinate_runtime, monkeypatch, target, stage, late):
    from types import SimpleNamespace
    runtime, issuer, operation, inventory, expected = coordinate_runtime
    resolution = None if stage == "issue" else runtime.issue(operation, inventory, expected)
    resolver = runtime.resolver
    kind = type(resolver)
    original = kind.read_catalog_coordinate
    admission = resolver._admission
    calls = []
    def hostile(*args, **kwargs):
        calls.append(True)
        raise AssertionError("foreign catalog reader dispatched")
    def poison():
        if target == "instance":
            resolver.read_catalog_coordinate = hostile
        elif target == "class":
            monkeypatch.setattr(kind, "read_catalog_coordinate", hostile)
        elif target == "resolver":
            runtime.resolver = SimpleNamespace(read_catalog_coordinate=hostile)
        else:
            resolver._admission = object()
    inventory_reader = issuer._validate_dependency_inventory
    if late:
        def read(*args, **kwargs):
            value = inventory_reader(*args, **kwargs)
            poison()
            return value
        issuer._validate_dependency_inventory = read
    else:
        poison()
    try:
        with pytest.raises(ContractViolation):
            if stage == "issue":
                runtime.issue(operation, inventory, expected)
            else:
                runtime.validate(resolution, expected)
    finally:
        runtime.resolver = resolver
        resolver._admission = admission
        kind.read_catalog_coordinate = original
        resolver.__dict__.pop("read_catalog_coordinate", None)
        issuer._validate_dependency_inventory = inventory_reader
    assert calls == []
    if resolution is not None:
        assert resolution not in runtime.records
        with pytest.raises((SourceObservationUnavailable, ContractViolation)):
            runtime.validate(resolution, expected)
    with pytest.raises(SourceObservationUnavailable):
        runtime.issue(operation, inventory, expected)
    unrelated = runtime.issue(object(), inventory, expected)
    runtime.validate(unrelated, expected)
