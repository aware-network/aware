from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import cast
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from aware_orm.registry import ORMModelRegistry
from aware_orm.models.orm_model import ORMModel
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.config.stable_ids import (
    stable_attribute_config_id,
    stable_class_config_id,
    stable_object_config_graph_id,
    stable_object_config_graph_node_id,
)
from aware_meta.graph.instance.commit.fs_store import FSCommitStore, FSSnapshotStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.handlers._generated import meta_handlers
from aware_meta.materialization.deltas.ocg_genesis import (
    MetaOcgGenesisSpec,
    ocg_genesis_preflight,
)
from aware_meta.materialization.deltas.ontology_execution.invocation import (
    execute_ontology_invocation_intents,
)
from aware_meta.runtime import build_meta_graph_runtime_for_aware_package_manifests
from aware_meta.runtime.handler_executor import (
    MetaGraphFunctionImplOwnership,
    MetaGraphImplementationPolicy,
)
from aware_meta.runtime.handler_executor.factory import (
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
)
from aware_meta.runtime.handler_executor.language_handler import (
    MetaGraphGeneratedLanguageHandlerCallable,
    MetaGraphGeneratedInvocationHandlerCallable,
    MetaGraphGeneratedLanguageHandlerKey,
)
from aware_meta.runtime.handler_executor.pre_state import (
    MetaGraphEmptyLaneBootstrapCallable,
)
from aware_meta.runtime.testing import MetaOIGAssertions
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.stable_ids import stable_object_config_graph_package_id
from aware_meta_ontology.stable_ids import stable_object_projection_graph_id
from aware_meta_ontology.stable_ids import stable_object_projection_graph_node_id
from _meta_runtime_test_paths import META_PACKAGE_MANIFEST_PATHS, REPO_ROOT


def _meta_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    assert repo_root == REPO_ROOT
    return META_PACKAGE_MANIFEST_PATHS


@dataclass(slots=True)
class _GeneratedLanguageHandlerModule:
    AWARE_META_GRAPH_HANDLERS: Mapping[
        MetaGraphGeneratedLanguageHandlerKey,
        MetaGraphGeneratedLanguageHandlerCallable,
    ]
    AWARE_META_GRAPH_INVOCATION_HANDLERS: Mapping[
        MetaGraphGeneratedLanguageHandlerKey,
        MetaGraphGeneratedInvocationHandlerCallable,
    ]


@dataclass(slots=True)
class _GeneratedConstructorBootstrapModule:
    AWARE_META_GRAPH_EMPTY_LANE_BOOTSTRAPS: Mapping[
        MetaGraphGeneratedLanguageHandlerKey,
        MetaGraphEmptyLaneBootstrapCallable,
    ]


