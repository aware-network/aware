from __future__ import annotations

import os
from pathlib import Path
import pytest

# Aware Content
from aware_content.builder import get_text

# Code Runtime
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.writer import CodeSectionWriter

# Kernel Graph Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Meta Ontology
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
    AttributeTypeDescriptorRole,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_link import (
    AttributeTypeDescriptorLink,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.enum.enum_option import EnumOption
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.config.object_config_graph_node_layout import (
    ObjectConfigGraphNodeLayout,
)

# Aware Meta
from aware_meta.graph.config.stable_ids import stable_object_config_graph_node_id
from aware_meta.graph.config.package_strategy import ObjectConfigGraphPackageSpec
from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)

# Dart Grammar
from dart_grammar.layout_strategy import DartLayoutStrategyTemplateMixin
from dart_grammar.package_strategy import DartPackageStrategy
from dart_grammar.renderer import DartRenderer
from dart_grammar.renderer_api_public_package import (
    DartApiPublicPackageLibraryRendererLanguage,
)
from dart_grammar.renderer_model import DartModelRenderer
from dart_grammar_test_support import (
    class_attr_link,
    make_attribute,
    make_class,
    make_class_node,
    make_enum,
)

_DECLARED_WORKSPACE_DEPS = [
    "aware_model_helpers:\n  path: ../aware_model_helpers",
    "aware_api:\n  path: ../aware_api",
]


class _TestDartLayoutStrategy(ObjectConfigGraphRenderLayoutStrategy):
    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.dart

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        return self.base_dir / f"{class_config.name}.dart"

    def get_enum_file_path(self, enum_config: EnumConfig) -> Path:
        return self.base_dir / f"{enum_config.name}.dart"

    def get_function_file_path(self, function_config) -> Path:
        return self.base_dir / "functions.dart"

    def get_file_extension(self) -> str:
        return ".dart"


def test_dart_renderer_uses_named_list_enum_extension(tmp_path: Path) -> None:
    """
    Regression: the Dart renderer must not emit invalid identifiers like `List<Enum>Extension`.

    JsonKey should reference `List{EnumName}Extension` and the corresponding extension
    must be emitted alongside the enum.
    """

    layout = _TestDartLayoutStrategy(base_dir=tmp_path)
    renderer = DartRenderer(layout_strategy=layout)

    enum_cfg = make_enum(name="Status")
    enum_cfg.enum_options = [
        EnumOption(enum_config_id=enum_cfg.id, value="active", position=0),
        EnumOption(enum_config_id=enum_cfg.id, value="inactive", position=1),
    ]

    enum_leaf = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.enum,
        enum_config=enum_cfg,
        enum_config_id=enum_cfg.id,
    )
    list_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.collection,
        collection_kind=AttributeCollectionType.list,
    )
    list_desc.child_links.append(
        AttributeTypeDescriptorLink(
            attribute_type_descriptor_id=list_desc.id,
            child=enum_leaf,
            child_id=enum_leaf.id,
            role=AttributeTypeDescriptorRole.element,
        )
    )

    cls_cfg = make_class(name="User")
    attr_cfg = make_attribute(
        name="statuses",
        owner_key=cls_cfg.class_fqn,
        is_required=True,
        type_descriptor=list_desc,
        type_descriptor_id=list_desc.id,
    )
    cls_cfg.class_config_attribute_configs.append(
        class_attr_link(cls_cfg, attr_cfg, position=0)
    )

    code = renderer.create_empty_code()
    with CodeSectionWriter(
        code, CodeSectionBuilderIndex(), indent_size=renderer.indent
    ) as writer:
        renderer.emit_file([enum_cfg, cls_cfg], writer)

    dart_source = get_text(code.content_part_text)
    assert "List<Status>Extension" not in dart_source
    assert "fromJson: ListStatusExtension.fromJson" in dart_source
    assert "toJson: ListStatusExtension.toJson" in dart_source
    assert "extension ListStatusExtension on List<Status>" in dart_source


