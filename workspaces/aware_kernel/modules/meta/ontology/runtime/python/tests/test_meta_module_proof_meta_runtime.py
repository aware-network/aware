from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from aware_code.primitive_codec_base import build_code_primitive_type
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.primitive.code_primitive_enums import (
    CodePrimitiveBaseType,
)
from aware_meta.graph.config.stable_ids import (
    stable_attribute_type_descriptor_id,
)
from aware_meta.handlers._generated import meta_handlers
from aware_meta.primitive.config.builder import build_primitive_config
from aware_meta.runtime import (
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime import graph_identity_generated_handlers
from aware_meta.runtime.graph_context import MetaGraphRuntimeContext
from aware_meta.runtime.handler_executor import (
    MetaGraphFunctionImplOwnership,
    MetaGraphImplementationPolicy,
)
from aware_meta.runtime.testing import (
    MetaOIGAssertions,
    materialize_meta_runtime_lane_head,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from _meta_runtime_test_paths import META_PACKAGE_MANIFEST_PATHS, REPO_ROOT


@dataclass(frozen=True, slots=True)
class IsolatedMetaAwareRoot:
    root: Path
    persistence_backend: str = "fs"
    database_url: str | None = None
    _env_overrides: dict[str, str | None] = field(
        default_factory=dict,
        init=False,
        repr=False,
        compare=False,
    )

    def __enter__(self) -> Path:
        root = self.root.expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        (root / ".aware").mkdir(parents=True, exist_ok=True)
        env_overrides = {
            "AWARE_ROOT": os.environ.get("AWARE_ROOT"),
            "AWARE_PERSISTENCE_BACKEND": os.environ.get("AWARE_PERSISTENCE_BACKEND"),
            "DATABASE_URL": os.environ.get("DATABASE_URL"),
        }
        object.__setattr__(self, "_env_overrides", env_overrides)
        os.environ["AWARE_ROOT"] = str(root)
        os.environ["AWARE_PERSISTENCE_BACKEND"] = self.persistence_backend
        if self.database_url is None:
            _ = os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = self.database_url
        return root

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        for key, previous in self._env_overrides.items():
            if previous is None:
                _ = os.environ.pop(key, None)
            else:
                os.environ[key] = previous


def _meta_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    assert repo_root == REPO_ROOT
    return META_PACKAGE_MANIFEST_PATHS


def _build_graph_identity_meta_runtime(repo_root: Path):
    aware_root = Path(os.environ["AWARE_ROOT"])
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_meta_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(graph_identity_generated_handlers,),
        bootstrap_modules=(graph_identity_generated_handlers,),
    )
    assert runtime.context is not None
    return runtime


def _build_generated_meta_runtime(repo_root: Path):
    aware_root = Path(os.environ["AWARE_ROOT"])
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_meta_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(meta_handlers,),
        bootstrap_modules=(meta_handlers,),
        implementation_policy=MetaGraphImplementationPolicy(
            default_function_impl_ownership=(MetaGraphFunctionImplOwnership.authored),
        ),
    )
    assert runtime.context is not None
    return runtime


def _projection_by_name(
    context: MetaGraphRuntimeContext,
    name: str,
) -> ObjectProjectionGraph:
    return next(opg for opg in context.index.opg_by_hash.values() if opg.name == name)


def _stable_primitive_descriptor_ids(
    base_type: CodePrimitiveBaseType,
) -> tuple[UUID, UUID, UUID]:
    primitive_config = build_primitive_config(
        build_code_primitive_type(base_type=base_type)
    )
    descriptor_id = stable_attribute_type_descriptor_id(
        kind="primitive",
        collection_kind="single",
        entity_id=primitive_config.id,
        child_links_fingerprint="",
    )
    return descriptor_id, primitive_config.id, primitive_config.primitive_type.id


