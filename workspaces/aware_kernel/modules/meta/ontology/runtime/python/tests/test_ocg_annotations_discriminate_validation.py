from __future__ import annotations

from uuid import UUID, uuid4

import pytest

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
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.graph.config.object_config_graph_annotation import (
    ObjectConfigGraphAnnotation,
)
from aware_meta_ontology.graph.config.object_config_graph_annotation_enums import (
    ObjectConfigGraphAnnotationKind,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.annotation.handlers import (
    validate_discriminate_annotations,
)
from aware_meta.test_support import (
    make_attribute_config,
    make_class_attribute_edge,
    make_class_config,
    make_ocg_node,
    test_class_fqn,
)


def _attr(name: str) -> AttributeConfig:
    td = AttributeTypeDescriptor(kind=AttributeTypeDescriptorKind.primitive)
    return make_attribute_config(
        owner_key=test_class_fqn("Base"), name=name, type_descriptor=td
    )


def _class_with_attrs(
    *,
    name: str,
    attrs: list[AttributeConfig],
    parent_id: UUID | None = None,
) -> ClassConfig:
    c = make_class_config(
        name, class_fqn=test_class_fqn(name), parent_class_id=parent_id
    )
    c.class_config_attribute_configs = [
        make_class_attribute_edge(class_config_id=c.id, attribute_config=a, name=a.name)
        for a in attrs
    ]
    return c


def _ann_view(
    *,
    pkg: str,
    namespace: str,
    cls: str,
    attr: str,
    mode: str,
    tag: str | None = None,
) -> CodeSectionAnnotationDiscriminate:
    return CodeSectionAnnotationDiscriminate(
        code_section_annotation_id=uuid4(),
        fqn_prefix=pkg,
        namespace=namespace,
        class_name=cls,
        attribute_name=attr,
        mode=mode,
        tag_value=tag,
    )


def _ann(
    ocg_id: UUID, view: CodeSectionAnnotationDiscriminate
) -> ObjectConfigGraphAnnotation:
    return ObjectConfigGraphAnnotation(
        object_config_graph_id=ocg_id,
        kind=ObjectConfigGraphAnnotationKind.discriminate,
        code_section_annotation_discriminate=view,
        code_section_annotation_discriminate_id=view.id,
    )


def test_discriminate_validation_ok_inherited_discriminator_field():
    ocg_id = uuid4()
    ns = NamespacePath(package="pkg", namespace="d.s")

    base = _class_with_attrs(name="Base", attrs=[_attr("kind")])
    v1 = _class_with_attrs(name="V1", attrs=[], parent_id=base.id)
    v2 = _class_with_attrs(name="V2", attrs=[], parent_id=base.id)

    anns = [
        _ann(
            ocg_id,
            _ann_view(
                pkg="pkg", namespace="d.s", cls="Base", attr="kind", mode="key"
            ),
        ),
        _ann(
            ocg_id,
            _ann_view(
                pkg="pkg",
                namespace="d.s",
                cls="V1",
                attr="kind",
                mode="tag",
                tag="v1",
            ),
        ),
        _ann(
            ocg_id,
            _ann_view(
                pkg="pkg",
                namespace="d.s",
                cls="V2",
                attr="kind",
                mode="tag",
                tag="v2",
            ),
        ),
    ]

    validate_discriminate_annotations(
        compiled_annotations=anns,
        class_configs=[base, v1, v2],
        namespace_by_class_config_id={base.id: ns, v1.id: ns, v2.id: ns},
    )


def test_discriminate_validation_duplicate_key_raises():
    ocg_id = uuid4()
    ns = NamespacePath(package="pkg", namespace="d.s")

    base = _class_with_attrs(name="Base", attrs=[_attr("kind"), _attr("kind2")])
    anns = [
        _ann(
            ocg_id,
            _ann_view(
                pkg="pkg", namespace="d.s", cls="Base", attr="kind", mode="key"
            ),
        ),
        _ann(
            ocg_id,
            _ann_view(
                pkg="pkg", namespace="d.s", cls="Base", attr="kind2", mode="key"
            ),
        ),
    ]

    with pytest.raises(ValueError, match="key already declared"):
        validate_discriminate_annotations(
            compiled_annotations=anns,
            class_configs=[base],
            namespace_by_class_config_id={base.id: ns},
        )


def test_discriminate_validation_tag_without_base_key_raises():
    ocg_id = uuid4()
    ns = NamespacePath(package="pkg", namespace="d.s")

    base = _class_with_attrs(name="Base", attrs=[_attr("kind")])
    v1 = _class_with_attrs(name="V1", attrs=[], parent_id=base.id)
    anns = [
        _ann(
            ocg_id,
            _ann_view(
                pkg="pkg",
                namespace="d.s",
                cls="V1",
                attr="kind",
                mode="tag",
                tag="v1",
            ),
        ),
    ]

    with pytest.raises(ValueError, match="no base class with a DISCRIMINATE key"):
        validate_discriminate_annotations(
            compiled_annotations=anns,
            class_configs=[base, v1],
            namespace_by_class_config_id={base.id: ns, v1.id: ns},
        )


def test_discriminate_validation_tag_must_match_base_attribute_raises():
    ocg_id = uuid4()
    ns = NamespacePath(package="pkg", namespace="d.s")

    base = _class_with_attrs(name="Base", attrs=[_attr("kind"), _attr("other")])
    v1 = _class_with_attrs(name="V1", attrs=[], parent_id=base.id)
    anns = [
        _ann(
            ocg_id,
            _ann_view(
                pkg="pkg", namespace="d.s", cls="Base", attr="kind", mode="key"
            ),
        ),
        _ann(
            ocg_id,
            _ann_view(
                pkg="pkg",
                namespace="d.s",
                cls="V1",
                attr="other",
                mode="tag",
                tag="v1",
            ),
        ),
    ]

    with pytest.raises(ValueError, match="does not match base discriminator attribute"):
        validate_discriminate_annotations(
            compiled_annotations=anns,
            class_configs=[base, v1],
            namespace_by_class_config_id={base.id: ns, v1.id: ns},
        )


def test_discriminate_validation_duplicate_tag_raises():
    ocg_id = uuid4()
    ns = NamespacePath(package="pkg", namespace="d.s")

    base = _class_with_attrs(name="Base", attrs=[_attr("kind")])
    v1 = _class_with_attrs(name="V1", attrs=[], parent_id=base.id)
    v2 = _class_with_attrs(name="V2", attrs=[], parent_id=base.id)
    anns = [
        _ann(
            ocg_id,
            _ann_view(
                pkg="pkg", namespace="d.s", cls="Base", attr="kind", mode="key"
            ),
        ),
        _ann(
            ocg_id,
            _ann_view(
                pkg="pkg",
                namespace="d.s",
                cls="V1",
                attr="kind",
                mode="tag",
                tag="dup",
            ),
        ),
        _ann(
            ocg_id,
            _ann_view(
                pkg="pkg",
                namespace="d.s",
                cls="V2",
                attr="kind",
                mode="tag",
                tag="dup",
            ),
        ),
    ]

    with pytest.raises(ValueError, match="Duplicate DISCRIMINATE tag"):
        validate_discriminate_annotations(
            compiled_annotations=anns,
            class_configs=[base, v1, v2],
            namespace_by_class_config_id={base.id: ns, v1.id: ns, v2.id: ns},
        )


def test_discriminate_validation_external_base_key_rejects_tag():
    ocg_id = uuid4()
    ns = NamespacePath(package="pkg_local", namespace="d.s")

    base = _class_with_attrs(name="Base", attrs=[_attr("kind")])
    variant = _class_with_attrs(name="Variant", attrs=[], parent_id=base.id)

    tag_ann = _ann(
        ocg_id,
        _ann_view(
            pkg="pkg_local",
            namespace="d.s",
            cls="Variant",
            attr="kind",
            mode="tag",
            tag="v1",
        ),
    )

    ext_graph = ObjectConfigGraph(
        name="external",
        description=None,
        hash="external",
        fqn_prefix="pkg_ext",
        language=CodeLanguage.aware,
    )
    ext_node = make_ocg_node(
        type=ObjectConfigGraphNodeType.class_,
        object_config_graph_id=ext_graph.id,
        class_config=base,
        class_config_id=base.id,
    )
    ext_graph.object_config_graph_nodes = [ext_node]

    base.class_fqn = "pkg_ext.d.s.Base"

    key_ann = _ann(
        ext_graph.id,
        _ann_view(
            pkg="pkg_ext", namespace="d.s", cls="Base", attr="kind", mode="key"
        ),
    )
    ext_graph.object_config_graph_annotations = [key_ann]

    with pytest.raises(ValueError, match="references external base class"):
        validate_discriminate_annotations(
            compiled_annotations=[tag_ann],
            class_configs=[variant],
            namespace_by_class_config_id={variant.id: ns},
            external_graphs=[ext_graph],
        )
