from __future__ import annotations

from pathlib import Path

import pytest

from aware_api_runtime.dto_ownership_inventory import (
    API_DTO_OWNER,
    MODULE_API_OWNER,
    UNKNOWN_OWNER,
    ApiDtoOwnershipViolation,
    assert_no_module_api_dependencies_for_cutovers,
    build_api_dto_ownership_inventory,
)
from _api_runtime_test_paths import REPO_ROOT


EXPECTED_KERNEL_MODULE_API_EDGES: set[tuple[str, str]] = set()


def test_inventory_collects_module_and_api_dto_edges_from_fixture(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "workspaces/aware_kernel/aware.workspace.toml",
        """
        aware = 1

        [workspace]
        handle = "aware_kernel"

        [[workspace.modules]]
        id = "identity"
        path = "modules/identity"
        """,
    )
    _write(
        tmp_path / "workspaces/aware_kernel/modules/identity/aware.module.toml",
        """
        aware = 1

        [[packages]]
        id = "identity_service_api"
        kind = "api"
        manifest = "apis/identity/aware.api.toml"
        visibility = "module"
        """,
    )
    _write(
        tmp_path / "modules/identity/structure/api/aware.toml",
        """
        aware = 1

        [package]
        package_name = "identity-api"
        fqn_prefix = "aware_identity_api"
        kind = "api"
        """,
    )
    _write(
        tmp_path / "modules/identity/structure/api/aware/identity/models.aware",
        "schema identity { class IdentityProfile { name text } }\n",
    )
    _write(
        tmp_path / "apis/identity/dto/aware.toml",
        """
        aware = 1

        [package]
        package_name = "identity-service-dto"
        fqn_prefix = "aware_identity_service_dto"
        kind = "api"
        """,
    )
    _write(
        tmp_path
        / "workspaces/aware_kernel/modules/identity/apis/identity/aware.api.toml",
        """
        aware_api = 1

        [api]
        package_name = "identity-service-api"
        fqn_prefix = "aware_identity_service_api"

        [[dependencies]]
        package_name = "identity-api"

        [[dependencies]]
        package_name = "identity-service-dto"

        [[dependencies]]
        package_name = "identity-ontology"
        """,
    )

    inventory = build_api_dto_ownership_inventory(tmp_path)

    assert [package.package_name for package in inventory.module_api_packages] == [
        "identity-api"
    ]
    assert inventory.module_api_packages[0].source_count == 1
    assert [package.package_name for package in inventory.api_owned_dto_packages] == [
        "identity-service-dto"
    ]
    assert [
        (
            edge.api_package_name,
            edge.dependency_package_name,
            edge.dependency_owner,
        )
        for edge in inventory.kernel_api_dependency_edges
    ] == [
        ("identity-service-api", "identity-api", MODULE_API_OWNER),
        ("identity-service-api", "identity-ontology", UNKNOWN_OWNER),
        ("identity-service-api", "identity-service-dto", API_DTO_OWNER),
    ]


def test_current_kernel_api_module_dependency_inventory_is_allowlisted() -> None:
    inventory = build_api_dto_ownership_inventory(REPO_ROOT)

    module_edges = {
        (edge.api_package_name, edge.dependency_package_name)
        for edge in inventory.kernel_module_api_dependency_edges
    }

    assert inventory.module_api_packages == ()
    assert sum(package.source_count for package in inventory.module_api_packages) == 0
    assert module_edges == EXPECTED_KERNEL_MODULE_API_EDGES


def test_cutover_guard_rejects_unallowlisted_module_api_dependencies(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "workspaces/aware_kernel/aware.workspace.toml",
        """
        aware = 1

        [workspace]
        handle = "aware_kernel"

        [[workspace.modules]]
        id = "meta"
        path = "modules/meta"
        """,
    )
    _write(
        tmp_path / "workspaces/aware_kernel/modules/meta/aware.module.toml",
        """
        aware = 1

        [[packages]]
        id = "meta_service_api"
        kind = "api"
        manifest = "apis/meta/aware.api.toml"
        visibility = "module"
        """,
    )
    _write(
        tmp_path / "modules/meta/structure/api/aware.toml",
        """
        aware = 1

        [package]
        package_name = "meta-api"
        fqn_prefix = "aware_meta_api"
        kind = "api"
        """,
    )
    _write(
        tmp_path / "modules/meta/structure/api/aware/graph/config/models.aware",
        "schema config { class ObjectConfigGraphDelta { graph_hash text } }\n",
    )
    _write(
        tmp_path / "workspaces/aware_kernel/modules/meta/apis/meta/aware.api.toml",
        """
        aware_api = 1

        [api]
        package_name = "meta-service-api"
        fqn_prefix = "aware_meta_service_api"

        [[dependencies]]
        package_name = "meta-api"
        """,
    )

    inventory = build_api_dto_ownership_inventory(tmp_path)

    with pytest.raises(ApiDtoOwnershipViolation, match="meta-service-api"):
        assert_no_module_api_dependencies_for_cutovers(
            inventory,
            cutover_api_package_names={"meta-service-api"},
        )

    current_inventory = build_api_dto_ownership_inventory(REPO_ROOT)

    assert_no_module_api_dependencies_for_cutovers(
        current_inventory,
        cutover_api_package_names={"meta-service-api"},
    )


def test_current_cutover_guard_allows_migrated_kernel_apis() -> None:
    inventory = build_api_dto_ownership_inventory(REPO_ROOT)

    assert_no_module_api_dependencies_for_cutovers(
        inventory,
        cutover_api_package_names={
            "code-service-api",
            "file-system-service-api",
            "meta-service-api",
            "ontology-service-api",
            "storage-service-api",
        },
    )


def test_inventory_json_shape_is_deterministic() -> None:
    inventory = build_api_dto_ownership_inventory(REPO_ROOT)
    payload = inventory.to_json_dict()

    assert list(payload) == [
        "module_api_packages",
        "api_owned_dto_packages",
        "kernel_api_manifest_paths",
        "kernel_api_dependency_edges",
    ]
    assert payload["kernel_api_manifest_paths"] == [
        "workspaces/aware_kernel/modules/api/apis/api/aware.api.toml",
        "workspaces/aware_kernel/modules/code/apis/code/aware.api.toml",
        "workspaces/aware_kernel/modules/filesystem/apis/filesystem/aware.api.toml",
        "workspaces/aware_kernel/modules/meta/apis/meta/aware.api.toml",
        "workspaces/aware_kernel/modules/ontology/apis/ontology/aware.api.toml",
        "workspaces/aware_kernel/modules/reactivity/apis/reactivity/aware.api.toml",
        "workspaces/aware_kernel/modules/storage/apis/storage/aware.api.toml",
    ]
    assert [
        edge["dependency_owner"] for edge in payload["kernel_api_dependency_edges"]
    ] == [
        API_DTO_OWNER,
        API_DTO_OWNER,
        API_DTO_OWNER,
        API_DTO_OWNER,
        API_DTO_OWNER,
        API_DTO_OWNER,
        API_DTO_OWNER,
    ]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8")
