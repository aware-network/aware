from __future__ import annotations

from abc import ABC
import re

from tree_sitter import Node

# Code Runtime
from aware_code.language.registry import CodeLanguagePluginRegistry

from aware_code.language_service.capability_scope import (
    CapabilityExecutionPlan,
    CapabilityProviderExecutionContext,
    WorkspaceCapabilityConfiguration,
)
# Language Service
from aware_code.language_service.features.base import ServiceMixinBase
from aware_code.language_service.features.diagnostics_capabilities import (
    AwareDiagnostic,
    ensure_builtin_diagnostics_capability_providers_registered,
    execute_diagnostics_capabilities,
    get_available_diagnostics_capability_provider_keys,
    get_registered_diagnostics_capability_descriptors,
)
from aware_code.language_service.programs import parse_tree

# Structure Runtime
from aware_workspace.compiler.workspace import WorkspaceSnapshot


class DiagnosticsMixin(ServiceMixinBase, ABC):
    _snapshot: WorkspaceSnapshot | None
    _workspace_capability_configuration: WorkspaceCapabilityConfiguration

    _CLASS_NOT_FOUND_RX: re.Pattern[str] = re.compile(
        r"^Class\s+(?P<identifier>.+?)\s+not found for type text\s+(?P<type_text>.+)$"
    )
    _OPTIONAL_LIST_RX: re.Pattern[str] = re.compile(r"^Optional list types are not allowed: (?P<type_text>.+)$")
    _COMMON_PRIMITIVE_TOKENS: tuple[str, ...] = (
        "Any",
        "Bool",
        "Bytes",
        "DateTime",
        "Dict[String, Any]",
        "Float",
        "Int",
        "Json",
        "JsonArray",
        "JsonObject",
        "JsonValue",
        "Null",
        "String",
        "UUID",
        "Vector",
    )

    def diagnostics_for(self, *, uri: str, allow_snapshot_rebuild: bool = True) -> list[AwareDiagnostic]:
        diagnostics: list[AwareDiagnostic] = []

        if self._snapshot is None:
            if allow_snapshot_rebuild and not self._last_build_error:
                self._ensure_snapshot_for_uri(uri=uri)
            if self._snapshot is None:
                # Avoid spamming editor diagnostics while the workspace is still indexing.
                if self._last_build_error:
                    diagnostics.append(
                        {
                            "message": self._last_build_error,
                            "severity": 1,
                            "source": "aware",
                            "range": {
                                "start": {"line": 0, "character": 0},
                                "end": {"line": 0, "character": 0},
                            },
                        }
                    )
                return diagnostics

        if self._last_build_error:
            diagnostics.append(
                {
                    "message": self._last_build_error,
                    "severity": 1,
                    "source": "aware",
                    "range": {
                        "start": {"line": 0, "character": 0},
                        "end": {"line": 0, "character": 0},
                    },
                }
            )
            return diagnostics

        if uri not in self._snapshot.codes_by_uri:
            if allow_snapshot_rebuild:
                self._ensure_snapshot_for_uri(uri=uri)
            if uri not in self._snapshot.codes_by_uri:
                return diagnostics

        code = self._snapshot.codes_by_uri.get(uri)
        if code is None:
            return diagnostics

        try:
            text = self._workspace.get_document_text(uri)
        except Exception:
            text = ""
        ctx = self._document_context(uri=uri, document_text=text)
        mapper = ctx.mapper
        doc_bytes = ctx.document_bytes
        projection_root: Node | None = None

        try:
            plugin = CodeLanguagePluginRegistry.get(self._workspace.language)
        except Exception:
            return diagnostics

        scope = self._snapshot.fqn_resolver.scope_for_code_id(code.id)
        execution_plan = self.diagnostics_capability_plan(uri=uri)
        provider_execution = CapabilityProviderExecutionContext(
            capability="diagnostics",
            uri=uri,
            workspace_root=self._workspace.workspace_root,
            document_path=self._workspace.uri_to_path(uri).resolve(),
            plan=execution_plan,
        )

        if (
            b"projection" in doc_bytes
            or b"experience" in doc_bytes
            or b"graph" in doc_bytes
            or b"role" in doc_bytes
            or b"actor" in doc_bytes
            or b"action" in doc_bytes
            or b"environment" in doc_bytes
            or b"event" in doc_bytes
        ):
            try:
                projection_root = parse_tree(document_bytes=doc_bytes)
            except Exception:
                projection_root = None

        diagnostics.extend(
            execute_diagnostics_capabilities(
                uri=uri,
                code=code,
                snapshot=self._snapshot,
                scope=scope,
                mapper=mapper,
                document_bytes=doc_bytes,
                projection_root=projection_root,
                plugin=plugin,
                common_primitive_tokens=self._COMMON_PRIMITIVE_TOKENS,
                class_not_found_rx=self._CLASS_NOT_FOUND_RX,
                optional_list_rx=self._OPTIONAL_LIST_RX,
                uri_to_path=self._workspace.uri_to_path,
                provider_execution=provider_execution,
                execution_scope=execution_plan.effective_scope,
                provider_keys=tuple(
                    provider.provider_key
                    for provider in execution_plan.providers
                    if provider.active
                ),
                overlay_descriptors=execution_plan.workspace_binding_provider_descriptors,
                overlay_providers=self._language_service_binding_overlay_providers(
                    capability="diagnostics",
                    uri=uri,
                    provider_keys=(
                        provider.provider_key
                        for provider in execution_plan.providers
                        if provider.active
                    ),
                ),
            )
        )

        return diagnostics

    def _effective_diagnostics_execution_scope(self, *, uri: str):
        return self.diagnostics_capability_plan(uri=uri).effective_scope

    def diagnostics_capability_plan(self, *, uri: str) -> CapabilityExecutionPlan:
        return self._capability_execution_plan_for_uri(
            capability="diagnostics",
            uri=uri,
            configured_selection=self._workspace_capability_configuration.diagnostics,
            ensure_providers_registered=ensure_builtin_diagnostics_capability_providers_registered,
            get_registered_descriptors=get_registered_diagnostics_capability_descriptors,
            get_available_provider_keys=get_available_diagnostics_capability_provider_keys,
        )