@pytest.mark.asyncio
async def test_meta_runtime_lane_commits_object_config_graph_identity_constructor(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    # Bootstrap generated ontology bindings used by ORM facade calls.
    import aware_meta_ontology  # noqa: F401
    from aware_meta_ontology.graph.config.object_config_graph_identity import (
        ObjectConfigGraphIdentity,
    )
    from aware_meta_ontology.stable_ids import (
        stable_object_config_graph_identity_id,
    )

    environment_id = uuid5(NAMESPACE_URL, "meta://tests/meta-runtime-proof/env")
    process_id = uuid5(NAMESPACE_URL, "meta://tests/meta-runtime-proof/process")
    thread_id = uuid5(NAMESPACE_URL, "meta://tests/meta-runtime-proof/thread")
    branch_id = uuid5(NAMESPACE_URL, "meta://tests/meta-runtime-proof/branch")
    ocgi_key = "kernel:identity"
    ocgi_id = stable_object_config_graph_identity_id(key=ocgi_key)

    with IsolatedMetaAwareRoot(tmp_path / "aware_root"):
        runtime = _build_graph_identity_meta_runtime(repo_root)
        context = runtime.context
        assert context is not None
        lane = runtime.bind(
            projection="ObjectConfigGraphIdentity",
            branch_id=branch_id,
        )
        with lane.activate(commit=True, publish=False):
            identity = await ObjectConfigGraphIdentity.create(
                key=ocgi_key,
                label="identity",
            )

        assert identity.id == ocgi_id
        assert lane.last_commit_id is not None
        assert lane.last_head_commit_id is not None
        assert lane.last_response is not None
        assert lane.last_response.root_object_id == ocgi_id

        oig = await materialize_meta_runtime_lane_head(
            runtime=runtime,
            lane=lane,
        )

    assertions = MetaOIGAssertions(oig=oig, index=context.index)
    assertions.expect_root(ocgi_id)
    assertions.expect_primitive(
        instance_id=ocgi_id,
        field_name="key",
        expected=ocgi_key,
    )


@pytest.mark.asyncio
async def test_meta_runtime_lane_commits_projection_identity_constructor_flow(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    # Bootstrap generated ontology bindings used by ORM facade calls.
    import aware_meta_ontology  # noqa: F401
    from aware_meta_ontology.graph.config.object_config_graph_identity import (
        ObjectConfigGraphIdentity,
    )
    from aware_meta_ontology.graph.projection.object_projection_graph_identity import (
        ObjectProjectionGraphIdentity,
    )
    from aware_meta_ontology.stable_ids import (
        stable_object_config_graph_identity_id,
        stable_object_projection_graph_identity_id,
    )

    environment_id = uuid5(NAMESPACE_URL, "meta://tests/meta-runtime-flow/env")
    process_id = uuid5(NAMESPACE_URL, "meta://tests/meta-runtime-flow/process")
    thread_id = uuid5(NAMESPACE_URL, "meta://tests/meta-runtime-flow/thread")
    ocgi_branch_id = uuid5(
        NAMESPACE_URL,
        "meta://tests/meta-runtime-flow/ocgi-branch",
    )
    opgi_branch_id = uuid5(
        NAMESPACE_URL,
        "meta://tests/meta-runtime-flow/opgi-branch",
    )
    ocgi_key = "kernel:identity"
    ocgi_id = stable_object_config_graph_identity_id(key=ocgi_key)

    with IsolatedMetaAwareRoot(tmp_path / "aware_root"):
        runtime = _build_graph_identity_meta_runtime(repo_root)
        context = runtime.context
        assert context is not None
        opgi_opg = _projection_by_name(
            context,
            "ObjectProjectionGraphIdentity",
        )
        opgi_id = stable_object_projection_graph_identity_id(
            object_config_graph_identity_id=ocgi_id,
            object_projection_graph_id=opgi_opg.id,
        )
        ocgi_lane = runtime.bind(
            projection="ObjectConfigGraphIdentity",
            branch_id=ocgi_branch_id,
        )
        with ocgi_lane.activate(commit=True, publish=False):
            ocgi = await ObjectConfigGraphIdentity.create(
                key=ocgi_key,
                label="identity",
            )

        opgi_lane = runtime.bind(
            projection="ObjectProjectionGraphIdentity",
            branch_id=opgi_branch_id,
        )
        with opgi_lane.activate(commit=True, publish=False):
            opgi = await ObjectProjectionGraphIdentity.create_via_object_config_graph_identity(
                object_config_graph_identity_id=ocgi.id,
                object_projection_graph_id=opgi_opg.id,
                projection_name=opgi_opg.name,
                label="identity",
            )

        assert ocgi.id == ocgi_id
        assert opgi.id == opgi_id
        assert ocgi_lane.last_response is not None
        assert ocgi_lane.last_response.root_object_id == ocgi_id
        assert opgi_lane.last_response is not None
        assert opgi_lane.last_response.root_object_id == opgi_id

        ocgi_oig = await materialize_meta_runtime_lane_head(
            runtime=runtime,
            lane=ocgi_lane,
        )
        opgi_oig = await materialize_meta_runtime_lane_head(
            runtime=runtime,
            lane=opgi_lane,
        )

    MetaOIGAssertions(oig=ocgi_oig, index=context.index).expect_root(ocgi_id)
    MetaOIGAssertions(oig=opgi_oig, index=context.index).expect_root(opgi_id)


@pytest.mark.asyncio
async def test_meta_runtime_lane_commits_projection_identity_function_impl(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    # Bootstrap generated ontology bindings used by ORM facade calls.
    import aware_meta_ontology  # noqa: F401
    from aware_meta_ontology.graph.config.object_config_graph_identity import (
        ObjectConfigGraphIdentity,
    )
    from aware_meta_ontology.stable_ids import (
        stable_object_config_graph_identity_id,
        stable_object_projection_graph_identity_id,
    )

    environment_id = uuid5(
        NAMESPACE_URL,
        "meta://tests/meta-runtime-observable/env",
    )
    process_id = uuid5(
        NAMESPACE_URL,
        "meta://tests/meta-runtime-observable/process",
    )
    thread_id = uuid5(
        NAMESPACE_URL,
        "meta://tests/meta-runtime-observable/thread",
    )
    ocgi_branch_id = uuid5(
        NAMESPACE_URL,
        "meta://tests/meta-runtime-observable/ocgi-branch",
    )
    ocgi_key = "kernel:identity"
    ocgi_id = stable_object_config_graph_identity_id(key=ocgi_key)

    with IsolatedMetaAwareRoot(tmp_path / "aware_root"):
        runtime = _build_graph_identity_meta_runtime(repo_root)
        context = runtime.context
        assert context is not None
        opgi_opg = _projection_by_name(
            context,
            "ObjectProjectionGraphIdentity",
        )
        opgi_id = stable_object_projection_graph_identity_id(
            object_config_graph_identity_id=ocgi_id,
            object_projection_graph_id=opgi_opg.id,
        )
        ocgi_lane = runtime.bind(
            projection="ObjectConfigGraphIdentity",
            branch_id=ocgi_branch_id,
        )
        with ocgi_lane.activate(commit=True, publish=False):
            ocgi = await ObjectConfigGraphIdentity.create(
                key=ocgi_key,
                label="identity",
            )

        with ocgi_lane.activate(commit=True, publish=False):
            opgi = await ocgi.create_object_projection_graph_identity(
                object_projection_graph_id=opgi_opg.id,
                projection_name=opgi_opg.name,
                label="identity",
            )

        assert ocgi_lane.last_response is not None
        assert ocgi_lane.last_response.changes

        ocgi_oig = await materialize_meta_runtime_lane_head(
            runtime=runtime,
            lane=ocgi_lane,
        )

    assert ocgi.id == ocgi_id
    assert opgi.id == opgi_id
    opgi_instances = [
        class_instance
        for class_instance in ocgi_oig.class_instances
        if class_instance.source_object_id == opgi_id
    ]
    assert len(opgi_instances) == 1
    MetaOIGAssertions(oig=ocgi_oig, index=context.index).expect_edge(
        source_id=ocgi_id,
        target_id=opgi_id,
    )


@pytest.mark.asyncio
async def test_meta_runtime_lane_commits_projection_observable_function_impl(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    # Bootstrap generated ontology bindings used by ORM facade calls.
    import aware_meta_ontology  # noqa: F401
    from aware_meta_ontology.graph.config.object_config_graph_identity import (
        ObjectConfigGraphIdentity,
    )
    from aware_meta_ontology.graph.projection.object_projection_graph_identity import (
        ObjectProjectionGraphIdentity,
    )
    from aware_meta_ontology.stable_ids import (
        stable_object_config_graph_identity_id,
        stable_object_projection_graph_identity_id,
        stable_object_projection_graph_observable_id,
    )

    environment_id = uuid5(
        NAMESPACE_URL,
        "meta://tests/meta-runtime-projection-observable/env",
    )
    process_id = uuid5(
        NAMESPACE_URL,
        "meta://tests/meta-runtime-projection-observable/process",
    )
    thread_id = uuid5(
        NAMESPACE_URL,
        "meta://tests/meta-runtime-projection-observable/thread",
    )
    ocgi_branch_id = uuid5(
        NAMESPACE_URL,
        "meta://tests/meta-runtime-projection-observable/ocgi-branch",
    )
    opgi_branch_id = uuid5(
        NAMESPACE_URL,
        "meta://tests/meta-runtime-projection-observable/opgi-branch",
    )
    ocgi_key = "kernel:identity"
    ocgi_id = stable_object_config_graph_identity_id(key=ocgi_key)
    observable_key = "default"

    with IsolatedMetaAwareRoot(tmp_path / "aware_root"):
        runtime = _build_graph_identity_meta_runtime(repo_root)
        context = runtime.context
        assert context is not None
        opgi_opg = _projection_by_name(
            context,
            "ObjectProjectionGraphIdentity",
        )
        opgi_id = stable_object_projection_graph_identity_id(
            object_config_graph_identity_id=ocgi_id,
            object_projection_graph_id=opgi_opg.id,
        )
        observable_selector_key = f"{opgi_opg.name}:{observable_key}"
        observable_id = stable_object_projection_graph_observable_id(
            object_projection_graph_identity_id=opgi_id,
            observable_key=observable_key,
        )
        ocgi_lane = runtime.bind(
            projection="ObjectConfigGraphIdentity",
            branch_id=ocgi_branch_id,
        )
        with ocgi_lane.activate(commit=True, publish=False):
            ocgi = await ObjectConfigGraphIdentity.create(
                key=ocgi_key,
                label="identity",
            )

        opgi_lane = runtime.bind(
            projection="ObjectProjectionGraphIdentity",
            branch_id=opgi_branch_id,
        )
        with opgi_lane.activate(commit=True, publish=False):
            opgi = await ObjectProjectionGraphIdentity.create_via_object_config_graph_identity(
                object_config_graph_identity_id=ocgi.id,
                object_projection_graph_id=opgi_opg.id,
                projection_name=opgi_opg.name,
                label="identity",
            )

        with opgi_lane.activate(commit=True, publish=False):
            observable = await opgi.create_observable(
                observable_key=observable_key,
                key=observable_selector_key,
                kind="construct",
                label="Default",
                position=0,
                is_default=True,
            )

        opgi_oig = await materialize_meta_runtime_lane_head(
            runtime=runtime,
            lane=opgi_lane,
        )

    assert ocgi.id == ocgi_id
    assert opgi.id == opgi_id
    assert observable.id == observable_id
    assert observable.observable_key == observable_key
    assert observable.key == observable_selector_key
    observable_instances = [
        class_instance
        for class_instance in opgi_oig.class_instances
        if class_instance.source_object_id == observable_id
    ]
    assert len(observable_instances) == 1
    MetaOIGAssertions(oig=opgi_oig, index=context.index).expect_edge(
        source_id=opgi_id,
        target_id=observable_id,
    )


@pytest.mark.asyncio
async def test_meta_runtime_lane_commits_ocg_attribute_update_primitive(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_meta_ontology  # noqa: F401
    from aware_meta_ontology.attribute.attribute_config import AttributeConfig
    from aware_meta_ontology.graph.config.object_config_graph import (
        ObjectConfigGraph,
    )
    from aware_meta_ontology.graph.config.object_config_graph_enums import (
        ObjectConfigGraphNodeType,
    )

    environment_id = uuid5(NAMESPACE_URL, "meta://tests/ocg-update/env")
    process_id = uuid5(NAMESPACE_URL, "meta://tests/ocg-update/process")
    thread_id = uuid5(NAMESPACE_URL, "meta://tests/ocg-update/thread")
    branch_id = uuid5(NAMESPACE_URL, "meta://tests/ocg-update/branch")
    class_fqn = "aware.meta.test.runtime.default.default.TestEntity"
    attr_name = "entity_id"
    string_descriptor_id, string_config_id, string_type_id = (
        _stable_primitive_descriptor_ids(CodePrimitiveBaseType.string)
    )

    with IsolatedMetaAwareRoot(tmp_path / "aware_root"):
        runtime = _build_generated_meta_runtime(repo_root)
        context = runtime.context
        assert context is not None
        lane = runtime.bind(
            projection="ObjectConfigGraph",
            branch_id=branch_id,
        )
        with lane.activate(commit=True, publish=False):
            graph = await ObjectConfigGraph.build(
                name="meta_test_ocg_runtime",
                hash="meta_test_ocg_runtime_hash",
                fqn_prefix="aware.meta.test.runtime",
                language=CodeLanguage.aware,
                description="Meta OCG runtime proof graph",
            )

        with lane.activate(commit=True, publish=False):
            class_node = await graph.create_node(
                type=ObjectConfigGraphNodeType.class_,
                node_key=class_fqn,
            )

        with lane.activate(commit=True, publish=False):
            class_config = await class_node.create_class(
                class_fqn=class_fqn,
                name="TestEntity",
                is_base=True,
                is_edge=False,
                description="Meta OCG class",
            )

        with lane.activate(commit=True, publish=False):
            attribute = await class_config.create_primitive_attribute_config(
                name=attr_name,
                primitive_base_type=CodePrimitiveBaseType.uuid,
                description=None,
                default_value=None,
                is_primary=False,
                is_public=True,
                is_required=True,
                is_unique=False,
                is_virtual=False,
                position=0,
            )

        assert isinstance(attribute, AttributeConfig)
        with lane.activate(commit=True, publish=False):
            await attribute.update_primitive(
                primitive_base_type=CodePrimitiveBaseType.string,
                description="Updated entity identifier contract",
                default_value="entity-0",
                is_primary=True,
                is_public=False,
                is_required=False,
                is_unique=True,
                is_virtual=False,
                exclude_serialization=True,
            )

        assert lane.last_response is not None
        assert lane.last_response.object_instance_graph_commit_id is not None
        assert lane.last_response.changes
        oig = await materialize_meta_runtime_lane_head(
            runtime=runtime,
            lane=lane,
        )

    assertions = MetaOIGAssertions(oig=oig, index=context.index)
    assertions.expect_instance(attribute.id)
    assertions.expect_instance(string_descriptor_id)
    assertions.expect_instance(string_config_id)
    assertions.expect_instance(string_type_id)
    assertions.expect_edge(source_id=attribute.id, target_id=string_descriptor_id)
    assertions.expect_edge(source_id=string_descriptor_id, target_id=string_config_id)
    assertions.expect_primitive(
        instance_id=attribute.id,
        field_name="description",
        expected="Updated entity identifier contract",
    )
    assertions.expect_primitive(
        instance_id=attribute.id,
        field_name="default_value",
        expected="entity-0",
    )
    assertions.expect_primitive(
        instance_id=attribute.id,
        field_name="is_primary",
        expected=True,
    )
    assertions.expect_primitive(
        instance_id=attribute.id,
        field_name="is_public",
        expected=False,
    )
    assertions.expect_primitive(
        instance_id=attribute.id,
        field_name="is_required",
        expected=False,
    )
    assertions.expect_primitive(
        instance_id=attribute.id,
        field_name="is_unique",
        expected=True,
    )
    assertions.expect_primitive(
        instance_id=attribute.id,
        field_name="exclude_serialization",
        expected=True,
    )
    assertions.expect_primitive(
        instance_id=string_type_id,
        field_name="base_type",
        expected="string",
    )


def test_meta_runtime_module_proof_has_no_runtime_harness_dependency() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    handler_source = Path(
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/runtime/"
        "graph_identity_generated_handlers.py"
    ).read_text(encoding="utf-8")
    factory_source = Path(
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/runtime/factory.py"
    ).read_text(encoding="utf-8")
    testing_source = Path(
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/runtime/testing/__init__.py"
    ).read_text(encoding="utf-8")

    forbidden_tokens = (
        "aware_" + "runtime",
        "Runtime" + "Harness",
        "FunctionCall" + "Invoker",
        "get" + "attr(",
    )
    for forbidden in forbidden_tokens:
        assert forbidden not in source
        assert forbidden not in handler_source
        assert forbidden not in factory_source
        assert forbidden not in testing_source
