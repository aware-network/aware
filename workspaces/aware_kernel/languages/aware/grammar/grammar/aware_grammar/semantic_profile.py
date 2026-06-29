from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

from aware_code_ontology.code.code_section_enums import CodeSectionType
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE


class AwareGrammarSemanticProfileError(ValueError):
    """Raised when a semantic grammar profile cannot be assembled honestly."""


class AwareGrammarSyntaxLaneContract(Protocol):
    """Structural syntax-lane contract consumed by grammar profiles."""

    @property
    def lane_key(self) -> str: ...

    @property
    def semantic_owner(self) -> str: ...

    @property
    def compiler_owner(self) -> str: ...

    @property
    def grammar_rules(self) -> Sequence[str]: ...

    @property
    def semantic_token_types(self) -> Sequence[str]: ...

    @property
    def semantic_token_modifiers(self) -> Sequence[str]: ...


class AwareGrammarSemanticContract(Protocol):
    """Structural semantic-contract input consumed by grammar profiles."""

    @property
    def provider_key(self) -> str: ...

    @property
    def syntax_lanes(self) -> Sequence[AwareGrammarSyntaxLaneContract]: ...

    @property
    def grammar_rule_declarations(self) -> Sequence[object]: ...


@dataclass(frozen=True, slots=True)
class AwareGrammarRuleBinding:
    """A semantic-contract claim over one Aware tree-sitter rule."""

    rule_name: str
    provider_key: str
    lane_key: str
    semantic_owner: str
    compiler_owner: str
    code_section_type: CodeSectionType | None = None
    semantic_token_types: tuple[str, ...] = ()
    semantic_token_modifiers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AwareGrammarRuleDeclarationBinding:
    """Provider-owned declaration for one grammar rule."""

    rule_name: str
    provider_key: str
    semantic_owner: str
    language: str
    grammar_backend: str
    declared_anchor_fields: tuple[str, ...] = ()
    top_level: bool = False
    generation_status: str = "declaration_only"


@dataclass(frozen=True, slots=True)
class AwareGrammarAnchorCoverageDiagnostic:
    """Coverage diagnostic linking a source-meaning anchor to grammar truth."""

    provider_key: str
    semantic_owner: str
    binding_key: str
    grammar_rule_name: str
    anchor_field_path: str
    reason: str

    def message(self) -> str:
        return (
            f"{self.provider_key}:{self.semantic_owner}:{self.binding_key} "
            f"references {self.grammar_rule_name}.{self.anchor_field_path}: "
            f"{self.reason}"
        )


@dataclass(frozen=True, slots=True)
class AwareGrammarDeclarationCoverageProfile:
    """Semantic-contract grammar declaration coverage over the active parser."""

    profile: AwareGrammarSemanticProfile
    rule_declarations: tuple[AwareGrammarRuleDeclarationBinding, ...]
    invalid_declaration_rules: tuple[str, ...] = ()
    missing_rule_declarations: tuple[str, ...] = ()
    anchor_diagnostics: tuple[AwareGrammarAnchorCoverageDiagnostic, ...] = ()

    @property
    def diagnostics(self) -> tuple[str, ...]:
        return (
            *(
                f"grammar declaration references unknown rule: {rule}"
                for rule in self.invalid_declaration_rules
            ),
            *(
                f"syntax lane rule has no semantic grammar declaration: {rule}"
                for rule in self.missing_rule_declarations
            ),
            *(item.message() for item in self.anchor_diagnostics),
        )

    @property
    def ok(self) -> bool:
        return not self.invalid_declaration_rules and not self.anchor_diagnostics


