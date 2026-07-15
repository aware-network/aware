from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest

from ._environment_runtime_test_paths import (
    ENVIRONMENT_RUNTIME_ROOT,
    REPO_ROOT,
)

for _path in (
    REPO_ROOT,
    ENVIRONMENT_RUNTIME_ROOT,
):
    _path_str = str(_path.resolve())
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)

from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex  # noqa: E402
from aware_environment.environment_config import (  # noqa: E402
    package_ref_resolution as env_refs,
)
from aware_environment.environment_config.package_ref_resolution import (  # noqa: E402
    EnvironmentRuntimePackageRef,
    resolve_committed_environment_runtime_package_ref,
    resolve_committed_projection_dto_artifact_bundle,
)
from aware_environment_ontology.environment.environment_config import (  # noqa: E402
    EnvironmentConfig,
)
from aware_environment_ontology.environment.environment_config_ontology_config import (  # noqa: E402
    EnvironmentConfigOntologyConfig,
)
from aware_environment_ontology.environment.environment_config_package import (  # noqa: E402
    EnvironmentConfigPackage,
)
from aware_environment_ontology.environment.environment_config_package_ontology_package import (  # noqa: E402
    EnvironmentConfigPackageOntologyPackage,
)

_PROJECTION_HASH_BY_NAME = {
    "EnvironmentConfigPackage": "sha256:environment_config_package",
    "EnvironmentConfig": "sha256:environment_config",
}


