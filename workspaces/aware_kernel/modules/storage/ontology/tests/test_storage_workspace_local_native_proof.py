from __future__ import annotations

from pathlib import Path
import sys
from uuid import NAMESPACE_URL, uuid5

import pytest
from aware_meta_sdk import FunctionCallProof, OigCommitExpectation

_MODULES_ROOT = Path(__file__).resolve().parents[3]
if str(_MODULES_ROOT) not in sys.path:
    sys.path.insert(0, str(_MODULES_ROOT))

from kernel_native_behavior_proof_support import (  # noqa: E402
    assert_kernel_module_native_function_impl_receipt,
    kernel_module_native_behavior_proof,
    missing_kernel_module_native_receipts,
)

_STORAGE_MODULE_NAME = "storage"
_STORAGE_REQUIRED_RECEIPTS = (
    "structure/python/orm_runtime/aware_storage_ontology/blob/storage_blob.py",
)


@pytest.mark.asyncio
async def test_storage_workspace_local_native_meta_runtime_module_proof(
    tmp_path: Path,
) -> None:
    missing_receipts = missing_kernel_module_native_receipts(
        _STORAGE_MODULE_NAME,
        required_receipts=_STORAGE_REQUIRED_RECEIPTS,
    )
    if missing_receipts:
        pytest.skip(
            "Storage kernel native behavior proof requires workspace "
            "materialization receipts. Run `aware-cli workspace materialize "
            "--repo-root workspaces/aware_kernel --workspace-toml "
            "aware.workspace.toml --kernel-repo-root . --package "
            "storage-ontology --execute-heavy-semantic-materialization` first. "
            "Missing: " + ", ".join(path.as_posix() for path in missing_receipts)
        )

    sha = "A" * 64
    normalized_sha = sha.lower()
    branch_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/kernel/storage/meta-runtime/branch",
    )
    actor_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/kernel/storage/meta-runtime/actor",
    )

    with kernel_module_native_behavior_proof(
        module_name=_STORAGE_MODULE_NAME,
        projection="StorageBlob",
        aware_root_path=tmp_path / "aware_root",
        actor_id=actor_id,
        branch_id=branch_id,
        composite_name="Aware Kernel Storage Local Meta SDK Native Proof",
        required_receipts=_STORAGE_REQUIRED_RECEIPTS,
    ) as proof:
        import aware_storage_ontology
        from aware_storage_ontology.blob.storage_blob import StorageBlob
        from aware_storage_ontology.stable_ids import stable_storage_blob_id

        proof.assert_orm_module_loaded(aware_storage_ontology)
        expected_blob_id = stable_storage_blob_id(sha=normalized_sha)
        commit_expectation = OigCommitExpectation(
            label="StorageBlob.create",
            expected_domain_branch_id=branch_id,
            expected_domain_projection_hash=proof.projection_hash,
            expected_root_object_id=expected_blob_id,
        )
        function_proof = FunctionCallProof(
            function_key="StorageBlob.create",
            commit_expectation=commit_expectation,
        )
        behavior_proof = proof.behavior_proof(function_proof)
        assert behavior_proof.projection_name == "StorageBlob"
        assert behavior_proof.covered_functions == (function_proof,)

        with proof.activate(commit=True, publish=False):
            blob = await StorageBlob.create(
                sha=sha,
                mime_type=" ",
                size_bytes=12,
            )

        assert blob.id == expected_blob_id
        assert blob.sha == normalized_sha
        assert blob.mime_type == "application/octet-stream"
        assert blob.size_bytes == 12
        assert blob.object_key == f"{normalized_sha[:2]}/{normalized_sha[2:]}"

        response = proof.assert_last_function_response(function_proof)
        assert response.status == "succeeded"
        assert response.root_object_id == expected_blob_id
        assert response.payload is not None
        payload_value = (
            response.payload.get("value")
            if isinstance(response.payload, dict)
            else None
        )
        assert isinstance(payload_value, dict)
        assert payload_value["id"] == str(expected_blob_id)
        assert payload_value["sha"] == normalized_sha
        assert payload_value["mime_type"] == "application/octet-stream"
        assert payload_value["size_bytes"] == 12
        assert payload_value["object_key"] == (
            f"{normalized_sha[:2]}/{normalized_sha[2:]}"
        )

        head = await proof.get_head()
        assert head.status == "succeeded"
        assert head.domain_commit_id == response.domain_commit_id
        assert head.root_object_id == expected_blob_id

        commit = await proof.assert_last_function_commit(function_proof)

    assert commit.status == "succeeded"
    assert commit.root_object_id == expected_blob_id
    assert commit.graph_hash_post == response.graph_hash_post
    assert commit.commit is not None


def test_storage_workspace_local_native_proof_has_no_legacy_runtime_dependency() -> (
    None
):
    source = Path(__file__).read_text(encoding="utf-8")
    missing_receipts = missing_kernel_module_native_receipts(
        _STORAGE_MODULE_NAME,
        required_receipts=_STORAGE_REQUIRED_RECEIPTS,
    )
    if missing_receipts:
        pytest.skip(
            "Storage kernel native behavior proof requires generated Meta "
            "handler receipts from workspace materialization."
        )
    receipts = assert_kernel_module_native_function_impl_receipt(
        _STORAGE_MODULE_NAME,
        required_receipts=_STORAGE_REQUIRED_RECEIPTS,
    )
    generated_source = receipts.generated_meta_handlers_path.read_text(encoding="utf-8")

    forbidden_tokens = (
        "aware_" + "runtime",
        "Runtime" + "Harness",
        "FunctionCall" + "Invoker",
    )
    for forbidden in forbidden_tokens:
        assert forbidden not in source
        assert forbidden not in generated_source

    consumer_forbidden_tokens = (
        "aware_meta." + "runtime",
        "aware_meta_" + "service",
        "build_meta_graph_" + "runtime",
        "materialize_meta_" + "runtime",
        "handler_" + "modules",
        "bootstrap_" + "modules",
        "generated_language_" + "handler_module",
        "MetaGraph" + "Runtime",
    )
    for forbidden in consumer_forbidden_tokens:
        assert forbidden not in source
