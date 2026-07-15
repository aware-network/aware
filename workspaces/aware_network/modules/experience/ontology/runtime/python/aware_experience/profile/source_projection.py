from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Literal

from aware_code.semantic_capability import SemanticCapabilityTypedOperation
from aware_code_service_dto.code.features.grammar_anchor_binding import (
    CodeGrammarAnchorBinding,
    CodeGrammarAnchorBindingDirection,
    CodeGraphFieldSelector,
)
from aware_code_service_dto.code.features.grammar_anchor_render_delta import (
    CodeGrammarAnchorRenderReplacement,
    CodeGrammarAnchorRenderSemanticValue,
    CodeGrammarAnchorRenderSemanticValueKind,
    CodeGrammarAnchorRenderSource,
    ResolveCodeGrammarAnchorRenderDeltaRequest,
)
from aware_code_service_dto.code.features.package_distribution import CodeLanguage
from aware_code_service_dto.code.features.semantic_source_meaning import (
    CodeSemanticSourceMeaningTemplateValueBinding,
)
from aware_types import JsonObject

from aware_experience.profile.semantic_operation_resolution import (
    EXPERIENCE_PROFILE_TITLE_UPDATE_OPERATION,
)
from aware_experience.profile.source_projection_contract import (
    EXPERIENCE_PROFILE_SOURCE_PROJECTION_CAPABILITY,
    EXPERIENCE_PROFILE_SOURCE_PROJECTION_CONTRACT_VERSION,
)
from aware_experience.semantic_contract import (
    EXPERIENCE_PROFILE_SOURCE_MEANING_CONTRACT,
)


ExperienceProfileSourceProjectionStatus = Literal["ready", "blocked"]
[_PROFILE_TITLE_SOURCE_MEANING_BINDING] = (
    EXPERIENCE_PROFILE_SOURCE_MEANING_CONTRACT.bindings
)


@dataclass(frozen=True, slots=True)
class ExperienceProfileSourceProjectionResolution:
    status: ExperienceProfileSourceProjectionStatus
    reason: str
    request: ResolveCodeGrammarAnchorRenderDeltaRequest | None = None
    blockers: tuple[str, ...] = ()
    operation_keys: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    @property
    def ready(self) -> bool:
        return self.status == "ready" and self.request is not None

    def provider_delta_result(
        self,
        *,
        package_name: str,
        source_session_context: Mapping[str, object] | None = None,
        commit_ids: Sequence[str] = (),
        head_commit_ids: Sequence[str] = (),
    ) -> dict[str, object]:
        stage: dict[str, object] = {
            "stage_kind": "semantic_operation_source_projection",
            "contract_version": EXPERIENCE_PROFILE_SOURCE_PROJECTION_CONTRACT_VERSION,
            "provider_key": "aware_experience",
            "semantic_owner": "aware_experience.profile",
            "status": self.status,
            "reason": self.reason,
            "ready": self.ready,
            "projected": self.ready,
            "blockers": self.blockers,
            "blocker_count": len(self.blockers),
            "operation_keys": self.operation_keys,
            "metadata": dict(self.metadata),
        }
        if self.request is not None:
            stage["grammar_anchor_render_delta_request"] = self.request.model_dump(
                mode="json",
                exclude_none=True,
            )
        return {
            "provider_key": "aware_experience",
            "package_name": package_name,
            "status": "succeeded" if self.ready else "blocked",
            "commit_ids": tuple(commit_ids),
            "head_commit_ids": tuple(head_commit_ids),
            "semantic_source_session_context": dict(source_session_context or {}),
            "details": {"provider_delta_source_projection": stage},
        }


