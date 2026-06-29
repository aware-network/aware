from pathlib import Path

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

# Code Runtime
from aware_code.primitive_codec_base import build_code_primitive_type
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.writer import CodeSectionWriter

# Meta Ontology
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import AttributeTypeDescriptor
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import AttributeTypeDescriptorKind
from aware_meta_ontology.annotation.code_section_annotation_discriminate import (
    CodeSectionAnnotationDiscriminate,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import ClassConfigAttributeConfig
from aware_meta_ontology.class_.class_config_function_config import ClassConfigFunctionConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_attribute_config import FunctionConfigAttributeConfig
from aware_meta_ontology.function.function_config_enums import (
    FunctionAttributeType,
    FunctionKind,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_annotation import (
    ObjectConfigGraphAnnotation,
)
from aware_meta_ontology.graph.config.object_config_graph_annotation_enums import (
    ObjectConfigGraphAnnotationKind,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.config.object_config_graph_node_layout import (
    ObjectConfigGraphNodeLayout,
)
from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig

# Meta API
from aware_meta_ontology.graph.config.object_config_graph_enums import ObjectConfigGraphNodeType

from aware_meta.graph.config.render.layout_strategy import ObjectConfigGraphRenderLayoutStrategy

from python_grammar.renderer import PythonRenderer
from python_grammar.renderer_policy import PythonRenderPolicy
from python_grammar_test_support import (
    class_attr_link,
    function_attr_link,
    function_io_owner_key,
    function_owner_key,
    make_attribute,
    make_class,
    make_class_node,
    make_function,
)


class _TestLayout(ObjectConfigGraphRenderLayoutStrategy):
    base_dir: Path

    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        return Path("default") / "models.py"

    def get_enum_file_path(self, enum_config) -> Path:  # pragma: no cover
        return Path("default") / "models.py"

    def get_function_file_path(self, function_config: FunctionConfig) -> Path:  # pragma: no cover
        return Path("default") / "models.py"

    def get_file_extension(self) -> str:
        return ".py"

    def get_module_import_path(self, file_path: Path) -> str:
        parts = list(file_path.parts)
        if parts:
            parts[-1] = Path(parts[-1]).stem
        return ".".join(p for p in parts if p).strip(".")


def test_python_renderer_emits_valid_signature_when_required_follows_default() -> None:
    cls = make_class(name="Thing", is_base=True)

    prim = build_code_primitive_type(base_type=CodePrimitiveBaseType.string)
    prim_cfg = PrimitiveConfig(primitive_type=prim, primitive_type_id=prim.id)
    desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive,
        primitive_config=prim_cfg,
        primitive_config_id=prim_cfg.id,
    )

    fn = make_function(name="do", owner_key=function_owner_key(cls), is_async=True, kind=FunctionKind.instance)
    optional_attr = make_attribute(
        name="optional",
        owner_key=function_io_owner_key(fn, FunctionAttributeType.input),
        is_public=True,
        is_required=False,
        is_unique=False,
        is_virtual=False,
        type_descriptor=desc,
        type_descriptor_id=desc.id,
    )
    required_attr = make_attribute(
        name="required",
        owner_key=function_io_owner_key(fn, FunctionAttributeType.input),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=desc,
        type_descriptor_id=desc.id,
    )

    fn.function_config_attribute_configs = [
        function_attr_link(fn, optional_attr, type=FunctionAttributeType.input, position=0),
        function_attr_link(fn, required_attr, type=FunctionAttributeType.input, position=1),
    ]
    cls.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=cls.id,
            function_config=fn,
            function_config_id=fn.id,
            is_public=True,
            is_constructor=False,
            position=0,
        )
    ]

    renderer = PythonRenderer(layout_strategy=_TestLayout(base_dir=Path("/tmp")))
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(code=code, index=CodeSectionBuilderIndex(), indent_size=renderer.indent)
    renderer.emit_file([cls, fn], writer, schema="default", class_to_class_config_map={cls.id: cls})

    out = writer.code.content_part_text.inline_text or ""
    compile(out, "generated.py", "exec")  # ensure render output is syntactically valid

    # Python requires required params before default params; renderer must repair the ordering.
    assert "async def do(self, required: str, optional: str | None = None) -> None" in out
    assert '"required": required' in out
    assert '"optional": optional' in out


