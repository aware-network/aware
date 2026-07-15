from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import msgpack

from aware_api_runtime.dependencies.runtime_resolution import (
    _RuntimeDependencyPackage,
    _compute_runtime_dependency_source_digest,
)
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.manifest.loader import load_aware_toml_spec
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.config.object_config_graph_node_layout import (
    ObjectConfigGraphNodeLayout,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_orm.runtime.models_manifest import ClassModelEntry, ModelsManifest


def write_home_api_dependency_runtime_artifacts(root: Path) -> None:
    write_ontology_dependency_runtime_artifacts(
        package_root=root / "modules" / "home" / "structure" / "ontology",
        package_name="home-ontology",
        fqn_prefix="aware_home",
        class_refs=("aware_home.home.Home", "aware_home.home.Door"),
        projection_names=("Home",),
    )
    write_python_models_manifest_for_refs(
        package_root=root / "apis" / "types" / "home",
        class_refs=(
            "aware_home_api.default.door.LockDoor",
            "aware_home_api.door.LockDoorResult",
            "aware_home_api.door.UnlockDoor",
            "aware_home_api.door.UnlockDoorResult",
            "aware_home_api.door.CloseDoor",
            "aware_home_api.door.CloseDoorResult",
            "aware_home_api.door.DoorSnapshot",
            "aware_home_api.door.DoorDelta",
            "aware_home_api.door.DoorByLabel",
            "aware_home_api.door.DoorDevice",
            "aware_home_api.default.door.BundleReleaseIdentity",
        ),
    )


def home_api_accessible_graphs() -> tuple[ObjectConfigGraph, ...]:
    return (
        _object_config_graph(
            package_name="home-ontology",
            fqn_prefix="aware_home",
            class_refs=("aware_home.home.Home", "aware_home.home.Door"),
            projection_names=("Home",),
        ),
        _object_config_graph(
            package_name="home-api",
            fqn_prefix="aware_home_api",
            class_refs=(
                "aware_home_api.door.LockDoor",
                "aware_home_api.door.LockDoorResult",
                "aware_home_api.door.UnlockDoor",
                "aware_home_api.door.UnlockDoorResult",
                "aware_home_api.door.CloseDoor",
                "aware_home_api.door.CloseDoorResult",
                "aware_home_api.door.DoorSnapshot",
                "aware_home_api.door.DoorDelta",
                "aware_home_api.door.DoorByLabel",
                "aware_home_api.door.DoorDevice",
                "aware_home_api.door.BundleReleaseIdentity",
            ),
            projection_names=(),
        ),
    )


def write_focus_api_dependency_runtime_artifacts(root: Path) -> None:
    write_ontology_dependency_runtime_artifacts(
        package_root=root / "modules" / "focus" / "structure" / "ontology",
        package_name="focus-ontology",
        fqn_prefix="aware_focus",
        class_refs=("aware_focus.focus.FocusScope",),
        projection_names=("FocusScope",),
    )
    write_python_models_manifest_for_refs(
        package_root=root / "apis" / "types" / "focus",
        class_refs=(
            "aware_focus_service_dto.comms.models.GetFocusRequest",
            "aware_focus_service_dto.comms.models.GetFocusResponse",
        ),
    )


def focus_api_accessible_graphs() -> tuple[ObjectConfigGraph, ...]:
    return (
        _object_config_graph(
            package_name="focus-ontology",
            fqn_prefix="aware_focus",
            class_refs=("aware_focus.focus.FocusScope",),
            projection_names=("FocusScope",),
        ),
        _object_config_graph(
            package_name="focus-service-dto",
            fqn_prefix="aware_focus_service_dto",
            class_refs=(
                "aware_focus_service_dto.comms.models.GetFocusRequest",
                "aware_focus_service_dto.comms.models.GetFocusResponse",
            ),
            projection_names=(),
        ),
    )


def write_ontology_dependency_runtime_artifacts(
    *,
    package_root: Path,
    package_name: str,
    fqn_prefix: str,
    class_refs: tuple[str, ...],
    projection_names: tuple[str, ...] = (),
) -> None:
    package = _runtime_dependency_package(
        package_root=package_root,
        package_name=package_name,
    )
    graph = _object_config_graph(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        class_refs=class_refs,
        projection_names=projection_names,
    )
    runtime_root = package.runtime_manifest_path.parent
    runtime_root.mkdir(parents=True, exist_ok=True)
    package.runtime_manifest_path.write_text(
        '{"ocg": {"snapshot": "ocg.snapshot.msgpack"}}\n',
        encoding="utf-8",
    )
    (runtime_root / "ocg.snapshot.msgpack").write_bytes(
        msgpack.packb(
            graph.model_dump(mode="json", by_alias=True, exclude_none=True),
            use_bin_type=True,
        )
    )
    write_python_models_manifest_for_refs(
        package_root=package_root,
        class_refs=class_refs,
        ontology_runtime=True,
    )
    package.runtime_source_digest_path.parent.mkdir(parents=True, exist_ok=True)
    package.runtime_source_digest_path.write_text(
        _compute_runtime_dependency_source_digest(package=package),
        encoding="utf-8",
    )


def write_python_models_manifest_for_refs(
    *,
    package_root: Path,
    class_refs: tuple[str, ...],
    ontology_runtime: bool = False,
) -> None:
    if ontology_runtime:
        path = (
            package_root
            / "python"
            / "orm_runtime"
            / ".aware"
            / "materializations"
            / "python.models.json"
        )
    else:
        path = package_root / ".aware" / "materializations" / "python.models.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        ModelsManifest(
            language="python",
            classes=[
                _class_model_entry(class_ref=class_ref) for class_ref in class_refs
            ],
        ).model_dump_json(indent=2),
        encoding="utf-8",
    )


