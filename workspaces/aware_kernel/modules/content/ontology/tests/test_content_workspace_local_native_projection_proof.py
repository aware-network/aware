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

_CONTENT_MODULE_NAME = "content"
_CONTENT_REQUIRED_RECEIPTS = (
    "structure/python/orm_runtime/aware_content_ontology/content/content.py",
    "structure/python/orm_runtime/aware_content_ontology/content/content_enums.py",
    "structure/python/orm_runtime/aware_content_ontology/stable_ids.py",
)


@pytest.mark.asyncio
async def test_content_workspace_local_native_content_projection_proof(
    tmp_path: Path,
) -> None:
    missing_receipts = missing_kernel_module_native_receipts(
        _CONTENT_MODULE_NAME,
        required_receipts=_CONTENT_REQUIRED_RECEIPTS,
    )
    if missing_receipts:
        pytest.skip(
            "Content kernel native projection proof requires workspace "
            "materialization receipts. Run `aware-cli workspace materialize "
            "--repo-root workspaces/aware_kernel --workspace-toml "
            "aware.workspace.toml --kernel-repo-root . --package "
            "content-ontology --execute-heavy-semantic-materialization` first. "
            "Missing: " + ", ".join(path.as_posix() for path in missing_receipts)
        )

    branch_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/kernel/content/meta-runtime/branch",
    )
    actor_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/kernel/content/meta-runtime/actor",
    )

    with kernel_module_native_behavior_proof(
        module_name=_CONTENT_MODULE_NAME,
        projection="Content",
        aware_root_path=tmp_path / "aware_root",
        actor_id=actor_id,
        branch_id=branch_id,
        composite_name="Aware Kernel Content Local Meta SDK Projection Proof",
        required_receipts=_CONTENT_REQUIRED_RECEIPTS,
    ) as proof:
        import aware_content_ontology
        from aware_content_ontology.content.content import Content
        from aware_content_ontology.content.content_enums import ContentSource
        from aware_content_ontology.stable_ids import stable_content_id

        proof.assert_orm_module_loaded(aware_content_ontology)
        content_key = "kernel-content-native-proof"
        expected_content_id = stable_content_id(key=content_key)
        commit_expectation = OigCommitExpectation(
            label="Content.create_content",
            expected_domain_branch_id=branch_id,
            expected_domain_projection_hash=proof.projection_hash,
            expected_root_object_id=expected_content_id,
        )
        function_proof = FunctionCallProof(
            function_key="Content.create_content",
            commit_expectation=commit_expectation,
        )
        behavior_proof = proof.behavior_proof(function_proof)
        assert behavior_proof.projection_name == "Content"
        assert behavior_proof.covered_functions == (function_proof,)

        with proof.activate(commit=True, publish=False):
            content = await Content.create_content(
                key=content_key,
                title="Kernel Content Native Proof",
                source=ContentSource.user,
                seed_inline_text="Content projection proof",
                seed_part_position=0,
            )

        assert content.id == expected_content_id
        assert content.key == content_key
        assert content.title == "Kernel Content Native Proof"
        assert content.source == ContentSource.user

        response = proof.assert_last_function_response(function_proof)
        assert response.status == "succeeded"
        assert response.root_object_id == expected_content_id
        assert response.payload is not None
        payload_value = (
            response.payload.get("value")
            if isinstance(response.payload, dict)
            else None
        )
        assert isinstance(payload_value, dict)
        assert payload_value["id"] == str(expected_content_id)
        assert payload_value["key"] == content_key
        assert payload_value["title"] == "Kernel Content Native Proof"
        assert payload_value["source"] == ContentSource.user.value

        head = await proof.get_head()
        assert head.status == "succeeded"
        assert head.domain_commit_id == response.domain_commit_id
        assert head.root_object_id == expected_content_id

        commit = await proof.assert_last_function_commit(function_proof)

    assert commit.status == "succeeded"
    assert commit.root_object_id == expected_content_id
    assert commit.graph_hash_post == response.graph_hash_post
    assert commit.commit is not None


def test_content_workspace_local_native_projection_proof_has_no_legacy_runtime_dependency() -> (
    None
):
    source = Path(__file__).read_text(encoding="utf-8")
    missing_receipts = missing_kernel_module_native_receipts(
        _CONTENT_MODULE_NAME,
        required_receipts=_CONTENT_REQUIRED_RECEIPTS,
    )
    if missing_receipts:
        pytest.skip(
            "Content kernel native projection proof requires generated Meta "
            "handler receipts from workspace materialization."
        )
    receipts = assert_kernel_module_native_function_impl_receipt(
        _CONTENT_MODULE_NAME,
        required_receipts=_CONTENT_REQUIRED_RECEIPTS,
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
