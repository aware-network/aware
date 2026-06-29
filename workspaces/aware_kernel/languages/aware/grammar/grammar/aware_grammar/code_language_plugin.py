"""Aware language plugin for the code processing system."""

from pathlib import Path

from tree_sitter import Node

from aware_code.module.schemas import CodeModuleInfo
from aware_code.package.schemas import CodePackageInfo
from aware_code.semantic_package.registry import SemanticPackageRegistry
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_section_enums import CodeSectionType

# Aware Primitive Type
from aware_grammar.primitive_codec import AwarePrimitiveCodec
from aware_grammar.type_parser import AwareTypeParser

# Code Runtime Section Adapters
from aware_grammar.adapters.annotation_adapter import AwareAnnotationAdapter
from aware_grammar.adapters.attribute_adapter import AwareAttributeAdapter
from aware_grammar.adapters.binding_adapter import AwareBindingAdapter
from aware_grammar.adapters.class_composite_adapter import AwareClassCompositeAdapter
from aware_grammar.adapters.comment_adapter import AwareCommentAdapter
from aware_grammar.adapters.enum_adapter import AwareEnumAdapter
from aware_grammar.adapters.enum_value_adapter import AwareEnumValueAdapter
from aware_grammar.adapters.function_adapter import AwareFunctionAdapter
from aware_grammar.adapters.import_adapter import AwareImportAdapter
from aware_grammar.adapters.mirror_adapter import AwareMirrorAdapter
from aware_grammar.adapters.projection_adapter import AwareProjectionAdapter
from aware_grammar.code_module_discovery import AwareCodeModuleDiscovery
from aware_grammar.semantic_profile import (
    AwareGrammarSemanticProfile,
    build_current_aware_grammar_semantic_profile,
)

from aware_grammar.type_descriptor_adapter import AwareTypeDescriptorAdapter

# Aware Metadata Adapters
from aware_grammar.metadata.fn_metadata import AwareFunctionMetadata

# Code Runtime
from aware_code.language.plugin import CodeLanguagePlugin
from aware_code.language.schemas import StructuralFilterDecision
from aware_code.node.adapter import CodeNodeAdapter
from aware_code.package.semantic_contract_discovery import (
    SemanticContractCodePackageDiscovery,
)
from aware_code.tree.tree_sitter_adapter import CodeTreeSitterAdapter
from aware_utils.logging import logger
from typing_extensions import override

from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE


