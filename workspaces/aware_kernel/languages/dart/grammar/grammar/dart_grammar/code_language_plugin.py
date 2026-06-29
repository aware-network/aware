"""Dart language plugin for the code processing system."""

from pathlib import Path
from typing_extensions import override

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_section_enums import CodeSectionType

from aware_code.language.plugin import (
    CodeLanguagePlugin,
    CodeLanguageQualityGate,
)
from aware_code.language.layout import CodeLanguagePluginLayout
from aware_code.language.schemas import CodeDomain, CodeSchema, StructuralFilterDecision
from aware_code.language.test_discovery import CodeLanguageTestDiscovery
from aware_code.language.tooling import (
    CodeLanguageToolSpec,
    CodeLanguageToolStateRequirement,
)
from aware_code.module.discovery import CodeModuleDiscovery
from aware_code.node.adapter import CodeNodeAdapter
from aware_code.package.discovery import CodePackageDiscovery
from aware_code.primitive_codec import CodePrimitiveCodec
from aware_code.section.metadata import CodeSectionMetadata
from aware_code.tree.tree_sitter_adapter import CodeTreeSitterAdapter
from tree_sitter import Node

# Dart Primitive Type
from dart_grammar.primitive_codec import DartPrimitiveCodec
from dart_grammar.type_descriptor_adapter import DartTypeDescriptorAdapter
from dart_grammar.type_parser import DartTypeParser

# Dart Module Discovery
from dart_grammar.module_discovery import DartCodeModuleDiscovery
from dart_grammar.code_package_discovery import DartCodePackageDiscovery
from dart_grammar.code_test_discovery import DartCodeTestDiscovery

# Adapters
from dart_grammar.adapters.attribute_adapter import DartAttributeAdapter
from dart_grammar.adapters.class_adapter import DartClassAdapter
from dart_grammar.adapters.import_adapter import DartImportAdapter
from dart_grammar.adapters.enum_adapter import DartEnumAdapter
from dart_grammar.adapters.enum_value_adapter import DartEnumValueAdapter
from dart_grammar.adapters.function_adapter import DartFunctionAdapter
from dart_grammar.adapters.comment_adapter import DartCommentAdapter
from dart_grammar.adapters.decorator_adapter import DartDecoratorAdapter
from dart_grammar.adapters.expression_adapter import DartExpressionAdapter

from dart_grammar._tree_sitter_dart import DART_LANGUAGE


