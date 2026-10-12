# pyright: reportImportCycles=false
"""Package/catalog authorities and positive-only cross-package type slices."""

from __future__ import annotations

import copy
import hashlib
import re
from dataclasses import dataclass
from time import perf_counter_ns

from .definition_fragment import TypeDefinitionFragment
from .encoding import digest_payload
from .persistent_index import (
    PERSISTENT_INDEX_DEPTH,
    PersistentBodyAuthority,
    PersistentBodyCoordinate,
    PersistentIndexNode,
    PersistentIndexRoot,
    TypeSchemaPersistentIndexError,
    _flat_protected_operand_guard,
    _meta_type_schema_operation,
    _MetaTypeSchemaOperationContext,
    _prevalidated_digest,
    _prevalidated_json,
    _require_meta_type_schema_operation,
    _require_meta_type_schema_operation_operands,
    key_digest_path,
)
from .positive_reader import (
    PersistentIndexMembershipProof,
    PersistentIndexProofBundle,
    PositiveReadObservation,
    TypeSchemaPositiveReaderCapability,
    _create_prevalidated_membership_proof,
    _create_prevalidated_proof_bundle_with_wire,
    _state,
)

TYPE_SCHEMA_PACKAGE_ROOT_CONTRACT = "aware.meta.type-schema.package-root.v1"
TYPE_OWNER_BINDING_CONTRACT = "aware.meta.type-schema.owner-binding.v1"
TYPE_SCHEMA_CATALOG_ROOT_CONTRACT = "aware.meta.type-schema.catalog-root.v1"
TYPE_SCHEMA_COMPOSED_SLICE_CONTRACT = "aware.meta.type-schema.composed-slice.v1"
_WHITESPACE = re.compile(r"\s").search


class TypeSchemaCompositionError(ValueError):
    """Raised when package ownership or requested closure is inexact."""


def _token(value: str, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value.strip() != value
        or _WHITESPACE(value) is not None
    ):
        raise TypeSchemaCompositionError(f"{field} must be a nonempty token")
    return value


def _tokens(values: tuple[str, ...], field: str) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise TypeSchemaCompositionError(f"{field} must be immutable tuple")
    normalized = tuple(sorted(_token(value, field) for value in values))
    if normalized != values or len(normalized) != len(set(normalized)):
        raise TypeSchemaCompositionError(f"{field} must be sorted and unique")
    return normalized


@dataclass(frozen=True, slots=True)
class TypeSchemaPackageRoot:
    package_ref: str
    package_name: str
    namespace: str
    semantic_version: str
    dependency_package_refs: tuple[str, ...]
    definition_index: PersistentIndexRoot
    source_attribution_index: PersistentIndexRoot
    package_root_ref: str
    contract: str = TYPE_SCHEMA_PACKAGE_ROOT_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != TYPE_SCHEMA_PACKAGE_ROOT_CONTRACT:
            raise TypeSchemaCompositionError("package root contract unsupported")
        for field in ("package_ref", "package_name", "namespace", "semantic_version"):
            object.__setattr__(self, field, _token(getattr(self, field), field))
        dependencies = _tokens(self.dependency_package_refs, "dependency_package_refs")
        if self.package_ref in dependencies:
            raise TypeSchemaCompositionError("package cannot depend on itself")
        for value, expected in (
            (self.definition_index, f"definition:{self.package_ref}"),
            (
                self.source_attribution_index,
                f"source-attribution:{self.package_ref}",
            ),
        ):
            if not isinstance(value, PersistentIndexRoot) or value.keyspace != expected:
                raise TypeSchemaCompositionError(
                    f"package index keyspace must be {expected!r}"
                )
        expected_ref = digest_payload(self.contract, self.semantic_wire())
        if self.package_root_ref != expected_ref:
            raise TypeSchemaCompositionError(
                f"package_root_ref mismatch; expected {expected_ref}"
            )

    @classmethod
    def create(
        cls,
        *,
        package_ref: str,
        package_name: str,
        namespace: str,
        semantic_version: str,
        dependency_package_refs: tuple[str, ...],
        definition_index: PersistentIndexRoot,
        source_attribution_index: PersistentIndexRoot,
    ) -> TypeSchemaPackageRoot:
        dependencies = tuple(sorted(dependency_package_refs))
        normalized_package_ref = _token(package_ref, "package_ref")
        normalized_package_name = _token(package_name, "package_name")
        normalized_namespace = _token(namespace, "namespace")
        normalized_version = _token(semantic_version, "semantic_version")
        semantic = {
            "contract": TYPE_SCHEMA_PACKAGE_ROOT_CONTRACT,
            "package_ref": normalized_package_ref,
            "package_name": normalized_package_name,
            "namespace": normalized_namespace,
            "semantic_version": normalized_version,
            "dependency_package_refs": list(dependencies),
            "definition_index": definition_index.to_wire(),
            "source_attribution_index": source_attribution_index.to_wire(),
        }
        return cls(
            normalized_package_ref,
            normalized_package_name,
            normalized_namespace,
            normalized_version,
            dependencies,
            definition_index,
            source_attribution_index,
            digest_payload(TYPE_SCHEMA_PACKAGE_ROOT_CONTRACT, semantic),
        )

    def semantic_wire(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "package_ref": self.package_ref,
            "package_name": self.package_name,
            "namespace": self.namespace,
            "semantic_version": self.semantic_version,
            "dependency_package_refs": list(self.dependency_package_refs),
            "definition_index": self.definition_index.to_wire(),
            "source_attribution_index": self.source_attribution_index.to_wire(),
        }

    def to_wire(self) -> dict[str, object]:
        return {**self.semantic_wire(), "package_root_ref": self.package_root_ref}

    def to_body(self) -> PersistentBodyAuthority:
        return PersistentBodyAuthority.from_wire(
            schema=self.contract,
            ref_field="package_root_ref",
            authority_ref=self.package_root_ref,
            wire=self.to_wire(),
        )


