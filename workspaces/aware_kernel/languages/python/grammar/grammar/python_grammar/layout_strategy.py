from pathlib import Path
from uuid import UUID

# Code
from aware_code_ontology.code.code_enums import CodeLanguage

# Meta
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph

from aware_meta.graph.config.render.layout_strategy_template import (
    ObjectConfigGraphRenderLayoutStrategyTemplate,
)
from aware_meta.graph.config.render.layout_strategy_merge import (
    ObjectConfigGraphRenderLayoutMerge,
)
from aware_meta.graph.config.render.generated_ocg_node_manifest import (
    GeneratedObjectConfigGraphNodeManifest,
)
from typing_extensions import override


def _python_module_import_path(*, base_dir: Path, file_path: Path, import_root: str | None) -> str:
    """Convert a file path to a Python module import path."""
    try:
        relative_path = file_path.relative_to(base_dir)
    except ValueError:
        relative_path = file_path

    parts = list(relative_path.parts)
    if parts:
        parts[-1] = Path(parts[-1]).stem

    module_parts = [part for part in parts if part]
    if import_root:
        module_parts.insert(0, import_root)

    return ".".join(module_parts).strip(".")


class PythonLayoutStrategy(ObjectConfigGraphRenderLayoutStrategyTemplate):
    """Template-aware base layout strategy for Python language files."""

    def __init__(
        self,
        base_dir: Path,
        template_paths: dict[str, Path] | None = None,
        entity_template_paths: dict[str, Path] | None = None,
        generated_ocg_node_manifest: GeneratedObjectConfigGraphNodeManifest | None = None,
        import_root: str | None = None,
    ) -> None:
        super().__init__(
            base_dir,
            template_paths=template_paths,
            entity_template_paths=entity_template_paths,
            generated_ocg_node_manifest=generated_ocg_node_manifest,
            import_root=import_root,
        )

    @property
    @override
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    @override
    def get_file_extension(self) -> str:
        return ".py"

    @override
    def get_module_import_path(self, file_path: Path) -> str:
        return _python_module_import_path(base_dir=self.base_dir, file_path=file_path, import_root=self.import_root)


class PythonLayoutStrategyTemplateMixin(PythonLayoutStrategy):
    """Compatibility alias for template-aware Python layout strategy."""


class PythonLayoutStrategyMergeMixin(ObjectConfigGraphRenderLayoutMerge):
    """Merger-based Python layout strategy with Python module import resolution."""

    generated_ocg_node_manifest: GeneratedObjectConfigGraphNodeManifest | None

    def __init__(
        self,
        base_dir: Path,
        old_graph: ObjectConfigGraph,
        new_graph: ObjectConfigGraph,
        old_template_paths: dict[UUID, Path] | None = None,
        new_template_paths: dict[UUID, Path] | None = None,
        generated_ocg_node_manifest: GeneratedObjectConfigGraphNodeManifest | None = None,
        import_root: str | None = None,
    ) -> None:
        super().__init__(
            base_dir,
            old_graph,
            new_graph,
            old_template_paths,
            new_template_paths,
            import_root=import_root,
        )
        if generated_ocg_node_manifest is not None:
            self.generated_ocg_node_manifest = generated_ocg_node_manifest

    @property
    @override
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    @override
    def get_file_extension(self) -> str:
        return ".py"

    @override
    def get_module_import_path(self, file_path: Path) -> str:
        return _python_module_import_path(base_dir=self.base_dir, file_path=file_path, import_root=self.import_root)
