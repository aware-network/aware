from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from aware_service_runtime.package_ref_resolution import (
    ServiceRuntimePackageRef,
    resolve_committed_service_runtime_package_ref,
    resolve_service_runtime_package_ref,
    resolve_service_runtime_package_refs,
)
from aware_meta.graph.instance.commit.contract import ObjectInstanceGraphCommitRef
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_api_ontology.api.api_package import ApiPackage
from aware_api_ontology.api.api_package_language_package import (
    ApiPackageLanguagePackage,
)
from aware_service_ontology.service.service_config import ServiceConfig
from aware_service_ontology.service.service_package import ServicePackage
from aware_service_ontology.service.service_package_provided_api_package import (
    ServicePackageProvidedApiPackage,
)


def _fake_projection_hash_token(projection_name: str) -> str:
    return {
        "ServicePackage": "service_package",
        "ServiceConfig": "service_config",
    }.get(projection_name, projection_name)


def test_service_runtime_package_ref_resolves_revision_local_manifest(
    tmp_path: Path,
) -> None:
    revision_root = tmp_path / "revision"
    service_toml = revision_root / "services" / "proof" / "aware.service.toml"
    _write_revision_manifest(revision_root)
    _write_service_toml(service_toml)

    package_ref = ServiceRuntimePackageRef(
        family_key="service",
        package_kind="service",
        package_name="proof-service",
        manifest_path="services/proof/aware.service.toml",
        workspace_package_id="workspace-service-package-proof",
        semantic_package_id="service-package-proof",
        semantic_object_instance_graph_commit_id="service-package-oig-commit-proof",
        semantic_head_commit_id="service-package-head-proof",
        semantic_branch_id="service-package-branch-proof",
        semantic_root_kind="service_package",
        semantic_root_id="service-package-proof-root",
        semantic_root_object_instance_graph_commit_id=(
            "service-config-oig-commit-proof"
        ),
        source_code_package_id="code-package-proof-service",
    )

    resolved = resolve_service_runtime_package_ref(
        package_ref=package_ref,
        materialized_workspace_root=revision_root,
    )

    assert resolved.package_ref == package_ref
    assert resolved.materialized_workspace_root == revision_root.resolve()
    assert resolved.manifest_path == service_toml.resolve()
    assert resolved.manifest_relative_path == "services/proof/aware.service.toml"
    assert resolved.package_name == "proof-service"
    assert resolved.fqn_prefix == "proof_service"
    assert resolved.toml_paths == (service_toml.resolve(),)
    assert resolved.workspace_package_id == "workspace-service-package-proof"
    assert resolved.semantic_package_id == "service-package-proof"
    assert (
        resolved.semantic_object_instance_graph_commit_id
        == "service-package-oig-commit-proof"
    )
    assert resolved.semantic_head_commit_id == "service-package-head-proof"
    assert resolved.semantic_branch_id == "service-package-branch-proof"
    assert resolved.semantic_root_kind == "service_package"
    assert resolved.semantic_root_id == "service-package-proof-root"
    assert (
        resolved.semantic_root_object_instance_graph_commit_id
        == "service-config-oig-commit-proof"
    )
    assert resolved.source_code_package_id == "code-package-proof-service"
    assert resolved.dependency_payloads == (
        {
            "package_name": "proof-service-api",
            "kind": "api_service_protocol",
        },
    )