@dataclass(frozen=True, slots=True)
class TypeOwnerBinding:
    type_ref: str
    package_ref: str
    owner_ref: str
    contract: str = TYPE_OWNER_BINDING_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != TYPE_OWNER_BINDING_CONTRACT:
            raise TypeSchemaCompositionError("owner binding contract unsupported")
        object.__setattr__(self, "type_ref", _token(self.type_ref, "type_ref"))
        object.__setattr__(self, "package_ref", _token(self.package_ref, "package_ref"))
        expected = digest_payload(self.contract, self.semantic_wire())
        if self.owner_ref != expected:
            raise TypeSchemaCompositionError(f"owner_ref mismatch; expected {expected}")

    @classmethod
    def create(cls, *, type_ref: str, package_ref: str) -> TypeOwnerBinding:
        semantic = {
            "contract": TYPE_OWNER_BINDING_CONTRACT,
            "type_ref": _token(type_ref, "type_ref"),
            "package_ref": _token(package_ref, "package_ref"),
        }
        value = object.__new__(cls)
        object.__setattr__(value, "type_ref", semantic["type_ref"])
        object.__setattr__(value, "package_ref", semantic["package_ref"])
        object.__setattr__(
            value,
            "owner_ref",
            _prevalidated_digest(TYPE_OWNER_BINDING_CONTRACT, semantic),
        )
        object.__setattr__(value, "contract", TYPE_OWNER_BINDING_CONTRACT)
        return value

    def semantic_wire(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "type_ref": self.type_ref,
            "package_ref": self.package_ref,
        }

    def to_wire(self) -> dict[str, object]:
        return {**self.semantic_wire(), "owner_ref": self.owner_ref}

    def to_body(self) -> PersistentBodyAuthority:
        return PersistentBodyAuthority.from_wire(
            schema=self.contract,
            ref_field="owner_ref",
            authority_ref=self.owner_ref,
            wire=self.to_wire(),
        )


@dataclass(frozen=True, slots=True)
class TypeSchemaCatalogRoot:
    target_package_ref: str
    package_index: PersistentIndexRoot
    owner_index: PersistentIndexRoot
    package_count: int
    owner_count: int
    catalog_ref: str
    contract: str = TYPE_SCHEMA_CATALOG_ROOT_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != TYPE_SCHEMA_CATALOG_ROOT_CONTRACT:
            raise TypeSchemaCompositionError("catalog root contract unsupported")
        object.__setattr__(
            self,
            "target_package_ref",
            _token(self.target_package_ref, "target_package_ref"),
        )
        for value, expected in (
            (self.package_index, "type-schema:catalog:packages"),
            (self.owner_index, "type-schema:catalog:owners"),
        ):
            if not isinstance(value, PersistentIndexRoot) or value.keyspace != expected:
                raise TypeSchemaCompositionError(
                    f"catalog index keyspace must be {expected!r}"
                )
        for field in ("package_count", "owner_count"):
            value = getattr(self, field)
            if type(value) is not int or value < 0:
                raise TypeSchemaCompositionError(f"{field} must be non-negative int")
        if self.package_count != self.package_index.binding_count:
            raise TypeSchemaCompositionError("package count/index mismatch")
        if self.owner_count != self.owner_index.binding_count:
            raise TypeSchemaCompositionError("owner count/index mismatch")
        expected = digest_payload(self.contract, self.semantic_wire())
        if self.catalog_ref != expected:
            raise TypeSchemaCompositionError(
                f"catalog_ref mismatch; expected {expected}"
            )

    @classmethod
    def create(
        cls,
        *,
        target_package_ref: str,
        package_index: PersistentIndexRoot,
        owner_index: PersistentIndexRoot,
    ) -> TypeSchemaCatalogRoot:
        normalized_target = _token(target_package_ref, "target_package_ref")
        package_count = package_index.binding_count
        owner_count = owner_index.binding_count
        semantic = {
            "contract": TYPE_SCHEMA_CATALOG_ROOT_CONTRACT,
            "target_package_ref": normalized_target,
            "package_index": package_index.to_wire(),
            "owner_index": owner_index.to_wire(),
            "package_count": package_count,
            "owner_count": owner_count,
        }
        return cls(
            normalized_target,
            package_index,
            owner_index,
            package_count,
            owner_count,
            digest_payload(TYPE_SCHEMA_CATALOG_ROOT_CONTRACT, semantic),
        )

    def semantic_wire(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "target_package_ref": self.target_package_ref,
            "package_index": self.package_index.to_wire(),
            "owner_index": self.owner_index.to_wire(),
            "package_count": self.package_count,
            "owner_count": self.owner_count,
        }

    def to_wire(self) -> dict[str, object]:
        return {**self.semantic_wire(), "catalog_ref": self.catalog_ref}


