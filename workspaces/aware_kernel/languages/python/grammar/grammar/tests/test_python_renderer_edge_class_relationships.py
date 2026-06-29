from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.writer import CodeSectionWriter
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
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
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipType,
)

from python_grammar.renderer import PythonRenderer
from python_grammar.renderer_policy import PythonRenderPolicy
from python_grammar_test_support import (
    class_attr_link,
    make_attribute,
    make_class,
    make_relationship,
    make_relationship_association,
    make_relationship_attribute,
)


@dataclass(frozen=True)
class _TestLayout(ObjectConfigGraphRenderLayoutStrategy):
    base_dir: Path
    import_root: str | None = None
    parent: ObjectConfigGraphRenderLayoutStrategy | None = None

    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        return Path("default") / "models.py"

    def get_enum_file_path(self, enum_config) -> Path:  # pragma: no cover
        return Path("default") / "models.py"

    def get_function_file_path(self, function_config) -> Path:  # pragma: no cover
        return Path("default") / "models.py"

    def get_file_extension(self) -> str:
        return ".py"

    def get_module_import_path(self, file_path: Path) -> str:
        parts = list(file_path.parts)
        if parts:
            parts[-1] = Path(parts[-1]).stem
        module_parts = [p for p in parts if p]
        if self.import_root:
            module_parts.insert(0, self.import_root)
        return ".".join(module_parts).strip(".")


@dataclass(frozen=True)
class _CrossLayout(ObjectConfigGraphRenderLayoutStrategy):
    base_dir: Path
    import_root: str | None = None
    parent: ObjectConfigGraphRenderLayoutStrategy | None = None

    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        if class_config.name == "Target":
            return Path("external") / "models.py"
        return Path("default") / "models.py"

    def get_enum_file_path(self, enum_config) -> Path:  # pragma: no cover
        return Path("default") / "models.py"

    def get_function_file_path(self, function_config) -> Path:  # pragma: no cover
        return Path("default") / "models.py"

    def get_file_extension(self) -> str:
        return ".py"

    def get_module_import_path(self, file_path: Path) -> str:
        parts = list(file_path.parts)
        if parts:
            parts[-1] = Path(parts[-1]).stem
        module_parts = [p for p in parts if p]
        if self.import_root:
            module_parts.insert(0, self.import_root)
        return ".".join(module_parts).strip(".")


def _class_descriptor(target: ClassConfig) -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.class_,
        class_config=target,
        class_config_id=target.id,
    )


def _acc(cls: ClassConfig, attr: AttributeConfig, pos: int) -> ClassConfigAttributeConfig:
    return class_attr_link(cls, attr, position=pos)


def _render(
    renderer: PythonRenderer,
    *,
    meta_objects: list[object],
    class_map: dict[UUID, ClassConfig],
) -> str:
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(code=code, index=CodeSectionBuilderIndex(), indent_size=renderer.indent)
    renderer.emit_file(meta_objects, writer, schema="default", class_to_class_config_map=class_map)
    return writer.code.content_part_text.inline_text or ""


