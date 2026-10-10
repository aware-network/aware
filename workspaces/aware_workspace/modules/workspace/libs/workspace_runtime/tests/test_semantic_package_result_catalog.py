from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest
from aware_workspace_runtime.semantic_package_result_catalog import (
    WorkspaceSemanticAcceptedPackageResult,
    WorkspaceSemanticResultBodyCoordinate,
    WorkspaceSemanticResultCatalogError,
    WorkspaceSemanticResultCatalogNode,
    WorkspaceSemanticResultCatalogPatch,
    WorkspaceSemanticResultCatalogRoot,
    patch_catalog_result,
    read_catalog_membership,
    read_catalog_nonmembership,
    validate_catalog_membership,
)


def _digest(value: bytes | str) -> str:
    body = value.encode() if isinstance(value, str) else value
    return "sha256:" + hashlib.sha256(body).hexdigest()


class _Reader:
    def __init__(self, bodies: dict[str, bytes]) -> None:
        self.bodies = bodies
        self.reads = 0

    def read_body(self, body_ref: str) -> bytes:
        self.reads += 1
        try:
            return self.bodies[body_ref]
        except KeyError as error:
            raise WorkspaceSemanticResultCatalogError("body unavailable") from error


def _coordinate(role: str, package: str) -> WorkspaceSemanticResultBodyCoordinate:
    body = f"{package}:{role}".encode()
    return WorkspaceSemanticResultBodyCoordinate(
        role=role,
        schema=f"test.{role}.v1",
        body_ref=f"cas://test/{package}/{role}",
        body_digest=_digest(body),
        size_bytes=len(body),
    )


def _result(
    package: str, dependencies: tuple[str, ...] = ()
) -> WorkspaceSemanticAcceptedPackageResult:
    package_ref = f"package:{package}@1.0.0"
    return WorkspaceSemanticAcceptedPackageResult.create(
        package_ref=package_ref,
        package_manifest_relative_path=f"workspaces/{package}/aware.toml",
        direct_dependency_package_refs=dependencies,
        producing_composition_ref=f"cas://composition/{package}",
        producing_composition_digest=_digest(package + ":composition"),
        coordinates=tuple(
            _coordinate(role, package) for role in ("package", "schema", "object_abi")
        ),
    )


def _store_patch(
    reader: _Reader,
    patch: WorkspaceSemanticResultCatalogPatch,
) -> None:
    accepted = patch.accepted_result
    reader.bodies[accepted.result_ref] = accepted.canonical_bytes
    for node in patch.emitted_nodes:
        reader.bodies[node.node_ref] = node.canonical_bytes


def test_typed_empty_nonmembership_then_positive_storage_membership() -> None:
    root, empty = WorkspaceSemanticResultCatalogRoot.typed_empty()
    reader = _Reader({empty.node_ref: empty.canonical_bytes})

    absent = read_catalog_nonmembership(
        catalog=root,
        package_ref="package:storage@1.0.0",
        reader=reader,
    )
    assert absent.catalog == root
    assert absent.missing_depth == 0

    storage = _result("storage")
    patch = patch_catalog_result(catalog=root, accepted_result=storage, reader=reader)
    _store_patch(reader, patch)
    membership, observed = read_catalog_membership(
        catalog=patch.result,
        package_ref=storage.package_ref,
        reader=reader,
    )
    assert observed == storage
    assert len(membership.node_refs) == 65
    assert patch.result.result_count == 1

    content_absent = read_catalog_nonmembership(
        catalog=patch.result,
        package_ref="package:content@1.0.0",
        reader=reader,
    )
    assert content_absent.catalog == patch.result


def test_patch_is_persistent_and_replay_is_deterministic() -> None:
    root, empty = WorkspaceSemanticResultCatalogRoot.typed_empty()
    reader = _Reader({empty.node_ref: empty.canonical_bytes})
    storage = _result("storage")

    first = patch_catalog_result(catalog=root, accepted_result=storage, reader=reader)
    second = patch_catalog_result(catalog=root, accepted_result=storage, reader=reader)

    assert first.result == second.result
    assert first.emitted_nodes == second.emitted_nodes
    assert reader.bodies == {empty.node_ref: empty.canonical_bytes}


def test_membership_and_reader_substitution_fail_closed() -> None:
    root, empty = WorkspaceSemanticResultCatalogRoot.typed_empty()
    reader = _Reader({empty.node_ref: empty.canonical_bytes})
    storage = _result("storage")
    patch = patch_catalog_result(catalog=root, accepted_result=storage, reader=reader)
    _store_patch(reader, patch)
    proof, result = read_catalog_membership(
        catalog=patch.result,
        package_ref=storage.package_ref,
        reader=reader,
    )
    nodes = tuple(
        WorkspaceSemanticResultCatalogNode.from_json_bytes(reader.bodies[ref])
        for ref in proof.node_refs
    )

    with pytest.raises(WorkspaceSemanticResultCatalogError):
        validate_catalog_membership(
            proof=replace(proof, result_ref="cas://foreign/result"),
            result=result,
            nodes=nodes,
        )

    reader.bodies[result.result_ref] += b" "
    with pytest.raises(
        WorkspaceSemanticResultCatalogError, match="reader body authority substituted"
    ):
        read_catalog_membership(
            catalog=patch.result,
            package_ref=storage.package_ref,
            reader=reader,
        )

    reader.bodies[result.result_ref] = result.canonical_bytes
    reader.bodies[proof.node_refs[0]] += b" "
    with pytest.raises(
        WorkspaceSemanticResultCatalogError, match="catalog node/path substituted"
    ):
        read_catalog_membership(
            catalog=patch.result,
            package_ref=storage.package_ref,
            reader=reader,
        )


def test_optional_artifact_is_preserved_and_unknown_roles_reject() -> None:
    storage = _result("storage")
    artifact = _coordinate("artifact", "storage")
    with_artifact = WorkspaceSemanticAcceptedPackageResult.create(
        package_ref=storage.package_ref,
        package_manifest_relative_path=storage.package_manifest_relative_path,
        direct_dependency_package_refs=(),
        producing_composition_ref=storage.producing_composition_ref,
        producing_composition_digest=storage.producing_composition_digest,
        coordinates=storage.coordinates + (artifact,),
    )
    assert with_artifact.coordinate("artifact") == artifact
    assert (
        WorkspaceSemanticAcceptedPackageResult.from_json_bytes(
            with_artifact.canonical_bytes
        )
        == with_artifact
    )

    with pytest.raises(WorkspaceSemanticResultCatalogError):
        replace(artifact, role="foreign")
