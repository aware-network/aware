from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from aware_code.types import JsonArray, JsonObject
from aware_identity.handlers._generated import meta_handlers as identity_meta_handlers
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.runtime import (
    META_SYSTEM_ACTOR_ID,
    MetaGraphCallTarget,
    MetaGraphFunctionImplOwnership,
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphImplementationPolicy,
    MetaGraphInvokeFunctionInput,
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


IDENTITY_CLASS_FQN = "aware_identity.identity.Identity"
ACTOR_CLASS_FQN = "aware_identity.actor.Actor"
CREDENTIAL_PROFILE_CLASS_FQN = "aware_identity.credential.CredentialProfile"

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


def _resolve_function_id(
    *,
    index: MetaGraphRuntimeIndex,
    class_fqn: str,
    function_name: str,
) -> UUID:
    matches: list[UUID] = []
    for class_config in index.class_configs_by_id.values():
        if class_config.class_fqn != class_fqn:
            continue
        for edge in class_config.class_config_function_configs:
            function_config = edge.function_config
            if function_config.name == function_name:
                matches.append(function_config.id)
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise AssertionError(
            "FunctionConfig not found in Meta graph index: "
            f"class_fqn={class_fqn!r} function_name={function_name!r}"
        )
    raise AssertionError(
        "FunctionConfig is ambiguous in Meta graph index: "
        f"class_fqn={class_fqn!r} function_name={function_name!r} "
        f"matches={matches}"
    )


async def _class_instance_id_for_source_object(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    source_object_id: UUID,
) -> UUID:
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    assert head and head.get("commit_id") and head.get("object_instance_graph_id")
    opg = index.opg_by_hash[projection_hash]
    oig, _ = await OIGMaterializer().get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=UUID(str(head["commit_id"])),
        oig_id=UUID(str(head["object_instance_graph_id"])),
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    for instance in oig.class_instances:
        if instance.source_object_id == source_object_id and instance.id is not None:
            return instance.id
    raise AssertionError(
        "Source object was not found in committed Identity lane: "
        f"source_object_id={source_object_id}"
    )


async def _invoke_identity_instance(
    *,
    runtime: MetaGraphRuntime,
    lane: LaneIds,
    branch_id: UUID,
    projection_hash: str,
    source_object_id: UUID,
    function_name: str,
    kwargs: dict[str, object],
):
    context = runtime.context
    assert context is not None
    target_object_id = await _class_instance_id_for_source_object(
        index=context.index,
        branch_id=branch_id,
        projection_hash=projection_hash,
        source_object_id=source_object_id,
    )
    return await runtime.invoke_function(
        MetaGraphInvokeFunctionInput(
            index=context.index,
            actor_id=lane.actor_id or META_SYSTEM_ACTOR_ID,
            function_id=_resolve_function_id(
                index=context.index,
                class_fqn=IDENTITY_CLASS_FQN,
                function_name=function_name,
            ),
            domain_branch_id=branch_id,
            domain_projection_hash=projection_hash,
            call_target=MetaGraphCallTarget.instance,
            target_object_id=target_object_id,
            object_projection_graph_id=None,
            args=JsonArray([]),
            kwargs=JsonObject(
                {str(key): _jsonify_value(value) for key, value in kwargs.items()}
            ),
            commit=True,
            publish=False,
        )
    )


def _jsonify_value(value: object) -> object:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, tuple):
        return [_jsonify_value(item) for item in value]
    if isinstance(value, list):
        return [_jsonify_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonify_value(item) for key, item in value.items()}
    return value


def _identity_lane(*, actor_id: UUID, branch_id: UUID | None = None) -> LaneIds:
    return LaneIds(
        branch_id=branch_id,
        actor_id=actor_id,
    )


