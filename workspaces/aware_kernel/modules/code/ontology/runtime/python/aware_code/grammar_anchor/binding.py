from __future__ import annotations

from collections.abc import Iterable, Mapping
from hashlib import sha256
from typing import cast

from aware_code_service_dto.code.features.grammar_anchor_binding import (
    CodeGrammarAnchorBinding,
    CodeGrammarAnchorBindingResolutionStatus,
    CodeGrammarAnchorFixture,
    CodeGrammarAnchorGraphChangeDraft,
    CodeGrammarAnchorTextEvidence,
    CodeGrammarAnchorTextTargetEvidence,
    ResolveCodeGrammarAnchorBindingEvidenceRequest,
    ResolveCodeGrammarAnchorBindingEvidenceResponse,
    ValidateCodeGrammarAnchorBindingRequest,
    ValidateCodeGrammarAnchorBindingResponse,
)
from aware_code.source_index import (
    CodeGrammarAnchorQuery,
    CodeGrammarGraphSelector,
    CodeGrammarSource,
    CodeGrammarSourceIndex,
)
from aware_grammar.semantic_profile import validate_aware_grammar_rule
from aware_types import JsonObject


def validate_code_grammar_anchor_binding(
    *,
    request: ValidateCodeGrammarAnchorBindingRequest,
) -> ValidateCodeGrammarAnchorBindingResponse:
    diagnostics = _validate_bindings(
        bindings=request.bindings,
        strict=request.strict,
    )
    evidence, evidence_diagnostics = _resolve_fixture_evidence(
        bindings=request.bindings,
        fixtures=request.fixtures,
        strict=request.strict,
    )
    diagnostics.extend(evidence_diagnostics)
    valid = not diagnostics
    return ValidateCodeGrammarAnchorBindingResponse(
        request_id=request.request_id,
        success=valid,
        valid=valid,
        status=(
            CodeGrammarAnchorBindingResolutionStatus.resolved
            if valid
            else CodeGrammarAnchorBindingResolutionStatus.blocked
        ),
        diagnostics=diagnostics,
        binding_count=len(request.bindings),
        fixture_count=len(request.fixtures),
        evidence=evidence,
        error=diagnostics[0] if diagnostics else None,
    )


def resolve_code_grammar_anchor_binding_evidence(
    *,
    request: ResolveCodeGrammarAnchorBindingEvidenceRequest,
) -> ResolveCodeGrammarAnchorBindingEvidenceResponse:
    diagnostics = _validate_bindings(
        bindings=request.bindings,
        strict=request.strict,
    )
    evidence, evidence_diagnostics = _resolve_fixture_evidence(
        bindings=request.bindings,
        fixtures=request.fixtures,
        strict=request.strict,
    )
    diagnostics.extend(evidence_diagnostics)

    graph_change_drafts = [
        CodeGrammarAnchorGraphChangeDraft(
            binding_key=item.binding_key,
            graph_selector=binding.graph_selector,
            after_value=item.text,
            text_evidence=item,
            metadata=JsonObject(
                {
                    "source": "aware_code.grammar_anchor.binding",
                    "draft_kind": "source_token_to_graph_attribute",
                }
            ),
        )
        for item in evidence
        if (binding := _binding_by_key(request.bindings).get(item.binding_key))
        is not None
    ]
    replacement_values = _replacement_values(request.replacement_values)
    text_targets = [
        _text_target_for_evidence(
            evidence=item,
            binding=binding,
            replacement_text=replacement_values.get(item.binding_key, item.text),
        )
        for item in evidence
        if (binding := _binding_by_key(request.bindings).get(item.binding_key))
        is not None
    ]
    resolved = not diagnostics and bool(evidence)
    return ResolveCodeGrammarAnchorBindingEvidenceResponse(
        request_id=request.request_id,
        success=resolved,
        resolved=resolved,
        status=(
            CodeGrammarAnchorBindingResolutionStatus.resolved
            if resolved
            else CodeGrammarAnchorBindingResolutionStatus.blocked
        ),
        diagnostics=diagnostics,
        evidence=evidence,
        graph_change_drafts=graph_change_drafts,
        text_targets=text_targets,
        binding_count=len(request.bindings),
        fixture_count=len(request.fixtures),
        evidence_count=len(evidence),
        error=diagnostics[0] if diagnostics else None,
    )


