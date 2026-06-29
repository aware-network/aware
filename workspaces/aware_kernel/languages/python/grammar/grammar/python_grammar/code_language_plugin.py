"""Python language plugin for the code processing system."""

from __future__ import annotations
from pathlib import Path
import re

from tree_sitter import Node
from typing_extensions import override

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_section_enums import CodeSectionType

from aware_code.language.plugin import (
    CodeLanguagePlugin,
    CodeLanguageMaterializationOutputDescriptor,
    CodeLanguageQualityGate,
)
from aware_code.language.operational_workspace import (
    CodeLanguageOperationalWorkspaceBuilder,
)
from aware_code.language.schemas import StructuralFilterDecision
from aware_code.language.test_discovery import CodeLanguageTestDiscovery
from aware_code.language.tooling import CodeLanguageToolSpec
from aware_code.node.adapter import CodeNodeAdapter
from aware_code.package.discovery import CodePackageDiscovery
from aware_code.primitive_codec import CodePrimitiveCodec
from aware_code.section.metadata import CodeSectionMetadata

# Python Primitive Type
from python_grammar.primitive_codec import PythonPrimitiveCodec
from python_grammar.type_parser import PythonTypeParser

# Python Layout Plugin
from python_grammar.layout_plugin import PythonCodeLanguagePluginLayout

# Python Module Discovery
from python_grammar.code_module_discovery import PythonCodeModuleDiscovery
from python_grammar.code_package_discovery import PythonCodePackageDiscovery
from python_grammar.code_test_discovery import PythonCodeTestDiscovery
from python_grammar.execution_closure import PythonExecutionClosureBuilder
from python_grammar.operational_workspace import PythonOperationalWorkspaceBuilder
from python_grammar.pypi_publish import create_python_pypi_tool_specs

# Python Code Section Adapters
from python_grammar.adapters.attribute_adapter import PythonAttributeAdapter
from python_grammar.adapters.class_adapter import PythonClassAdapter
from python_grammar.adapters.comment_adapter import PythonCommentAdapter
from python_grammar.adapters.decorator_adapter import PythonDecoratorAdapter
from python_grammar.adapters.enum_adapter import PythonEnumAdapter
from python_grammar.adapters.enum_value_adapter import PythonEnumValueAdapter
from python_grammar.adapters.expression_adapter import PythonExpressionAdapter
from python_grammar.adapters.function_adapter import PythonFunctionAdapter
from python_grammar.adapters.import_adapter import PythonImportAdapter
from python_grammar.type_descriptor_adapter import PythonTypeDescriptorAdapter

# Tree sitter adapter
from aware_code.tree.tree_sitter_adapter import CodeTreeSitterAdapter

# Tree-sitter
from python_grammar._tree_sitter_python import PYTHON_LANGUAGE