def _create_prevalidated_package_root(
    context: _MetaTypeSchemaOperationContext,
    *,
    package_ref: str,
    package_name: str,
    namespace: str,
    semantic_version: str,
    dependency_package_refs: tuple[str, ...],
    definition_index: PersistentIndexRoot,
    source_attribution_index: PersistentIndexRoot,
) -> TypeSchemaPackageRoot:
    _require_meta_type_schema_operation(context)
    semantic = {
        "contract": TYPE_SCHEMA_PACKAGE_ROOT_CONTRACT,
        "package_ref": package_ref,
        "package_name": package_name,
        "namespace": namespace,
        "semantic_version": semantic_version,
        "dependency_package_refs": list(dependency_package_refs),
        "definition_index": definition_index.to_wire(),
        "source_attribution_index": source_attribution_index.to_wire(),
    }
    value = object.__new__(TypeSchemaPackageRoot)
    object.__setattr__(value, "package_ref", package_ref)
    object.__setattr__(value, "package_name", package_name)
    object.__setattr__(value, "namespace", namespace)
    object.__setattr__(value, "semantic_version", semantic_version)
    object.__setattr__(value, "dependency_package_refs", dependency_package_refs)
    object.__setattr__(value, "definition_index", definition_index)
    object.__setattr__(value, "source_attribution_index", source_attribution_index)
    object.__setattr__(
        value,
        "package_root_ref",
        _prevalidated_digest(TYPE_SCHEMA_PACKAGE_ROOT_CONTRACT, semantic),
    )
    object.__setattr__(value, "contract", TYPE_SCHEMA_PACKAGE_ROOT_CONTRACT)
    return value


def _create_prevalidated_catalog_root(
    context: _MetaTypeSchemaOperationContext,
    *,
    target_package_ref: str,
    package_index: PersistentIndexRoot,
    owner_index: PersistentIndexRoot,
) -> TypeSchemaCatalogRoot:
    _require_meta_type_schema_operation(context)
    semantic = {
        "contract": TYPE_SCHEMA_CATALOG_ROOT_CONTRACT,
        "target_package_ref": target_package_ref,
        "package_index": package_index.to_wire(),
        "owner_index": owner_index.to_wire(),
        "package_count": package_index.binding_count,
        "owner_count": owner_index.binding_count,
    }
    value = object.__new__(TypeSchemaCatalogRoot)
    object.__setattr__(value, "target_package_ref", target_package_ref)
    object.__setattr__(value, "package_index", package_index)
    object.__setattr__(value, "owner_index", owner_index)
    object.__setattr__(value, "package_count", package_index.binding_count)
    object.__setattr__(value, "owner_count", owner_index.binding_count)
    object.__setattr__(
        value,
        "catalog_ref",
        _prevalidated_digest(TYPE_SCHEMA_CATALOG_ROOT_CONTRACT, semantic),
    )
    object.__setattr__(value, "contract", TYPE_SCHEMA_CATALOG_ROOT_CONTRACT)
    return value


@dataclass(frozen=True, slots=True)
class ComposedTypeOwnerEvidence:
    type_ref: str
    package_ref: str
    owner: PersistentBodyCoordinate
    package: PersistentBodyCoordinate
    definition: PersistentBodyCoordinate

    def __post_init__(self) -> None:
        object.__setattr__(self, "type_ref", _token(self.type_ref, "type_ref"))
        object.__setattr__(self, "package_ref", _token(self.package_ref, "package_ref"))
        for value in (self.owner, self.package, self.definition):
            if not isinstance(value, PersistentBodyCoordinate):
                raise TypeError("owner evidence requires body coordinates")
        expected_owner = (
            TypeOwnerBinding.create(
                type_ref=self.type_ref, package_ref=self.package_ref
            )
            .to_body()
            .coordinate
        )
        if self.owner != expected_owner:
            raise TypeSchemaCompositionError(
                "owner coordinate does not bind exact type/package ownership"
            )

    def to_wire(self) -> dict[str, object]:
        return {
            "type_ref": self.type_ref,
            "package_ref": self.package_ref,
            "owner": self.owner.to_wire(),
            "package": self.package.to_wire(),
            "definition": self.definition.to_wire(),
        }


@dataclass(frozen=True, slots=True)
class ComposedPackageEvidence:
    package_ref: str
    package: TypeSchemaPackageRoot
    coordinate: PersistentBodyCoordinate

    def __post_init__(self) -> None:
        object.__setattr__(self, "package_ref", _token(self.package_ref, "package_ref"))
        if not isinstance(self.package, TypeSchemaPackageRoot):
            raise TypeError("package evidence requires TypeSchemaPackageRoot")
        if not isinstance(self.coordinate, PersistentBodyCoordinate):
            raise TypeError("package evidence requires body coordinate")
        if self.package.package_ref != self.package_ref:
            raise TypeSchemaCompositionError("package evidence ref mismatch")
        if self.coordinate != self.package.to_body().coordinate:
            raise TypeSchemaCompositionError(
                "package coordinate does not bind exact package root"
            )

    def to_wire(self) -> dict[str, object]:
        return {
            "package_ref": self.package_ref,
            "package": self.package.to_wire(),
            "coordinate": self.coordinate.to_wire(),
        }