@dataclass(frozen=True, slots=True)
class AwareGrammarSemanticProfile:
    """Assembled Aware grammar profile over the current superset parser."""

    profile_key: str
    provider_keys: tuple[str, ...]
    lane_keys: tuple[str, ...]
    rule_bindings: tuple[AwareGrammarRuleBinding, ...]
    code_section_types: tuple[CodeSectionType, ...]

    @property
    def grammar_rules(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(item.rule_name for item in self.rule_bindings))

    def bindings_for_rule(self, rule_name: str) -> tuple[AwareGrammarRuleBinding, ...]:
        return tuple(item for item in self.rule_bindings if item.rule_name == rule_name)

    def semantic_owners_for_rule(self, rule_name: str) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                item.semantic_owner for item in self.bindings_for_rule(rule_name)
            )
        )

    def code_section_type_for_rule(self, rule_name: str) -> CodeSectionType | None:
        return _AWARE_CODE_SECTION_TYPE_BY_GRAMMAR_RULE.get(rule_name)


_AWARE_CODE_SECTION_TYPE_BY_GRAMMAR_RULE: Mapping[str, CodeSectionType] = {
    "ann_def": CodeSectionType.annotation,
    "attr_def": CodeSectionType.attribute,
    "binding_def": CodeSectionType.binding,
    "class_def": CodeSectionType.class_,
    "comment": CodeSectionType.comment,
    "edge_def": CodeSectionType.class_,
    "enum_def": CodeSectionType.enum,
    "enum_value_def": CodeSectionType.enum_value,
    "fn_def": CodeSectionType.function,
    "import_stmt": CodeSectionType.import_,
    "input_attr": CodeSectionType.attribute,
    "mirror_stmt": CodeSectionType.mirror,
    "output_attr": CodeSectionType.attribute,
    "projection_def": CodeSectionType.projection,
}

_CURRENT_AWARE_CODE_SECTION_TYPES = (
    CodeSectionType.annotation,
    CodeSectionType.attribute,
    CodeSectionType.binding,
    CodeSectionType.class_,
    CodeSectionType.comment,
    CodeSectionType.enum,
    CodeSectionType.enum_value,
    CodeSectionType.function,
    CodeSectionType.import_,
    CodeSectionType.mirror,
    CodeSectionType.projection,
)


def build_aware_grammar_semantic_profile(
    *,
    profile_key: str,
    semantic_contracts: Iterable[AwareGrammarSemanticContract],
    include_current_code_sections: bool = False,
) -> AwareGrammarSemanticProfile:
    """Assemble a profile from module semantic-contract syntax lanes."""

    provider_keys: list[str] = []
    lane_keys: list[str] = []
    rule_bindings: list[AwareGrammarRuleBinding] = []
    invalid_rules: dict[str, tuple[str, ...]] = defaultdict(tuple)

    for contract in semantic_contracts:
        provider_keys.append(contract.provider_key)
        for lane in contract.syntax_lanes:
            lane_keys.append(lane.lane_key)
            _append_lane_bindings(
                contract=contract,
                lane=lane,
                rule_bindings=rule_bindings,
                invalid_rules=invalid_rules,
            )

    if invalid_rules:
        details = ", ".join(
            f"{rule} ({', '.join(sorted(lanes))})"
            for rule, lanes in sorted(invalid_rules.items())
        )
        raise AwareGrammarSemanticProfileError(
            f"Aware grammar profile {profile_key!r} references unknown rules: {details}"
        )

    code_section_types = _code_section_types_for_bindings(
        rule_bindings,
        include_current_code_sections=include_current_code_sections,
    )
    return AwareGrammarSemanticProfile(
        profile_key=profile_key,
        provider_keys=tuple(dict.fromkeys(provider_keys)),
        lane_keys=tuple(dict.fromkeys(lane_keys)),
        rule_bindings=tuple(rule_bindings),
        code_section_types=code_section_types,
    )


def build_current_aware_grammar_semantic_profile() -> AwareGrammarSemanticProfile:
    """Build the compatibility profile used by the historical singleton plugin."""

    return build_aware_grammar_semantic_profile(
        profile_key="aware_grammar.current_superset",
        semantic_contracts=(),
        include_current_code_sections=True,
    )


