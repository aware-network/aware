from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from aware_identity.handlers._generated import meta_handlers as identity_meta_handlers
from aware_meta.runtime import (
    META_SYSTEM_ACTOR_ID,
    MetaGraphFunctionImplOwnership,
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphImplementationPolicy,
    MetaGraphRuntime,
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


ACTOR_CLASS_FQN = "aware_identity.actor.Actor"
IDENTITY_CLASS_FQN = "aware_identity.identity.Identity"
ROLE_CLASS_FQN = "aware_identity.role.Role"
ROLE_CONFIG_CLASS_FQN = "aware_identity.role.RoleConfig"

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


def _identity_lane(
    *,
    actor_id: UUID | None = None,
    branch_id: UUID | None = None,
    environment_id: UUID | None = None,
    process_id: UUID | None = None,
    thread_id: UUID | None = None,
) -> LaneIds:
    return LaneIds(
        branch_id=branch_id,
        actor_id=actor_id,
    )


@pytest.mark.asyncio
async def test_actor_role_portal_to_role_registered(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    import aware_identity_ontology  # noqa: F401
    import aware_meta_ontology  # noqa: F401

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

        actor_role_portals = idx.portal_index.portals_by_source_projection_hash.get(
            identity_opg.projection_hash,
            [],
        )
        assert any(
            p.reference_field_name == "role_config"
            and p.target_projection_hash == role_config_opg.projection_hash
            for p in actor_role_portals
        )


@pytest.mark.asyncio
async def test_actor_role_create_module_proof(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    import aware_identity_ontology  # noqa: F401
    import aware_meta_ontology  # noqa: F401
    from aware_identity_ontology.stable_ids import (
        stable_actor_id,
        stable_actor_role_id,
        stable_identity_id,
        stable_role_config_id,
        stable_role_id,
    )

    key_hex = "44" * 32
    public_key = f"ed25519:{key_hex}"
    identity_id = stable_identity_id(public_key=public_key, type="human")
    actor_id = stable_actor_id(identity_id=identity_id, key="default")

    role_config_name = "aware.identity.actor-role.module-proof"
    role_config_id = stable_role_config_id(name=role_config_name)
    oigi_id = uuid5(NAMESPACE_URL, "aware.identity.actor-role.module-proof:oigi")
    role_id = stable_role_id(
        role_config_id=role_config_id,
        object_instance_graph_identity_id=oigi_id,
        object_instance_graph_branch_key="all",
    )
    expected_actor_role_id = stable_actor_role_id(actor_id=actor_id, role_id=role_id)

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_identity_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )

        await run_meta_runtime_proof(
            runtime=runtime,
            lane=_identity_lane(
                actor_id=actor_id,
                branch_id=identity_id,
            ),
            opg_name="Identity",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=IDENTITY_CLASS_FQN,
                    function_name="signup",
                    args=[public_key],
                    expected_root_object_id=identity_id,
                )
            ],
        )
        await run_meta_runtime_proof(
            runtime=runtime,
            lane=_identity_lane(
                actor_id=META_SYSTEM_ACTOR_ID,
                branch_id=role_config_id,
            ),
            opg_name="RoleConfig",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ROLE_CONFIG_CLASS_FQN,
                    function_name="create",
                    args=[
                        role_config_name,
                        "Role policy for ActorRole module proof.",
                    ],
                    expected_root_object_id=role_config_id,
                )
            ],
        )
        await run_meta_runtime_proof(
            runtime=runtime,
            lane=_identity_lane(
                actor_id=META_SYSTEM_ACTOR_ID,
                branch_id=role_id,
            ),
            opg_name="Role",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ROLE_CLASS_FQN,
                    function_name="create",
                    args=[role_config_id, oigi_id],
                    expected_root_object_id=role_id,
                )
            ],
        )

        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=_identity_lane(
                actor_id=actor_id,
                branch_id=identity_id,
            ),
            opg_name="Identity",
            calls=[
                ProofCall(
                    target="instance",
                    class_fqn=ACTOR_CLASS_FQN,
                    function_name="add_role",
                    object_id=SourceObjectId(actor_id),
                    args=[role_id],
                ),
            ],
        )

        assertions.expect_root(identity_id)
        assertions.expect_instance(expected_actor_role_id)
        assertions.expect_edge(source_id=actor_id, target_id=expected_actor_role_id)
        assertions.expect_primitive(
            instance_id=expected_actor_role_id,
            field_name="actor_id",
            expected=actor_id,
        )
        assertions.expect_primitive(
            instance_id=expected_actor_role_id,
            field_name="role_id",
            expected=role_id,
        )
        assert result.branch_id == identity_id