@pytest.mark.asyncio
async def test_identity_signup_module_proof(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    import aware_identity_ontology  # noqa: F401
    from aware_identity_ontology.stable_ids import (
        stable_actor_id,
        stable_human_id,
        stable_identity_id,
    )

    key_hex = "11" * 32
    public_key = f"ed25519:{key_hex}"

    expected_identity_id = stable_identity_id(public_key=public_key, type="human")
    expected_actor_id = stable_actor_id(identity_id=expected_identity_id, key="default")
    expected_human_id = stable_human_id(actor_id=expected_actor_id)

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
                    expected_root_object_id=expected_identity_id,
                )
            ],
        )
        assertions.expect_root(expected_identity_id)
        assertions.expect_instance(expected_identity_id)
        assertions.expect_instance(expected_actor_id)
        assertions.expect_instance(expected_human_id)

        assertions.expect_edge(
            source_id=expected_identity_id, target_id=expected_human_id
        )
        assertions.expect_edge(source_id=expected_human_id, target_id=expected_actor_id)
        assertions.expect_edge(
            source_id=expected_actor_id, target_id=expected_identity_id
        )
        assert result.root_object_id == expected_identity_id

        commit_id = result.responses[-1].commit_id
        assert commit_id is not None
        meta_path = (
            aware_root
            / ".aware"
            / "oig"
            / str(result.branch_id)
            / result.projection_hash
            / "commits"
            / f"{commit_id}.meta.json"
        )
        assert meta_path.is_file(), f"Expected commit metadata sidecar: {meta_path}"
        action_payload = json.loads(meta_path.read_text(encoding="utf-8"))
        assert action_payload["operation_label"] == "Identity.signup"
        assert result.commits[-1].commit.author_id == expected_actor_id


@pytest.mark.asyncio
async def test_identity_signup_agent_module_proof(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    import aware_identity_ontology  # noqa: F401
    from aware_identity_ontology.stable_ids import (
        stable_actor_id,
        stable_human_id,
        stable_identity_id,
    )

    key_hex = "22" * 32
    public_key = f"ed25519:{key_hex}"

    expected_identity_id = stable_identity_id(public_key=public_key, type="agent")
    expected_actor_id = stable_actor_id(identity_id=expected_identity_id, key="default")
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
                    kwargs={"type": "agent"},
                    expected_root_object_id=expected_identity_id,
                )
            ],
        )
        assertions.expect_root(expected_identity_id)
        assertions.expect_instance(expected_identity_id)

        ids = {
            ci.source_object_id or ci.id
            for ci in assertions.oig.class_instances
            if ci.id is not None or ci.source_object_id is not None
        }
        assert unexpected_human_id not in ids
        assert result.root_object_id == expected_identity_id
        assert result.commits[-1].commit.author_id == expected_actor_id


@pytest.mark.asyncio
async def test_identity_signup_system_module_proof(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    import aware_identity_ontology  # noqa: F401
    from aware_identity_ontology.stable_ids import (
        stable_actor_id,
        stable_identity_id,
    )

    key_hex = "33" * 32
    public_key = f"ed25519:{key_hex}"

    expected_identity_id = stable_identity_id(public_key=public_key, type="system")
    expected_actor_id = stable_actor_id(identity_id=expected_identity_id, key="default")

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
                    kwargs={"type": "system"},
                    expected_root_object_id=expected_identity_id,
                )
            ],
        )
        assertions.expect_root(expected_identity_id)
        assertions.expect_instance(expected_identity_id)
        assert result.root_object_id == expected_identity_id
        assert result.commits[-1].commit.author_id == expected_actor_id