def build_aware_grammar_declaration_coverage_profile(
    *,
    profile_key: str,
    semantic_contracts: Iterable[AwareGrammarSemanticContract],
    source_meaning_contracts: Iterable[object] = (),
) -> AwareGrammarDeclarationCoverageProfile:
    """Assemble provider grammar declarations and validate anchor coverage."""

    contracts = tuple(semantic_contracts)
    profile = build_aware_grammar_semantic_profile(
        profile_key=profile_key,
        semantic_contracts=contracts,
    )
    rule_declarations = tuple(
        declaration
        for contract in contracts
        for declaration in _rule_declarations_for_contract(contract)
    )
    invalid_declaration_rules = tuple(
        dict.fromkeys(
            item.rule_name
            for item in rule_declarations
            if not validate_aware_grammar_rule(item.rule_name)
        )
    )
    declaration_keys = {
        (item.provider_key, item.semantic_owner, item.rule_name)
        for item in rule_declarations
    }
    missing_rule_declarations = tuple(
        dict.fromkeys(
            f"{item.provider_key}:{item.semantic_owner}:{item.rule_name}"
            for item in profile.rule_bindings
            if (item.provider_key, item.semantic_owner, item.rule_name)
            not in declaration_keys
        )
    )
    anchor_diagnostics = tuple(
        diagnostic
        for contract in source_meaning_contracts
        for diagnostic in _anchor_coverage_diagnostics(
            source_meaning_contract=contract,
            rule_declarations=rule_declarations,
        )
    )
    return AwareGrammarDeclarationCoverageProfile(
        profile=profile,
        rule_declarations=rule_declarations,
        invalid_declaration_rules=invalid_declaration_rules,
        missing_rule_declarations=missing_rule_declarations,
        anchor_diagnostics=anchor_diagnostics,
    )


def validate_aware_grammar_rule(rule_name: str) -> bool:
    """Return True when the current tree-sitter parser exposes a named rule."""

    try:
        AWARE_LANGUAGE.query(f"({rule_name}) @node")
    except Exception:
        return False
    return True


def _rule_declarations_for_contract(
    contract: AwareGrammarSemanticContract,
) -> tuple[AwareGrammarRuleDeclarationBinding, ...]:
    provider_key = contract.provider_key
    return tuple(
        AwareGrammarRuleDeclarationBinding(
            rule_name=_required_text(descriptor, "rule_name"),
            provider_key=provider_key,
            semantic_owner=_required_text(descriptor, "semantic_owner"),
            language=_optional_text(descriptor, "language") or "aware",
            grammar_backend=(
                _optional_text(descriptor, "grammar_backend") or "tree_sitter.aware"
            ),
            declared_anchor_fields=_declared_anchor_fields(descriptor),
            top_level=_optional_bool(descriptor, "top_level"),
            generation_status=(
                _optional_text(descriptor, "generation_status") or "declaration_only"
            ),
        )
        for descriptor in getattr(contract, "grammar_rule_declarations", ())
    )


def _anchor_coverage_diagnostics(
    *,
    source_meaning_contract: object,
    rule_declarations: tuple[AwareGrammarRuleDeclarationBinding, ...],
) -> tuple[AwareGrammarAnchorCoverageDiagnostic, ...]:
    provider_key = _required_text(source_meaning_contract, "provider_key")
    semantic_owner = _required_text(source_meaning_contract, "semantic_owner")
    declarations_by_rule = {
        item.rule_name: item
        for item in rule_declarations
        if item.provider_key == provider_key and item.semantic_owner == semantic_owner
    }
    diagnostics: list[AwareGrammarAnchorCoverageDiagnostic] = []
    for binding in _source_meaning_bindings(source_meaning_contract):
        grammar_rule_name = _required_text(binding, "grammar_rule_name")
        anchor_field_path = _required_text(binding, "anchor_field_path")
        declaration = declarations_by_rule.get(grammar_rule_name)
        if declaration is None:
            reason = "no provider-owned grammar declaration for rule"
        elif anchor_field_path not in declaration.declared_anchor_fields:
            reason = "anchor field is not declared by provider grammar rule"
        else:
            continue
        diagnostics.append(
            AwareGrammarAnchorCoverageDiagnostic(
                provider_key=provider_key,
                semantic_owner=semantic_owner,
                binding_key=_optional_text(binding, "binding_key") or "<unknown>",
                grammar_rule_name=grammar_rule_name,
                anchor_field_path=anchor_field_path,
                reason=reason,
            )
        )
    return tuple(diagnostics)