class DartCodeLanguagePlugin(CodeLanguagePlugin[Node]):
    """Dart language plugin with basic structural filtering."""

    def __init__(
        self,
        language: CodeLanguage,
        primitive_codec: CodePrimitiveCodec,
        tree_sitter_adapter: CodeTreeSitterAdapter,
        node_adapters: dict[CodeSectionType, CodeNodeAdapter[Node]],
        metadata_adapters: dict[CodeSectionType, type[CodeSectionMetadata]],
        extensions: list[str],
        comment_prefix: str,
        type_descriptor_adapter: DartTypeDescriptorAdapter,
        layout_plugin: CodeLanguagePluginLayout | None = None,
        module_discovery: CodeModuleDiscovery | None = None,
        package_discovery: CodePackageDiscovery | None = None,
        test_discovery: CodeLanguageTestDiscovery | None = None,
        quality_gates: tuple[CodeLanguageQualityGate, ...] = (),
        tooling: tuple[CodeLanguageToolSpec, ...] = (),
    ) -> None:
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
        )

    @override
    def is_structural(
        self, relative_path: str, file_content: str | None = None
    ) -> bool:
        """
        Determine if a Dart file should be considered structural.

        For Dart/Flutter projects, structural files are typically:
        - Model files in lib/ directories
        - Files that define classes with data structures
        - Files that contain @freezed or similar data model annotations
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

        # Path-based exclusions (non-structural)
        path_str = str(path).lower()
        if any(
            pattern in path_str
            for pattern in [
                "test",
                "tests/",
                "/test_",
                "_test.dart",
                "example",
                "examples/",
                ".dart_tool/",
                "build/",
                "android/",
                "ios/",
                "linux/",
                "macos/",
                "web/",
                "windows/",
            ]
        ):
            return False

        # Only process .dart files
        if path.suffix.lower() != ".dart":
            return False

        # Files in lib/ directory are likely structural
        if "lib/" in str(path) or str(path).startswith("lib/"):
            # Additional content-based filtering if we have file content
            if file_content:
                # Look for structural indicators
                structural_indicators = [
                    "@freezed",
                    "@JsonSerializable",
                    "class ",
                    "enum ",
                    "mixin ",
                    "extension ",
                    "part of ",
                    "part '",
                ]

                content_lower = file_content.lower()
                if any(
                    indicator.lower() in content_lower
                    for indicator in structural_indicators
                ):
                    return True

                # If it's in lib/ but has no structural indicators, might be utility/logic
                return False

            # Default to structural for lib/ files when no content analysis
            return True

        return False


class DartAwareModelsLayout(CodeLanguagePluginLayout):
    """Layout extractor for Dart aware_models.

    Interprets paths like:
    languages/dart/domains/aware_models/lib/<domain>/<schema>/... ->
      domain = <domain>, schema = <schema>
      domain_path = languages/dart/domains/aware_models/lib/<domain>
      schema_path = <schema>
    """

    @override
    def extract_domains_and_schemas(
        self,
        file_paths: list[str],
        language: CodeLanguage,
        enforce_domains_layout: bool = False,
    ) -> list[CodeDomain]:
        domains_map: dict[str, set[str]] = {}
        domain_paths: dict[str, str] = {}

        for rel_path in file_paths:
            parts = list(Path(rel_path).parts)
            # Find the 'domains' segment
            try:
                idx = parts.index("domains")
            except ValueError:
                continue

            # Require explicit aware_models/lib structure
            # Need at least: domains/aware_models/lib/<domain>/<schema>
            if len(parts) < idx + 5:
                continue
            if parts[idx + 1] != "aware_models" or parts[idx + 2] != "lib":
                continue

            domain_name = parts[idx + 3]
            raw_schema_name = parts[idx + 4]

            # Normalize known schema aliases for Dart layout without changing the path.
            # Only apply for meta: class_ -> class. Do NOT alias identity:auth (kept explicit).
            schema_name = self._normalize_schema_name(domain_name, raw_schema_name)

            # Build domain path up to <domain>
            domain_path = "/".join(parts[: idx + 4])

            domain_paths[domain_name] = domain_path
            if domain_name not in domains_map:
                domains_map[domain_name] = set()
            domains_map[domain_name].add(schema_name)

        result: list[CodeDomain] = []
        for domain_name, schema_set in domains_map.items():
            domain_path = domain_paths.get(domain_name, "")
            # Keep the on-disk folder as the path, but expose normalized schema names.
            # Since we only normalize meta/class_ -> meta/class, the folder stays 'class_' while
            # the logical schema is 'class'. For other schemas, name == path.
            schemas = [
                CodeSchema(
                    name=schema,
                    path=(
                        "class_"
                        if (domain_name == "meta" and schema == "class")
                        else schema
                    ),
                )
                for schema in sorted(schema_set)
            ]
            result.append(
                CodeDomain(name=domain_name, path=domain_path, schemas=schemas)
            )

        return result

    def _normalize_schema_name(self, domain: str, schema: str) -> str:
        """
        Normalize Dart-specific folder names to canonical schema names without changing paths.

        - meta: class_ -> class
        - all others unchanged (e.g., identity:auth stays as 'auth')
        """
        if domain == "meta" and schema == "class_":
            return "class"
        return schema


# Create a factory function for Dart language plugin
def create_dart_code_plugin() -> DartCodeLanguagePlugin:
    """Create Dart language plugin with adapters and tree-sitter configuration."""

    # The language binding is required for Dart grammar boot.
    tree_sitter_adapter = CodeTreeSitterAdapter(language=DART_LANGUAGE)

    node_adapters: dict[CodeSectionType, CodeNodeAdapter[Node]] = {
        CodeSectionType.attribute: DartAttributeAdapter(),
        CodeSectionType.class_: DartClassAdapter(),
        CodeSectionType.import_: DartImportAdapter(),
        CodeSectionType.enum: DartEnumAdapter(),
        CodeSectionType.enum_value: DartEnumValueAdapter(),
        CodeSectionType.function: DartFunctionAdapter(),
        CodeSectionType.comment: DartCommentAdapter(),
        CodeSectionType.decorator: DartDecoratorAdapter(),
        CodeSectionType.expression: DartExpressionAdapter(),
    }

    # Singletons: shared parser + codec + adapter
    type_parser = DartTypeParser()
    primitive_codec = DartPrimitiveCodec(parser=type_parser)
    type_descriptor_adapter = DartTypeDescriptorAdapter(
        parser=type_parser, primitive_codec=primitive_codec
    )

    return DartCodeLanguagePlugin(
        language=CodeLanguage.dart,
        primitive_codec=primitive_codec,
        tree_sitter_adapter=tree_sitter_adapter,
        node_adapters=node_adapters,
        metadata_adapters={},
        extensions=[".dart"],
        comment_prefix="//",
        type_descriptor_adapter=type_descriptor_adapter,
        layout_plugin=DartAwareModelsLayout(),
        module_discovery=DartCodeModuleDiscovery(),
        package_discovery=DartCodePackageDiscovery(),
        test_discovery=DartCodeTestDiscovery(),
        quality_gates=(
            CodeLanguageQualityGate(
                gate_id="dart.analyze",
                description="Run Dart static analysis.",
                command=("dart", "analyze"),
                target_mode="paths",
            ),
        ),
        tooling=(
            CodeLanguageToolSpec(
                tool_id="dart.format",
                language=CodeLanguage.dart,
                role="formatter",
                description="Format Dart sources.",
                backend="cli",
                target_mode="paths",
                command=("dart", "format"),
                default_timeout_s=30.0,
                mutates_targets=True,
                metadata={
                    "materialization_post_step_default": "true",
                    "materialization_post_step_order": "20",
                    "materialization_post_step_warn_if_missing": "true",
                    "materialization_post_step_missing_warning": (
                        "Dart formatting is not enforced for this packaged "
                        + "materialization. Add post_step name='dart.format' "
                        + "(or remove explicit post_steps to use strict defaults)."
                    ),
                    "materialization_target_suffixes": ".dart",
                    "materialization_target_search_roots": "lib",
                },
                state_requirements=(
                    CodeLanguageToolStateRequirement(
                        key="home",
                        kind="home",
                        env_var="HOME",
                        default_subdir="home",
                    ),
                ),
            ),
            CodeLanguageToolSpec(
                tool_id="dart.pub_get",
                language=CodeLanguage.dart,
                role="dependency_resolver",
                description="Resolve Dart package dependencies.",
                backend="cli",
                target_mode="package_root",
                command=("dart", "pub", "get"),
                default_timeout_s=120.0,
                mutates_targets=True,
                network=True,
                metadata={
                    "materialization_post_step_default": "true",
                    "materialization_post_step_order": "5",
                    "materialization_target_suffixes": ".dart",
                    "materialization_target_search_roots": "lib",
                },
                state_requirements=(
                    CodeLanguageToolStateRequirement(
                        key="home",
                        kind="home",
                        env_var="HOME",
                        default_subdir="home",
                    ),
                    CodeLanguageToolStateRequirement(
                        key="pub_cache",
                        kind="cache",
                        env_var="PUB_CACHE",
                        default_subdir="pub-cache",
                    ),
                ),
            ),
            CodeLanguageToolSpec(
                tool_id="dart.build_runner",
                language=CodeLanguage.dart,
                role="code_generator",
                description="Generate Dart package build artifacts with build_runner.",
                backend="cli",
                target_mode="package_root",
                command=(
                    "dart",
                    "run",
                    "build_runner",
                    "build",
                    "--delete-conflicting-outputs",
                ),
                default_timeout_s=600.0,
                mutates_targets=True,
                metadata={
                    "materialization_post_step_default": "true",
                    "materialization_post_step_order": "10",
                    "materialization_target_suffixes": ".dart",
                    "materialization_target_search_roots": "lib",
                    "materialization_target_excluded_suffixes": ".g.dart,.freezed.dart",
                },
                state_requirements=(
                    CodeLanguageToolStateRequirement(
                        key="home",
                        kind="home",
                        env_var="HOME",
                        default_subdir="home",
                    ),
                    CodeLanguageToolStateRequirement(
                        key="pub_cache",
                        kind="cache",
                        env_var="PUB_CACHE",
                        default_subdir="pub-cache",
                    ),
                ),
            ),
        ),
    )


# Create the default Dart language plugin
DART_CODE_PLUGIN = create_dart_code_plugin()
