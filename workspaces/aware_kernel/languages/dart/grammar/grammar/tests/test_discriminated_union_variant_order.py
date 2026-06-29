from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from aware_orm.session.autobind import disable_autobind

from aware_code_ontology.code.code_enums import CodeLanguage
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
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_annotation import (
    ObjectConfigGraphAnnotation,
)
from aware_meta_ontology.graph.config.object_config_graph_annotation_enums import (
    ObjectConfigGraphAnnotationKind,
)

from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)

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
        mapping = {
            "EnvironmentServiceOperation": self.base_dir / "base.dart",
            "AlphaOperation": self.base_dir / "b.dart",
            "ZuluOperation": self.base_dir / "a.dart",
        }
        return mapping.get(
            class_config.name, self.base_dir / f"{class_config.name}.dart"
        )

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


def test_dart_renderer_orders_union_variants_by_position(tmp_path: Path) -> None:
    layout = _TestDartLayoutStrategy(base_dir=tmp_path)
    renderer = DartRenderer(layout_strategy=layout)

    with disable_autobind():
        base_cls = make_class(name="EnvironmentServiceOperation")
        base_attr = _attr("service", owner_key=base_cls.class_fqn)
        base_cls.class_config_attribute_configs = [class_attr_link(base_cls, base_attr)]
        alpha_cls = make_class(name="AlphaOperation", parent_class_id=base_cls.id)
        zulu_cls = make_class(name="ZuluOperation", parent_class_id=base_cls.id)

    graph = ObjectConfigGraph(
        name="environment",
        description=None,
        hash="local",
        fqn_prefix="aware_environment_api",
        language=CodeLanguage.aware,
    )
    graph.object_config_graph_nodes = [
        make_class_node(object_config_graph_id=graph.id, class_config=base_cls),
        make_class_node(object_config_graph_id=graph.id, class_config=alpha_cls),
        make_class_node(object_config_graph_id=graph.id, class_config=zulu_cls),
    ]
    graph.object_config_graph_annotations = [
        _ann(
            ocg_id=graph.id,
            pkg="aware_environment_api",
            domain="comms",
            schema="models",
            cls="EnvironmentServiceOperation",
            attr="service",
            mode="key",
        ),
        _ann(
            ocg_id=graph.id,
            pkg="aware_environment_api",
            domain="comms",
            schema="models",
            cls="AlphaOperation",
            attr="service",
            mode="tag",
            tag="alpha",
            source_position=1,
        ),
        _ann(
            ocg_id=graph.id,
            pkg="aware_environment_api",
            domain="comms",
            schema="models",
            cls="ZuluOperation",
            attr="service",
            mode="tag",
            tag="zulu",
            source_position=0,
        ),
    ]

    renderer.bind_object_config_graph(graph)

    union = renderer._discriminated_unions_by_base_id.get(base_cls.id)  # type: ignore[attr-defined]
    assert union is not None
    assert [variant.class_config.name for variant in union.variants] == [
        "ZuluOperation",
        "AlphaOperation",
    ]