def _validate_bindings(
    *,
    bindings: Iterable[CodeGrammarAnchorBinding],
    strict: bool,
) -> list[str]:
    diagnostics: list[str] = []
    seen_keys: set[str] = set()
    bindings_tuple = tuple(bindings)
    if strict and not bindings_tuple:
        diagnostics.append("bindings must include at least one grammar anchor binding.")
    for index, binding in enumerate(bindings_tuple):
        prefix = f"bindings[{index}]"
        if not binding.binding_key.strip():
            diagnostics.append(f"{prefix}.binding_key is required.")
        elif binding.binding_key in seen_keys:
            diagnostics.append(
                f"{prefix}.binding_key {binding.binding_key!r} is duplicated."
            )
        seen_keys.add(binding.binding_key)
        if binding.language != "aware":
            diagnostics.append(f"{prefix}.language must be 'aware'.")
        if not binding.grammar_rule_name.strip():
            diagnostics.append(f"{prefix}.grammar_rule_name is required.")
        elif not validate_aware_grammar_rule(binding.grammar_rule_name):
            diagnostics.append(
                f"{prefix}.grammar_rule_name {binding.grammar_rule_name!r} "
                "is not exposed by the active aware tree-sitter backend."
            )
        if not binding.anchor_field_path.strip():
            diagnostics.append(f"{prefix}.anchor_field_path is required.")
        if not _selector_has_attribute_anchor(binding):
            diagnostics.append(
                f"{prefix}.graph_selector must include "
                "a generic subject/field selector or "
                "class_config_attribute_config_id or class_fqn/class_name plus "
                "attribute_name/attribute_path."
            )
    return diagnostics


def _selector_has_attribute_anchor(binding: CodeGrammarAnchorBinding) -> bool:
    selector = binding.graph_selector
    if _selector_has_generic_field_anchor(selector):
        return True
    if selector.class_config_attribute_config_id is not None:
        return True
    has_class = bool((selector.class_fqn or selector.class_name or "").strip())
    has_attribute = bool(
        (selector.attribute_name or selector.attribute_path or "").strip()
    )
    return has_class and has_attribute


def _selector_has_generic_field_anchor(selector: object) -> bool:
    field_path = getattr(selector, "field_path", None)
    field_name = getattr(selector, "field_name", None)
    has_field = bool(
        (field_path if isinstance(field_path, str) else "")
        or (field_name if isinstance(field_name, str) else "")
    )
    if not has_field:
        return False
    for attr_name in (
        "semantic_key",
        "object_key",
        "subject_type",
        "subject_kind",
        "class_fqn",
        "class_name",
    ):
        value = getattr(selector, attr_name, None)
        if isinstance(value, str) and value.strip():
            return True
    return False


def _resolve_fixture_evidence(
    *,
    bindings: Iterable[CodeGrammarAnchorBinding],
    fixtures: Iterable[CodeGrammarAnchorFixture],
    strict: bool,
) -> tuple[list[CodeGrammarAnchorTextEvidence], list[str]]:
    bindings_by_key = _binding_by_key(bindings)
    fixtures_tuple = tuple(fixtures)
    diagnostics: list[str] = []
    evidence: list[CodeGrammarAnchorTextEvidence] = []
    if strict and bindings_by_key and not fixtures_tuple:
        return evidence, []
    for fixture_index, fixture in enumerate(fixtures_tuple):
        fixture_bindings = _fixture_bindings(
            fixture=fixture,
            bindings_by_key=bindings_by_key,
            diagnostics=diagnostics,
            fixture_index=fixture_index,
        )
        if not fixture_bindings:
            continue
        source_index = CodeGrammarSourceIndex.from_sources(
            (
                CodeGrammarSource(
                    source_key=fixture.fixture_key,
                    source_text=fixture.source_text,
                    grammar_profile_key=_fixture_grammar_profile_key(
                        fixture_bindings,
                    ),
                ),
            )
        )
        for binding in fixture_bindings:
            resolved = _evidence_for_binding(
                binding=binding,
                fixture=fixture,
                source_index=source_index,
            )
            if resolved is None:
                diagnostics.append(
                    "fixtures["
                    f"{fixture_index}].{binding.binding_key} did not resolve "
                    f"{binding.grammar_rule_name}.{binding.anchor_field_path}."
                )
                continue
            if (
                fixture.expected_text is not None
                and resolved.text != fixture.expected_text
            ):
                diagnostics.append(
                    "fixtures["
                    f"{fixture_index}].expected_text mismatch for "
                    f"{binding.binding_key}: expected {fixture.expected_text!r}, "
                    f"resolved {resolved.text!r}."
                )
                continue
            evidence.append(resolved)
    return evidence, diagnostics


def _fixture_bindings(
    *,
    fixture: CodeGrammarAnchorFixture,
    bindings_by_key: Mapping[str, CodeGrammarAnchorBinding],
    diagnostics: list[str],
    fixture_index: int,
) -> tuple[CodeGrammarAnchorBinding, ...]:
    binding_key = fixture.binding_key.strip() if fixture.binding_key else None
    if binding_key:
        binding = bindings_by_key.get(binding_key)
        if binding is None:
            diagnostics.append(
                f"fixtures[{fixture_index}].binding_key {binding_key!r} "
                "does not match a binding."
            )
            return ()
        return (binding,)
    return tuple(bindings_by_key.values())


