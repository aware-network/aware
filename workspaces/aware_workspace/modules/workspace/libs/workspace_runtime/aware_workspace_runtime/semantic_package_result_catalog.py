"""Portable accepted semantic-package results and persistent catalog proofs.

All values in this module are portable input.  Workspace operation admission
is deliberately owned by the higher adapter; decoding or a successful lookup
cannot issue Workspace authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Protocol, cast

WORKSPACE_SEMANTIC_ACCEPTED_RESULT_CONTRACT = (
    "aware.workspace.semantic-package-accepted-result.v1"
)
WORKSPACE_SEMANTIC_RESULT_NODE_CONTRACT = (
    "aware.workspace.semantic-package-result-catalog-node.v1"
)
WORKSPACE_SEMANTIC_RESULT_CATALOG_CONTRACT = (
    "aware.workspace.semantic-package-result-catalog.v1"
)
WORKSPACE_SEMANTIC_RESULT_MEMBERSHIP_CONTRACT = (
    "aware.workspace.semantic-package-result-membership.v1"
)
WORKSPACE_SEMANTIC_RESULT_NONMEMBERSHIP_CONTRACT = (
    "aware.workspace.semantic-package-result-nonmembership.v1"
)
WORKSPACE_SEMANTIC_RESULT_CATALOG_DEPTH = 64
WORKSPACE_SEMANTIC_RESULT_AUTHORITY_GRADE = "portable_input"

_DIGEST_PREFIX = "sha256:"
_REQUIRED_ROLES = frozenset({"package", "schema", "object_abi"})
_ROLES = _REQUIRED_ROLES | {"artifact"}


class WorkspaceSemanticResultCatalogError(ValueError):
    """Raised when result-catalog authority is malformed or substituted."""


class WorkspaceSemanticResultCatalogReader(Protocol):
    """Request-scoped positive reader; never part of semantic identity."""

    def read_body(self, body_ref: str) -> bytes: ...


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _digest_bytes(value: bytes) -> str:
    return _DIGEST_PREFIX + hashlib.sha256(value).hexdigest()


def _digest_value(value: str, field: str) -> str:
    value = _token(value, field)
    if len(value) != 71 or not value.startswith(_DIGEST_PREFIX):
        raise WorkspaceSemanticResultCatalogError(f"{field} must be SHA-256")
    try:
        _ = int(value[7:], 16)
    except ValueError as error:
        raise WorkspaceSemanticResultCatalogError(f"{field} must be SHA-256") from error
    if value != value.lower():
        raise WorkspaceSemanticResultCatalogError(f"{field} must be lowercase")
    return value


def _token(value: object, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value.strip() != value
        or any(character.isspace() for character in value)
    ):
        raise WorkspaceSemanticResultCatalogError(f"{field} must be a token")
    return value


def _count(value: int, field: str) -> int:
    if type(value) is not int or value < 0:
        raise WorkspaceSemanticResultCatalogError(
            f"{field} must be a non-negative integer"
        )
    return value


def _path(package_ref: str) -> str:
    return hashlib.sha256(_token(package_ref, "package_ref").encode()).hexdigest()


def _semantic_digest(contract: str, payload: object) -> str:
    return _digest_bytes(_canonical_bytes({"contract": contract, "value": payload}))


def _cas_ref(kind: str, digest: str) -> str:
    return (
        "cas://workspace-semantic-package-result/"
        + kind
        + "/"
        + _digest_value(digest, "digest")[7:]
        + ".json"
    )


@dataclass(frozen=True, slots=True, order=True)
class WorkspaceSemanticResultBodyCoordinate:
    role: str
    schema: str
    body_ref: str
    body_digest: str
    size_bytes: int

    def __post_init__(self) -> None:
        if self.role not in _ROLES:
            raise WorkspaceSemanticResultCatalogError("result role unsupported")
        object.__setattr__(self, "schema", _token(self.schema, "schema"))
        object.__setattr__(self, "body_ref", _token(self.body_ref, "body_ref"))
        object.__setattr__(
            self, "body_digest", _digest_value(self.body_digest, "body_digest")
        )
        _ = _count(self.size_bytes, "size_bytes")

    def to_dict(self) -> dict[str, object]:
        return {
            "role": self.role,
            "schema": self.schema,
            "body_ref": self.body_ref,
            "body_digest": self.body_digest,
            "size_bytes": self.size_bytes,
        }

    @classmethod
    def from_dict(cls, value: object) -> WorkspaceSemanticResultBodyCoordinate:
        payload = _object(
            value, {"role", "schema", "body_ref", "body_digest", "size_bytes"}
        )
        return cls(
            role=_string(payload["role"]),
            schema=_string(payload["schema"]),
            body_ref=_string(payload["body_ref"]),
            body_digest=_string(payload["body_digest"]),
            size_bytes=_integer(payload["size_bytes"]),
        )


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticAcceptedPackageResult:
    package_ref: str
    package_manifest_relative_path: str
    direct_dependency_package_refs: tuple[str, ...]
    producing_composition_ref: str
    producing_composition_digest: str
    coordinates: tuple[WorkspaceSemanticResultBodyCoordinate, ...]
    result_digest: str
    result_ref: str
    contract: str = WORKSPACE_SEMANTIC_ACCEPTED_RESULT_CONTRACT
    authority_grade: str = WORKSPACE_SEMANTIC_RESULT_AUTHORITY_GRADE

    def __post_init__(self) -> None:
        if self.contract != WORKSPACE_SEMANTIC_ACCEPTED_RESULT_CONTRACT:
            raise WorkspaceSemanticResultCatalogError("result contract unsupported")
        if self.authority_grade != WORKSPACE_SEMANTIC_RESULT_AUTHORITY_GRADE:
            raise WorkspaceSemanticResultCatalogError("result grade unsupported")
        object.__setattr__(self, "package_ref", _token(self.package_ref, "package_ref"))
        object.__setattr__(
            self,
            "package_manifest_relative_path",
            _token(self.package_manifest_relative_path, "manifest path"),
        )
        dependencies = tuple(
            sorted(
                _token(item, "dependency package_ref")
                for item in self.direct_dependency_package_refs
            )
        )
        if self.package_ref in dependencies or len(dependencies) != len(
            set(dependencies)
        ):
            raise WorkspaceSemanticResultCatalogError(
                "result dependency closure is invalid"
            )
        coordinates = tuple(sorted(self.coordinates))
        roles = tuple(item.role for item in coordinates)
        if not _REQUIRED_ROLES.issubset(roles) or len(roles) != len(set(roles)):
            raise WorkspaceSemanticResultCatalogError(
                "result requires unique package/schema/object_abi coordinates"
            )
        object.__setattr__(self, "direct_dependency_package_refs", dependencies)
        object.__setattr__(self, "coordinates", coordinates)
        object.__setattr__(
            self,
            "producing_composition_ref",
            _token(self.producing_composition_ref, "producing_composition_ref"),
        )
        object.__setattr__(
            self,
            "producing_composition_digest",
            _digest_value(
                self.producing_composition_digest, "producing_composition_digest"
            ),
        )
        expected_digest = _semantic_digest(self.contract, self._semantic_payload())
        if self.result_digest != expected_digest:
            raise WorkspaceSemanticResultCatalogError("result digest mismatched")
        if self.result_ref != _cas_ref("result", expected_digest):
            raise WorkspaceSemanticResultCatalogError("result ref mismatched")

    @classmethod
    def create(
        cls,
        *,
        package_ref: str,
        package_manifest_relative_path: str,
        direct_dependency_package_refs: tuple[str, ...],
        producing_composition_ref: str,
        producing_composition_digest: str,
        coordinates: tuple[WorkspaceSemanticResultBodyCoordinate, ...],
    ) -> WorkspaceSemanticAcceptedPackageResult:
        provisional = cls.__new__(cls)
        semantic = {
            "authority_grade": WORKSPACE_SEMANTIC_RESULT_AUTHORITY_GRADE,
            "package_ref": package_ref,
            "package_manifest_relative_path": package_manifest_relative_path,
            "direct_dependency_package_refs": sorted(direct_dependency_package_refs),
            "producing_composition_ref": producing_composition_ref,
            "producing_composition_digest": producing_composition_digest,
            "coordinates": [item.to_dict() for item in sorted(coordinates)],
        }
        digest = _semantic_digest(WORKSPACE_SEMANTIC_ACCEPTED_RESULT_CONTRACT, semantic)
        del provisional
        return cls(
            package_ref=package_ref,
            package_manifest_relative_path=package_manifest_relative_path,
            direct_dependency_package_refs=tuple(
                sorted(direct_dependency_package_refs)
            ),
            producing_composition_ref=producing_composition_ref,
            producing_composition_digest=producing_composition_digest,
            coordinates=tuple(sorted(coordinates)),
            result_digest=digest,
            result_ref=_cas_ref("result", digest),
        )

    def _semantic_payload(self) -> dict[str, object]:
        return {
            "authority_grade": self.authority_grade,
            "package_ref": self.package_ref,
            "package_manifest_relative_path": self.package_manifest_relative_path,
            "direct_dependency_package_refs": list(self.direct_dependency_package_refs),
            "producing_composition_ref": self.producing_composition_ref,
            "producing_composition_digest": self.producing_composition_digest,
            "coordinates": [item.to_dict() for item in self.coordinates],
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            **self._semantic_payload(),
            "result_digest": self.result_digest,
            "result_ref": self.result_ref,
        }

    @property
    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self.to_dict())

    def coordinate(self, role: str) -> WorkspaceSemanticResultBodyCoordinate | None:
        return next((item for item in self.coordinates if item.role == role), None)

    @classmethod
    def from_json_bytes(cls, value: bytes) -> WorkspaceSemanticAcceptedPackageResult:
        payload = _json_object(value)
        exact = _object(
            payload,
            {
                "contract",
                "authority_grade",
                "package_ref",
                "package_manifest_relative_path",
                "direct_dependency_package_refs",
                "producing_composition_ref",
                "producing_composition_digest",
                "coordinates",
                "result_digest",
                "result_ref",
            },
        )
        return cls(
            contract=_string(exact["contract"]),
            authority_grade=_string(exact["authority_grade"]),
            package_ref=_string(exact["package_ref"]),
            package_manifest_relative_path=_string(
                exact["package_manifest_relative_path"]
            ),
            direct_dependency_package_refs=tuple(
                _string(item) for item in _list(exact["direct_dependency_package_refs"])
            ),
            producing_composition_ref=_string(exact["producing_composition_ref"]),
            producing_composition_digest=_string(exact["producing_composition_digest"]),
            coordinates=tuple(
                WorkspaceSemanticResultBodyCoordinate.from_dict(item)
                for item in _list(exact["coordinates"])
            ),
            result_digest=_string(exact["result_digest"]),
            result_ref=_string(exact["result_ref"]),
        )


@dataclass(frozen=True, slots=True, order=True)
class WorkspaceSemanticResultCatalogChild:
    nibble: str
    node_ref: str

    def __post_init__(self) -> None:
        if len(self.nibble) != 1 or self.nibble not in "0123456789abcdef":
            raise WorkspaceSemanticResultCatalogError("child nibble invalid")
        object.__setattr__(self, "node_ref", _token(self.node_ref, "node_ref"))

    def to_dict(self) -> dict[str, str]:
        return {"nibble": self.nibble, "node_ref": self.node_ref}


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticResultCatalogNode:
    depth: int
    path: str
    children: tuple[WorkspaceSemanticResultCatalogChild, ...]
    package_ref: str | None
    result_ref: str | None
    result_digest: str | None
    result_size_bytes: int | None
    node_digest: str
    node_ref: str
    contract: str = WORKSPACE_SEMANTIC_RESULT_NODE_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != WORKSPACE_SEMANTIC_RESULT_NODE_CONTRACT:
            raise WorkspaceSemanticResultCatalogError("node contract unsupported")
        if type(self.depth) is not int or not 0 <= self.depth <= 64:
            raise WorkspaceSemanticResultCatalogError("node depth invalid")
        if len(self.path) != self.depth or any(
            item not in "0123456789abcdef" for item in self.path
        ):
            raise WorkspaceSemanticResultCatalogError("node path invalid")
        children = tuple(sorted(self.children))
        if children != self.children or len({item.nibble for item in children}) != len(
            children
        ):
            raise WorkspaceSemanticResultCatalogError("node children invalid")
        if self.depth == 64:
            package_ref = self.package_ref
            result_ref = self.result_ref
            result_digest = self.result_digest
            result_size_bytes = self.result_size_bytes
            if (
                children
                or package_ref is None
                or result_ref is None
                or result_digest is None
                or result_size_bytes is None
            ):
                raise WorkspaceSemanticResultCatalogError("leaf value incomplete")
            if _path(package_ref) != self.path:
                raise WorkspaceSemanticResultCatalogError("leaf key/path mismatched")
            _ = _token(result_ref, "result_ref")
            _ = _digest_value(result_digest, "result_digest")
            _ = _count(result_size_bytes, "result_size_bytes")
        elif any(
            item is not None
            for item in (
                self.package_ref,
                self.result_ref,
                self.result_digest,
                self.result_size_bytes,
            )
        ):
            raise WorkspaceSemanticResultCatalogError("branch carries leaf value")
        expected_digest = _semantic_digest(self.contract, self._semantic_payload())
        if self.node_digest != expected_digest:
            raise WorkspaceSemanticResultCatalogError("node digest mismatched")
        if self.node_ref != _cas_ref("node", expected_digest):
            raise WorkspaceSemanticResultCatalogError("node ref mismatched")

    @classmethod
    def create(
        cls,
        *,
        depth: int,
        path: str,
        children: tuple[WorkspaceSemanticResultCatalogChild, ...] = (),
        result: WorkspaceSemanticAcceptedPackageResult | None = None,
    ) -> WorkspaceSemanticResultCatalogNode:
        children = tuple(sorted(children))
        semantic = {
            "depth": depth,
            "path": path,
            "children": [item.to_dict() for item in children],
            "package_ref": result.package_ref if result else None,
            "result_ref": result.result_ref if result else None,
            "result_digest": result.result_digest if result else None,
            "result_size_bytes": len(result.canonical_bytes) if result else None,
        }
        digest = _semantic_digest(WORKSPACE_SEMANTIC_RESULT_NODE_CONTRACT, semantic)
        return cls(
            depth=depth,
            path=path,
            children=children,
            package_ref=result.package_ref if result else None,
            result_ref=result.result_ref if result else None,
            result_digest=result.result_digest if result else None,
            result_size_bytes=len(result.canonical_bytes) if result else None,
            node_digest=digest,
            node_ref=_cas_ref("node", digest),
        )

    def _semantic_payload(self) -> dict[str, object]:
        return {
            "depth": self.depth,
            "path": self.path,
            "children": [item.to_dict() for item in self.children],
            "package_ref": self.package_ref,
            "result_ref": self.result_ref,
            "result_digest": self.result_digest,
            "result_size_bytes": self.result_size_bytes,
        }

    @property
    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(
            {
                "contract": self.contract,
                **self._semantic_payload(),
                "node_digest": self.node_digest,
                "node_ref": self.node_ref,
            }
        )

    @classmethod
    def from_json_bytes(cls, value: bytes) -> WorkspaceSemanticResultCatalogNode:
        payload = _object(
            _json_object(value),
            {
                "contract",
                "depth",
                "path",
                "children",
                "package_ref",
                "result_ref",
                "result_digest",
                "result_size_bytes",
                "node_digest",
                "node_ref",
            },
        )
        return cls(
            contract=_string(payload["contract"]),
            depth=_integer(payload["depth"]),
            path=_string_allow_empty(payload["path"]),
            children=tuple(
                WorkspaceSemanticResultCatalogChild(
                    nibble=_string(_object(item, {"nibble", "node_ref"})["nibble"]),
                    node_ref=_string(_object(item, {"nibble", "node_ref"})["node_ref"]),
                )
                for item in _list(payload["children"])
            ),
            package_ref=_optional_string(payload["package_ref"]),
            result_ref=_optional_string(payload["result_ref"]),
            result_digest=_optional_string(payload["result_digest"]),
            result_size_bytes=_optional_integer(payload["result_size_bytes"]),
            node_digest=_string(payload["node_digest"]),
            node_ref=_string(payload["node_ref"]),
        )


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticResultCatalogRoot:
    root_node_ref: str
    result_count: int
    catalog_digest: str
    catalog_ref: str
    contract: str = WORKSPACE_SEMANTIC_RESULT_CATALOG_CONTRACT
    authority_grade: str = WORKSPACE_SEMANTIC_RESULT_AUTHORITY_GRADE

    def __post_init__(self) -> None:
        if self.contract != WORKSPACE_SEMANTIC_RESULT_CATALOG_CONTRACT:
            raise WorkspaceSemanticResultCatalogError("catalog contract unsupported")
        if self.authority_grade != WORKSPACE_SEMANTIC_RESULT_AUTHORITY_GRADE:
            raise WorkspaceSemanticResultCatalogError("catalog grade unsupported")
        object.__setattr__(
            self, "root_node_ref", _token(self.root_node_ref, "root_node_ref")
        )
        _ = _count(self.result_count, "result_count")
        expected = _semantic_digest(self.contract, self._semantic_payload())
        if self.catalog_digest != expected or self.catalog_ref != _cas_ref(
            "catalog", expected
        ):
            raise WorkspaceSemanticResultCatalogError("catalog identity mismatched")

    @classmethod
    def create(
        cls, *, root_node_ref: str, result_count: int
    ) -> WorkspaceSemanticResultCatalogRoot:
        semantic = {
            "authority_grade": WORKSPACE_SEMANTIC_RESULT_AUTHORITY_GRADE,
            "root_node_ref": root_node_ref,
            "result_count": result_count,
        }
        digest = _semantic_digest(WORKSPACE_SEMANTIC_RESULT_CATALOG_CONTRACT, semantic)
        return cls(root_node_ref, result_count, digest, _cas_ref("catalog", digest))

    @classmethod
    def typed_empty(
        cls,
    ) -> tuple[WorkspaceSemanticResultCatalogRoot, WorkspaceSemanticResultCatalogNode]:
        node = WorkspaceSemanticResultCatalogNode.create(depth=0, path="")
        return cls.create(root_node_ref=node.node_ref, result_count=0), node

    def _semantic_payload(self) -> dict[str, object]:
        return {
            "authority_grade": self.authority_grade,
            "root_node_ref": self.root_node_ref,
            "result_count": self.result_count,
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            **self._semantic_payload(),
            "catalog_digest": self.catalog_digest,
            "catalog_ref": self.catalog_ref,
        }

    @classmethod
    def from_dict(cls, value: object) -> WorkspaceSemanticResultCatalogRoot:
        payload = _object(
            value,
            {
                "contract",
                "authority_grade",
                "root_node_ref",
                "result_count",
                "catalog_digest",
                "catalog_ref",
            },
        )
        return cls(
            root_node_ref=_string(payload["root_node_ref"]),
            result_count=_integer(payload["result_count"]),
            catalog_digest=_string(payload["catalog_digest"]),
            catalog_ref=_string(payload["catalog_ref"]),
            contract=_string(payload["contract"]),
            authority_grade=_string(payload["authority_grade"]),
        )


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticResultMembershipProof:
    catalog: WorkspaceSemanticResultCatalogRoot
    package_ref: str
    result_ref: str
    node_refs: tuple[str, ...]
    proof_digest: str
    contract: str = WORKSPACE_SEMANTIC_RESULT_MEMBERSHIP_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != WORKSPACE_SEMANTIC_RESULT_MEMBERSHIP_CONTRACT:
            raise WorkspaceSemanticResultCatalogError("membership contract unsupported")
        object.__setattr__(self, "package_ref", _token(self.package_ref, "package_ref"))
        object.__setattr__(self, "result_ref", _token(self.result_ref, "result_ref"))
        if type(self.node_refs) is not tuple or len(self.node_refs) != 65:
            raise WorkspaceSemanticResultCatalogError("membership path incomplete")
        expected = _semantic_digest(self.contract, self._semantic_payload())
        if self.proof_digest != expected:
            raise WorkspaceSemanticResultCatalogError("membership digest mismatched")

    def _semantic_payload(self) -> dict[str, object]:
        return {
            "catalog": self.catalog.to_dict(),
            "package_ref": self.package_ref,
            "result_ref": self.result_ref,
            "node_refs": list(self.node_refs),
        }

    @classmethod
    def create(
        cls,
        *,
        catalog: WorkspaceSemanticResultCatalogRoot,
        package_ref: str,
        result_ref: str,
        node_refs: tuple[str, ...],
    ) -> WorkspaceSemanticResultMembershipProof:
        semantic = {
            "catalog": catalog.to_dict(),
            "package_ref": package_ref,
            "result_ref": result_ref,
            "node_refs": list(node_refs),
        }
        return cls(
            catalog,
            package_ref,
            result_ref,
            node_refs,
            _semantic_digest(WORKSPACE_SEMANTIC_RESULT_MEMBERSHIP_CONTRACT, semantic),
        )


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticResultNonmembershipProof:
    catalog: WorkspaceSemanticResultCatalogRoot
    package_ref: str
    node_refs: tuple[str, ...]
    missing_depth: int
    proof_digest: str
    contract: str = WORKSPACE_SEMANTIC_RESULT_NONMEMBERSHIP_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != WORKSPACE_SEMANTIC_RESULT_NONMEMBERSHIP_CONTRACT:
            raise WorkspaceSemanticResultCatalogError(
                "nonmembership contract unsupported"
            )
        object.__setattr__(self, "package_ref", _token(self.package_ref, "package_ref"))
        if (
            type(self.node_refs) is not tuple
            or len(self.node_refs) != self.missing_depth + 1
            or not 0 <= self.missing_depth < 64
        ):
            raise WorkspaceSemanticResultCatalogError("nonmembership path incomplete")
        expected = _semantic_digest(self.contract, self._semantic_payload())
        if self.proof_digest != expected:
            raise WorkspaceSemanticResultCatalogError("nonmembership digest mismatched")

    def _semantic_payload(self) -> dict[str, object]:
        return {
            "catalog": self.catalog.to_dict(),
            "package_ref": self.package_ref,
            "node_refs": list(self.node_refs),
            "missing_depth": self.missing_depth,
        }

    @classmethod
    def create(
        cls,
        *,
        catalog: WorkspaceSemanticResultCatalogRoot,
        package_ref: str,
        node_refs: tuple[str, ...],
        missing_depth: int,
    ) -> WorkspaceSemanticResultNonmembershipProof:
        semantic = {
            "catalog": catalog.to_dict(),
            "package_ref": package_ref,
            "node_refs": list(node_refs),
            "missing_depth": missing_depth,
        }
        return cls(
            catalog,
            package_ref,
            node_refs,
            missing_depth,
            _semantic_digest(
                WORKSPACE_SEMANTIC_RESULT_NONMEMBERSHIP_CONTRACT, semantic
            ),
        )


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticResultCatalogPatch:
    prior: WorkspaceSemanticResultCatalogRoot
    result: WorkspaceSemanticResultCatalogRoot
    accepted_result: WorkspaceSemanticAcceptedPackageResult
    emitted_nodes: tuple[WorkspaceSemanticResultCatalogNode, ...]


def read_catalog_membership(
    *,
    catalog: WorkspaceSemanticResultCatalogRoot,
    package_ref: str,
    reader: WorkspaceSemanticResultCatalogReader,
) -> tuple[
    WorkspaceSemanticResultMembershipProof, WorkspaceSemanticAcceptedPackageResult
]:
    path = _path(package_ref)
    nodes = _read_path(
        catalog=catalog, package_ref=package_ref, reader=reader, require_leaf=True
    )
    leaf = nodes[-1]
    if leaf.package_ref != package_ref or leaf.result_ref is None:
        raise WorkspaceSemanticResultCatalogError("catalog result membership absent")
    result_body = reader.read_body(leaf.result_ref)
    if len(result_body) != cast(int, leaf.result_size_bytes):
        raise WorkspaceSemanticResultCatalogError("reader body authority substituted")
    result = WorkspaceSemanticAcceptedPackageResult.from_json_bytes(result_body)
    if (
        result.package_ref != package_ref
        or result.result_ref != leaf.result_ref
        or result.result_digest != leaf.result_digest
        or result.canonical_bytes != result_body
    ):
        raise WorkspaceSemanticResultCatalogError("reader body authority substituted")
    proof = WorkspaceSemanticResultMembershipProof.create(
        catalog=catalog,
        package_ref=package_ref,
        result_ref=result.result_ref,
        node_refs=tuple(item.node_ref for item in nodes),
    )
    validate_catalog_membership(proof=proof, result=result, nodes=nodes)
    assert _path(package_ref) == path
    return proof, result


def read_catalog_nonmembership(
    *,
    catalog: WorkspaceSemanticResultCatalogRoot,
    package_ref: str,
    reader: WorkspaceSemanticResultCatalogReader,
) -> WorkspaceSemanticResultNonmembershipProof:
    nodes = _read_path(
        catalog=catalog, package_ref=package_ref, reader=reader, require_leaf=False
    )
    if len(nodes) == 65:
        raise WorkspaceSemanticResultCatalogError("catalog result already exists")
    proof = WorkspaceSemanticResultNonmembershipProof.create(
        catalog=catalog,
        package_ref=package_ref,
        node_refs=tuple(item.node_ref for item in nodes),
        missing_depth=len(nodes) - 1,
    )
    validate_catalog_nonmembership(proof=proof, nodes=nodes)
    return proof


def validate_catalog_membership(
    *,
    proof: WorkspaceSemanticResultMembershipProof,
    result: WorkspaceSemanticAcceptedPackageResult,
    nodes: tuple[WorkspaceSemanticResultCatalogNode, ...],
) -> None:
    _validate_path(
        proof.catalog, proof.package_ref, proof.node_refs, nodes, require_leaf=True
    )
    leaf = nodes[-1]
    if (
        leaf.result_ref != proof.result_ref
        or result.result_ref != proof.result_ref
        or result.package_ref != proof.package_ref
    ):
        raise WorkspaceSemanticResultCatalogError("membership result substituted")


def validate_catalog_nonmembership(
    *,
    proof: WorkspaceSemanticResultNonmembershipProof,
    nodes: tuple[WorkspaceSemanticResultCatalogNode, ...],
) -> None:
    _validate_path(
        proof.catalog, proof.package_ref, proof.node_refs, nodes, require_leaf=False
    )
    if proof.missing_depth != len(nodes) - 1:
        raise WorkspaceSemanticResultCatalogError(
            "nonmembership missing depth substituted"
        )


def patch_catalog_result(
    *,
    catalog: WorkspaceSemanticResultCatalogRoot,
    accepted_result: WorkspaceSemanticAcceptedPackageResult,
    reader: WorkspaceSemanticResultCatalogReader,
) -> WorkspaceSemanticResultCatalogPatch:
    try:
        membership, _ = read_catalog_membership(
            catalog=catalog, package_ref=accepted_result.package_ref, reader=reader
        )
    except WorkspaceSemanticResultCatalogError as error:
        if "membership absent" not in str(
            error
        ) and "terminates before leaf" not in str(error):
            raise
        membership = None
    nodes = _read_path(
        catalog=catalog,
        package_ref=accepted_result.package_ref,
        reader=reader,
        require_leaf=False,
    )
    exists = len(nodes) == 65
    path = _path(accepted_result.package_ref)
    emitted: list[WorkspaceSemanticResultCatalogNode] = []
    replacement = WorkspaceSemanticResultCatalogNode.create(
        depth=64, path=path, result=accepted_result
    )
    emitted.append(replacement)
    start_depth = 63
    if exists:
        ancestors = nodes[:-1]
    else:
        ancestors = nodes
        for depth in range(63, nodes[-1].depth, -1):
            replacement = WorkspaceSemanticResultCatalogNode.create(
                depth=depth,
                path=path[:depth],
                children=(
                    WorkspaceSemanticResultCatalogChild(
                        path[depth], replacement.node_ref
                    ),
                ),
            )
            emitted.append(replacement)
        start_depth = nodes[-1].depth
    for node in reversed(ancestors):
        nibble = path[node.depth]
        children = tuple(item for item in node.children if item.nibble != nibble) + (
            WorkspaceSemanticResultCatalogChild(nibble, replacement.node_ref),
        )
        replacement = WorkspaceSemanticResultCatalogNode.create(
            depth=node.depth, path=node.path, children=tuple(sorted(children))
        )
        emitted.append(replacement)
    if replacement.depth != 0:
        raise WorkspaceSemanticResultCatalogError("catalog patch did not reach root")
    result_root = WorkspaceSemanticResultCatalogRoot.create(
        root_node_ref=replacement.node_ref,
        result_count=catalog.result_count + (0 if exists else 1),
    )
    del membership, start_depth
    return WorkspaceSemanticResultCatalogPatch(
        catalog,
        result_root,
        accepted_result,
        tuple(
            sorted(
                {item.node_ref: item for item in emitted}.values(),
                key=lambda item: (item.depth, item.node_ref),
            )
        ),
    )


def _read_path(
    *,
    catalog: WorkspaceSemanticResultCatalogRoot,
    package_ref: str,
    reader: WorkspaceSemanticResultCatalogReader,
    require_leaf: bool,
) -> tuple[WorkspaceSemanticResultCatalogNode, ...]:
    path = _path(package_ref)
    expected_ref = catalog.root_node_ref
    nodes: list[WorkspaceSemanticResultCatalogNode] = []
    for depth in range(65):
        body = reader.read_body(expected_ref)
        node = WorkspaceSemanticResultCatalogNode.from_json_bytes(body)
        if (
            node.canonical_bytes != body
            or node.node_ref != expected_ref
            or node.depth != depth
            or node.path != path[:depth]
        ):
            raise WorkspaceSemanticResultCatalogError("catalog node/path substituted")
        nodes.append(node)
        if depth == 64:
            break
        child = next(
            (item for item in node.children if item.nibble == path[depth]), None
        )
        if child is None:
            if require_leaf:
                raise WorkspaceSemanticResultCatalogError(
                    "catalog path terminates before leaf"
                )
            break
        expected_ref = child.node_ref
    if require_leaf and len(nodes) != 65:
        raise WorkspaceSemanticResultCatalogError("catalog membership absent")
    return tuple(nodes)


def _validate_path(
    catalog: WorkspaceSemanticResultCatalogRoot,
    package_ref: str,
    refs: tuple[str, ...],
    nodes: tuple[WorkspaceSemanticResultCatalogNode, ...],
    *,
    require_leaf: bool,
) -> None:
    if (
        tuple(item.node_ref for item in nodes) != refs
        or not nodes
        or nodes[0].node_ref != catalog.root_node_ref
    ):
        raise WorkspaceSemanticResultCatalogError("proof nodes substituted")
    path = _path(package_ref)
    for depth, node in enumerate(nodes):
        if node.depth != depth or node.path != path[:depth]:
            raise WorkspaceSemanticResultCatalogError("proof path substituted")
        if depth < len(nodes) - 1:
            child = next(
                (item for item in node.children if item.nibble == path[depth]), None
            )
            if child is None or child.node_ref != nodes[depth + 1].node_ref:
                raise WorkspaceSemanticResultCatalogError("proof link substituted")
    if require_leaf:
        if len(nodes) != 65 or nodes[-1].package_ref != package_ref:
            raise WorkspaceSemanticResultCatalogError("proof leaf substituted")
    else:
        terminal = nodes[-1]
        if terminal.depth >= 64 or any(
            item.nibble == path[terminal.depth] for item in terminal.children
        ):
            raise WorkspaceSemanticResultCatalogError("nonmembership is not proven")


def _json_object(value: bytes) -> dict[str, object]:
    try:
        return _object(cast(object, json.loads(value)), None)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise WorkspaceSemanticResultCatalogError("JSON body invalid") from error


def _object(value: object, fields: set[str] | None) -> dict[str, object]:
    if not isinstance(value, dict):
        raise WorkspaceSemanticResultCatalogError("value must be an object")
    untyped = cast(dict[object, object], value)
    if any(not isinstance(key, str) for key in untyped):
        raise WorkspaceSemanticResultCatalogError("object keys must be text")
    result = cast(dict[str, object], untyped)
    if fields is not None and set(result) != fields:
        raise WorkspaceSemanticResultCatalogError("object fields incomplete or unknown")
    return result


def _list(value: object) -> list[object]:
    if not isinstance(value, list):
        raise WorkspaceSemanticResultCatalogError("value must be a list")
    return cast(list[object], value)


def _string(value: object) -> str:
    if not isinstance(value, str):
        raise WorkspaceSemanticResultCatalogError("value must be text")
    return value


def _string_allow_empty(value: object) -> str:
    if not isinstance(value, str):
        raise WorkspaceSemanticResultCatalogError("value must be text")
    return value


def _optional_string(value: object) -> str | None:
    return None if value is None else _string(value)


def _integer(value: object) -> int:
    if type(value) is not int:
        raise WorkspaceSemanticResultCatalogError("value must be integer")
    return value


def _optional_integer(value: object) -> int | None:
    return None if value is None else _integer(value)


__all__ = [
    "WORKSPACE_SEMANTIC_ACCEPTED_RESULT_CONTRACT",
    "WORKSPACE_SEMANTIC_RESULT_AUTHORITY_GRADE",
    "WORKSPACE_SEMANTIC_RESULT_CATALOG_CONTRACT",
    "WorkspaceSemanticAcceptedPackageResult",
    "WorkspaceSemanticResultBodyCoordinate",
    "WorkspaceSemanticResultCatalogChild",
    "WorkspaceSemanticResultCatalogError",
    "WorkspaceSemanticResultCatalogNode",
    "WorkspaceSemanticResultCatalogPatch",
    "WorkspaceSemanticResultCatalogReader",
    "WorkspaceSemanticResultCatalogRoot",
    "WorkspaceSemanticResultMembershipProof",
    "WorkspaceSemanticResultNonmembershipProof",
    "patch_catalog_result",
    "read_catalog_membership",
    "read_catalog_nonmembership",
    "validate_catalog_membership",
    "validate_catalog_nonmembership",
]