class PythonCodeLanguagePlugin(CodeLanguagePlugin[Node]):
    """Python language plugin with structural filtering capabilities and enum caching."""

    def __init__(
        self,
        language: CodeLanguage,
        primitive_codec: CodePrimitiveCodec,
        tree_sitter_adapter: CodeTreeSitterAdapter,
        node_adapters: dict[CodeSectionType, CodeNodeAdapter[Node]],
        metadata_adapters: dict[CodeSectionType, type[CodeSectionMetadata]],
        extensions: list[str],
        comment_prefix: str,
        layout_plugin: PythonCodeLanguagePluginLayout,
        module_discovery: PythonCodeModuleDiscovery,
        package_discovery: CodePackageDiscovery | None,
        test_discovery: CodeLanguageTestDiscovery | None,
        type_descriptor_adapter: PythonTypeDescriptorAdapter,
        quality_gates: tuple[CodeLanguageQualityGate, ...] = (),
        tooling: tuple[CodeLanguageToolSpec, ...] = (),
        materialization_artifact_outputs: tuple[
            CodeLanguageMaterializationOutputDescriptor, ...
        ] = (),
        operational_workspace_builder: (
            CodeLanguageOperationalWorkspaceBuilder | None
        ) = None,
    ):
        super().__init__(
            language=language,
            primitive_codec=primitive_codec,
            tree_sitter_adapter=tree_sitter_adapter,
            node_adapters=node_adapters,
            metadata_adapters=metadata_adapters,
            extensions=extensions,
            comment_prefix=comment_prefix,
            type_descriptor_adapter=type_descriptor_adapter,
            layout_plugin=layout_plugin,
            module_discovery=module_discovery,
            package_discovery=package_discovery,
            test_discovery=test_discovery,
            quality_gates=quality_gates,
            tooling=tooling,
            materialization_artifact_outputs=materialization_artifact_outputs,
            execution_closure_builder=PythonExecutionClosureBuilder(),
            operational_workspace_builder=operational_workspace_builder,
        )
        # Cache for tracking which files contain structural elements
        self._structural_files_cache: set[str] = set()
        # Cache for tracking which enums are imported by structural files
        self._structural_enums_cache: set[str] = set()
        # Cache for tracking imports by file
        self._file_imports_cache: dict[str, set[str]] = {}
        # Flag to track if we need to refresh the cache
        self._cache_dirty: bool = True

    def _clear_cache(self) -> None:
        """Clear all caches - useful when the repository changes."""
        self._structural_files_cache.clear()
        self._structural_enums_cache.clear()
        self._file_imports_cache.clear()
        self._cache_dirty = True

    def _extract_imports(self, file_content: str) -> set[str]:
        """Extract import statements to understand dependencies."""
        imports: set[str] = set()

        # Pattern for various import types
        import_patterns = [
            r"^from\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s+import",
            r"^import\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)",
        ]

        for line in file_content.split("\n"):
            line = line.strip()
            for pattern in import_patterns:
                match = re.match(pattern, line)
                if match:
                    module_name = match.group(1)
                    imports.add(module_name)
                    # Don't add partial imports - they cause false positives in enum matching

        return imports

    def _contains_orm_model(self, file_content: str) -> bool:
        """Check if the file contains classes that inherit from ORMModel."""
        # Look for class definitions that inherit from ORMModel
        class_pattern = r"class\s+\w+\s*\([^)]*ORMModel[^)]*\)\s*:"
        return bool(re.search(class_pattern, file_content))

    def _contains_enum_definitions(self, file_content: str) -> bool:
        """Check if the file contains enum definitions."""
        # Look for enum imports and definitions
        enum_patterns = [
            r"from\s+enum\s+import",
            r"import\s+enum",
            r"class\s+\w+\s*\([^)]*Enum[^)]*\)\s*:",
            r"class\s+\w+\s*\([^)]*IntEnum[^)]*\)\s*:",
            r"class\s+\w+\s*\([^)]*StrEnum[^)]*\)\s*:",
        ]

        for pattern in enum_patterns:
            if re.search(pattern, file_content):
                return True
        return False

    def _is_enum_structural(self, relative_path: str, file_content: str) -> bool:
        """Check if an enum file should be considered structural based on usage by ORM files."""
        if not file_content:
            return False

        # If we don't have enum definitions, it's not structural
        if not self._contains_enum_definitions(file_content):
            return False

        # Check if this enum file is in our structural enums cache
        return relative_path in self._structural_enums_cache

    def _update_enum_cache(self, all_files: dict[str, str]) -> None:
        """Incremental cache update: add new files without clearing existing enum cache."""
        # First pass: identify files with ORM models in current batch
        current_structural_files: set[str] = set()

        for relative_path, file_content in all_files.items():
            if self._contains_orm_model(file_content):
                current_structural_files.add(relative_path)
                self._structural_files_cache.add(relative_path)

                # Update imports cache for this file
                imports = self._extract_imports(file_content)
                self._file_imports_cache[relative_path] = imports

        # Second pass: find enum files that are imported by structural files
        # Check current batch for new enum files that should be structural
        for relative_path, file_content in all_files.items():
            if self._contains_enum_definitions(file_content):
                # Skip if already marked as structural
                if relative_path in self._structural_enums_cache:
                    continue

                # Check if any structural file (from all batches) imports this enum
                for structural_file in self._structural_files_cache:
                    structural_imports = self._file_imports_cache.get(
                        structural_file, set[str]()
                    )

                    # Check if any import matches the enum file
                    if self._enum_file_matches_imports(
                        relative_path, structural_imports
                    ):
                        self._structural_enums_cache.add(relative_path)
                        break

        self._cache_dirty = False

    def _enum_file_matches_imports(
        self, enum_file_path: str, imports: set[str]
    ) -> bool:
        """
        Check if an enum file path matches any of the imports using precise matching.

        Args:
            enum_file_path: Relative path to enum file (e.g. "enums/status.py")
            imports: Set of import module names (e.g. "enums.status")

        Returns:
            True if the enum file matches any import
        """
        # Convert file path to potential module names
        file_path_no_ext = str(Path(enum_file_path).with_suffix(""))

        # Strategy 1: Full path conversion - exact match only
        full_module = file_path_no_ext.replace("/", ".").replace("\\", ".")
        if full_module in imports:
            return True

        # Strategy 2: Check if any import exactly matches the file path structure
        # This handles cases where the file path includes extra directory structure
        file_parts = file_path_no_ext.split("/")
        for import_name in imports:
            import_parts = import_name.split(".")

            # Only match if import_parts is an exact suffix of file_parts
            if len(import_parts) <= len(file_parts):
                file_suffix = file_parts[-len(import_parts) :]
                if file_suffix == import_parts:
                    return True

        # No more overly permissive strategies - be precise about matching
        return False

    def clear_cache(self) -> None:
        """Public method to completely clear the cache when needed."""
        self._clear_cache()

    @override
    def update_cache_with_all_files(self, all_files: dict[str, str]):
        """
        Public method to update the cache with repository files.

        Note: This performs incremental updates. If you need to completely refresh
        the cache (e.g., after file deletions), call clear_cache() first.
        """
        self._update_enum_cache(all_files)

    @override
    def is_structural(
        self, relative_path: str, file_content: str | None = None
    ) -> bool:
        """
        Determine if a Python file should be considered structural.

        This now uses a more targeted approach:
        - Files with ORMModel classes are structural
        - Enums are structural only if imported by ORMModel files
        - Uses caching for performance across multiple calls
        """
        # External kernel-injected filter takes precedence if it returns a boolean
        if self.injected_structural_filter is not None:
            decision = self.injected_structural_filter(relative_path, file_content)
            if decision == StructuralFilterDecision.STRUCTURAL:
                return True
            elif decision == StructuralFilterDecision.NON_STRUCTURAL:
                return False
            # Continue with default implementation

        path = Path(relative_path)

        # Path-based exclusions (non-structural) - keep existing logic
        path_str = str(path).lower()
        if any(
            pattern in path_str
            for pattern in [
                "test",
                "tests/",
                "/test_",
                "_test.py",
                "migrations/",  # Only exclude migration directories, not files with "migration" in name
                "/migrations/",  # Database migrations directory
                "alembic/",  # Alembic database migrations
                "/alembic/",  # Alembic database migrations
                "scripts/",
                "script/",
                "utils/",
                "util/",
                "helper",
                "helpers/",
                "example",
                "examples/",
                "demos/",
                "fixtures/",
                "fixture/",
                "mock",
                "mocks/",
            ]
        ):
            return False

        if not file_content:
            return False

        # For performance, if we've already cached this as structural, return true
        if relative_path in self._structural_files_cache:
            return True

        # Check ORM model detection
        if self._contains_orm_model(file_content):
            return True

        # Check if the file contains enum definitions in cache (used by ORM models)
        if self._is_enum_structural(relative_path, file_content):
            return True

        return False


