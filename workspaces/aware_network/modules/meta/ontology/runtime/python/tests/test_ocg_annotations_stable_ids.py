from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID, uuid4

from aware_code_ontology.annotation.code_section_annotation import CodeSectionAnnotation
from aware_meta_ontology.class_.class_config import ClassConfig

from aware_meta.graph.config.annotation.compiler import (
    compile_object_config_graph_annotations,
)
from aware_meta.test_support import make_class_config, test_class_fqn


class _FakeFqnScope:
    def try_resolve_class_with_fqn(self, type_ref: str):
        if not type_ref:
            return None
        name = type_ref.split(".")[-1]
        return type_ref, make_class_config(name, class_fqn=test_class_fqn(name))

    def try_resolve_enum_with_fqn(self, type_ref: str):
        return None


class _FakeFqnResolver:
    def scope_for_code_id(self, _code_id: UUID) -> _FakeFqnScope:
        return _FakeFqnScope()


def test_annotation_compiler_assigns_stable_ids_for_load_views():
    ocg_id = uuid4()
    code_id = uuid4()
    resolver = _FakeFqnResolver()

    code_section = SimpleNamespace(code_id=code_id, content_part_text_segment=None)
    ann_id = uuid4()

    ann = CodeSectionAnnotation.model_construct(
        id=ann_id,
        code_section=code_section,
        path="pkg.d.s.User::friends",
        verb="load",
        args=["lazy"],
    )

    out1 = compile_object_config_graph_annotations(
        code_section_annotations=[ann],
        fqn_resolver=resolver,
        object_config_graph_id=ocg_id,
    )
    out2 = compile_object_config_graph_annotations(
        code_section_annotations=[ann],
        fqn_resolver=resolver,
        object_config_graph_id=ocg_id,
    )

    assert len(out1) == 1
    assert len(out2) == 1

    w1 = out1[0]
    w2 = out2[0]

    assert w1.id == w2.id
    assert w1.code_section_annotation_load is not None
    assert w2.code_section_annotation_load is not None
    assert w1.code_section_annotation_load.id == w2.code_section_annotation_load.id
    assert w1.code_section_annotation_load_id == w1.code_section_annotation_load.id


def test_annotation_compiler_load_id_changes_when_semantics_change():
    ocg_id = uuid4()
    code_id = uuid4()
    resolver = _FakeFqnResolver()

    code_section = SimpleNamespace(code_id=code_id, content_part_text_segment=None)
    ann_id = uuid4()

    lazy = CodeSectionAnnotation.model_construct(
        id=ann_id,
        code_section=code_section,
        path="pkg.d.s.User::friends",
        verb="load",
        args=["lazy"],
    )
    eager = CodeSectionAnnotation.model_construct(
        id=ann_id,
        code_section=code_section,
        path="pkg.d.s.User::friends",
        verb="load",
        args=["eager"],
    )

    out_lazy = compile_object_config_graph_annotations(
        code_section_annotations=[lazy],
        fqn_resolver=resolver,
        object_config_graph_id=ocg_id,
    )
    out_eager = compile_object_config_graph_annotations(
        code_section_annotations=[eager],
        fqn_resolver=resolver,
        object_config_graph_id=ocg_id,
    )

    assert out_lazy[0].code_section_annotation_load is not None
    assert out_eager[0].code_section_annotation_load is not None
    assert (
        out_lazy[0].code_section_annotation_load.id
        != out_eager[0].code_section_annotation_load.id
    )
