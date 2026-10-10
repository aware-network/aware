"""Neutral predecessor adapter mechanics; Workspace conformance runs separately."""

from dataclasses import replace
from types import SimpleNamespace
from typing import Any, cast

import pytest
from aware_code_retained_registry_policy_runtime.authority_execution import (
    RetainedAuthorityPredecessor,
    _authority_input_bodies,
    _requested_output_roles,
    read_retained_authority_predecessor,
    retain_authority_predecessor,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    SemanticContractRef,
    SemanticValueCoordinate,
    TypedEmptyCoordinate,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.materialization_planning import (
    CodeSemanticMaterializationIntent,
    CodeSemanticRequiredResultProduct,
)
from aware_code_semantic_contract_runtime.retained_admission_interfaces import (
    RetainedSemanticAdmissionExpectation,
)
from aware_code_semantic_contract_runtime.runtime import SemanticBody


def _ref(name):
    return SemanticContractRef(
        name,
        "1",
        ContentDigest.of_bytes(canonical_json_bytes({"contract": name})),
    )


def _expected():
    opaque = lambda: cast(Any, object())
    return RetainedSemanticAdmissionExpectation(
        opaque(),
        object(),
        object(),
        1,
        opaque(),
        "authority_derivation",
        opaque(),
        opaque(),
        opaque(),
        opaque(),
        ContentDigest.of_bytes(b"source"),
        opaque(),
        opaque(),
        opaque(),
        opaque(),
        opaque(),
    )


class Evidence:
    def __init__(self, contract):
        self.disposition = "genesis"
        self.predecessor = TypedEmptyCoordinate(contract)
        self.predecessor_body = None
        self.materialization_head_revision = 0
        self.materialization_head_digest = None


class Issuer:
    def __init__(self, evidence):
        self.evidence = evidence
        self.live = True
        self.calls = []

    def _check(self, admission, kwargs):
        if not self.live or admission is not TOKEN:
            raise ContractViolation("original predecessor unavailable")
        if kwargs["authority_context"] is not CONTEXT:
            raise ContractViolation("authority context differs")
        if kwargs["execution_identity"] is not EXECUTION:
            raise ContractViolation("execution differs")

    def read_authority_predecessor(self, admission, **kwargs):
        self._check(admission, kwargs)
        self.calls.append("read")
        return self.evidence

    def validate_authority_predecessor_admission(self, admission, **kwargs):
        self._check(admission, kwargs)
        self.calls.append("validate")


TOKEN = object()
CONTEXT = object()
EXECUTION = object()


def retained():
    contract = _ref("package-authority")
    issuer = Issuer(Evidence(contract))
    handle = retain_authority_predecessor(
        issuer,
        TOKEN,
        authority_context=CONTEXT,
        authority_expected=_expected(),
        execution_identity=EXECUTION,
        result_contract=contract,
    )
    return issuer, handle


def test_retains_original_reader_and_validator_and_rereads_currentness():
    issuer, handle = retained()
    assert type(handle) is RetainedAuthorityPredecessor
    evidence = read_retained_authority_predecessor(handle)
    assert evidence.disposition == "genesis"
    assert issuer.calls.count("read") >= 3
    assert issuer.calls.count("validate") >= 4


def test_changed_or_revoked_original_evidence_rejects():
    issuer, handle = retained()
    issuer.evidence.materialization_head_revision = 1
    with pytest.raises(ContractViolation):
        read_retained_authority_predecessor(handle)
    issuer.live = False
    with pytest.raises(ContractViolation):
        read_retained_authority_predecessor(handle)


def test_substituted_method_and_foreign_handle_reject():
    issuer, handle = retained()
    issuer.read_authority_predecessor = lambda *args, **kwargs: issuer.evidence
    with pytest.raises(ContractViolation, match="substituted"):
        read_retained_authority_predecessor(handle)
    with pytest.raises(ContractViolation, match="foreign"):
        read_retained_authority_predecessor(
            object.__new__(RetainedAuthorityPredecessor)
        )


def test_wrong_stage_and_contract_reject_before_retention():
    contract = _ref("package-authority")
    issuer = Issuer(Evidence(contract))
    with pytest.raises(TypeError, match="authority-stage"):
        retain_authority_predecessor(
            issuer,
            TOKEN,
            authority_context=CONTEXT,
            authority_expected=replace(_expected(), stage="source_planning"),
            execution_identity=EXECUTION,
            result_contract=contract,
        )
    issuer.evidence.predecessor = TypedEmptyCoordinate(_ref("foreign"))
    with pytest.raises(ContractViolation, match="contract differs"):
        retain_authority_predecessor(
            issuer,
            TOKEN,
            authority_context=CONTEXT,
            authority_expected=_expected(),
            execution_identity=EXECUTION,
            result_contract=contract,
        )


def test_expected_type_remains_exact():
    assert type(_expected()) is RetainedSemanticAdmissionExpectation


def _body(role: str, contract: SemanticContractRef) -> SemanticBody:
    content = role.encode()
    return SemanticBody(
        SemanticValueCoordinate(
            role, contract, f"test-{role}", ContentDigest.of_bytes(content), len(content)
        ),
        content,
    )


def test_authority_terminal_roles_follow_original_intent_and_contract():
    contract = _ref("delta")
    intent = CodeSemanticMaterializationIntent.create(
        operation_kind="materialize",
        requested_semantic_root_refs=("test.root",),
        requested_terminal_output_roles=("package_delta",),
        semantic_configuration_coordinate=None,
    )
    required = CodeSemanticRequiredResultProduct.create(
        role="package_delta", contract=contract
    )
    profile = SimpleNamespace(
        terminal_output_roles=("package_delta",),
        terminal_result_role="package_authority",
        providers=(
            SimpleNamespace(
                output_roles=(SimpleNamespace(role="package_delta", contract=contract),),
                result_role=SimpleNamespace(
                    role="package_authority", contract=_ref("package-authority")
                ),
            ),
        ),
    )
    context = SimpleNamespace(
        expected=SimpleNamespace(runtime=SimpleNamespace(profile=profile)),
        demand=SimpleNamespace(
            context=SimpleNamespace(code_intent=intent, required_result_products=(required,))
        ),
    )
    assert _requested_output_roles(context) == ("package_delta",)
    profile.terminal_output_roles = ("other_delta",)
    with pytest.raises(ContractViolation, match="undeclared terminal output"):
        _requested_output_roles(context)
    profile.terminal_output_roles = ("package_delta",)
    profile.providers = (
        SimpleNamespace(
            output_roles=(SimpleNamespace(role="package_delta", contract=_ref("wrong")),),
            result_role=SimpleNamespace(
                role="package_authority", contract=_ref("package-authority")
            ),
        ),
    )
    with pytest.raises(ContractViolation, match="result contract differs"):
        _requested_output_roles(context)


def test_terminal_result_is_not_a_requested_provider_output():
    result = _ref("package-authority")
    intent = CodeSemanticMaterializationIntent.create(
        operation_kind="materialize",
        requested_semantic_root_refs=("test.root",),
        requested_terminal_output_roles=("package_authority",),
        semantic_configuration_coordinate=None,
    )
    context = SimpleNamespace(
        expected=SimpleNamespace(runtime=SimpleNamespace(profile=SimpleNamespace(
            terminal_result_role="package_authority",
            terminal_output_roles=(),
            providers=(SimpleNamespace(
                result_role=SimpleNamespace(role="package_authority", contract=result),
                output_roles=(),
            ),),
        ))),
        demand=SimpleNamespace(context=SimpleNamespace(
            code_intent=intent,
            required_result_products=(CodeSemanticRequiredResultProduct.create(
                role="package_authority", contract=result,
            ),),
        )),
    )
    assert _requested_output_roles(context) == ()


def test_authority_closure_requires_only_declared_roles_and_exact_contracts():
    contract = _ref("input")
    profile = SimpleNamespace(
        inputs=tuple(
            SimpleNamespace(role=role, contract=contract)
            for role in ("manifest_source", "dependency_planning", "semantic_dependencies", "parsed_documents")
        )
    )
    request = (_body("manifest_source", contract),)
    planning = _body("dependency_planning", contract)
    products = _body("semantic_dependencies", contract)
    parsed = _body("parsed_documents", contract)
    unrelated = _body("planning_diagnostic", contract)
    assert tuple(
        body.coordinate.role
        for body in _authority_input_bodies(
            profile, request, planning, (parsed, unrelated), products
        )
    ) == (
        "dependency_planning",
        "manifest_source",
        "parsed_documents",
        "semantic_dependencies",
    )
    with pytest.raises(ContractViolation, match="input closure incomplete"):
        _authority_input_bodies(profile, request, planning, (unrelated,), products)
    with pytest.raises(ContractViolation, match="input closure incomplete"):
        _authority_input_bodies(profile, request, planning, (parsed, parsed), products)
    with pytest.raises(ContractViolation, match="input closure incomplete"):
        _authority_input_bodies(
            profile, request, planning, (_body("parsed_documents", _ref("wrong")),), products
        )
