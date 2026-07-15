from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from aware_experience.program import runtime_discovery


def test_program_runtime_discovery_builds_capability_objects_from_meta_index() -> None:
    create_id = uuid4()
    close_id = uuid4()
    private_id = uuid4()
    home_id = uuid4()

    index = SimpleNamespace(
        ocg=SimpleNamespace(
            object_config_graph_nodes=(
                SimpleNamespace(
                    type="class",
                    class_config=SimpleNamespace(
                        id=home_id,
                        name="Home",
                        description="Home aggregate",
                        class_config_function_configs=(
                            SimpleNamespace(
                                id=uuid4(),
                                position=2,
                                is_public=True,
                                is_constructor=False,
                                function_config=SimpleNamespace(
                                    id=close_id,
                                    name="close",
                                    description="Close the home",
                                ),
                            ),
                            SimpleNamespace(
                                id=uuid4(),
                                position=1,
                                is_public=True,
                                is_constructor=True,
                                function_config=SimpleNamespace(
                                    id=create_id,
                                    name="create",
                                    description="Create the home",
                                ),
                            ),
                            SimpleNamespace(
                                id=uuid4(),
                                position=3,
                                is_public=False,
                                is_constructor=False,
                                function_config=SimpleNamespace(
                                    id=private_id,
                                    name="private",
                                    description="Private operation",
                                ),
                            ),
                        ),
                    ),
                ),
            )
        ),
    )

    objects = runtime_discovery.build_program_capability_objects(index=index)

    assert len(objects) == 1
    assert objects[0].id == home_id
    assert objects[0].name == "Home"
    assert [fn.name for fn in objects[0].functions] == ["create", "close"]
    assert [fn.id for fn in objects[0].functions] == [create_id, close_id]
    assert [fn.is_constructor for fn in objects[0].functions] == [True, False]


def test_program_runtime_discovery_builds_describe_opgs_from_meta_index() -> None:
    function_edge_id = uuid4()
    constructor_function_id = uuid4()
    root_node_id = uuid4()
    root_class_config_id = uuid4()
    opg_id = uuid4()

    index = SimpleNamespace(
        ocg=SimpleNamespace(
            object_config_graph_nodes=(
                SimpleNamespace(
                    type="class",
                    class_config=SimpleNamespace(
                        class_config_function_configs=(
                            SimpleNamespace(
                                id=function_edge_id,
                                function_config=SimpleNamespace(
                                    id=constructor_function_id,
                                ),
                            ),
                        ),
                    ),
                ),
            )
        ),
        opg_by_id={
            opg_id: SimpleNamespace(
                id=opg_id,
                projection_hash="sha256:test:home",
                name="Home",
                description="Home projection",
                supports_virtual_build=True,
                object_projection_graph_constructors=(
                    SimpleNamespace(
                        function_constructor_id=function_edge_id,
                        root_node_id=root_node_id,
                    ),
                    SimpleNamespace(
                        function_constructor_id=uuid4(),
                        root_node_id=root_node_id,
                    ),
                ),
                object_projection_graph_nodes=(
                    SimpleNamespace(
                        id=root_node_id,
                        class_config_id=root_class_config_id,
                    ),
                ),
            )
        },
    )

    opgs = runtime_discovery.build_program_describe_environment_opgs(index=index)

    assert len(opgs) == 1
    assert opgs[0].id == opg_id
    assert opgs[0].projection_hash == "sha256:test:home"
    assert opgs[0].name == "Home"
    assert opgs[0].supports_virtual_build is True
    assert len(opgs[0].constructors) == 1
    assert opgs[0].constructors[0].function_id == constructor_function_id
    assert opgs[0].constructors[0].root_class_config_id == root_class_config_id


def test_program_runtime_invocation_discovery_sources_are_clean() -> None:
    runtime_dir = Path(__file__).resolve().parents[1] / "aware_experience" / "program"

    assert "aware_runtime" not in (runtime_dir / "runtime_invocation.py").read_text(
        encoding="utf-8"
    )
    assert "aware_runtime" not in (runtime_dir / "runtime_discovery.py").read_text(
        encoding="utf-8"
    )