@pytest.mark.asyncio
async def test_committed_service_runtime_package_ref_hydrates_package_and_service_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    revision_root = tmp_path / "revision"
    dependency_revision_root = tmp_path / "dependency-revision"
    _write_revision_manifest(revision_root)
    _write_revision_manifest(dependency_revision_root)

    branch_id = uuid4()
    package_id = uuid4()
    service_config_id = uuid4()
    package_oig_commit_id = uuid4()
    legacy_head_commit_id = uuid4()
    package_domain_commit_id = uuid4()
    service_config_oig_commit_id = uuid4()
    service_config_domain_commit_id = uuid4()
    source_code_package_id = uuid4()
    api_package_id = uuid4()
    protocol_package_id = uuid4()
    protocol_code_package_id = uuid4()
    protocol_code_package_commit_id = uuid4()
    api_package_commit_id = uuid4()
    protocol_lock_id = uuid4()

    service_config_commit = ObjectInstanceGraphCommit.model_construct(
        id=service_config_oig_commit_id,
        commit_id=service_config_domain_commit_id,
    )
    service_config = ServiceConfig.model_construct(
        id=service_config_id,
        name="proof-service",
    )
    api_package = ApiPackage.model_construct(
        id=api_package_id,
        name="proof-service-api",
        version_number=7,
        language_packages=[],
    )
    protocol_package = ApiPackageLanguagePackage.model_construct(
        id=protocol_package_id,
        api_package_id=api_package_id,
        code_package_id=protocol_code_package_id,
        output_key="python.service_protocol_package",
        object_instance_graph_commit_id=protocol_code_package_commit_id,
    )
    api_package.language_packages.append(protocol_package)
    protocol_lock = ServicePackageProvidedApiPackage.model_construct(
        id=protocol_lock_id,
        api_package_id=api_package_id,
        api_package=None,
        api_package_object_instance_graph_commit_id=api_package_commit_id,
        service_protocol_package_id=protocol_package_id,
        service_protocol_package=None,
        service_protocol_plan_hash_sha256="a" * 64,
    )
    service_package = ServicePackage.model_construct(
        id=package_id,
        name="proof-service",
        service_config_id=service_config_id,
        service_config=service_config,
        service_config_object_instance_graph_commit_id=service_config_oig_commit_id,
        service_config_object_instance_graph_commit=service_config_commit,
        source_code_package_id=source_code_package_id,
        manifest_relative_path="services/proof/aware.service.toml",
        fqn_prefix="proof_service_from_package",
        dependencies=[],
        provided_api_packages=[protocol_lock],
    )
    package_ref = ServiceRuntimePackageRef(
        family_key="service",
        package_kind="service",
        package_name="proof-service",
        semantic_package_id=str(package_id),
        semantic_object_instance_graph_commit_id=str(package_oig_commit_id),
        semantic_head_commit_id=str(legacy_head_commit_id),
        semantic_branch_id=str(branch_id),
        semantic_root_kind="service_config",
        semantic_root_id=str(service_config_id),
        semantic_root_object_instance_graph_commit_id=str(service_config_oig_commit_id),
    )
    index = cast(
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

    def _fake_projection_hash(
        *, index: MetaGraphRuntimeIndex, projection_name: str
    ) -> str:
        del index
        return f"sha256:{_fake_projection_hash_token(projection_name)}"

    async def _fake_domain_commit_id_for_oig_commit_id(
        self: object,
        **kwargs: Any,
    ) -> UUID:
        del self
        assert kwargs["branch_id"] == branch_id
        assert kwargs["projection_hash"] == "sha256:service_package"
        assert kwargs["object_instance_graph_commit_id"] == package_oig_commit_id
        return package_domain_commit_id

    async def _fake_hydrate_root_from_commit(**kwargs: Any) -> object:
        if kwargs["root_type"] is ServicePackage:
            assert kwargs["projection_hash"] == "sha256:service_package"
            assert kwargs["commit_id"] == package_domain_commit_id
            assert kwargs["root_id"] == package_id
            return service_package
        if kwargs["root_type"] is ApiPackage:
            assert kwargs["projection_hash"] == "sha256:ApiPackage"
            assert kwargs["commit_id"] == api_package_domain_commit_id
            assert kwargs["root_id"] == api_package_id
            return api_package
        assert kwargs["root_type"] is ServiceConfig
        assert kwargs["projection_hash"] == "sha256:service_config"
        assert kwargs["commit_id"] == service_config_domain_commit_id
        assert kwargs["root_id"] == service_config_id
        return service_config

    api_package_domain_commit_id = uuid4()

    async def _fake_domain_commit_refs_for_oig_commit_id(
        self: object,
        **kwargs: Any,
    ) -> tuple[ObjectInstanceGraphCommitRef, ...]:
        assert kwargs["projection_hash"] == "sha256:ApiPackage"
        assert kwargs["object_instance_graph_commit_id"] == api_package_commit_id
        if getattr(self, "aware_root") == revision_root:
            return ()
        assert getattr(self, "aware_root") == dependency_revision_root
        return (
            ObjectInstanceGraphCommitRef(
                branch_id=uuid4(),
                projection_hash="sha256:ApiPackage",
                object_instance_graph_commit_id=api_package_commit_id,
                domain_commit_id=api_package_domain_commit_id,
            ),
        )

    def _raise_if_toml_loaded(*args: Any, **kwargs: Any) -> object:
        raise AssertionError(
            "committed package ref resolution must not load aware.service.toml"
        )

    monkeypatch.setattr(
        "aware_service_runtime.package_ref_resolution._find_projection_hash_by_name",
        _fake_projection_hash,
    )
    monkeypatch.setattr(
        "aware_service_runtime.package_ref_resolution.FSCommitStore."
        "domain_commit_id_for_object_instance_graph_commit_id",
        _fake_domain_commit_id_for_oig_commit_id,
    )
    monkeypatch.setattr(
        "aware_service_runtime.package_ref_resolution.FSCommitStore."
        "domain_commit_refs_for_object_instance_graph_commit_id",
        _fake_domain_commit_refs_for_oig_commit_id,
    )
    monkeypatch.setattr(
        "aware_service_runtime.package_ref_resolution._hydrate_root_from_commit",
        _fake_hydrate_root_from_commit,
    )
    monkeypatch.setattr(
        "aware_service_runtime.package_ref_resolution.load_aware_service_toml_spec",
        _raise_if_toml_loaded,
    )

    resolved = await resolve_committed_service_runtime_package_ref(
        index=index,
        package_ref=package_ref,
        materialized_workspace_root=revision_root,
        dependency_workspace_roots=(dependency_revision_root,),
    )

    assert resolved.service_package_id == package_id
    assert resolved.service_config_id == service_config_id
    assert (
        resolved.service_config_object_instance_graph_commit_id
        == service_config_oig_commit_id
    )
    assert resolved.manifest_path is None
    assert resolved.manifest_relative_path == "services/proof/aware.service.toml"
    assert resolved.toml_paths == ()
    assert resolved.service_package is service_package
    assert resolved.service_config is service_config
    assert resolved.dependency_payloads == (
        {
            "package_name": "proof-service-api",
            "kind": "api_service_protocol",
            "version_number": 7,
            "service_package_provided_api_package_id": str(protocol_lock_id),
            "api_package_id": str(api_package_id),
            "api_package_object_instance_graph_commit_id": str(api_package_commit_id),
            "service_protocol_package_id": str(protocol_package_id),
            "service_protocol_code_package_id": str(protocol_code_package_id),
            "service_protocol_code_package_object_instance_graph_commit_id": str(
                protocol_code_package_commit_id
            ),
            "service_protocol_plan_hash_sha256": "a" * 64,
        },
    )
    assert resolved.package_name == "proof-service"
    assert resolved.fqn_prefix == "proof_service_from_package"
    assert resolved.semantic_package_id == str(package_id)
    assert resolved.semantic_object_instance_graph_commit_id == str(
        package_oig_commit_id
    )
    assert resolved.semantic_head_commit_id == str(legacy_head_commit_id)
    assert resolved.semantic_root_object_instance_graph_commit_id == str(
        service_config_oig_commit_id
    )
    assert resolved.source_code_package_id == str(source_code_package_id)


@pytest.mark.asyncio
async def test_committed_service_runtime_package_ref_resolves_branch_from_oig_pin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    revision_root = tmp_path / "revision"
    _write_revision_manifest(revision_root)

    branch_id = uuid4()
    package_id = uuid4()
    service_config_id = uuid4()
    package_oig_commit_id = uuid4()
    package_domain_commit_id = uuid4()
    service_config_oig_commit_id = uuid4()
    service_config_domain_commit_id = uuid4()

    service_config_commit = ObjectInstanceGraphCommit.model_construct(
        id=service_config_oig_commit_id,
        commit_id=service_config_domain_commit_id,
    )
    service_config = ServiceConfig.model_construct(
        id=service_config_id,
        name="proof-service",
    )
    service_package = ServicePackage.model_construct(
        id=package_id,
        name="proof-service",
        service_config_id=service_config_id,
        service_config=service_config,
        service_config_object_instance_graph_commit_id=service_config_oig_commit_id,
        service_config_object_instance_graph_commit=service_config_commit,
        manifest_relative_path="services/proof/aware.service.toml",
        fqn_prefix="proof_service_from_package",
        dependencies=[],
    )
    package_ref = ServiceRuntimePackageRef(
        family_key="service",
        package_kind="service",
        package_name="proof-service",
        semantic_package_id=str(package_id),
        semantic_object_instance_graph_commit_id=str(package_oig_commit_id),
        semantic_root_kind="service_config",
        semantic_root_id=str(service_config_id),
        semantic_root_object_instance_graph_commit_id=str(service_config_oig_commit_id),
    )
    index = cast(
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

    def _fake_projection_hash(
        *, index: MetaGraphRuntimeIndex, projection_name: str
    ) -> str:
        del index
        return f"sha256:{_fake_projection_hash_token(projection_name)}"

    async def _fake_domain_commit_refs_for_oig_commit_id(
        self: object,
        **kwargs: Any,
    ) -> tuple[ObjectInstanceGraphCommitRef, ...]:
        del self
        assert kwargs["projection_hash"] == "sha256:service_package"
        assert kwargs["object_instance_graph_commit_id"] == package_oig_commit_id
        return (
            ObjectInstanceGraphCommitRef(
                branch_id=branch_id,
                projection_hash="sha256:service_package",
                object_instance_graph_commit_id=package_oig_commit_id,
                domain_commit_id=package_domain_commit_id,
            ),
        )

    async def _fake_hydrate_root_from_commit(**kwargs: Any) -> object:
        assert kwargs["branch_id"] == branch_id
        if kwargs["root_type"] is ServicePackage:
            assert kwargs["projection_hash"] == "sha256:service_package"
            assert kwargs["commit_id"] == package_domain_commit_id
            assert kwargs["root_id"] == package_id
            return service_package
        assert kwargs["root_type"] is ServiceConfig
        assert kwargs["projection_hash"] == "sha256:service_config"
        assert kwargs["commit_id"] == service_config_domain_commit_id
        assert kwargs["root_id"] == service_config_id
        return service_config

    monkeypatch.setattr(
        "aware_service_runtime.package_ref_resolution._find_projection_hash_by_name",
        _fake_projection_hash,
    )
    monkeypatch.setattr(
        "aware_service_runtime.package_ref_resolution.FSCommitStore."
        "domain_commit_refs_for_object_instance_graph_commit_id",
        _fake_domain_commit_refs_for_oig_commit_id,
    )
    monkeypatch.setattr(
        "aware_service_runtime.package_ref_resolution._hydrate_root_from_commit",
        _fake_hydrate_root_from_commit,
    )

    resolved = await resolve_committed_service_runtime_package_ref(
        index=index,
        package_ref=package_ref,
        materialized_workspace_root=revision_root,
    )

    assert resolved.semantic_branch_id == str(branch_id)
    assert resolved.semantic_object_instance_graph_commit_id == str(
        package_oig_commit_id
    )
    assert resolved.service_package_id == package_id
    assert resolved.service_config_id == service_config_id
    assert resolved.manifest_path is None
    assert resolved.manifest_relative_path == "services/proof/aware.service.toml"


@pytest.mark.asyncio
async def test_committed_service_runtime_package_ref_rejects_missing_branchless_oig_pin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    revision_root = tmp_path / "revision"
    _write_revision_manifest(revision_root)
    package_oig_commit_id = uuid4()
    index = _empty_runtime_index()

    monkeypatch.setattr(
        "aware_service_runtime.package_ref_resolution._find_projection_hash_by_name",
        lambda *, index, projection_name: (
            f"sha256:{_fake_projection_hash_token(projection_name)}"
        ),
    )
    monkeypatch.setattr(
        "aware_service_runtime.package_ref_resolution.FSCommitStore."
        "domain_commit_refs_for_object_instance_graph_commit_id",
        _async_commit_refs(()),
    )

    with pytest.raises(RuntimeError, match="did not resolve to any indexed"):
        await resolve_committed_service_runtime_package_ref(
            index=index,
            package_ref=ServiceRuntimePackageRef(
                family_key="service",
                package_kind="service",
                package_name="proof-service",
                semantic_object_instance_graph_commit_id=str(package_oig_commit_id),
            ),
            materialized_workspace_root=revision_root,
        )


@pytest.mark.asyncio
async def test_committed_service_runtime_package_ref_rejects_ambiguous_branchless_oig_pin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    revision_root = tmp_path / "revision"
    _write_revision_manifest(revision_root)
    package_oig_commit_id = uuid4()
    index = _empty_runtime_index()

    monkeypatch.setattr(
        "aware_service_runtime.package_ref_resolution._find_projection_hash_by_name",
        lambda *, index, projection_name: (
            f"sha256:{_fake_projection_hash_token(projection_name)}"
        ),
    )
    monkeypatch.setattr(
        "aware_service_runtime.package_ref_resolution.FSCommitStore."
        "domain_commit_refs_for_object_instance_graph_commit_id",
        _async_commit_refs(
            (
                ObjectInstanceGraphCommitRef(
                    branch_id=uuid4(),
                    projection_hash="sha256:service_package",
                    object_instance_graph_commit_id=package_oig_commit_id,
                    domain_commit_id=uuid4(),
                ),
                ObjectInstanceGraphCommitRef(
                    branch_id=uuid4(),
                    projection_hash="sha256:service_package",
                    object_instance_graph_commit_id=package_oig_commit_id,
                    domain_commit_id=uuid4(),
                ),
            )
        ),
    )

    with pytest.raises(RuntimeError, match="multiple ServicePackage branches"):
        await resolve_committed_service_runtime_package_ref(
            index=index,
            package_ref=ServiceRuntimePackageRef(
                family_key="service",
                package_kind="service",
                package_name="proof-service",
                semantic_object_instance_graph_commit_id=str(package_oig_commit_id),
            ),
            materialized_workspace_root=revision_root,
        )


def test_service_runtime_package_ref_accepts_absolute_manifest_under_revision_root(
    tmp_path: Path,
) -> None:
    revision_root = tmp_path / "revision"
    service_toml = revision_root / "services" / "proof" / "aware.service.toml"
    _write_revision_manifest(revision_root)
    _write_service_toml(service_toml)

    resolved = resolve_service_runtime_package_ref(
        package_ref=ServiceRuntimePackageRef(
            family_key="service",
            package_kind="service",
            package_name="proof-service",
            manifest_path=service_toml,
        ),
        materialized_workspace_root=revision_root,
    )

    assert resolved.manifest_path == service_toml.resolve()
    assert resolved.manifest_relative_path == "services/proof/aware.service.toml"


def test_service_runtime_package_ref_rejects_manifest_outside_revision_root(
    tmp_path: Path,
) -> None:
    revision_root = tmp_path / "revision"
    service_toml = tmp_path / "outside" / "aware.service.toml"
    _write_revision_manifest(revision_root)
    _write_service_toml(service_toml)

    with pytest.raises(RuntimeError, match="outside materialized workspace root"):
        resolve_service_runtime_package_ref(
            package_ref=ServiceRuntimePackageRef(
                family_key="service",
                package_kind="service",
                package_name="proof-service",
                manifest_path=service_toml,
            ),
            materialized_workspace_root=revision_root,
        )


def test_service_runtime_package_ref_requires_manifest_coordinate_for_now(
    tmp_path: Path,
) -> None:
    revision_root = tmp_path / "revision"
    _write_revision_manifest(revision_root)

    with pytest.raises(RuntimeError, match="requires manifest_path"):
        resolve_service_runtime_package_ref(
            package_ref=ServiceRuntimePackageRef(
                family_key="service",
                package_kind="service",
                package_name="proof-service",
            ),
            materialized_workspace_root=revision_root,
        )


def test_service_runtime_package_ref_requires_revision_manifest(
    tmp_path: Path,
) -> None:
    revision_root = tmp_path / "revision"
    service_toml = revision_root / "services" / "proof" / "aware.service.toml"
    _write_service_toml(service_toml)

    with pytest.raises(
        FileNotFoundError, match="WorkspaceRevision filesystem manifest"
    ):
        resolve_service_runtime_package_ref(
            package_ref=ServiceRuntimePackageRef(
                family_key="service",
                package_kind="service",
                package_name="proof-service",
                manifest_path=service_toml,
            ),
            materialized_workspace_root=revision_root,
        )


def test_service_runtime_package_ref_rejects_non_service_package_kind(
    tmp_path: Path,
) -> None:
    revision_root = tmp_path / "revision"
    _write_revision_manifest(revision_root)

    with pytest.raises(RuntimeError, match="package_kind='service'"):
        resolve_service_runtime_package_ref(
            package_ref=ServiceRuntimePackageRef(
                family_key="service",
                package_kind="api",
                package_name="proof-service",
                manifest_path="services/proof/aware.service.toml",
            ),
            materialized_workspace_root=revision_root,
        )


def test_service_runtime_package_refs_reject_conflicting_semantic_identity(
    tmp_path: Path,
) -> None:
    revision_root = tmp_path / "revision"
    first_toml = revision_root / "services" / "first" / "aware.service.toml"
    second_toml = revision_root / "services" / "second" / "aware.service.toml"
    _write_revision_manifest(revision_root)
    _write_service_toml(
        first_toml, package_name="first-service", fqn_prefix="first_service"
    )
    _write_service_toml(
        second_toml, package_name="second-service", fqn_prefix="second_service"
    )

    with pytest.raises(RuntimeError, match="Conflicting service runtime package refs"):
        resolve_service_runtime_package_refs(
            package_refs=(
                ServiceRuntimePackageRef(
                    family_key="service",
                    package_kind="service",
                    package_name="first-service",
                    manifest_path=first_toml,
                    semantic_package_id="service-package-proof",
                ),
                ServiceRuntimePackageRef(
                    family_key="service",
                    package_kind="service",
                    package_name="second-service",
                    manifest_path=second_toml,
                    semantic_package_id="service-package-proof",
                ),
            ),
            materialized_workspace_root=revision_root,
        )


def _empty_runtime_index() -> MetaGraphRuntimeIndex:
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


def _async_commit_refs(
    refs: tuple[ObjectInstanceGraphCommitRef, ...],
) -> Callable[..., Awaitable[tuple[ObjectInstanceGraphCommitRef, ...]]]:
    async def _fake_commit_refs(
        self: object,
        **kwargs: Any,
    ) -> tuple[ObjectInstanceGraphCommitRef, ...]:
        del self, kwargs
        return refs

    return _fake_commit_refs


def _write_revision_manifest(revision_root: Path) -> None:
    manifest = (
        revision_root / ".aware" / "workspace" / "revision-filesystem.manifest.json"
    )
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("{}", encoding="utf-8")


def _write_service_toml(
    path: Path,
    *,
    package_name: str = "proof-service",
    fqn_prefix: str = "proof_service",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "aware_service = 1",
                "",
                "[service]",
                f'package_name = "{package_name}"',
                f'fqn_prefix = "{fqn_prefix}"',
                "",
                "[build]",
                'sources_dir = "bindings"',
                'compilation_mode = "service_ontology"',
                "",
                "[[dependencies]]",
                'package_name = "proof-service-api"',
                'kind = "api_service_protocol"',
                "",
            ]
        ),
        encoding="utf-8",
    )
