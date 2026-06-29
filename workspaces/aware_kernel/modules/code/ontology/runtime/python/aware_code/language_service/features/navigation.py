from __future__ import annotations

from pathlib import Path

# Third-party
from tree_sitter import Node
from typing_extensions import override

# Language Service
from aware_code.language_service.document import DocumentContext
from aware_code.language_service.features.base import ServiceMixinBase
from aware_code.language_service.features.navigation_capabilities.annotation import (
    collect_annotation_member_definition_target,
    collect_annotation_path_hover,
)
from aware_code.language_service.features.navigation_capabilities.api import (
    collect_api_definition_targets,
)
from aware_code.language_service.features.navigation_capabilities.environment import (
    collect_environment_definition_targets,
)
from aware_code.language_service.features.navigation_capabilities.executor import (
    collect_context_definition_targets,
    collect_program_definition_targets,
    collect_symbol_definition_targets,
)
from aware_code.language_service.features.navigation_capabilities.experience import (
    collect_experience_definition_targets,
    collect_experience_definition_targets_by_symbol,
    collect_experience_node_definition_targets_by_symbol,
    collect_experience_view_definition_targets_by_symbol,
    resolve_nearest_experience_toml_for_uri,
)
from aware_code.language_service.features.navigation_capabilities.hover import (
    collect_program_call_hover,
    collect_symbol_hover,
)
from aware_code.language_service.features.navigation_capabilities.program import (
    collect_program_call_definition_targets,
    collect_program_topology_definition_targets,
)
from aware_code.language_service.features.navigation_capabilities.projection import (
    collect_projection_definition_targets,
    collect_projection_definition_targets_by_symbol,
    collect_projection_view_definition_targets_by_symbol,
)
from aware_code.language_service.features.navigation_capabilities.role_actor import (
    collect_role_actor_definition_targets,
)
from aware_code.language_service.features.resolution import ResolutionMixin
from aware_code.language_service.features.targets import TargetMixin
from aware_code.language_service.json_rpc import JsonObject
from aware_code.language_service.position import ByteRange, Utf16Position
from aware_code.language_service.types import DefinitionTarget, ResolvedSymbol

# Structure Runtime
from aware_workspace.compiler.workspace import WorkspaceSnapshot


