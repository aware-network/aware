"""Original staged role with selected grouped-source dependency production.

The original Semantic join must open before its profile slot executes. This
owner delegates original Language payload reconstruction and never fabricates
Language result envelopes or cross-occurrence target admission. Original grouped
source validation owns the admitted edges; portable helper results grant nothing.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import cast

from aware_code_module_manifest_contract_runtime.grammar_profile_composition import (
    reconstruct_grammar_group_dependency_binding,
    reconstruct_grammar_local_dependency_binding,
)
from aware_code_module_manifest_contract_runtime.grammar_source_operands import (
    derive_grammar_source_operands,
)
from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.grammar_product_contracts import (
    GRAMMAR_PROFILE_RESULT_REF,
)
from aware_code_semantic_contract_runtime.grammar_profile_codec import (
    grammar_profile_selection_body,
)
from aware_code_semantic_contract_runtime.grammar_profile_contract import (
    GRAMMAR_SYNTAX_BINDING_V2_REF,
)
from aware_code_semantic_contract_runtime.runtime import (
    SemanticBody,
    SemanticContractRuntime,
)

from . import direct_host as direct
from . import grammar_profile_role as profile_owner
from . import grammar_role_cleanup as cleanup
from .grammar_role_attachment import _validate_grammar_source_role_attachment
from .grammar_role_epoch import _grammar_source_epoch_use, _GrammarRoleEpochWork


class CodeGrammarSyntaxRoleJoin(direct._Opaque):
    """Original source-role view; detached coordinates cannot construct it."""

    _state: object = None

    def __init_subclass__(cls, **kwargs):
        raise TypeError("grammar syntax role join is sealed")


@dataclass(eq=False, slots=True)
class _SyntaxRoleState:
    handle: CodeGrammarSyntaxRoleJoin
    profile_role: profile_owner.CodeGrammarProfileSourceRole
    profile_state: profile_owner._ProfileRoleState
    resources: cleanup._SyntaxRoleResources
    declaration: inputs.SemanticInputJoinedProducerDeclaration
    declaration_tree: inputs._ResultTree
    producer: _SyntaxProducer | None = None
    registration_record: object = None
    join_record: object = None
    slot_record: object = None
    received_input: inputs.SemanticInputJoinedProductionInput | None = None


def _state(role: CodeGrammarSyntaxRoleJoin, *, live: bool) -> _SyntaxRoleState:
    if type(role) is not CodeGrammarSyntaxRoleJoin:
        raise TypeError("exact original syntax role join required")
    if CodeGrammarSyntaxRoleJoin.__dict__.get("_state", object()) is not None:
        raise ContractViolation("original syntax role field substituted")
    state = object.__getattribute__(role, "__dict__").get("_state")
    if type(state) is not _SyntaxRoleState or state.handle is not role:
        raise ContractViolation("original syntax role record required")
    profile = profile_owner._state(state.profile_role, live=False)
    if (
        profile is not state.profile_state
        or profile.resources.syntax is not state.resources
        or state.resources.role_state is not state
    ):
        raise ContractViolation("original syntax role association differs")
    if live:
        try:
            if state.resources.constructing:
                raise ContractViolation("original syntax construction is active")
            _verify_binding(state)
        except BaseException:
            profile.attachment.retired = True
            raise
    return state


def _verify_binding(state: _SyntaxRoleState) -> None:
    profile = profile_owner._state(state.profile_role, live=True)
    resources = state.resources
    if (
        profile is not state.profile_state
        or resources.registration_status != "pending"
        or resources.join_status not in ("pending", "unknown")
        or profile.resources.host is None
        or resources.registration is None
        or resources.join is None
    ):
        raise ContractViolation("original syntax role binding is unavailable")
    state.declaration_tree.check(state.declaration)
    registered = inputs._joined_registration_state(
        profile.resources.host, resources.registration
    )
    joined = inputs._role_join_state(profile.resources.host, resources.join)
    validate, context, read = profile.attachment.methods
    if (
        registered is not state.registration_record
        or registered.declaration is not state.declaration
        or registered.producer is not state.producer
        or registered.validator is not validate.receiver
        or registered.reader is not read.receiver
        or registered.validator_entrance != validate.method
        or registered.reader_entrance != read.method
        or registered.context_validator_entrance != context.method
        or not registered.retain_result
        or type(state.producer) is not _SyntaxProducer
        or state.producer.state is not state
        or _SyntaxProducer.__dict__["__call__"] is not _PRODUCE
        or _PRODUCE.__code__ is not _PRODUCE_CODE
        or joined is not state.join_record
        or joined.joined_registration is not resources.registration
        or joined.joined_expected is not resources.expected
        or joined.source_admission is not resources.expected.source_identity
        or joined.operation_identity is not resources.expected.operation_identity
        or len(joined.slots) != 1
        or joined.slots[0] is not state.slot_record
        or joined.slots[0].registration is not profile.resources.registration
        or joined.slots[0].expected is not profile.resources.expected
        or joined.slots[0].role != "code.profile_selection"
        or joined.slots[0].contract != GRAMMAR_PROFILE_RESULT_REF
    ):
        raise ContractViolation("original syntax registration or predecessor changed")


class _SyntaxProducer:
    def __init__(self, state: _SyntaxRoleState):
        self.state = state

    async def __call__(
        self, value: inputs.SemanticInputJoinedProductionInput
    ) -> SemanticBody:
        state = _state(self.state.handle, live=True)
        resources = state.resources
        profile = state.profile_state
        expected = resources.expected
        work = profile.attachment.epoch_work.get(expected.use_ref)
        if (
            type(work) is not _GrammarRoleEpochWork
            or not work.lifetime_active
            or work.task is not asyncio.current_task()
            or work.work_state != "running"
            or work.epoch_state != "running"
            or profile.resources.host is None
            or resources.registration is None
            or resources.join is None
            or inputs._joined_registration_state(
                profile.resources.host, resources.registration
            ).running
            != 1
        ):
            raise ContractViolation("original registered syntax execution required")
        if type(value) is not inputs.SemanticInputJoinedProductionInput:
            raise TypeError("exact original joined syntax input required")
        ordinary = value.ordinary
        predecessor = profile.resources.result
        if (
            ordinary.use_ref != expected.use_ref
            or ordinary.operation_ref != expected.operation_ref
            or ordinary.stage != expected.stage
            or ordinary.package_identity != expected.package_identity
            or ordinary.input_digest != expected.input_digest
            or ordinary.context_bodies is not expected.context_bodies
            or tuple(row.source for row in ordinary.sources)
            != expected.source_coordinates
            or profile.resources.result_status != "pending"
            or predecessor is None
            or len(value.predecessors) != 1
            or value.predecessors[0].coordinate != predecessor.coordinate
            or value.predecessors[0].canonical_body != predecessor.canonical_body
            or inputs._role_join_state(profile.resources.host, resources.join)
            .slots[0]
            .result
            != predecessor
        ):
            raise ContractViolation("original syntax input/predecessor differs")
        operands = derive_grammar_source_operands(
            ordinary,
            profile_key=profile.original_key,
            catalog=profile.attachment.retention.resolver,
        )
        if grammar_profile_selection_body(operands.profile) != predecessor:
            raise ContractViolation("complete original syntax profile changed")
        state.received_input = value
        # Original Code execution owns this inline output; Language's canonical
        # helper/codec remains the interpreter. No standalone Language capability
        # or caller-supplied observed frame is adopted here.
        # Explicit source shape selects the grouped interpretation, never a
        # fallback after failed local execution. The complete original source
        # expectation is authenticated around this use by the registered owner.
        reconstruct = (
            reconstruct_grammar_group_dependency_binding
            if len(set(operands.provider_occurrences)) > 1
            else reconstruct_grammar_local_dependency_binding
        )
        result = reconstruct(
            value,
            selection=operands.selection,
            catalog=profile.attachment.retention.resolver,
            provider_occurrences=operands.provider_occurrences,
        )
        _state(state.handle, live=True)
        return result


_PRODUCE = _SyntaxProducer.__call__
_PRODUCE_CODE = _PRODUCE.__code__


def _compose_grammar_syntax_role_join(
    *, profile_role: profile_owner.CodeGrammarProfileSourceRole
) -> CodeGrammarSyntaxRoleJoin:
    profile = profile_owner._state(profile_role, live=True)
    resources = cleanup._reserve_syntax_role_resources(profile.resources)
    try:
        input_host = profile.resources.host
        prior_registration = profile.resources.registration
        if input_host is None or prior_registration is None:
            raise ContractViolation("original profile host/registration required")
        runtime, registration = profile.attachment.products[1]
        if type(runtime) is not SemanticContractRuntime:
            raise ContractViolation("original syntax Code runtime required")
        retained = profile.attachment.retention
        matches = [
            entry
            for pair, entry in zip(retained.products, retained.entries, strict=True)
            if pair[0] is runtime and pair[1] is registration
        ]
        if len(matches) != 1:
            raise ContractViolation("original syntax product binding required")
        binding = matches[0][3]
        previous = profile.declaration
        declaration = inputs.SemanticInputJoinedProducerDeclaration(
            inputs.SemanticInputProducerDeclaration(
                "aware.code.grammar.syntax-binding.source.v2",
                runtime.profile.profile_ref,
                binding.implementation,
                binding.configuration,
                previous.source_contracts,
                "code.syntax_binding",
                GRAMMAR_SYNTAX_BINDING_V2_REF,
                previous.context_contracts,
            ),
            (
                inputs.SemanticInputSourceContract(
                    "code.profile_selection", GRAMMAR_PROFILE_RESULT_REF
                ),
            ),
            ("profile_selection",),
        )
        handle = object.__new__(CodeGrammarSyntaxRoleJoin)
        state = _SyntaxRoleState(
            handle,
            profile_role,
            profile,
            resources,
            declaration,
            inputs._result_tree(declaration),
        )
        object.__setattr__(handle, "_state", state)
        resources.role_state = state
        producer = _SyntaxProducer(state)
        state.producer = producer
        validate, context, read = profile.attachment.methods
        resources.registration_status = "unknown"
        admitted = inputs.register_joined_semantic_input_producer(
            input_host,
            declaration=declaration,
            producer=producer,
            validator=cast(inputs.SemanticInputSourceValidator, validate.receiver),
            validator_entrance=validate.method,
            reader=cast(inputs.SemanticInputSourceReader, read.receiver),
            reader_entrance=read.method,
            context_validator_entrance=context.method,
            retain_result=True,
        )
        resources.raw_return_present, resources.raw_return = True, admitted
        registered = inputs._joined_registration_state(input_host, admitted)
        if (
            registered.declaration is not declaration
            or registered.producer is not producer
        ):
            raise ContractViolation("original syntax registration acquisition differs")
        resources.registration = resources.registration_origin = admitted
        resources.registration_status = "pending"
        state.registration_record = registered
        resources.validation_epoch = "uncertain"
        resources.join_status = "unknown"
        joined = inputs.open_semantic_input_role_join(
            input_host,
            joined_registration=admitted,
            joined_expected=resources.expected,
            source_admission=resources.expected.source_identity,
            predecessors=(
                inputs.SemanticInputRoleJoinPredecessor(
                    prior_registration, profile.resources.expected
                ),
            ),
        )
        resources.raw_return_present, resources.raw_return = True, joined
        join_record = inputs._role_join_state(input_host, joined)
        if (
            join_record.joined_registration is not admitted
            or join_record.joined_expected is not resources.expected
            or join_record.source_admission is not resources.expected.source_identity
            or len(join_record.slots) != 1
            or join_record.slots[0].registration is not profile.resources.registration
            or join_record.slots[0].expected is not profile.resources.expected
        ):
            raise ContractViolation("original syntax join acquisition differs")
        resources.join = resources.join_origin = joined
        resources.join_status = "pending"
        state.join_record = join_record
        state.slot_record = join_record.slots[0]
        _validate_grammar_source_role_attachment(
            profile.attachment.host, profile.attachment
        )
        resources.validation_epoch = "finished"
        _state(handle, live=False)
        _verify_binding(state)
    except BaseException as error:
        resources.construction_error = error
        profile.attachment.retired = True
        raise
    finally:
        resources.constructing = False
    return handle


async def execute_grammar_syntax_role_join(
    role: CodeGrammarSyntaxRoleJoin, *, predecessor: SemanticBody
) -> SemanticBody:
    state = _state(role, live=True)
    resources = state.resources
    profile = state.profile_state.resources
    original_join_record = state.join_record
    if profile.result_status != "pending" or profile.result is not predecessor:
        raise ContractViolation("original retained profile predecessor required")
    if resources.execution_attempted:
        raise ContractViolation("original syntax execution attempt is consumed")
    input_host, prior_registration = profile.host, profile.registration
    registration, role_join = resources.registration, resources.join
    if (
        input_host is None
        or prior_registration is None
        or registration is None
        or role_join is None
    ):
        raise ContractViolation("original syntax host/registration/join required")
    resources.execution_attempted = True
    try:
        async with _grammar_source_epoch_use(
            state.profile_state.attachment.host,
            state.profile_state.attachment,
            expected=resources.expected,
        ):
            inputs.validate_registered_semantic_input_result(
                input_host,
                prior_registration,
                source_admission=profile.expected.source_identity,
                expected=profile.expected,
                result=predecessor,
            )
            # The original executor consumes the join on either success or
            # failure. A thrown failure is not a separate disposal confirmation.
            resources.join_status = "unknown"
            resources.result_status = "unknown"
            returned = await inputs.execute_registered_joined_semantic_input(
                input_host,
                registration,
                role_join=role_join,
                source_admission=resources.expected.source_identity,
                expected=resources.expected,
            )
            resources.execution_return_present, resources.execution_return = (
                True,
                returned,
            )
            if type(returned) is not SemanticBody:
                raise ContractViolation("unqualified syntax execution returned a value")
            validated = inputs.validate_registered_semantic_input_result(
                input_host,
                registration,
                source_admission=resources.expected.source_identity,
                expected=resources.expected,
                result=returned,
            )
            if validated is not None:
                raise ContractViolation(
                    "original syntax result validator returned a value"
                )
            # Read the retained original owner record, never infer settlement
            # from an empty registry or a caller-supplied completion flag.
            joined = original_join_record
            if (
                type(joined) is not inputs._RoleJoinState
                or state.join_record is not joined
                or not joined.consumed
                or joined.running
                or joined.active_predecessors
            ):
                raise ContractViolation("original syntax join consumption unconfirmed")
            resources.result = resources.result_origin = returned
            resources.result_status = "pending"
            resources.join_status = "released"
        return returned
    except BaseException:
        state.profile_state.attachment.retired = True
        raise


def close_grammar_syntax_role_join(role: CodeGrammarSyntaxRoleJoin):
    state = _state(role, live=False)
    return cleanup.dispose_grammar_role_cleanup(state.resources.profile.custody.ticket)
