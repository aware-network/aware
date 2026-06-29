from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

# Aware Meta
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph

# Code
from aware_code_ontology.code.code_enums import CodeLanguage

from aware_meta.graph.config.render.generated_ocg_node_manifest import (
    GeneratedObjectConfigGraphNodeManifest,
)
from aware_meta.graph.config.model_bootstrap import get_node_function_config


class ObjectConfigGraphRenderLayoutStrategy(ABC):
    """
    Abstract strategy for determining file paths for meta objects.
    Different languages can implement their own layout strategy.
    """

    def __init__(
        self,
        base_dir: Path,
        import_root: str | None = None,
        parent: ObjectConfigGraphRenderLayoutStrategy | None = None,
        generated_ocg_node_manifest: GeneratedObjectConfigGraphNodeManifest | None = None,
        template_paths: dict[str, Path] | None = None,
        entity_template_paths: dict[str, Path] | None = None,
    ):
        """
        Initialize the layout strategy with a language and base directory.

        Args:
            language: The language this layout strategy is designed for
            base_dir: The base directory for all output files
        """
        self.base_dir = Path(base_dir)
        self.import_root = import_root
        self.parent = parent
        self.generated_ocg_node_manifest = generated_ocg_node_manifest
        self.template_paths: dict[str, Path] = template_paths or {}
        self.entity_template_paths: dict[str, Path] = entity_template_paths or {}
        self.entity_layout_paths: dict[str, Path] = {}
        self.entity_layout_positions: dict[str, int] = {}

    @classmethod
    def from_parent(cls, parent: ObjectConfigGraphRenderLayoutStrategy) -> ObjectConfigGraphRenderLayoutStrategy:
        """
        Create a new layout strategy from a parent layout strategy.
        """
        return cls(base_dir=parent.base_dir, import_root=parent.import_root, parent=parent)

    @property
    @abstractmethod
    def language(self) -> CodeLanguage:
        """The language this layout strategy is designed for."""
        pass

    @abstractmethod
    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        """
        Get the file path for a class config.

        Args:
            class_config: The class config to get the path for

        Returns:
            Path to the file that should contain this class
        """
        pass

    @abstractmethod
    def get_enum_file_path(self, enum_config: EnumConfig) -> Path:
        """
        Get the file path for an enum config.

        Args:
            enum_config: The enum config to get the path for

        Returns:
            Path to the file that should contain this enum
        """
        pass

    @abstractmethod
    def get_function_file_path(self, function_config: FunctionConfig) -> Path:
        """
        Get the file path for a function config.

        Args:
            function_config: The function config to get the path for

        Returns:
            Path to the file that should contain this function
        """
        pass

    @abstractmethod
    def get_file_extension(self) -> str:
        """
        Get the file extension for this language.

        Returns:
            The file extension (e.g., ".aware", ".sql")
        """
        pass

    def get_module_import_path(self, file_path: Path) -> str:
        """
        Get the module import path for a file path.

        Args:
            file_path: The file path to get the module import path for

        Returns:
            The module import path
        """
        return ".".join(file_path.parts)

    def get_parent(self) -> ObjectConfigGraphRenderLayoutStrategy | None:
        """
        Get the parent layout strategy.

        Returns:
            The parent layout strategy
        """
        return self.parent

    def bind_graph(self, graph: ObjectConfigGraph) -> None:
        """
        Optional hook: allow layout strategies to derive internal state from the graph being rendered.

        Motivation:
        - Some languages (notably SQL) may render synthetic nodes (e.g. join tables) that do not have code provenance.
        - Layout must remain deterministic and namespace-driven in those cases.

        Default: load canonical layout metadata (if available).
        """
        self.entity_layout_paths = {}
        self.entity_layout_positions = {}

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

            entity_id: str | None = None
            if node.class_config is not None:
                entity_id = str(node.class_config.id)
            elif node.enum_config is not None:
                entity_id = str(node.enum_config.id)
            else:
                node_function_config = get_node_function_config(node)
                if node_function_config is not None:
                    entity_id = str(node_function_config.id)
            if entity_id is None or not layout.relative_path:
                continue

            self.entity_layout_paths[entity_id] = Path(layout.relative_path)
            if layout.source_position is not None:
                self.entity_layout_positions[entity_id] = int(layout.source_position)
