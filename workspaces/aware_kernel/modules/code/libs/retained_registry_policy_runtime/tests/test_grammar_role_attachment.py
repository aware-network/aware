"""Original Code factories/host checks with an explicit fixture source owner.

The parent and source issuer below are mechanics fixtures, not a production
Workspace entrance, Language result issuer or installed application admission.
"""

from __future__ import annotations

import asyncio
import copy
import os
from contextlib import contextmanager
from threading import Thread

import pytest
from aware_code_module_manifest_contract_runtime import grammar_factory as factory
from aware_code_retained_registry_policy_runtime import direct_host as direct
from aware_code_retained_registry_policy_runtime import epoch_participation as epochs
from aware_code_retained_registry_policy_runtime import grammar_role_attachment as owner
from aware_code_retained_registry_policy_runtime.declaration_eligibility import (
    calculate_declaration_eligibility,
)
from aware_code_retained_registry_policy_runtime.declaration_host import (
    _prepare_declaration_source,
)
from aware_code_retained_registry_policy_runtime.direct_epoch_tracking import (
    _bind_direct_policy_epoch,
)
from aware_code_semantic_contract_runtime import product_contribution as products
from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
    CatalogPairEpochExpectation,
    DirectInvocationExpectation,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    SemanticConfigurationCoordinate,
    SemanticImplementationCoordinate,
)
from aware_code_semantic_contract_runtime.direct_origin_interfaces import (
    DECLARATION_V3_RESOURCE_ROLES,
    DirectCommandExpectedContext,
    DirectCommandResourceBinding,
)
from aware_code_semantic_contract_runtime.grammar_profile_join import (
    read_grammar_declaration_context,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    _issue_code_semantic_contract_catalog,
)
from aware_code_semantic_contract_runtime.retained_declaration_scope import (
    CodeDeclarationScopeExpectation,
)
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputProductionExpectation,
)
from test_declaration_host import OriginalEpochDeclarationOwner
from test_grammar_profile_composition import supplied_input
from test_materialization_catalog import _catalog, _execution_closure

FACTORIES = (
    factory.construct_grammar_profile_selection_product,
    factory.construct_grammar_syntax_binding_product,
)


@pytest.fixture(scope="module")
def admissions():
    return tuple(
        selected._admit_selected_provider_factory(
            factory_ref=fn.__module__ + ":" + fn.__name__,
            provider_key=fn().binding.provider_key,
            selection_factory=fn,
        )
        for fn in FACTORIES
    )


class SourceOwner(OriginalEpochDeclarationOwner):
    def __init__(self, projection, ordinary):
        super().__init__(projection)
        self.ordinary = ordinary
        self.inputs = ()
        self.calls = []
        self.source_live = True
        self.failure = None
        self.return_override = None
        self.after_read = None

    def validate_semantic_input_source(self, source, *, expected):
        assert not self.guards, "source callback under parent exclusion"
        self.calls.append("source")
        if self.failure is not None:
            raise self.failure
        if (
            not self.source_live
            or source is not self.selected
            or not any(expected is item for item in self.inputs)
            or expected.operation_identity is not self.parent
        ):
            raise ContractViolation("original fixture source expectation required")
        return self.return_override

    def validate_semantic_input_context(self, source, *, expected):
        self.calls.append("context")
        return self.validate_semantic_input_source(source, expected=expected)

    def read_semantic_input_sources(self, source, *, expected):
        self.validate_semantic_input_source(source, expected=expected)
        self.calls.append("read")
        result = self.ordinary.sources
        if self.after_read is not None:
            self.after_read()
        return result


