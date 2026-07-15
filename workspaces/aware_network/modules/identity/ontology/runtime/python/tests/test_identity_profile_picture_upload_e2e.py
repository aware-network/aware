from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from aware_comms.http.file.router import FileRouter
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
from aware_node_service.http_api.file_ops import (
    download_file_handler,
    upload_file_handler,
)
from aware_storage.blob_store import compute_blob_hash
from aware_storage.handlers._generated import meta_handlers as storage_meta_handlers
from aware_storage.stable_ids import stable_storage_blob_id
from ._paths import REPO_ROOT


IDENTITY_CLASS_FQN = "aware_identity.identity.Identity"
IDENTITY_PROFILE_CLASS_FQN = "aware_identity.identity.IdentityProfile"

_IDENTITY_META_HANDLERS_ANY: Any = identity_meta_handlers
_IDENTITY_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _IDENTITY_META_HANDLERS_ANY,
)
_IDENTITY_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _IDENTITY_META_HANDLERS_ANY,
)
_STORAGE_META_HANDLERS_ANY: Any = storage_meta_handlers
_STORAGE_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _STORAGE_META_HANDLERS_ANY,
)
_STORAGE_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _STORAGE_META_HANDLERS_ANY,
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
        handler_modules=(_IDENTITY_META_HANDLER_MODULE, _STORAGE_META_HANDLER_MODULE),
        bootstrap_modules=(
            _IDENTITY_META_BOOTSTRAP_MODULE,
            _STORAGE_META_BOOTSTRAP_MODULE,
        ),
        implementation_policy=MetaGraphImplementationPolicy(
            default_function_impl_ownership=MetaGraphFunctionImplOwnership.authored,
        ),
    )
    assert runtime.context is not None
    return runtime


def _build_file_ops_app() -> FastAPI:
    app = FastAPI()
    router = FileRouter(
        upload_handler=upload_file_handler,
        download_handler=download_file_handler,
    ).register()
    app.include_router(router)
    return app


@pytest.mark.asyncio
async def test_identity_profile_picture_upload_then_commit_reference(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_identity_ontology  # noqa: F401
    from aware_identity_ontology.stable_ids import (
        stable_actor_id,
        stable_identity_id,
        stable_identity_profile_id,
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_identity_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        key_hex = "44" * 32
        public_key = f"ed25519:{key_hex}"
        expected_identity_id = stable_identity_id(public_key=public_key, type="human")
        expected_actor_id = stable_actor_id(
            identity_id=expected_identity_id, key="default"
        )
        expected_profile_id = stable_identity_profile_id(public_handle="pictureuser")

        image_bytes = b"identity-picture-upload-e2e"
        image_sha = compute_blob_hash(image_bytes)
        expected_blob_id = stable_storage_blob_id(sha=image_sha)

        client = TestClient(_build_file_ops_app())
        upload = client.post(
            "/crud/upload",
            headers={"Authorization": f"Bearer {expected_actor_id}"},
            files={"file": ("avatar.png", image_bytes, "image/png")},
        )
        assert upload.status_code == 200
        upload_payload = upload.json()
        assert upload_payload["object_id"] == str(expected_blob_id)
        assert upload_payload["sha"] == image_sha
        assert upload_payload["mime_type"] == "image/png"
        assert upload_payload["size_bytes"] == len(image_bytes)

        lane = LaneIds(
            actor_id=expected_actor_id,
        )

        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="Identity",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=IDENTITY_CLASS_FQN,
                    function_name="signup_via_profile",
                    args=[public_key],
                    kwargs={
                        "create_profile_request": {
                            "display_name": "Picture User",
                            "public_handle": "pictureuser",
                            "full_name": "Picture User",
                            "country_code": "US",
                            "language_code": "en",
                            "bio": "Picture flow",
                            "identity_type": "human",
                        }
                    },
                    expected_root_object_id=expected_identity_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=IDENTITY_PROFILE_CLASS_FQN,
                    function_name="update_picture",
                    object_id=SourceObjectId(expected_profile_id),
                    args=[
                        str(expected_blob_id),
                        image_sha,
                        "image/png",
                        len(image_bytes),
                    ],
                ),
            ],
        )

        assertions.expect_root(expected_identity_id)
        assertions.expect_instance(expected_profile_id)
        # StorageBlob is portal-routed via aware_storage.StorageBlob.
        # Identity projection commits only the FK reference (`image_id`) in-lane.
        image_id_value = assertions.primitive(
            instance_id=expected_profile_id,
            field_name="image_id",
        )
        assert image_id_value in {expected_blob_id, str(expected_blob_id)}
        assert result.root_object_id == expected_identity_id
