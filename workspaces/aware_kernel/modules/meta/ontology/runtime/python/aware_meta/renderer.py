"""
Abstract base renderer for entities with language-agnostic logic.

This module provides the foundation for all entity renderers, handling:
- Common surgical operations (CREATE, UPDATE, DELETE)
- Insertion point heuristics and positioning logic
- Section lookup and error handling utilities
- File path determination and layout integration

Language-specific renderers extend this to implement actual syntax generation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping, Optional, Type, cast
from pathlib import Path

# Logging
from aware_utils.logging import logger

# Code Infrastructure
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_section import CodeSection

from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph

# Aware Content
from aware_content.builder import get_text

# Code Runtime
from aware_code.section.render_context import CodeSectionRenderContext
from aware_code.section.writer_surgical import CodeSectionWriterSurgical
from aware_code.section.builder_index import CodeSectionBuilderIndex

# History
from aware_history_ontology.change.change_enums import ChangeType

# Layout strategy
from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)

# Deletion marker used when a non-surgical writer cannot remove sections in-place.
DELETION_SENTINEL_TEXT = "AWARE_DELETED_SECTION"
DELETION_SENTINEL_TEMPLATE = "{comment_prefix} {sentinel_text}:{section_id}"


# !! TODO: RECONSIDER USE HISTORY CHANGE DIFF.
class DiffField:
    """
    Represents a field change for surgical code updates.

    Used to track individual property changes for precise code generation.
    """

    def __init__(self, property: str, old_value: Any, new_value: Any):
        """
        Initialize a diff field.

        Args:
            property: The name of the property that changed
            old_value: The previous value
            new_value: The new value
        """
        self.property = property
        self.old_value = old_value
        self.new_value = new_value

    def __repr__(self) -> str:
        return f"DiffField(property='{self.property}', old_value={self.old_value}, new_value={self.new_value})"


class MetaRenderer(ABC):
    """
    Abstract base class for entity renderers with language-agnostic logic.

    This class provides common functionality for all entity renderers:
    - Standard CRUD operations (create, update, delete)
    - Insertion point determination and positioning
    - Section lookup and error handling
    - File path resolution via layout strategy

    Subclasses implement language-specific syntax in render_* methods.

    **Updated Architecture**: Renderers now receive change objects with full
    hierarchical context, enabling complete and explicit rendering.
    """

    def __init__(
        self,
        renderers: Mapping[type[Any], Type[MetaRenderer]],
        section_index: CodeSectionBuilderIndex,
        layout_strategy: ObjectConfigGraphRenderLayoutStrategy,
        baseline_graph: Optional[ObjectConfigGraph],
        new_graph: Optional[ObjectConfigGraph],
        namespace: str = "default",
        comment_prefix: str = "#",
    ):
        """
        Initialize the meta renderer with shared infrastructure.

        Args:
            renderers: Mapping of entity type -> renderer class
            section_index: Index for looking up existing code sections
            layout_strategy: Strategy for determining file paths
            baseline_graph: The baseline ObjectConfigGraph for lookups
            new_graph: The new ObjectConfigGraph for lookups
            namespace: Default namespace for annotations
            comment_prefix: Comment prefix for deletion sentinels (from code plugin)
        """
        self.renderers = renderers
        self.section_index = section_index
        self.layout_strategy = layout_strategy
        self.baseline_graph = baseline_graph
        self.new_graph = new_graph
        self.namespace = namespace
        self.comment_prefix = comment_prefix

        # Track deletions marked by this renderer
        self.deletions_marked = 0

    # ==================== UPDATED API: Change-based Operations ====================

    def create_from_change(
        self,
        entity_change,
        entity_config,
        ctx: CodeSectionRenderContext,
        parent: Optional[Any] = None,
    ) -> None:
        """
        Create a new entity using change context for complete rendering.

        This method handles the common logic (insertion points, heuristics)
        and delegates syntax rendering to the abstract render_create method.

        Args:
            entity_change: The change object containing hierarchical context
            entity_config: The entity configuration to create
            ctx: Render context with positioned writer
            parent: Optional parent entity for nested entities
        """
        logger.info(f"Creating {type(entity_config).__name__}: {getattr(entity_config, 'name', 'unnamed')}")

        # For top-level entities (no parent), determine insertion point and create scope
        if parent is None:
            # Determine insertion point using entity-specific logic
            insertion_point = self._find_insertion_point(entity_config, ctx, parent)

            # Position context at insertion point
            positioned_ctx = ctx.positioned_at(insertion_point)
        else:
            # For child entities, use existing context (may contain parent scope)
            positioned_ctx = ctx

        # Delegate to language-specific renderer with change context
        self.render_create_from_change(entity_change, entity_config, positioned_ctx, parent)

        logger.info(f"Successfully created {type(entity_config).__name__}")

    def update_from_change(self, entity_change, entity_config, ctx: CodeSectionRenderContext) -> None:
        """
        Update an existing entity using change context.

        This method handles the common logic (section lookup, error handling)
        and delegates syntax rendering to the abstract render_update method.

        Args:
            entity_change: The change object containing hierarchical context
            entity_config: The entity configuration to update
            ctx: Render context
        """
        logger.info(f"Updating {type(entity_config).__name__}: {getattr(entity_config, 'name', 'unnamed')}")

        # Get the entity code section
        target_language = ctx.language or self.layout_strategy.language
        entity_section = self._get_entity_code_section(entity_config, target_language)
        if not entity_section:
            logger.warning(f"Could not find entity section to update: {getattr(entity_config, 'name', 'unnamed')}")
            return

        # Create section-specific context
        section_ctx = ctx.for_section(entity_section)

        # Delegate to language-specific renderer with change context
        self.render_update_from_change(entity_change, entity_config, section_ctx)

        logger.info(f"Successfully updated {type(entity_config).__name__}")

    def delete_from_change(self, entity_change, entity_config, ctx: CodeSectionRenderContext) -> None:
        """
        Delete an existing entity using change context.

        Args:
            entity_change: The change object containing hierarchical context
            entity_config: The entity configuration to delete
            ctx: Render context
        """
        logger.info(f"Deleting {type(entity_config).__name__}: {getattr(entity_config, 'name', 'unnamed')}")

        # Get the entity code section
        target_language = ctx.language or self.layout_strategy.language
        entity_section = self._get_entity_code_section(entity_config, target_language)
        if not entity_section:
            logger.warning(f"Could not find entity section to delete: {getattr(entity_config, 'name', 'unnamed')}")
            return

        # Create section-specific context
        section_ctx = ctx.for_section(entity_section)

        # Delegate to language-specific renderer with change context
        self.render_delete_from_change(entity_change, entity_config, section_ctx)

        logger.info(f"Successfully deleted {type(entity_config).__name__}")

    # ==================== Abstract Methods: Language-Specific Implementation ====================

    @abstractmethod
    def render_create_from_change(
        self,
        entity_change,
        entity_config,
        ctx: CodeSectionRenderContext,
        parent: Optional[Any] = None,
    ) -> None:
        """
        Render creation of an entity with full change context.

        Args:
            entity_change: The change object with hierarchical context (e.g., ClassConfigChange)
            entity_config: The entity configuration to render (e.g., ClassConfig)
            ctx: Positioned render context
            parent: Optional parent entity for nested entities
        """
        pass

    @abstractmethod
    def render_update_from_change(self, entity_change, entity_config, ctx: CodeSectionRenderContext) -> None:
        """
        Render updates to an entity with full change context.

        Args:
            entity_change: The change object with hierarchical context
            entity_config: The entity configuration to update
            ctx: Render context with section
        """
        pass

    @abstractmethod
    def render_delete_from_change(self, entity_change, entity_config, ctx: CodeSectionRenderContext) -> None:
        """
        Render deletion of an entity with full change context.

        Args:
            entity_change: The change object with hierarchical context
            entity_config: The entity configuration to delete
            ctx: Render context with section
        """
        pass

    # ==================== Common Utilities ====================

    def get_entity_renderer(self, entity_type: type[Any], **override_params: Any) -> MetaRenderer:
        """
        Get a renderer for the specified entity type using the plugin.

        This enables clean delegation between renderers without tight coupling.

        Args:
            entity_type: The entity class type (e.g., AttributeConfig, FunctionConfig)
            **override_params: Optional parameter overrides

        Returns:
            A renderer instance for the entity type
        """
        renderer_cls = self.renderers[entity_type]
        renderers = cast(
            Mapping[type[Any], Type[MetaRenderer]],
            override_params.get("renderers", self.renderers),
        )
        section_index = cast(
            CodeSectionBuilderIndex,
            override_params.get("section_index", self.section_index),
        )
        layout_strategy = cast(
            ObjectConfigGraphRenderLayoutStrategy,
            override_params.get("layout_strategy", self.layout_strategy),
        )
        baseline_graph = cast(
            Optional[ObjectConfigGraph],
            override_params.get("baseline_graph", self.baseline_graph),
        )
        new_graph = cast(
            Optional[ObjectConfigGraph],
            override_params.get("new_graph", self.new_graph),
        )
        namespace = cast(str, override_params.get("namespace", self.namespace))
        comment_prefix = cast(str, override_params.get("comment_prefix", self.comment_prefix))
        return renderer_cls(
            renderers=renderers,
            section_index=section_index,
            layout_strategy=layout_strategy,
            baseline_graph=baseline_graph,
            new_graph=new_graph,
            namespace=namespace,
            comment_prefix=comment_prefix,
        )

    def file_for(self, entity_config, parent: Optional[Any] = None) -> Path:
        """
        Determine the file path for an entity using the layout strategy.

        Args:
            entity_config: The entity configuration
            parent: Optional parent entity for context

        Returns:
            The file path for the entity
        """
        # This is overridden by specific renderer types
        # Base implementation returns a generic path
        entity_name = getattr(entity_config, "name", "unknown")
        return Path(f"{entity_name.lower()}{self.layout_strategy.get_file_extension()}")

    def _find_insertion_point(self, entity_config, ctx: CodeSectionRenderContext, parent: Optional[Any] = None) -> int:
        """
        Find the optimal insertion point for a new entity.

        Default implementation appends to end of file.
        Subclasses override for entity-specific positioning logic.

        Args:
            entity_config: The entity configuration
            ctx: Render context
            parent: Optional parent entity

        Returns:
            Byte position for insertion
        """
        # Default: append to end of file
        return len(get_text(ctx.code.content_part_text))

    @abstractmethod
    def _get_entity_code_section(
        self, entity_config, target_language: CodeLanguage = CodeLanguage.aware
    ) -> Optional[CodeSection]:
        """
        Get the code section for an entity configuration.

        Args:
            entity_config: The entity configuration
            target_language: Target language for the code section

        Returns:
            The code section if found
        """
        pass

    def _apply_diff_with_error_handling(self, entity_name: str, diff: DiffField, apply_func) -> None:
        """
        Apply a diff with comprehensive error handling.

        Args:
            entity_name: Name of the entity for logging
            diff: The diff to apply
            apply_func: Function to apply the diff
        """
        try:
            apply_func(diff)
            logger.info(f"Applied {diff.property} change to {entity_name}")
        except Exception as e:
            logger.error(f"Failed to apply {diff.property} change to {entity_name}: {e}")
            raise

    def _mark_section_for_deletion(self, section: CodeSection, ctx: CodeSectionRenderContext) -> None:
        """
        Mark a code section for deletion using language-specific sentinel.

        This writes a deletion sentinel comment that:
        1. Uses the appropriate comment syntax for the target language
        2. Includes the section UUID for behavioral lookup
        3. Can be detected and cleaned up later in the pipeline

        Args:
            section: The section to mark for deletion
            ctx: Render context
        """
        if not section or not ctx.writer:
            logger.warning("Cannot mark section for deletion: missing section or writer")
            return

        # Create deletion sentinel using constants and language-specific comment prefix
        sentinel = DELETION_SENTINEL_TEMPLATE.format(
            comment_prefix=self.comment_prefix,
            sentinel_text=DELETION_SENTINEL_TEXT,
            section_id=section.id,
        )

        if isinstance(ctx.writer, CodeSectionWriterSurgical):
            segment = getattr(section, "content_part_text_segment", None)
            byte_start = getattr(segment, "byte_start", None)
            byte_end = getattr(segment, "byte_end", None)
            logger.warning(
                "Deleting section %s (%s) byte_start=%s byte_end=%s",
                getattr(section, "qualname", None),
                getattr(section, "type", None),
                byte_start,
                byte_end,
            )
            # Remove section entirely when surgical editing is available
            ctx.writer.replace_section_text(section, "")
        else:
            # Fallback to sentinel marking for non-surgical writers
            ctx.writer.replace_section_text(section, sentinel)

        # Increment deletion counter
        self.deletions_marked += 1

        logger.info(f"Marked section for deletion: {section.qualname} with sentinel")

    def _get_clean_description(self, raw_description: Optional[str]) -> Optional[str]:
        """
        Clean and normalize description text.

        Args:
            raw_description: Raw description text

        Returns:
            Cleaned description or None
        """
        if not raw_description:
            return None

        # Remove extra whitespace and normalize
        cleaned = " ".join(raw_description.split())
        return cleaned if cleaned else None

    def _find_entity_by_id(self, entity_id, entity_type=None):
        """
        Find an entity by its ID using efficient index lookups.

        Args:
            entity_id: The entity ID to look up
            entity_type: Optional type filter for the entity

        Returns:
            The entity if found, None otherwise
        """
        # Try new graph first (for CREATE operations)
        new_index = getattr(self.new_graph, "index", None) if self.new_graph else None
        if new_index is not None:
            entity = new_index.get_entity_by_id(entity_id)
            if entity and (not entity_type or isinstance(entity, entity_type)):
                return entity

        # Try baseline graph
        baseline_index = getattr(self.baseline_graph, "index", None) if self.baseline_graph else None
        if baseline_index is not None:
            entity = baseline_index.get_entity_by_id(entity_id)
            if entity and (not entity_type or isinstance(entity, entity_type)):
                return entity

        return None

    def _find_entity_by_id_with_operation_hint(self, entity_id, operation_type, entity_type=None):
        """
        Find an entity by its ID with operation-type-aware optimization.

        Args:
            entity_id: The entity ID to look up
            operation_type: The type of operation (CREATE, UPDATE, DELETE) for search optimization
            entity_type: Optional type filter for the entity

        Returns:
            The entity if found, None otherwise
        """
        # For CREATE operations, the entity is likely in the new graph
        # For DELETE operations, the entity is likely in the baseline graph
        # For UPDATE operations, try both

        if operation_type == ChangeType.create:
            # For CREATE, try new graph first
            entity = self._find_entity_by_id(entity_id, entity_type)
            return entity

        elif operation_type == ChangeType.delete:
            # For DELETE, we could optimize by checking baseline first, but _find_entity_by_id already does both
            return self._find_entity_by_id(entity_id, entity_type)

        else:
            # For UPDATE or unknown, use standard lookup
            return self._find_entity_by_id(entity_id, entity_type)

    def get_total_deletions_marked(self) -> int:
        """
        Get the total number of deletions marked by this renderer.

        Returns:
            Total count of sections marked for deletion
        """
        return self.deletions_marked
