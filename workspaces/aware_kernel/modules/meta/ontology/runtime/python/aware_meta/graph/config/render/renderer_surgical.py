"""
Unified surgical code editing system using language plugins.

**Updated Architecture**: No more emitter anti-pattern. Works directly with
ObjectConfigGraphChange objects to follow hierarchical structure and enable
complete, explicit rendering with full change context.
"""

from pathlib import Path
from typing import Any, Iterable, Optional
from uuid import UUID, uuid4

# Logging
from aware_utils.logging import logger

# Code Runtime
from aware_code.builder import create_from_text
from aware_content.builder import get_text

# Code Models
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_section import CodeSection

# Code Runtime
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.writer_surgical import CodeSectionWriterSurgical
from aware_code.section.render_context import CodeSectionRenderContext

# Meta Models
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.enum.enum_config import EnumConfig

# Aware Structure
from aware_meta.language_plugin import MetaLanguagePlugin
from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)

# History Models
from aware_history_ontology.change.change_enums import ChangeType


class ObjectConfigGraphRendererSurgical:
    """
    Unified surgical code editing system using language plugins.

    ## Features

    - Language-agnostic surgical editing through plugins
    - Direct ObjectConfigGraphChange → Code modification pipeline
    - Hierarchical delegation following change tree structure
    - Complete entity rendering with child context
    - Cross-object relationship coordination
    """

    def __init__(
        self,
        plugin: MetaLanguagePlugin,
        existing_codes: dict[str, Code],
        section_index: CodeSectionBuilderIndex,
        layout_strategy: ObjectConfigGraphRenderLayoutStrategy,
        baseline_graph: Optional[ObjectConfigGraph] = None,
        new_graph: Optional[ObjectConfigGraph] = None,
        namespace: str = "default",
    ):
        """
        Initialize the surgical renderer.

        Args:
            plugin: MetaLanguagePlugin for the target language
            existing_codes: Map of file_path -> Code objects with existing sections
            section_index: Index for looking up existing sections
            layout_strategy: Strategy for determining file paths
            baseline_graph: The baseline ObjectConfigGraph for lookups
            new_graph: The new ObjectConfigGraph for lookups
            namespace: Default namespace for annotations
        """
        self.plugin = plugin
        self.section_index = section_index
        self.layout_strategy = layout_strategy
        self.baseline_graph = baseline_graph
        self.new_graph = new_graph
        self.namespace = namespace

        # Canonicalize all paths so the section index, builder, and writer work
        # off a single key space regardless of language.
        self.existing_codes: dict[str, Code] = {}
        for original_path, code in existing_codes.items():
            normalized_key = self._normalize_path_key(original_path)
            self.existing_codes[normalized_key] = code
            self._hydrate_code_section_positions(code)
            self._register_code_with_index(code, normalized_key)

        # Track deletions marked during rendering
        self.deletions_marked = 0

        # Track all renderer instances to collect deletion counts
        self.used_renderers = []

        # Track files we create during this rendering session to disambiguate from baseline copies
        self.created_files: set[str] = set()
        # Track files whose existing buffers are being reused for CREATE operations
        self.recreated_files: set[str] = set()

    def apply_changes(self, changes: list[Any]) -> tuple[dict[str, Code], int]:
        """
        Apply a list of graph changes to the existing code.

        **Updated Approach**: Works directly with ObjectConfigGraphChange objects,
        following their hierarchical structure for complete rendering.

        Args:
            changes: List of ObjectConfigGraphChange objects to apply

        Returns:
            Tuple of (updated map of file_path -> Code objects, number of deletions marked)
        """
        logger.info(f"Applying {len(changes)} graph changes")

        # Reset deletion counter
        self.deletions_marked = 0

        # Reset renderer tracking
        self.used_renderers = []

        # Process each change directly, following hierarchical structure
        for change in changes:
            try:
                self._apply_change(change)
            except Exception as e:
                import traceback

                logger.error(f"Error applying graph change {e}")
                logger.error(traceback.format_exc())
                raise

        # Collect deletion counts from all used renderers
        total_deletions = 0
        for renderer in self.used_renderers:
            if hasattr(renderer, "get_total_deletions_marked"):
                renderer_deletions = renderer.get_total_deletions_marked()
                total_deletions += renderer_deletions
                logger.debug(f"Renderer {type(renderer).__name__} marked {renderer_deletions} deletions")

        logger.info(f"Applied {len(changes)} changes, marked {total_deletions} deletions")

        # Return the updated codes and deletion count
        return self.existing_codes, total_deletions

    def _apply_change(self, change: Any) -> None:
        """
        Apply a change to the graph.

        Args:
            change: The ObjectConfigGraphChange to apply
        """
        # Iterate through all node changes in this graph change, ordering deletions first
        ordered_nodes: list[tuple[int, int, Any]] = []
        for index, change_node in enumerate(change.object_config_graph_node_change_list):
            node = change_node.object_config_graph_node_change
            priority = self._get_node_change_priority(node)
            ordered_nodes.append((priority, index, node))

        for _, _, node_change in sorted(ordered_nodes, key=lambda item: (item[0], item[1])):

            node_change_type = self._node_change_type_token(node_change)

            if node_change_type in {"class", "class_", "object_config"}:
                self._handle_object_config_change(node_change)
            elif node_change_type == "enum":
                self._handle_enum_config_change(node_change)
            elif node_change_type == "function":
                self._handle_function_config_change(node_change)
            elif node_change_type in {"relationship", "object_relationship"}:
                self._handle_relationship_change(node_change)
            else:
                raise ValueError(f"Unknown change type: {node_change_type!r}")

    def _node_change_type_token(self, node_change: Any) -> str:
        raw_type = getattr(node_change, "type", None)
        if raw_type is None:
            return ""
        return str(getattr(raw_type, "value", raw_type)).strip().lower()

    def _get_node_change_priority(self, node_change: Any) -> int:
        """Return a stable sort priority for node changes.

        Deletions must run before creations so baseline content is removed prior to
        inserting rebuilt sections. Updates follow deletions, and creations execute last.
        Unknown or relationship-only changes preserve original ordering.
        """

        change_type = self._extract_node_change_type(node_change)
        if change_type == ChangeType.delete:
            return 0
        if change_type == ChangeType.update:
            return 1
        if change_type == ChangeType.create:
            return 2
        return 3

    def _extract_node_change_type(self, node_change: Any) -> Optional[ChangeType]:
        """Safely pull the ChangeType enum from a node change structure."""

        change_attr_map = {
            "class": "object_config_change",
            "class_": "object_config_change",
            "object_config": "object_config_change",
            "enum": "enum_config_change",
            "function": "function_config_change",
            "relationship": "object_relationship_change",
            "object_relationship": "object_relationship_change",
        }

        attr_name = change_attr_map.get(self._node_change_type_token(node_change))
        if not attr_name:
            return None

        change_container = getattr(node_change, attr_name, None)
        if not change_container:
            return None

        change_payload = getattr(change_container, "change", None)
        if not change_payload:
            return None

        return getattr(change_payload, "type", None)

    def _handle_object_config_change(self, change: Any) -> None:
        """
        Handle object-level changes by delegating to ClassConfig rendering.

        Args:
            change: The ObjectConfigGraphChange with ObjectConfigChange
        """
        # Access the object config change through the correct field structure
        object_config_change = change.object_config_change
        if not object_config_change:
            raise ValueError("ObjectConfig change is required")
        if not object_config_change.change:
            raise ValueError("ObjectConfig change type is required")
        logger.info(f"Handling ObjectConfig change: {object_config_change.change.type}")

        # Canonical ontology no longer exposes ObjectConfig as a renderable entity.
        # Object-level graph deltas are represented through ClassConfig changes.
        self._delegate_object_change_to_class_renderer(change)

    def _delegate_object_change_to_class_renderer(self, change: Any) -> None:
        """
        Delegate ObjectConfig change to ClassConfig renderer for languages without object-level syntax.

        Args:
            change: The ObjectConfigGraphChange with ObjectConfigChange
        """
        object_config_change = change.object_config_change
        if not object_config_change:
            raise ValueError("ObjectConfig change is required")
        if not object_config_change.change:
            raise ValueError("ObjectConfig change type is required")
        # Check if this ObjectConfig change has a ClassConfig change
        if not object_config_change.object_config_change_class_config_change:
            logger.info("ObjectConfig change has no ClassConfig change - skipping")
            return

        class_config_change = object_config_change.object_config_change_class_config_change.class_config_change
        logger.info(f"Delegating to ClassConfig change: {class_config_change.change.type}")

        supports_recreation = getattr(self.plugin, "supports_full_file_recreation", False)

        # Get ClassConfigRenderer from plugin
        renderer = self._get_and_track_renderer(ClassConfig)

        # Get the class config entity
        if not class_config_change.class_config_id:
            raise ValueError("ClassConfig ID is required")
        class_config = self._find_entity_by_id(class_config_change.class_config_id, ClassConfig)
        if not class_config:
            logger.error("Could not find ClassConfig for delegated change")
            return

        change_type = class_config_change.change.type
        file_path = str(self.layout_strategy.get_class_file_path(class_config))
        ctx = self._create_render_context(file_path, change_type)

        # Delegate to ClassConfigRenderer with full change context
        if change_type == ChangeType.create:
            renderer.render_create_from_change(class_config_change, class_config, ctx)
        elif change_type == ChangeType.update:
            renderer.render_update_from_change(class_config_change, class_config, ctx)
        elif change_type == ChangeType.delete:
            normalized_key = self._normalize_path_key(file_path)
            if supports_recreation and normalized_key in self.recreated_files:
                self.recreated_files.discard(normalized_key)
                return
            renderer.render_delete_from_change(class_config_change, class_config, ctx)
            if supports_recreation:
                if normalized_key in self.recreated_files:
                    self.recreated_files.discard(normalized_key)
                else:
                    self._remove_existing_code_entries(file_path)

    def _handle_enum_config_change(self, change: Any) -> None:
        """
        Handle EnumConfig changes by delegating to EnumConfigRenderer.

        Args:
            change: The ObjectConfigGraphChange with EnumConfigChange
        """
        # Access the enum config change through the correct field structure
        enum_config_change = change.enum_config_change
        if not enum_config_change:
            raise ValueError("EnumConfig change is required")
        if not enum_config_change.change:
            raise ValueError("EnumConfig change type is required")
        logger.info(f"Handling EnumConfig change: {enum_config_change.change.type}")

        # Get EnumConfigRenderer from plugin
        renderer = self._get_and_track_renderer(EnumConfig)

        # Get the enum config entity
        enum_config = self._get_enum_config_from_change(change)
        if not enum_config:
            logger.error("Could not find EnumConfig for change")
            return

        file_path = str(self.layout_strategy.get_enum_file_path(enum_config))
        change_type = enum_config_change.change.type
        ctx = self._create_render_context(file_path, change_type)

        supports_recreation = getattr(self.plugin, "supports_full_file_recreation", False)

        # Delegate to EnumConfigRenderer with full change context
        if change_type == ChangeType.create:
            renderer.render_create_from_change(enum_config_change, enum_config, ctx)
        elif change_type == ChangeType.update:
            renderer.render_update_from_change(enum_config_change, enum_config, ctx)
        elif change_type == ChangeType.delete:
            normalized_key = self._normalize_path_key(file_path)
            if supports_recreation and normalized_key in self.recreated_files:
                self.recreated_files.discard(normalized_key)
                return
            renderer.render_delete_from_change(enum_config_change, enum_config, ctx)
            if supports_recreation:
                if normalized_key in self.recreated_files:
                    self.recreated_files.discard(normalized_key)
                else:
                    self._remove_existing_code_entries(file_path)

    def _handle_function_config_change(self, change: Any) -> None:
        """
        Handle FunctionConfig changes by delegating to FunctionConfigRenderer.

        **ARCHITECTURE FIX**: Skip class methods - they're handled through class delegation.
        Only handle standalone functions that don't belong to any class.

        Args:
            change: The ObjectConfigGraphChange with FunctionConfigChange
        """
        # Access the function config change through the correct field structure
        function_config_change = change.function_config_change
        if not function_config_change:
            raise ValueError("FunctionConfig change is required")
        if not function_config_change.change:
            raise ValueError("FunctionConfig change type is required")

        # Get the function config entity
        function_config = self._get_function_config_from_change(change)
        if not function_config:
            logger.error("Could not find FunctionConfig for change")
            return

        # Check if this function belongs to a class
        if self._function_belongs_to_class(function_config):
            logger.info(
                f"Function {function_config.name} belongs to a class - will be handled through class delegation"
            )
            return

        # This is a standalone function - handle it directly
        logger.info(f"Handling standalone FunctionConfig change: {function_config_change.change.type}")

        # Get FunctionConfigRenderer from plugin
        renderer = self._get_and_track_renderer(FunctionConfig)

        # Delegate to FunctionConfigRenderer with full change context
        if not function_config_change:
            raise ValueError("FunctionConfig change is required")
        if not function_config_change.change:
            raise ValueError("FunctionConfig change type is required")
        change_type = function_config_change.change.type
        file_path = str(self.layout_strategy.get_function_file_path(function_config))
        ctx = self._create_render_context(file_path, change_type)
        if change_type == ChangeType.create:
            renderer.render_create_from_change(function_config_change, function_config, ctx)
        elif change_type == ChangeType.update:
            renderer.render_update_from_change(function_config_change, function_config, ctx)
        elif change_type == ChangeType.delete:
            renderer.render_delete_from_change(function_config_change, function_config, ctx)

    def _function_belongs_to_class(self, function_config: FunctionConfig) -> bool:
        """
        Check if a function belongs to a class.

        Args:
            function_config: The function to check

        Returns:
            True if the function belongs to a class, False if standalone
        """
        # Check in both graphs for any ClassConfig that contains this function
        for graph in [self.new_graph, self.baseline_graph]:
            if not graph:
                continue

            for node in graph.object_config_graph_nodes:
                class_config = node.class_config
                if class_config is None:
                    continue
                for func_link in class_config.class_config_function_configs:
                    if func_link.function_config and func_link.function_config.id == function_config.id:
                        logger.info(f"Function {function_config.name} belongs to class {class_config.name}")
                        return True

        logger.info(f"Function {function_config.name} is standalone")
        return False

    def _handle_relationship_change(self, change: Any) -> None:
        """
        Handle relationship changes with cross-object coordination.

        Args:
            change: The ObjectConfigGraphChange with relationship change
        """
        if not change.object_config_relationship_change:
            raise ValueError("ObjectConfigRelationship change is required")
        logger.info(f"Handling relationship change: {change.type}")
        # TODO: Implement relationship handling when needed
        # For now, relationships are handled through object/class attribute changes
        logger.info("Relationship changes are handled through object/class attribute changes")

    # ==================== Entity Lookup Helpers ====================

    def _get_enum_config_from_change(self, change: Any) -> Optional[EnumConfig]:
        """Get EnumConfig entity from change."""
        if not change.enum_config_change:
            raise ValueError("EnumConfig change is required")
        if not change.enum_config_change.enum_config_id:
            raise ValueError("EnumConfig ID is required")
        enum_config_id = change.enum_config_change.enum_config_id
        return self._find_entity_by_id(enum_config_id, EnumConfig)

    def _get_function_config_from_change(self, change: Any) -> Optional[FunctionConfig]:
        """Get FunctionConfig entity from change."""
        if not change.function_config_change:
            raise ValueError("FunctionConfig change is required")
        if not change.function_config_change.function_config_id:
            raise ValueError("FunctionConfig ID is required")
        function_config_id = change.function_config_change.function_config_id
        return self._find_entity_by_id(function_config_id, FunctionConfig)

    def _find_entity_by_id(self, entity_id: UUID, entity_type) -> Optional[Any]:
        """
        Find any entity by its ID using both graph indexes.

        Args:
            entity_id: The entity ID to look up
            entity_type: The type of entity to find

        Returns:
            The entity if found, None otherwise
        """
        # Try new graph first
        new_index = getattr(self.new_graph, "index", None) if self.new_graph else None
        if new_index is not None:
            entity = new_index.get_entity_by_id(entity_id)
            if entity and isinstance(entity, entity_type):
                return entity

        # Try baseline graph
        baseline_index = getattr(self.baseline_graph, "index", None) if self.baseline_graph else None
        if baseline_index is not None:
            entity = baseline_index.get_entity_by_id(entity_id)
            if entity and isinstance(entity, entity_type):
                return entity

        return None

    # ==================== Render Context Creation ====================

    def _create_render_context(
        self, file_path: str, change_type: Optional[ChangeType] = None
    ) -> CodeSectionRenderContext:
        """Create a render context for a specific file."""

        # Get or create code object for the file, considering the change type
        code = self._get_or_create_code_object(file_path, change_type)

        # Create positioned writer
        writer = CodeSectionWriterSurgical(code=code, index=self.section_index, indent_size=4)
        existing_text = get_text(code.content_part_text)
        writer._cursor = len(existing_text)
        writer._at_line_start = existing_text.endswith("\n") or not existing_text

        # Create render context
        return CodeSectionRenderContext(code=code, writer=writer)

    def _get_or_create_code_object(self, file_path: str, change_type: Optional[ChangeType]) -> Code:
        """Get existing Code object or create a new one for the file path.

        Important: keep the full relative path provided by the layout strategy
        (e.g., "domains/default/my_class.py") as the key so downstream
        persistence can map back to the intended location.
        """
        normalized_key = self._normalize_path_key(file_path)
        supports_recreation = getattr(self.plugin, "supports_full_file_recreation", False)

        if normalized_key in self.existing_codes:
            code = self.existing_codes[normalized_key]
            if supports_recreation and change_type == ChangeType.create and normalized_key not in self.created_files:
                self.recreated_files.add(normalized_key)

                new_code = create_from_text("", self.plugin.language)
                self.existing_codes[normalized_key] = new_code
                self._register_code_with_index(new_code, normalized_key)
                self._seed_module_scaffolding(new_code, normalized_key)
                return new_code

            if supports_recreation and change_type == ChangeType.create:
                self.recreated_files.add(normalized_key)
            self._hydrate_code_section_positions(code)
            self._register_code_with_index(code, normalized_key)
            return code

        # Fallback: search by filename across existing entries, preferring non-created copies
        target_name = Path(file_path).name
        matched_code: Optional[Code] = None
        matched_key: Optional[str] = None
        for existing_key, existing_code in self.existing_codes.items():
            if Path(existing_key).name == target_name and existing_key not in self.created_files:
                matched_code = existing_code
                matched_key = existing_key
                break

        if matched_code is not None:
            if matched_key is not None and matched_key != normalized_key:
                self.existing_codes.pop(matched_key, None)
                self.created_files.discard(matched_key)
                self.recreated_files.discard(matched_key)
            self.existing_codes[normalized_key] = matched_code
            if supports_recreation and change_type == ChangeType.create and normalized_key not in self.created_files:
                self.recreated_files.add(normalized_key)
                new_code = create_from_text("", self.plugin.language)
                self.existing_codes[normalized_key] = new_code
                self._register_code_with_index(new_code, normalized_key)
                self._seed_module_scaffolding(new_code, normalized_key)
                return new_code
            if supports_recreation and change_type == ChangeType.create:
                self.recreated_files.add(normalized_key)
            self._hydrate_code_section_positions(matched_code)
            self._register_code_with_index(matched_code, normalized_key)
            return matched_code

        # No existing entry matched; create a fresh Code object for this file
        code = create_from_text("", self.plugin.language)
        self.existing_codes[normalized_key] = code
        self.created_files.add(normalized_key)
        if supports_recreation:
            self.recreated_files.discard(normalized_key)
        self._hydrate_code_section_positions(code)
        self._register_code_with_index(code, normalized_key)
        self._seed_module_scaffolding(code, normalized_key)
        return code

    def _hydrate_code_section_positions(self, code: Code) -> None:
        """Rebind section segments to this code buffer and refresh lookup index."""
        if not code:
            return

        for section in self._iter_sections_for_code(code):
            segment = getattr(section, "content_part_text_segment", None)
            if segment and segment.content_part_text is not code.content_part_text:
                segment.content_part_text = code.content_part_text
            try:
                self.section_index.add(section)
            except Exception:
                pass

    def _iter_sections_for_code(self, code: Code) -> Iterable[CodeSection]:
        """Yield every CodeSection attached to the provided code instance."""

        if not code:
            return

        seen: set[UUID] = set()

        def emit(section: Optional[CodeSection]) -> Iterable[CodeSection]:
            if not section:
                return []

            if getattr(section, "code_id", None) != code.id:
                return []

            if section.id in seen:
                return []

            seen.add(section.id)

            segment = getattr(section, "content_part_text_segment", None)
            if segment and segment.content_part_text is not code.content_part_text:
                segment.content_part_text = code.content_part_text

            return [section]

        # Direct sections declared on the Code instance
        for direct_section in code.code_sections:
            for yielded in emit(direct_section):
                yield yielded

        graphs = [self.baseline_graph, self.new_graph]
        for graph in graphs:
            if not graph:
                continue

            for node in graph.object_config_graph_nodes:
                class_config = node.class_config
                if class_config is not None:
                    class_section = getattr(class_config, "code_section_class", None)
                    for yielded in emit(getattr(class_section, "code_section", None)):
                        yield yielded

                    for attr_link in class_config.class_config_attribute_configs:
                        attribute_config = attr_link.attribute_config
                        if attribute_config is None:
                            continue
                        attr_section = getattr(attribute_config, "code_section_attribute", None)
                        for yielded in emit(getattr(attr_section, "code_section", None)):
                            yield yielded

                    for func_link in class_config.class_config_function_configs:
                        function_config = func_link.function_config
                        if function_config is None:
                            continue
                        func_section = getattr(function_config, "code_section_function", None)
                        for yielded in emit(getattr(func_section, "code_section", None)):
                            yield yielded

                enum_config = node.enum_config
                if enum_config is not None:
                    enum_section = getattr(enum_config, "code_section_enum", None)
                    for yielded in emit(getattr(enum_section, "code_section", None)):
                        yield yielded

    def _normalize_path_key(self, file_path: str) -> str:
        """Return a stable key for code lookups relative to the layout base when possible."""
        path_obj = Path(file_path)

        try:
            base_dir = Path(self.layout_strategy.base_dir)
        except Exception:
            base_dir = None

        if base_dir:
            try:
                return Path(path_obj).relative_to(base_dir).as_posix()
            except Exception:
                # If file_path is relative, the attempt above may fail; fall
                # back to normalising the already-relative representation.
                pass

        return path_obj.as_posix()

    def _register_code_with_index(self, code: Code, normalized_key: str) -> None:
        """Keep the section index's code-to-path mapping aligned with our keys."""

        if not code or not self.section_index:
            return

        try:
            self.section_index.set_code_path_mapping(code.id, normalized_key)
        except Exception:
            pass

    def _seed_module_scaffolding(self, code: Code, canonical_path: str) -> None:
        """Populate language-specific module scaffolding (docstrings, etc.) when available."""

        if self.plugin.language != CodeLanguage.python:
            return

        try:
            path_obj = Path(canonical_path)
            if not path_obj.is_file():
                return

            import ast

            text = path_obj.read_text()
            module = ast.parse(text)
            docstring = ast.get_docstring(module)
            if docstring:
                header = f'"""{docstring}"""\n\n'
                code.content_part_text.inline_text = header
            else:
                code.content_part_text.inline_text = ""
        except Exception:
            pass

    def _clone_code_with_sections(self, source: Optional[Code]) -> Code:
        """Create a deep copy of a Code object including section metadata."""

        if not source:
            return create_from_text("", self.plugin.language)

        try:
            cloned: Code = source.model_copy(deep=True)  # type: ignore[attr-defined]
        except Exception:
            cloned = create_from_text(get_text(source.content_part_text), source.language)
            cloned.code_sections = []
            for section in source.code_sections:
                try:
                    cloned_section = section.model_copy(deep=True)  # type: ignore[attr-defined]
                except Exception:
                    cloned_section = section
                cloned.code_sections.append(cloned_section)

        # Ensure cloned identifiers do not collide with the source so both can coexist temporarily.
        try:
            if getattr(cloned, "id", None) == getattr(source, "id", None):
                cloned.id = uuid4()
        except Exception:
            pass

        try:
            content_part = getattr(cloned, "content_part_text", None)
            source_part = getattr(source, "content_part_text", None)
            if content_part and source_part and getattr(content_part, "id", None) == getattr(source_part, "id", None):
                content_part.id = uuid4()
        except Exception:
            pass

        return cloned

    def _remove_existing_code_entries(self, file_path: str) -> None:
        """Remove baseline code entries that match the provided file path by filename."""
        target_name = Path(file_path).name
        keys_to_remove = [
            key
            for key in self.existing_codes
            if Path(key).name == target_name and key not in self.created_files and key not in self.recreated_files
        ]
        for key in keys_to_remove:
            del self.existing_codes[key]
            self.created_files.discard(key)

    def _get_and_track_renderer(self, entity_type):
        """
        Get a renderer and track it for deletion counting.

        Args:
            entity_type: Type of entity to get renderer for

        Returns:
            Renderer instance
        """
        renderer = self.plugin.get_surgical_renderer(
            entity_type,
            section_index=self.section_index,
            layout_strategy=self.layout_strategy,
            baseline_graph=self.baseline_graph,
            new_graph=self.new_graph,
            namespace=self.namespace,
        )

        # Track this renderer for deletion counting
        self.used_renderers.append(renderer)

        return renderer
