from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import UUID

import pytest

from aware_identity.handlers._generated import meta_handlers as identity_meta_handlers
from aware_meta.runtime import (
    MetaGraphFunctionImplOwnership,
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphImplementationPolicy,
    MetaGraphRuntime,
    MetaGraphRuntimeIndex,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot as IsolatedAwareRoot,
    LaneIds,
    ProofCall,
    SourceObjectId,
    run_meta_runtime_proof,
)
from ._paths import REPO_ROOT


ROLE_CONFIG_CLASS_FQN = "aware_identity.role.RoleConfig"
ROLE_CONFIG_CLASS_CONFIG_CLASS_FQN = "aware_identity.role.RoleConfigClassConfig"

_IDENTITY_META_HANDLERS_ANY: Any = identity_meta_handlers
_IDENTITY_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _IDENTITY_META_HANDLERS_ANY,
)
_IDENTITY_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _IDENTITY_META_HANDLERS_ANY,
)


def _identity_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    return tuple(
        repo_root / path
        for path in (
            "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml",
            "workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml",
            "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml",
            "workspaces/aware_kernel/modules/code/ontology/structure/aware.toml",
            "workspaces/aware_kernel/modules/history/ontology/structure/aware.toml",
            "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml",
            "workspaces/aware_kernel/modules/reactivity/ontology/structure/aware.toml",
            "workspaces/aware_network/modules/identity/ontology/structure/aware.toml",
        )
    )


def _build_identity_meta_runtime(
    *,
    repo_root: Path,
    aware_root: Path,
) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_identity_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(_IDENTITY_META_HANDLER_MODULE,),
        bootstrap_modules=(_IDENTITY_META_BOOTSTRAP_MODULE,),
        implementation_policy=MetaGraphImplementationPolicy(
            default_function_impl_ownership=MetaGraphFunctionImplOwnership.authored,
        ),
    )
    assert runtime.context is not None
    return runtime


def _identity_lane(*, branch_id: UUID | None = None) -> LaneIds:
    return LaneIds(
        branch_id=branch_id,
    )


def _identity_root_class_and_function_ids(
    index: MetaGraphRuntimeIndex,
) -> tuple[UUID, UUID]:
    identity_opg = next(
        opg for opg in index.opg_by_hash.values() if opg.name == "Identity"
    )
    identity_root = next(
        node for node in identity_opg.object_projection_graph_nodes if node.is_root
    )
    class_config_id = identity_root.class_config_id
    assert class_config_id is not None
    identity_root_class_config = index.class_configs_by_id[class_config_id]

    function_config_id: UUID | None = None
    for class_function_link in (
        identity_root_class_config.class_config_function_configs or []
    ):
        function_config = getattr(class_function_link, "function_config", None)
        if function_config is not None and isinstance(function_config.id, UUID):
            function_config_id = function_config.id
            break
        link_function_config_id = getattr(
            class_function_link,
            "function_config_id",
            None,
        )
        if isinstance(link_function_config_id, UUID):
            function_config_id = link_function_config_id
            break
    assert function_config_id is not None
    return class_config_id, function_config_id


@pytest.mark.asyncio
async def test_role_config_portal_chain_registered(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    import aware_identity_ontology  # noqa: F401

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_identity_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        context = runtime.context
        assert context is not None
        idx = context.index

        identity_opg = next(
            opg for opg in idx.opg_by_hash.values() if opg.name == "Identity"
        )
        role_config_opg = next(
            opg for opg in idx.opg_by_hash.values() if opg.name == "RoleConfig"
        )

        identity_portals = idx.portal_index.portals_by_source_projection_hash.get(
            identity_opg.projection_hash,
            [],
        )
        assert any(
            p.reference_field_name == "role_config"
            and p.target_projection_hash == role_config_opg.projection_hash
            for p in identity_portals
        )

        role_config_portals = idx.portal_index.portals_by_source_projection_hash.get(
            role_config_opg.projection_hash,
            [],
        )
        assert any(
            p.reference_field_name == "class_config" for p in role_config_portals
        )
        assert any(
            p.reference_field_name == "function_config" for p in role_config_portals
        )


@pytest.mark.asyncio
async def test_role_config_create_then_upsert_class_policy_commit(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_identity_ontology  # noqa: F401
    from aware_identity_ontology.role.role_enums import AccessLevelType
    from aware_identity_ontology.stable_ids import (
        stable_role_config_class_config_function_config_id,
        stable_role_config_class_config_id,
        stable_role_config_id,
    )

    role_config_name = "aware.identity.admin"
    expected_role_config_id = stable_role_config_id(name=role_config_name)

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_identity_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        context = runtime.context
        assert context is not None
        class_config_id, function_config_id = _identity_root_class_and_function_ids(
            context.index,
        )

        expected_policy_id = stable_role_config_class_config_id(
            role_config_id=expected_role_config_id,
            class_config_id=class_config_id,
        )
        expected_function_policy_id = (
            stable_role_config_class_config_function_config_id(
                role_config_class_config_id=expected_policy_id,
                function_config_id=function_config_id,
            )
        )

        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=_identity_lane(branch_id=expected_role_config_id),
            opg_name="RoleConfig",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ROLE_CONFIG_CLASS_FQN,
                    function_name="create",
                    args=[role_config_name, "Admin policy lane for identity"],
                    expected_root_object_id=expected_role_config_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=ROLE_CONFIG_CLASS_FQN,
                    function_name="upsert_class_config_policy",
                    object_id=SourceObjectId(expected_role_config_id),
                    args=[class_config_id, AccessLevelType.admin.value],
                ),
                ProofCall(
                    target="instance",
                    class_fqn=ROLE_CONFIG_CLASS_CONFIG_CLASS_FQN,
                    function_name="upsert_function_config_policy",
                    object_id=SourceObjectId(expected_policy_id),
                    args=[function_config_id, AccessLevelType.admin.value],
                ),
            ],
        )

        assertions.expect_root(expected_role_config_id)
        assertions.expect_instance(expected_role_config_id)
        assertions.expect_instance(expected_policy_id)
        assertions.expect_instance(expected_function_policy_id)
        assertions.expect_edge(
            source_id=expected_role_config_id,
            target_id=expected_policy_id,
        )
        assertions.expect_edge(
            source_id=expected_policy_id,
            target_id=expected_function_policy_id,
        )

        assertions.expect_primitive(
            instance_id=expected_role_config_id,
            field_name="name",
            expected=role_config_name,
        )
        assertions.expect_primitive(
            instance_id=expected_policy_id,
            field_name="role_config_id",
            expected=expected_role_config_id,
        )
        assertions.expect_primitive(
            instance_id=expected_policy_id,
            field_name="class_config_id",
            expected=class_config_id,
        )
        assertions.expect_primitive(
            instance_id=expected_policy_id,
            field_name="access_level",
            expected=AccessLevelType.admin.value,
        )
        assertions.expect_primitive(
            instance_id=expected_function_policy_id,
            field_name="role_config_class_config_id",
            expected=expected_policy_id,
        )
        assertions.expect_primitive(
            instance_id=expected_function_policy_id,
            field_name="function_config_id",
            expected=function_config_id,
        )
        assertions.expect_primitive(
            instance_id=expected_function_policy_id,
            field_name="access_level",
            expected=AccessLevelType.admin.value,
        )
        assert result.root_object_id == expected_role_config_id
