from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import cast

from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.language_service_provider_descriptor import (
    LanguageServiceProviderDescriptor as CapabilityProviderDescriptor,
    WorkspaceActivation,
)
from aware_code.module_plugin_registry import AwareModulePluginRegistry
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage

from aware_code.language_service.capability_provider_bootstrap import (
    ensure_builtin_language_service_capability_providers_registered,
)
from aware_code.language_service.capability_scope import (
    CapabilityExecutionScope,
    CapabilityProviderExecutionContext,
)
from aware_code.language_service.position import Utf16PositionMapper
from aware_meta.fqn_resolver import FqnScope

from .collector import SemanticTokenCollector
from .contracts import SemanticToken, SemanticTokensContext, TOKEN_TYPES


_TOKEN_TYPE_PRECEDENCE: dict[str, int] = {
    "namespace": 60,
    "class": 90,
    "enum": 90,
    "enumMember": 85,
    "function": 88,
    "method": 88,
    "property": 96,
    "parameter": 96,
    "type": 70,
    "keyword": 40,
    "modifier": 35,
    "comment": 10,
    "string": 20,
    "number": 20,
    "operator": 30,
}

SemanticTokensCapabilityProvider = Callable[[SemanticTokenCollector], None]


@dataclass(frozen=True, slots=True)
class RegisteredSemanticTokensCapabilityProvider:
    descriptor: CapabilityProviderDescriptor
    provider: SemanticTokensCapabilityProvider


_SEMANTIC_TOKENS_CAPABILITY_PROVIDERS: dict[str, RegisteredSemanticTokensCapabilityProvider] = {}


def register_semantic_tokens_capability_provider(
    *,
    provider_key: str,
    provider: SemanticTokensCapabilityProvider,
    semantic_owner: str | None = None,
    required_semantic_scope_keys: Iterable[str] | None = None,
    priority: int = 100,
    applies_when: str = "always",
    workspace_activation: WorkspaceActivation = "owner",
) -> None:
    if provider_key not in _SEMANTIC_TOKENS_CAPABILITY_PROVIDERS:
        _SEMANTIC_TOKENS_CAPABILITY_PROVIDERS[provider_key] = RegisteredSemanticTokensCapabilityProvider(
            descriptor=CapabilityProviderDescriptor(
                capability="semantic_tokens",
                provider_key=provider_key,
                semantic_owner=semantic_owner or provider_key,
                required_semantic_scope_keys=_normalize_required_semantic_scope_keys(
                    required_semantic_scope_keys
                ),
                priority=priority,
                applies_when=applies_when,
                workspace_activation=workspace_activation,
            ),
            provider=provider,
        )


def get_registered_semantic_tokens_capability_provider_keys() -> tuple[str, ...]:
    return tuple(entry.descriptor.provider_key for entry in _ordered_semantic_tokens_capability_providers())


def get_available_semantic_tokens_capability_provider_keys(
    *,
    module_provider_keys: Iterable[str] | None = None,
) -> tuple[str, ...]:
    return AwareModulePluginRegistry.get_language_service_capability_available_provider_keys(
        capability="semantic_tokens",
        module_provider_keys=module_provider_keys,
        overlay_provider_keys=get_registered_semantic_tokens_capability_provider_keys(),
    )


def get_registered_semantic_tokens_capability_descriptors() -> tuple[CapabilityProviderDescriptor, ...]:
    return tuple(entry.descriptor for entry in _ordered_semantic_tokens_capability_providers())


def clear_semantic_tokens_capability_providers() -> None:
    _SEMANTIC_TOKENS_CAPABILITY_PROVIDERS.clear()


def ensure_builtin_semantic_tokens_capability_providers_registered() -> None:
    if _SEMANTIC_TOKENS_CAPABILITY_PROVIDERS:
        return
    ensure_builtin_language_service_capability_providers_registered()


def _ordered_semantic_tokens_capability_providers() -> tuple[RegisteredSemanticTokensCapabilityProvider, ...]:
    return tuple(
        sorted(
            _SEMANTIC_TOKENS_CAPABILITY_PROVIDERS.values(),
            key=lambda entry: entry.descriptor.priority,
        )
    )


def _normalize_required_semantic_scope_keys(
    values: Iterable[str] | None,
) -> tuple[str, ...]:
    if values is None:
        return ()
    return tuple(
        sorted(
            {
                value.strip()
                for value in values
                if isinstance(value, str) and value.strip()
            }
        )
    )


def _is_never_primitive(_value: str) -> bool:
    return False


def _primitive_type_resolver(*, language: CodeLanguage) -> Callable[[str], bool]:
    if not CodeLanguagePluginRegistry.has_language(language):
        return _is_never_primitive

    primitive_codec = CodeLanguagePluginRegistry.get(language).primitive_codec

    def _is_primitive(token: str) -> bool:
        return primitive_codec.parse(token) is not None

    return _is_primitive