@pytest.mark.asyncio
async def test_identity_actor_commit_module_proof(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    import aware_identity_ontology  # noqa: F401
    from aware_identity_ontology.stable_ids import (
        stable_actor_commit_id,
        stable_actor_id,
        stable_identity_id,
    )

    key_hex = "55" * 32
    public_key = f"ed25519:{key_hex}"

    expected_identity_id = stable_identity_id(public_key=public_key, type="human")
    expected_actor_id = stable_actor_id(identity_id=expected_identity_id, key="default")
    domain_branch_id = uuid5(
        NAMESPACE_URL, "aware://tests/identity/actor-commit/domain-branch"
    )
    domain_commit_id = uuid5(
        NAMESPACE_URL, "aware://tests/identity/actor-commit/domain-commit"
    )
    object_instance_graph_commit_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/identity/actor-commit/oig-commit",
    )
    receipt_actor_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/identity/actor-commit/receipt-actor",
    )
    domain_projection_hash = "identity-test-projection"
    expected_actor_commit_id = stable_actor_commit_id(
        actor_id=expected_actor_id,
        domain_branch_id=domain_branch_id,
        domain_projection_hash=domain_projection_hash,
        domain_commit_id=domain_commit_id,
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
            lane=_identity_lane(actor_id=expected_actor_id),
            opg_name="Identity",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=IDENTITY_CLASS_FQN,
                    function_name="signup",
                    args=[public_key],
                    expected_root_object_id=expected_identity_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=ACTOR_CLASS_FQN,
                    function_name="ensure_commit",
                    object_id=SourceObjectId(expected_actor_id),
                    kwargs={
                        "domain_branch_id": domain_branch_id,
                        "domain_projection_hash": domain_projection_hash,
                        "domain_commit_id": domain_commit_id,
                        "object_instance_graph_commit_id": object_instance_graph_commit_id,
                        "receipt_actor_id": receipt_actor_id,
                        "created_at_unix_ms": 1760000000000,
                        "operation_label": "Identity.signup",
                        "call_target": "opg_constructor",
                        "object_id": expected_identity_id,
                        "graph_hash_post": "actor-commit-proof-hash",
                        "object_instance_graph_id": domain_branch_id,
                        "root_object_id": expected_identity_id,
                        "head_version": 1,
                    },
                ),
            ],
        )

        assertions.expect_root(expected_identity_id)
        assertions.expect_instance(expected_actor_id)
        assertions.expect_instance(expected_actor_commit_id)
        assertions.expect_edge(
            source_id=expected_actor_id,
            target_id=expected_actor_commit_id,
            relationship_name="actor_commits",
        )
        assertions.expect_primitive(
            instance_id=expected_actor_commit_id,
            field_name="domain_branch_id",
            expected=domain_branch_id,
        )
        assertions.expect_primitive(
            instance_id=expected_actor_commit_id,
            field_name="domain_projection_hash",
            expected=domain_projection_hash,
        )
        assertions.expect_primitive(
            instance_id=expected_actor_commit_id,
            field_name="domain_commit_id",
            expected=domain_commit_id,
        )
        assertions.expect_primitive(
            instance_id=expected_actor_commit_id,
            field_name="object_instance_graph_commit_id",
            expected=object_instance_graph_commit_id,
        )
        assertions.expect_primitive(
            instance_id=expected_actor_commit_id,
            field_name="receipt_actor_id",
            expected=receipt_actor_id,
        )
        assertions.expect_primitive(
            instance_id=expected_actor_commit_id,
            field_name="operation_label",
            expected="Identity.signup",
        )
        assertions.expect_primitive(
            instance_id=expected_actor_commit_id,
            field_name="source",
            expected="environment_lane_commit_receipt",
        )
        assert result.root_object_id == expected_identity_id


