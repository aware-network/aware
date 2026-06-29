from __future__ import annotations

from importlib import import_module
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from aware_meta.handlers._generated import meta_handlers
from aware_meta.runtime import build_meta_graph_runtime_for_aware_package_manifests
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot as IsolatedAwareRoot,
    LaneIds,
    ProofCall,
    ROOT_OBJECT_ID,
    SourceObjectId,
    run_meta_runtime_proof,
)
from _meta_runtime_test_paths import META_PACKAGE_MANIFEST_PATHS, REPO_ROOT


OBJECT_CONFIG_GRAPH_FQN = "aware_meta.graph.config.ObjectConfigGraph"
OBJECT_CONFIG_GRAPH_NODE_FQN = "aware_meta.graph.config.ObjectConfigGraphNode"
ENUM_CONFIG_FQN = "aware_meta.default.enum.EnumConfig"


def _meta_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    assert repo_root == REPO_ROOT
    return META_PACKAGE_MANIFEST_PATHS


def _build_meta_runtime(*, repo_root: Path, aware_root: Path):
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_meta_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(meta_handlers,),
        bootstrap_modules=(meta_handlers,),
    )
    assert runtime.context is not None
    return runtime


def _resolve_class_config_id(*, class_fqn: str) -> UUID:
    module_name, class_name = class_fqn.rsplit(".", 1)
    module = import_module(module_name)
    orm_class = getattr(module, class_name)
    class_config = orm_class.get_class_config()
    assert class_config is not None, f"Missing ClassConfig binding for {class_fqn}"
    return UUID(str(class_config.id))


