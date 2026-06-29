from pathlib import Path
from uuid import UUID

# Meta
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph

from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)
from aware_meta.graph.config.model_bootstrap import get_node_function_config


class ObjectConfigGraphRenderLayoutMerge(ObjectConfigGraphRenderLayoutStrategy):
    """
    Layout strategy that merges layout metadata from two object config graphs.

    Uses OCG node layouts + optional explicit template mappings (by entity id) to
    resolve file paths without relying on code sections.
    """

    def __init__(
        self,
        base_dir: Path,
        old_graph: ObjectConfigGraph,
        new_graph: ObjectConfigGraph,
        old_template_paths: dict[UUID, Path] | None = None,
        new_template_paths: dict[UUID, Path] | None = None,
        import_root: str | None = None,
    ):
        """
        Initialize the merger layout strategy.

        Args:
            base_dir: Base directory for output files
            old_graph: The old/baseline object config graph
            new_graph: The new/overlay object config graph
            old_template_paths: Optional template paths from old graph introspection
            new_template_paths: Optional template paths from new graph introspection
        """
        super().__init__(base_dir, import_root=import_root)
        self.old_graph = old_graph
        self.new_graph = new_graph
        self.old_template_paths = old_template_paths or {}
        self.new_template_paths = new_template_paths or {}
        self._merge_layout_paths: dict[str, Path] = {}
        self._build_merge_layout_paths()

    def _build_merge_layout_paths(self) -> None:
        # Extract layouts from old graph, then let new graph override.
        self._extract_layouts_from_graph(self.old_graph)
        self._extract_layouts_from_graph(self.new_graph)

    def _extract_layouts_from_graph(self, graph: ObjectConfigGraph) -> None:
        for node in graph.object_config_graph_nodes:
            layouts = node.layouts
            if not layouts:
                continue
            aware_layouts = [layout for layout in layouts if not layout.layout_kind or layout.layout_kind == "aware"]
            if not aware_layouts:
                continue
            layout = min(
                aware_layouts,
                key=lambda l: (
                    l.source_position is None,
                    l.source_position or 0,
                    l.relative_path or "",
                ),
            )
            if not layout.relative_path:
                continue

            entity_id: str | None = None
            if node.class_config is not None:
                entity_id = str(node.class_config.id)
            elif node.enum_config is not None:
                entity_id = str(node.enum_config.id)
            else:
                node_function_config = get_node_function_config(node)
                if node_function_config is not None:
                    entity_id = str(node_function_config.id)
            if entity_id is None:
                continue
            self._merge_layout_paths[entity_id] = Path(layout.relative_path)

    def _get_template_path_for_entity(self, entity_id: UUID) -> Path | None:
        # Search in new template paths first (overlay takes precedence).
        if entity_id in self.new_template_paths:
            return self.new_template_paths[entity_id]
        if entity_id in self.old_template_paths:
            return self.old_template_paths[entity_id]
        return None

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        """Get the file path for a class config."""
        layout_path = self.entity_layout_paths.get(str(class_config.id))
        if layout_path is not None:
            return self.base_dir / layout_path.with_suffix(".py")
        layout_path = self._merge_layout_paths.get(str(class_config.id))
        if layout_path is not None:
            return self.base_dir / layout_path.with_suffix(".py")
        template_path = self._get_template_path_for_entity(class_config.id)
        if template_path is None:
            # Fall back to default naming if no template path found
            return self.base_dir / f"{class_config.name.lower()}.py"

        # Create the target path with the new extension
        return self.base_dir / template_path.with_suffix(".py")

    def get_enum_file_path(self, enum_config: EnumConfig) -> Path:
        """Get the file path for an enum config."""
        layout_path = self.entity_layout_paths.get(str(enum_config.id))
        if layout_path is not None:
            return self.base_dir / layout_path.with_suffix(".py")
        layout_path = self._merge_layout_paths.get(str(enum_config.id))
        if layout_path is not None:
            return self.base_dir / layout_path.with_suffix(".py")
        template_path = self._get_template_path_for_entity(enum_config.id)
        if template_path is None:
            # Fall back to default naming if no template path found
            return self.base_dir / f"{enum_config.name.lower()}.py"

        # Create the target path with the new extension
        return self.base_dir / template_path.with_suffix(".py")

    def get_function_file_path(self, function_config: FunctionConfig) -> Path:
        """Get the file path for a function config."""
        layout_path = self.entity_layout_paths.get(str(function_config.id))
        if layout_path is not None:
            return self.base_dir / layout_path.with_suffix(".py")
        layout_path = self._merge_layout_paths.get(str(function_config.id))
        if layout_path is not None:
            return self.base_dir / layout_path.with_suffix(".py")
        template_path = self._get_template_path_for_entity(function_config.id)
        if template_path is None:
            # Fall back to default naming if no template path found
            return self.base_dir / f"{function_config.name.lower()}.py"

        # Create the target path with the new extension
        return self.base_dir / template_path.with_suffix(".py")