@pytest.mark.asyncio
async def test_identity_organization_credential_profile_module_proof(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_identity_ontology  # noqa: F401
    from aware_identity_ontology.stable_ids import (
        stable_actor_id,
        stable_credential_grant_id,
        stable_credential_profile_id,
        stable_credential_readiness_receipt_id,
        stable_credential_secret_material_ref_id,
        stable_credential_usage_receipt_id,
        stable_identity_id,
    )

    key_hex = "44" * 32
    public_key = f"ed25519:{key_hex}"

    expected_identity_id = stable_identity_id(
        public_key=public_key, type="organization"
    )
    expected_actor_id = stable_actor_id(identity_id=expected_identity_id, key="default")
    expected_profile_id = stable_credential_profile_id(
        identity_id=expected_identity_id,
        profile_key="pypi.publish",
        target_kind="test_pypi",
    )
    expected_secret_ref_id = stable_credential_secret_material_ref_id(
        credential_profile_id=expected_profile_id,
        secret_ref_key="twine-password",
        resolver_kind="env_var",
    )
    expected_grant_id = stable_credential_grant_id(
        credential_profile_id=expected_profile_id,
        grant_key="publish",
        scope_kind="python-package",
        scope_value="aware-api-client",
    )
    expected_readiness_id = stable_credential_readiness_receipt_id(
        credential_profile_id=expected_profile_id,
        receipt_key="testpypi-local",
    )
    expected_usage_id = stable_credential_usage_receipt_id(
        credential_profile_id=expected_profile_id,
        receipt_key="plan-only",
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
                ),
                ProofCall(
                    target="instance",
                    class_fqn=IDENTITY_CLASS_FQN,
                    function_name="create_credential_profile",
                    object_id=SourceObjectId(expected_identity_id),
                    kwargs={
                        "profile_key": "pypi.publish",
                        "target_kind": "test_pypi",
                        "credential_kind": "api_key",
                        "status": "planned",
                        "display_name": "TestPyPI publisher",
                        "target_name": "aware-api-client",
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=CREDENTIAL_PROFILE_CLASS_FQN,
                    function_name="attach_secret_material_ref",
                    object_id=SourceObjectId(expected_profile_id),
                    kwargs={
                        "secret_ref_key": "twine-password",
                        "resolver_kind": "env_var",
                        "secret_name": "TWINE_PASSWORD",
                        "username_hint": "__token__",
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=CREDENTIAL_PROFILE_CLASS_FQN,
                    function_name="grant_scope",
                    object_id=SourceObjectId(expected_profile_id),
                    kwargs={
                        "grant_key": "publish",
                        "scope_kind": "python-package",
                        "scope_value": "aware-api-client",
                        "operation": "publish",
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=CREDENTIAL_PROFILE_CLASS_FQN,
                    function_name="record_readiness",
                    object_id=SourceObjectId(expected_profile_id),
                    kwargs={
                        "receipt_key": "testpypi-local",
                        "status": "missing",
                        "resolver_kind": "env_var",
                        "secret_ref_key": "twine-password",
                        "missing_requirements": ["TWINE_PASSWORD"],
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=CREDENTIAL_PROFILE_CLASS_FQN,
                    function_name="record_usage",
                    object_id=SourceObjectId(expected_profile_id),
                    kwargs={
                        "receipt_key": "plan-only",
                        "status": "planned",
                        "operation": "publish",
                        "target_ref": "testpypi:aware-api-client",
                        "secret_ref_key": "twine-password",
                        "receipt": {"would_execute": False},
                    },
                ),
            ],
        )

        assertions.expect_root(expected_identity_id)
        assertions.expect_instance(expected_identity_id)
        assertions.expect_instance(expected_profile_id)
        assertions.expect_instance(expected_secret_ref_id)
        assertions.expect_instance(expected_grant_id)
        assertions.expect_instance(expected_readiness_id)
        assertions.expect_instance(expected_usage_id)

        assertions.expect_edge(
            source_id=expected_identity_id,
            target_id=expected_profile_id,
            relationship_name="credential_profiles",
        )
        assertions.expect_edge(
            source_id=expected_profile_id,
            target_id=expected_secret_ref_id,
            relationship_name="secret_material_refs",
        )
        assertions.expect_edge(
            source_id=expected_profile_id,
            target_id=expected_grant_id,
            relationship_name="grants",
        )
        assertions.expect_edge(
            source_id=expected_profile_id,
            target_id=expected_readiness_id,
            relationship_name="readiness_receipts",
        )
        assertions.expect_edge(
            source_id=expected_profile_id,
            target_id=expected_usage_id,
            relationship_name="usage_receipts",
        )

        assertions.expect_primitive(
            instance_id=expected_profile_id,
            field_name="profile_key",
            expected="pypi.publish",
        )
        assertions.expect_primitive(
            instance_id=expected_profile_id,
            field_name="target_kind",
            expected="test_pypi",
        )
        assertions.expect_primitive(
            instance_id=expected_profile_id,
            field_name="identity_id",
            expected=expected_identity_id,
        )
        assertions.expect_primitive(
            instance_id=expected_secret_ref_id,
            field_name="secret_name",
            expected="TWINE_PASSWORD",
        )
        assertions.expect_primitive(
            instance_id=expected_secret_ref_id,
            field_name="resolver_kind",
            expected="env_var",
        )
        assertions.expect_primitive(
            instance_id=expected_grant_id,
            field_name="scope_value",
            expected="aware-api-client",
        )
        assertions.expect_primitive(
            instance_id=expected_readiness_id,
            field_name="status",
            expected="missing",
        )
        assertions.expect_primitive(
            instance_id=expected_usage_id,
            field_name="status",
            expected="planned",
        )
        assert result.root_object_id == expected_identity_id
        assert result.commits[-1].commit.author_id == expected_actor_id


@pytest.mark.asyncio
async def test_identity_signup_then_create_profile_two_commits(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_identity_ontology  # noqa: F401
    from aware_identity_ontology.stable_ids import (
        stable_actor_id,
        stable_human_id,
        stable_identity_id,
        stable_identity_profile_id,
    )

    key_hex = "11" * 32
    public_key = f"ed25519:{key_hex}"

    expected_identity_id = stable_identity_id(public_key=public_key, type="human")
    expected_actor_id = stable_actor_id(identity_id=expected_identity_id, key="default")
    expected_human_id = stable_human_id(actor_id=expected_actor_id)

    profile_public_handle = "luis"
    expected_profile_id = stable_identity_profile_id(
        public_handle=profile_public_handle,
    )

    lane = LaneIds(
        actor_id=expected_actor_id,
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
            opg_name="Identity",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=IDENTITY_CLASS_FQN,
                    function_name="signup",
                    args=[public_key],
                    expected_root_object_id=expected_identity_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=IDENTITY_CLASS_FQN,
                    function_name="create_profile",
                    object_id=SourceObjectId(expected_identity_id),
                    args=[
                        profile_public_handle,
                        "Luis",
                        "Luis Aware",
                        "US",
                        "en",
                        "Canonical year",
                        None,
                    ],
                ),
            ],
        )

        assertions.expect_root(expected_identity_id)
        assertions.expect_instance(expected_identity_id)
        assertions.expect_instance(expected_human_id)
        assertions.expect_instance(expected_profile_id)
        assertions.expect_edge(
            source_id=expected_identity_id, target_id=expected_profile_id
        )

        assertions.expect_primitive(
            instance_id=expected_profile_id,
            field_name="public_handle",
            expected="luis",
        )
        assertions.expect_primitive(
            instance_id=expected_profile_id,
            field_name="display_name",
            expected="Luis",
        )
        assertions.expect_primitive(
            instance_id=expected_profile_id,
            field_name="full_name",
            expected="Luis Aware",
        )
        assertions.expect_primitive(
            instance_id=expected_profile_id,
            field_name="country_code",
            expected="US",
        )
        assertions.expect_primitive(
            instance_id=expected_profile_id,
            field_name="language_code",
            expected="en",
        )
        assertions.expect_primitive(
            instance_id=expected_profile_id,
            field_name="bio",
            expected="Canonical year",
        )
        assert result.root_object_id == expected_identity_id
        assert len(result.commits) == 2


@pytest.mark.asyncio
async def test_identity_ensure_actor_agent_allows_keyed_secondary_actor(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_identity_ontology  # noqa: F401
    from aware_identity_ontology.stable_ids import (
        stable_actor_id,
        stable_identity_id,
    )

    key_hex = "77" * 32
    public_key = f"ed25519:{key_hex}"
    expected_identity_id = stable_identity_id(public_key=public_key, type="agent")
    expected_default_actor_id = stable_actor_id(
        identity_id=expected_identity_id,
        key="default",
    )
    expected_secondary_actor_id = stable_actor_id(
        identity_id=expected_identity_id,
        key="codex-main",
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
            lane=_identity_lane(actor_id=expected_default_actor_id),
            opg_name="Identity",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=IDENTITY_CLASS_FQN,
                    function_name="signup",
                    args=[public_key],
                    kwargs={"type": "agent"},
                    expected_root_object_id=expected_identity_id,
                ),
            ],
        )

        assertions.expect_root(expected_identity_id)
        response = await _invoke_identity_instance(
            runtime=runtime,
            lane=_identity_lane(actor_id=expected_default_actor_id),
            branch_id=result.branch_id,
            projection_hash=result.projection_hash,
            source_object_id=expected_identity_id,
            function_name="ensure_actor",
            kwargs={"key": "codex-main"},
        )
        assert response.status == "succeeded"
        assert isinstance(response.payload, dict)
        value = response.payload.get("value")
        assert isinstance(value, dict)
        assert value.get("id") == str(expected_secondary_actor_id)
        assert value.get("key") == "codex-main"


@pytest.mark.asyncio
async def test_identity_ensure_actor_human_rejects_non_default_key(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_identity_ontology  # noqa: F401
    from aware_identity_ontology.stable_ids import (
        stable_actor_id,
        stable_identity_id,
    )

    key_hex = "88" * 32
    public_key = f"ed25519:{key_hex}"
    expected_identity_id = stable_identity_id(public_key=public_key, type="human")
    expected_actor_id = stable_actor_id(identity_id=expected_identity_id, key="default")

    lane = _identity_lane(actor_id=expected_actor_id)
    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_identity_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        result, _assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="Identity",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=IDENTITY_CLASS_FQN,
                    function_name="signup",
                    args=[public_key],
                    kwargs={"type": "human"},
                    expected_root_object_id=expected_identity_id,
                ),
            ],
        )

        with pytest.raises(
            ValueError,
            match="only supports non-default keys for IdentityType.agent",
        ):
            await _invoke_identity_instance(
                runtime=runtime,
                lane=lane,
                branch_id=result.branch_id,
                projection_hash=result.projection_hash,
                source_object_id=expected_identity_id,
                function_name="ensure_actor",
                kwargs={"key": "codex-main"},
            )