def _token_priority(*, token: SemanticToken) -> tuple[int, int]:
    token_name = TOKEN_TYPES[token.token_type]
    return _TOKEN_TYPE_PRECEDENCE.get(token_name, 0), token.token_modifiers.bit_count()


def _token_end(*, token: SemanticToken) -> int:
    return token.start_char + token.length


def _winner_for_segment(*, candidates: list[SemanticToken]) -> SemanticToken:
    return max(candidates, key=lambda token: (_token_priority(token=token), token.length, token.token_type))


def _normalize_line_tokens(*, line_tokens: list[SemanticToken]) -> list[SemanticToken]:
    if not line_tokens:
        return []

    boundaries: set[int] = set()
    for token in line_tokens:
        end_char = _token_end(token=token)
        if end_char <= token.start_char:
            continue
        boundaries.add(token.start_char)
        boundaries.add(end_char)

    if len(boundaries) < 2:
        return []

    ordered = sorted(boundaries)
    normalized: list[SemanticToken] = []

    for i in range(len(ordered) - 1):
        seg_start = ordered[i]
        seg_end = ordered[i + 1]
        if seg_end <= seg_start:
            continue

        covering = [
            token
            for token in line_tokens
            if token.start_char <= seg_start and _token_end(token=token) >= seg_end
        ]
        if not covering:
            continue

        winner = _winner_for_segment(candidates=covering)
        segment_len = seg_end - seg_start

        if (
            normalized
            and normalized[-1].start_char + normalized[-1].length == seg_start
            and normalized[-1].token_type == winner.token_type
            and normalized[-1].token_modifiers == winner.token_modifiers
        ):
            previous = normalized[-1]
            normalized[-1] = SemanticToken(
                line=previous.line,
                start_char=previous.start_char,
                length=previous.length + segment_len,
                token_type=previous.token_type,
                token_modifiers=previous.token_modifiers,
            )
            continue

        normalized.append(
            SemanticToken(
                line=winner.line,
                start_char=seg_start,
                length=segment_len,
                token_type=winner.token_type,
                token_modifiers=winner.token_modifiers,
            )
        )

    return normalized


def _normalize_tokens(*, tokens: list[SemanticToken]) -> list[SemanticToken]:
    by_line: dict[int, list[SemanticToken]] = {}
    for token in tokens:
        by_line.setdefault(token.line, []).append(token)

    normalized: list[SemanticToken] = []
    for line in sorted(by_line):
        normalized.extend(_normalize_line_tokens(line_tokens=by_line[line]))

    return sorted(normalized, key=lambda token: (token.line, token.start_char))


def _encode_tokens(*, tokens: list[SemanticToken]) -> list[int]:
    data: list[int] = []
    prev_line = 0
    prev_char = 0

    for token in tokens:
        delta_line = token.line - prev_line
        delta_start = token.start_char - (prev_char if delta_line == 0 else 0)
        data.extend([delta_line, delta_start, token.length, token.token_type, token.token_modifiers])
        prev_line = token.line
        prev_char = token.start_char

    return data


def execute_semantic_tokens_capabilities(
    *,
    code: Code,
    provider_execution: CapabilityProviderExecutionContext,
    scope: FqnScope,
    mapper: Utf16PositionMapper,
    document_bytes: bytes,
    workspace_language: CodeLanguage,
    execution_scope: CapabilityExecutionScope | None = None,
    provider_keys: Iterable[str] | None = None,
    overlay_descriptors: Iterable[CapabilityProviderDescriptor] = (),
    overlay_providers: Mapping[str, Callable[..., object]] | None = None,
) -> list[int]:
    ensure_builtin_semantic_tokens_capability_providers_registered()
    context = SemanticTokensContext(
        code=code,
        execution=provider_execution,
        scope=scope,
        mapper=mapper,
        document_bytes=document_bytes,
        workspace_language=workspace_language,
        is_primitive_type=_primitive_type_resolver(language=workspace_language),
    )

    collector = SemanticTokenCollector(context=context)
    registered_entries = _ordered_semantic_tokens_capability_providers()
    selected_overlay_providers: dict[str, Callable[..., object]] = {
        entry.descriptor.provider_key: entry.provider
        for entry in registered_entries
    }
    selected_overlay_providers.update(overlay_providers or {})
    for resolved in AwareModulePluginRegistry.resolve_language_service_capability_execution_providers(
        capability="semantic_tokens",
        provider_keys=provider_keys,
        overlay_descriptors=(
            *(entry.descriptor for entry in registered_entries),
            *overlay_descriptors,
        ),
        overlay_providers=selected_overlay_providers,
        descriptor_filter=(
            (lambda descriptor: execution_scope.allows(descriptor=descriptor))
            if execution_scope is not None
            else None
        ),
    ):
        semantic_tokens_provider = cast(SemanticTokensCapabilityProvider, resolved.provider)
        semantic_tokens_provider(collector)

    normalized_tokens = _normalize_tokens(tokens=collector.tokens)
    return _encode_tokens(tokens=normalized_tokens)