@pytest.mark.asyncio
async def test_committed_environment_package_ref_resolves_ontology_pointers_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    revision_root = tmp_path / "revision"
    environment_toml = revision_root / "aware.environment.toml"
    _write_revision_manifest(revision_root)
    monkeypatch.setenv("AWARE_ROOT", str(tmp_path / "aware-root"))

    branch_id = uuid4()
    environment_package_id = uuid4()
    environment_config_id = uuid4()
    environment_package_oig_commit_id = uuid4()
    environment_package_domain_commit_id = uuid4()
    environment_config_oig_commit_id = uuid4()
    environment_config_domain_commit_id = uuid4()
    ontology_config_id = uuid4()
    ontology_config_oig_commit_id = uuid4()
    ontology_package_id = uuid4()
    ontology_package_oig_commit_id = uuid4()

    environment_config = EnvironmentConfig.model_construct(
        id=environment_config_id,
        handle="kernel",
        ontology_configs=[
            EnvironmentConfigOntologyConfig.model_construct(
                id=uuid4(),
                environment_config_id=environment_config_id,
                name="demo-ontology",
                fqn_prefix="aware_demo",
                ontology_config_id=ontology_config_id,
                ontology_config_object_instance_graph_commit_id=(
                    ontology_config_oig_commit_id
                ),
            )
        ],
    )
    environment_package = EnvironmentConfigPackage.model_construct(
        id=environment_package_id,
        handle="kernel",
        environment_config_id=environment_config_id,
        environment_config_object_instance_graph_commit_id=(
            environment_config_oig_commit_id
        ),
        ontology_packages=[
            EnvironmentConfigPackageOntologyPackage.model_construct(
                id=uuid4(),
                environment_config_package_id=environment_package_id,
                name="demo-ontology",
                fqn_prefix="aware_demo",
                ontology_package_id=ontology_package_id,
                ontology_package_object_instance_graph_commit_id=(
                    ontology_package_oig_commit_id
                ),
            )
        ],
    )
    package_ref = EnvironmentRuntimePackageRef(
        family_key="environment",
        package_kind="environment",
        package_name="kernel",
        manifest_path="aware.environment.toml",
        semantic_package_id=str(environment_package_id),
        semantic_object_instance_graph_commit_id=str(environment_package_oig_commit_id),
        semantic_root_kind="environment_config",
        semantic_root_id=str(environment_config_id),
        semantic_root_object_instance_graph_commit_id=(
            str(environment_config_oig_commit_id)
        ),
    )
    index = _runtime_index()

    async def _fake_find_domain_commit_ref_for_oig_commit_id(
        **kwargs: Any,
    ) -> env_refs._DomainCommitRef | None:
        if kwargs["projection_hash"] == "sha256:environment_config_package":
            assert (
                kwargs["object_instance_graph_commit_id"]
                == environment_package_oig_commit_id
            )
            return env_refs._DomainCommitRef(
                branch_id=branch_id,
                projection_hash=kwargs["projection_hash"],
                domain_commit_id=environment_package_domain_commit_id,
            )
        assert kwargs["projection_hash"] == "sha256:environment_config"
        assert (
            kwargs["object_instance_graph_commit_id"]
            == environment_config_oig_commit_id
        )
        return env_refs._DomainCommitRef(
            branch_id=branch_id,
            projection_hash=kwargs["projection_hash"],
            domain_commit_id=environment_config_domain_commit_id,
        )

    async def _fake_hydrate_root_from_commit(**kwargs: Any) -> object:
        if kwargs["root_type"] is EnvironmentConfigPackage:
            assert kwargs["commit_id"] == environment_package_domain_commit_id
            return environment_package
        assert kwargs["root_type"] is EnvironmentConfig
        assert kwargs["commit_id"] == environment_config_domain_commit_id
        return environment_config

    monkeypatch.setattr(
        "aware_environment.environment_config.package_ref_resolution._find_domain_commit_ref_for_oig_commit_id",
        _fake_find_domain_commit_ref_for_oig_commit_id,
    )
    monkeypatch.setattr(
        "aware_environment.environment_config.package_ref_resolution._hydrate_root_from_commit",
        _fake_hydrate_root_from_commit,
    )

    resolved = await resolve_committed_environment_runtime_package_ref(
        index=index,
        package_ref=package_ref,
        materialized_workspace_root=revision_root,
        meta_projection_catalog={"projection_hash_by_name": _PROJECTION_HASH_BY_NAME},
    )

    assert resolved.environment_package_id == environment_package_id
    assert resolved.environment_config_id == environment_config_id
    assert resolved.manifest_path == environment_toml.resolve()
    assert resolved.environment_package is environment_package
    assert resolved.environment_config is environment_config
    assert len(resolved.ontology_pointers) == 1
    pointer = resolved.ontology_pointers[0]
    assert pointer.name == "demo-ontology"
    assert pointer.fqn_prefix == "aware_demo"
    assert pointer.ontology_config_ref.ontology_config_id == ontology_config_id
    assert (
        pointer.ontology_config_ref.ontology_config_object_instance_graph_commit_id
        == ontology_config_oig_commit_id
    )
    assert pointer.ontology_package_ref.ontology_package_id == ontology_package_id
    assert (
        pointer.ontology_package_ref.ontology_package_object_instance_graph_commit_id
        == ontology_package_oig_commit_id
    )
    assert not hasattr(resolved, "object_config_graph_packages")


