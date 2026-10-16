"""Detached read-product and failure evidence; no live host or cleanup ticket."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import (
    ConsumedRoleDeclaration,
    ContentDigest,
    ContractViolation,
    ProducedRoleDeclaration,
    SemanticContractProviderDeclaration,
    SemanticContractRef,
    SemanticImplementationCoordinate,
    SemanticValueCoordinate,
    canonical_json_bytes,
)
from .grammar_profile_codec import (
    _implementation,
    _keys,
    _list,
    _load,
    _read_coordinate,
    _read_declaration,
)
from .grammar_profile_contract import (
    GRAMMAR_PROFILE_RESULT_REF,
    GRAMMAR_SYNTAX_BINDING_V2_REF,
    CodeGrammarDeclarationSourceV1,
    CodeGrammarSyntaxBindingV2,
    _bounded,
    _coordinate,
    _digest,
    _exact,
    _items,
    _ordered,
    _ref,
    _token,
)
from .grammar_source_group import GRAMMAR_SOURCE_GROUP_REF
from .profile import (
    ProfileInputDeclaration,
    ProfileStepDeclaration,
    RoleBinding,
    SemanticContractProfileDeclaration,
)
from .retained_declaration_scope_codec import RETAINED_DECLARATION_SCOPE_V3_REF
from .runtime import SemanticBodyValidationContext

GRAMMAR_SOURCE_ROLE_SELECTION_REF = SemanticContractRef(
    "aware.code.grammar-source-role-selection.v1",
    "1",
    ContentDigest(
        "sha256:c75e5a31fed8d58d66cfe367464ab5515475986e7ef6215d99d30e42f0842838"
    ),
)
GRAMMAR_READ_TRANSITION_REF = SemanticContractRef(
    "aware.code.grammar-read-transition.v1",
    "1",
    ContentDigest(
        "sha256:951583241771d244f217b411754ab5806fef63fb13c2e66859685daa0591a707"
    ),
)
GRAMMAR_READ_EFFECT_REF = SemanticContractRef(
    "aware.code.grammar-read-effect.v1",
    "1",
    ContentDigest(
        "sha256:b6227e2a42926d6d6a0c5a2f7cf107d5afef20a86779a19e634525c8bd745066"
    ),
)
GRAMMAR_ROLE_CLEANUP_REF = SemanticContractRef(
    "aware.code.grammar-role-cleanup-receipt.v1",
    "1",
    ContentDigest(
        "sha256:3f8f62cf14ffb0bfe327098ca80a0e80eb9914e32498824dd695f0c5ba5a92f1"
    ),
)
GRAMMAR_ROLE_FAILURE_REF = SemanticContractRef(
    "aware.code.grammar-role-failure-evidence.v1",
    "1",
    ContentDigest(
        "sha256:82cbd64b5591ddd6e06e8abde4b9b8eacb3f1413961206382710252b6f539042"
    ),
)

GRAMMAR_PROFILE_PROVIDER_REF = SemanticContractRef(
    "aware.code.grammar.profile-selection.provider.v1",
    "1",
    ContentDigest(
        "sha256:105b62166a5d6e807c09f6760934174d5390b6ead57e9f1011eeeb5c880e8239"
    ),
)
GRAMMAR_SYNTAX_PROVIDER_V2_REF = SemanticContractRef(
    "aware.code.grammar.syntax-binding.provider.v2",
    "2",
    ContentDigest(
        "sha256:7140dae9c7c53edebaf90d320a10b6a52f0bb6dbdda6fa1ca5f984bfcf5f5f3b"
    ),
)

GRAMMAR_SOURCE_ROLE_PLANNER_DESCRIPTOR = canonical_json_bytes(
    {
        "contract": "aware.code.grammar-source-role-planner.v1",
        "version": "1",
        "entrance": "async plan(*, package: SemanticPackageCoordinate, intent: CodeSemanticMaterializationIntent, selected_match: CodeSemanticContractMatch, planning_input: SemanticDependencyPlanningInput) -> SemanticDependencyDemandSet",
        "disposition": "revalidate original contribution/catalog binding and then raise ContractViolation('grammar products require original source-role join'); invalid/stale originals refuse first",
        "laws": [
            "no empty demand success, target intent construction, source selection, supplier execution or dependency filtering",
            "helpers are consumed through original registered source roles, not automatic graph planning; explicit future graph targeting needs a separate contract",
        ],
    }
)
GRAMMAR_SOURCE_ROLE_PLANNER_REF = SemanticContractRef(
    "aware.code.grammar-source-role-planner.v1",
    "1",
    ContentDigest.of_bytes(GRAMMAR_SOURCE_ROLE_PLANNER_DESCRIPTOR),
)
GRAMMAR_SOURCE_ROLE_DEMAND_REF = SemanticContractRef(
    "aware.code.grammar-source-role-demand.v1",
    "1",
    ContentDigest(
        "sha256:1cb5fec6dfce1aaac82e66a06f004e7e57ea6e494ced8d47ff5f3b9f01ba0b03"
    ),
)
GRAMMAR_SOURCE_ROLE_TARGET_INTENT_REF = SemanticContractRef(
    "aware.code.grammar-source-role-target-intent.v1",
    "1",
    ContentDigest(
        "sha256:79cc582616a36b2292085c183cd8558c5ead439bb88b8d53e51a5e684c5caaa3"
    ),
)


class CodeGrammarUnadmittedGraphCodec:
    """Closed graph refusal contracts; no value or target permission exists."""

    contract: SemanticContractRef
    implementation: SemanticImplementationCoordinate

    def __init__(self, contract: SemanticContractRef) -> None:
        contract = _ref(contract)
        if contract not in (
            GRAMMAR_SOURCE_ROLE_DEMAND_REF,
            GRAMMAR_SOURCE_ROLE_TARGET_INTENT_REF,
        ):
            raise ContractViolation("grammar graph refusal contract differs")
        self.contract = contract
        self.implementation = _implementation(
            contract,
            contract.key + ".codec",
            "no value admitted; refuse every encode/decode; original source-role helpers grant no graph or write authority",
        )

    def encode(self, value: object) -> bytes:
        _ = value
        raise ContractViolation("grammar graph value is not admitted")

    def decode(self, canonical_body: bytes) -> object:
        _ = canonical_body
        raise ContractViolation("grammar graph value is not admitted")


GRAMMAR_CLEANUP_RESOURCE_KINDS = (
    "attachment",
    "role_host",
    "profile_registration",
    "syntax_registration",
    "role_join",
    "profile_result",
    "syntax_result",
    "epoch_use",
)
GRAMMAR_CLEANUP_RESOURCE_STATUSES = (
    "not_acquired",
    "released",
    "pending",
    "blocked_active",
    "failed",
    "unknown",
)
GRAMMAR_CLEANUP_CAUSES = (
    "construction_failure",
    "execution_failure",
    "normal_close",
    "context_exit",
)
GRAMMAR_CLEANUP_WORK_STATES = ("not_started", "quiescent", "unverified")
GRAMMAR_CLEANUP_EPOCH_STATES = (
    "not_started",
    "pending",
    "running",
    "finished",
    "uncertain",
    "unavailable",
)
GRAMMAR_CLEANUP_COMPLETIONS = ("verified", "unverified")
GRAMMAR_FAILURE_PHASES = (
    "validate_host",
    "construct",
    "profile_selection",
    "syntax_binding",
    "validate_result",
    "release_result",
    "close",
    "context_exit",
)
GRAMMAR_FAILURE_REASONS = (
    "admission_refused",
    "construction_failed",
    "execution_failed",
    "result_unvalidated",
    "cleanup_blocked",
    "cleanup_failed",
    "interrupted",
)
GRAMMAR_FAILURE_RESULT_STATES = ("not_started", "known", "unvalidated", "unverified")


def _enum(value: object, choices: tuple[str, ...]) -> str:
    text = _exact(value, str)
    if text not in choices:
        raise ContractViolation("grammar enum literal differs")
    return text


def _stage(value: object) -> str:
    return _enum(value, ("profile_selection", "syntax_binding"))


def grammar_operational_profile(stage: str) -> SemanticContractProfileDeclaration:
    """Fresh complete helper declaration, not an authored interpretation profile.

    The original profile constructor resolves and validates its graph. This
    data entrance registers no provider, selects no source and grants no host
    or execution authority. Syntax consumes the retained profile result as an
    input; its own generic state predecessor remains typed-empty.
    """
    selected = _stage(stage)
    syntax = selected == "syntax_binding"
    version = "2" if syntax else "1"
    provider_key = "aware_code.grammar." + selected
    inputs = (
        ProfileInputDeclaration("declaration_scope", RETAINED_DECLARATION_SCOPE_V3_REF),
        ProfileInputDeclaration("grammar_selection", GRAMMAR_SOURCE_ROLE_SELECTION_REF),
        ProfileInputDeclaration("grammar_source_group", GRAMMAR_SOURCE_GROUP_REF),
    )
    if syntax:
        inputs = (
            ProfileInputDeclaration(
                "code.profile_selection", GRAMMAR_PROFILE_RESULT_REF
            ),
        ) + inputs
    result = ProducedRoleDeclaration(
        "code." + selected,
        GRAMMAR_SYNTAX_BINDING_V2_REF if syntax else GRAMMAR_PROFILE_RESULT_REF,
    )
    effect = ProducedRoleDeclaration(
        "code." + selected + "_effect", GRAMMAR_READ_EFFECT_REF
    )
    provider = SemanticContractProviderDeclaration(
        provider_key=provider_key,
        provider_contract=GRAMMAR_SYNTAX_PROVIDER_V2_REF
        if syntax
        else GRAMMAR_PROFILE_PROVIDER_REF,
        package_kinds=("code", "ontology", "sdk"),
        operation_kinds=("resolve_grammar_profile",),
        consumed_roles=tuple(
            ConsumedRoleDeclaration(row.role, (row.contract,)) for row in inputs
        ),
        result_role=result,
        transition_contract=GRAMMAR_READ_TRANSITION_REF,
        effect_role=effect,
        effect_contract=GRAMMAR_READ_EFFECT_REF,
        allows_typed_empty=True,
        predecessor_required=False,
        terminal_statuses=("delta",),
    )
    return SemanticContractProfileDeclaration(
        profile_ref="aware.code.grammar."
        + selected.replace("_", "-")
        + ".product.v"
        + version,
        version=version,
        package_kinds=provider.package_kinds,
        operation_kinds=provider.operation_kinds,
        inputs=inputs,
        providers=(provider,),
        steps=(
            ProfileStepDeclaration(
                selected,
                provider_key,
                tuple(RoleBinding(row.role, row.role) for row in inputs),
            ),
        ),
        terminal_result_role=result.role,
        terminal_effect_role=effect.role,
    )


def grammar_operational_contracts(stage: str) -> tuple[SemanticContractRef, ...]:
    """Complete canonical body-contract inventory; no codecs or admission issued.

    References include all inputs and the transition/result/effect, each once.
    Concrete contextual codecs must still bind the original admitted step and
    result. A coordinate inventory does not qualify those implementations.
    """
    profile = grammar_operational_profile(stage)
    provider = profile.providers[0]
    refs = {row.contract for row in profile.inputs} | {
        provider.transition_contract,
        provider.result_role.contract,
        provider.effect_role.contract,
    }
    return tuple(sorted(refs, key=lambda ref: canonical_json_bytes(ref.to_wire())))


def _stage_result(stage: str, value: object) -> SemanticValueCoordinate:
    item = _coordinate(value)
    ref = (
        GRAMMAR_PROFILE_RESULT_REF
        if stage == "profile_selection"
        else GRAMMAR_SYNTAX_BINDING_V2_REF
    )
    if item.role != "code." + stage or item.contract != ref:
        raise ContractViolation("grammar stage result reference differs")
    return item


@dataclass(frozen=True, slots=True)
class CodeGrammarSourceRoleSelectionV1:
    operation_ref: str
    stage: str
    input_digest: ContentDigest
    root_occurrence_ref: str
    profile_key: str
    profile_source: CodeGrammarDeclarationSourceV1

    def __post_init__(self) -> None:
        _ = _exact(self, CodeGrammarSourceRoleSelectionV1)
        for value in (self.operation_ref, self.root_occurrence_ref, self.profile_key):
            _ = _token(value)
        _ = _stage(self.stage)
        _ = _digest(self.input_digest)
        _ = _exact(self.profile_source, CodeGrammarDeclarationSourceV1).__post_init__()
        if self.profile_source.source_kind != "profile":
            raise ContractViolation("selection requires a profile declaration")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": "aware.code.grammar-source-role-selection.v1",
            "operation_ref": self.operation_ref,
            "stage": self.stage,
            "input_digest": self.input_digest.value,
            "root_occurrence_ref": self.root_occurrence_ref,
            "profile_key": self.profile_key,
            "profile_source": self.profile_source.to_wire(),
        }


def encode_grammar_source_role_selection(
    value: CodeGrammarSourceRoleSelectionV1,
) -> bytes:
    return _bounded(_exact(value, CodeGrammarSourceRoleSelectionV1).to_wire())


def decode_grammar_source_role_selection(
    body: bytes,
) -> CodeGrammarSourceRoleSelectionV1:
    row = _keys(
        _load(body),
        {
            "contract",
            "operation_ref",
            "stage",
            "input_digest",
            "root_occurrence_ref",
            "profile_key",
            "profile_source",
        },
        "aware.code.grammar-source-role-selection.v1",
    )
    value = CodeGrammarSourceRoleSelectionV1(
        _exact(row["operation_ref"], str),
        _exact(row["stage"], str),
        ContentDigest.of_wire(row["input_digest"]),
        _exact(row["root_occurrence_ref"], str),
        _exact(row["profile_key"], str),
        _read_declaration(row["profile_source"]),
    )
    if encode_grammar_source_role_selection(value) != body:
        raise ContractViolation("selection round trip differs")
    return value


@dataclass(frozen=True, slots=True)
class CodeGrammarReadTransitionV1:
    stage: str
    input_closure_digest: ContentDigest
    source_input_digest: ContentDigest
    result: SemanticValueCoordinate

    def __post_init__(self) -> None:
        _ = _exact(self, CodeGrammarReadTransitionV1)
        _ = _stage(self.stage)
        _ = _digest(self.input_closure_digest)
        _ = _digest(self.source_input_digest)
        _ = _stage_result(self.stage, self.result)

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": "aware.code.grammar-read-transition.v1",
            "stage": self.stage,
            "input_closure_digest": self.input_closure_digest.value,
            "source_input_digest": self.source_input_digest.value,
            "result": self.result.to_wire(),
        }


@dataclass(frozen=True, slots=True)
class CodeGrammarReadEffectV1:
    stage: str
    input_closure_digest: ContentDigest
    source_input_digest: ContentDigest
    result: SemanticValueCoordinate

    def __post_init__(self) -> None:
        _ = _exact(self, CodeGrammarReadEffectV1)
        _ = _stage(self.stage)
        _ = _digest(self.input_closure_digest)
        _ = _digest(self.source_input_digest)
        _ = _stage_result(self.stage, self.result)

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": "aware.code.grammar-read-effect.v1",
            "stage": self.stage,
            "input_closure_digest": self.input_closure_digest.value,
            "source_input_digest": self.source_input_digest.value,
            "result": self.result.to_wire(),
            "physical_effect": "none",
        }


_GRAMMAR_CONTEXT_CODEC_RECIPE = "closed contextual-only stage values above; stage/provider/result/closure/source digests must match original admitted input and known result; physical effects not inferred on failures"
GRAMMAR_READ_TRANSITION_CODEC_IMPLEMENTATION = _implementation(
    GRAMMAR_READ_TRANSITION_REF,
    "aware.code.grammar-read-transition.codec.v1",
    _GRAMMAR_CONTEXT_CODEC_RECIPE,
)
GRAMMAR_READ_EFFECT_CODEC_IMPLEMENTATION = _implementation(
    GRAMMAR_READ_EFFECT_REF,
    "aware.code.grammar-read-effect.codec.v1",
    _GRAMMAR_CONTEXT_CODEC_RECIPE,
)


def _grammar_context_value(
    context: SemanticBodyValidationContext,
    contract: SemanticContractRef,
    implementation: SemanticImplementationCoordinate,
    body: bytes,
) -> CodeGrammarReadTransitionV1 | CodeGrammarReadEffectV1:
    """Verify original Code body registration, not Workspace/host authority."""
    ctx = _exact(context, SemanticBodyValidationContext)
    ctx.__post_init__()
    purpose = "transition" if contract == GRAMMAR_READ_TRANSITION_REF else "effect"
    if ctx.purpose != purpose or ctx.coordinate.contract != contract:
        raise ContractViolation("grammar output context purpose/contract differs")
    _ = ctx._assert_registered_body(
        ctx._registered_admission_token, implementation, ctx.coordinate, body
    )
    selection = _exact(
        ctx.input_value("grammar_selection"), CodeGrammarSourceRoleSelectionV1
    )
    selection.__post_init__()
    profile = grammar_operational_profile(selection.stage)
    provider = profile.providers[0]
    if (
        ctx.provider_key != provider.provider_key
        or ctx._profile_digest != profile.digest
        or ctx.target_package.package_kind not in profile.package_kinds
        or ctx.predecessor is not None
    ):
        raise ContractViolation("grammar output provider/profile/state differs")
    if tuple(row.target_role for row in ctx.inputs) != tuple(
        row.role for row in profile.inputs
    ):
        raise ContractViolation("grammar output input roles differ")
    for observed, required in zip(ctx.inputs, profile.inputs, strict=True):
        coordinate = observed.admitted.coordinate
        if coordinate.role != required.role or coordinate.contract != required.contract:
            raise ContractViolation("grammar output input contract differs")
    result = _stage_result(selection.stage, ctx.candidate.coordinate)
    value = ctx.candidate.value
    if selection.stage == "profile_selection":
        _exact(value, SemanticContractProfileDeclaration).__post_init__()
    else:
        syntax = _exact(value, CodeGrammarSyntaxBindingV2)
        syntax.__post_init__()
        prior = next(
            row.admitted
            for row in ctx.inputs
            if row.target_role == "code.profile_selection"
        )
        prior_profile = _exact(prior.value, SemanticContractProfileDeclaration)
        if (
            syntax.interpretation_profile != prior.coordinate
            or syntax.profile_ref != prior_profile.profile_ref
            or syntax.profile_version != prior_profile.version
            or syntax.code_profile_digest != prior_profile.digest
            or syntax.profile_key != selection.profile_key
            or syntax.profile_source != selection.profile_source
        ):
            raise ContractViolation(
                "grammar syntax result differs from retained profile/selection"
            )
    transition = CodeGrammarReadTransitionV1(
        selection.stage, ctx.input_closure_digest, selection.input_digest, result
    )
    if purpose == "transition":
        return transition
    if ctx.coordinate.role != provider.effect_role.role or ctx.transition is None:
        raise ContractViolation("grammar effect lacks its original transition")
    if (
        ctx.transition.coordinate.contract != GRAMMAR_READ_TRANSITION_REF
        or ctx.transition.value != transition
    ):
        raise ContractViolation("grammar effect differs from original transition")
    return CodeGrammarReadEffectV1(
        selection.stage, ctx.input_closure_digest, selection.input_digest, result
    )


class CodeGrammarReadTransitionCodec:
    """Output codec: an original registered context is mandatory."""

    contract: SemanticContractRef = GRAMMAR_READ_TRANSITION_REF
    implementation: SemanticImplementationCoordinate = (
        GRAMMAR_READ_TRANSITION_CODEC_IMPLEMENTATION
    )

    def decode(self, body: bytes) -> object:
        _ = body
        raise ContractViolation("grammar output requires original contextual admission")

    def encode(self, value: object) -> bytes:
        _ = value
        raise ContractViolation("grammar output requires original contextual admission")

    def decode_contextual(
        self, body: bytes, context: SemanticBodyValidationContext
    ) -> CodeGrammarReadTransitionV1:
        expected = _grammar_context_value(
            context, self.contract, self.implementation, body
        )
        row = _keys(
            _load(body),
            {
                "contract",
                "stage",
                "input_closure_digest",
                "source_input_digest",
                "result",
            },
            "aware.code.grammar-read-transition.v1",
        )
        value = CodeGrammarReadTransitionV1(
            _exact(row["stage"], str),
            ContentDigest.of_wire(row["input_closure_digest"]),
            ContentDigest.of_wire(row["source_input_digest"]),
            _read_coordinate(row["result"]),
        )
        if value != expected or _bounded(value.to_wire()) != body:
            raise ContractViolation("grammar transition differs from original context")
        return value

    def encode_contextual(
        self, value: object, context: SemanticBodyValidationContext
    ) -> bytes:
        item = _exact(value, CodeGrammarReadTransitionV1)
        body = _bounded(item.to_wire())
        if item != _grammar_context_value(
            context, self.contract, self.implementation, body
        ):
            raise ContractViolation("grammar transition differs from original context")
        return body


class CodeGrammarReadEffectCodec:
    """Successful read-only effect; failures retain separate custody evidence."""

    contract: SemanticContractRef = GRAMMAR_READ_EFFECT_REF
    implementation: SemanticImplementationCoordinate = (
        GRAMMAR_READ_EFFECT_CODEC_IMPLEMENTATION
    )

    def decode(self, body: bytes) -> object:
        _ = body
        raise ContractViolation("grammar output requires original contextual admission")

    def encode(self, value: object) -> bytes:
        _ = value
        raise ContractViolation("grammar output requires original contextual admission")

    def decode_contextual(
        self, body: bytes, context: SemanticBodyValidationContext
    ) -> CodeGrammarReadEffectV1:
        expected = _grammar_context_value(
            context, self.contract, self.implementation, body
        )
        row = _keys(
            _load(body),
            {
                "contract",
                "stage",
                "input_closure_digest",
                "source_input_digest",
                "result",
                "physical_effect",
            },
            "aware.code.grammar-read-effect.v1",
        )
        if _exact(row["physical_effect"], str) != "none":
            raise ContractViolation(
                "grammar effect is not a successful read-only result"
            )
        value = CodeGrammarReadEffectV1(
            _exact(row["stage"], str),
            ContentDigest.of_wire(row["input_closure_digest"]),
            ContentDigest.of_wire(row["source_input_digest"]),
            _read_coordinate(row["result"]),
        )
        if value != expected or _bounded(value.to_wire()) != body:
            raise ContractViolation("grammar effect differs from original context")
        return value

    def encode_contextual(
        self, value: object, context: SemanticBodyValidationContext
    ) -> bytes:
        item = _exact(value, CodeGrammarReadEffectV1)
        body = _bounded(item.to_wire())
        if item != _grammar_context_value(
            context, self.contract, self.implementation, body
        ):
            raise ContractViolation("grammar effect differs from original context")
        return body


@dataclass(frozen=True, slots=True)
class CodeGrammarRoleCleanupResourceV1:
    resource_kind: str
    resource_ref: str
    status: str

    def __post_init__(self) -> None:
        _ = _exact(self, CodeGrammarRoleCleanupResourceV1)
        _ = _enum(self.resource_kind, GRAMMAR_CLEANUP_RESOURCE_KINDS)
        _ = _token(self.resource_ref)
        _ = _enum(self.status, GRAMMAR_CLEANUP_RESOURCE_STATUSES)

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": "aware.code.grammar-role-cleanup-resource.v1",
            "resource_kind": self.resource_kind,
            "resource_ref": self.resource_ref,
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class CodeGrammarRoleCleanupReceiptV1:
    attempt_ref: str | None
    operation_ref: str | None
    profile_input_digest: ContentDigest | None
    syntax_input_digest: ContentDigest | None
    cause: str
    work_state: str
    epoch_state: str
    resources: tuple[CodeGrammarRoleCleanupResourceV1, ...]
    completion: str

    def __post_init__(self) -> None:
        _ = _exact(self, CodeGrammarRoleCleanupReceiptV1)
        for value in (self.attempt_ref, self.operation_ref):
            if value is not None:
                _ = _token(value)
        for value in (self.profile_input_digest, self.syntax_input_digest):
            if value is not None:
                _ = _digest(value)
        _ = _enum(self.cause, GRAMMAR_CLEANUP_CAUSES)
        _ = _enum(self.work_state, GRAMMAR_CLEANUP_WORK_STATES)
        _ = _enum(self.epoch_state, GRAMMAR_CLEANUP_EPOCH_STATES)
        _ = _enum(self.completion, GRAMMAR_CLEANUP_COMPLETIONS)
        for value in _items(self.resources, 16):
            _ = _exact(value, CodeGrammarRoleCleanupResourceV1).__post_init__()
        _ordered(
            tuple(
                (r.resource_kind.encode(), r.resource_ref.encode())
                for r in self.resources
            )
        )
        has_input = (
            self.profile_input_digest is not None
            or self.syntax_input_digest is not None
        )
        if (has_input or self.resources) and self.attempt_ref is None:
            raise ContractViolation(
                "cleanup evidence needs original attempt correlation"
            )
        if has_input and self.operation_ref is None:
            raise ContractViolation("cleanup input digests need operation correlation")
        settled = (
            self.work_state in {"not_started", "quiescent"}
            and self.epoch_state in {"not_started", "finished"}
            and all(r.status in {"not_acquired", "released"} for r in self.resources)
        )
        if (self.completion == "verified") != settled:
            raise ContractViolation(
                "cleanup completion contradicts its complete evidence"
            )
        _ = _bounded(self._wire(), 65_536)

    def _wire(self) -> dict[str, object]:
        return {
            "contract": "aware.code.grammar-role-cleanup-receipt.v1",
            "attempt_ref": self.attempt_ref,
            "operation_ref": self.operation_ref,
            "profile_input_digest": None
            if self.profile_input_digest is None
            else self.profile_input_digest.value,
            "syntax_input_digest": None
            if self.syntax_input_digest is None
            else self.syntax_input_digest.value,
            "cause": self.cause,
            "work_state": self.work_state,
            "epoch_state": self.epoch_state,
            "resources": [r.to_wire() for r in self.resources],
            "completion": self.completion,
        }

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return self._wire()


@dataclass(frozen=True, slots=True)
class CodeGrammarRoleFailureEvidenceV1:
    phase: str
    reason: str
    results_state: str
    known_results: tuple[SemanticValueCoordinate, ...]
    cleanup: CodeGrammarRoleCleanupReceiptV1

    def __post_init__(self) -> None:
        _ = _exact(self, CodeGrammarRoleFailureEvidenceV1)
        _ = _enum(self.phase, GRAMMAR_FAILURE_PHASES)
        _ = _enum(self.reason, GRAMMAR_FAILURE_REASONS)
        _ = _enum(self.results_state, GRAMMAR_FAILURE_RESULT_STATES)
        _ = _exact(self.cleanup, CodeGrammarRoleCleanupReceiptV1).__post_init__()
        for value in _items(self.known_results, 2):
            _ = _coordinate(value)
        _ordered(tuple(canonical_json_bytes(c.to_wire()) for c in self.known_results))
        known: set[str] = set()
        for coord in self.known_results:
            if (
                coord.role not in {"code.profile_selection", "code.syntax_binding"}
                or coord.role in known
            ):
                raise ContractViolation("failure known-result roles differ")
            _ = _stage_result(coord.role.removeprefix("code."), coord)
            known.add(coord.role)
        if self.results_state == "known" and not known:
            raise ContractViolation("known results state needs a known result")
        if self.results_state == "not_started" and known:
            raise ContractViolation("not-started failure cannot carry a known result")
        if (
            "code.profile_selection" in known
            and self.cleanup.profile_input_digest is None
        ):
            raise ContractViolation("known profile needs its original input digest")
        if "code.syntax_binding" in known and (
            "code.profile_selection" not in known
            or self.cleanup.syntax_input_digest is None
        ):
            raise ContractViolation(
                "known syntax needs original input and known profile predecessor"
            )
        _ = _bounded(self._wire(), 131_072)

    def _wire(self) -> dict[str, object]:
        return {
            "contract": "aware.code.grammar-role-failure-evidence.v1",
            "phase": self.phase,
            "reason": self.reason,
            "results_state": self.results_state,
            "known_results": [c.to_wire() for c in self.known_results],
            "cleanup": self.cleanup.to_wire(),
        }

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return self._wire()


def _read_cleanup(value: object) -> CodeGrammarRoleCleanupReceiptV1:
    row = _keys(
        value,
        {
            "contract",
            "attempt_ref",
            "operation_ref",
            "profile_input_digest",
            "syntax_input_digest",
            "cause",
            "work_state",
            "epoch_state",
            "resources",
            "completion",
        },
        "aware.code.grammar-role-cleanup-receipt.v1",
    )
    resources: list[CodeGrammarRoleCleanupResourceV1] = []
    for item in _list(row["resources"], 16):
        resource = _keys(
            item,
            {"contract", "resource_kind", "resource_ref", "status"},
            "aware.code.grammar-role-cleanup-resource.v1",
        )
        resources.append(
            CodeGrammarRoleCleanupResourceV1(
                _exact(resource["resource_kind"], str),
                _exact(resource["resource_ref"], str),
                _exact(resource["status"], str),
            )
        )
    return CodeGrammarRoleCleanupReceiptV1(
        None if row["attempt_ref"] is None else _exact(row["attempt_ref"], str),
        None if row["operation_ref"] is None else _exact(row["operation_ref"], str),
        None
        if row["profile_input_digest"] is None
        else ContentDigest.of_wire(row["profile_input_digest"]),
        None
        if row["syntax_input_digest"] is None
        else ContentDigest.of_wire(row["syntax_input_digest"]),
        _exact(row["cause"], str),
        _exact(row["work_state"], str),
        _exact(row["epoch_state"], str),
        tuple(resources),
        _exact(row["completion"], str),
    )


def encode_grammar_role_cleanup(value: CodeGrammarRoleCleanupReceiptV1) -> bytes:
    return _bounded(_exact(value, CodeGrammarRoleCleanupReceiptV1).to_wire(), 65_536)


def decode_grammar_role_cleanup(body: bytes) -> CodeGrammarRoleCleanupReceiptV1:
    value = _read_cleanup(_load(body, 65_536))
    if encode_grammar_role_cleanup(value) != body:
        raise ContractViolation("cleanup round trip differs")
    return value


def encode_grammar_role_failure(value: CodeGrammarRoleFailureEvidenceV1) -> bytes:
    return _bounded(_exact(value, CodeGrammarRoleFailureEvidenceV1).to_wire(), 131_072)


def decode_grammar_role_failure(body: bytes) -> CodeGrammarRoleFailureEvidenceV1:
    row = _keys(
        _load(body, 131_072),
        {"contract", "phase", "reason", "results_state", "known_results", "cleanup"},
        "aware.code.grammar-role-failure-evidence.v1",
    )
    value = CodeGrammarRoleFailureEvidenceV1(
        _exact(row["phase"], str),
        _exact(row["reason"], str),
        _exact(row["results_state"], str),
        tuple(_read_coordinate(v) for v in _list(row["known_results"], 2)),
        _read_cleanup(row["cleanup"]),
    )
    if encode_grammar_role_failure(value) != body:
        raise ContractViolation("failure round trip differs")
    return value