@contextmanager
def case(
    admissions,
    *,
    bind=True,
    include=(0, 1),
    extra_catalog_entries=(),
    ordinary_input=None,
):
    ordinary = ordinary_input
    if ordinary is None:
        ordinary, _, _, _ = supplied_input()
    _, closure = read_grammar_declaration_context(ordinary)
    source = SourceOwner(closure, ordinary)
    contributions = tuple(
        products.issue_selected_provider_product_contribution(admissions[index])
        for index in include
    )
    rows = tuple(
        products.produce_selected_provider_product_catalog_contribution(item)
        for item in contributions
    )
    actual = tuple(
        products.read_selected_provider_product_contribution(item)
        for item in contributions
    )
    source.contributions = contributions
    source.closed_contributions = set()
    catalog = _catalog(
        *(entry for row in rows for entry in row.entries), *extra_catalog_entries
    )
    extra_catalog = _catalog(*extra_catalog_entries)
    extra_executables, extra_planners = _execution_closure(extra_catalog)
    # The two read helpers advertise one planner coordinate. This mechanics
    # catalog binds the first original planner once; graph planning is never
    # invoked and genuine fixed-application planner intake remains unqualified.
    planners = {}
    for row in rows:
        entry = row.entries[0]
        planners.setdefault(
            (
                entry.dependency_planner_implementation,
                entry.dependency_planner_configuration,
            ),
            row.planner,
        )
    admitted = _issue_code_semantic_contract_catalog(
        catalog=catalog,
        provider_executable_bindings=tuple(row.executables[0] for row in rows)
        + extra_executables,
        dependency_planner_bindings=tuple(
            (*coordinate, planner) for coordinate, planner in planners.items()
        )
        + extra_planners,
        host_liveness=lambda: source.catalog_live,
    )
    resources = dict(
        catalog=admitted,
        code_runtime=actual[0].expected.runtime,
        composition_factory=source,
        lifetime_runtime=source,
        declaration_scope_runtime=source,
        policy_producer=calculate_declaration_eligibility,
    )
    digest = ContentDigest.of_bytes(b"explicit mechanics fixture, not application")
    source.expected = DirectCommandExpectedContext(
        object(),
        object(),
        os.getpid(),
        actual[0].expected.runtime,
        admitted,
        SemanticImplementationCoordinate("fixture.composition", digest),
        SemanticConfigurationCoordinate("fixture.composition", digest),
        SemanticImplementationCoordinate("fixture.policy", digest),
        SemanticConfigurationCoordinate("fixture.policy", digest),
        tuple(
            DirectCommandResourceBinding(role, resources[role], "borrowed")
            for role in DECLARATION_V3_RESOURCE_ROLES
        ),
        source_rail="declaration_v3",
        product_runtime_bindings=tuple(item.expected for item in actual),
    )
    bootstrap = direct._assemble_direct_command_bootstrap(
        lifetime=source.lifetime, expected=source.expected
    )
    host = direct.register_direct_workspace_origin(bootstrap, source.lifetime)
    source.declaration_expectation = CodeDeclarationScopeExpectation(
        closure.repository_binding_ref, "parent", os.getpid(), "operation", "epoch"
    )
    prepared = _prepare_declaration_source(
        host, source.snapshot, source.declaration_expectation
    )
    invocation = DirectInvocationExpectation(
        source.expected.invocation_identity, source.expected.epoch_identity, os.getpid()
    )
    source.epoch = CatalogPairEpochExpectation(
        invocation, object(), direct._HOSTS[host].catalog_digest, digest, digest
    )
    guard = source.acquire_catalog_epoch_exclusion(source.parent, expected=invocation)
    try:
        participant = epochs._assemble_code_epoch_participation(
            owner=source,
            parent=source.parent,
            invocation=invocation,
            epoch_owner=source,
            guard=guard,
        )
        if bind:
            _bind_direct_policy_epoch(
                host,
                participant,
                source.current,
                expected=source.epoch,
                guard=guard,
                declaration_source=prepared,
            )
    finally:
        source.release_catalog_epoch_exclusion(guard)
    source.inputs = tuple(
        SemanticInputProductionExpectation.create(
            use_ref="original." + stage,
            operation_ref=ordinary.operation_ref,
            stage=stage,
            package_identity=ordinary.package_identity,
            operation_identity=source.parent,
            source_identity=source.selected,
            source_coordinates=tuple(item.source for item in ordinary.sources),
            context_bodies=ordinary.context_bodies,
        )
        for stage in ("profile_selection", "syntax_binding")
    )
    try:
        yield source, host, participant, actual
    finally:
        direct.close_direct_validation_host(host)
        for item in reversed(contributions):
            if item not in source.closed_contributions:
                products.close_selected_provider_product_contribution(item)


def attach(source, host, **changes):
    arguments = dict(
        code_host=host,
        profile_expected=source.inputs[0],
        syntax_expected=source.inputs[1],
    )
    arguments.update(changes)
    return owner._capture_grammar_source_role_attachment(**arguments)


def test_original_host_retains_one_attachment_without_execution(admissions):
    with case(admissions) as (source, host, participant, actual):
        record = attach(source, host)
        assert direct._HOSTS[host].grammar_attachment is record
        assert record.products == tuple(
            (item.expected.runtime, item.expected.registration) for item in actual
        )
        owner._validate_grammar_source_role_attachment(host, record)
        assert len(source.calls) > 10 and not source.guards
        assert not epochs._state(participant).uses
        for item in actual:
            with pytest.raises(ContractViolation, match="source-role attachment"):
                item.executable.input_closure(object())
        with pytest.raises(ContractViolation, match="consumed"):
            attach(source, host)


@pytest.mark.parametrize("stage", (0, 1))
@pytest.mark.parametrize("bad", (None, (), {}, object()))
def test_exact_expected_shape_refuses_before_original_calls(admissions, stage, bad):
    with case(admissions) as (source, host, _, _):
        key = "profile_expected" if stage == 0 else "syntax_expected"
        with pytest.raises(TypeError):
            attach(source, host, **{key: bad})
        assert not source.calls
        assert direct._HOSTS[host].grammar_attachment is None