def test_dart_model_renderer_imports_cross_file_enum_from_graph_layout(
    tmp_path: Path,
) -> None:
    """
    Regression: current ontology materialization uses graph-derived layout paths,
    not template paths. Cross-file local enum attributes must still render as
    typed enums with JsonKey converters.
    """

    layout = DartLayoutStrategyTemplateMixin(
        base_dir=tmp_path,
        import_root="aware_identity_ontology",
    )
    renderer = DartModelRenderer(layout_strategy=layout)

    enum_cfg = make_enum(name="IdentityType", package="aware_identity")
    enum_cfg.enum_options = [
        EnumOption(enum_config_id=enum_cfg.id, value="agent", position=0),
        EnumOption(enum_config_id=enum_cfg.id, value="human", position=1),
    ]

    cls_cfg = make_class(name="Identity", package="aware_identity")
    enum_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.enum,
        enum_config=enum_cfg,
        enum_config_id=enum_cfg.id,
    )
    attr_cfg = make_attribute(
        name="type",
        owner_key=cls_cfg.class_fqn,
        is_required=True,
        type_descriptor=enum_desc,
        type_descriptor_id=enum_desc.id,
    )
    cls_cfg.class_config_attribute_configs.append(
        class_attr_link(cls_cfg, attr_cfg, position=0)
    )

    graph = ObjectConfigGraph(
        name="identity",
        hash="test",
        fqn_prefix="aware_identity",
        language=CodeLanguage.aware,
    )
    class_node = make_class_node(
        object_config_graph_id=graph.id,
        class_config=cls_cfg,
    )
    class_node.layouts = [
        ObjectConfigGraphNodeLayout(
            object_config_graph_node_id=class_node.id,
            relative_path="identity/identity.dart",
            source_position=10,
        )
    ]
    enum_node_id = stable_object_config_graph_node_id(
        object_config_graph_id=graph.id,
        type=ObjectConfigGraphNodeType.enum.value,
        node_key=enum_cfg.enum_fqn,
    )
    enum_node = ObjectConfigGraphNode(
        id=enum_node_id,
        object_config_graph_id=graph.id,
        type=ObjectConfigGraphNodeType.enum,
        node_key=enum_cfg.enum_fqn,
        enum_config=enum_cfg,
        layouts=[
            ObjectConfigGraphNodeLayout(
                object_config_graph_node_id=enum_node_id,
                relative_path="identity/identity_enums.dart",
                source_position=0,
            )
        ],
    )
    graph.object_config_graph_nodes = [enum_node, class_node]

    renderer.layout_strategy.bind_graph(graph)
    renderer.bind_object_config_graph(graph)

    code = renderer.create_empty_code()
    with CodeSectionWriter(
        code,
        CodeSectionBuilderIndex(),
        indent_size=renderer.indent,
    ) as writer:
        renderer.emit_file([cls_cfg], writer)

    dart_source = get_text(code.content_part_text)
    assert (
        "import 'package:aware_identity_ontology/identity/identity_enums.dart';"
        in dart_source
    )
    assert "fromJson: IdentityTypeExtension.fromJson" in dart_source
    assert "toJson: IdentityTypeExtension.toJson" in dart_source
    assert "required IdentityType type" in dart_source
    assert "required String type" not in dart_source


def test_dart_api_public_package_library_exports_enum_modules(
    tmp_path: Path,
) -> None:
    """
    Regression: API public-package root barrels must export enum-only modules.

    Storage exposes StorageMediaDisposition as a standalone enum DTO. The Dart
    model file is generated, so the public package barrel must export it too.
    """

    layout = DartLayoutStrategyTemplateMixin(
        base_dir=tmp_path,
        import_root="",
    )
    renderer = DartApiPublicPackageLibraryRendererLanguage(layout_strategy=layout)
    renderer.bind_profile_inputs(
        {
            "api.public_package_plan": {
                "package_name": "aware_storage_service_api",
            }
        }
    )

    graph = ObjectConfigGraph(
        name="storage",
        hash="test",
        fqn_prefix="aware_storage_service_dto",
        language=CodeLanguage.aware,
    )

    cls_cfg = make_class(
        name="StorageMediaRef",
        package="aware_storage_service_dto",
    )
    class_node = make_class_node(
        object_config_graph_id=graph.id,
        class_config=cls_cfg,
    )
    class_node.layouts = [
        ObjectConfigGraphNodeLayout(
            object_config_graph_node_id=class_node.id,
            relative_path="default/storage_media_ref.dart",
            source_position=10,
        )
    ]

    enum_cfg = make_enum(
        name="StorageMediaDisposition",
        package="aware_storage_service_dto",
    )
    enum_node_id = stable_object_config_graph_node_id(
        object_config_graph_id=graph.id,
        type=ObjectConfigGraphNodeType.enum.value,
        node_key=enum_cfg.enum_fqn,
    )
    enum_node = ObjectConfigGraphNode(
        id=enum_node_id,
        object_config_graph_id=graph.id,
        type=ObjectConfigGraphNodeType.enum,
        node_key=enum_cfg.enum_fqn,
        enum_config=enum_cfg,
        layouts=[
            ObjectConfigGraphNodeLayout(
                object_config_graph_node_id=enum_node_id,
                relative_path="default/storage_media_disposition.dart",
                source_position=0,
            )
        ],
    )
    graph.object_config_graph_nodes = [enum_node, class_node]

    renderer.layout_strategy.bind_graph(graph)
    renderer.bind_object_config_graph(graph)

    code = renderer.create_empty_code()
    with CodeSectionWriter(
        code,
        CodeSectionBuilderIndex(),
        indent_size=renderer.indent,
    ) as writer:
        renderer.emit_file([], writer)

    dart_source = get_text(code.content_part_text)
    assert "export 'default/storage_media_disposition.dart';" in dart_source
    assert "export 'default/storage_media_ref.dart';" in dart_source


