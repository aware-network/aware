from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from difflib import get_close_matches
from pathlib import Path
from re import Pattern
from typing import Protocol, cast

from tree_sitter import Node

from aware_code.language_service_provider_descriptor import (
    LanguageServiceProviderDescriptor as CapabilityProviderDescriptor,
    WorkspaceActivation,
)
from aware_code.module_plugin_registry import AwareModulePluginRegistry
from aware_code_ontology.code.code import Code

from aware_meta.fqn_resolver import FqnScope

from aware_code.language_service.capability_provider_bootstrap import (
    ensure_builtin_language_service_capability_providers_registered,
)
from aware_code.language_service.position import ByteRange, Utf16PositionMapper

from aware_workspace.compiler.workspace import WorkspaceSnapshot

from aware_code.language_service.capability_scope import (
    CapabilityExecutionScope,
    CapabilityProviderExecutionContext,
)

from .contracts import AwareDiagnostic, DiagnosticDataValue
from .defaults import DefaultsPluginContract
from .projection import (
    ProjectionAddDiagnostic,
    ProjectionLookup,
    ProjectionSuggestFn,
    build_projection_lookup,
)
from .type_mirror import TypeMirrorPluginContract


class DiagnosticsPluginContract(TypeMirrorPluginContract, DefaultsPluginContract, Protocol):
    pass


DiagnosticsCapabilityProvider = Callable[["DiagnosticsCapabilityContext"], list[AwareDiagnostic]]


@dataclass(frozen=True, slots=True)
class RegisteredDiagnosticsCapabilityProvider:
    descriptor: CapabilityProviderDescriptor
    provider: DiagnosticsCapabilityProvider


@dataclass(frozen=True, slots=True)
class DiagnosticsCapabilityContext:
    uri: str
    code: Code
    execution: CapabilityProviderExecutionContext
    snapshot: WorkspaceSnapshot
    scope: FqnScope
    mapper: Utf16PositionMapper
    document_bytes: bytes
    projection_root: Node | None
    plugin: DiagnosticsPluginContract
    class_candidates: list[str]
    enum_candidates: list[str]
    projection_lookup: ProjectionLookup
    common_primitive_tokens: tuple[str, ...]
    class_not_found_rx: Pattern[str]
    optional_list_rx: Pattern[str]
    uri_to_path: Callable[[str], Path]
    add: ProjectionAddDiagnostic
    suggest: ProjectionSuggestFn


_DIAGNOSTICS_CAPABILITY_PROVIDERS: dict[str, RegisteredDiagnosticsCapabilityProvider] = {}