@dataclass(frozen=True, slots=True)
class TypeSchemaComposedSlice:
    catalog: TypeSchemaCatalogRoot
    target_package_ref: str
    dependency_package_refs: tuple[str, ...]
    root_type_refs: tuple[str, ...]
    packages: tuple[ComposedPackageEvidence, ...]
    definitions: tuple[TypeDefinitionFragment, ...]
    owners: tuple[ComposedTypeOwnerEvidence, ...]
    membership_proofs: PersistentIndexProofBundle
    slice_ref: str
    contract: str = TYPE_SCHEMA_COMPOSED_SLICE_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != TYPE_SCHEMA_COMPOSED_SLICE_CONTRACT:
            raise TypeSchemaCompositionError("composed slice contract unsupported")
        if not isinstance(self.catalog, TypeSchemaCatalogRoot):
            raise TypeError("composed slice requires exact catalog root")
        object.__setattr__(
            self,
            "target_package_ref",
            _token(self.target_package_ref, "target_package_ref"),
        )
        dependencies = _tokens(self.dependency_package_refs, "dependency_package_refs")
        roots = _tokens(self.root_type_refs, "root_type_refs")
        if not roots:
            raise TypeSchemaCompositionError("composed slice requires root types")
        if self.catalog.target_package_ref != self.target_package_ref:
            raise TypeSchemaCompositionError("slice target differs from catalog target")
        if not isinstance(self.membership_proofs, PersistentIndexProofBundle):
            raise TypeError("slice membership proofs must be exact proof bundle")
        if (
            type(self.packages) is not tuple
            or type(self.definitions) is not tuple
            or type(self.owners) is not tuple
        ):
            raise TypeSchemaCompositionError("slice values must be immutable tuples")
        packages = tuple(sorted(self.packages, key=lambda item: item.package_ref))
        definitions = tuple(sorted(self.definitions, key=lambda item: item.type_ref))
        owners = tuple(sorted(self.owners, key=lambda item: item.type_ref))
        if (
            packages != self.packages
            or definitions != self.definitions
            or owners != self.owners
        ):
            raise TypeSchemaCompositionError("slice values must be sorted")
        package_by_ref = {value.package_ref: value for value in packages}
        expected_package_refs = {self.target_package_ref, *dependencies}
        if (
            len(package_by_ref) != len(packages)
            or set(package_by_ref) != expected_package_refs
        ):
            raise TypeSchemaCompositionError(
                "slice package evidence differs from target/dependency set"
            )
        reachable = _package_closure(package_by_ref, self.target_package_ref)
        if reachable != expected_package_refs:
            raise TypeSchemaCompositionError(
                "slice package evidence is not the exact reachable closure"
            )
        by_ref = {value.type_ref: value for value in definitions}
        if len(by_ref) != len(definitions):
            raise TypeSchemaCompositionError("slice contains duplicate type_ref")
        owner_refs = tuple(value.type_ref for value in owners)
        if owner_refs != tuple(by_ref):
            raise TypeSchemaCompositionError("slice owner/definition sets differ")
        exact = _definition_closure(by_ref, roots)
        if exact != set(by_ref):
            raise TypeSchemaCompositionError(
                "slice contains definitions outside closure"
            )
        for owner in owners:
            package_evidence = package_by_ref.get(owner.package_ref)
            if package_evidence is None:
                raise TypeSchemaCompositionError("slice owner package is unreachable")
            if owner.package != package_evidence.coordinate:
                raise TypeSchemaCompositionError(
                    "owner package coordinate does not bind package evidence"
                )
            if owner.definition != by_ref[owner.type_ref].to_body().coordinate:
                raise TypeSchemaCompositionError(
                    "owner definition coordinate does not bind definition fragment"
                )
        expected_memberships = {
            (
                self.catalog.package_index.root_ref,
                package.package_ref,
                package.coordinate.coordinate_ref,
            )
            for package in packages
        }
        expected_memberships.update(
            (
                self.catalog.owner_index.root_ref,
                owner.type_ref,
                owner.owner.coordinate_ref,
            )
            for owner in owners
        )
        expected_memberships.update(
            (
                package_by_ref[owner.package_ref].package.definition_index.root_ref,
                owner.type_ref,
                owner.definition.coordinate_ref,
            )
            for owner in owners
        )
        actual_memberships = {
            (
                proof.root.root_ref,
                proof.key,
                proof.value.coordinate_ref,
            )
            for proof in self.membership_proofs.memberships
        }
        if actual_memberships != expected_memberships or len(actual_memberships) != len(
            self.membership_proofs.memberships
        ):
            raise TypeSchemaCompositionError(
                "slice membership proofs differ from exact catalog/package bindings"
            )
        expected = digest_payload(self.contract, self.semantic_wire())
        if self.slice_ref != expected:
            raise TypeSchemaCompositionError(f"slice_ref mismatch; expected {expected}")

    @classmethod
    def create(
        cls,
        *,
        catalog: TypeSchemaCatalogRoot,
        target_package_ref: str,
        dependency_package_refs: tuple[str, ...],
        root_type_refs: tuple[str, ...],
        packages: tuple[ComposedPackageEvidence, ...],
        definitions: tuple[TypeDefinitionFragment, ...],
        owners: tuple[ComposedTypeOwnerEvidence, ...],
        membership_proofs: PersistentIndexProofBundle,
    ) -> TypeSchemaComposedSlice:
        dependencies = tuple(sorted(dependency_package_refs))
        roots = tuple(sorted(root_type_refs))
        packages = tuple(sorted(packages, key=lambda item: item.package_ref))
        definitions = tuple(sorted(definitions, key=lambda item: item.type_ref))
        owners = tuple(sorted(owners, key=lambda item: item.type_ref))
        if not isinstance(catalog, TypeSchemaCatalogRoot):
            raise TypeError("catalog must be TypeSchemaCatalogRoot")
        normalized_target = _token(target_package_ref, "target_package_ref")
        semantic = {
            "contract": TYPE_SCHEMA_COMPOSED_SLICE_CONTRACT,
            "catalog": catalog.to_wire(),
            "target_package_ref": normalized_target,
            "dependency_package_refs": list(dependencies),
            "root_type_refs": list(roots),
            "packages": [item.to_wire() for item in packages],
            "definitions": [item.to_wire() for item in definitions],
            "owners": [item.to_wire() for item in owners],
            "membership_proofs": membership_proofs.to_wire(),
        }
        return cls(
            catalog,
            normalized_target,
            dependencies,
            roots,
            packages,
            definitions,
            owners,
            membership_proofs,
            digest_payload(TYPE_SCHEMA_COMPOSED_SLICE_CONTRACT, semantic),
        )

    def semantic_wire(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "catalog": self.catalog.to_wire(),
            "target_package_ref": self.target_package_ref,
            "dependency_package_refs": list(self.dependency_package_refs),
            "root_type_refs": list(self.root_type_refs),
            "packages": [item.to_wire() for item in self.packages],
            "definitions": [item.to_wire() for item in self.definitions],
            "owners": [item.to_wire() for item in self.owners],
            "membership_proofs": self.membership_proofs.to_wire(),
        }

    @property
    def catalog_ref(self) -> str:
        return self.catalog.catalog_ref

    def to_wire(self) -> dict[str, object]:
        return {**self.semantic_wire(), "slice_ref": self.slice_ref}