class AwareCodeLanguagePlugin(CodeLanguagePlugin[Node]):
    """Aware language plugin with structural filtering capabilities."""

    @override
    def discover_modules(
        self, file_tree: dict[str, str], workspace_root: Path
    ) -> list[CodeModuleInfo]:
        """
        Discover Aware modules from `aware.module.toml`.

        Aware modules are manifest-defined, so discovery scans for module manifests
        directly instead of inferring candidate roots from `.aware` file layout.
        """
        _ = file_tree
        if not self.module_discovery:
            logger.warning(
                f"No module discovery plugin available for {self.language.value}"
            )
            return []
        if isinstance(self.module_discovery, AwareCodeModuleDiscovery):
            self.module_discovery.clear_cache()

        modules: list[CodeModuleInfo] = []
        for module_root in self._iter_module_manifest_roots(workspace_root):
            try:
                module_name = self.module_discovery.get_module_name(
                    module_root, workspace_root
                )
                entry_points = self.module_discovery.get_entry_points(
                    module_root, workspace_root
                )
                metadata = self.module_discovery.get_metadata(
                    module_root, workspace_root
                )
            except Exception as exc:
                logger.warning(
                    f"Failed to resolve Aware module at {module_root}: {exc}"
                )
                continue

            modules.append(
                CodeModuleInfo(
                    name=module_name,
                    root_path=module_root,
                    language=self.language,
                    entry_points=entry_points,
                    metadata=metadata,
                )
            )
            logger.debug(
                f"Discovered {self.language.value} module: {module_name} at {module_root}"
            )

        return modules

    @override
    def discover_packages(
        self, file_tree: dict[str, str], workspace_root: Path
    ) -> list[CodePackageInfo]:
        """
        Discover Aware packages from canonical authored manifests.

        Aware packages are manifest-defined, so discovery scans for package manifests
        directly instead of inferring candidate roots from `.aware` file layout.
        """
        _ = file_tree
        if not self.package_discovery:
            logger.warning(
                f"No package discovery plugin available for {self.language.value}"
            )
            return []
        if isinstance(self.package_discovery, SemanticContractCodePackageDiscovery):
            self.package_discovery.clear_cache()
        SemanticPackageRegistry.ensure_builtin_providers_registered()

        packages: list[CodePackageInfo] = []
        for package_root in self._iter_package_manifest_roots(workspace_root):
            try:
                package_name = self.package_discovery.get_package_name(
                    package_root, workspace_root
                )
                manifest_path = self.package_discovery.get_manifest_path(
                    package_root, workspace_root
                )
                metadata = self.package_discovery.get_metadata(
                    package_root, workspace_root
                )
            except Exception as exc:
                logger.warning(
                    f"Failed to resolve Aware package at {package_root}: {exc}"
                )
                continue

            packages.append(
                SemanticPackageRegistry.enrich_code_package(
                    CodePackageInfo(
                        name=package_name,
                        root_path=package_root,
                        manifest_path=manifest_path,
                        language=self.language,
                        metadata=metadata,
                    )
                )
            )
            logger.debug(
                f"Discovered {self.language.value} package: {package_name} at {package_root}"
            )

        return packages

    @override
    def is_structural(
        self, relative_path: str, file_content: str | None = None
    ) -> bool:
        """
        Determine if an Aware DSL file should be considered structural.

        In Aware DSL, most files are structural by design since they define:
        - Type definitions (type declarations)
        - Edge definitions (relationships)
        - Enum definitions
        - Function signatures

        Non-structural Aware files might include:
        - Test files (test_*.aware, *_test.aware)
        - Example/demo files
        - Temporary/scratch files
        """
        # Respect kernel-injected structural filter if present
        if self.injected_structural_filter is not None:
            try:
                decision = self.injected_structural_filter(relative_path, file_content)
                if decision == StructuralFilterDecision.STRUCTURAL:
                    return True
                elif decision == StructuralFilterDecision.NON_STRUCTURAL:
                    return False
                # UNKNOWN → fall through to Aware-specific heuristics
            except Exception:
                # Ignore injection errors to avoid blocking discovery
                pass

        path = Path(relative_path)
        lower_segments = [segment.lower() for segment in path.parts]
        excluded_dir_names = {
            "tests",
            "test",
            "examples",
            "example",
            "demo",
            "demos",
            "scratch",
            "fixtures",
            "fixture",
        }

        if any(segment in excluded_dir_names for segment in lower_segments[:-1]):
            return False

        # Content-based analysis if available
        if file_content:
            content_lower = file_content.lower()

            # Structural indicators (most Aware constructs are structural)
            structural_patterns = [
                "class ",
                "edge ",  # Core Aware constructs
                "enum ",  # Enum definitions
                "fn ",  # Function definitions
                "primary",
                "ref",  # Relationship markers
                "many",
                "one",  # Cardinality markers
            ]

            # Non-structural indicators
            non_structural_patterns = [
                "// test",
                "// example",  # Comment indicators
                "demo",
                "scratch",  # Content indicators
            ]

            # Count structural vs non-structural indicators
            structural_count = sum(
                1 for pattern in structural_patterns if pattern in content_lower
            )
            non_structural_count = sum(
                1 for pattern in non_structural_patterns if pattern in content_lower
            )

            # If we have strong non-structural indicators, exclude
            if non_structural_count > 0 and structural_count == 0:
                return False

            # If we have any structural constructs, include
            if structural_count > 0:
                return True

        # Path-based exclusions (non-structural). These run after content
        # checks so ontology nouns such as `CodeTest` in `code_test.aware`
        # remain structural when the file declares real Aware constructs.
        path_str = str(path).lower()
        if any(
            pattern in path_str
            for pattern in [
                "test/",
                "/test_",
                "_test.aware",
                "example/",
                "examples/",
                "demo/",
                "demos/",
                "scratch/",
                "fixtures/",
                "fixture/",
            ]
        ):
            return False

        stem = path.stem.lower()
        if stem in {"scratch", "demo", "example"}:
            return False
        if stem.startswith("test_") or stem.endswith("_test"):
            return False

        # Default: Aware files are structural by design
        # .aware files typically define domain models, so they should be in OCG
        # Default to structural
        return True

    @override
    def format_source(self, text: str, *, indent_size: int = 4) -> str | None:
        from aware_grammar.formatter import format_aware_source

        return format_aware_source(text=text, indent_size=indent_size)

    def _iter_module_manifest_roots(self, workspace_root: Path) -> list[Path]:
        ignored_segments = {
            ".aware",
            ".git",
            "__pycache__",
            "node_modules",
            ".venv",
            "venv",
        }
        if self.module_discovery is None:
            return []
        manifest_roots: list[Path] = []
        for manifest_path in sorted(workspace_root.rglob("aware.module.toml")):
            if any(segment in ignored_segments for segment in manifest_path.parts):
                continue
            module_root = manifest_path.parent.resolve()
            try:
                rel_module_root = module_root.relative_to(workspace_root.resolve())
            except Exception:
                logger.debug(
                    f"Skipping Aware manifest outside workspace root: {manifest_path}"
                )
                continue
            if self.module_discovery.is_module_root(rel_module_root, workspace_root):
                manifest_roots.append(rel_module_root)
        return manifest_roots

    def _iter_package_manifest_roots(self, workspace_root: Path) -> list[Path]:
        ignored_segments = {
            ".aware",
            ".git",
            "__pycache__",
            "node_modules",
            ".venv",
            "venv",
        }
        manifest_root_set: set[Path] = set()
        manifest_filenames = (
            self.package_discovery.manifest_filenames()
            if isinstance(self.package_discovery, SemanticContractCodePackageDiscovery)
            else ("aware.toml",)
        )
        for manifest_filename in manifest_filenames:
            for manifest_path in sorted(workspace_root.rglob(manifest_filename)):
                if any(segment in ignored_segments for segment in manifest_path.parts):
                    continue
                package_root = manifest_path.parent.resolve()
                try:
                    rel_package_root = package_root.relative_to(
                        workspace_root.resolve()
                    )
                except Exception:
                    logger.debug(
                        f"Skipping Aware package manifest outside workspace root: {manifest_path}"
                    )
                    continue
                if self.package_discovery and self.package_discovery.is_package_root(
                    rel_package_root, workspace_root
                ):
                    manifest_root_set.add(rel_package_root)
        return sorted(manifest_root_set, key=lambda item: (len(item.parts), str(item)))


