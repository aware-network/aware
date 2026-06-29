from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

import pytest

from aware_code.primitive_codec_base import build_code_primitive_type
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)
from aware_meta.graph.config.stable_ids_spec.spec import (
    FunctionSpec,
    NamespaceSpec,
    ParamSpec,
    StableIdsSpec,
)
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.function.function_config_enums import (
    FunctionAttributeType,
    FunctionKind,
)
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig
from python_grammar.renderer_stable_ids import (
    PythonStableIdsRendererLanguage,
    _derive_constructor_stable_id_bindings,
    render_python_stable_ids_module,
)
from python_grammar_test_support import (
    function_attr_link,
    function_io_owner_key,
    function_owner_key,
    make_attribute,
    make_class,
    make_class_node,
    make_function,
)


@dataclass(frozen=True)
class _Layout(ObjectConfigGraphRenderLayoutStrategy):
    base_dir: Path

    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        _ = class_config
        return Path("models.py")

    def get_enum_file_path(self, enum_config: EnumConfig) -> Path:
        _ = enum_config
        return Path("models.py")

    def get_function_file_path(self, function_config: FunctionConfig) -> Path:
        _ = function_config
        return Path("functions.py")

    def get_file_extension(self) -> str:
        return ".py"


def _primitive_desc(base: CodePrimitiveBaseType) -> AttributeTypeDescriptor:
    prim = build_code_primitive_type(base_type=base)
    prim_cfg = PrimitiveConfig(primitive_type=prim, primitive_type_id=prim.id)
    return AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive,
        primitive_config=prim_cfg,
        primitive_config_id=prim_cfg.id,
    )


def test_python_stable_ids_renderer_defaults_to_class_strict_policy() -> None:
    renderer = PythonStableIdsRendererLanguage(
        layout_strategy=_Layout(base_dir=Path("."))
    )

    assert renderer._resolution_policy == "class_strict"

    renderer.set_policy({"stable_ids_ownership": "authored"})

    assert renderer._resolution_policy == "class_strict"


def test_python_stable_ids_renderer_rejects_compat_policy() -> None:
    renderer = PythonStableIdsRendererLanguage(
        layout_strategy=_Layout(base_dir=Path("."))
    )

    with pytest.raises(ValueError, match="must be class_strict"):
        renderer.set_policy({"stable_ids_resolution_policy": "compat"})


def test_constructor_stable_id_bindings_preserve_helper_signature() -> None:
    child = make_class(name="ChildEntity", is_base=True)
    build = make_function(
        name="build_via_parent",
        owner_key=function_owner_key(child),
        is_async=True,
        kind=FunctionKind.class_,
    )
    parent_entity_id = make_attribute(
        name="parent_entity_id",
        owner_key=function_io_owner_key(build, FunctionAttributeType.input),
        is_public=True,
        is_required=True,
        is_unique=True,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.uuid),
    )
    type_attr = make_attribute(
        name="type",
        owner_key=function_io_owner_key(build, FunctionAttributeType.input),
        default_value='"text"',
        is_public=True,
        is_required=False,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.string),
    )
    build.function_config_attribute_configs = [
        function_attr_link(
            build,
            parent_entity_id,
            type=FunctionAttributeType.input,
            position=0,
            is_identity_key=True,
        ),
        function_attr_link(
            build,
            type_attr,
            type=FunctionAttributeType.input,
            position=1,
            is_identity_key=False,
        ),
    ]
    child.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=child.id,
            function_config_id=build.id,
            function_config=build,
            is_public=True,
            is_constructor=True,
            position=0,
        ),
    ]
    graph = ObjectConfigGraph(
        name="test",
        description="test",
        hash="sha256:test",
        fqn_prefix="aware_test",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            make_class_node(UUID("00000000-0000-0000-0000-000000000000"), child),
        ],
        object_projection_graphs=[],
    )
    spec = StableIdsSpec(
        version=1,
        namespaces=(
            NamespaceSpec(
                name="NS_TEST",
                kind="ns_url",
                value="aware://test/v1",
            ),
        ),
        functions=(
            FunctionSpec(
                name="stable_child_entity_id",
                namespace="NS_TEST",
                template="aware:child:{parent_entity_id}:{type}",
                params=(
                    ParamSpec(name="parent_entity_id", type="uuid"),
                    ParamSpec(name="type", type="str", default="text"),
                ),
            ),
        ),
    )

    bindings = _derive_constructor_stable_id_bindings(graph=graph, spec=spec)
    assert bindings[str(child.id)] == (
        "stable_child_entity_id",
        ("parent_entity_id", "type"),
    )

    out = render_python_stable_ids_module(
        spec=spec,
        constructor_bindings=bindings,
    )

    compile(out, "stable_ids.py", "exec")
    assert (
        f"{str(child.id)!r}: "
        "('stable_child_entity_id', ('parent_entity_id', 'type'))"
    ) in out