@dataclass(frozen=True, slots=True)
class TypeSchemaComposedSliceResult:
    slice: TypeSchemaComposedSlice
    observation: PositiveReadObservation


_FRESH_COMPOSED_SLICE_BYTES: dict[int, tuple[TypeSchemaComposedSlice, bytes]] = {}


def _take_prevalidated_composed_slice_bytes(
    value: TypeSchemaComposedSlice,
) -> bytes:
    retained = _FRESH_COMPOSED_SLICE_BYTES.pop(id(value), None)
    if retained is None or retained[0] is not value:
        raise TypeSchemaCompositionError("fresh composed-slice bytes are absent")
    return retained[1]


def _prevalidated_package_evidence(
    context: _MetaTypeSchemaOperationContext,
    package: TypeSchemaPackageRoot,
    coordinate: PersistentBodyCoordinate,
) -> ComposedPackageEvidence:
    _require_meta_type_schema_operation(context)
    result = object.__new__(ComposedPackageEvidence)
    object.__setattr__(result, "package_ref", package.package_ref)
    object.__setattr__(result, "package", package)
    object.__setattr__(result, "coordinate", coordinate)
    return result


def _prevalidated_owner_evidence(
    context: _MetaTypeSchemaOperationContext,
    owner: TypeOwnerBinding,
    owner_coordinate: PersistentBodyCoordinate,
    package_coordinate: PersistentBodyCoordinate,
    definition_coordinate: PersistentBodyCoordinate,
) -> ComposedTypeOwnerEvidence:
    _require_meta_type_schema_operation(context)
    result = object.__new__(ComposedTypeOwnerEvidence)
    object.__setattr__(result, "type_ref", owner.type_ref)
    object.__setattr__(result, "package_ref", owner.package_ref)
    object.__setattr__(result, "owner", owner_coordinate)
    object.__setattr__(result, "package", package_coordinate)
    object.__setattr__(result, "definition", definition_coordinate)
    return result


