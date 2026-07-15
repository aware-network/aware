from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

import pytest

from aware_hub.handlers._generated import meta_handlers as hub_meta_handlers
from aware_meta.runtime import (
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
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


HUB_AUTHORITY_CLASS_FQN = "aware_hub.hub.HubAuthority"
_REPO_ROOT = Path(__file__).resolve().parents[8]

_HUB_META_HANDLERS_ANY: Any = hub_meta_handlers
_HUB_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _HUB_META_HANDLERS_ANY,
)
_HUB_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _HUB_META_HANDLERS_ANY,
)


def _hub_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    return (
        repo_root
        / "workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/code/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/hub/ontology/structure/aware.toml",
    )


def _build_hub_meta_runtime(*, repo_root: Path, aware_root: Path) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_hub_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(_HUB_META_HANDLER_MODULE,),
        bootstrap_modules=(_HUB_META_BOOTSTRAP_MODULE,),
    )
    assert runtime.context is not None
    return runtime


@pytest.mark.asyncio
async def test_hub_code_package_publication_authority_module_proof(
    tmp_path: Path,
) -> None:
    repo_root = _REPO_ROOT

    import aware_hub_ontology  # noqa: F401
    from aware_code.stable_ids import stable_code_package_id
    from aware_hub_ontology.stable_ids import (
        stable_hub_artifact_id,
        stable_hub_artifact_revision_id,
        stable_hub_authority_id,
        stable_hub_channel_head_id,
        stable_hub_channel_id,
        stable_hub_code_package_publication_id,
        stable_hub_producer_provenance_id,
        stable_hub_publication_receipt_id,
    )

    authority_key = "default"
    package_name = "aware-hub-service-api"
    language = "python"
    surface = "service"
    channel_key = "stable"
    revision_id = "rev-2026-05-08"
    artifact_url = (
        "https://hub.local/artifacts/aware-hub-service-api/rev-2026-05-08.tar.zst"
    )
    artifact_sha256 = "0" * 64
    producer_key = "workspace:kernel"
    producer_revision_id = "workspace-rev-2026-05-08"

    code_package_id = stable_code_package_id(
        package_name=package_name, language=language
    )
    authority_id = stable_hub_authority_id(authority_key=authority_key)
    artifact_family = "code-package"
    artifact_key = f"{language}:{surface}:{package_name}"
    artifact_id = stable_hub_artifact_id(
        hub_authority_id=authority_id,
        artifact_family=artifact_family,
        artifact_key=artifact_key,
    )
    artifact_revision_id = stable_hub_artifact_revision_id(
        hub_artifact_id=artifact_id,
        revision_id=revision_id,
    )
    channel_id = stable_hub_channel_id(
        hub_authority_id=authority_id, channel_key=channel_key
    )
    channel_head_id = stable_hub_channel_head_id(
        hub_channel_id=channel_id,
        artifact_family=artifact_family,
        artifact_key=artifact_key,
    )
    publication_id = stable_hub_code_package_publication_id(
        hub_authority_id=authority_id,
        channel_key=channel_key,
        language=language,
        package_name=package_name,
        revision_id=revision_id,
        surface=surface,
    )
    provenance_id = stable_hub_producer_provenance_id(
        producer_kind="workspace",
        producer_key=producer_key,
        provenance_key=producer_revision_id,
    )
    receipt_key = f"publish_code_package:{artifact_family}:{artifact_key}:{revision_id}"
    receipt_id = stable_hub_publication_receipt_id(
        hub_authority_id=authority_id,
        receipt_key=receipt_key,
    )

    lane = LaneIds(branch_id=uuid5(NAMESPACE_URL, "aware://tests/hub/lane"))

    with IsolatedAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_hub_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        context = runtime.context
        assert context is not None
        idx = context.index
        opg_names = {(opg.name or "").strip() for opg in idx.opg_by_hash.values()}
        assert "CodePackage" in opg_names
        assert "HubCodePackageAuthority" in opg_names
        assert "HubChannelHeads" in opg_names

        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="HubCodePackageAuthority",
            root_class_fqn=HUB_AUTHORITY_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=HUB_AUTHORITY_CLASS_FQN,
                    function_name="ensure_authority",
                    kwargs={"authority_key": authority_key, "title": "Aware Hub"},
                    expected_root_object_id=authority_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=HUB_AUTHORITY_CLASS_FQN,
                    function_name="publish_code_package",
                    object_id=SourceObjectId(authority_id),
                    kwargs={
                        "package_name": package_name,
                        "language": language,
                        "surface": surface,
                        "revision_id": revision_id,
                        "artifact_url": artifact_url,
                        "artifact_sha256": artifact_sha256,
                        "channel_key": channel_key,
                        "code_package_id": code_package_id,
                        "artifact_size_bytes": 4096,
                        "media_type": "application/zstd",
                        "manifest_kind": "pyproject_toml",
                        "manifest_relative_path": "pyproject.toml",
                        "package_root": (
                            "workspaces/aware_network/modules/hub/services/hub"
                        ),
                        "sources_root": (
                            "workspaces/aware_network/modules/hub/services/hub/"
                            "aware_hub_service"
                        ),
                        "fqn_prefix": "aware_hub_service",
                        "producer_kind": "workspace",
                        "producer_key": producer_key,
                        "provenance_key": producer_revision_id,
                        "producer_revision_id": producer_revision_id,
                        "source_revision_kind": "workspace_revision",
                        "source_revision_id": producer_revision_id,
                        "published_at_utc": "2026-05-08T00:00:00Z",
                    },
                ),
            ],
        )

        source_to_ci_id = {
            class_instance.source_object_id: class_instance.id
            for class_instance in assertions.oig.class_instances
            if class_instance.source_object_id is not None
            and class_instance.id is not None
        }

        authority_ci_id = source_to_ci_id[authority_id]
        artifact_ci_id = source_to_ci_id[artifact_id]
        revision_ci_id = source_to_ci_id[artifact_revision_id]
        channel_ci_id = source_to_ci_id[channel_id]
        channel_head_ci_id = source_to_ci_id[channel_head_id]
        publication_ci_id = source_to_ci_id[publication_id]
        provenance_ci_id = source_to_ci_id[provenance_id]
        receipt_ci_id = source_to_ci_id[receipt_id]

        assert result.root_object_id == authority_id
        assertions.expect_root(authority_ci_id)
        assertions.expect_primitive(
            instance_id=authority_ci_id,
            field_name="authority_key",
            expected=authority_key,
        )
        assertions.expect_primitive(
            instance_id=publication_ci_id,
            field_name="package_name",
            expected=package_name,
        )
        assertions.expect_primitive(
            instance_id=publication_ci_id,
            field_name="revision_id",
            expected=revision_id,
        )
        assertions.expect_primitive(
            instance_id=publication_ci_id,
            field_name="artifact_url",
            expected=artifact_url,
        )
        code_package_primitive = assertions.primitive(
            instance_id=publication_ci_id,
            field_name="code_package_id",
        )
        assert code_package_primitive in {code_package_id, str(code_package_id)}
        assertions.expect_primitive(
            instance_id=revision_ci_id,
            field_name="payload_sha256",
            expected=artifact_sha256,
        )
        assertions.expect_primitive(
            instance_id=channel_head_ci_id,
            field_name="revision_id",
            expected=revision_id,
        )
        assertions.expect_primitive(
            instance_id=provenance_ci_id,
            field_name="producer_revision_id",
            expected=producer_revision_id,
        )
        assertions.expect_primitive(
            instance_id=receipt_ci_id,
            field_name="operation",
            expected="publish_code_package",
        )
        assertions.expect_edge(
            source_id=authority_ci_id,
            target_id=artifact_ci_id,
            relationship_name="artifacts",
        )
        assertions.expect_edge(
            source_id=authority_ci_id,
            target_id=channel_ci_id,
            relationship_name="channels",
        )
        assertions.expect_edge(
            source_id=authority_ci_id,
            target_id=publication_ci_id,
            relationship_name="code_package_publications",
        )
        assertions.expect_edge(
            source_id=authority_ci_id,
            target_id=receipt_ci_id,
            relationship_name="receipts",
        )
        assertions.expect_edge(
            source_id=artifact_ci_id,
            target_id=revision_ci_id,
            relationship_name="revisions",
        )
        assertions.expect_edge(
            source_id=channel_ci_id,
            target_id=channel_head_ci_id,
            relationship_name="heads",
        )
        assertions.expect_edge(
            source_id=channel_head_ci_id,
            target_id=revision_ci_id,
            relationship_name="artifact_revision",
        )
        assertions.expect_edge(
            source_id=channel_head_ci_id,
            target_id=publication_ci_id,
            relationship_name="code_package_publication",
        )
        assertions.expect_edge(
            source_id=publication_ci_id,
            target_id=revision_ci_id,
            relationship_name="artifact_revision",
        )
        assertions.expect_edge(
            source_id=publication_ci_id,
            target_id=provenance_ci_id,
            relationship_name="producer_provenance",
        )