def _source_meaning_bindings(source_meaning_contract: object) -> tuple[object, ...]:
    if isinstance(source_meaning_contract, Mapping):
        bindings = source_meaning_contract.get("bindings", ())
    else:
        bindings = getattr(source_meaning_contract, "bindings", ())
    if isinstance(bindings, tuple):
        return bindings
    if isinstance(bindings, list):
        return tuple(bindings)
    return tuple(bindings or ())


def _declared_anchor_fields(descriptor: object) -> tuple[str, ...]:
    declared = getattr(descriptor, "declared_anchor_fields", None)
    if declared is not None:
        return tuple(str(item) for item in declared if str(item).strip())
    fields = getattr(descriptor, "fields", ())
    source_anchor_fields = getattr(descriptor, "source_anchor_fields", ())
    return tuple(
        dict.fromkeys(
            item
            for item in (
                *(_required_text(field, "field_path") for field in tuple(fields or ())),
                *(str(item) for item in tuple(source_anchor_fields or ())),
            )
            if item.strip()
        )
    )


def _required_text(value: object, key: str) -> str:
    result = _optional_text(value, key)
    if result is None:
        raise AwareGrammarSemanticProfileError(f"{key} is required")
    return result


def _optional_text(value: object, key: str) -> str | None:
    if isinstance(value, Mapping):
        raw_value = value.get(key)
    else:
        raw_value = getattr(value, key, None)
    if raw_value is None:
        return None
    normalized = str(raw_value).strip()
    return normalized or None


def _optional_bool(value: object, key: str) -> bool:
    if isinstance(value, Mapping):
        raw_value = value.get(key)
    else:
        raw_value = getattr(value, key, None)
    return bool(raw_value)


def _append_lane_bindings(
    *,
    contract: AwareGrammarSemanticContract,
    lane: AwareGrammarSyntaxLaneContract,
    rule_bindings: list[AwareGrammarRuleBinding],
    invalid_rules: dict[str, tuple[str, ...]],
) -> None:
    for rule_name in lane.grammar_rules:
        if not validate_aware_grammar_rule(rule_name):
            invalid_rules[rule_name] = (*invalid_rules[rule_name], lane.lane_key)
            continue
        rule_bindings.append(
            AwareGrammarRuleBinding(
                rule_name=rule_name,
                provider_key=contract.provider_key,
                lane_key=lane.lane_key,
                semantic_owner=lane.semantic_owner,
                compiler_owner=lane.compiler_owner,
                code_section_type=_AWARE_CODE_SECTION_TYPE_BY_GRAMMAR_RULE.get(
                    rule_name
                ),
                semantic_token_types=tuple(lane.semantic_token_types),
                semantic_token_modifiers=tuple(lane.semantic_token_modifiers),
            )
        )


def _code_section_types_for_bindings(
    rule_bindings: Iterable[AwareGrammarRuleBinding],
    *,
    include_current_code_sections: bool,
) -> tuple[CodeSectionType, ...]:
    if include_current_code_sections:
        return _CURRENT_AWARE_CODE_SECTION_TYPES
    section_types = tuple(
        dict.fromkeys(
            item.code_section_type
            for item in rule_bindings
            if item.code_section_type is not None
        )
    )
    return tuple(item for item in section_types if item is not None)


__all__ = [
    "AwareGrammarAnchorCoverageDiagnostic",
    "AwareGrammarDeclarationCoverageProfile",
    "AwareGrammarRuleDeclarationBinding",
    "AwareGrammarRuleBinding",
    "AwareGrammarSemanticContract",
    "AwareGrammarSemanticProfile",
    "AwareGrammarSemanticProfileError",
    "AwareGrammarSyntaxLaneContract",
    "build_aware_grammar_declaration_coverage_profile",
    "build_aware_grammar_semantic_profile",
    "build_current_aware_grammar_semantic_profile",
    "validate_aware_grammar_rule",
]