def test_dart_package_strategy_default_sdk_constraint_is_3_8(tmp_path: Path) -> None:
    strategy = DartPackageStrategy(base_dir=tmp_path)
    spec = ObjectConfigGraphPackageSpec(
        name="aware_meta_ontology",
        version="0.1.0",
        dependencies=list(_DECLARED_WORKSPACE_DEPS),
    )
    pubspec = strategy._render_pubspec(
        "aware_meta_ontology", spec, package_root=tmp_path
    )
    assert 'sdk: ">=3.8.0 <4.0.0"' in pubspec


def test_dart_package_strategy_prunes_stale_generated_package_files(
    tmp_path: Path,
) -> None:
    render_root = tmp_path / "render"
    rendered_source = render_root / "environment" / "environment_model.dart"
    rendered_source.parent.mkdir(parents=True)
    rendered_source.write_text("class EnvironmentProfile {}\n", encoding="utf-8")

    package_root = tmp_path / "package"
    stale_source = package_root / "lib" / "default" / "environment_experience.dart"
    stale_generated = (
        package_root / "lib" / "default" / "environment_experience_model.g.dart"
    )
    stale_source.parent.mkdir(parents=True)
    stale_source.write_text("class EnvironmentExperience {}\n", encoding="utf-8")
    stale_generated.write_text("// stale generated part\n", encoding="utf-8")

    strategy = DartPackageStrategy(base_dir=render_root)
    spec = ObjectConfigGraphPackageSpec(
        name="aware_sdk_ontology",
        package_name="aware_sdk_ontology",
        version="0.1.0",
        import_root="",
        dependencies=list(_DECLARED_WORKSPACE_DEPS),
        metadata={"aware_package_kind": "ontology"},
    )

    written_files = strategy.build_into(
        output_root=package_root,
        rendered_files=[rendered_source],
        spec=spec,
    )

    assert package_root / "lib" / "environment" / "environment_model.dart" in {
        path.resolve() for path in written_files
    }
    assert not stale_source.exists()
    assert not stale_generated.exists()


def test_dart_package_strategy_resolves_workspace_dependencies_via_ancestor_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = tmp_path / "repo"
    sample_root = repo_root / "samples" / "home_story"
    package_root = sample_root / "modules" / "home" / "structure" / "ontology" / "dart"
    package_root.mkdir(parents=True, exist_ok=True)
    (sample_root / "aware.environment.toml").write_text("aware = 1\n", encoding="utf-8")

    helpers_dir = repo_root / "libs" / "model_helpers" / "dart" / "aware_model_helpers"
    helpers_dir.mkdir(parents=True, exist_ok=True)
    aware_api_dir = repo_root / "libs" / "api" / "dart"
    aware_api_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("AWARE_REPO_ROOT", str(sample_root))

    strategy = DartPackageStrategy(base_dir=tmp_path)
    spec = ObjectConfigGraphPackageSpec(name="aware_home_ontology", version="0.1.0")
    pubspec = strategy._render_pubspec(
        "aware_home_ontology",
        spec,
        package_root=package_root,
    )

    expected_helpers_rel = Path(
        os.path.relpath(helpers_dir.resolve(), start=package_root.resolve())
    ).as_posix()
    expected_api_rel = Path(
        os.path.relpath(aware_api_dir.resolve(), start=package_root.resolve())
    ).as_posix()

    assert "aware_model_helpers:" in pubspec
    assert f"path: {expected_helpers_rel}" in pubspec
    assert "aware_api:" in pubspec
    assert f"path: {expected_api_rel}" in pubspec


