"""Original profile source-role execution; syntax/dependencies remain separate.

The private composer accepts original host/expectations and an explicit request
selector, never a resolver, callback, producer or detached role host. This is not
the complete two-stage constructor or a mounted/public SDK operation.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import cast

from aware_code_module_manifest_contract_runtime.grammar_profile_composition import (
    produce_grammar_profile_selection,
    validate_grammar_profile_selection_result,
)
from aware_code_module_manifest_contract_runtime.grammar_profile_source import _selector
from aware_code_module_manifest_contract_runtime.grammar_source_operands import (
    derive_grammar_source_operands,
)
from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.grammar_product_contracts import (
    GRAMMAR_PROFILE_RESULT_REF,
)
from aware_code_semantic_contract_runtime.runtime import (
    SemanticBody,
    SemanticContractRuntime,
)
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputContextContract,
    SemanticInputProducerDeclaration,
    SemanticInputProductionExpectation,
    SemanticInputProductionInput,
    SemanticInputSourceContract,
    _result_tree,
    _ResultTree,
)

from . import direct_host as direct
from . import grammar_role_cleanup as cleanup
from .grammar_role_attachment import (
    _capture_grammar_source_role_attachment,
    _check_products,
    _GrammarSourceRoleAttachment,
    _validate_grammar_source_role_attachment,
)
from .grammar_role_epoch import _grammar_source_epoch_use, _GrammarRoleEpochWork


class CodeGrammarProfileSourceRole(direct._Opaque):
    """Original-owner view, not an independently constructible role host."""

    _state: object = None

    def __init_subclass__(cls, **kwargs):
        raise TypeError("grammar profile source role is sealed")


@dataclass(eq=False, slots=True)
class _ProfileRoleState:
    handle: CodeGrammarProfileSourceRole
    attachment: _GrammarSourceRoleAttachment
    resources: cleanup._ProfileRoleResources
    profile_key: str
    original_key: str
    declaration: SemanticInputProducerDeclaration
    declaration_tree: _ResultTree
    producer: _ProfileProducer | None = None
    host_origin: inputs.SemanticInputProducerHost | None = None
    registration_origin: inputs.AdmittedSemanticInputProducerRegistration | None = None


def _state(role: CodeGrammarProfileSourceRole, *, live: bool) -> _ProfileRoleState:
    if type(role) is not CodeGrammarProfileSourceRole:
        raise TypeError("exact original profile source role required")
    if CodeGrammarProfileSourceRole.__dict__.get("_state", object()) is not None:
        raise ContractViolation("original profile role field substituted")
    state = object.__getattribute__(role, "__dict__").get("_state")
    if type(state) is not _ProfileRoleState or state.handle is not role:
        raise ContractViolation("original profile role record required")
    resources = state.resources
    custody = cleanup._custody(resources.custody.ticket)
    if (
        custody.attachment is not state.attachment
        or custody.profile_resources is not resources
        or resources.role_state is not state
    ):
        raise ContractViolation("original profile role association differs")
    if not live:
        return state
    try:
        if resources.constructing:
            raise ContractViolation("original profile role is retired or changed")
        _verify_registration(state)
    except BaseException:
        state.attachment.retired = True
        raise
    return state


def _verify_registration(state: _ProfileRoleState) -> None:
    resources = state.resources
    custody = cleanup._custody(resources.custody.ticket)
    if (
        resources.role_state is not state
        or custody.attachment is not state.attachment
        or state.attachment.retired
        or custody.disposal_state != "pending"
        or direct._HOSTS.get(state.attachment.host) is not state.attachment.state
        or state.profile_key != state.original_key
        or resources.host is None
        or resources.registration is None
        or resources.host_status != "pending"
        or resources.registration_status != "pending"
        or resources.host is not state.host_origin
        or resources.registration is not state.registration_origin
    ):
        raise ContractViolation("original profile role is retired or changed")
    state.declaration_tree.check(state.declaration)
    _check_products(state.attachment.state)
    registered = inputs._registration_state(resources.host, resources.registration)
    validate, context, read = state.attachment.methods
    if (
        registered.declaration is not state.declaration
        or registered.producer is not state.producer
        or registered.validator is not validate.receiver
        or registered.reader is not read.receiver
        or registered.validator_entrance != validate.method
        or registered.reader_entrance != read.method
        or registered.context_validator_entrance != context.method
        or not registered.retain_result
        or type(state.producer) is not _ProfileProducer
        or state.producer.state is not state
        or _ProfileProducer.__dict__["__call__"] is not _PRODUCE
        or _PRODUCE.__code__ is not _PRODUCE_CODE
    ):
        raise ContractViolation("original profile producer registration differs")


class _ProfileProducer:
    """Fixed owner adapter; interpretation stays in the original Module helpers."""

    def __init__(self, state: _ProfileRoleState) -> None:
        self.state = state

    async def __call__(self, value: SemanticInputProductionInput) -> SemanticBody:
        state = _state(self.state.handle, live=True)
        resources = state.resources
        expected = resources.expected
        work = state.attachment.epoch_work.get(expected.use_ref)
        if (
            type(work) is not _GrammarRoleEpochWork
            or not work.lifetime_active
            or work.task is not asyncio.current_task()
            or work.epoch_state != "running"
            or work.work_state != "running"
            or resources.host is None
            or resources.registration is None
            or inputs._registration_state(
                resources.host, resources.registration
            ).running
            != 1
        ):
            raise ContractViolation("original registered profile execution required")
        if (
            type(value) is not SemanticInputProductionInput
            or value.use_ref != expected.use_ref
            or value.operation_ref != expected.operation_ref
            or value.stage != expected.stage
            or value.package_identity != expected.package_identity
            or value.input_digest != expected.input_digest
            or value.context_bodies is not expected.context_bodies
            or tuple(row.source for row in value.sources) != expected.source_coordinates
        ):
            raise ContractViolation("original registered profile input differs")
        catalog = state.attachment.retention.resolver
        operands = derive_grammar_source_operands(
            value, profile_key=state.profile_key, catalog=catalog
        )
        result = produce_grammar_profile_selection(
            value,
            selection=operands.selection,
            profile=operands.profile,
            catalog=catalog,
            provider_occurrences=operands.provider_occurrences,
        )
        validate_grammar_profile_selection_result(
            result,
            input=value,
            selection=operands.selection,
            profile=operands.profile,
            catalog=catalog,
            provider_occurrences=operands.provider_occurrences,
        )
        _state(state.handle, live=True)
        return result


_PRODUCE = _ProfileProducer.__call__
_PRODUCE_CODE = _PRODUCE.__code__
_HOST_TYPE = inputs.SemanticInputProducerHost
_HOST_NEW = _HOST_TYPE.__new__
_HOST_INIT = _HOST_TYPE.__init__
_HOST_INIT_CODE = _HOST_INIT.__code__
_REGISTRATION_TYPE = inputs.AdmittedSemanticInputProducerRegistration


def _check_host_construction_entrance() -> None:
    if (
        inputs.SemanticInputProducerHost is not _HOST_TYPE
        or type(_HOST_TYPE) is not type
        or _HOST_TYPE.__new__ is not _HOST_NEW
        or _HOST_NEW is not object.__new__
        or _HOST_TYPE.__init__ is not _HOST_INIT
        or _HOST_INIT.__code__ is not _HOST_INIT_CODE
    ):
        raise ContractViolation("original input host construction entrance differs")


def _compose_grammar_profile_source_role(
    *,
    code_host: direct.DirectValidationHost,
    profile_expected: SemanticInputProductionExpectation,
    syntax_expected: SemanticInputProductionExpectation,
    profile_key: str,
) -> CodeGrammarProfileSourceRole:
    """Bounded internal first stage; the selector is not source authority."""
    key = _selector(profile_key)
    attachment = _capture_grammar_source_role_attachment(
        code_host=code_host,
        profile_expected=profile_expected,
        syntax_expected=syntax_expected,
    )
    resources = cleanup._reserve_profile_role_resources(attachment)
    try:
        runtime, registration = attachment.products[0]
        if type(runtime) is not SemanticContractRuntime:
            raise ContractViolation("original profile Code runtime required")
        retained = attachment.retention
        matches = [
            entry
            for pair, entry in zip(retained.products, retained.entries, strict=True)
            if pair[0] is runtime and pair[1] is registration
        ]
        if len(matches) != 1:
            raise ContractViolation("original profile product binding required")
        binding = matches[0][3]
        contracts = tuple(
            sorted(
                {
                    SemanticInputSourceContract(
                        row.coordinate.role, row.coordinate.contract
                    )
                    for row in profile_expected.source_coordinates
                },
                key=lambda row: row.role.encode(),
            )
        )
        declaration = SemanticInputProducerDeclaration(
            "aware.code.grammar.profile-selection.source.v1",
            runtime.profile.profile_ref,
            binding.implementation,
            binding.configuration,
            contracts,
            "code.profile_selection",
            GRAMMAR_PROFILE_RESULT_REF,
            tuple(
                SemanticInputContextContract(
                    row.coordinate.role, row.coordinate.contract
                )
                for row in profile_expected.context_bodies
            ),
        )
        handle = object.__new__(CodeGrammarProfileSourceRole)
        state = _ProfileRoleState(
            handle,
            attachment,
            resources,
            key,
            key,
            declaration,
            _result_tree(declaration),
        )
        object.__setattr__(handle, "_state", state)
        resources.role_state = state
        producer = _ProfileProducer(state)
        state.producer = producer
        _check_host_construction_entrance()
        resources.host_status = "unknown"
        host = inputs.SemanticInputProducerHost()
        resources.raw_return_present, resources.raw_return = True, host
        _check_host_construction_entrance()
        if type(host) is not _HOST_TYPE:
            raise ContractViolation(
                "original input host constructor returned invalid host"
            )
        resources.host, resources.host_status = host, "pending"
        resources.host_origin = host
        state.host_origin = host
        validate, context, read = attachment.methods
        resources.registration_status = "unknown"
        admitted = inputs.register_semantic_input_producer(
            host,
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
        if type(admitted) is not _REGISTRATION_TYPE:
            raise ContractViolation(
                "original producer admission returned invalid registration"
            )
        resources.registration, resources.registration_status = admitted, "pending"
        resources.registration_origin = admitted
        state.registration_origin = admitted
        resources.validation_epoch = "uncertain"
        _validate_grammar_source_role_attachment(code_host, attachment)
        resources.validation_epoch = "finished"
        _state(handle, live=False)
        _verify_registration(state)
    except BaseException as error:
        resources.construction_error = error
        attachment.retired = True
        raise
    finally:
        resources.constructing = False
    return handle


async def execute_grammar_profile_source_role(
    role: CodeGrammarProfileSourceRole,
) -> SemanticBody:
    state = _state(role, live=True)
    resources = state.resources
    if resources.result_status != "not_acquired":
        raise ContractViolation("original profile result attempt already consumed")
    expected = resources.expected
    try:
        async with _grammar_source_epoch_use(
            state.attachment.host, state.attachment, expected=expected
        ):
            if resources.host is None or resources.registration is None:
                raise ContractViolation("original profile resources required")
            resources.result_status = "unknown"
            result = await inputs.execute_registered_semantic_input(
                resources.host,
                resources.registration,
                source_admission=expected.source_identity,
                expected=expected,
            )
            resources.raw_return_present, resources.raw_return = True, result
            inputs.validate_registered_semantic_input_result(
                resources.host,
                resources.registration,
                source_admission=expected.source_identity,
                expected=expected,
                result=result,
            )
            resources.result, resources.result_status = result, "pending"
            resources.result_origin = result
        return result
    except BaseException:
        state.attachment.retired = True
        raise


def release_grammar_profile_source_result(
    role: CodeGrammarProfileSourceRole,
    *,
    result: SemanticBody,
) -> None:
    state = _state(role, live=False)
    resources = state.resources
    if resources.result is not result or resources.result_status != "pending":
        raise ContractViolation("original retained profile result required")
    if resources.host is None or resources.registration is None:
        raise ContractViolation("original profile resources required")
    resources.result_status = "unknown"
    try:
        returned = inputs.release_registered_semantic_input_result(
            resources.host,
            resources.registration,
            source_admission=resources.expected.source_identity,
            expected=resources.expected,
            result=result,
        )
        cleanup._require_profile_disposal_none(resources, "profile_result", returned)
    except BaseException:
        resources.result_status = "unknown"
        state.attachment.retired = True
        raise
    resources.result_status = "released"


def close_grammar_profile_source_role(
    role: CodeGrammarProfileSourceRole,
):
    state = _state(role, live=False)
    return cleanup.dispose_grammar_role_cleanup(state.resources.custody.ticket)