def _create_prevalidated_composed_slice(
    context: _MetaTypeSchemaOperationContext,
    *,
    catalog: TypeSchemaCatalogRoot,
    target_package_ref: str,
    dependency_package_refs: tuple[str, ...],
    root_type_refs: tuple[str, ...],
    packages: tuple[ComposedPackageEvidence, ...],
    definitions: tuple[TypeDefinitionFragment, ...],
    owners: tuple[ComposedTypeOwnerEvidence, ...],
    membership_proofs: PersistentIndexProofBundle,
    membership_proofs_wire: bytes | None = None,
) -> TypeSchemaComposedSlice:
    _require_meta_type_schema_operation(context)
    dependencies = tuple(sorted(dependency_package_refs))
    roots = tuple(sorted(root_type_refs))
    ordered_packages = tuple(sorted(packages, key=lambda item: item.package_ref))
    ordered_definitions = tuple(sorted(definitions, key=lambda item: item.type_ref))
    ordered_owners = tuple(sorted(owners, key=lambda item: item.type_ref))
    proof_marker = "__aware_meta_type_schema_prevalidated_proof_bundle__"
    semantic = {
        "contract": TYPE_SCHEMA_COMPOSED_SLICE_CONTRACT,
        "catalog": catalog.to_wire(),
        "target_package_ref": target_package_ref,
        "dependency_package_refs": list(dependencies),
        "root_type_refs": list(roots),
        "packages": [item.to_wire() for item in ordered_packages],
        "definitions": [item.to_wire() for item in ordered_definitions],
        "owners": [item.to_wire() for item in ordered_owners],
        "membership_proofs": proof_marker,
    }
    semantic_template = _prevalidated_json(semantic)
    encoded_marker = b'"' + proof_marker.encode("ascii") + b'"'
    if semantic_template.count(encoded_marker) != 1:
        raise AssertionError("composed-slice proof marker must be unique")
    semantic_bytes = semantic_template.replace(
        encoded_marker,
        (
            _prevalidated_json(membership_proofs.to_wire())
            if membership_proofs_wire is None
            else membership_proofs_wire
        ),
        1,
    )
    result = object.__new__(TypeSchemaComposedSlice)
    object.__setattr__(result, "catalog", catalog)
    object.__setattr__(result, "target_package_ref", target_package_ref)
    object.__setattr__(result, "dependency_package_refs", dependencies)
    object.__setattr__(result, "root_type_refs", roots)
    object.__setattr__(result, "packages", ordered_packages)
    object.__setattr__(result, "definitions", ordered_definitions)
    object.__setattr__(result, "owners", ordered_owners)
    object.__setattr__(result, "membership_proofs", membership_proofs)
    object.__setattr__(
        result,
        "slice_ref",
        "sha256:"
        + hashlib.sha256(
            TYPE_SCHEMA_COMPOSED_SLICE_CONTRACT.encode("utf-8") + b"\n" + semantic_bytes
        ).hexdigest(),
    )
    object.__setattr__(result, "contract", TYPE_SCHEMA_COMPOSED_SLICE_CONTRACT)
    encoded_slice_ref = _prevalidated_json(result.slice_ref)
    insertion = b',"target_package_ref":'
    prefix, marker, suffix = semantic_bytes.rpartition(insertion)
    if not marker:
        raise AssertionError("composed-slice target marker is absent")
    canonical_bytes = prefix + b',"slice_ref":' + encoded_slice_ref + marker + suffix
    _FRESH_COMPOSED_SLICE_BYTES[id(result)] = (result, canonical_bytes)
    return result


def resolve_composed_slice(
    catalog: TypeSchemaCatalogRoot,
    *,
    root_type_refs: tuple[str, ...],
    reader: TypeSchemaPositiveReaderCapability,
    request_ref: str,
    _operation_context: object | None = None,
) -> TypeSchemaComposedSliceResult:
    admission_started = perf_counter_ns()
    if type(reader) is not TypeSchemaPositiveReaderCapability:
        raise TypeSchemaCompositionError(
            "reader must be exact TypeSchemaPositiveReaderCapability"
        )
    if (
        type(request_ref) is not str
        or not request_ref
        or request_ref.strip() != request_ref
    ):
        raise TypeSchemaCompositionError("request_ref must be normalized text")
    retained_request_ref = object.__getattribute__(reader, "_request_ref")
    if type(retained_request_ref) is not str or retained_request_ref != request_ref:
        raise TypeSchemaCompositionError("reader capability belongs to another request")
    operands = (catalog, root_type_refs)
    try:
        operand_snapshot = (
            "composition.resolve",
            _flat_protected_operand_guard(operands),
        )
    except TypeSchemaPersistentIndexError as error:
        raise TypeSchemaCompositionError(
            f"composition operand admission failed: {error}"
        ) from error
    if _operation_context is None:
        admitted_catalog, admitted_roots = copy.deepcopy(operands)
    else:
        from .type_schema_operation import (
            _is_recorded_type_schema_catalog_successor,
        )

        if not _is_recorded_type_schema_catalog_successor(
            _operation_context, catalog  # pyright: ignore[reportArgumentType]
        ):
            raise TypeSchemaCompositionError(
                "composition catalog is not this operation's admitted successor"
            )
        # This successor was freshly assembled and sealed inside the same
        # still-active Meta operation. The surrounding operand snapshot and
        # terminal check protect it; copying the complete catalog here would
        # traverse the same package graph without creating new authority.
        admitted_catalog, admitted_roots = catalog, root_type_refs
    admission_finished = perf_counter_ns()
    with _meta_type_schema_operation(
        operation_ref="composition.resolve",
        operands=operands,
        reader=reader,
        request_ref=request_ref,
        operand_snapshot=operand_snapshot,
    ) as context:
        construction_started = perf_counter_ns()
        result = _resolve_composed_slice(
            context,
            admitted_catalog,
            root_type_refs=admitted_roots,
            reader=reader,
            request_ref=request_ref,
            decoded_nodes=(
                None
                if _operation_context is None
                else _operation_decoded_nodes(_operation_context)
            ),
        )
        construction_finished = perf_counter_ns()
        try:
            _require_meta_type_schema_operation_operands(
                context,
                operation_ref="composition.resolve",
                operands=operands,
            )
        except TypeSchemaPersistentIndexError as error:
            raise TypeSchemaCompositionError(
                f"composition operands changed after admission: {error}"
            ) from error
        verification_finished = perf_counter_ns()
    # Every graph reachable from the result was either decoded from an exact
    # positive read or derived from the detached admitted catalog above. No
    # caller-owned graph is retained, so another full-closure copy would only
    # amplify the positive proof graph.
    canonical_bytes = _take_prevalidated_composed_slice_bytes(result.slice)
    if _operation_context is not None:
        from .type_schema_operation import (
            _record_type_schema_composed_slice,
            _record_type_schema_operation_diagnostic,
        )

        record_started = perf_counter_ns()
        _record_type_schema_composed_slice(
            _operation_context,  # pyright: ignore[reportArgumentType]
            result.slice,
            canonical_bytes,
        )
        record_finished = perf_counter_ns()
        for name, duration_ns in (
            ("meta_composed_operand_admission", admission_finished - admission_started),
            ("meta_composed_construction", construction_finished - construction_started),
            (
                "meta_composed_terminal_verification",
                verification_finished - construction_finished,
            ),
            ("meta_composed_result_record", record_finished - record_started),
        ):
            _record_type_schema_operation_diagnostic(
                _operation_context,  # pyright: ignore[reportArgumentType]
                name,
                duration_ns,
            )
    return result