@pytest.mark.asyncio
async def test_committed_environment_package_ref_rejects_membership_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    revision_root = tmp_path / "revision"
    _write_revision_manifest(revision_root)
    monkeypatch.setenv("AWARE_ROOT", str(tmp_path / "aware-root"))

    branch_id = uuid4()
    environment_package_id = uuid4()
    environment_config_id = uuid4()
    environment_package_oig_commit_id = uuid4()
    environment_config_oig_commit_id = uuid4()
    environment_config = EnvironmentConfig.model_construct(
        id=environment_config_id,
        handle="kernel",
        ontology_configs=[
            EnvironmentConfigOntologyConfig.model_construct(
                id=uuid4(),
                environment_config_id=environment_config_id,
                name="demo-ontology",
                fqn_prefix="aware_demo",
                ontology_config_id=uuid4(),
                ontology_config_object_instance_graph_commit_id=uuid4(),
            )
        ],
    )
    environment_package = EnvironmentConfigPackage.model_construct(
        id=environment_package_id,
        handle="kernel",
        environment_config_id=environment_config_id,
        environment_config_object_instance_graph_commit_id=(
            environment_config_oig_commit_id
        ),
        ontology_packages=[],
    )

    async def _fake_find_domain_commit_ref_for_oig_commit_id(
        **kwargs: Any,
    ) -> env_refs._DomainCommitRef | None:
        return env_refs._DomainCommitRef(
            branch_id=branch_id,
            projection_hash=kwargs["projection_hash"],
            domain_commit_id=uuid4(),
        )

    async def _fake_hydrate_root_from_commit(**kwargs: Any) -> object:
        if kwargs["root_type"] is EnvironmentConfigPackage:
            return environment_package
        return environment_config

    monkeypatch.setattr(
        "aware_environment.environment_config.package_ref_resolution._find_domain_commit_ref_for_oig_commit_id",
        _fake_find_domain_commit_ref_for_oig_commit_id,
    )
    monkeypatch.setattr(
        "aware_environment.environment_config.package_ref_resolution._hydrate_root_from_commit",
        _fake_hydrate_root_from_commit,
    )

    with pytest.raises(RuntimeError, match="ontology memberships do not match"):
        await resolve_committed_environment_runtime_package_ref(
            index=_runtime_index(),
            package_ref=EnvironmentRuntimePackageRef(
                family_key="environment",
                package_kind="environment",
                package_name="kernel",
                semantic_package_id=str(environment_package_id),
                semantic_object_instance_graph_commit_id=(
                    str(environment_package_oig_commit_id)
                ),
            ),
            materialized_workspace_root=revision_root,
            meta_projection_catalog={
                "projection_hash_by_name": _PROJECTION_HASH_BY_NAME
            },
        )


def test_committed_projection_dto_artifact_bundle_resolves_revision_artifacts(
    tmp_path: Path,
) -> None:
    revision_root = tmp_path / "revision"
    _write_revision_manifest(revision_root)
    artifact_path = (
        revision_root
        / "modules"
        / "demo"
        / "ontology"
        / "ontology"
        / "python"
        / "aware_demo"
        / "_aware"
        / "python.bootstrap.json"
    )
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_payload = b'{"modules":["aware_demo"]}\n'
    artifact_path.write_bytes(artifact_payload)
    artifact_digest = sha256(artifact_payload).hexdigest()

    bundle = resolve_committed_projection_dto_artifact_bundle(
        artifact_refs=(
            SimpleNamespace(
                artifact_family="ocg_language_materialization",
                artifact_key="python:package_bootstrap:aware_demo",
                artifact_role="package_bootstrap",
                required_for=("committed_projection_dto",),
                status="available",
                package_name="aware_demo",
                workspace_relative_path=artifact_path.relative_to(
                    revision_root
                ).as_posix(),
                digest=f"sha256:{artifact_digest}",
                media_type="application/json",
            ),
        ),
        materialized_workspace_root=revision_root,
        dto_import_root="aware_demo",
    )

    assert bundle.artifact_count == 1
    assert bundle.artifacts[0].path == artifact_path.resolve()
    assert bundle.artifacts[0].sha256 == artifact_digest
    assert bundle.missing_requirements == ("dependency_import_resolution",)


def _runtime_index() -> MetaGraphRuntimeIndex:
    return cast(
        MetaGraphRuntimeIndex,
        cast(
            object,
            SimpleNamespace(
                opg_by_hash={},
                ocg=object(),
                attribute_configs_by_id={},
                class_configs_by_id={},
            ),
        ),
    )


def _write_revision_manifest(revision_root: Path) -> None:
    manifest_path = (
        revision_root / ".aware" / "workspace" / "revision-filesystem.manifest.json"
    )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text('{"artifact_files":[]}\n', encoding="utf-8")
