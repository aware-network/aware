from __future__ import annotations

import logging
from pathlib import Path
from uuid import uuid4

import pytest

# Aware ORM
from aware_orm.session.autobind import disable_autobind

# Kernel Graph Ontology
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_annotation import (
    ObjectConfigGraphAnnotation,
)
from aware_meta_ontology.graph.config.object_config_graph_annotation_enums import (
    ObjectConfigGraphAnnotationKind,
)
from aware_meta_ontology.annotation.code_section_annotation_discriminate import (
    CodeSectionAnnotationDiscriminate,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig

# Aware Meta
from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)

# Dart Grammar
from dart_grammar.renderer import DartRenderer
from dart_grammar_test_support import (
    class_attr_link,
    make_attribute,
    make_class,
    make_class_node,
)


class _TestDartLayoutStrategy(ObjectConfigGraphRenderLayoutStrategy):
    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.dart

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        return self.base_dir / f"{class_config.name}.dart"

    def get_enum_file_path(self, enum_config) -> Path:
        return self.base_dir / "enums.dart"

    def get_function_file_path(self, function_config) -> Path:
        return self.base_dir / "functions.dart"

    def get_file_extension(self) -> str:
        return ".dart"

    def get_module_import_path(self, file_path: Path) -> str:
        return f"package:test/{file_path.name}"


def _attr(name: str, *, owner_key: str) -> AttributeConfig:
    td = AttributeTypeDescriptor(kind=AttributeTypeDescriptorKind.primitive)
    return make_attribute(name=name, owner_key=owner_key, type_descriptor=td)


def _ann(
    *,
    ocg_id,
    pkg: str,
    domain: str,
    schema: str,
    cls: str,
    attr: str,
    mode: str,
    tag: str | None = None,
    source_position: int | None = None,
) -> ObjectConfigGraphAnnotation:
    disc = CodeSectionAnnotationDiscriminate(
        code_section_annotation_id=uuid4(),
        fqn_prefix=pkg,
        namespace=schema,
        domain_name=domain,
        schema_name=schema,
        class_name=cls,
        attribute_name=attr,
        mode=mode,
        tag_value=tag,
        source_position=source_position,
    )
    return ObjectConfigGraphAnnotation(
        object_config_graph_id=ocg_id,
        kind=ObjectConfigGraphAnnotationKind.discriminate,
        code_section_annotation_discriminate=disc,
        code_section_annotation_discriminate_id=disc.id,
    )


def test_dart_renderer_resolves_external_base_discriminator(
    caplog: pytest.LogCaptureFixture, tmp_path: Path
) -> None:
    layout = _TestDartLayoutStrategy(base_dir=tmp_path)
    renderer = DartRenderer(layout_strategy=layout)

    with disable_autobind():
        base_cls = make_class(name="NetworkNodeOperationRequest")
        base_attr = _attr("operation", owner_key=base_cls.class_fqn)
        base_cls.class_config_attribute_configs = [class_attr_link(base_cls, base_attr)]
        variant_cls = make_class(
            name="IdentityChallengeRequest",
            parent_class_id=base_cls.id,
        )

    external_graph = ObjectConfigGraph(
        name="network",
        description=None,
        hash="external",
        fqn_prefix="aware_network_service_dto",
        language=CodeLanguage.aware,
    )
    external_graph.object_config_graph_nodes = [
        make_class_node(object_config_graph_id=external_graph.id, class_config=base_cls)
    ]
    external_graph.object_config_graph_annotations = [
        _ann(
            ocg_id=external_graph.id,
            pkg="aware_network_service_dto",
            domain="comms",
            schema="models",
            cls="NetworkNodeOperationRequest",
            attr="operation",
            mode="key",
            source_position=0,
        )
    ]

    local_graph = ObjectConfigGraph(
        name="identity",
        description=None,
        hash="local",
        fqn_prefix="aware_identity_api",
        language=CodeLanguage.aware,
    )
    local_graph.object_config_graph_nodes = [
        make_class_node(object_config_graph_id=local_graph.id, class_config=variant_cls)
    ]
    local_graph.object_config_graph_annotations = [
        _ann(
            ocg_id=local_graph.id,
            pkg="aware_identity_api",
            domain="identity",
            schema="session",
            cls="IdentityChallengeRequest",
            attr="operation",
            mode="tag",
            tag="identity_challenge",
            source_position=1,
        )
    ]

    renderer.external_graphs = [external_graph]
    with caplog.at_level(logging.WARNING):
        renderer.bind_object_config_graph(local_graph)

    assert not renderer._discriminated_unions_by_base_id  # type: ignore[attr-defined]
    assert not renderer._discriminated_union_base_id_by_variant_id  # type: ignore[attr-defined]
    assert not any(
        "has no ancestor discriminate key" in record.message
        for record in caplog.records
    )