def _operation_decoded_nodes(
    operation: object,
) -> dict[
    str,
    tuple[
        tuple[str, str, str, str, str, int, str, str],
        bytes,
        PersistentIndexNode,
    ],
]:
    from .type_schema_operation import _type_schema_operation_decoded_nodes

    return _type_schema_operation_decoded_nodes(operation)  # type: ignore[arg-type]


def _resolve_composed_slice(
    context: _MetaTypeSchemaOperationContext,
    catalog: TypeSchemaCatalogRoot,
    *,
    root_type_refs: tuple[str, ...],
    reader: TypeSchemaPositiveReaderCapability,
    request_ref: str,
    decoded_nodes: dict[
        str,
        tuple[
            tuple[str, str, str, str, str, int, str, str],
            bytes,
            PersistentIndexNode,
        ],
    ]
    | None = None,
) -> TypeSchemaComposedSliceResult:
    """Resolve only the positive target-reachable package and type closure."""

    _require_meta_type_schema_operation(context)
    from .composition_codec import (
        decode_definition_fragment,
        decode_package_root,
        decode_type_owner_binding,
    )

    if not isinstance(catalog, TypeSchemaCatalogRoot):
        raise TypeError("catalog must be TypeSchemaCatalogRoot")
    roots = _tokens(tuple(sorted(root_type_refs)), "root_type_refs")
    if not roots:
        raise TypeSchemaCompositionError("root_type_refs must not be empty")
    body_observation = PositiveReadObservation()
    memberships: list[PersistentIndexMembershipProof] = []
    packages: dict[str, tuple[TypeSchemaPackageRoot, PersistentBodyCoordinate]] = {}
    visiting: set[str] = set()
    if decoded_nodes is None:
        decoded_nodes = {}
    read_state = _state(reader, request_ref, decoded_nodes=decoded_nodes)

    def prove(
        root: PersistentIndexRoot,
        *,
        key: str,
    ) -> PersistentIndexMembershipProof | None:
        """Prove membership while sharing only decoded node bytes this operation."""

        _require_meta_type_schema_operation(context)
        path = key_digest_path(key)
        coordinate: PersistentBodyCoordinate | None = root.root_node
        node_refs: list[str] = []
        for depth in range(PERSISTENT_INDEX_DEPTH + 1):
            if coordinate is None:
                return None
            retained = read_state.cache.get(coordinate.coordinate_ref)
            node = read_state.node(
                coordinate,
                keyspace=root.keyspace,
                depth=depth,
                path=path[:depth],
            )
            if retained is not None:
                read_state.cache_hits += 1
                read_state.max_lookup_depth = max(
                    read_state.max_lookup_depth, depth
                )
            node_refs.append(node.node_ref)
            if depth == PERSISTENT_INDEX_DEPTH:
                if node.key != key:
                    raise TypeSchemaCompositionError("SHA-256 index key collision")
                if node.value is None:
                    raise AssertionError("persistent leaf must contain a value")
                proof = _create_prevalidated_membership_proof(
                    context,
                    root=root,
                    key=key,
                    value=node.value,
                    node_refs=tuple(node_refs),
                )
                return proof
            child = next(
                (item for item in node.children if item.nibble == path[depth]), None
            )
            coordinate = None if child is None else child.node
        raise AssertionError("fixed-depth membership proof did not terminate")

    def load_package(package_ref: str) -> None:
        nonlocal body_observation
        if package_ref in visiting:
            raise TypeSchemaCompositionError("package dependency cycle")
        if package_ref in packages:
            return
        visiting.add(package_ref)
        proof = prove(
            catalog.package_index,
            key=package_ref,
        )
        if proof is None:
            raise TypeSchemaCompositionError(f"missing package {package_ref!r}")
        memberships.append(proof)
        coordinate = proof.value
        body, read_observation = reader.read_exact(
            request_ref=request_ref,
            expected=coordinate,
            lookup_depth=0,
        )
        body_observation = body_observation.plus(read_observation)
        package = decode_package_root(body.canonical_bytes)
        if package.package_ref != package_ref:
            raise TypeSchemaCompositionError("package index key/body mismatch")
        for dependency in package.dependency_package_refs:
            load_package(dependency)
        packages[package_ref] = (package, coordinate)
        visiting.remove(package_ref)

    load_package(catalog.target_package_ref)
    dependency_refs = tuple(sorted(set(packages) - {catalog.target_package_ref}))
    pending = list(reversed(roots))
    definitions: dict[str, TypeDefinitionFragment] = {}
    owners: dict[str, ComposedTypeOwnerEvidence] = {}
    while pending:
        type_ref = pending.pop()
        if type_ref in definitions:
            continue
        owner_proof = prove(
            catalog.owner_index,
            key=type_ref,
        )
        if owner_proof is None:
            raise TypeSchemaCompositionError(f"unresolved owner for {type_ref!r}")
        memberships.append(owner_proof)
        owner_coordinate = owner_proof.value
        owner_body, read_observation = reader.read_exact(
            request_ref=request_ref,
            expected=owner_coordinate,
            lookup_depth=0,
        )
        body_observation = body_observation.plus(read_observation)
        owner = decode_type_owner_binding(owner_body.canonical_bytes)
        if owner.type_ref != type_ref:
            raise TypeSchemaCompositionError("owner index key/body mismatch")
        package_entry = packages.get(owner.package_ref)
        if package_entry is None:
            raise TypeSchemaCompositionError("type owner is outside reachable packages")
        package, package_coordinate = package_entry
        definition_proof = prove(
            package.definition_index,
            key=type_ref,
        )
        if definition_proof is None:
            raise TypeSchemaCompositionError("owner package lacks definition")
        memberships.append(definition_proof)
        definition_coordinate = definition_proof.value
        definition_body, read_observation = reader.read_exact(
            request_ref=request_ref,
            expected=definition_coordinate,
            lookup_depth=0,
        )
        body_observation = body_observation.plus(read_observation)
        definition = decode_definition_fragment(definition_body.canonical_bytes)
        if definition.type_ref != type_ref:
            raise TypeSchemaCompositionError("definition index key/body mismatch")
        definitions[type_ref] = definition
        owners[type_ref] = _prevalidated_owner_evidence(
            context,
            owner,
            owner_coordinate,
            package_coordinate,
            definition_coordinate,
        )
        pending.extend(
            sorted(
                set(definition.referenced_type_refs) - set(definitions), reverse=True
            )
        )
    proof_nodes = tuple(read_state.cache.values())
    proof_node_refs = {node.node_ref for node in proof_nodes}
    proof_bundle, proof_bundle_wire = _create_prevalidated_proof_bundle_with_wire(
        context,
        memberships=tuple(memberships),
        nodes=proof_nodes,
        node_wires=(
            None
            if read_state.decoded_nodes is None
            else {
                retained[2].node_ref: (retained[2], retained[1])
                for retained in read_state.decoded_nodes.values()
                if retained[2].node_ref in proof_node_refs
            }
        ),
    )
    value = _create_prevalidated_composed_slice(
        context,
        catalog=catalog,
        target_package_ref=catalog.target_package_ref,
        dependency_package_refs=dependency_refs,
        root_type_refs=roots,
        packages=tuple(
            _prevalidated_package_evidence(context, package, coordinate)
            for package, coordinate in packages.values()
        ),
        definitions=tuple(definitions.values()),
        owners=tuple(owners.values()),
        membership_proofs=proof_bundle,
        membership_proofs_wire=proof_bundle_wire,
    )
    return TypeSchemaComposedSliceResult(
        value, read_state.observation.plus(body_observation)
    )