@pytest.mark.parametrize(
    "field",
    (
        "use_ref",
        "operation_ref",
        "stage",
        "operation_identity",
        "source_identity",
    ),
)
def test_source_pair_substitution_refuses_before_owner_calls(admissions, field):
    with case(admissions) as (source, host, _, _):
        value = source.inputs[1]
        values = dict(
            use_ref=value.use_ref,
            operation_ref=value.operation_ref,
            stage=value.stage,
            package_identity=value.package_identity,
            operation_identity=value.operation_identity,
            source_identity=value.source_identity,
            source_coordinates=value.source_coordinates,
            context_bodies=value.context_bodies,
        )
        values[field] = (
            source.inputs[0].use_ref
            if field == "use_ref"
            else (object() if field.endswith("identity") else "foreign")
        )
        changed = SemanticInputProductionExpectation.create(**values)
        with pytest.raises(ContractViolation):
            attach(source, host, syntax_expected=changed)
        assert not source.calls
        assert direct._HOSTS[host].grammar_attachment is None


@pytest.mark.parametrize("copied_stage", (0, 1))
def test_equal_copied_expected_is_not_original_source_admission(
    admissions, copied_stage
):
    with case(admissions) as (source, host, _, _):
        key = "profile_expected" if copied_stage == 0 else "syntax_expected"
        with pytest.raises(ContractViolation, match="fixture source"):
            attach(source, host, **{key: copy.copy(source.inputs[copied_stage])})
        with pytest.raises(ContractViolation, match="consumed"):
            attach(source, host)


@pytest.mark.parametrize("include", ((0,), (1,)))
def test_missing_original_product_refuses_terminally(admissions, include):
    with case(admissions, include=include) as (source, host, _, _):
        with pytest.raises(ContractViolation, match="grammar product"):
            attach(source, host)
        assert not source.calls
        with pytest.raises(ContractViolation, match="consumed"):
            attach(source, host)


def test_unbound_epoch_refuses_without_attempt(admissions):
    with case(admissions, bind=False) as (source, host, _, _):
        with pytest.raises(ContractViolation, match="epoch host"):
            attach(source, host)
        assert not source.calls
        assert direct._HOSTS[host].grammar_attachment is None


@pytest.mark.parametrize(
    "name",
    (
        "validate_semantic_input_source",
        "validate_semantic_input_context",
        "read_semantic_input_sources",
    ),
)
def test_original_issuer_method_substitution_is_terminal(admissions, name):
    with case(admissions) as (source, host, _, _):
        record = attach(source, host)
        original = getattr(source, name)
        setattr(source, name, lambda *a, **kw: None)
        with pytest.raises(ContractViolation, match="substituted"):
            owner._validate_grammar_source_role_attachment(host, record)
        setattr(source, name, original)
        with pytest.raises(ContractViolation, match="retired"):
            owner._validate_grammar_source_role_attachment(host, record)


@pytest.mark.parametrize(
    "field",
    (
        "operation_ref",
        "source_identity",
        "input_digest",
        "context_bodies",
    ),
)
def test_mutation_and_restoration_cannot_revive_attachment(admissions, field):
    with case(admissions) as (source, host, _, _):
        record = attach(source, host)
        value = source.inputs[0]
        original = getattr(value, field)
        object.__setattr__(value, field, object())
        with pytest.raises((ContractViolation, TypeError)):
            owner._validate_grammar_source_role_attachment(host, record)
        object.__setattr__(value, field, original)
        with pytest.raises(ContractViolation, match="retired"):
            owner._validate_grammar_source_role_attachment(host, record)


@pytest.mark.parametrize(
    "error",
    (
        ValueError("source"),
        KeyboardInterrupt(),
        SystemExit(7),
        asyncio.CancelledError(),
    ),
)
def test_original_failure_and_interruption_identity(admissions, error):
    with case(admissions) as (source, host, participant, _):
        record = attach(source, host)
        source.failure = error
        with pytest.raises(type(error)) as caught:
            owner._validate_grammar_source_role_attachment(host, record)
        assert caught.value is error and record.retired
        assert not epochs._state(participant).uses
        assert not source.guards


def test_non_none_original_validator_refuses(admissions):
    with case(admissions) as (source, host, _, _):
        source.return_override = object()
        with pytest.raises(ContractViolation, match="returned a value"):
            attach(source, host)


def test_source_callbacks_run_with_real_running_epoch_use(admissions):
    with case(admissions) as (source, host, participant, _):
        calls = []

        def during():
            assert not source.guards
            assert {use.status for use in epochs._state(participant).uses.values()} == {
                "running"
            }
            calls.append(True)

        source.after_read = during
        attach(source, host)
        assert len(calls) == 2