class NavigationMixin(ServiceMixinBase, TargetMixin, ResolutionMixin):
    _snapshot: WorkspaceSnapshot | None

    @override
    def _ensure_snapshot_for_uri(self, *, uri: str) -> None:
        raise NotImplementedError

    @override
    def _rebuild_full(self, *, focus_uri: str | None = None, reason: str = "change") -> None:
        raise NotImplementedError

    @override
    def _document_context(self, *, uri: str, document_text: str) -> DocumentContext:
        raise NotImplementedError

    @staticmethod
    def _cursor_in_range(*, byte_offset: int, start: int, end: int) -> bool:
        if end <= start:
            return False
        cursor = int(byte_offset)
        if cursor < start:
            return False
        if cursor > end:
            return False
        if cursor == end and cursor > start:
            cursor -= 1
        return start <= cursor < end

    @staticmethod
    def _node_text(node: Node | None) -> str:
        if node is None or node.text is None:
            return ""
        return node.text.decode("utf-8", errors="replace")

    def _program_call_definition_targets(
        self, *, uri: str, byte_offset: int, document_bytes: bytes
    ) -> list[DefinitionTarget]:
        return collect_program_call_definition_targets(
            snapshot=self._snapshot,
            uri=uri,
            byte_offset=byte_offset,
            document_bytes=document_bytes,
            class_definition_target=self._class_definition_target,
            function_definition_target=self._function_definition_target,
        )

    def _projection_view_definition_targets_by_symbol(self, *, uri: str, symbol: str) -> list[DefinitionTarget]:
        return collect_projection_view_definition_targets_by_symbol(
            snapshot=self._snapshot,
            uri=uri,
            symbol=symbol,
        )

    def _nearest_experience_toml_for_uri(self, *, uri: str) -> Path | None:
        return resolve_nearest_experience_toml_for_uri(
            uri=uri,
            uri_to_path=self._workspace.uri_to_path,
        )

    def _experience_definition_targets_by_symbol(self, *, uri: str, symbol: str) -> list[DefinitionTarget]:
        return collect_experience_definition_targets_by_symbol(
            uri=uri,
            symbol=symbol,
            uri_to_path=self._workspace.uri_to_path,
            path_to_uri=self._workspace.path_to_uri,
            node_text=self._node_text,
        )

    def _experience_view_definition_targets_by_symbol(self, *, uri: str, symbol: str) -> list[DefinitionTarget]:
        return collect_experience_view_definition_targets_by_symbol(
            uri=uri,
            symbol=symbol,
            uri_to_path=self._workspace.uri_to_path,
            path_to_uri=self._workspace.path_to_uri,
            node_text=self._node_text,
        )

    def _experience_node_definition_targets_by_symbol(
        self,
        *,
        uri: str,
        experience_symbol: str,
        node_symbol: str,
    ) -> list[DefinitionTarget]:
        return collect_experience_node_definition_targets_by_symbol(
            uri=uri,
            experience_symbol=experience_symbol,
            node_symbol=node_symbol,
            uri_to_path=self._workspace.uri_to_path,
            path_to_uri=self._workspace.path_to_uri,
            node_text=self._node_text,
        )

    def _program_topology_definition_targets(
        self, *, uri: str, byte_offset: int, document_bytes: bytes
    ) -> list[DefinitionTarget]:
        return collect_program_topology_definition_targets(
            snapshot=self._snapshot,
            uri=uri,
            byte_offset=byte_offset,
            document_bytes=document_bytes,
            cursor_in_range=self._cursor_in_range,
            node_text=self._node_text,
            experience_targets_by_symbol=self._experience_definition_targets_by_symbol,
            experience_view_targets_by_symbol=self._experience_view_definition_targets_by_symbol,
            experience_node_targets_by_symbol=self._experience_node_definition_targets_by_symbol,
            projection_targets_by_symbol=self._projection_definition_targets_by_symbol,
            projection_view_targets_by_symbol=self._projection_view_definition_targets_by_symbol,
        )

    def _experience_definition_targets(
        self, *, uri: str, byte_offset: int, document_bytes: bytes
    ) -> list[DefinitionTarget]:
        return collect_experience_definition_targets(
            snapshot=self._snapshot,
            uri=uri,
            byte_offset=byte_offset,
            document_bytes=document_bytes,
            cursor_in_range=self._cursor_in_range,
            node_text=self._node_text,
            experience_targets_by_symbol=self._experience_definition_targets_by_symbol,
            experience_node_targets_by_symbol=self._experience_node_definition_targets_by_symbol,
            projection_targets_by_symbol=self._projection_definition_targets_by_symbol,
            projection_view_targets_by_symbol=self._projection_view_definition_targets_by_symbol,
        )

    def _api_definition_targets(
        self, *, uri: str, byte_offset: int, document_bytes: bytes
    ) -> list[DefinitionTarget]:
        return collect_api_definition_targets(
            snapshot=self._snapshot,
            uri=uri,
            byte_offset=byte_offset,
            document_bytes=document_bytes,
            cursor_in_range=self._cursor_in_range,
            node_text=self._node_text,
            projection_targets_by_symbol=self._projection_definition_targets_by_symbol,
            class_definition_target=self._class_definition_target,
            attribute_definition_target=self._attribute_definition_target,
        )

    def _environment_definition_targets(
        self, *, uri: str, byte_offset: int, document_bytes: bytes
    ) -> list[DefinitionTarget]:
        return collect_environment_definition_targets(
            uri=uri,
            byte_offset=byte_offset,
            document_bytes=document_bytes,
            cursor_in_range=self._cursor_in_range,
            node_text=self._node_text,
        )

    def _role_actor_definition_targets(
        self, *, uri: str, byte_offset: int, document_bytes: bytes
    ) -> list[DefinitionTarget]:
        return collect_role_actor_definition_targets(
            snapshot=self._snapshot,
            uri=uri,
            byte_offset=byte_offset,
            document_bytes=document_bytes,
            cursor_in_range=self._cursor_in_range,
            node_text=self._node_text,
            class_definition_target=self._class_definition_target,
            function_definition_target=self._function_definition_target,
        )

    def _program_call_hover(self, *, byte_offset: int, document_bytes: bytes) -> JsonObject | None:
        return collect_program_call_hover(
            byte_offset=byte_offset,
            document_bytes=document_bytes,
        )

    def _projection_definition_targets(
        self,
        *,
        uri: str,
        byte_offset: int,
        document_bytes: bytes,
        document_text: str,
    ) -> list[DefinitionTarget]:
        _ = document_text
        return collect_projection_definition_targets(
            snapshot=self._snapshot,
            uri=uri,
            byte_offset=byte_offset,
            document_bytes=document_bytes,
            class_definition_target=self._class_definition_target,
            attribute_definition_target=self._attribute_definition_target,
            function_definition_target=self._function_definition_target,
            projection_targets_by_symbol=self._projection_definition_targets_by_symbol,
        )

    def _projection_definition_targets_by_symbol(self, *, uri: str, symbol: str) -> list[DefinitionTarget]:
        return collect_projection_definition_targets_by_symbol(
            snapshot=self._snapshot,
            uri=uri,
            symbol=symbol,
        )

    def _symbol_definition_targets(self, *, uri: str, symbol: ResolvedSymbol | None) -> list[DefinitionTarget]:
        return collect_symbol_definition_targets(
            snapshot=self._snapshot,
            uri=uri,
            symbol=symbol,
            class_definition_target=self._class_definition_target,
            enum_definition_target=self._enum_definition_target,
        )

    def definition(self, *, uri: str, position: Utf16Position, document_text: str) -> list[DefinitionTarget]:
        self._ensure_snapshot_for_uri(uri=uri)
        if self._snapshot is None or uri not in self._snapshot.codes_by_uri:
            return []

        ctx = self._document_context(uri=uri, document_text=document_text)
        offset = ctx.mapper.position_to_byte_offset(position)
        doc_bytes = ctx.document_bytes

        program_targets = collect_program_definition_targets(
            snapshot=self._snapshot,
            uri=uri,
            byte_offset=offset,
            document_bytes=doc_bytes,
            cursor_in_range=self._cursor_in_range,
            node_text=self._node_text,
            class_definition_target=self._class_definition_target,
            function_definition_target=self._function_definition_target,
            experience_targets_by_symbol=self._experience_definition_targets_by_symbol,
            experience_view_targets_by_symbol=self._experience_view_definition_targets_by_symbol,
            experience_node_targets_by_symbol=self._experience_node_definition_targets_by_symbol,
            projection_targets_by_symbol=self._projection_definition_targets_by_symbol,
            projection_view_targets_by_symbol=self._projection_view_definition_targets_by_symbol,
        )
        if program_targets:
            return program_targets

        context_targets = collect_context_definition_targets(
            snapshot=self._snapshot,
            uri=uri,
            byte_offset=offset,
            document_bytes=doc_bytes,
            cursor_in_range=self._cursor_in_range,
            node_text=self._node_text,
            experience_targets_by_symbol=self._experience_definition_targets_by_symbol,
            experience_node_targets_by_symbol=self._experience_node_definition_targets_by_symbol,
            projection_targets_by_symbol=self._projection_definition_targets_by_symbol,
            projection_view_targets_by_symbol=self._projection_view_definition_targets_by_symbol,
            class_definition_target=self._class_definition_target,
            function_definition_target=self._function_definition_target,
        )
        if context_targets:
            return context_targets

        api_targets = self._api_definition_targets(
            uri=uri,
            byte_offset=offset,
            document_bytes=doc_bytes,
        )
        if api_targets:
            return api_targets

        symbol = self._resolve_symbol_at_byte_offset(
            uri=uri,
            byte_offset=offset,
            document_bytes=doc_bytes,
            document_text=document_text,
        )
        symbol_targets = self._symbol_definition_targets(uri=uri, symbol=symbol)
        if symbol_targets:
            return symbol_targets

        member_target = self._annotation_member_definition_target(
            uri=uri,
            byte_offset=offset,
            document_bytes=doc_bytes,
            document_text=document_text,
        )
        if member_target is not None:
            return [member_target]

        proj_targets = self._projection_definition_targets(
            uri=uri,
            byte_offset=offset,
            document_bytes=doc_bytes,
            document_text=document_text,
        )
        if proj_targets:
            return proj_targets
        return []

    def hover(self, *, uri: str, position: Utf16Position, document_text: str) -> JsonObject | None:
        self._ensure_snapshot_for_uri(uri=uri)
        if self._snapshot is None or uri not in self._snapshot.codes_by_uri:
            return None

        ctx = self._document_context(uri=uri, document_text=document_text)
        offset = ctx.mapper.position_to_byte_offset(position)
        doc_bytes = ctx.document_bytes

        ann_path = self._find_annotation_path_segment_at(byte_offset=offset, document_bytes=doc_bytes)
        if ann_path is not None:
            hover = self._annotation_path_hover(
                uri=uri,
                byte_offset=offset,
                document_bytes=doc_bytes,
                path_range=ann_path,
            )
            if hover is not None:
                return hover

        prog_hover = self._program_call_hover(byte_offset=offset, document_bytes=doc_bytes)
        if prog_hover is not None:
            return prog_hover

        token = self._find_type_token_at(uri=uri, byte_offset=offset, document_bytes=doc_bytes)
        return collect_symbol_hover(
            snapshot=self._snapshot,
            uri=uri,
            token=token,
            workspace_language=self._workspace.language,
        )

    def _annotation_path_hover(
        self,
        *,
        uri: str,
        byte_offset: int,
        document_bytes: bytes,
        path_range: ByteRange,
    ) -> JsonObject | None:
        return collect_annotation_path_hover(
            snapshot=self._snapshot,
            uri=uri,
            byte_offset=byte_offset,
            document_bytes=document_bytes,
            path_range=path_range,
            get_document_text=self._workspace.get_document_text,
        )

    def _annotation_member_definition_target(
        self, *, uri: str, byte_offset: int, document_bytes: bytes, document_text: str
    ) -> DefinitionTarget | None:
        _ = document_text
        ann_seg = self._find_annotation_path_segment_at(byte_offset=byte_offset, document_bytes=document_bytes)
        if ann_seg is None:
            return None
        return collect_annotation_member_definition_target(
            snapshot=self._snapshot,
            uri=uri,
            byte_offset=byte_offset,
            document_bytes=document_bytes,
            annotation_path_range=ann_seg,
            class_definition_target=self._class_definition_target,
            attribute_definition_target=self._attribute_definition_target,
            function_definition_target=self._function_definition_target,
            enum_value_definition_target=self._enum_value_definition_target,
        )