# Create the Aware language plugin
_AWARE_TYPE_PARSER = AwareTypeParser()
_AWARE_PRIMITIVE_CODEC = AwarePrimitiveCodec(parser=_AWARE_TYPE_PARSER)
AWARE_GRAMMAR_FULL_PROFILE = build_current_aware_grammar_semantic_profile()


def build_aware_code_language_plugin(
    *,
    profile: AwareGrammarSemanticProfile | None = None,
) -> AwareCodeLanguagePlugin:
    """Build an Aware Code plugin from a semantic grammar profile."""

    semantic_profile = profile or AWARE_GRAMMAR_FULL_PROFILE
    return AwareCodeLanguagePlugin(
        language=CodeLanguage.aware,
        primitive_codec=_AWARE_PRIMITIVE_CODEC,
        tree_sitter_adapter=CodeTreeSitterAdapter(language=AWARE_LANGUAGE),
        node_adapters=_build_aware_node_adapters(profile=semantic_profile),
        metadata_adapters={
            # Use custom metadata adapter for functions to preserve docstring formatting
            CodeSectionType.function: AwareFunctionMetadata,
        },
        extensions=[".aware"],
        comment_prefix="//",  # AWARE uses C-style comments
        type_descriptor_adapter=AwareTypeDescriptorAdapter(
            parser=_AWARE_TYPE_PARSER, primitive_codec=_AWARE_PRIMITIVE_CODEC
        ),
        module_discovery=AwareCodeModuleDiscovery(),
        package_discovery=SemanticContractCodePackageDiscovery(),
    )


def _build_aware_node_adapters(
    *,
    profile: AwareGrammarSemanticProfile,
) -> dict[CodeSectionType, CodeNodeAdapter[Node]]:
    adapters: dict[CodeSectionType, CodeNodeAdapter[Node]] = {}
    if CodeSectionType.binding in profile.code_section_types:
        adapters[CodeSectionType.binding] = AwareBindingAdapter()
    if CodeSectionType.class_ in profile.code_section_types:
        adapters[CodeSectionType.class_] = AwareClassCompositeAdapter()
    if CodeSectionType.comment in profile.code_section_types:
        adapters[CodeSectionType.comment] = AwareCommentAdapter()
    if CodeSectionType.enum in profile.code_section_types:
        adapters[CodeSectionType.enum] = AwareEnumAdapter()
    if CodeSectionType.enum_value in profile.code_section_types:
        adapters[CodeSectionType.enum_value] = AwareEnumValueAdapter()
    if CodeSectionType.attribute in profile.code_section_types:
        adapters[CodeSectionType.attribute] = AwareAttributeAdapter()
    if CodeSectionType.function in profile.code_section_types:
        adapters[CodeSectionType.function] = AwareFunctionAdapter()
    if CodeSectionType.import_ in profile.code_section_types:
        adapters[CodeSectionType.import_] = AwareImportAdapter()
    if CodeSectionType.mirror in profile.code_section_types:
        adapters[CodeSectionType.mirror] = AwareMirrorAdapter()
    if CodeSectionType.projection in profile.code_section_types:
        adapters[CodeSectionType.projection] = AwareProjectionAdapter()
    if CodeSectionType.annotation in profile.code_section_types:
        adapters[CodeSectionType.annotation] = AwareAnnotationAdapter()
    return adapters


AWARE_CODE_PLUGIN = build_aware_code_language_plugin()
