from __future__ import annotations

import hashlib
from uuid import uuid4

import pytest

from aware_code.package.snapshot_artifact_payloads import (
    code_package_artifact_payload_bundle_satisfies_refs_at_commit,
    load_code_package_artifact_payloads_at_commit,
    write_code_package_artifact_payload_bundle,
)
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.package.code_package import CodePackage
from aware_code_ontology.package.code_package_artifact import CodePackageArtifactRef
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_types import JsonObject


def test_code_package_artifact_payload_bundle_replays_exact_committed_bytes(
    tmp_path,
) -> None:
    package_root = tmp_path / "modules" / "demo" / "python"
    artifact_path = package_root / "aware_demo" / "_aware" / "binding.msgpack"
    artifact_path.parent.mkdir(parents=True)
    content = b"\x82\xa5graph\x01\xa7version\x02"
    artifact_path.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    code_package = CodePackage(
        id=uuid4(),
        code_package_config_id=uuid4(),
        manifest_relative_path="modules/demo/python/pyproject.toml",
        package_name="aware-demo",
        package_root="modules/demo/python",
        sources_root="aware_demo",
        language=CodeLanguage.python,
    )
    artifact_ref = CodePackageArtifactRef(
        code_package_id=code_package.id,
        output_key="python.orm_graph_binding",
        artifact_key="demo-binding",
        required_for=["workspace_revision"],
        digest=digest,
        relative_path=("aware_demo/_aware/binding.msgpack"),
        receipt_payload=JsonObject(
            {
                "output_kind": "embedded_artifact",
                "path": artifact_path.as_posix(),
            }
        ),
    )
    store = FSCommitStore(root_dir=tmp_path)
    branch_id = uuid4()
    commit_id = uuid4()

    write_code_package_artifact_payload_bundle(
        store=store,
        branch_id=branch_id,
        projection_hash="code-package-projection",
        code_package=code_package,
        commit_id=commit_id,
        code_package_artifact_refs=(artifact_ref,),
    )
    artifact_path.unlink()

    replayed = load_code_package_artifact_payloads_at_commit(
        store=store,
        branch_id=branch_id,
        projection_hash="code-package-projection",
        code_package_id=code_package.id,
        commit_id=commit_id,
    )

    assert replayed == {"aware_demo/_aware/binding.msgpack": content}
    assert code_package_artifact_payload_bundle_satisfies_refs_at_commit(
        store=store,
        branch_id=branch_id,
        projection_hash="code-package-projection",
        code_package_id=code_package.id,
        commit_id=commit_id,
        code_package_artifact_refs=(artifact_ref,),
    )


def test_code_package_artifact_payload_bundle_missing_at_commit_is_incomplete(
    tmp_path,
) -> None:
    content = b"committed binding"
    code_package_id = uuid4()
    artifact_ref = CodePackageArtifactRef(
        code_package_id=code_package_id,
        output_key="python.orm_graph_binding",
        artifact_key="demo-binding",
        required_for=["workspace_revision"],
        digest=hashlib.sha256(content).hexdigest(),
        relative_path="aware_demo/_aware/binding.msgpack",
        receipt_payload=JsonObject({"output_kind": "embedded_artifact"}),
    )

    assert not code_package_artifact_payload_bundle_satisfies_refs_at_commit(
        store=FSCommitStore(root_dir=tmp_path),
        branch_id=uuid4(),
        projection_hash="code-package-projection",
        code_package_id=code_package_id,
        commit_id=uuid4(),
        code_package_artifact_refs=(artifact_ref,),
    )


def test_code_package_artifact_payload_bundle_rejects_digest_drift(tmp_path) -> None:
    package_root = tmp_path / "modules" / "demo" / "python"
    artifact_path = package_root / "aware_demo" / "_aware" / "binding.msgpack"
    artifact_path.parent.mkdir(parents=True)
    artifact_path.write_bytes(b"actual")
    code_package = CodePackage(
        id=uuid4(),
        code_package_config_id=uuid4(),
        manifest_relative_path="modules/demo/python/pyproject.toml",
        package_name="aware-demo",
        package_root="modules/demo/python",
        sources_root="aware_demo",
        language=CodeLanguage.python,
    )
    artifact_ref = CodePackageArtifactRef(
        code_package_id=code_package.id,
        output_key="python.orm_graph_binding",
        artifact_key="demo-binding",
        required_for=["workspace_revision"],
        digest=hashlib.sha256(b"expected").hexdigest(),
        relative_path="aware_demo/_aware/binding.msgpack",
        receipt_payload=JsonObject(
            {
                "output_kind": "embedded_artifact",
                "path": artifact_path.as_posix(),
            }
        ),
    )

    with pytest.raises(RuntimeError, match="payload digest mismatch"):
        write_code_package_artifact_payload_bundle(
            store=FSCommitStore(root_dir=tmp_path),
            branch_id=uuid4(),
            projection_hash="code-package-projection",
            code_package=code_package,
            commit_id=uuid4(),
            code_package_artifact_refs=(artifact_ref,),
        )


def test_code_package_artifact_payload_bundle_skips_non_embedded_evidence(
    tmp_path,
) -> None:
    code_package = CodePackage(
        id=uuid4(),
        code_package_config_id=uuid4(),
        manifest_relative_path="modules/demo/python/pyproject.toml",
        package_name="aware-demo",
        package_root="modules/demo/python",
        sources_root="aware_demo",
        language=CodeLanguage.python,
    )
    outside_package_path = tmp_path / ".aware" / "runtime-evidence.json"
    outside_package_path.parent.mkdir(parents=True)
    outside_package_path.write_text("{}", encoding="utf-8")
    artifact_ref = CodePackageArtifactRef(
        code_package_id=code_package.id,
        output_key="runtime.evidence",
        artifact_key="runtime-evidence",
        required_for=["workspace_revision"],
        digest=hashlib.sha256(b"{}").hexdigest(),
        relative_path=".aware/runtime-evidence.json",
        receipt_payload=JsonObject(
            {
                "output_kind": "file",
                "path": outside_package_path.as_posix(),
            }
        ),
    )
    store = FSCommitStore(root_dir=tmp_path)
    branch_id = uuid4()
    commit_id = uuid4()

    write_code_package_artifact_payload_bundle(
        store=store,
        branch_id=branch_id,
        projection_hash="code-package-projection",
        code_package=code_package,
        commit_id=commit_id,
        code_package_artifact_refs=(artifact_ref,),
    )

    assert (
        load_code_package_artifact_payloads_at_commit(
            store=store,
            branch_id=branch_id,
            projection_hash="code-package-projection",
            code_package_id=code_package.id,
            commit_id=commit_id,
        )
        == {}
    )