def _runtime_dependency_package(
    *,
    package_root: Path,
    package_name: str,
) -> _RuntimeDependencyPackage:
    aware_toml_path = package_root / "aware.toml"
    return _RuntimeDependencyPackage(
        package_name=package_name,
        aware_toml_path=aware_toml_path.resolve(),
        package_root=package_root.resolve(),
        spec=load_aware_toml_spec(toml_path=aware_toml_path),
    )


def _object_config_graph(
    *,
    package_name: str,
    fqn_prefix: str,
    class_refs: tuple[str, ...],
    projection_names: tuple[str, ...],
) -> ObjectConfigGraph:
    graph_id = uuid4()
    nodes = [
        _object_config_graph_node(graph_id=graph_id, class_ref=class_ref)
        for class_ref in class_refs
    ]
    return ObjectConfigGraph.model_construct(
        id=graph_id,
        name=package_name,
        fqn_prefix=fqn_prefix,
        hash=f"sha256:{package_name}",
        language=CodeLanguage.aware,
        object_config_graph_nodes=nodes,
        object_projection_graphs=[
            ObjectProjectionGraph.model_construct(
                id=uuid4(),
                object_config_graph_id=graph_id,
                name=name,
                language=CodeLanguage.aware,
                projection_hash=f"sha256:{fqn_prefix}:{name}",
            )
            for name in projection_names
        ],
    )


def _object_config_graph_node(
    *,
    graph_id: UUID,
    class_ref: str,
) -> ObjectConfigGraphNode:
    class_name = class_ref.rsplit(".", 1)[-1]
    class_config_id = uuid4()
    class_config = ClassConfig.model_construct(
        id=class_config_id,
        class_fqn=class_ref,
        name=class_name,
        is_base=True,
        class_config_attribute_configs=[],
        class_config_function_configs=[],
        class_config_relationships=[],
    )
    if class_ref == "aware_home.home.Door":
        class_config.class_config_function_configs.extend(
            (
                _class_function_config(
                    class_config_id=class_config_id,
                    owner_key=class_ref,
                    name="lock",
                ),
                _class_function_config(
                    class_config_id=class_config_id,
                    owner_key=class_ref,
                    name="open",
                ),
            )
        )
    node = ObjectConfigGraphNode.model_construct(
        id=uuid4(),
        type=ObjectConfigGraphNodeType.class_,
        node_key=class_ref,
        object_config_graph_id=graph_id,
        class_config=class_config,
        layouts=[],
    )
    relative_path = _relative_layout_path_for_class_ref(class_ref=class_ref)
    if relative_path is not None:
        node.layouts.append(
            ObjectConfigGraphNodeLayout(
                object_config_graph_node_id=node.id,
                layout_kind="aware",
                relative_path=relative_path,
                source_position=0,
            )
        )
    class_config.object_config_graph_node_id = node.id
    return node


def _relative_layout_path_for_class_ref(*, class_ref: str) -> str | None:
    if class_ref.startswith("aware_home_api.door."):
        if class_ref.endswith(".DoorDevice") or class_ref.endswith(".DoorByLabel"):
            return "door/keys.aware"
        return "door/endpoints.aware"
    if class_ref.startswith("aware_focus_service_dto.comms.models."):
        return "section/models.aware"
    if class_ref.startswith("aware_home.home."):
        return f"home/{_snake_case(class_ref.rsplit('.', 1)[-1])}.aware"
    if class_ref.startswith("aware_focus.focus."):
        return "focus/focus_scope.aware"
    return None


def _class_function_config(
    *,
    class_config_id: UUID,
    owner_key: str,
    name: str,
) -> ClassConfigFunctionConfig:
    function_config = FunctionConfig.model_construct(
        id=uuid4(),
        owner_key=owner_key,
        name=name,
        description=None,
        verb=None,
        is_async=False,
    )
    return ClassConfigFunctionConfig.model_construct(
        id=uuid4(),
        class_config_id=class_config_id,
        function_config_id=function_config.id,
        function_config=function_config,
        is_public=True,
        is_constructor=False,
        position=0,
    )


def _class_model_entry(*, class_ref: str) -> ClassModelEntry:
    return ClassModelEntry(
        class_config_id=uuid4(),
        module=_python_module_for_class_ref(class_ref=class_ref),
        name=class_ref.rsplit(".", 1)[-1],
        aware_class_ref=class_ref,
    )


def _python_module_for_class_ref(*, class_ref: str) -> str:
    parts = [part.strip() for part in class_ref.split(".") if part.strip()]
    if len(parts) <= 1:
        return class_ref
    return ".".join([*parts[:-1], _snake_case(parts[-1])])


def _snake_case(value: str) -> str:
    chars: list[str] = []
    for index, char in enumerate(value):
        if char.isupper() and index > 0:
            chars.append("_")
        chars.append(char.lower())
    return "".join(chars)