def resolve_experience_profile_source_projection(
    *,
    typed_operations: Iterable[
        SemanticCapabilityTypedOperation | Mapping[str, object]
    ],
    package_name: str,
    package_root: str,
    sources_root: str,
    source_text_by_ref: Mapping[str, str],
    baseline_fingerprint: str | None = None,
) -> ExperienceProfileSourceProjectionResolution:
    operations = tuple(_operation_payload(item) for item in typed_operations)
    supported = tuple(
        operation
        for operation in operations
        if _text(operation.get("semantic_operation_type"))
        == EXPERIENCE_PROFILE_TITLE_UPDATE_OPERATION
    )
    if not supported:
        return _blocked(
            reason="experience_profile_source_projection_operation_unsupported",
            blockers=("experience_profile_source_projection_operation_unsupported",),
        )

    bindings: list[CodeGrammarAnchorBinding] = []
    sources_by_key: dict[str, CodeGrammarAnchorRenderSource] = {}
    replacements: list[CodeGrammarAnchorRenderReplacement] = []
    operation_keys: list[str] = []
    for operation in supported:
        operation_key = _text(operation.get("operation_key"))
        operation_keys.append(operation_key)
        operation_family = _text(operation.get("operation_family"))
        if operation_family != "update":
            return _blocked(
                reason="experience_profile_source_projection_update_required",
                blockers=("experience_profile_source_projection_update_required",),
                operation_keys=tuple(operation_keys),
            )
        semantic_key = _text(operation.get("semantic_key"))
        source_ref = _single_source_ref(operation.get("source_refs"))
        after_payload = _mapping(operation.get("after_payload"))
        title = after_payload.get("title")
        if not semantic_key or source_ref is None or not isinstance(title, str):
            return _blocked(
                reason="experience_profile_source_projection_context_incomplete",
                blockers=("experience_profile_source_projection_context_incomplete",),
                operation_keys=tuple(operation_keys),
            )
        source_text = source_text_by_ref.get(source_ref)
        if source_text is None:
            return _blocked(
                reason="experience_profile_source_projection_source_text_missing",
                blockers=("experience_profile_source_projection_source_text_missing",),
                operation_keys=tuple(operation_keys),
            )

        meaning_binding = _PROFILE_TITLE_SOURCE_MEANING_BINDING
        binding_key = f"{meaning_binding.binding_key}:{semantic_key}"
        bindings.append(
            CodeGrammarAnchorBinding(
                binding_key=binding_key,
                language=meaning_binding.language,
                grammar_profile_key=(
                    meaning_binding.grammar_profile_key
                    or EXPERIENCE_PROFILE_SOURCE_MEANING_CONTRACT.grammar_profile_key
                ),
                provider_key="aware_experience",
                lane_key="aware_experience.profile.source_projection",
                grammar_rule_name=meaning_binding.grammar_rule_name,
                anchor_field_path=meaning_binding.anchor_field_path,
                anchor_role=(
                    meaning_binding.anchor_role or "graph_attribute_value"
                ),
                graph_selector=CodeGraphFieldSelector.model_validate(
                    {
                        **meaning_binding.graph_selector.evidence_payload(),
                        "semantic_key": semantic_key,
                    }
                ),
                semantic_key_template=meaning_binding.semantic_key_template,
                template_value_bindings=[
                    CodeSemanticSourceMeaningTemplateValueBinding(
                        value_key=item.value_key,
                        grammar_rule_name=item.grammar_rule_name,
                        field_path=item.field_path,
                        required=item.required,
                    )
                    for item in meaning_binding.template_value_bindings
                ],
                value_domain=meaning_binding.value_domain or "text",
                direction=CodeGrammarAnchorBindingDirection.graph_to_source,
                renderer_key="aware.grammar_anchor",
            )
        )
        sources_by_key.setdefault(
            source_ref,
            CodeGrammarAnchorRenderSource(
                source_key=source_ref,
                language=CodeLanguage.aware,
                relative_path=source_ref,
                source_text=source_text,
                before_hash=_sha256_text(source_text),
            ),
        )
        replacements.append(
            CodeGrammarAnchorRenderReplacement(
                replacement_key=f"{operation_key}.profile_title",
                binding_key=binding_key,
                source_key=source_ref,
                semantic_value=CodeGrammarAnchorRenderSemanticValue(
                    kind=CodeGrammarAnchorRenderSemanticValueKind.string,
                    string_value=title,
                ),
                event_ref=_optional_text(operation.get("event_key")),
                semantic_key=semantic_key,
            )
        )

    request = ResolveCodeGrammarAnchorRenderDeltaRequest(
        package_name=package_name,
        package_root=package_root,
        sources_root=sources_root,
        baseline_fingerprint=baseline_fingerprint,
        bindings=bindings,
        sources=list(sources_by_key.values()),
        replacements=replacements,
        strict=True,
        metadata=JsonObject(
            {
                "source": "aware_experience.profile.source_projection",
                "semantic_apply_head_required": True,
            }
        ),
    )
    return ExperienceProfileSourceProjectionResolution(
        status="ready",
        reason="experience_profile_title_grammar_anchor_render_request_ready",
        request=request,
        operation_keys=tuple(operation_keys),
        metadata={"binding_count": len(bindings)},
    )


def _blocked(
    *,
    reason: str,
    blockers: tuple[str, ...],
    operation_keys: tuple[str, ...] = (),
) -> ExperienceProfileSourceProjectionResolution:
    return ExperienceProfileSourceProjectionResolution(
        status="blocked",
        reason=reason,
        blockers=blockers,
        operation_keys=operation_keys,
    )


def _operation_payload(
    operation: SemanticCapabilityTypedOperation | Mapping[str, object],
) -> Mapping[str, object]:
    if isinstance(operation, SemanticCapabilityTypedOperation):
        return operation.evidence_payload()
    return operation


def _single_source_ref(value: object) -> str | None:
    if not isinstance(value, (tuple, list)):
        return None
    refs = tuple(item.strip() for item in value if isinstance(item, str) and item.strip())
    return refs[0] if len(refs) == 1 else None


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _optional_text(value: object) -> str | None:
    text = _text(value)
    return text or None


def _sha256_text(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"


__all__ = [
    "EXPERIENCE_PROFILE_SOURCE_PROJECTION_CAPABILITY",
    "EXPERIENCE_PROFILE_SOURCE_PROJECTION_CONTRACT_VERSION",
    "ExperienceProfileSourceProjectionResolution",
    "resolve_experience_profile_source_projection",
]