def _definition_closure(
    definitions: dict[str, TypeDefinitionFragment], roots: tuple[str, ...]
) -> set[str]:
    pending = list(roots)
    result: set[str] = set()
    while pending:
        type_ref = pending.pop()
        if type_ref in result:
            continue
        definition = definitions.get(type_ref)
        if definition is None:
            raise TypeSchemaCompositionError(f"unresolved type ref {type_ref!r}")
        result.add(type_ref)
        pending.extend(definition.referenced_type_refs)
    return result


def _package_closure(
    packages: dict[str, ComposedPackageEvidence], target_package_ref: str
) -> set[str]:
    visiting: set[str] = set()
    visited: set[str] = set()

    pending: list[tuple[str, bool]] = [(target_package_ref, False)]
    while pending:
        package_ref, exiting = pending.pop()
        if exiting:
            visiting.remove(package_ref)
            visited.add(package_ref)
            continue
        if package_ref in visiting:
            raise TypeSchemaCompositionError("slice package dependency cycle")
        if package_ref in visited:
            continue
        evidence = packages.get(package_ref)
        if evidence is None:
            raise TypeSchemaCompositionError(
                f"slice package dependency is missing: {package_ref!r}"
            )
        visiting.add(package_ref)
        pending.append((package_ref, True))
        pending.extend(
            (dependency_ref, False)
            for dependency_ref in reversed(evidence.package.dependency_package_refs)
        )
    return visited


__all__ = [
    "TYPE_OWNER_BINDING_CONTRACT",
    "TYPE_SCHEMA_CATALOG_ROOT_CONTRACT",
    "TYPE_SCHEMA_COMPOSED_SLICE_CONTRACT",
    "TYPE_SCHEMA_PACKAGE_ROOT_CONTRACT",
    "ComposedPackageEvidence",
    "ComposedTypeOwnerEvidence",
    "TypeOwnerBinding",
    "TypeSchemaCatalogRoot",
    "TypeSchemaComposedSlice",
    "TypeSchemaComposedSliceResult",
    "TypeSchemaCompositionError",
    "TypeSchemaPackageRoot",
    "resolve_composed_slice",
]