# Create the Python language plugin
_PYTHON_TYPE_PARSER = PythonTypeParser()
_PYTHON_PRIMITIVE_CODEC = PythonPrimitiveCodec(parser=_PYTHON_TYPE_PARSER)
_PYTHON_TYPE_DESCRIPTOR_ADAPTER = PythonTypeDescriptorAdapter(
    parser=_PYTHON_TYPE_PARSER, primitive_codec=_PYTHON_PRIMITIVE_CODEC
)
_PYTHON_COMPILE_SYNTAX_SCRIPT = (
    "import pathlib, sys; "
    "[compile(pathlib.Path(path).read_text(encoding='utf-8'), path, 'exec') "
    "for path in sys.argv[1:]]"
)
_PYTHON_MATERIALIZATION_ARTIFACT_OUTPUTS = (
    CodeLanguageMaterializationOutputDescriptor(
        output_key="python.models_manifest",
        description="Python runtime model location manifest.",
        output_kind="manifest",
        artifact_role="runtime_model_index",
        path_templates=(
            ".aware/materializations/python.models.json",
            "{import_root}/_aware/python.models.json",
        ),
        producer_step="manifest_write",
        required_for=("workspace_revision", "runtime_index", "environment_config"),
        materialization_sources=("ontology", "api", "ontology_orm_models"),
    ),
    CodeLanguageMaterializationOutputDescriptor(
        output_key="python.orm_graph_binding",
        description="Python ORM graph binding package artifact.",
        output_kind="embedded_artifact",
        artifact_role="runtime_binding_snapshot",
        path_templates=("{import_root}/_aware/orm.graph.binding.msgpack",),
        producer_step="artifact_embed",
        required_for=("runtime_index", "environment_config"),
        materialization_sources=("ontology", "api", "ontology_orm_models"),
    ),
    CodeLanguageMaterializationOutputDescriptor(
        output_key="python.ocg_binding_snapshot",
        description="Python DTO ClassConfig binding snapshot package artifact.",
        output_kind="embedded_artifact",
        artifact_role="runtime_class_config_snapshot",
        path_templates=("{import_root}/_aware/ocg.binding.snapshot.msgpack",),
        producer_step="artifact_embed",
        required_for=("runtime_index", "environment_config"),
        materialization_sources=("api", "ontology_dto"),
    ),
    CodeLanguageMaterializationOutputDescriptor(
        output_key="python.bootstrap_manifest",
        description="Python package bootstrap metadata.",
        output_kind="package_metadata",
        artifact_role="package_bootstrap",
        path_templates=("{import_root}/_aware/python.bootstrap.json",),
        producer_step="artifact_embed",
        required_for=("workspace_revision", "runtime_index", "environment_config"),
        materialization_sources=(
            "ontology",
            "api",
            "ontology_dto",
            "ontology_orm_models",
        ),
    ),
    CodeLanguageMaterializationOutputDescriptor(
        output_key="python.ocg_node_paths",
        description="ObjectConfigGraph node path manifest for import resolution.",
        output_kind="manifest",
        artifact_role="dependency_import_resolution",
        path_templates=(
            ".aware/materializations/ocg.node_paths.python.json",
            "{import_root}/_aware/ocg.node_paths.python.json",
        ),
        producer_step="manifest_write",
        required_for=(
            "workspace_revision",
            "runtime_index",
            "environment_config",
            "dependency_import_resolution",
        ),
        materialization_sources=(
            "ontology",
            "api",
            "ontology_dto",
            "ontology_orm_models",
        ),
    ),
    CodeLanguageMaterializationOutputDescriptor(
        output_key="python.meta_runtime_handlers_provider",
        description="Python Meta runtime generated handler provider.",
        output_kind="generated_file",
        artifact_role="meta_runtime_handler_provider",
        path_templates=("handlers/_generated/meta_handlers.py",),
        producer_step="render",
        required_for=(
            "workspace_revision",
            "runtime_index",
            "environment_config",
        ),
        renderer_kinds=("runtime_handlers_meta",),
        materialization_sources=("runtime_handlers",),
        required=True,
        provider_payload={
            "renderer_kind": "runtime_handlers_meta",
            "provider_module": "handlers._generated.meta_handlers",
        },
    ),
)