@pytest.mark.asyncio
async def test_object_config_graph_module_proof(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    import aware_code_ontology  # noqa: F401
    import aware_content_ontology  # noqa: F401
    import aware_history_ontology  # noqa: F401
    import aware_meta_ontology  # noqa: F401
    import aware_storage_ontology  # noqa: F401

    lane = LaneIds(
        environment_id=uuid5(NAMESPACE_URL, "aware://tests/meta/ocg/env"),
        process_id=uuid5(NAMESPACE_URL, "aware://tests/meta/ocg/process"),
        thread_id=uuid5(NAMESPACE_URL, "aware://tests/meta/ocg/thread"),
    )

    from aware_meta_ontology.stable_ids import (
        stable_class_config_id,
        stable_enum_config_id,
        stable_enum_option_id,
        stable_object_config_graph_id,
        stable_object_config_graph_node_id,
    )

    class_fqn = "aware.meta.test.runtime.default.default.TestEntity"
    enum_fqn = "aware.meta.test.runtime.default.default.PublicationState"
    object_config_graph_id = stable_object_config_graph_id(
        fqn_prefix="aware.meta.test.runtime",
        language="aware",
    )
    class_node_id = stable_object_config_graph_node_id(
        object_config_graph_id=object_config_graph_id,
        type="class",
        node_key=class_fqn,
    )
    enum_node_id = stable_object_config_graph_node_id(
        object_config_graph_id=object_config_graph_id,
        type="enum",
        node_key=enum_fqn,
    )
    class_config_id = stable_class_config_id(
        object_config_graph_node_id=class_node_id,
        class_fqn=class_fqn,
    )
    enum_config_id = stable_enum_config_id(
        object_config_graph_node_id=enum_node_id,
        enum_fqn=enum_fqn,
    )
    enum_option_draft_id = stable_enum_option_id(
        enum_config_id=enum_config_id, value="draft"
    )
    enum_option_published_id = stable_enum_option_id(
        enum_config_id=enum_config_id, value="published"
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        runtime_index = runtime.context.index
        projection_graphs = [
            opg
            for opg in runtime_index.opg_by_hash.values()
            if (opg.name or "").strip() == "ObjectConfigGraph"
        ]
        assert len(projection_graphs) == 1
        object_config_graph_projection = projection_graphs[0]
        projection_node_class_ids = {
            UUID(str(node.class_config_id))
            for node in object_config_graph_projection.object_projection_graph_nodes
        }
        projection_relationship_pairs = set()
        for edge in object_config_graph_projection.object_projection_graph_edges:
            relationship = runtime_index.relationships_by_id.get(
                UUID(str(edge.class_config_relationship_id))
            )
            if relationship is None:
                continue
            projection_relationship_pairs.add(
                (
                    UUID(str(relationship.class_config_id)),
                    UUID(str(relationship.target_class_config_id)),
                )
            )

        function_impl_class_config_by_fqn = {
            "object_config_graph": _resolve_class_config_id(
                class_fqn="aware_meta_ontology.graph.config.object_config_graph.ObjectConfigGraph"
            ),
            "function_config": _resolve_class_config_id(
                class_fqn="aware_meta_ontology.function.function_config.FunctionConfig"
            ),
            "function_impl": _resolve_class_config_id(
                class_fqn="aware_meta_ontology.function.function_impl.FunctionImpl"
            ),
            "function_impl_instruction": _resolve_class_config_id(
                class_fqn="aware_meta_ontology.function.function_impl_instruction.FunctionImplInstruction"
            ),
            "function_impl_instruction_let": _resolve_class_config_id(
                class_fqn="aware_meta_ontology.function.function_impl_instruction_let.FunctionImplInstructionLet"
            ),
            "function_impl_instruction_invoke": _resolve_class_config_id(
                class_fqn="aware_meta_ontology.function.function_impl_instruction_invoke.FunctionImplInstructionInvoke"
            ),
            "function_impl_instruction_construct": _resolve_class_config_id(
                class_fqn=(
                    "aware_meta_ontology.function.function_impl_instruction_construct."
                    "FunctionImplInstructionConstruct"
                )
            ),
            "function_impl_instruction_construct_assignment": _resolve_class_config_id(
                class_fqn=(
                    "aware_meta_ontology.function.function_impl_instruction_construct_assignment."
                    "FunctionImplInstructionConstructAssignment"
                )
            ),
            "function_impl_instruction_set": _resolve_class_config_id(
                class_fqn="aware_meta_ontology.function.function_impl_instruction_set.FunctionImplInstructionSet"
            ),
            "function_impl_instruction_require": _resolve_class_config_id(
                class_fqn="aware_meta_ontology.function.function_impl_instruction_require.FunctionImplInstructionRequire"
            ),
            "function_impl_instruction_invoke_attribute_config": _resolve_class_config_id(
                class_fqn="aware_meta_ontology.function.function_impl_instruction_invoke_attribute_config.FunctionImplInstructionInvokeAttributeConfig"
            ),
            "function_impl_instruction_require_operand": _resolve_class_config_id(
                class_fqn="aware_meta_ontology.function.function_impl_instruction_require_operand.FunctionImplInstructionRequireOperand"
            ),
            "function_impl_value_source": _resolve_class_config_id(
                class_fqn="aware_meta_ontology.function.function_impl_value_source.FunctionImplValueSource"
            ),
            "function_impl_value_source_literal_primitive": _resolve_class_config_id(
                class_fqn="aware_meta_ontology.function.function_impl_value_source_literal_primitive.FunctionImplValueSourceLiteralPrimitive"
            ),
            "function_impl_value_source_transform": _resolve_class_config_id(
                class_fqn="aware_meta_ontology.function.function_impl_value_source_transform.FunctionImplValueSourceTransform"
            ),
            "function_impl_value_source_transform_operand": _resolve_class_config_id(
                class_fqn=(
                    "aware_meta_ontology.function.function_impl_value_source_transform_operand."
                    "FunctionImplValueSourceTransformOperand"
                )
            ),
            "function_config_attribute_config": _resolve_class_config_id(
                class_fqn="aware_meta_ontology.function.function_config_attribute_config.FunctionConfigAttributeConfig"
            ),
            "class_config_attribute_config": _resolve_class_config_id(
                class_fqn="aware_meta_ontology.class_.class_config_attribute_config.ClassConfigAttributeConfig"
            ),
            "class_config": _resolve_class_config_id(
                class_fqn="aware_meta_ontology.class_.class_config.ClassConfig"
            ),
            "class_config_relationship": _resolve_class_config_id(
                class_fqn="aware_meta_ontology.class_.class_config_relationship.ClassConfigRelationship"
            ),
            "attribute_config": _resolve_class_config_id(
                class_fqn="aware_meta_ontology.attribute.attribute_config.AttributeConfig"
            ),
            "primitive_config": _resolve_class_config_id(
                class_fqn="aware_meta_ontology.primitive.primitive_config.PrimitiveConfig"
            ),
        }

        for projected_class_config_id in function_impl_class_config_by_fqn.values():
            assert projected_class_config_id in projection_node_class_ids

        expected_function_impl_relationship_pairs = {
            ("function_config", "function_impl"),
            ("function_impl", "function_impl_instruction"),
            ("function_impl_instruction", "function_impl_instruction_let"),
            ("function_impl_instruction", "function_impl_instruction_invoke"),
            ("function_impl_instruction", "function_impl_instruction_construct"),
            ("function_impl_instruction", "function_impl_instruction_set"),
            ("function_impl_instruction", "function_impl_instruction_require"),
            ("function_impl_instruction_construct", "class_config"),
            (
                "function_impl_instruction_construct",
                "function_impl_instruction_construct_assignment",
            ),
            (
                "function_impl_instruction_construct_assignment",
                "class_config_attribute_config",
            ),
            (
                "function_impl_instruction_construct_assignment",
                "function_impl_value_source",
            ),
            ("function_impl_instruction_invoke", "function_config"),
            ("function_impl_instruction_invoke", "class_config_relationship"),
            (
                "function_impl_instruction_invoke",
                "function_impl_instruction_invoke_attribute_config",
            ),
            ("function_impl_instruction_invoke_attribute_config", "attribute_config"),
            ("function_impl_instruction_set", "class_config_attribute_config"),
            ("function_impl_instruction_set", "function_impl_value_source"),
            (
                "function_impl_instruction_require",
                "function_impl_instruction_require_operand",
            ),
            ("function_impl_instruction_require_operand", "function_impl_value_source"),
            ("function_impl_value_source", "function_config_attribute_config"),
            ("function_impl_value_source", "function_impl_instruction_let"),
            (
                "function_impl_value_source",
                "function_impl_value_source_literal_primitive",
            ),
            ("function_impl_value_source", "function_impl_value_source_transform"),
            ("function_impl_value_source_literal_primitive", "primitive_config"),
            ("function_impl_value_source_transform", "primitive_config"),
            (
                "function_impl_value_source_transform",
                "function_impl_value_source_transform_operand",
            ),
            (
                "function_impl_value_source_transform_operand",
                "function_impl_value_source",
            ),
        }
        for source_key, target_key in expected_function_impl_relationship_pairs:
            assert (
                function_impl_class_config_by_fqn[source_key],
                function_impl_class_config_by_fqn[target_key],
            ) in projection_relationship_pairs

        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="ObjectConfigGraph",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=OBJECT_CONFIG_GRAPH_FQN,
                    function_name="build",
                    kwargs={
                        "name": "meta_test_ocg_runtime",
                        "hash": "meta_test_ocg_runtime_hash",
                        "fqn_prefix": "aware.meta.test.runtime",
                        "language": "aware",
                        "object_config_graph_id": object_config_graph_id,
                        "description": "Meta OCG module proof runtime graph",
                    },
                    expected_root_object_id=object_config_graph_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=OBJECT_CONFIG_GRAPH_FQN,
                    function_name="create_node",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "type": "class",
                        "node_key": class_fqn,
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=OBJECT_CONFIG_GRAPH_NODE_FQN,
                    function_name="create_class",
                    object_id=SourceObjectId(class_node_id),
                    kwargs={
                        "class_fqn": class_fqn,
                        "name": "TestEntity",
                        "is_base": True,
                        "is_edge": False,
                        "description": "Meta OCG class",
                        "value_mode": "graph_ref",
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=OBJECT_CONFIG_GRAPH_FQN,
                    function_name="create_node",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "type": "enum",
                        "node_key": enum_fqn,
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=OBJECT_CONFIG_GRAPH_NODE_FQN,
                    function_name="create_enum",
                    object_id=SourceObjectId(enum_node_id),
                    kwargs={
                        "enum_fqn": enum_fqn,
                        "name": "PublicationState",
                        "description": "Meta OCG enum",
                        "values": [],
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=ENUM_CONFIG_FQN,
                    function_name="create_enum_option",
                    object_id=SourceObjectId(enum_config_id),
                    kwargs={
                        "value": "draft",
                        "label": None,
                        "description": None,
                        "position": 0,
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=ENUM_CONFIG_FQN,
                    function_name="create_enum_option",
                    object_id=SourceObjectId(enum_config_id),
                    kwargs={
                        "value": "published",
                        "label": None,
                        "description": None,
                        "position": 1,
                    },
                ),
            ],
        )

        assert (
            result.root_object_id
            == object_config_graph_id
            == UUID(str(result.root_object_id))
        )

        class_instance_id_by_source_id = {
            UUID(str(class_instance.source_object_id)): UUID(str(class_instance.id))
            for class_instance in result.oig.class_instances
            if class_instance.source_object_id is not None
            and class_instance.id is not None
        }
        ci = class_instance_id_by_source_id.__getitem__

        assertions.expect_root(ci(object_config_graph_id))
        assertions.expect_instance(ci(object_config_graph_id))
        assertions.expect_instance(ci(class_node_id))
        assertions.expect_instance(ci(enum_node_id))
        assertions.expect_instance(ci(class_config_id))
        assertions.expect_instance(ci(enum_config_id))
        assertions.expect_instance(ci(enum_option_draft_id))
        assertions.expect_instance(ci(enum_option_published_id))

        assertions.expect_edge(
            source_id=ci(object_config_graph_id),
            target_id=ci(class_node_id),
        )
        assertions.expect_edge(
            source_id=ci(object_config_graph_id),
            target_id=ci(enum_node_id),
        )
        assertions.expect_edge(
            source_id=ci(class_node_id),
            target_id=ci(class_config_id),
        )
        assertions.expect_edge(
            source_id=ci(enum_node_id),
            target_id=ci(enum_config_id),
        )
        assertions.expect_edge(
            source_id=ci(enum_config_id),
            target_id=ci(enum_option_draft_id),
        )
        assertions.expect_edge(
            source_id=ci(enum_config_id),
            target_id=ci(enum_option_published_id),
        )
        assertions.expect_primitive(
            instance_id=ci(class_node_id),
            field_name="type",
            expected="class",
        )
        assertions.expect_primitive(
            instance_id=ci(enum_node_id),
            field_name="type",
            expected="enum",
        )
        assertions.expect_primitive(
            instance_id=ci(class_config_id),
            field_name="name",
            expected="TestEntity",
        )
        assertions.expect_primitive(
            instance_id=ci(enum_option_draft_id),
            field_name="value",
            expected="draft",
        )
        assertions.expect_primitive(
            instance_id=ci(enum_option_published_id),
            field_name="value",
            expected="published",
        )


@pytest.mark.asyncio
async def test_object_config_graph_module_proof_function_impl_runtime_handlers(
    monkeypatch,
) -> None:
    import aware_meta_ontology  # noqa: F401
    from aware_meta.handlers.impl.function import (
        function_config as function_config_handler,
    )
    from aware_meta.handlers.impl.function import (
        function_config_attribute_config as function_config_attribute_handler,
    )
    from aware_meta.handlers.impl.function import function_impl as function_impl_handler
    from aware_meta.handlers.impl.function import (
        function_impl_instruction as function_instruction_handler,
    )
    from aware_meta.handlers.impl.function import (
        function_impl_instruction_construct as function_instruction_construct_handler,
    )
    from aware_meta.handlers.impl.function import (
        function_impl_instruction_construct_assignment as function_instruction_construct_assignment_handler,
    )
    from aware_meta.handlers.impl.function import (
        function_impl_instruction_set as function_instruction_set_handler,
    )
    from aware_meta.handlers.impl.function import (
        function_impl_value_source as function_value_source_handler,
    )
    from aware_meta_ontology.attribute.attribute_type_descriptor import (
        AttributeTypeDescriptor,
    )
    from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
        AttributeTypeDescriptorKind,
    )
    from aware_meta_ontology.function.function_config_enums import FunctionAttributeType
    from aware_meta_ontology.function.function_impl_instruction_enums import (
        FunctionImplInstructionType,
        FunctionImplValueSourceKind,
    )
    from aware_meta.test_support import (
        make_attribute_config,
        make_class_attribute_edge,
        make_class_config,
        make_function_attribute_edge,
        make_function_config,
        test_class_fqn,
    )

    class _Session:
        def __init__(self) -> None:
            self._rows: dict[tuple[type, UUID], object] = {}

        def put(self, value: object) -> None:
            value_id = getattr(value, "id", None)
            if value_id is not None:
                self._rows[(type(value), UUID(str(value_id)))] = value

        def imap_get(self, cls: type, value_id: UUID):
            return self._rows.get((cls, UUID(str(value_id))))

    session = _Session()

    function_config_id = uuid5(
        NAMESPACE_URL, "aware://tests/meta/function_impl/function_config"
    )
    class_config_id = uuid5(
        NAMESPACE_URL, "aware://tests/meta/function_impl/class_config"
    )
    type_descriptor_id = uuid5(
        NAMESPACE_URL, "aware://tests/meta/function_impl/type_descriptor"
    )
    attribute_config_id = uuid5(
        NAMESPACE_URL, "aware://tests/meta/function_impl/attribute_config"
    )
    class_config_attribute_config_id = uuid5(
        NAMESPACE_URL, "aware://tests/meta/function_impl/class_config_attr"
    )
    missing_class_config_attribute_config_id = uuid5(
        NAMESPACE_URL, "aware://tests/meta/function_impl/class_config_attr_missing"
    )
    missing_value_source_id = uuid5(
        NAMESPACE_URL, "aware://tests/meta/function_impl/value_source_missing"
    )

    class_fqn = test_class_fqn("TestClass")
    function_config = make_function_config(
        owner_key=class_fqn,
        id=function_config_id,
        name="test_fn",
        kind="instance",
    )
    class_config = make_class_config(
        "TestClass",
        class_fqn=class_fqn,
        id=class_config_id,
    )
    type_descriptor = AttributeTypeDescriptor(
        id=type_descriptor_id,
        kind=AttributeTypeDescriptorKind.primitive,
    )
    attribute_config = make_attribute_config(
        owner_key=class_fqn,
        id=attribute_config_id,
        name="display_name",
        type_descriptor=type_descriptor,
        type_descriptor_id=type_descriptor.id,
    )
    class_config_attribute_config = make_class_attribute_edge(
        class_config_id=class_config.id,
        attribute_config=attribute_config,
        name=attribute_config.name,
        id=class_config_attribute_config_id,
        position=0,
    )

    for obj in (
        function_config,
        class_config,
        type_descriptor,
        attribute_config,
        class_config_attribute_config,
    ):
        session.put(obj)

    for module in (
        function_config_attribute_handler,
        function_impl_handler,
        function_instruction_handler,
        function_instruction_construct_handler,
        function_instruction_construct_assignment_handler,
        function_instruction_set_handler,
        function_value_source_handler,
    ):
        monkeypatch.setattr(module, "current_handler_session", lambda: session)

    monkeypatch.setattr(
        function_config_handler.FunctionImpl,
        "build_via_function_config",
        function_impl_handler.build_via_function_config,
    )
    monkeypatch.setattr(
        function_impl_handler.FunctionImplInstruction,
        "build_via_function_impl",
        function_instruction_handler.build_via_function_impl,
    )
    monkeypatch.setattr(
        function_instruction_handler.FunctionImplValueSource,
        "build_via_function_impl_instruction",
        function_value_source_handler.build_via_function_impl_instruction,
    )
    monkeypatch.setattr(
        function_instruction_handler.FunctionImplInstructionSet,
        "build_via_function_impl_instruction",
        function_instruction_set_handler.build_via_function_impl_instruction,
    )
    monkeypatch.setattr(
        function_instruction_handler.FunctionImplInstructionConstruct,
        "build_via_function_impl_instruction",
        function_instruction_construct_handler.build_via_function_impl_instruction,
    )
    monkeypatch.setattr(
        function_instruction_construct_handler.FunctionImplInstructionConstructAssignment,
        "build_via_function_impl_instruction_construct",
        function_instruction_construct_assignment_handler.build_via_function_impl_instruction_construct,
    )
    monkeypatch.setattr(
        function_config_handler.FunctionConfigAttributeConfig,
        "create_primitive_via_function_config",
        function_config_attribute_handler.create_primitive_via_function_config,
    )

    function_impl = await function_config_handler.create_function_impl(
        function_config=function_config, key="default"
    )
    session.put(function_impl)
    function_impl_again = await function_config_handler.create_function_impl(
        function_config=function_config, key="default"
    )
    assert function_impl_again.id == function_impl.id

    set_instruction = await function_impl_handler.create_instruction(
        function_impl=function_impl,
        type=FunctionImplInstructionType.set,
        sequence=0,
    )
    session.put(set_instruction)

    let_instruction = await function_impl_handler.create_instruction(
        function_impl=function_impl,
        type=FunctionImplInstructionType.let,
        sequence=1,
    )
    session.put(let_instruction)

    foreign_value_source = await function_instruction_handler.create_value_source(
        function_impl_instruction=let_instruction,
        key="foreign",
        kind=FunctionImplValueSourceKind.literal,
    )
    session.put(foreign_value_source)

    with pytest.raises(
        RuntimeError, match="requires value source from same instruction"
    ):
        await function_instruction_handler.attach_set(
            function_impl_instruction=set_instruction,
            target_class_config_attribute_config_id=class_config_attribute_config.id,
            value_source_id=foreign_value_source.id,
        )

    local_value_source = await function_instruction_handler.create_value_source(
        function_impl_instruction=set_instruction,
        key="local",
        kind=FunctionImplValueSourceKind.literal,
    )
    session.put(local_value_source)
    set_payload = await function_instruction_handler.attach_set(
        function_impl_instruction=set_instruction,
        target_class_config_attribute_config_id=class_config_attribute_config.id,
        value_source_id=local_value_source.id,
    )
    session.put(set_payload)
    assert set_payload.value_source_id == local_value_source.id

    replacement_attribute_config = make_attribute_config(
        owner_key=class_fqn,
        id=uuid5(
            NAMESPACE_URL,
            "aware://tests/meta/function_impl/replacement_attribute_config",
        ),
        name="display_label",
        type_descriptor=type_descriptor,
        type_descriptor_id=type_descriptor.id,
    )
    replacement_class_edge = make_class_attribute_edge(
        class_config_id=class_config.id,
        attribute_config=replacement_attribute_config,
        name=replacement_attribute_config.name,
        id=uuid5(
            NAMESPACE_URL, "aware://tests/meta/function_impl/replacement_class_attr"
        ),
        position=1,
    )
    input_attribute_config = make_attribute_config(
        owner_key=f"{class_fqn}.test_fn",
        id=uuid5(
            NAMESPACE_URL, "aware://tests/meta/function_impl/input_attribute_config"
        ),
        name="new_display_name",
        type_descriptor=type_descriptor,
        type_descriptor_id=type_descriptor.id,
    )
    function_input_edge = make_function_attribute_edge(
        function_config_id=function_config.id,
        attribute_config=input_attribute_config,
        name=input_attribute_config.name,
        type=FunctionAttributeType.input,
        id=uuid5(NAMESPACE_URL, "aware://tests/meta/function_impl/function_input_edge"),
        position=0,
        is_identity_key=False,
    )
    replacement_input_attribute_config = make_attribute_config(
        owner_key=f"{class_fqn}.test_fn",
        id=uuid5(
            NAMESPACE_URL,
            "aware://tests/meta/function_impl/replacement_input_attribute_config",
        ),
        name="replacement_display_name",
        type_descriptor=type_descriptor,
        type_descriptor_id=type_descriptor.id,
    )
    replacement_function_input_edge = make_function_attribute_edge(
        function_config_id=function_config.id,
        attribute_config=replacement_input_attribute_config,
        name=replacement_input_attribute_config.name,
        type=FunctionAttributeType.input,
        id=uuid5(
            NAMESPACE_URL,
            "aware://tests/meta/function_impl/replacement_function_input_edge",
        ),
        position=1,
        is_identity_key=False,
    )
    for obj in (
        replacement_attribute_config,
        replacement_class_edge,
        input_attribute_config,
        function_input_edge,
        replacement_input_attribute_config,
        replacement_function_input_edge,
    ):
        session.put(obj)

    input_value_source = await function_instruction_handler.create_value_source(
        function_impl_instruction=set_instruction,
        key="input",
        kind=FunctionImplValueSourceKind.function_input_ref,
        source_function_config_attribute_config_id=function_input_edge.id,
    )
    session.put(input_value_source)
    await function_instruction_set_handler.update_assignment(
        function_impl_instruction_set=set_payload,
        target_class_config_attribute_config_id=replacement_class_edge.id,
        value_source_id=input_value_source.id,
    )
    assert (
        set_payload.target_class_config_attribute_config_id == replacement_class_edge.id
    )
    assert set_payload.value_source_id == input_value_source.id

    await function_value_source_handler.update_function_input_ref(
        function_impl_value_source=input_value_source,
        source_function_config_attribute_config_id=replacement_function_input_edge.id,
    )
    assert (
        input_value_source.source_function_config_attribute_config_id
        == replacement_function_input_edge.id
    )
    with pytest.raises(RuntimeError, match="requires kind 'function_input_ref'"):
        await function_value_source_handler.update_function_input_ref(
            function_impl_value_source=local_value_source,
            source_function_config_attribute_config_id=function_input_edge.id,
        )

    construct_instruction = await function_impl_handler.create_instruction(
        function_impl=function_impl,
        type=FunctionImplInstructionType.construct,
        sequence=2,
    )
    session.put(construct_instruction)

    with pytest.raises(RuntimeError, match="requires instruction type 'construct'"):
        await function_instruction_handler.attach_construct(
            function_impl_instruction=let_instruction,
            target_class_config_id=class_config.id,
        )

    construct_payload = await function_instruction_handler.attach_construct(
        function_impl_instruction=construct_instruction,
        target_class_config_id=class_config.id,
    )
    session.put(construct_payload)
    construct_payload_again = await function_instruction_handler.attach_construct(
        function_impl_instruction=construct_instruction,
        target_class_config_id=class_config.id,
    )
    assert construct_payload_again.id == construct_payload.id

    with pytest.raises(
        RuntimeError, match="requires existing ClassConfigAttributeConfig"
    ):
        await function_instruction_construct_handler.add_assignment(
            function_impl_instruction_construct=construct_payload,
            target_class_config_attribute_config_id=missing_class_config_attribute_config_id,
            value_source_id=local_value_source.id,
            position=0,
        )

    with pytest.raises(RuntimeError, match="requires existing FunctionImplValueSource"):
        await function_instruction_construct_handler.add_assignment(
            function_impl_instruction_construct=construct_payload,
            target_class_config_attribute_config_id=class_config_attribute_config.id,
            value_source_id=missing_value_source_id,
            position=0,
        )

    construct_local_value_source = (
        await function_instruction_handler.create_value_source(
            function_impl_instruction=construct_instruction,
            key="construct_local",
            kind=FunctionImplValueSourceKind.literal,
        )
    )
    session.put(construct_local_value_source)
    construct_assignment = await function_instruction_construct_handler.add_assignment(
        function_impl_instruction_construct=construct_payload,
        target_class_config_attribute_config_id=class_config_attribute_config.id,
        value_source_id=construct_local_value_source.id,
        position=0,
    )
    session.put(construct_assignment)
    assert construct_assignment.value_source_id == construct_local_value_source.id
    construct_assignment_again = (
        await function_instruction_construct_handler.add_assignment(
            function_impl_instruction_construct=construct_payload,
            target_class_config_attribute_config_id=class_config_attribute_config.id,
            value_source_id=construct_local_value_source.id,
            position=0,
        )
    )
    assert construct_assignment_again.id == construct_assignment.id

    with pytest.raises(RuntimeError, match="payload mismatch for existing assignment"):
        await function_instruction_construct_handler.add_assignment(
            function_impl_instruction_construct=construct_payload,
            target_class_config_attribute_config_id=class_config_attribute_config.id,
            value_source_id=construct_local_value_source.id,
            position=1,
        )

    with pytest.raises(RuntimeError, match="requires position >= 0"):
        await function_config_handler.add_primitive_attribute_config(
            function_config=function_config,
            name="display_name",
            type=FunctionAttributeType.input,
            position=-1,
            is_identity_key=False,
        )