def register_diagnostics_capability_provider(
    *,
    provider_key: str,
    provider: DiagnosticsCapabilityProvider,
    semantic_owner: str | None = None,
    required_semantic_scope_keys: Iterable[str] | None = None,
    priority: int = 100,
    applies_when: str = "always",
    workspace_activation: WorkspaceActivation = "owner",
) -> None:
    if provider_key not in _DIAGNOSTICS_CAPABILITY_PROVIDERS:
        _DIAGNOSTICS_CAPABILITY_PROVIDERS[provider_key] = RegisteredDiagnosticsCapabilityProvider(
            descriptor=CapabilityProviderDescriptor(
                capability="diagnostics",
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


def get_registered_diagnostics_capability_provider_keys() -> tuple[str, ...]:
    return tuple(entry.descriptor.provider_key for entry in _ordered_diagnostics_capability_providers())


def get_available_diagnostics_capability_provider_keys(
    *,
    module_provider_keys: Iterable[str] | None = None,
) -> tuple[str, ...]:
    return AwareModulePluginRegistry.get_language_service_capability_available_provider_keys(
        capability="diagnostics",
        module_provider_keys=module_provider_keys,
        overlay_provider_keys=get_registered_diagnostics_capability_provider_keys(),
    )


def get_registered_diagnostics_capability_descriptors() -> tuple[CapabilityProviderDescriptor, ...]:
    return tuple(entry.descriptor for entry in _ordered_diagnostics_capability_providers())


def clear_diagnostics_capability_providers() -> None:
    _DIAGNOSTICS_CAPABILITY_PROVIDERS.clear()


def ensure_builtin_diagnostics_capability_providers_registered() -> None:
    if _DIAGNOSTICS_CAPABILITY_PROVIDERS:
        return
    ensure_builtin_language_service_capability_providers_registered()


def _ordered_diagnostics_capability_providers() -> tuple[RegisteredDiagnosticsCapabilityProvider, ...]:
    return tuple(
        sorted(
            _DIAGNOSTICS_CAPABILITY_PROVIDERS.values(),
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


def execute_diagnostics_capabilities(
    *,
    uri: str,
    code: Code,
    snapshot: WorkspaceSnapshot,
    scope: FqnScope,
    mapper: Utf16PositionMapper,
    document_bytes: bytes,
    projection_root: Node | None,
    plugin: DiagnosticsPluginContract,
    common_primitive_tokens: tuple[str, ...],
    class_not_found_rx: Pattern[str],
    optional_list_rx: Pattern[str],
    uri_to_path: Callable[[str], Path],
    provider_execution: CapabilityProviderExecutionContext,
    execution_scope: CapabilityExecutionScope | None = None,
    provider_keys: Iterable[str] | None = None,
    overlay_descriptors: Iterable[CapabilityProviderDescriptor] = (),
    overlay_providers: Mapping[str, Callable[..., object]] | None = None,
) -> list[AwareDiagnostic]:
    diagnostics: list[AwareDiagnostic] = []

    def _suggest(value: str, options: list[str]) -> list[str]:
        v = (value or "").strip()
        if not v:
            return []
        try:
            return list(get_close_matches(v, options, n=3, cutoff=0.6))
        except Exception:
            return []

    def _add(
        *,
        rng: ByteRange,
        message: str,
        code: str | None = None,
        data: Mapping[str, DiagnosticDataValue] | None = None,
        severity: int = 1,
    ) -> None:
        start = mapper.byte_offset_to_position(rng.start)
        end = mapper.byte_offset_to_position(rng.end)
        diag: AwareDiagnostic = {
            "message": message,
            "severity": severity,
            "source": "aware",
            "range": {
                "start": {"line": start.line, "character": start.character},
                "end": {"line": end.line, "character": end.character},
            },
        }
        if code is not None:
            diag["code"] = code
        if data is not None:
            diag["data"] = data
        diagnostics.append(diag)

    def _type_ref_candidates() -> tuple[list[str], list[str]]:
        classes: set[str] = set()
        enums: set[str] = set()
        for fqn in snapshot.fqn_resolver.classes_by_fqn.keys():
            classes.add(fqn)
            parts = [p for p in fqn.split(".") if p]
            if len(parts) == 4:
                classes.add(parts[3])
                classes.add(f"{parts[2]}.{parts[3]}")
        for fqn in snapshot.fqn_resolver.enums_by_fqn.keys():
            enums.add(fqn)
            parts = [p for p in fqn.split(".") if p]
            if len(parts) == 4:
                enums.add(parts[3])
                enums.add(f"{parts[2]}.{parts[3]}")
        return sorted(classes), sorted(enums)

    class_candidates, enum_candidates = _type_ref_candidates()
    projection_lookup = build_projection_lookup(snapshot=snapshot, code=code)
    ensure_builtin_diagnostics_capability_providers_registered()
    context = DiagnosticsCapabilityContext(
        uri=uri,
        code=code,
        execution=provider_execution,
        snapshot=snapshot,
        scope=scope,
        mapper=mapper,
        document_bytes=document_bytes,
        projection_root=projection_root,
        plugin=plugin,
        class_candidates=class_candidates,
        enum_candidates=enum_candidates,
        projection_lookup=projection_lookup,
        common_primitive_tokens=common_primitive_tokens,
        class_not_found_rx=class_not_found_rx,
        optional_list_rx=optional_list_rx,
        uri_to_path=uri_to_path,
        add=_add,
        suggest=_suggest,
    )
    registered_entries = _ordered_diagnostics_capability_providers()
    selected_overlay_providers: dict[str, Callable[..., object]] = {
        entry.descriptor.provider_key: entry.provider
        for entry in registered_entries
    }
    selected_overlay_providers.update(overlay_providers or {})
    for resolved in AwareModulePluginRegistry.resolve_language_service_capability_execution_providers(
        capability="diagnostics",
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
        diagnostics_provider = cast(DiagnosticsCapabilityProvider, resolved.provider)
        diagnostics.extend(diagnostics_provider(context))

    return diagnostics