def test_parent_retirement_cannot_revive_attachment(admissions):
    with case(admissions) as (source, host, _, _):
        record = attach(source, host)
        source.live = False
        with pytest.raises(ContractViolation):
            owner._validate_grammar_source_role_attachment(host, record)
        source.live = True
        with pytest.raises(ContractViolation):
            owner._validate_grammar_source_role_attachment(host, record)


def test_foreign_record_does_not_retire_original(admissions):
    with case(admissions) as (source, host, _, _):
        record = attach(source, host)
        with pytest.raises(ContractViolation):
            owner._validate_grammar_source_role_attachment(host, copy.copy(record))
        owner._validate_grammar_source_role_attachment(host, record)


def test_other_thread_refuses_before_callbacks(admissions):
    with case(admissions) as (source, host, _, _):
        record = attach(source, host)
        before = len(source.calls)
        errors = []

        def call():
            try:
                owner._validate_grammar_source_role_attachment(host, record)
            except BaseException as error:
                errors.append(error)

        thread = Thread(target=call)
        thread.start()
        thread.join(timeout=5)
        assert not thread.is_alive()
        assert len(errors) == 1 and isinstance(errors[0], ContractViolation)
        assert len(source.calls) == before
        owner._validate_grammar_source_role_attachment(host, record)


def test_other_process_refuses_before_callbacks(admissions, monkeypatch):
    with case(admissions) as (source, host, _, _):
        record = attach(source, host)
        before = len(source.calls)
        process = os.getpid()
        with monkeypatch.context() as child:
            child.setattr(os, "getpid", lambda: process + 1)
            with pytest.raises(ContractViolation, match="process"):
                owner._validate_grammar_source_role_attachment(host, record)
        assert len(source.calls) == before
        owner._validate_grammar_source_role_attachment(host, record)


@pytest.mark.parametrize("stage", (0, 1))
def test_factory_symbol_substitution_is_terminal(admissions, monkeypatch, stage):
    with case(admissions) as (source, host, _, _):
        record = attach(source, host)
        fn = FACTORIES[stage]
        with monkeypatch.context() as changed:
            changed.setattr(factory, fn.__name__, lambda: fn())
            with pytest.raises(ContractViolation, match="factory entrance"):
                owner._validate_grammar_source_role_attachment(host, record)
        with pytest.raises(ContractViolation, match="retired"):
            owner._validate_grammar_source_role_attachment(host, record)


@pytest.mark.parametrize("size", (512, 513))
def test_operation_reference_bound_precedes_attempt_and_callbacks(admissions, size):
    with case(admissions) as (source, host, _, _):
        source.inputs = tuple(
            SemanticInputProductionExpectation.create(
                use_ref=value.use_ref,
                operation_ref="r" * size,
                stage=value.stage,
                package_identity=value.package_identity,
                operation_identity=value.operation_identity,
                source_identity=value.source_identity,
                source_coordinates=value.source_coordinates,
                context_bodies=value.context_bodies,
            )
            for value in source.inputs
        )
        if size == 512:
            attach(source, host)
        else:
            with pytest.raises(ContractViolation, match="bound"):
                attach(source, host)
            assert not source.calls
            assert direct._HOSTS[host].grammar_attachment is None


@pytest.mark.parametrize("stage", (0, 1))
def test_equal_product_from_foreign_factory_cannot_attach(admissions, stage):
    fn = FACTORIES[stage]

    def foreign_factory():
        return fn()

    # The original registry already refuses a different function under the
    # admitted provider key. Do not reset/bypass it to manufacture a fixture.
    with pytest.raises(ContractViolation, match="exact factory"):
        selected._admit_selected_provider_factory(
            factory_ref="fixture.foreign." + str(stage),
            provider_key=fn().binding.provider_key,
            selection_factory=foreign_factory,
        )


@pytest.mark.parametrize("stage", (0, 1))
def test_registration_close_remains_terminal(admissions, stage):
    with case(admissions) as (source, host, _, actual):
        record = attach(source, host)
        contribution = source.contributions[stage]
        products.close_selected_provider_product_contribution(contribution)
        source.closed_contributions.add(contribution)
        with pytest.raises(ContractViolation):
            owner._validate_grammar_source_role_attachment(host, record)
        assert record.retired


def test_late_source_retirement_during_read_refuses(admissions):
    with case(admissions) as (source, host, participant, _):

        def during():
            source.source_live = False

        source.after_read = during
        with pytest.raises(ContractViolation):
            attach(source, host)
        assert not epochs._state(participant).uses
        source.source_live = True
        with pytest.raises(ContractViolation, match="consumed"):
            attach(source, host)