def test_python_renderer_relationship_to_edge_class_renders_under_relationships() -> None:
    edge_cls = make_class(name="EdgeThing", is_base=True, is_edge=True)
    holder = make_class(name="Holder", is_base=True)

    edge_ref_attr = make_attribute(
        name="edge_ref",
        owner_key=holder.class_fqn,
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_class_descriptor(edge_cls),
    )
    holder.class_config_attribute_configs = [_acc(holder, edge_ref_attr, pos=0)]

    rel = make_relationship(
        holder,
        edge_cls,
        relationship_key="edge_ref",
        relationship_type=ClassConfigRelationshipType.many_to_one,
        forward_required=True,
    )
    rel.class_config_relationship_attributes = [
        make_relationship_attribute(
            rel,
            edge_ref_attr,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
    ]

    renderer = PythonRenderer(layout_strategy=_TestLayout(base_dir=Path("/tmp")))
    class_map = {c.id: c for c in (holder, edge_cls)}
    output = _render(renderer, meta_objects=[holder, edge_cls, rel], class_map=class_map)

    assert "# Relationships" in output
    assert "# Edges" not in output
    assert "edge_ref" in output


def test_python_renderer_edge_backed_property_imports_external_target() -> None:
    source = make_class(name="Source", is_base=True)
    target = make_class(name="Target", is_base=True)
    edge_cls = make_class(name="Edge", is_base=True, is_edge=True)

    target_attr = make_attribute(
        name="target",
        owner_key=edge_cls.class_fqn,
        is_public=True,
        is_required=False,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_class_descriptor(target),
    )
    edge_cls.class_config_attribute_configs = [_acc(edge_cls, target_attr, pos=0)]

    edge_helper = make_attribute(
        name="edge_items",
        owner_key=source.class_fqn,
        is_public=True,
        is_required=False,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_class_descriptor(edge_cls),
    )
    rel_attr = make_attribute(
        name="targets",
        owner_key=source.class_fqn,
        is_public=True,
        is_required=False,
        is_unique=False,
        is_virtual=True,
        type_descriptor=_class_descriptor(target),
    )
    source.class_config_attribute_configs = [
        _acc(source, edge_helper, pos=0),
        _acc(source, rel_attr, pos=1),
    ]

    rel = make_relationship(
        source,
        target,
        relationship_key="targets",
        relationship_type=ClassConfigRelationshipType.many_to_many,
        forward_required=False,
    )
    rel.class_config_relationship_association_edge = make_relationship_association(rel, edge_cls)
    rel.class_config_relationship_attributes = [
        make_relationship_attribute(
            rel,
            rel_attr,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
    ]

    renderer = PythonRenderer(layout_strategy=_CrossLayout(base_dir=Path("/tmp")))
    class_map = {c.id: c for c in (source, target, edge_cls)}
    output = _render(renderer, meta_objects=[source, target, edge_cls, rel], class_map=class_map)

    assert "if TYPE_CHECKING" in output
    assert "from external.models import Target" in output


def test_api_policy_runtime_imports_external_model_field_types() -> None:
    source = make_class(name="Source", is_base=True)
    target = make_class(name="Target", is_base=True)
    target_attr = make_attribute(
        name="target",
        owner_key=source.class_fqn,
        is_public=True,
        is_required=False,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_class_descriptor(target),
    )
    source.class_config_attribute_configs = [_acc(source, target_attr, pos=0)]

    renderer = PythonRenderer(
        layout_strategy=_CrossLayout(base_dir=Path("/tmp")),
        policy=PythonRenderPolicy.api_default(),
    )
    output = _render(
        renderer,
        meta_objects=[source],
        class_map={source.id: source, target.id: target},
    )

    assert "from external.models import Target" in output
    assert "if TYPE_CHECKING" not in output
    assert "target: Target | None = Field(default=None)" in output


def test_parented_api_policy_does_not_import_unused_base_model() -> None:
    parent = make_class(name="Target", is_base=True)
    child = make_class(
        name="Child",
        value_mode=ClassValueMode.inline_value,
        parent_class=parent,
        parent_class_id=parent.id,
    )

    renderer = PythonRenderer(
        layout_strategy=_CrossLayout(base_dir=Path("/tmp")),
        policy=PythonRenderPolicy.api_default(),
    )
    output = _render(
        renderer,
        meta_objects=[child],
        class_map={child.id: child, parent.id: parent},
    )

    assert "from external.models import Target" in output
    assert "BaseModel" not in output
    assert "class Child(Target):" in output


def test_python_renderer_edge_backed_property_ordering() -> None:
    source = make_class(name="Source", is_base=True)
    target_a = make_class(name="TargetA", is_base=True)
    target_b = make_class(name="TargetB", is_base=True)
    edge_a = make_class(name="EdgeA", is_base=True, is_edge=True)
    edge_b = make_class(name="EdgeB", is_base=True, is_edge=True)

    edge_a_target = make_attribute(
        name="target_a",
        owner_key=edge_a.class_fqn,
        is_public=True,
        is_required=False,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_class_descriptor(target_a),
    )
    edge_a.class_config_attribute_configs = [_acc(edge_a, edge_a_target, pos=0)]

    edge_b_target = make_attribute(
        name="target_b",
        owner_key=edge_b.class_fqn,
        is_public=True,
        is_required=False,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_class_descriptor(target_b),
    )
    edge_b.class_config_attribute_configs = [_acc(edge_b, edge_b_target, pos=0)]

    rel_a = make_attribute(
        name="alpha",
        owner_key=source.class_fqn,
        is_public=True,
        is_required=False,
        is_unique=False,
        is_virtual=True,
        type_descriptor=_class_descriptor(target_a),
    )
    rel_b = make_attribute(
        name="beta",
        owner_key=source.class_fqn,
        is_public=True,
        is_required=False,
        is_unique=False,
        is_virtual=True,
        type_descriptor=_class_descriptor(target_b),
    )
    edge_helper_a = make_attribute(
        name="edge_a_items",
        owner_key=source.class_fqn,
        is_public=True,
        is_required=False,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_class_descriptor(edge_a),
    )
    edge_helper_b = make_attribute(
        name="edge_b_items",
        owner_key=source.class_fqn,
        is_public=True,
        is_required=False,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_class_descriptor(edge_b),
    )

    # Intentionally order rel_a before rel_b to assert order is respected
    source.class_config_attribute_configs = [
        _acc(source, rel_a, pos=0),
        _acc(source, rel_b, pos=1),
        _acc(source, edge_helper_a, pos=2),
        _acc(source, edge_helper_b, pos=3),
    ]

    rel_a_cfg = make_relationship(
        source,
        target_a,
        relationship_key="alpha",
        relationship_type=ClassConfigRelationshipType.many_to_many,
        forward_required=False,
    )
    rel_a_cfg.class_config_relationship_association_edge = make_relationship_association(rel_a_cfg, edge_a)
    rel_a_cfg.class_config_relationship_attributes = [
        make_relationship_attribute(
            rel_a_cfg,
            rel_a,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
    ]

    rel_b_cfg = make_relationship(
        source,
        target_b,
        relationship_key="beta",
        relationship_type=ClassConfigRelationshipType.many_to_many,
        forward_required=False,
    )
    rel_b_cfg.class_config_relationship_association_edge = make_relationship_association(rel_b_cfg, edge_b)
    rel_b_cfg.class_config_relationship_attributes = [
        make_relationship_attribute(
            rel_b_cfg,
            rel_b,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
    ]

    renderer = PythonRenderer(layout_strategy=_TestLayout(base_dir=Path("/tmp")))
    class_map = {c.id: c for c in (source, target_a, target_b, edge_a, edge_b)}
    output = _render(
        renderer,
        meta_objects=[source, target_a, target_b, edge_a, edge_b, rel_a_cfg, rel_b_cfg],
        class_map=class_map,
    )

    alpha_idx = output.find("def alpha(self)")
    beta_idx = output.find("def beta(self)")
    assert alpha_idx != -1 and beta_idx != -1
    assert alpha_idx < beta_idx
