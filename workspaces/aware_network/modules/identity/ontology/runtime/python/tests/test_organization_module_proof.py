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


IDENTITY_CLASS_FQN = "aware_identity.identity.Identity"
ORGANIZATION_CLASS_FQN = "aware_identity.organization.Organization"

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


def _identity_lane(*, actor_id: UUID, branch_id: UUID | None = None) -> LaneIds:
    return LaneIds(
        actor_id=actor_id,
        branch_id=branch_id,
    )


@pytest.mark.asyncio
async def test_organization_portal_chain_registered(tmp_path: Path) -> None:
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
        organization_opg = next(
            opg for opg in idx.opg_by_hash.values() if opg.name == "Organization"
        )

        identity_portals = idx.portal_index.portals_by_source_projection_hash.get(
            identity_opg.projection_hash,
            [],
        )
        assert any(
            p.reference_field_name == "organization"
            and p.target_projection_hash == organization_opg.projection_hash
            for p in identity_portals
        )

        org_portals = idx.portal_index.portals_by_source_projection_hash.get(
            organization_opg.projection_hash,
            [],
        )
        assert any(
            p.reference_field_name == "actor"
            and p.target_projection_hash == identity_opg.projection_hash
            for p in org_portals
        )
        assert any(
            p.reference_field_name == "identity"
            and p.target_projection_hash == identity_opg.projection_hash
            for p in org_portals
        )


@pytest.mark.asyncio
async def test_identity_signup_organization_module_proof(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    import aware_identity_ontology  # noqa: F401
    from aware_identity_ontology.stable_ids import (
        stable_actor_id,
        stable_human_id,
        stable_identity_id,
        stable_organization_id,
    )

    key_hex = "33" * 32
    public_key = f"ed25519:{key_hex}"

    expected_identity_id = stable_identity_id(
        public_key=public_key,
        type="organization",
    )
    expected_actor_id = stable_actor_id(
        identity_id=expected_identity_id,
        key="default",
    )
    expected_organization_id = stable_organization_id(actor_id=expected_actor_id)
    unexpected_human_id = stable_human_id(actor_id=expected_actor_id)

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_identity_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=_identity_lane(actor_id=expected_actor_id),
            opg_name="Identity",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=IDENTITY_CLASS_FQN,
                    function_name="signup",
                    args=[public_key],
                    kwargs={"type": "organization"},
                    expected_root_object_id=expected_identity_id,
                )
            ],
        )
        assertions.expect_root(expected_identity_id)
        assertions.expect_instance(expected_identity_id)
        assertions.expect_primitive(
            instance_id=expected_identity_id,
            field_name="organization_id",
            expected=expected_organization_id,
        )

        source_ids = {
            ci.source_object_id
            for ci in assertions.oig.class_instances
            if ci.source_object_id is not None
        }
        assert unexpected_human_id not in source_ids
        assert expected_organization_id not in source_ids
        assert result.root_object_id == expected_identity_id
        assert result.commits[-1].commit.author_id == expected_actor_id


@pytest.mark.asyncio
async def test_organization_create_then_add_member_module_proof(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_identity_ontology  # noqa: F401
    from aware_identity_ontology.stable_ids import (
        stable_actor_id,
        stable_identity_id,
        stable_organization_id,
        stable_organization_member_id,
    )

    org_key_hex = "aa" * 32
    org_public_key = f"ed25519:{org_key_hex}"
    org_identity_id = stable_identity_id(
        public_key=org_public_key,
        type="organization",
    )
    org_actor_id = stable_actor_id(identity_id=org_identity_id, key="default")
    organization_id = stable_organization_id(actor_id=org_actor_id)

    agent_key_hex = "bb" * 32
    agent_public_key = f"ed25519:{agent_key_hex}"
    agent_identity_id = stable_identity_id(public_key=agent_public_key, type="agent")
    agent_actor_id = stable_actor_id(identity_id=agent_identity_id, key="default")

    expected_member_id = stable_organization_member_id(
        organization_id=organization_id,
        identity_id=agent_identity_id,
    )

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
            lane=_identity_lane(actor_id=org_actor_id),
            opg_name="Identity",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=IDENTITY_CLASS_FQN,
                    function_name="signup",
                    args=[org_public_key],
                    kwargs={"type": "organization"},
                    expected_root_object_id=org_identity_id,
                )
            ],
        )

        await run_meta_runtime_proof(
            runtime=runtime,
            lane=_identity_lane(actor_id=agent_actor_id),
            opg_name="Identity",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=IDENTITY_CLASS_FQN,
                    function_name="signup",
                    args=[agent_public_key],
                    kwargs={"type": "agent"},
                    expected_root_object_id=agent_identity_id,
                )
            ],
        )

        _result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=_identity_lane(
                actor_id=org_actor_id,
                branch_id=organization_id,
            ),
            opg_name="Organization",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ORGANIZATION_CLASS_FQN,
                    function_name="create",
                    args=[org_actor_id],
                    expected_root_object_id=organization_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=ORGANIZATION_CLASS_FQN,
                    function_name="create_member",
                    object_id=SourceObjectId(organization_id),
                    args=[agent_identity_id, "member"],
                ),
            ],
        )

        assertions.expect_root(organization_id)
        assertions.expect_instance(organization_id)
        assertions.expect_instance(expected_member_id)
        assertions.expect_edge(source_id=organization_id, target_id=expected_member_id)
        assertions.expect_primitive(
            instance_id=expected_member_id,
            field_name="identity_id",
            expected=agent_identity_id,
        )
        assertions.expect_primitive(
            instance_id=expected_member_id,
            field_name="role",
            expected="member",
        )