def test_python_renderer_discriminator_tag_order_uses_source_position() -> None:
    base_cls = make_class(name="BaseEvent", package="test_pkg", schema="events", is_base=True)
    variant_a = make_class(
        name="EventAlpha",
        package="test_pkg",
        schema="events",
        is_base=False,
        parent_class_id=base_cls.id,
    )
    variant_b = make_class(
        name="EventBeta",
        package="test_pkg",
        schema="events",
        is_base=False,
        parent_class_id=base_cls.id,
    )
    base_cls.class_fqn = "test_pkg.events.BaseEvent"
    variant_a.class_fqn = "test_pkg.events.EventAlpha"
    variant_b.class_fqn = "test_pkg.events.EventBeta"

    prim = build_code_primitive_type(base_type=CodePrimitiveBaseType.string)
    prim_cfg = PrimitiveConfig(primitive_type=prim, primitive_type_id=prim.id)
    desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive,
        primitive_config=prim_cfg,
        primitive_config_id=prim_cfg.id,
    )
    discr_attr = make_attribute(
        name="kind",
        owner_key=base_cls.class_fqn,
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=desc,
        type_descriptor_id=desc.id,
    )
    base_cls.class_config_attribute_configs = [
        class_attr_link(base_cls, discr_attr, position=0)
    ]

    graph = ObjectConfigGraph(
        name="test_discriminator_order",
        description=None,
        hash="test-hash",
        fqn_prefix="test_pkg",
        language=CodeLanguage.python,
    )

    graph.object_config_graph_nodes = [
        make_class_node(graph.id, base_cls),
        make_class_node(graph.id, variant_a),
        make_class_node(graph.id, variant_b),
    ]

    graph.object_config_graph_annotations = [
        ObjectConfigGraphAnnotation(
            object_config_graph_id=graph.id,
            kind=ObjectConfigGraphAnnotationKind.discriminate,
            code_section_annotation_discriminate=CodeSectionAnnotationDiscriminate(
                code_section_annotation_id=base_cls.id,
                fqn_prefix="test_pkg",
                namespace="events",
                class_name="BaseEvent",
                attribute_name="kind",
                mode="key",
                tag_value=None,
            ),
        ),
        ObjectConfigGraphAnnotation(
            object_config_graph_id=graph.id,
            kind=ObjectConfigGraphAnnotationKind.discriminate,
            code_section_annotation_discriminate=CodeSectionAnnotationDiscriminate(
                code_section_annotation_id=variant_a.id,
                fqn_prefix="test_pkg",
                namespace="events",
                class_name="EventAlpha",
                attribute_name="kind",
                mode="tag",
                tag_value="alpha",
                source_position=20,
            ),
        ),
        ObjectConfigGraphAnnotation(
            object_config_graph_id=graph.id,
            kind=ObjectConfigGraphAnnotationKind.discriminate,
            code_section_annotation_discriminate=CodeSectionAnnotationDiscriminate(
                code_section_annotation_id=variant_b.id,
                fqn_prefix="test_pkg",
                namespace="events",
                class_name="EventBeta",
                attribute_name="kind",
                mode="tag",
                tag_value="beta",
                source_position=10,
            ),
        ),
    ]

    renderer = PythonRenderer(layout_strategy=_TestLayout(base_dir=Path("/tmp")))
    renderer.set_policy(PythonRenderPolicy.api_default())
    renderer.bind_object_config_graph(graph)
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(code=code, index=CodeSectionBuilderIndex(), indent_size=renderer.indent)

    class_map = {cfg.id: cfg for cfg in [base_cls, variant_a, variant_b]}
    renderer.emit_file([base_cls, variant_a, variant_b], writer, schema="events", class_to_class_config_map=class_map)

    out = writer.code.content_part_text.inline_text or ""
    beta_line = '"beta": "default.models.EventBeta",'
    alpha_line = '"alpha": "default.models.EventAlpha",'
    assert beta_line in out
    assert alpha_line in out
    assert out.index(beta_line) < out.index(alpha_line)


def test_python_renderer_respects_layout_order_when_code_sections_missing() -> None:
    cls_alpha = make_class(name="Alpha", is_base=True)
    cls_beta = make_class(name="Beta", is_base=True)

    graph = ObjectConfigGraph(
        name="test_layout_order",
        description=None,
        hash="test-hash",
        fqn_prefix="test_pkg",
        language=CodeLanguage.python,
    )

    graph.object_config_graph_nodes = [
        ObjectConfigGraphNode(
            object_config_graph_id=graph.id,
            type=ObjectConfigGraphNodeType.class_,
            node_key=cls_alpha.class_fqn,
            class_config=cls_alpha,
            class_config_id=cls_alpha.id,
            layouts=[
                ObjectConfigGraphNodeLayout(
                    object_config_graph_node_id=make_class_node(graph.id, cls_alpha).id,
                    layout_kind="aware",
                    relative_path="default/models.aware",
                    source_position=20,
                )
            ],
        ),
        ObjectConfigGraphNode(
            object_config_graph_id=graph.id,
            type=ObjectConfigGraphNodeType.class_,
            node_key=cls_beta.class_fqn,
            class_config=cls_beta,
            class_config_id=cls_beta.id,
            layouts=[
                ObjectConfigGraphNodeLayout(
                    object_config_graph_node_id=make_class_node(graph.id, cls_beta).id,
                    layout_kind="aware",
                    relative_path="default/models.aware",
                    source_position=10,
                )
            ],
        ),
    ]

    renderer = PythonRenderer(layout_strategy=_TestLayout(base_dir=Path("/tmp")))
    renderer.set_policy(PythonRenderPolicy.api_default())
    renderer.bind_object_config_graph(graph)
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(code=code, index=CodeSectionBuilderIndex(), indent_size=renderer.indent)

    renderer.emit_file([cls_alpha, cls_beta], writer, schema="default", class_to_class_config_map={})
    out = writer.code.content_part_text.inline_text or ""
    beta_line = "class Beta("
    alpha_line = "class Alpha("
    assert beta_line in out
    assert alpha_line in out
    assert out.index(beta_line) < out.index(alpha_line)