PYTHON_CODE_PLUGIN = PythonCodeLanguagePlugin(
    language=CodeLanguage.python,
    primitive_codec=_PYTHON_PRIMITIVE_CODEC,
    tree_sitter_adapter=CodeTreeSitterAdapter(
        language=PYTHON_LANGUAGE, allowed_empty_files=["__init__.py"]
    ),
    node_adapters={
        CodeSectionType.attribute: PythonAttributeAdapter(),
        CodeSectionType.class_: PythonClassAdapter(),
        CodeSectionType.comment: PythonCommentAdapter(),
        CodeSectionType.decorator: PythonDecoratorAdapter(),
        CodeSectionType.enum: PythonEnumAdapter(),
        CodeSectionType.enum_value: PythonEnumValueAdapter(),
        CodeSectionType.expression: PythonExpressionAdapter(),
        CodeSectionType.function: PythonFunctionAdapter(),
        CodeSectionType.import_: PythonImportAdapter(),
    },
    metadata_adapters={
        # Python doesn't need complex metadata - just clean description extraction
    },
    extensions=[".py"],
    comment_prefix="#",  # Python uses hash comments
    layout_plugin=PythonCodeLanguagePluginLayout(),  # Python-specific layout handling
    module_discovery=PythonCodeModuleDiscovery(),  # Python-specific module discovery
    package_discovery=PythonCodePackageDiscovery(),  # Python-specific package discovery
    test_discovery=PythonCodeTestDiscovery(),  # Python-specific test discovery
    type_descriptor_adapter=_PYTHON_TYPE_DESCRIPTOR_ADAPTER,
    quality_gates=(
        CodeLanguageQualityGate(
            gate_id="python.compile.syntax",
            description="Validate Python generated artifacts with the Python compiler.",
            command=("uv", "run", "python", "-c", _PYTHON_COMPILE_SYNTAX_SCRIPT),
            target_mode="paths",
        ),
        CodeLanguageQualityGate(
            gate_id="python.flake8",
            description="Run Python lint checks with flake8.",
            command=("uv", "run", "flake8"),
            target_mode="paths",
        ),
        CodeLanguageQualityGate(
            gate_id="python.mypy",
            description="Run Python type checks with mypy.",
            command=("uv", "run", "mypy"),
            target_mode="paths",
        ),
        CodeLanguageQualityGate(
            gate_id="python.basedpyright",
            description="Run Python type checks with basedpyright.",
            command=("uv", "run", "basedpyright"),
            target_mode="paths",
        ),
    ),
    tooling=(
        CodeLanguageToolSpec(
            tool_id="python.format.black",
            language=CodeLanguage.python,
            role="formatter",
            description="Format Python generated artifacts with Black.",
            backend="python_api",
            target_mode="paths",
            module="black",
            callable_name="format_file_in_place",
            version_package="black",
            default_timeout_s=30.0,
            default_batch_size=8,
            mutates_targets=True,
            metadata={
                "line_length": "120",
                "cli_fallback_backend": "cli",
                "materialization_post_step_default": "true",
                "materialization_post_step_order": "10",
                "materialization_post_step_legacy_names": "python.black",
                "materialization_target_suffixes": ".py,.pyi",
            },
        ),
        *create_python_pypi_tool_specs(CodeLanguage.python),
    ),
    materialization_artifact_outputs=_PYTHON_MATERIALIZATION_ARTIFACT_OUTPUTS,
    operational_workspace_builder=PythonOperationalWorkspaceBuilder(),
)
