from abc import ABC
from pathlib import Path
from typing import Callable
from uuid import UUID
from typing_extensions import override

# Primitive
from aware_code_ontology.code.code_enums import CodeLanguage

# Meta
from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)
from aware_meta.graph.config.render.layout_strategy_template import (
    ObjectConfigGraphRenderLayoutStrategyTemplate,
)
from aware_meta.graph.config.render.layout_strategy_merge import (
    ObjectConfigGraphRenderLayoutMerge,
)
from aware_meta.graph.config.render.generated_ocg_node_manifest import (
    GeneratedObjectConfigGraphNodeManifest,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.function.function_config import FunctionConfig


class DartLayoutStrategy(ObjectConfigGraphRenderLayoutStrategy, ABC):
    """
    Base layout strategy for Dart language files.

    Provides Dart-specific behavior like file extensions and import path generation.
    This can be extended by template-based or merger-based strategies.
    """

    @property
    @override
    def language(self) -> CodeLanguage:
        return CodeLanguage.dart

    def __init__(
        self,
        base_dir: Path,
        generated_ocg_node_manifest: GeneratedObjectConfigGraphNodeManifest | None = None,
        import_root: str | None = None,
    ) -> None:
        super().__init__(base_dir, generated_ocg_node_manifest=generated_ocg_node_manifest, import_root=import_root)
        self.import_root: str | None = import_root

    @override
    def get_file_extension(self) -> str:
        return ".dart"

    @override
    def get_module_import_path(self, file_path: Path) -> str:
        """
        Convert a file path to a Dart import path.

        Args:
            file_path: The absolute file path

        Returns:
            Import path (e.g., "package:my_app/models/user.dart" or relative path)
        """
        # Get relative path from base_dir
        try:
            relative_path = file_path.relative_to(self.base_dir)
        except ValueError:
            # If not relative to base_dir, try to extract meaningful parts
            parts = file_path.parts
            # Find a reasonable starting point (look for common Dart patterns)
            start_idx = 0
            for i, part in enumerate(parts):
                if part in ["lib", "bin", "test", "src"]:
                    start_idx = i + 1  # Start after lib/bin/test/src
                    break
            relative_path = Path(*parts[start_idx:]) if start_idx < len(parts) else file_path

        rel = str(relative_path).replace("\\", "/")

        # When an import_root is configured, treat it as the Dart package/module
        # root and emit a package: import.
        root = self.import_root
        if root:
            if root.startswith("package:"):
                return f"{root}/{rel}"
            return f"package:{root}/{rel}"

        # Fallback: relative import path
        return rel


class DartLayoutStrategyTemplateMixin(ObjectConfigGraphRenderLayoutStrategyTemplate):
    """
    Dart layout strategy that combines Dart-specific behavior with template-based path resolution.

    Uses template-based path resolution from ObjectConfigGraphRenderLayoutStrategyTemplate,
    while keeping Dart-specific file extension/import behavior.
    """

    def __init__(
        self,
        base_dir: Path,
        template_paths: dict[str, Path] | None = None,
        entity_template_paths: dict[str, Path] | None = None,
        generated_ocg_node_manifest: GeneratedObjectConfigGraphNodeManifest | None = None,
        import_root: str | None = None,
    ):
        """
        Initialize the mixin layout strategy.

        Args:
            base_dir: Base directory for output files
            template_paths: A mapping of code_id to original file paths
            entity_template_paths: A mapping of entity_id to original file paths
        """
        ObjectConfigGraphRenderLayoutStrategyTemplate.__init__(
            self,
            base_dir,
            template_paths=template_paths,
            entity_template_paths=entity_template_paths,
            generated_ocg_node_manifest=generated_ocg_node_manifest,
            import_root=import_root,
        )

    @property
    @override
    def language(self) -> CodeLanguage:
        return CodeLanguage.dart

    @override
    def get_file_extension(self) -> str:
        return ".dart"

    @override
    def get_module_import_path(self, file_path: Path) -> str:
        try:
            relative_path = file_path.relative_to(self.base_dir)
        except ValueError:
            parts = file_path.parts
            start_idx = 0
            for i, part in enumerate(parts):
                if part in ["lib", "bin", "test", "src"]:
                    start_idx = i + 1
                    break
            relative_path = Path(*parts[start_idx:]) if start_idx < len(parts) else file_path

        rel = str(relative_path).replace("\\", "/")
        root = self.import_root
        if root:
            if root.startswith("package:"):
                return f"{root}/{rel}"
            return f"package:{root}/{rel}"
        return rel


class DartLayoutStrategyMergeMixin(ObjectConfigGraphRenderLayoutMerge):
    """
    Dart layout strategy that combines Dart-specific behavior with merger-based path resolution.

    Uses merger-based path resolution from ObjectConfigGraphRenderLayoutMerge,
    while keeping Dart-specific file extension/import behavior.
    """

    def __init__(
        self,
        base_dir: Path,
        old_graph: ObjectConfigGraph,
        new_graph: ObjectConfigGraph,
        old_template_paths: dict[UUID, Path] | None = None,
        new_template_paths: dict[UUID, Path] | None = None,
    ):
        """
        Initialize the mixin layout strategy.

        Args:
            base_dir: Base directory for output files
            old_graph: The old/baseline object config graph
            new_graph: The new/overlay object config graph
            old_template_paths: Optional template paths from old graph introspection
            new_template_paths: Optional template paths from new graph introspection
        """
        ObjectConfigGraphRenderLayoutMerge.__init__(
            self, base_dir, old_graph, new_graph, old_template_paths, new_template_paths
        )

    @property
    @override
    def language(self) -> CodeLanguage:
        return CodeLanguage.dart

    @override
    def get_file_extension(self) -> str:
        return ".dart"

    @override
    def get_module_import_path(self, file_path: Path) -> str:
        try:
            relative_path = file_path.relative_to(self.base_dir)
        except ValueError:
            parts = file_path.parts
            start_idx = 0
            for i, part in enumerate(parts):
                if part in ["lib", "bin", "test", "src"]:
                    start_idx = i + 1
                    break
            relative_path = Path(*parts[start_idx:]) if start_idx < len(parts) else file_path

        rel = str(relative_path).replace("\\", "/")
        root = self.import_root
        if root:
            if root.startswith("package:"):
                return f"{root}/{rel}"
            return f"package:{root}/{rel}"
        return rel


class DartFunctionsLayoutStrategy(ObjectConfigGraphRenderLayoutStrategy):
    """
    Wrapper layout strategy that delegates to an underlying Dart layout strategy
    but writes class-based outputs to `*_functions.dart` files.

    This allows the functions renderer to generate per-object extension files
    without clobbering the primary model files.
    """

    def __init__(
        self,
        base_dir: Path,
        import_root: str | None = None,
        parent: ObjectConfigGraphRenderLayoutStrategy | None = None,
        generated_ocg_node_manifest: GeneratedObjectConfigGraphNodeManifest | None = None,
        template_paths: dict[str, Path] | None = None,
        entity_template_paths: dict[str, Path] | None = None,
    ) -> None:
        super().__init__(
            base_dir,
            import_root=import_root,
            parent=parent,
            generated_ocg_node_manifest=generated_ocg_node_manifest,
            template_paths=template_paths,
            entity_template_paths=entity_template_paths,
        )
        self.entity_template_paths: dict[str, Path] = self.inner.entity_template_paths

    @property
    def inner(self) -> ObjectConfigGraphRenderLayoutStrategy:
        parent = self.get_parent()
        if parent is None:
            raise ValueError("No parent layout strategy found")
        return parent

    @property
    @override
    def language(self) -> CodeLanguage:
        return self.inner.language

    @override
    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        base = self.inner.get_class_file_path(class_config)
        return base.with_name(f"{base.stem}_functions{base.suffix}")

    @override
    def get_enum_file_path(self, enum_config: EnumConfig) -> Path:
        return self.inner.get_enum_file_path(enum_config)

    @override
    def get_function_file_path(self, function_config: FunctionConfig) -> Path:
        return self.inner.get_function_file_path(function_config)

    @override
    def get_file_extension(self) -> str:
        return self.inner.get_file_extension()

    @override
    def get_module_import_path(self, file_path: Path) -> str:
        # Reuse inner strategy's module mapping; extension files live alongside models.
        return self.inner.get_module_import_path(file_path)


class DartModelLayoutStrategy(ObjectConfigGraphRenderLayoutStrategy):
    """
    Wrapper layout strategy that delegates to an underlying Dart layout strategy
    but writes class-based outputs to `*_model.dart` files.

    This allows the canonical "model" renderer to emit Freezed/JsonSerializable
    libraries without clobbering the API barrel files at the original `*.dart`
    locations.
    """

    def __init__(
        self,
        base_dir: Path,
        import_root: str | None = None,
        parent: ObjectConfigGraphRenderLayoutStrategy | None = None,
        generated_ocg_node_manifest: GeneratedObjectConfigGraphNodeManifest | None = None,
        template_paths: dict[str, Path] | None = None,
        entity_template_paths: dict[str, Path] | None = None,
    ) -> None:
        super().__init__(
            base_dir,
            import_root=import_root,
            parent=parent,
            generated_ocg_node_manifest=generated_ocg_node_manifest,
            template_paths=template_paths,
            entity_template_paths=entity_template_paths,
        )
        self._base_class_paths: set[Path] = set()
        self.entity_template_paths: dict[str, Path] = self.inner.entity_template_paths

    @property
    def inner(self) -> ObjectConfigGraphRenderLayoutStrategy:
        parent = self.get_parent()
        if parent is None:
            raise ValueError("No parent layout strategy found")
        return parent

    @property
    @override
    def language(self) -> CodeLanguage:
        return self.inner.language

    @override
    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        base = self.inner.get_class_file_path(class_config)
        return base.with_name(f"{base.stem}_model{base.suffix}")

    @override
    def get_enum_file_path(self, enum_config: EnumConfig) -> Path:
        """
        Ensure enums are not emitted into the API barrel file.

        Canonical/template layouts often place enums in the same module as classes
        (e.g. `environment.dart`). The Dart materialization emits an API barrel to the
        canonical `<name>.dart` path, so enums must be written to a sibling
        `<name>_enums.dart` file to avoid being overwritten.
        """
        base = self.inner.get_enum_file_path(enum_config)
        if base.stem.endswith("_enums"):
            return base
        # Only redirect when a class also targets this canonical module (i.e. a barrel
        # will exist and would clobber enums). Enum-only modules should retain their
        # canonical `<name>.dart` paths for stable fallback layouts.
        if base in self._base_class_paths:
            return base.with_name(f"{base.stem}_enums{base.suffix}")
        return base

    @override
    def bind_graph(self, graph: ObjectConfigGraph) -> None:
        # Bind inner strategy first (if it derives state).
        try:
            self.inner.bind_graph(graph)
        except Exception:
            pass

        # Precompute the canonical base module paths that contain at least one class.
        base_class_paths: set[Path] = set()
        try:
            for node in graph.object_config_graph_nodes:
                class_cfg = node.class_config
                if class_cfg is None:
                    continue
                base_class_paths.add(self.inner.get_class_file_path(class_cfg))
        except Exception:
            base_class_paths = set()
        self._base_class_paths = base_class_paths

    @override
    def get_function_file_path(self, function_config: FunctionConfig) -> Path:
        return self.inner.get_function_file_path(function_config)

    @override
    def get_file_extension(self) -> str:
        return self.inner.get_file_extension()

    @override
    def get_module_import_path(self, file_path: Path) -> str:
        # Reuse inner strategy's module mapping; model files live alongside barrels.
        return self.inner.get_module_import_path(file_path)


class DartOigMaterializationLayoutStrategy(ObjectConfigGraphRenderLayoutStrategy):
    """
    Wrapper layout strategy that delegates to an underlying Dart layout strategy
    but writes class-based outputs to `*_oig.dart` files.

    This allows the OIG materialization renderer to generate per-object extension
    files without clobbering the primary model files.
    """

    @property
    def inner(self) -> ObjectConfigGraphRenderLayoutStrategy:
        parent = self.get_parent()
        if parent is None:
            raise ValueError("No parent layout strategy found")
        return parent

    @property
    @override
    def language(self) -> CodeLanguage:
        return self.inner.language

    @override
    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        base = self.inner.get_class_file_path(class_config)
        if base.is_absolute():
            try:
                rel = base.relative_to(self.inner.base_dir)
            except ValueError:
                rel = Path(base.name)
        else:
            rel = base
        oig_rel = rel.with_name(f"{base.stem}_oig{base.suffix}")
        return Path(self.base_dir) / "_aware" / oig_rel

    @override
    def get_enum_file_path(self, enum_config: EnumConfig) -> Path:
        return self.inner.get_enum_file_path(enum_config)

    @override
    def get_function_file_path(self, function_config: FunctionConfig) -> Path:
        return self.inner.get_function_file_path(function_config)

    @override
    def get_file_extension(self) -> str:
        return self.inner.get_file_extension()

    @override
    def get_module_import_path(self, file_path: Path) -> str:
        # Reuse inner strategy's module mapping; extension files live alongside models.
        return self.inner.get_module_import_path(file_path)


class DartFixedFileLayoutStrategy(ObjectConfigGraphRenderLayoutStrategy):
    """
    Layout strategy that maps all entity types to a single fixed file.

    Used by global renderers that emit registries/support files once per graph
    (rather than per canonical source file).
    """

    def __init__(self, *, parent: ObjectConfigGraphRenderLayoutStrategy, rel_path: Path) -> None:
        super().__init__(base_dir=parent.base_dir, import_root=parent.import_root, parent=parent)
        self.entity_template_paths: dict[str, Path] = parent.entity_template_paths
        self._rel_path: Path = Path(rel_path)

    @property
    def inner(self) -> ObjectConfigGraphRenderLayoutStrategy:
        p = self.get_parent()
        if p is None:
            raise ValueError("No parent layout strategy found")
        return p

    @property
    @override
    def language(self) -> CodeLanguage:
        return self.inner.language

    @override
    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        return Path(self.base_dir) / self._rel_path

    @override
    def get_enum_file_path(self, enum_config: EnumConfig) -> Path:
        return Path(self.base_dir) / self._rel_path

    @override
    def get_function_file_path(self, function_config: FunctionConfig) -> Path:
        return Path(self.base_dir) / self._rel_path

    @override
    def get_file_extension(self) -> str:
        # The fixed path includes its extension; fall back to inner if needed.
        return self.inner.get_file_extension()

    @override
    def get_module_import_path(self, file_path: Path) -> str:
        # Always delegate to the inner Dart strategy so package: imports remain correct.
        return self.inner.get_module_import_path(file_path)


class DartGraphFixedFileLayoutStrategy(DartFixedFileLayoutStrategy):
    """Fixed file layout where the rel_path is derived from the bound graph."""

    def __init__(
        self,
        *,
        parent: ObjectConfigGraphRenderLayoutStrategy,
        rel_path_factory: Callable[[ObjectConfigGraph], Path],
        placeholder_path: Path | None = None,
    ) -> None:
        self._rel_path_factory: Callable[[ObjectConfigGraph], Path] = rel_path_factory
        super().__init__(
            parent=parent,
            rel_path=placeholder_path or Path("_aware/generated.dart"),
        )

    @override
    def bind_graph(self, graph: ObjectConfigGraph) -> None:
        self._rel_path: Path = Path(self._rel_path_factory(graph))
