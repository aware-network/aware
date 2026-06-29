from pathlib import Path
from uuid import UUID

# Meta
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.function.function_config import FunctionConfig

from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)
from aware_meta.graph.config.render.generated_ocg_node_manifest import (
    GeneratedObjectConfigGraphNodeManifest,
)
from aware_utils.string_transform import to_snake_case


class ObjectConfigGraphRenderLayoutStrategyTemplate(ObjectConfigGraphRenderLayoutStrategy):
    """Template-aware layout strategy that mirrors existing file structures."""

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
            generated_ocg_node_manifest=generated_ocg_node_manifest,
            import_root=import_root,
        )
        self.template_paths: dict[str, Path] = {key: Path(value) for key, value in (template_paths or {}).items()}
        self.entity_template_paths: dict[str, Path] = {
            key: Path(value) for key, value in (entity_template_paths or {}).items()
        }

    def _get_template_path(self, code_id: UUID | str | None, entity_id: str | None = None) -> Path | None:
        if code_id is not None:
            rel = self.template_paths.get(str(code_id))
            if rel is not None:
                return rel.with_suffix(self.get_file_extension())
        if entity_id:
            rel = self.entity_template_paths.get(entity_id)
            if rel is not None:
                return rel.with_suffix(self.get_file_extension())
        return None

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        """Get the file path for a class config."""
        # Prefer entity-level template mapping (materialization-owned overrides).
        path = self._get_template_path(None, str(class_config.id))
        if path is not None:
            return path
        layout_path = self.entity_layout_paths.get(str(class_config.id))
        if layout_path is not None:
            return layout_path.with_suffix(self.get_file_extension())
        rel = Path("default") / to_snake_case(class_config.name)
        return rel.with_suffix(self.get_file_extension())

    def get_enum_file_path(self, enum_config: EnumConfig) -> Path:
        """Get the file path for an enum config."""
        # Prefer entity-level template mapping (materialization-owned overrides).
        path = self._get_template_path(None, str(enum_config.id))
        if path is not None:
            return path
        layout_path = self.entity_layout_paths.get(str(enum_config.id))
        if layout_path is not None:
            return layout_path.with_suffix(self.get_file_extension())
        rel = Path("default") / to_snake_case(enum_config.name)
        return rel.with_suffix(self.get_file_extension())

    def get_function_file_path(self, function_config: FunctionConfig) -> Path:
        """Get the file path for a function config."""
        # Prefer entity-level template mapping (materialization-owned overrides).
        path = self._get_template_path(None, str(function_config.id))
        if path is not None:
            return path
        layout_path = self.entity_layout_paths.get(str(function_config.id))
        if layout_path is not None:
            return layout_path.with_suffix(self.get_file_extension())
        rel = Path("default") / to_snake_case(function_config.name)
        return rel.with_suffix(self.get_file_extension())
