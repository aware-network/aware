from __future__ import annotations

from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from aware_meta.handlers.impl.class_ import class_config as class_config_handler
from aware_meta.handlers.impl.function import function_call as function_call_handler
from aware_meta.handlers.impl.function import (
    function_call_response as function_call_response_handler,
)
from aware_meta.handlers.impl.function import function_config as function_config_handler
from aware_meta.handlers.impl.function import function_impl as function_impl_handler
from aware_meta.handlers.impl.function import (
    function_impl_instruction_set as instruction_set_handler,
)
from aware_meta.handlers.impl.function import (
    function_impl_value_source as value_source_handler,
)
from aware_meta.handlers.impl.instance import (
    object_instance_graph_lane as oig_lane_handler,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.function.function_config_attribute_config import (
    FunctionConfigAttributeConfig,
)
from aware_meta_ontology.function.function_config_enums import FunctionAttributeType
from aware_meta_ontology.function.function_call_response import FunctionCallResponse
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_impl import FunctionImpl
from aware_meta_ontology.function.function_impl_instruction import (
    FunctionImplInstruction,
)
from aware_meta_ontology.function.function_impl_instruction_enums import (
    FunctionImplInstructionType,
    FunctionImplValueSourceKind,
)
from aware_meta_ontology.function.function_impl_value_source import (
    FunctionImplValueSource,
)
from aware_meta_ontology.graph.instance.object_instance_graph_lane import (
    ObjectInstanceGraphLane,
)
from aware_meta_ontology.stable_ids import (
    stable_function_call_id,
    stable_function_call_response_id,
    stable_function_impl_instruction_set_id,
    stable_function_impl_value_source_id,
)


class _Session:
    def __init__(self) -> None:
        self._rows: dict[tuple[type, UUID], object] = {}

    def put(self, value: object) -> None:
        value_id = getattr(value, "id", None)
        if value_id is not None:
            self._rows[(type(value), UUID(str(value_id)))] = value

    def imap_get(self, cls: type, value_id: UUID):
        return self._rows.get((cls, value_id))


@pytest.mark.asyncio
async def test_function_call_projection_handlers_are_deterministic(monkeypatch) -> None:
    session = _Session()
    monkeypatch.setattr(
        function_call_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        function_call_response_handler, "current_handler_session", lambda: session
    )

    function_config_id = uuid4()
    function_config = FunctionConfig(
        id=function_config_id,
        owner_key="aware.tests",
        name="prove_function_call",
    )
    session.put(function_config)

    object_instance_graph_lane_id = uuid4()
    call_key = uuid4()
    created = await function_call_handler.build_via_object_instance_graph_lane(
        object_instance_graph_lane_id=object_instance_graph_lane_id,
        call_key=call_key,
        function_config_id=function_config_id,
        graph_hash_pre="pre-hash",
    )
    expected_function_call_id = stable_function_call_id(
        object_instance_graph_lane_id=object_instance_graph_lane_id,
        function_config_id=function_config_id,
        call_key=call_key,
    )
    assert created.id == expected_function_call_id
    assert created.function_config is function_config
    assert created.function_config_id == function_config_id
    assert created.graph_hash_pre == "pre-hash"

    session.put(created)
    created_again = await function_call_handler.build_via_object_instance_graph_lane(
        object_instance_graph_lane_id=object_instance_graph_lane_id,
        call_key=call_key,
        function_config_id=function_config_id,
        graph_hash_pre="pre-hash",
    )
    assert created_again is created

    async def _build_response_via_constructor(**kwargs):
        response_value = await function_call_response_handler.build_via_function_call(
            **kwargs
        )
        session.put(response_value)
        return response_value

    monkeypatch.setattr(
        FunctionCallResponse,
        "build_via_function_call",
        staticmethod(_build_response_via_constructor),
    )

    response = await function_call_handler.create_response(
        created,
        success=True,
        execution_time_ms=11,
        graph_hash_post="post-hash",
    )
    assert response.id == stable_function_call_response_id(
        function_call_id=expected_function_call_id,
    )
    assert response.function_call_id == expected_function_call_id
    assert response.success is True
    assert response.execution_time_ms == 11
    assert response.graph_hash_post == "post-hash"
    assert created.function_call_response is response

    session.put(response)
    response_again = await function_call_handler.create_response(
        created,
        success=True,
        execution_time_ms=11,
        graph_hash_post="post-hash",
    )
    assert response_again is response


@pytest.mark.asyncio
async def test_object_instance_graph_lane_creates_function_call_once(
    monkeypatch,
) -> None:
    session = _Session()
    monkeypatch.setattr(
        function_call_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(oig_lane_handler, "current_handler_session", lambda: session)

    function_config_id = uuid4()
    session.put(
        FunctionConfig(
            id=function_config_id,
            owner_key="aware.tests",
            name="lane_function_call",
        )
    )
    object_instance_graph_lane = ObjectInstanceGraphLane.model_construct(
        id=uuid4(),
        object_instance_graph_branch_id=uuid4(),
        lane_id=uuid4(),
        lane=None,
        function_calls=[],
    )
    call_key = uuid4()

    created = await oig_lane_handler.create_function_call(
        object_instance_graph_lane,
        call_key=call_key,
        function_config_id=function_config_id,
    )
    session.put(created)
    created_again = await oig_lane_handler.create_function_call(
        object_instance_graph_lane,
        call_key=call_key,
        function_config_id=function_config_id,
    )

    assert created_again is created
    assert object_instance_graph_lane.function_calls == [created]


@pytest.mark.asyncio
async def test_function_impl_value_source_accepts_wire_kind(monkeypatch) -> None:
    session = _Session()
    monkeypatch.setattr(
        value_source_handler, "current_handler_session", lambda: session
    )

    instruction_id = uuid4()
    instruction = FunctionImplInstruction.model_construct(
        id=instruction_id,
        function_impl_id=uuid4(),
        type=FunctionImplInstructionType.set,
        sequence=0,
        value_sources=[],
    )
    source_edge = FunctionConfigAttributeConfig.model_construct(
        id=uuid4(),
        function_config_id=uuid4(),
        attribute_config_id=uuid4(),
        name="display_name",
        position=0,
        type=FunctionAttributeType.input,
        is_identity_key=False,
    )
    replacement_source_edge = FunctionConfigAttributeConfig.model_construct(
        id=uuid4(),
        function_config_id=source_edge.function_config_id,
        attribute_config_id=uuid4(),
        name="display_label",
        position=1,
        type=FunctionAttributeType.input,
        is_identity_key=False,
    )
    session.put(instruction)
    session.put(source_edge)
    session.put(replacement_source_edge)

    created = await value_source_handler.build_via_function_impl_instruction(
        function_impl_instruction_id=cast(Any, str(instruction_id)),
        key="value",
        kind=cast(Any, "function_input_ref"),
        source_function_config_attribute_config_id=cast(Any, str(source_edge.id)),
    )

    assert created.id == stable_function_impl_value_source_id(
        function_impl_instruction_id=instruction_id,
        key="value",
    )
    assert created.kind == FunctionImplValueSourceKind.function_input_ref
    assert created.source_function_config_attribute_config is source_edge
    assert created.source_function_config_attribute_config_id == source_edge.id

    session.put(created)
    created.kind = cast(Any, "function_input_ref")
    await value_source_handler.update_function_input_ref(
        created,
        source_function_config_attribute_config_id=cast(
            Any,
            str(replacement_source_edge.id),
        ),
    )

    assert created.kind == FunctionImplValueSourceKind.function_input_ref
    assert created.source_function_config_attribute_config is replacement_source_edge
    assert (
        created.source_function_config_attribute_config_id == replacement_source_edge.id
    )


@pytest.mark.asyncio
async def test_function_impl_instruction_set_accepts_wire_ids(monkeypatch) -> None:
    session = _Session()
    monkeypatch.setattr(
        instruction_set_handler,
        "current_handler_session",
        lambda: session,
    )

    instruction_id = uuid4()
    instruction = FunctionImplInstruction.model_construct(
        id=instruction_id,
        function_impl_id=uuid4(),
        type=FunctionImplInstructionType.set,
        sequence=0,
        value_sources=[],
    )
    target_edge = ClassConfigAttributeConfig.model_construct(
        id=uuid4(),
        class_config_id=uuid4(),
        attribute_config_id=uuid4(),
    )
    replacement_target_edge = ClassConfigAttributeConfig.model_construct(
        id=uuid4(),
        class_config_id=target_edge.class_config_id,
        attribute_config_id=uuid4(),
    )
    value_source = FunctionImplValueSource.model_construct(
        id=uuid4(),
        function_impl_instruction_id=instruction_id,
        key="value",
        kind=FunctionImplValueSourceKind.function_input_ref,
    )
    replacement_value_source = FunctionImplValueSource.model_construct(
        id=uuid4(),
        function_impl_instruction_id=instruction_id,
        key="replacement",
        kind=FunctionImplValueSourceKind.function_input_ref,
    )
    for value in (
        instruction,
        target_edge,
        replacement_target_edge,
        value_source,
        replacement_value_source,
    ):
        session.put(value)

    created = await instruction_set_handler.build_via_function_impl_instruction(
        function_impl_instruction_id=cast(Any, str(instruction_id)),
        target_class_config_attribute_config_id=cast(Any, str(target_edge.id)),
        value_source_id=cast(Any, str(value_source.id)),
    )

    assert created.id == stable_function_impl_instruction_set_id(
        function_impl_instruction_id=instruction_id,
    )
    assert created.target_class_config_attribute_config is target_edge
    assert created.target_class_config_attribute_config_id == target_edge.id
    assert created.value_source is value_source
    assert created.value_source_id == value_source.id

    session.put(created)
    await instruction_set_handler.update_assignment(
        created,
        target_class_config_attribute_config_id=cast(
            Any,
            str(replacement_target_edge.id),
        ),
        value_source_id=cast(Any, str(replacement_value_source.id)),
    )

    assert created.target_class_config_attribute_config is replacement_target_edge
    assert created.target_class_config_attribute_config_id == replacement_target_edge.id
    assert created.value_source is replacement_value_source
    assert created.value_source_id == replacement_value_source.id


@pytest.mark.asyncio
async def test_function_impl_remove_instruction_accepts_wire_payloads() -> None:
    keep_instruction = FunctionImplInstruction.model_construct(
        id=uuid4(),
        function_impl_id=uuid4(),
        type=FunctionImplInstructionType.set,
        sequence=0,
    )
    stale_instruction = FunctionImplInstruction.model_construct(
        id=uuid4(),
        function_impl_id=keep_instruction.function_impl_id,
        type=FunctionImplInstructionType.set,
        sequence=1,
    )
    function_impl = FunctionImpl.model_construct(
        id=keep_instruction.function_impl_id,
        key="default",
        instructions=[keep_instruction, stale_instruction],
    )

    await function_impl_handler.remove_instruction(
        function_impl,
        type=cast(Any, "set"),
        sequence=cast(Any, "1"),
    )

    assert function_impl.instructions == [keep_instruction]

    await function_impl_handler.remove_instruction(
        function_impl,
        type=cast(Any, "set"),
        sequence=cast(Any, "1"),
    )

    assert function_impl.instructions == [keep_instruction]


@pytest.mark.asyncio
async def test_class_config_remove_attribute_config_accepts_wire_id() -> None:
    class_config_id = uuid4()
    keep_attribute = AttributeConfig.model_construct(
        id=uuid4(),
        owner_key="aware.tests.Room",
        name="name",
    )
    stale_attribute = AttributeConfig.model_construct(
        id=uuid4(),
        owner_key="aware.tests.Room",
        name="state",
    )
    keep_edge = ClassConfigAttributeConfig.model_construct(
        id=uuid4(),
        class_config_id=class_config_id,
        attribute_config_id=keep_attribute.id,
        attribute_config=keep_attribute,
    )
    stale_edge = ClassConfigAttributeConfig.model_construct(
        id=uuid4(),
        class_config_id=class_config_id,
        attribute_config_id=stale_attribute.id,
        attribute_config=stale_attribute,
    )
    class_config = ClassConfig.model_construct(
        id=class_config_id,
        class_fqn="aware.tests.Room",
        name="Room",
        class_config_attribute_configs=[keep_edge, stale_edge],
        class_config_function_configs=[],
        class_config_relationships=[],
    )

    await class_config_handler.remove_attribute_config(
        class_config,
        name="state",
        attribute_config_id=cast(Any, str(stale_attribute.id)),
    )

    assert class_config.class_config_attribute_configs == [keep_edge]

    await class_config_handler.remove_attribute_config(
        class_config,
        name="state",
        attribute_config_id=cast(Any, str(stale_attribute.id)),
    )

    assert class_config.class_config_attribute_configs == [keep_edge]


@pytest.mark.asyncio
async def test_function_config_remove_attribute_config_accepts_wire_type() -> None:
    function_config_id = uuid4()
    input_attribute = AttributeConfig.model_construct(
        id=uuid4(),
        owner_key="aware.tests.Room.rename",
        name="payload",
    )
    output_attribute = AttributeConfig.model_construct(
        id=uuid4(),
        owner_key="aware.tests.Room.rename",
        name="payload",
    )
    input_edge = FunctionConfigAttributeConfig.model_construct(
        id=uuid4(),
        function_config_id=function_config_id,
        attribute_config_id=input_attribute.id,
        attribute_config=input_attribute,
        name="payload",
        type=FunctionAttributeType.input,
        position=0,
        is_identity_key=False,
    )
    output_edge = FunctionConfigAttributeConfig.model_construct(
        id=uuid4(),
        function_config_id=function_config_id,
        attribute_config_id=output_attribute.id,
        attribute_config=output_attribute,
        name="payload",
        type=FunctionAttributeType.output,
        position=1,
        is_identity_key=False,
    )
    function_config = FunctionConfig.model_construct(
        id=function_config_id,
        owner_key="aware.tests.Room",
        name="rename",
        function_config_attribute_configs=[input_edge, output_edge],
        invocations=[],
    )

    await function_config_handler.remove_attribute_config(
        function_config,
        name="payload",
        type=cast(Any, "input"),
    )

    assert function_config.function_config_attribute_configs == [output_edge]

    await function_config_handler.remove_attribute_config(
        function_config,
        name="payload",
        type=cast(Any, "input"),
    )

    assert function_config.function_config_attribute_configs == [output_edge]
