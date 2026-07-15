from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

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
    ROOT_OBJECT_ID,
    SourceObjectId,
    run_meta_runtime_proof,
)
from ._paths import REPO_ROOT


AUTH_TOKEN_CLASS_FQN = "aware_identity.auth.AuthToken"
AUTH_TOKEN_REGISTRY_CLASS_FQN = "aware_identity.auth.AuthTokenRegistry"

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


@pytest.mark.asyncio
async def test_auth_token_issue_and_revoke_module_proof(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    import aware_identity_ontology  # noqa: F401

    from aware_identity_ontology.identity.identity_enums import IdentityType
    from aware_identity_ontology.stable_ids import (
        stable_actor_id,
        stable_auth_token_registry_id,
        stable_identity_id,
    )

    key_hex = "22" * 32
    public_key = f"ed25519:{key_hex}"
    identity_id = stable_identity_id(
        public_key=public_key,
        type=IdentityType.human.value,
    )
    actor_id = stable_actor_id(identity_id=identity_id, key="default")

    registry_id = stable_auth_token_registry_id()
    token_id = uuid4()

    secret_bytes = bytes(range(32))
    expected_sha256 = hashlib.sha256(secret_bytes).hexdigest()
    issued_at = datetime(2026, 1, 1, tzinfo=timezone.utc).isoformat()

    env_id = uuid4()
    proc_id = uuid4()
    thread_id = uuid4()
    lane = LaneIds(
        branch_id=registry_id,
        actor_id=actor_id,
    )

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
            lane=lane,
            opg_name="AuthToken",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=AUTH_TOKEN_REGISTRY_CLASS_FQN,
                    function_name="ensure_registry",
                    expected_root_object_id=registry_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=AUTH_TOKEN_REGISTRY_CLASS_FQN,
                    function_name="create_token",
                    object_id=ROOT_OBJECT_ID,
                    args=[
                        actor_id,
                        public_key,
                        actor_id,
                        issued_at,
                        env_id,
                        proc_id,
                        thread_id,
                        expected_sha256,
                    ],
                    kwargs={
                        "label": "codex",
                        "scopes": ["agent:turn.execute"],
                        "token_id": token_id,
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=AUTH_TOKEN_CLASS_FQN,
                    function_name="revoke",
                    object_id=SourceObjectId(token_id),
                ),
            ],
        )

        assertions.expect_root(registry_id)
        assertions.expect_instance(registry_id)
        assertions.expect_instance(token_id)
        assertions.expect_edge(
            source_id=registry_id,
            target_id=token_id,
            relationship_name="tokens",
        )

        assertions.expect_primitive(
            instance_id=token_id,
            field_name="token_type",
            expected="apt",
        )
        assertions.expect_primitive(
            instance_id=token_id,
            field_name="actor_id",
            expected=actor_id,
        )
        assertions.expect_primitive(
            instance_id=token_id,
            field_name="public_key",
            expected=public_key,
        )
        assertions.expect_primitive(
            instance_id=token_id,
            field_name="context_environment_id",
            expected=env_id,
        )
        assertions.expect_primitive(
            instance_id=token_id,
            field_name="context_process_id",
            expected=proc_id,
        )
        assertions.expect_primitive(
            instance_id=token_id,
            field_name="context_thread_id",
            expected=thread_id,
        )
        assertions.expect_primitive(
            instance_id=token_id,
            field_name="sha256",
            expected=expected_sha256,
        )

        revoked_at = assertions.primitive(instance_id=token_id, field_name="revoked_at")
        assert revoked_at is not None

        issue_payload = result.responses[1].payload
        assert isinstance(issue_payload, dict)
        value = issue_payload.get("value")
        assert isinstance(value, dict)
        assert value.get("id") == str(token_id)
        assert value.get("sha256") == expected_sha256