@pytest.mark.asyncio
async def test_ocg_genesis_executes_functioncalls_and_hydrates_head(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    aware_root = tmp_path / "aware-root"
    (aware_root / ".aware").mkdir(parents=True)
    monkeypatch.setenv("AWARE_ROOT", str(aware_root))
    monkeypatch.setenv("AWARE_PERSISTENCE_BACKEND", "fs")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    import aware_meta_ontology  # noqa: F401

    handler_module: MetaGraphGeneratedLanguageHandlerModule = (
        _GeneratedLanguageHandlerModule(
            AWARE_META_GRAPH_HANDLERS=(meta_handlers.AWARE_META_GRAPH_HANDLERS),
            AWARE_META_GRAPH_INVOCATION_HANDLERS=(
                meta_handlers.AWARE_META_GRAPH_INVOCATION_HANDLERS
            ),
        )
    )
    bootstrap_module: MetaGraphGeneratedConstructorBootstrapModule = (
        _GeneratedConstructorBootstrapModule(
            AWARE_META_GRAPH_EMPTY_LANE_BOOTSTRAPS=(
                meta_handlers.AWARE_META_GRAPH_EMPTY_LANE_BOOTSTRAPS
            ),
        )
    )
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_meta_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(handler_module,),
        bootstrap_modules=(bootstrap_module,),
        implementation_policy=MetaGraphImplementationPolicy(
            default_function_impl_ownership=(MetaGraphFunctionImplOwnership.authored),
        ),
    )
    context = runtime.context
    assert context is not None
    registry_snapshot = ORMModelRegistry.snapshot_state()
    _attach_generated_orm_bindings(context=context)
    root_projection_hash = context.projection_hash_for_name("ObjectConfigGraph")

    spec = _genesis_spec()
    preflight = ocg_genesis_preflight(spec=spec)
    ontology_plan = cast(dict[str, object], preflight["ontology_execution_plan"])
    planned_invocation_intents = cast(
        Sequence[dict[str, object]],
        ontology_plan["invocation_intents"],
    )
    invocation_intents = tuple(
        intent
        for intent in planned_invocation_intents
        if intent.get("owner_class_name") != "ObjectConfigGraphPackage"
    )
    assert _runtime_orm_bindings_available(context=context)
    branch_id = uuid5(NAMESPACE_URL, "meta://tests/ocg-genesis/branch")
    actor_id = uuid5(NAMESPACE_URL, "meta://tests/ocg-genesis/actor")

    try:
        execution_receipt = await execute_ontology_invocation_intents(
            runtime=runtime,
            graph_runtime_context=context,
            actor_id=actor_id,
            branch_id=branch_id,
            projection_hash=root_projection_hash,
            invocation_intents=invocation_intents,
        )

        assert execution_receipt["status"] == (
            "ontology_function_call_execution_applied"
        ), json.dumps(execution_receipt, indent=2, sort_keys=True, default=str)
        assert execution_receipt["applied_invocation_count"] == 6
        assert execution_receipt["did_execute"] is True
        assert execution_receipt["did_persist"] is True
        assert execution_receipt["commit_id"] is not None
        assert execution_receipt["object_instance_graph_commit_id"] is not None
        attribute_receipt = _receipt_for_semantic_key(
            execution_receipt=execution_receipt,
            semantic_key=(
                f"ocg:{spec.fqn_prefix}/node:{spec.class_fqn}"
                f"/attribute:{spec.attribute_name}"
            ),
            function_name="create_primitive_attribute_config",
        )
        assert attribute_receipt["commit_id"] is not None
        opg_create_receipt = _receipt_for_semantic_key(
            execution_receipt=execution_receipt,
            semantic_key=f"ocg:{spec.fqn_prefix}/projection:{spec.projection_name}",
            function_name="build_via_object_config_graph",
        )
        assert opg_create_receipt["commit_id"] is not None
        assert opg_create_receipt["result_projection_name"] == "ObjectProjectionGraph"
        opg_node_receipt = _receipt_for_semantic_key(
            execution_receipt=execution_receipt,
            semantic_key=(
                f"ocg:{spec.fqn_prefix}/projection:{spec.projection_name}"
                f"/node:{spec.class_fqn}"
            ),
            function_name="create_node",
        )
        assert opg_node_receipt["commit_id"] is not None
        assert opg_node_receipt["target_projection_name"] == "ObjectProjectionGraph"
        opg_projection_hash = context.projection_hash_for_name("ObjectProjectionGraph")
        assert opg_create_receipt["projection_hash"] == opg_projection_hash
        assert opg_node_receipt["projection_hash"] == opg_projection_hash

        materializer = OIGMaterializer(
            commits=FSCommitStore(root_dir=aware_root),
            snaps=FSSnapshotStore(root_dir=aware_root),
        )
        oig, _ = await materializer.get(
            branch_id=branch_id,
            ocg=context.index.ocg,
            opg=context.index.opg_by_hash[root_projection_hash],
            commit_id=UUID(str(attribute_receipt["commit_id"])),
        )
        assertions = MetaOIGAssertions(
            oig=oig,
            class_configs_by_id=dict(context.index.class_configs_by_id),
            relationships_by_id=dict(context.index.relationships_by_id),
        )
        assertions.expect_instance(UUID(spec.object_config_graph_id))
        assertions.expect_instance(UUID(spec.object_config_graph_node_id))
        assertions.expect_instance(UUID(spec.class_config_id))
        assertions.expect_instance(UUID(spec.attribute_config_id))
        assertions.expect_primitive(
            instance_id=UUID(spec.object_config_graph_id),
            field_name="fqn_prefix",
            expected=spec.fqn_prefix,
        )
        assertions.expect_primitive(
            instance_id=UUID(spec.class_config_id),
            field_name="name",
            expected=spec.class_name,
        )
        assertions.expect_primitive(
            instance_id=UUID(spec.attribute_config_id),
            field_name="name",
            expected=spec.attribute_name,
        )
        opg_oig, _ = await materializer.get(
            branch_id=branch_id,
            ocg=context.index.ocg,
            opg=context.index.opg_by_hash[opg_projection_hash],
            commit_id=UUID(str(opg_node_receipt["commit_id"])),
        )
        opg_assertions = MetaOIGAssertions(
            oig=opg_oig,
            class_configs_by_id=dict(context.index.class_configs_by_id),
            relationships_by_id=dict(context.index.relationships_by_id),
        )
        opg_assertions.expect_instance(UUID(spec.object_projection_graph_id))
        opg_assertions.expect_instance(UUID(spec.object_projection_graph_node_id))
        opg_assertions.expect_primitive(
            instance_id=UUID(spec.object_projection_graph_id),
            field_name="name",
            expected=spec.projection_name,
        )
        opg_assertions.expect_primitive(
            instance_id=UUID(spec.object_projection_graph_id),
            field_name="projection_hash",
            expected=spec.projection_hash,
        )
    finally:
        ORMModelRegistry.restore_state(registry_snapshot)


