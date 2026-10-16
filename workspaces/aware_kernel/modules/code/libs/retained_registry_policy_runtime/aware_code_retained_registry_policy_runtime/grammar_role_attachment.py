"""Original-host grammar attachment checks, not productive role execution.

The fixed owner constructor will consume these private records. No detached
role host, issuer, resolver or callback can be supplied here. No registration,
result retention or cleanup capability is issued by this bounded source unit.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from threading import current_thread
from typing import cast

from aware_code_module_manifest_contract_runtime import grammar_factory as factory
from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.grammar_product_contracts import (
    grammar_operational_contracts,
    grammar_operational_profile,
)
from aware_code_semantic_contract_runtime.grammar_profile_join import (
    read_grammar_declaration_context,
)
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputProductionExpectation,
    SemanticInputProductionInput,
    SemanticInputSourceBody,
    _result_tree,
    _ResultTree,
)

from . import direct_epoch_tracking as epochs
from . import direct_host as direct
from . import epoch_participation as participation
from .declaration_host import _validate_declaration_source
from .product_runtime_retention import _ProductRuntimeRetention

_PENDING = object()
_FACTORIES = (
    (
        "profile_selection",
        "construct_grammar_profile_selection_product",
        factory.construct_grammar_profile_selection_product,
        factory.GrammarProfileSelectionProvider,
    ),
    (
        "syntax_binding",
        "construct_grammar_syntax_binding_product",
        factory.construct_grammar_syntax_binding_product,
        factory.GrammarSyntaxBindingProvider,
    ),
)


@dataclass(eq=False, slots=True)
class _GrammarSourceRoleAttachment:
    host: direct.DirectValidationHost
    state: direct._State
    binding: epochs._Binding
    retention: _ProductRuntimeRetention
    expectations: tuple[SemanticInputProductionExpectation, ...]
    snapshots: tuple[_ResultTree, ...]
    methods: tuple[direct._Entrance, ...]
    products: tuple[tuple[object, object], ...]
    process: int
    thread: object
    retired: bool = False
    # Original async obligations outlive execution revocation. Only the fixed
    # role owner reserves these two uses; this is not a second epoch tracker.
    epoch_work: dict[str, object] = field(default_factory=dict)
    # Cleanup-only custody stays on this original record after revocation.
    cleanup_custody: object = None
    # The fixed profile-role owner retains its owned host/registration/result
    # here. Borrowed products and source/lifetime owners remain untouched.
    profile_resources: object = None
    # Original staged syntax registration/join; no contribution authority.
    syntax_resources: object = None
    # Optional public composition view, issued only after both original roles.
    public_view: object = None


def _check_expectations(profile_expected, syntax_expected) -> None:
    for value, stage in (
        (profile_expected, "profile_selection"),
        (syntax_expected, "syntax_binding"),
    ):
        if type(value) is not SemanticInputProductionExpectation:
            raise TypeError("exact grammar source expectation required")
        # Bound correlation before journal reservation or original owner calls.
        if (
            type(value.operation_ref) is not str
            or len(value.operation_ref.encode("utf-8")) > 512
        ):
            raise ContractViolation("grammar operation reference exceeds bound")
        _result_tree(value).check(value)
        value.__post_init__()
        if value.stage != stage:
            raise ContractViolation("grammar source stage differs")
    if (
        profile_expected.use_ref == syntax_expected.use_ref
        or profile_expected.operation_ref != syntax_expected.operation_ref
        or profile_expected.operation_identity is not syntax_expected.operation_identity
        or profile_expected.source_identity is not syntax_expected.source_identity
        or profile_expected.package_identity != syntax_expected.package_identity
        or profile_expected.source_coordinates != syntax_expected.source_coordinates
        or profile_expected.context_bodies != syntax_expected.context_bodies
    ):
        raise ContractViolation("grammar source uses do not share original association")


def _check_products(state) -> tuple[tuple[object, object], ...]:
    retained = state.product_retention
    if retained is None:
        raise ContractViolation("original grammar product retention required")
    retained.validate()
    result = []
    for stage, name, entrance, kind in _FACTORIES:
        if getattr(factory, name) is not entrance:
            raise ContractViolation("original grammar factory entrance substituted")
        profile = grammar_operational_profile(stage)
        matches = tuple(
            (runtime, registration)
            for runtime, registration in retained.products
            if runtime.profile == profile
        )
        if len(matches) != 1:
            raise ContractViolation("unique original grammar product required")
        runtime, registration = matches[0]
        original = selected._registration_state(registration)
        root = selected._selection_root_state(original.selection_root)
        if (
            root.selection_factory is not entrance
            or type(original.provider) is not kind
            or set(runtime._body_codecs) != set(grammar_operational_contracts(stage))
        ):
            raise ContractViolation(
                "original grammar factory or complete codecs differ"
            )
        result.append((runtime, registration))
    retained.validate()
    return tuple(result)


def _check_sources(record) -> None:
    prepared = _validate_declaration_source(record.host)
    validate, context, read = record.methods
    for expected, snapshot in zip(record.expectations, record.snapshots, strict=True):
        snapshot.check(expected)
        for method in (validate, context):
            if method.call(expected.source_identity, expected=expected) is not None:
                raise ContractViolation(
                    "original grammar source validator returned a value"
                )
        bodies = read.call(expected.source_identity, expected=expected)
        if type(bodies) is not tuple or any(
            type(item) is not SemanticInputSourceBody for item in bodies
        ):
            raise ContractViolation(
                "original grammar source reader returned invalid bodies"
            )
        ordinary = SemanticInputProductionInput(
            expected.use_ref,
            expected.operation_ref,
            expected.stage,
            expected.package_identity,
            bodies,
            expected.input_digest,
            expected.context_bodies,
        )
        _, closure = read_grammar_declaration_context(ordinary)
        if closure != prepared.closure:
            raise ContractViolation(
                "grammar declaration differs from original host source"
            )
        for method in (context, validate):
            if method.call(expected.source_identity, expected=expected) is not None:
                raise ContractViolation(
                    "original grammar source validator returned a value"
                )
        snapshot.check(expected)
    if _validate_declaration_source(record.host) is not prepared:
        raise ContractViolation("original grammar declaration preparation changed")


def _validate_grammar_source_role_attachment(host, attachment) -> None:
    """Before/after original checks; failure retires this exact attempt forever."""
    if type(host) is not direct.DirectValidationHost:
        raise TypeError("exact original Code host required")
    if type(attachment) is not _GrammarSourceRoleAttachment:
        raise TypeError("exact original grammar attachment required")
    if attachment.host is not host or direct._HOSTS.get(host) is not attachment.state:
        raise ContractViolation("foreign grammar host attachment")
    # Refuse another process/thread before touching inherited owner locks.
    if attachment.process != os.getpid() or attachment.thread is not current_thread():
        raise ContractViolation("grammar attachment process or thread differs")
    try:
        state = direct._state(host)
        if (
            attachment.retired
            or state.grammar_attachment is not attachment
            or epochs._BINDINGS.get(host) is not attachment.binding
            or state.product_retention is not attachment.retention
        ):
            raise ContractViolation(
                "original grammar attachment is retired or substituted"
            )
        for snapshot, expected in zip(
            attachment.snapshots, attachment.expectations, strict=True
        ):
            snapshot.check(expected)
        if any(
            expected.operation_identity
            is not cast(participation._State, attachment.binding.tracker).parent
            for expected in attachment.expectations
        ):
            raise ContractViolation("grammar source belongs to another command parent")
        with epochs._policy_epoch_use(host) as pair:
            if pair is None or pair[0] is not attachment.binding:
                raise ContractViolation("original grammar epoch binding required")
            if _check_products(state) != attachment.products:
                raise ContractViolation(
                    "original grammar product registrations changed"
                )
            # Source reads occur outside the parent exclusion, under its genuine
            # running epoch obligation. This synchronous envelope spans no await.
            _check_sources(attachment)
            if _check_products(state) != attachment.products:
                raise ContractViolation(
                    "original grammar product registrations changed"
                )
            state.check(read_catalog=False)
        if state.grammar_attachment is not attachment:
            raise ContractViolation(
                "original grammar attachment changed during validation"
            )
    except BaseException:
        attachment.retired = True
        raise


def _capture_grammar_source_role_attachment(
    *,
    code_host: direct.DirectValidationHost,
    profile_expected: SemanticInputProductionExpectation,
    syntax_expected: SemanticInputProductionExpectation,
) -> _GrammarSourceRoleAttachment:
    """Owner-only receiving unit, not the public registered-role constructor.

    Reserve one attempt in original direct-host state before borrowed callbacks.
    No role host, producer registration, result or cleanup ticket is constructed.
    The complete public constructor/async lifecycle remains separately scoped.
    """
    _check_expectations(profile_expected, syntax_expected)
    state = direct._state(code_host)
    binding = epochs._BINDINGS.get(code_host)
    if (
        state.source_rail != "declaration_v3"
        or binding is None
        or binding.state is not state
    ):
        raise ContractViolation("original declaration and epoch host required")
    if (
        profile_expected.operation_identity
        is not cast(participation._State, binding.tracker).parent
    ):
        raise ContractViolation("grammar source belongs to another command parent")
    with direct._LOCK:
        if state.closed or state.grammar_attachment is not None:
            raise ContractViolation("grammar host attachment attempt already consumed")
        state.grammar_attachment = _PENDING
    products = _check_products(state)
    issuer = state.methods["read"].receiver
    record = _GrammarSourceRoleAttachment(
        code_host,
        state,
        binding,
        cast(_ProductRuntimeRetention, state.product_retention),
        (profile_expected, syntax_expected),
        (_result_tree(profile_expected), _result_tree(syntax_expected)),
        tuple(
            direct._capture(issuer, name)
            for name in (
                "validate_semantic_input_source",
                "validate_semantic_input_context",
                "read_semantic_input_sources",
            )
        ),
        products,
        os.getpid(),
        current_thread(),
    )
    with direct._LOCK:
        if state.closed or state.grammar_attachment is not _PENDING:
            raise ContractViolation(
                "grammar host changed during attachment construction"
            )
        state.grammar_attachment = record
    from .grammar_role_cleanup import (
        _correlate_grammar_role_cleanup,
        _issue_grammar_role_cleanup,
    )

    _issue_grammar_role_cleanup(record)
    _correlate_grammar_role_cleanup(record)
    return record
