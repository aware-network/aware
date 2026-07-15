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
IDENTITY_CONNECTION_CLASS_FQN = "aware_identity.identity.IdentityConnection"

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


def _identity_lane(*, actor_id: UUID, branch_id: UUID) -> LaneIds:
    return LaneIds(
        actor_id=actor_id,
        branch_id=branch_id,
    )


@pytest.mark.asyncio
async def test_identity_connection_request_accept_module_proof(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_identity_ontology  # noqa: F401
    from aware_identity_ontology.stable_ids import (
        stable_actor_id,
        stable_identity_connection_id,
        stable_identity_id,
    )

    key_a = "11" * 32
    public_key_a = f"ed25519:{key_a}"
    identity_a = stable_identity_id(public_key=public_key_a, type="human")
    actor_a = stable_actor_id(identity_id=identity_a, key="default")

    key_b = "22" * 32
    public_key_b = f"ed25519:{key_b}"
    identity_b = stable_identity_id(public_key=public_key_b, type="human")
    actor_b = stable_actor_id(identity_id=identity_b, key="default")

    expected_connection_id = stable_identity_connection_id(
        requester_identity_id=identity_a,
        recipient_identity_id=identity_b,
        connection_type="connect",
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
            lane=_identity_lane(actor_id=actor_a, branch_id=identity_a),
            opg_name="Identity",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=IDENTITY_CLASS_FQN,
                    function_name="signup",
                    args=[public_key_a],
                    expected_root_object_id=identity_a,
                )
            ],
        )
        await run_meta_runtime_proof(
            runtime=runtime,
            lane=_identity_lane(actor_id=actor_b, branch_id=identity_b),
            opg_name="Identity",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=IDENTITY_CLASS_FQN,
                    function_name="signup",
                    args=[public_key_b],
                    expected_root_object_id=identity_b,
                )
            ],
        )

        _request_result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=_identity_lane(
                actor_id=actor_a,
                branch_id=expected_connection_id,
            ),
            opg_name="IdentityConnection",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=IDENTITY_CONNECTION_CLASS_FQN,
                    function_name="request",
                    kwargs={
                        "requester_identity_id": identity_a,
                        "recipient_identity_id": identity_b,
                        "connection_type": "connect",
                    },
                    expected_root_object_id=expected_connection_id,
                )
            ],
        )
        assertions.expect_root(expected_connection_id)
        assertions.expect_instance(expected_connection_id)
        assertions.expect_primitive(
            instance_id=expected_connection_id,
            field_name="connection_type",
            expected="connect",
        )
        assertions.expect_primitive(
            instance_id=expected_connection_id,
            field_name="requester_identity_id",
            expected=identity_a,
        )
        assertions.expect_primitive(
            instance_id=expected_connection_id,
            field_name="recipient_identity_id",
            expected=identity_b,
        )
        assertions.expect_primitive(
            instance_id=expected_connection_id,
            field_name="status",
            expected="pending",
        )

        _accept_result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=_identity_lane(
                actor_id=actor_b,
                branch_id=expected_connection_id,
            ),
            opg_name="IdentityConnection",
            calls=[
                ProofCall(
                    target="instance",
                    class_fqn=IDENTITY_CONNECTION_CLASS_FQN,
                    function_name="respond",
                    object_id=SourceObjectId(expected_connection_id),
                    args=["accepted"],
                )
            ],
        )
        assertions.expect_instance(expected_connection_id)
        assertions.expect_primitive(
            instance_id=expected_connection_id,
            field_name="status",
            expected="accepted",
        )