def _receipt_for_semantic_key(
    *,
    execution_receipt: dict[str, object],
    semantic_key: str,
    function_name: str,
) -> dict[str, object]:
    receipts = execution_receipt.get("invocation_receipts")
    assert isinstance(receipts, (list, tuple))
    for receipt in receipts:
        assert isinstance(receipt, dict)
        if (
            receipt.get("semantic_key") == semantic_key
            and receipt.get("function_name") == function_name
        ):
            return receipt
    raise AssertionError(
        "Invocation receipt not found: "
        f"semantic_key={semantic_key} function_name={function_name}"
    )


def _runtime_orm_bindings_available(*, context: object) -> bool:
    index = getattr(context, "index", None)
    class_configs_by_id = getattr(index, "class_configs_by_id", {})
    if not isinstance(class_configs_by_id, Mapping):
        return False
    for class_config in class_configs_by_id.values():
        if getattr(class_config, "name", None) != "ObjectConfigGraph":
            continue
        class_config_id = getattr(class_config, "id", None)
        if not isinstance(class_config_id, UUID):
            return False
        return (
            ORMModelRegistry.get_class_by_class_config_id(class_config_id) is not None
        )
    return False


def _attach_generated_orm_bindings(*, context: object) -> None:
    index = getattr(context, "index", None)
    class_configs_by_id = getattr(index, "class_configs_by_id", {})
    if not isinstance(class_configs_by_id, Mapping):
        return
    for class_config in class_configs_by_id.values():
        class_config_id = getattr(class_config, "id", None)
        class_fqn = getattr(class_config, "class_fqn", None)
        if not isinstance(class_config_id, UUID) or not isinstance(class_fqn, str):
            continue
        if ORMModelRegistry.get_class_by_class_config_id(class_config_id) is not None:
            continue
        model_class = _generated_model_class(class_fqn=class_fqn)
        if model_class is None:
            continue
        fqn = ORMModelRegistry.register_class_stub(model_class)
        model_class.bind_class_config(class_config)
        _ = ORMModelRegistry.attach_class_config(fqn, class_config)


def _generated_model_class(*, class_fqn: str) -> type[ORMModel] | None:
    provider, separator, remainder = class_fqn.partition(".")
    if not separator:
        return None
    ontology_package = _ontology_package_for_provider(provider=provider)
    if ontology_package is None:
        return None
    *module_parts, class_name = remainder.split(".")
    module_parts = [
        "class_" if part == "class" else part
        for part in module_parts
        if part != "default"
    ]
    module_name = ".".join(
        (ontology_package, *module_parts, _camel_to_snake(class_name))
    )
    try:
        module = import_module(module_name)
    except ModuleNotFoundError:
        return None
    model_class = getattr(module, class_name, None)
    if isinstance(model_class, type) and issubclass(model_class, ORMModel):
        return model_class
    return None


def _ontology_package_for_provider(*, provider: str) -> str | None:
    if not provider.startswith("aware_"):
        return None
    return f"{provider}_ontology"


def _camel_to_snake(value: str) -> str:
    first_pass = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", value)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", first_pass).lower()


def _genesis_spec() -> MetaOcgGenesisSpec:
    package_name = "demo-ontology"
    fqn_prefix = "aware_demo"
    graph_language = CodeLanguage.aware.value
    graph_id = stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=graph_language,
    )
    class_name = "Room"
    class_fqn = f"{fqn_prefix}.{class_name}"
    node_id = stable_object_config_graph_node_id(
        object_config_graph_id=graph_id,
        type=ObjectConfigGraphNodeType.class_.value,
        node_key=class_fqn,
    )
    class_config_id = stable_class_config_id(
        object_config_graph_node_id=node_id,
        class_fqn=class_fqn,
    )
    attribute_name = "name"
    projection_name = "Demo"
    object_projection_graph_id = stable_object_projection_graph_id(
        object_config_graph_id=graph_id,
        name=projection_name,
    )
    return MetaOcgGenesisSpec(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        source_ref="aware/home/model.aware",
        package_id=str(
            stable_object_config_graph_package_id(
                package_name=package_name,
                fqn_prefix=fqn_prefix,
            )
        ),
        object_config_graph_id=str(graph_id),
        object_config_graph_node_id=str(node_id),
        class_config_id=str(class_config_id),
        attribute_config_id=str(
            stable_attribute_config_id(
                owner_key=class_fqn,
                name=attribute_name,
            )
        ),
        object_projection_graph_id=str(object_projection_graph_id),
        object_projection_graph_node_id=str(
            stable_object_projection_graph_node_id(
                object_projection_graph_id=object_projection_graph_id,
                class_config_id=class_config_id,
            )
        ),
        class_name=class_name,
        attribute_name=attribute_name,
        graph_hash="sha256:ocg-genesis-graph",
        layout_hash="sha256:ocg-genesis-layout",
        projection_name=projection_name,
        projection_hash="sha256:opg-genesis-projection",
        package_title="Demo ontology",
        package_description="Demo package.",
        class_description="Room in a demo home.",
        attribute_description="Human-readable room name.",
    )