def _evidence_for_binding(
    *,
    binding: CodeGrammarAnchorBinding,
    fixture: CodeGrammarAnchorFixture,
    source_index: CodeGrammarSourceIndex,
) -> CodeGrammarAnchorTextEvidence | None:
    return resolve_code_grammar_anchor_text_evidence_from_source_index(
        binding=binding,
        source_index=source_index,
        source_key=fixture.fixture_key,
        fixture_key=fixture.fixture_key,
    )


def resolve_code_grammar_anchor_text_evidence_from_source_index(
    *,
    binding: CodeGrammarAnchorBinding,
    source_index: CodeGrammarSourceIndex,
    source_key: str | None = None,
    fixture_key: str | None = None,
) -> CodeGrammarAnchorTextEvidence | None:
    resolution = source_index.resolve_anchor(
        query=_query_from_binding(binding),
        source_key=source_key,
    )
    if resolution is None:
        return None
    return CodeGrammarAnchorTextEvidence(
        binding_key=binding.binding_key,
        fixture_key=fixture_key,
        language=resolution.language,
        grammar_rule_name=resolution.grammar_rule_name,
        anchor_field_path=resolution.anchor_field_path,
        parser_node_kind=resolution.parser_node_kind,
        anchor_node_kind=resolution.anchor_node_kind,
        relative_path=resolution.relative_path,
        byte_start=resolution.byte_start,
        byte_end=resolution.byte_end,
        text=resolution.text,
        text_hash=resolution.text_hash,
        metadata=JsonObject(
            {
                "source": "aware_code.grammar_anchor.binding",
                "source_index": resolution.evidence_payload(),
                "anchor_role": binding.anchor_role,
                "value_domain": binding.value_domain,
                "direction": _enum_text(binding.direction),
                "graph_selector": binding.graph_selector.model_dump(
                    mode="json",
                    exclude_none=True,
                ),
            }
        ),
    )


def _query_from_binding(
    binding: CodeGrammarAnchorBinding,
) -> CodeGrammarAnchorQuery:
    return CodeGrammarAnchorQuery(
        binding_key=binding.binding_key,
        language=binding.language,
        grammar_profile_key=binding.grammar_profile_key,
        grammar_rule_name=binding.grammar_rule_name,
        anchor_field_path=binding.anchor_field_path,
        graph_selector=CodeGrammarGraphSelector.from_object(binding.graph_selector),
        anchor_role=binding.anchor_role,
        value_domain=binding.value_domain,
        direction=_enum_text(binding.direction),
    )


def _fixture_grammar_profile_key(
    bindings: Iterable[CodeGrammarAnchorBinding],
) -> str | None:
    for binding in bindings:
        if binding.grammar_profile_key is not None and binding.grammar_profile_key:
            return binding.grammar_profile_key
    return None


def _text_target_for_evidence(
    *,
    evidence: CodeGrammarAnchorTextEvidence,
    binding: CodeGrammarAnchorBinding,
    replacement_text: str | None,
) -> CodeGrammarAnchorTextTargetEvidence:
    replacement = replacement_text if replacement_text is not None else evidence.text
    return CodeGrammarAnchorTextTargetEvidence(
        binding_key=evidence.binding_key,
        graph_selector=binding.graph_selector,
        text_evidence=evidence,
        replacement_text=replacement,
        before_hash=evidence.text_hash,
        after_hash=_sha256_text(replacement) if replacement is not None else None,
        metadata=JsonObject(
            {
                "source": "aware_code.grammar_anchor.binding",
                "draft_kind": "graph_attribute_to_source_token",
            }
        ),
    )


def _binding_by_key(
    bindings: Iterable[CodeGrammarAnchorBinding],
) -> dict[str, CodeGrammarAnchorBinding]:
    return {binding.binding_key: binding for binding in bindings}


def _replacement_values(value: JsonObject | None) -> dict[str, str]:
    if value is None:
        return {}
    raw = cast(Mapping[str, object], value)
    replacements: dict[str, str] = {}
    for key, item in raw.items():
        if isinstance(item, str):
            replacements[str(key)] = item
    return replacements


def _sha256_text(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _enum_text(value: object) -> str:
    raw_value = getattr(value, "value", value)
    return raw_value if isinstance(raw_value, str) else str(raw_value)


__all__ = [
    "resolve_code_grammar_anchor_binding_evidence",
    "resolve_code_grammar_anchor_text_evidence_from_source_index",
    "validate_code_grammar_anchor_binding",
]
