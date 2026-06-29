from __future__ import annotations

from aware_code.language_service.features.navigation_capabilities.contracts import (
    ClassDefinitionTargetResolver,
    CursorInRangeMatcher,
    EnumDefinitionTargetResolver,
    ExperienceNodeTargetResolver,
    FunctionDefinitionTargetResolver,
    NodeTextReader,
    ProjectionTargetResolver,
    SymbolTargetResolver,
)
from aware_code.language_service.features.navigation_capabilities.environment import (
    collect_environment_definition_targets,
)
from aware_code.language_service.features.navigation_capabilities.experience import (
    collect_experience_definition_targets,
)
from aware_code.language_service.features.navigation_capabilities.program import (
    collect_program_call_definition_targets,
    collect_program_topology_definition_targets,
)
from aware_code.language_service.features.navigation_capabilities.role_actor import (
    collect_role_actor_definition_targets,
)
from aware_code.language_service.features.navigation_capabilities.symbols import (
    collect_symbol_definition_targets as collect_symbol_definition_targets_for_fallback,
)
from aware_code.language_service.types import DefinitionTarget
from aware_code.language_service.types import ResolvedSymbol
from aware_workspace.compiler.workspace import WorkspaceSnapshot


def collect_program_definition_targets(
    *,
    snapshot: WorkspaceSnapshot | None,
    uri: str,
    byte_offset: int,
    document_bytes: bytes,
    cursor_in_range: CursorInRangeMatcher,
    node_text: NodeTextReader,
    class_definition_target: ClassDefinitionTargetResolver,
    function_definition_target: FunctionDefinitionTargetResolver,
    experience_targets_by_symbol: SymbolTargetResolver,
    experience_view_targets_by_symbol: SymbolTargetResolver,
    experience_node_targets_by_symbol: ExperienceNodeTargetResolver,
    projection_targets_by_symbol: SymbolTargetResolver,
    projection_view_targets_by_symbol: SymbolTargetResolver,
) -> list[DefinitionTarget]:
    # Keep ordering stable with NavigationMixin definition flow.
    call_targets = collect_program_call_definition_targets(
        snapshot=snapshot,
        uri=uri,
        byte_offset=byte_offset,
        document_bytes=document_bytes,
        class_definition_target=class_definition_target,
        function_definition_target=function_definition_target,
    )
    if call_targets:
        return call_targets

    return collect_program_topology_definition_targets(
        snapshot=snapshot,
        uri=uri,
        byte_offset=byte_offset,
        document_bytes=document_bytes,
        cursor_in_range=cursor_in_range,
        node_text=node_text,
        experience_targets_by_symbol=experience_targets_by_symbol,
        experience_view_targets_by_symbol=experience_view_targets_by_symbol,
        experience_node_targets_by_symbol=experience_node_targets_by_symbol,
        projection_targets_by_symbol=projection_targets_by_symbol,
        projection_view_targets_by_symbol=projection_view_targets_by_symbol,
    )


def collect_context_definition_targets(
    *,
    snapshot: WorkspaceSnapshot | None,
    uri: str,
    byte_offset: int,
    document_bytes: bytes,
    cursor_in_range: CursorInRangeMatcher,
    node_text: NodeTextReader,
    experience_targets_by_symbol: SymbolTargetResolver,
    experience_node_targets_by_symbol: ExperienceNodeTargetResolver,
    projection_targets_by_symbol: ProjectionTargetResolver,
    projection_view_targets_by_symbol: ProjectionTargetResolver,
    class_definition_target: ClassDefinitionTargetResolver,
    function_definition_target: FunctionDefinitionTargetResolver,
) -> list[DefinitionTarget]:
    # Keep ordering stable with NavigationMixin definition flow.
    experience_targets = collect_experience_definition_targets(
        snapshot=snapshot,
        uri=uri,
        byte_offset=byte_offset,
        document_bytes=document_bytes,
        cursor_in_range=cursor_in_range,
        node_text=node_text,
        experience_targets_by_symbol=experience_targets_by_symbol,
        experience_node_targets_by_symbol=experience_node_targets_by_symbol,
        projection_targets_by_symbol=projection_targets_by_symbol,
        projection_view_targets_by_symbol=projection_view_targets_by_symbol,
    )
    if experience_targets:
        return experience_targets

    environment_targets = collect_environment_definition_targets(
        uri=uri,
        byte_offset=byte_offset,
        document_bytes=document_bytes,
        cursor_in_range=cursor_in_range,
        node_text=node_text,
    )
    if environment_targets:
        return environment_targets

    return collect_role_actor_definition_targets(
        snapshot=snapshot,
        uri=uri,
        byte_offset=byte_offset,
        document_bytes=document_bytes,
        cursor_in_range=cursor_in_range,
        node_text=node_text,
        class_definition_target=class_definition_target,
        function_definition_target=function_definition_target,
    )


def collect_symbol_definition_targets(
    *,
    snapshot: WorkspaceSnapshot | None,
    uri: str,
    symbol: ResolvedSymbol | None,
    class_definition_target: ClassDefinitionTargetResolver,
    enum_definition_target: EnumDefinitionTargetResolver,
) -> list[DefinitionTarget]:
    return collect_symbol_definition_targets_for_fallback(
        snapshot=snapshot,
        uri=uri,
        symbol=symbol,
        class_definition_target=class_definition_target,
        enum_definition_target=enum_definition_target,
    )