def test_dart_package_strategy_uses_declared_path_dependencies(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    package_root = repo_root / ".aware" / "api" / "runtime" / "story" / "dart"
    package_root.mkdir(parents=True, exist_ok=True)
    helpers_dir = repo_root / "libs" / "model_helpers" / "dart" / "aware_model_helpers"
    helpers_dir.mkdir(parents=True, exist_ok=True)
    aware_api_dir = (
        repo_root
        / "workspaces"
        / "aware_kernel"
        / "modules"
        / "api"
        / "libs"
        / "api"
        / "dart"
    )
    aware_api_dir.mkdir(parents=True, exist_ok=True)
    (aware_api_dir / "pubspec.yaml").write_text("name: aware_api\n", encoding="utf-8")
    (helpers_dir / "pubspec.yaml").write_text(
        "name: aware_model_helpers\n", encoding="utf-8"
    )

    strategy = DartPackageStrategy(base_dir=tmp_path)
    spec = ObjectConfigGraphPackageSpec(
        name="aware_story_api",
        version="0.1.0",
        metadata={
            "aware_package_kind": "api_public_package",
            "repo_root": repo_root.as_posix(),
            "path_dependencies": {
                "aware_api": "workspaces/aware_kernel/modules/api/libs/api/dart",
                "aware_model_helpers": "libs/model_helpers/dart/aware_model_helpers",
            },
        },
    )
    pubspec = strategy._render_pubspec(
        "aware_story_api",
        spec,
        package_root=package_root,
    )

    expected_api_rel = Path(
        os.path.relpath(aware_api_dir.resolve(), start=package_root.resolve())
    ).as_posix()
    expected_helpers_rel = Path(
        os.path.relpath(helpers_dir.resolve(), start=package_root.resolve())
    ).as_posix()
    assert pubspec.count("aware_api:") == 1
    assert f"path: {expected_api_rel}" in pubspec
    assert pubspec.count("aware_model_helpers:") == 1
    assert f"path: {expected_helpers_rel}" in pubspec


def test_dart_package_strategy_adds_ontology_dependency_paths_from_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = tmp_path / "repo"
    package_root = repo_root / "modules" / "sdk" / "structure" / "ontology" / "dart"
    package_root.mkdir(parents=True, exist_ok=True)
    (repo_root / "aware.environment.toml").write_text("aware = 1\n", encoding="utf-8")
    helpers_dir = repo_root / "libs" / "model_helpers" / "dart" / "aware_model_helpers"
    helpers_dir.mkdir(parents=True, exist_ok=True)
    aware_api_dir = repo_root / "libs" / "api" / "dart"
    aware_api_dir.mkdir(parents=True, exist_ok=True)
    api_ontology_dir = repo_root / "modules" / "api" / "structure" / "ontology" / "dart"
    api_ontology_dir.mkdir(parents=True, exist_ok=True)
    (api_ontology_dir / "pubspec.yaml").write_text(
        "name: aware_api_ontology\n", encoding="utf-8"
    )
    meta_dto_dir = (
        repo_root / "modules" / "meta" / "structure" / "ontology_dto" / "dart"
    )
    meta_dto_dir.mkdir(parents=True, exist_ok=True)
    (meta_dto_dir / "pubspec.yaml").write_text(
        "name: aware_meta_ontology_dto\n", encoding="utf-8"
    )

    monkeypatch.setenv("AWARE_REPO_ROOT", str(repo_root))

    strategy = DartPackageStrategy(base_dir=tmp_path)
    spec = ObjectConfigGraphPackageSpec(
        name="aware_sdk_ontology",
        version="0.1.0",
        metadata={
            "dependency_import_roots": [
                "aware_api_ontology",
                "aware_meta_ontology_dto",
            ]
        },
    )
    pubspec = strategy._render_pubspec(
        "aware_sdk_ontology",
        spec,
        package_root=package_root,
    )

    expected_api_rel = Path(
        os.path.relpath(api_ontology_dir.resolve(), start=package_root.resolve())
    ).as_posix()
    expected_meta_dto_rel = Path(
        os.path.relpath(meta_dto_dir.resolve(), start=package_root.resolve())
    ).as_posix()

    assert "aware_api_ontology:" in pubspec
    assert f"path: {expected_api_rel}" in pubspec
    assert "aware_meta_ontology_dto:" in pubspec
    assert f"path: {expected_meta_dto_rel}" in pubspec


def test_dart_package_strategy_emits_flutter_stanza_for_flutter_packages(
    tmp_path: Path,
) -> None:
    strategy = DartPackageStrategy(base_dir=tmp_path)
    spec = ObjectConfigGraphPackageSpec(
        name="aware_widget_kit",
        version="0.1.0",
        dependencies=list(_DECLARED_WORKSPACE_DEPS),
        metadata={"flutter_package": "true"},
    )

    pubspec = strategy._render_pubspec(
        "aware_widget_kit",
        spec,
        package_root=tmp_path,
    )

    assert "  flutter:\n    sdk: flutter" in pubspec
    assert "flutter:\n  uses-material-design: true" in pubspec


def test_dart_package_strategy_preserves_uses_material_design_metadata(
    tmp_path: Path,
) -> None:
    strategy = DartPackageStrategy(base_dir=tmp_path)
    spec = ObjectConfigGraphPackageSpec(
        name="aware_terminal_surface",
        version="0.1.0",
        dependencies=list(_DECLARED_WORKSPACE_DEPS),
        metadata={
            "flutter_package": "true",
            "uses_material_design": "false",
        },
    )

    pubspec = strategy._render_pubspec(
        "aware_terminal_surface",
        spec,
        package_root=tmp_path,
    )

    assert "flutter:\n  uses-material-design: false" in pubspec
