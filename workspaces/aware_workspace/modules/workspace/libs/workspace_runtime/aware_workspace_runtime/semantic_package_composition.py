"""Input-only semantic-package composition child authority.

The value in this module is a child of an existing Workspace operation. It
does not create an operation, source authority, parser result, semantic result,
renderer result, or publication authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import cast

from .semantic_package_result_catalog import WorkspaceSemanticResultCatalogRoot

WORKSPACE_SEMANTIC_PACKAGE_COMPOSITION_CONTRACT = (
    "aware.workspace.semantic-package-composition.v2"
)
CONTENT_ADDRESSED_AUTHORITY_REF_SCHEMA = "aware.authority.content-addressed-ref.v1"
WORKSPACE_OPERATION_AUTHORITY_REF_KIND = "workspace_operation_authority_ref"
WORKSPACE_OPERATION_AUTHORITY_INPUT_ROLE = "operation"
WORKSPACE_SEMANTIC_PACKAGE_AUTHORITY_GRADE = "portable_input"
WORKSPACE_SEMANTIC_PACKAGE_NON_CLAIMS = (
    "canonical_commit",
    "code_package_delta",
    "function_impl_execution",
    "graph_effect",
    "materialization",
    "ontology_meaning",
    "parsed_aware",
    "renderer_output",
    "result_abi",
    "result_schema",
    "source_authority",
    "workspace_operation",
)

_DIGEST_PREFIX = "sha256:"
_PRIOR_KINDS = frozenset({"exact_refs", "typed_empty"})
_PRIOR_ROLES = frozenset({"artifact", "object_abi", "package", "schema"})
_REQUIRED_PACKAGE_PRIOR_ROLES = frozenset({"object_abi", "package", "schema"})
_SOURCE_MOVEMENT_KINDS = frozenset({"create", "delete", "update"})


class WorkspaceSemanticPackageCompositionError(ValueError):
    """Raised when semantic-package composition authority is not exact."""


@dataclass(frozen=True, slots=True)
class WorkspaceParentOperationAuthorityRef:
    """Exact foreign value of the already-existing Workspace operation ref."""

    input_name: str
    input_role: str
    ref: str
    digest: str
    size: int
    authority_digest: str
    schema: str = CONTENT_ADDRESSED_AUTHORITY_REF_SCHEMA
    ref_kind: str = WORKSPACE_OPERATION_AUTHORITY_REF_KIND

    def __post_init__(self) -> None:
        if self.schema != CONTENT_ADDRESSED_AUTHORITY_REF_SCHEMA:
            raise WorkspaceSemanticPackageCompositionError(
                "parent operation authority ref schema is unsupported"
            )
        input_name = _text(self.input_name, "parent operation input_name")
        if not input_name.startswith("workspace-operation:"):
            raise WorkspaceSemanticPackageCompositionError(
                "parent operation input_name is not a Workspace operation"
            )
        if self.input_role != WORKSPACE_OPERATION_AUTHORITY_INPUT_ROLE:
            raise WorkspaceSemanticPackageCompositionError(
                "parent operation input_role is unsupported"
            )
        if self.ref_kind != WORKSPACE_OPERATION_AUTHORITY_REF_KIND:
            raise WorkspaceSemanticPackageCompositionError(
                "parent operation ref kind is unsupported"
            )
        object.__setattr__(self, "input_name", input_name)
        object.__setattr__(self, "ref", _text(self.ref, "parent operation ref"))
        object.__setattr__(
            self,
            "digest",
            _digest_value(self.digest, "parent operation digest"),
        )
        _ = _non_negative(self.size, "parent operation size")
        authority_digest = _digest_value(
            self.authority_digest,
            "parent operation authority_digest",
        )
        expected = _authority_digest(self.identity_payload())
        if authority_digest != expected:
            raise WorkspaceSemanticPackageCompositionError(
                "parent operation authority digest mismatched"
            )
        object.__setattr__(self, "authority_digest", authority_digest)

    def identity_payload(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "input_name": self.input_name,
            "input_role": self.input_role,
            "ref_kind": self.ref_kind,
            "ref": self.ref,
            "digest": self.digest,
            "size": self.size,
        }

    def to_dict(self) -> dict[str, object]:
        return {**self.identity_payload(), "authority_digest": self.authority_digest}


@dataclass(frozen=True, slots=True, order=True)
class WorkspaceCapturedSemanticInput:
    """One exact create/update after-body captured by Workspace."""

    input_kind: str
    relative_path: str
    body_ref: str
    body_digest: str
    size_bytes: int

    def __post_init__(self) -> None:
        if self.input_kind not in {"aware_source", "manifest"}:
            raise WorkspaceSemanticPackageCompositionError(
                "captured input kind is unsupported"
            )
        object.__setattr__(
            self,
            "relative_path",
            _relative_path(self.relative_path, "captured input relative_path"),
        )
        if self.input_kind == "aware_source" and not self.relative_path.endswith(
            ".aware"
        ):
            raise WorkspaceSemanticPackageCompositionError(
                "captured aware source path must end in .aware"
            )
        if self.input_kind == "manifest" and not self.relative_path.endswith(".toml"):
            raise WorkspaceSemanticPackageCompositionError(
                "captured manifest path must end in .toml"
            )
        object.__setattr__(self, "body_ref", _text(self.body_ref, "body_ref"))
        object.__setattr__(
            self,
            "body_digest",
            _digest_value(self.body_digest, "body_digest"),
        )
        _ = _non_negative(self.size_bytes, "captured input size_bytes")

    def to_dict(self) -> dict[str, object]:
        return {
            "input_kind": self.input_kind,
            "relative_path": self.relative_path,
            "body_ref": self.body_ref,
            "body_digest": self.body_digest,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticPackageManifestAuthority:
    """Content-addressed current package-manifest authority, never its source body."""

    relative_path: str
    ref: str
    digest: str
    size_bytes: int

    def __post_init__(self) -> None:
        path = _relative_path(self.relative_path, "manifest relative_path")
        if not path.endswith(".toml"):
            raise WorkspaceSemanticPackageCompositionError(
                "semantic package manifest path must end in .toml"
            )
        object.__setattr__(self, "relative_path", path)
        object.__setattr__(self, "ref", _text(self.ref, "manifest ref"))
        object.__setattr__(
            self,
            "digest",
            _digest_value(self.digest, "manifest digest"),
        )
        _ = _non_negative(self.size_bytes, "manifest size_bytes")

    def to_dict(self) -> dict[str, object]:
        return {
            "relative_path": self.relative_path,
            "ref": self.ref,
            "digest": self.digest,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True, slots=True, order=True)
class WorkspaceSemanticSourceMovement:
    """One exact admitted source create/update/delete movement."""

    package_ref: str
    input_kind: str
    relative_path: str
    change_kind: str
    before_digest: str | None = None
    after_body: WorkspaceCapturedSemanticInput | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "package_ref", _text(self.package_ref, "package_ref"))
        if self.input_kind not in {"aware_source", "manifest"}:
            raise WorkspaceSemanticPackageCompositionError(
                "source movement input kind is unsupported"
            )
        path = _relative_path(self.relative_path, "source movement relative_path")
        expected_suffix = ".aware" if self.input_kind == "aware_source" else ".toml"
        if not path.endswith(expected_suffix):
            raise WorkspaceSemanticPackageCompositionError(
                "source movement path classification mismatched"
            )
        if self.change_kind not in _SOURCE_MOVEMENT_KINDS:
            raise WorkspaceSemanticPackageCompositionError(
                "source movement kind is unsupported"
            )
        before = self.before_digest
        body = self.after_body
        if self.change_kind == "create":
            if before is not None or body is None:
                raise WorkspaceSemanticPackageCompositionError(
                    "source create requires only an after-body"
                )
        elif self.change_kind == "update":
            if before is None or body is None:
                raise WorkspaceSemanticPackageCompositionError(
                    "source update requires before digest and after-body"
                )
        elif before is None or body is not None:
            raise WorkspaceSemanticPackageCompositionError(
                "source delete requires only a before digest tombstone"
            )
        if before is not None:
            object.__setattr__(
                self,
                "before_digest",
                _digest_value(before, "source movement before_digest"),
            )
        if body is not None and (
            body.input_kind != self.input_kind or body.relative_path != path
        ):
            raise WorkspaceSemanticPackageCompositionError(
                "source movement after-body coordinate mismatched"
            )
        object.__setattr__(self, "relative_path", path)

    def to_dict(self) -> dict[str, object]:
        return {
            "package_ref": self.package_ref,
            "input_kind": self.input_kind,
            "relative_path": self.relative_path,
            "change_kind": self.change_kind,
            "before_digest": self.before_digest,
            "after_body": self.after_body.to_dict() if self.after_body else None,
        }


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticPackageInputAuthority:
    """Exact current package descriptor, independent from source movements."""

    package_ref: str
    package_name: str
    package_kind: str
    fqn_prefix: str
    semantic_version: str
    package_root: str
    sources_root: str
    owned_semantic_root_refs: tuple[str, ...]
    manifest: WorkspaceSemanticPackageManifestAuthority
    declared_source_relative_paths: tuple[str, ...]
    direct_dependency_package_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "package_ref",
            "package_name",
            "package_kind",
            "fqn_prefix",
            "semantic_version",
        ):
            object.__setattr__(
                self,
                field_name,
                _text(cast(str, getattr(self, field_name)), field_name),
            )
        object.__setattr__(
            self,
            "package_root",
            _relative_path(self.package_root, "package_root"),
        )
        object.__setattr__(
            self,
            "sources_root",
            _relative_path(self.sources_root, "sources_root"),
        )
        package_root = PurePosixPath(self.package_root)
        if package_root not in PurePosixPath(self.sources_root).parents:
            raise WorkspaceSemanticPackageCompositionError(
                "sources_root must be contained beneath package_root"
            )
        if package_root not in PurePosixPath(self.manifest.relative_path).parents:
            raise WorkspaceSemanticPackageCompositionError(
                "manifest must be contained beneath package_root"
            )
        declared_sources = tuple(
            sorted(
                _relative_path(path, "declared_source_relative_paths")
                for path in self.declared_source_relative_paths
            )
        )
        if not declared_sources or len(declared_sources) != len(set(declared_sources)):
            raise WorkspaceSemanticPackageCompositionError(
                "declared source paths must be non-empty and unique"
            )
        source_root = PurePosixPath(self.sources_root)
        if any(
            not path.endswith(".aware")
            or source_root not in PurePosixPath(path).parents
            for path in declared_sources
        ):
            raise WorkspaceSemanticPackageCompositionError(
                "declared .aware source path must be contained beneath sources_root"
            )
        owned_roots = _texts(
            self.owned_semantic_root_refs,
            "owned_semantic_root_refs",
        )
        if not owned_roots:
            raise WorkspaceSemanticPackageCompositionError(
                "package must own semantic roots"
            )
        dependencies = _texts(
            self.direct_dependency_package_refs,
            "direct_dependency_package_refs",
        )
        if self.package_ref in dependencies:
            raise WorkspaceSemanticPackageCompositionError(
                "package cannot depend on itself"
            )
        object.__setattr__(
            self,
            "declared_source_relative_paths",
            declared_sources,
        )
        object.__setattr__(self, "owned_semantic_root_refs", owned_roots)
        object.__setattr__(self, "direct_dependency_package_refs", dependencies)

    def to_dict(self) -> dict[str, object]:
        return {
            "package_ref": self.package_ref,
            "package_name": self.package_name,
            "package_kind": self.package_kind,
            "fqn_prefix": self.fqn_prefix,
            "semantic_version": self.semantic_version,
            "package_root": self.package_root,
            "sources_root": self.sources_root,
            "owned_semantic_root_refs": list(self.owned_semantic_root_refs),
            "manifest": self.manifest.to_dict(),
            "declared_source_relative_paths": list(self.declared_source_relative_paths),
            "direct_dependency_package_refs": list(self.direct_dependency_package_refs),
        }


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticProviderSelectionAuthority:
    """Exact Workspace-selected semantic provider advertisement/binding."""

    capability_key: str
    semantic_version: str
    contract_schema_digest: str
    selection_binding_ref: str
    selection_binding_fingerprint: str

    def __post_init__(self) -> None:
        for field_name in (
            "capability_key",
            "semantic_version",
            "selection_binding_ref",
        ):
            object.__setattr__(
                self,
                field_name,
                _text(cast(str, getattr(self, field_name)), field_name),
            )
        for field_name in (
            "contract_schema_digest",
            "selection_binding_fingerprint",
        ):
            object.__setattr__(
                self,
                field_name,
                _digest_value(cast(str, getattr(self, field_name)), field_name),
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "capability_key": self.capability_key,
            "semantic_version": self.semantic_version,
            "contract_schema_digest": self.contract_schema_digest,
            "selection_binding_ref": self.selection_binding_ref,
            "selection_binding_fingerprint": self.selection_binding_fingerprint,
        }


@dataclass(frozen=True, slots=True, order=True)
class WorkspaceSemanticPriorAuthorityRef:
    package_ref: str
    role: str
    ref: str
    digest: str
    size_bytes: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "package_ref",
            _text(self.package_ref, "prior authority package_ref"),
        )
        if self.role not in _PRIOR_ROLES:
            raise WorkspaceSemanticPackageCompositionError(
                "prior authority role is unsupported"
            )
        object.__setattr__(self, "ref", _text(self.ref, "prior authority ref"))
        object.__setattr__(
            self,
            "digest",
            _digest_value(self.digest, "prior authority digest"),
        )
        _ = _non_negative(self.size_bytes, "prior authority size_bytes")

    def to_dict(self) -> dict[str, object]:
        return {
            "package_ref": self.package_ref,
            "role": self.role,
            "ref": self.ref,
            "digest": self.digest,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticPackagePriorAuthority:
    package_ref: str
    prior_kind: str
    base_authority_ref: str
    refs: tuple[WorkspaceSemanticPriorAuthorityRef, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "package_ref", _text(self.package_ref, "package_ref"))
        if self.prior_kind not in _PRIOR_KINDS:
            raise WorkspaceSemanticPackageCompositionError(
                "prior authority kind is unsupported"
            )
        refs = tuple(sorted(self.refs))
        object.__setattr__(
            self,
            "base_authority_ref",
            _digest_value(self.base_authority_ref, "base_authority_ref"),
        )
        if self.prior_kind == "typed_empty" and refs:
            raise WorkspaceSemanticPackageCompositionError(
                "typed-empty prior authority cannot carry refs"
            )
        if self.prior_kind == "exact_refs" and not refs:
            raise WorkspaceSemanticPackageCompositionError(
                "exact prior authority requires refs"
            )
        identities = tuple((item.package_ref, item.role) for item in refs)
        if len(identities) != len(set(identities)):
            raise WorkspaceSemanticPackageCompositionError(
                "prior authority refs must be unique"
            )
        if any(item.package_ref != self.package_ref for item in refs):
            raise WorkspaceSemanticPackageCompositionError(
                "package prior refs name a foreign package"
            )
        roles = {item.role for item in refs}
        if self.prior_kind == "exact_refs" and (
            not _REQUIRED_PACKAGE_PRIOR_ROLES.issubset(roles)
            or len(roles - _REQUIRED_PACKAGE_PRIOR_ROLES) > 1
        ):
            raise WorkspaceSemanticPackageCompositionError(
                "exact package prior requires package/schema/object_abi and optional artifact"
            )
        object.__setattr__(self, "refs", refs)

    def to_dict(self) -> dict[str, object]:
        return {
            "package_ref": self.package_ref,
            "prior_kind": self.prior_kind,
            "base_authority_ref": self.base_authority_ref,
            "refs": [item.to_dict() for item in self.refs],
        }


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticPriorAuthority:
    package_priors: tuple[WorkspaceSemanticPackagePriorAuthority, ...]

    def __post_init__(self) -> None:
        priors = tuple(sorted(self.package_priors, key=lambda item: item.package_ref))
        if not priors or len({item.package_ref for item in priors}) != len(priors):
            raise WorkspaceSemanticPackageCompositionError(
                "package priors must be non-empty and unique"
            )
        object.__setattr__(self, "package_priors", priors)

    def to_dict(self) -> dict[str, object]:
        return {"package_priors": [item.to_dict() for item in self.package_priors]}

    def for_package(self, package_ref: str) -> WorkspaceSemanticPackagePriorAuthority:
        matches = tuple(
            item for item in self.package_priors if item.package_ref == package_ref
        )
        if len(matches) != 1:
            raise WorkspaceSemanticPackageCompositionError(
                "package prior is absent or duplicated"
            )
        return matches[0]


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticRendererInputAuthority:
    renderer_profile_ref: str
    renderer_configuration_ref: str
    renderer_configuration_digest: str
    allowed_output_namespace: str

    def __post_init__(self) -> None:
        for field_name in ("renderer_profile_ref", "renderer_configuration_ref"):
            object.__setattr__(
                self,
                field_name,
                _text(cast(str, getattr(self, field_name)), field_name),
            )
        object.__setattr__(
            self,
            "renderer_configuration_digest",
            _digest_value(
                self.renderer_configuration_digest,
                "renderer_configuration_digest",
            ),
        )
        object.__setattr__(
            self,
            "allowed_output_namespace",
            _relative_path(
                self.allowed_output_namespace,
                "allowed_output_namespace",
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "renderer_profile_ref": self.renderer_profile_ref,
            "renderer_configuration_ref": self.renderer_configuration_ref,
            "renderer_configuration_digest": self.renderer_configuration_digest,
            "allowed_output_namespace": self.allowed_output_namespace,
        }


@dataclass(frozen=True, slots=True, order=True)
class WorkspaceAwareParseInput:
    """Derived exact input for the one later canonical `.aware` parse."""

    package_ref: str
    package_name: str
    fqn_prefix: str
    semantic_version: str
    sources_root: str
    source: WorkspaceCapturedSemanticInput

    def to_dict(self) -> dict[str, object]:
        return {
            "package_ref": self.package_ref,
            "package_name": self.package_name,
            "fqn_prefix": self.fqn_prefix,
            "semantic_version": self.semantic_version,
            "sources_root": self.sources_root,
            "source": self.source.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticPackageCompositionAuthority:
    """Input-only child authority under one canonical Workspace operation."""

    parent_operation: WorkspaceParentOperationAuthorityRef
    target_package_ref: str
    packages: tuple[WorkspaceSemanticPackageInputAuthority, ...]
    source_movements: tuple[WorkspaceSemanticSourceMovement, ...]
    requested_semantic_root_refs: tuple[str, ...]
    provider: WorkspaceSemanticProviderSelectionAuthority
    accepted_result_catalog: WorkspaceSemanticResultCatalogRoot
    prior_authority: WorkspaceSemanticPriorAuthority
    renderer: WorkspaceSemanticRendererInputAuthority
    authority_digest: str
    authority_grade: str = WORKSPACE_SEMANTIC_PACKAGE_AUTHORITY_GRADE
    non_claims: tuple[str, ...] = WORKSPACE_SEMANTIC_PACKAGE_NON_CLAIMS
    contract: str = WORKSPACE_SEMANTIC_PACKAGE_COMPOSITION_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != WORKSPACE_SEMANTIC_PACKAGE_COMPOSITION_CONTRACT:
            raise WorkspaceSemanticPackageCompositionError(
                "semantic package composition contract is unsupported"
            )
        if self.authority_grade != WORKSPACE_SEMANTIC_PACKAGE_AUTHORITY_GRADE:
            raise WorkspaceSemanticPackageCompositionError(
                "semantic package authority grade is unsupported"
            )
        if tuple(self.non_claims) != WORKSPACE_SEMANTIC_PACKAGE_NON_CLAIMS:
            raise WorkspaceSemanticPackageCompositionError(
                "semantic package non-claims are incomplete or substituted"
            )
        target = _text(self.target_package_ref, "target_package_ref")
        packages = tuple(sorted(self.packages, key=lambda item: item.package_ref))
        if not packages:
            raise WorkspaceSemanticPackageCompositionError(
                "semantic package composition requires packages"
            )
        package_refs = tuple(item.package_ref for item in packages)
        package_names = tuple(item.package_name for item in packages)
        if len(package_refs) != len(set(package_refs)):
            raise WorkspaceSemanticPackageCompositionError(
                "semantic package refs must be unique"
            )
        if len(package_names) != len(set(package_names)):
            raise WorkspaceSemanticPackageCompositionError(
                "semantic package names must be unique"
            )
        if target not in package_refs:
            raise WorkspaceSemanticPackageCompositionError(
                "target package is absent from composition"
            )
        known = set(package_refs)
        for package in packages:
            missing = set(package.direct_dependency_package_refs) - known
            if missing:
                raise WorkspaceSemanticPackageCompositionError(
                    "declared dependency package is absent from composition"
                )
        _validate_acyclic(packages)
        reachable = _reachable_package_refs(target, packages)
        if reachable != known:
            raise WorkspaceSemanticPackageCompositionError(
                "semantic package set must equal the target dependency closure"
            )
        movements = tuple(
            sorted(
                self.source_movements,
                key=lambda item: (item.package_ref, item.relative_path),
            )
        )
        movement_coordinates = tuple(
            (item.package_ref, item.relative_path) for item in movements
        )
        if len(movement_coordinates) != len(set(movement_coordinates)):
            raise WorkspaceSemanticPackageCompositionError(
                "source movement coordinates must be unique"
            )
        if any(item.package_ref not in known for item in movements):
            raise WorkspaceSemanticPackageCompositionError(
                "source movement package is absent from composition"
            )
        packages_by_ref = {package.package_ref: package for package in packages}
        for movement in movements:
            package = packages_by_ref[movement.package_ref]
            if movement.input_kind == "manifest":
                if movement.relative_path != package.manifest.relative_path:
                    raise WorkspaceSemanticPackageCompositionError(
                        "manifest movement coordinate mismatched"
                    )
                if movement.change_kind == "delete":
                    raise WorkspaceSemanticPackageCompositionError(
                        "reachable package manifest cannot be deleted"
                    )
            elif movement.change_kind != "delete" and (
                movement.relative_path not in package.declared_source_relative_paths
            ):
                raise WorkspaceSemanticPackageCompositionError(
                    "source upsert is absent from current package authority"
                )
            elif movement.change_kind == "delete" and (
                PurePosixPath(package.sources_root)
                not in PurePosixPath(movement.relative_path).parents
            ):
                raise WorkspaceSemanticPackageCompositionError(
                    "source tombstone is outside package sources_root"
                )
        owned_roots = [
            root for package in packages for root in package.owned_semantic_root_refs
        ]
        if len(owned_roots) != len(set(owned_roots)):
            raise WorkspaceSemanticPackageCompositionError(
                "semantic root ownership must be globally unique"
            )
        roots = _texts(
            self.requested_semantic_root_refs,
            "requested_semantic_root_refs",
        )
        if not roots:
            raise WorkspaceSemanticPackageCompositionError(
                "semantic package composition requires requested roots"
            )
        target_package = next(
            package for package in packages if package.package_ref == target
        )
        if not set(roots).issubset(target_package.owned_semantic_root_refs):
            raise WorkspaceSemanticPackageCompositionError(
                "requested semantic root is not owned by the target package"
            )
        _validate_prior_authority(
            prior=self.prior_authority,
            target_package_ref=target,
            packages=packages,
            movements=movements,
        )
        object.__setattr__(self, "target_package_ref", target)
        object.__setattr__(self, "packages", packages)
        object.__setattr__(self, "source_movements", movements)
        object.__setattr__(self, "requested_semantic_root_refs", roots)
        expected = _semantic_digest(self._semantic_payload())
        object.__setattr__(
            self,
            "authority_digest",
            _digest_value(self.authority_digest, "authority_digest"),
        )
        if self.authority_digest != expected:
            raise WorkspaceSemanticPackageCompositionError(
                "semantic package composition authority digest mismatched"
            )

    @classmethod
    def create(
        cls,
        *,
        parent_operation: WorkspaceParentOperationAuthorityRef,
        target_package_ref: str,
        packages: tuple[WorkspaceSemanticPackageInputAuthority, ...],
        source_movements: tuple[WorkspaceSemanticSourceMovement, ...],
        requested_semantic_root_refs: tuple[str, ...],
        provider: WorkspaceSemanticProviderSelectionAuthority,
        accepted_result_catalog: WorkspaceSemanticResultCatalogRoot,
        prior_authority: WorkspaceSemanticPriorAuthority,
        renderer: WorkspaceSemanticRendererInputAuthority,
    ) -> WorkspaceSemanticPackageCompositionAuthority:
        normalized_packages = tuple(sorted(packages, key=lambda item: item.package_ref))
        normalized_roots = _texts(
            requested_semantic_root_refs,
            "requested_semantic_root_refs",
        )
        semantic = _composition_payload(
            parent_operation=parent_operation,
            target_package_ref=target_package_ref,
            packages=normalized_packages,
            source_movements=source_movements,
            requested_semantic_root_refs=normalized_roots,
            provider=provider,
            accepted_result_catalog=accepted_result_catalog,
            prior_authority=prior_authority,
            renderer=renderer,
        )
        return cls(
            parent_operation=parent_operation,
            target_package_ref=target_package_ref,
            packages=normalized_packages,
            source_movements=source_movements,
            requested_semantic_root_refs=normalized_roots,
            provider=provider,
            accepted_result_catalog=accepted_result_catalog,
            prior_authority=prior_authority,
            renderer=renderer,
            authority_digest=_semantic_digest(semantic),
        )

    @classmethod
    def from_dict(cls, value: object) -> WorkspaceSemanticPackageCompositionAuthority:
        payload = _object(
            value,
            {
                "contract",
                "parent_operation",
                "target_package_ref",
                "packages",
                "source_movements",
                "requested_semantic_root_refs",
                "provider",
                "accepted_result_catalog",
                "prior_authority",
                "renderer",
                "authority_grade",
                "non_claims",
                "authority_digest",
            },
            "semantic package composition",
        )
        parent = _object(
            payload["parent_operation"],
            {
                "schema",
                "input_name",
                "input_role",
                "ref_kind",
                "ref",
                "digest",
                "size",
                "authority_digest",
            },
            "parent operation",
        )
        packages = tuple(
            _package_from_dict(item) for item in _list(payload["packages"], "packages")
        )
        movements = tuple(
            _source_movement_from_dict(item)
            for item in _list(payload["source_movements"], "source_movements")
        )
        provider = _object(
            payload["provider"],
            {
                "capability_key",
                "semantic_version",
                "contract_schema_digest",
                "selection_binding_ref",
                "selection_binding_fingerprint",
            },
            "provider",
        )
        prior = _object(
            payload["prior_authority"],
            {"package_priors"},
            "prior authority",
        )
        renderer = _object(
            payload["renderer"],
            {
                "renderer_profile_ref",
                "renderer_configuration_ref",
                "renderer_configuration_digest",
                "allowed_output_namespace",
            },
            "renderer",
        )
        return cls(
            contract=_string(payload["contract"], "contract"),
            parent_operation=WorkspaceParentOperationAuthorityRef(
                schema=_string(parent["schema"], "parent schema"),
                input_name=_string(parent["input_name"], "parent input_name"),
                input_role=_string(parent["input_role"], "parent input_role"),
                ref_kind=_string(parent["ref_kind"], "parent ref_kind"),
                ref=_string(parent["ref"], "parent ref"),
                digest=_string(parent["digest"], "parent digest"),
                size=_integer(parent["size"], "parent size"),
                authority_digest=_string(
                    parent["authority_digest"],
                    "parent authority_digest",
                ),
            ),
            target_package_ref=_string(
                payload["target_package_ref"], "target_package_ref"
            ),
            packages=packages,
            source_movements=movements,
            requested_semantic_root_refs=tuple(
                _string(item, "requested semantic root")
                for item in _list(
                    payload["requested_semantic_root_refs"],
                    "requested_semantic_root_refs",
                )
            ),
            provider=WorkspaceSemanticProviderSelectionAuthority(
                capability_key=_string(provider["capability_key"], "capability_key"),
                semantic_version=_string(
                    provider["semantic_version"], "semantic_version"
                ),
                contract_schema_digest=_string(
                    provider["contract_schema_digest"],
                    "contract_schema_digest",
                ),
                selection_binding_ref=_string(
                    provider["selection_binding_ref"], "selection_binding_ref"
                ),
                selection_binding_fingerprint=_string(
                    provider["selection_binding_fingerprint"],
                    "selection_binding_fingerprint",
                ),
            ),
            accepted_result_catalog=WorkspaceSemanticResultCatalogRoot.from_dict(
                payload["accepted_result_catalog"]
            ),
            prior_authority=WorkspaceSemanticPriorAuthority(
                package_priors=tuple(
                    _package_prior_from_dict(item)
                    for item in _list(prior["package_priors"], "package_priors")
                ),
            ),
            renderer=WorkspaceSemanticRendererInputAuthority(
                renderer_profile_ref=_string(
                    renderer["renderer_profile_ref"], "renderer_profile_ref"
                ),
                renderer_configuration_ref=_string(
                    renderer["renderer_configuration_ref"],
                    "renderer_configuration_ref",
                ),
                renderer_configuration_digest=_string(
                    renderer["renderer_configuration_digest"],
                    "renderer_configuration_digest",
                ),
                allowed_output_namespace=_string(
                    renderer["allowed_output_namespace"],
                    "allowed_output_namespace",
                ),
            ),
            authority_grade=_string(payload["authority_grade"], "authority_grade"),
            non_claims=tuple(
                _string(item, "non_claim")
                for item in _list(payload["non_claims"], "non_claims")
            ),
            authority_digest=_string(payload["authority_digest"], "authority_digest"),
        )

    @classmethod
    def from_json_bytes(
        cls, value: bytes
    ) -> WorkspaceSemanticPackageCompositionAuthority:
        try:
            payload = cast(object, json.loads(value))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise WorkspaceSemanticPackageCompositionError(
                "semantic package composition JSON is invalid"
            ) from error
        return cls.from_dict(payload)

    def _semantic_payload(self) -> dict[str, object]:
        return _composition_payload(
            parent_operation=self.parent_operation,
            target_package_ref=self.target_package_ref,
            packages=self.packages,
            source_movements=self.source_movements,
            requested_semantic_root_refs=self.requested_semantic_root_refs,
            provider=self.provider,
            accepted_result_catalog=self.accepted_result_catalog,
            prior_authority=self.prior_authority,
            renderer=self.renderer,
        )

    def to_dict(self) -> dict[str, object]:
        return {**self._semantic_payload(), "authority_digest": self.authority_digest}

    def to_json_bytes(self) -> bytes:
        return _canonical_bytes(self.to_dict())

    @property
    def authority_ref(self) -> str:
        return (
            "cas://workspace-semantic-package-composition/"
            + self.authority_digest.removeprefix(_DIGEST_PREFIX)
            + ".json"
        )

    def aware_parse_inputs(self) -> tuple[WorkspaceAwareParseInput, ...]:
        """Return changed create/update `.aware` after-bodies without parsing."""

        packages_by_ref = {package.package_ref: package for package in self.packages}
        return tuple(
            WorkspaceAwareParseInput(
                package_ref=package.package_ref,
                package_name=package.package_name,
                fqn_prefix=package.fqn_prefix,
                semantic_version=package.semantic_version,
                sources_root=package.sources_root,
                source=cast(WorkspaceCapturedSemanticInput, movement.after_body),
            )
            for movement in self.source_movements
            if movement.input_kind == "aware_source"
            and movement.change_kind in {"create", "update"}
            for package in (packages_by_ref[movement.package_ref],)
        )

    @property
    def source_lifecycle(self) -> str:
        """Report source admission state, never command-wide currentness."""

        if (
            self.prior_authority.for_package(self.target_package_ref).prior_kind
            == "typed_empty"
        ):
            return "genesis"
        return "source_delta" if self.source_movements else "source_current"

    @property
    def requires_source_semantic_work(self) -> bool:
        """Whether changed source requires later parse/Meaning derivation."""

        return self.source_lifecycle != "source_current"

    @property
    def aware_parse_input_digest(self) -> str:
        return _semantic_digest(
            {
                "composition_authority_digest": self.authority_digest,
                "inputs": [item.to_dict() for item in self.aware_parse_inputs()],
            },
            contract="aware.workspace.semantic-package-parse-input.v1",
        )


def _composition_payload(
    *,
    parent_operation: WorkspaceParentOperationAuthorityRef,
    target_package_ref: str,
    packages: tuple[WorkspaceSemanticPackageInputAuthority, ...],
    source_movements: tuple[WorkspaceSemanticSourceMovement, ...],
    requested_semantic_root_refs: tuple[str, ...],
    provider: WorkspaceSemanticProviderSelectionAuthority,
    accepted_result_catalog: WorkspaceSemanticResultCatalogRoot,
    prior_authority: WorkspaceSemanticPriorAuthority,
    renderer: WorkspaceSemanticRendererInputAuthority,
) -> dict[str, object]:
    return {
        "contract": WORKSPACE_SEMANTIC_PACKAGE_COMPOSITION_CONTRACT,
        "parent_operation": parent_operation.to_dict(),
        "target_package_ref": target_package_ref,
        "packages": [item.to_dict() for item in packages],
        "source_movements": [
            item.to_dict()
            for item in sorted(
                source_movements,
                key=lambda movement: (
                    movement.package_ref,
                    movement.relative_path,
                ),
            )
        ],
        "requested_semantic_root_refs": list(requested_semantic_root_refs),
        "provider": provider.to_dict(),
        "accepted_result_catalog": accepted_result_catalog.to_dict(),
        "prior_authority": prior_authority.to_dict(),
        "renderer": renderer.to_dict(),
        "authority_grade": WORKSPACE_SEMANTIC_PACKAGE_AUTHORITY_GRADE,
        "non_claims": list(WORKSPACE_SEMANTIC_PACKAGE_NON_CLAIMS),
    }


def _package_from_dict(value: object) -> WorkspaceSemanticPackageInputAuthority:
    payload = _object(
        value,
        {
            "package_ref",
            "package_name",
            "package_kind",
            "fqn_prefix",
            "semantic_version",
            "package_root",
            "sources_root",
            "owned_semantic_root_refs",
            "manifest",
            "declared_source_relative_paths",
            "direct_dependency_package_refs",
        },
        "package",
    )
    return WorkspaceSemanticPackageInputAuthority(
        package_ref=_string(payload["package_ref"], "package_ref"),
        package_name=_string(payload["package_name"], "package_name"),
        package_kind=_string(payload["package_kind"], "package_kind"),
        fqn_prefix=_string(payload["fqn_prefix"], "fqn_prefix"),
        semantic_version=_string(payload["semantic_version"], "semantic_version"),
        package_root=_string(payload["package_root"], "package_root"),
        sources_root=_string(payload["sources_root"], "sources_root"),
        owned_semantic_root_refs=tuple(
            _string(item, "owned semantic root")
            for item in _list(
                payload["owned_semantic_root_refs"],
                "owned_semantic_root_refs",
            )
        ),
        manifest=_manifest_authority_from_dict(payload["manifest"]),
        declared_source_relative_paths=tuple(
            _string(item, "declared source relative path")
            for item in _list(
                payload["declared_source_relative_paths"],
                "declared_source_relative_paths",
            )
        ),
        direct_dependency_package_refs=tuple(
            _string(item, "direct dependency package ref")
            for item in _list(
                payload["direct_dependency_package_refs"],
                "direct_dependency_package_refs",
            )
        ),
    )


def _manifest_authority_from_dict(
    value: object,
) -> WorkspaceSemanticPackageManifestAuthority:
    payload = _object(
        value,
        {"relative_path", "ref", "digest", "size_bytes"},
        "manifest authority",
    )
    return WorkspaceSemanticPackageManifestAuthority(
        relative_path=_string(payload["relative_path"], "relative_path"),
        ref=_string(payload["ref"], "ref"),
        digest=_string(payload["digest"], "digest"),
        size_bytes=_integer(payload["size_bytes"], "size_bytes"),
    )


def _captured_input_from_dict(value: object) -> WorkspaceCapturedSemanticInput:
    payload = _object(
        value,
        {"input_kind", "relative_path", "body_ref", "body_digest", "size_bytes"},
        "captured input",
    )
    return WorkspaceCapturedSemanticInput(
        input_kind=_string(payload["input_kind"], "input_kind"),
        relative_path=_string(payload["relative_path"], "relative_path"),
        body_ref=_string(payload["body_ref"], "body_ref"),
        body_digest=_string(payload["body_digest"], "body_digest"),
        size_bytes=_integer(payload["size_bytes"], "size_bytes"),
    )


def _prior_ref_from_dict(value: object) -> WorkspaceSemanticPriorAuthorityRef:
    payload = _object(
        value,
        {"package_ref", "role", "ref", "digest", "size_bytes"},
        "prior authority ref",
    )
    return WorkspaceSemanticPriorAuthorityRef(
        package_ref=_string(payload["package_ref"], "package_ref"),
        role=_string(payload["role"], "role"),
        ref=_string(payload["ref"], "ref"),
        digest=_string(payload["digest"], "digest"),
        size_bytes=_integer(payload["size_bytes"], "size_bytes"),
    )


def _package_prior_from_dict(
    value: object,
) -> WorkspaceSemanticPackagePriorAuthority:
    payload = _object(
        value,
        {"package_ref", "prior_kind", "base_authority_ref", "refs"},
        "package prior authority",
    )
    return WorkspaceSemanticPackagePriorAuthority(
        package_ref=_string(payload["package_ref"], "package_ref"),
        prior_kind=_string(payload["prior_kind"], "prior_kind"),
        base_authority_ref=_string(payload["base_authority_ref"], "base_authority_ref"),
        refs=tuple(
            _prior_ref_from_dict(item) for item in _list(payload["refs"], "prior refs")
        ),
    )


def _source_movement_from_dict(value: object) -> WorkspaceSemanticSourceMovement:
    payload = _object(
        value,
        {
            "package_ref",
            "input_kind",
            "relative_path",
            "change_kind",
            "before_digest",
            "after_body",
        },
        "source movement",
    )
    before = payload["before_digest"]
    after = payload["after_body"]
    if before is not None and not isinstance(before, str):
        raise WorkspaceSemanticPackageCompositionError(
            "source movement before_digest must be text or null"
        )
    return WorkspaceSemanticSourceMovement(
        package_ref=_string(payload["package_ref"], "package_ref"),
        input_kind=_string(payload["input_kind"], "input_kind"),
        relative_path=_string(payload["relative_path"], "relative_path"),
        change_kind=_string(payload["change_kind"], "change_kind"),
        before_digest=before,
        after_body=(_captured_input_from_dict(after) if after is not None else None),
    )


def _validate_prior_authority(
    *,
    prior: WorkspaceSemanticPriorAuthority,
    target_package_ref: str,
    packages: tuple[WorkspaceSemanticPackageInputAuthority, ...],
    movements: tuple[WorkspaceSemanticSourceMovement, ...],
) -> None:
    known = {package.package_ref for package in packages}
    if {item.package_ref for item in prior.package_priors} != known:
        raise WorkspaceSemanticPackageCompositionError(
            "package priors must equal the reachable package closure"
        )
    target_prior = prior.for_package(target_package_ref)
    if any(
        item.prior_kind == "typed_empty" and item.package_ref != target_package_ref
        for item in prior.package_priors
    ):
        raise WorkspaceSemanticPackageCompositionError(
            "only the target package may use typed-empty prior authority"
        )
    if any(movement.package_ref != target_package_ref for movement in movements):
        raise WorkspaceSemanticPackageCompositionError(
            "dependency packages cannot carry source movements"
        )

    if target_prior.prior_kind == "typed_empty":
        target_package = next(
            item for item in packages if item.package_ref == target_package_ref
        )
        expected_coordinates = {
            (target_package.package_ref, target_package.manifest.relative_path)
        } | {
            (target_package.package_ref, path)
            for path in target_package.declared_source_relative_paths
        }
        actual_coordinates = {
            (movement.package_ref, movement.relative_path) for movement in movements
        }
        if actual_coordinates != expected_coordinates or any(
            movement.change_kind != "create" for movement in movements
        ):
            raise WorkspaceSemanticPackageCompositionError(
                "typed-empty genesis requires complete create-only target bodies"
            )

    manifest_moved = {
        movement.package_ref
        for movement in movements
        if movement.input_kind == "manifest"
    }
    for package in packages:
        package_prior = prior.for_package(package.package_ref)
        if package_prior.prior_kind != "exact_refs":
            continue
        if package.package_ref in manifest_moved:
            continue
        prior_package = next(
            item for item in package_prior.refs if item.role == "package"
        )
        if (
            prior_package.ref != package.manifest.ref
            or prior_package.digest != package.manifest.digest
            or prior_package.size_bytes != package.manifest.size_bytes
        ):
            raise WorkspaceSemanticPackageCompositionError(
                "unchanged package manifest authority mismatched prior fragment"
            )


def _validate_acyclic(
    packages: tuple[WorkspaceSemanticPackageInputAuthority, ...],
) -> None:
    dependencies = {
        package.package_ref: package.direct_dependency_package_refs
        for package in packages
    }
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(package_ref: str) -> None:
        if package_ref in visited:
            return
        if package_ref in visiting:
            raise WorkspaceSemanticPackageCompositionError(
                "semantic package dependency graph contains a cycle"
            )
        visiting.add(package_ref)
        for dependency_ref in dependencies[package_ref]:
            visit(dependency_ref)
        visiting.remove(package_ref)
        visited.add(package_ref)

    for package_ref in sorted(dependencies):
        visit(package_ref)


def _reachable_package_refs(
    target_package_ref: str,
    packages: tuple[WorkspaceSemanticPackageInputAuthority, ...],
) -> set[str]:
    dependencies = {
        package.package_ref: package.direct_dependency_package_refs
        for package in packages
    }
    reachable: set[str] = set()
    pending = [target_package_ref]
    while pending:
        package_ref = pending.pop()
        if package_ref in reachable:
            continue
        reachable.add(package_ref)
        pending.extend(dependencies[package_ref])
    return reachable


def _semantic_digest(
    payload: object,
    *,
    contract: str = WORKSPACE_SEMANTIC_PACKAGE_COMPOSITION_CONTRACT,
) -> str:
    return (
        _DIGEST_PREFIX
        + hashlib.sha256(
            _canonical_bytes({"contract": contract, "payload": payload})
        ).hexdigest()
    )


def _authority_digest(payload: object) -> str:
    """Match the canonical content-addressed authority-ref identity codec."""

    return _DIGEST_PREFIX + hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise WorkspaceSemanticPackageCompositionError(
            f"{field} must be non-empty normalized text"
        )
    return value


def _texts(values: tuple[str, ...], field: str) -> tuple[str, ...]:
    normalized = tuple(sorted(_text(value, field) for value in values))
    if len(normalized) != len(set(normalized)):
        raise WorkspaceSemanticPackageCompositionError(f"{field} must be unique")
    return normalized


def _digest_value(value: str, field: str) -> str:
    value = _text(value, field)
    normalized = value.removeprefix(_DIGEST_PREFIX)
    if len(normalized) != 64 or any(
        item not in "0123456789abcdef" for item in normalized
    ):
        raise WorkspaceSemanticPackageCompositionError(f"{field} must be SHA-256")
    return _DIGEST_PREFIX + normalized


def _relative_path(value: str, field: str) -> str:
    value = _text(value, field)
    path = PurePosixPath(value)
    if (
        "\\" in value
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise WorkspaceSemanticPackageCompositionError(
            f"{field} must be a normalized relative path"
        )
    return value


def _non_negative(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise WorkspaceSemanticPackageCompositionError(
            f"{field} must be a non-negative integer"
        )
    return value


def _object(value: object, fields: set[str], label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise WorkspaceSemanticPackageCompositionError(
            f"{label} fields are incomplete or unknown"
        )
    raw = cast(dict[object, object], value)
    if any(not isinstance(key, str) for key in raw):
        raise WorkspaceSemanticPackageCompositionError(
            f"{label} fields are incomplete or unknown"
        )
    payload = {cast(str, key): item for key, item in raw.items()}
    if set(payload) != fields:
        raise WorkspaceSemanticPackageCompositionError(
            f"{label} fields are incomplete or unknown"
        )
    return payload


def _list(value: object, field: str) -> list[object]:
    if not isinstance(value, list):
        raise WorkspaceSemanticPackageCompositionError(f"{field} must be a list")
    return cast(list[object], value)


def _string(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise WorkspaceSemanticPackageCompositionError(f"{field} must be text")
    return value


def _integer(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise WorkspaceSemanticPackageCompositionError(f"{field} must be integer")
    return value


__all__ = [
    "CONTENT_ADDRESSED_AUTHORITY_REF_SCHEMA",
    "WORKSPACE_OPERATION_AUTHORITY_INPUT_ROLE",
    "WORKSPACE_OPERATION_AUTHORITY_REF_KIND",
    "WORKSPACE_SEMANTIC_PACKAGE_AUTHORITY_GRADE",
    "WORKSPACE_SEMANTIC_PACKAGE_COMPOSITION_CONTRACT",
    "WORKSPACE_SEMANTIC_PACKAGE_NON_CLAIMS",
    "WorkspaceAwareParseInput",
    "WorkspaceCapturedSemanticInput",
    "WorkspaceParentOperationAuthorityRef",
    "WorkspaceSemanticPackageCompositionAuthority",
    "WorkspaceSemanticPackageCompositionError",
    "WorkspaceSemanticPackageInputAuthority",
    "WorkspaceSemanticPackageManifestAuthority",
    "WorkspaceSemanticPriorAuthority",
    "WorkspaceSemanticPriorAuthorityRef",
    "WorkspaceSemanticProviderSelectionAuthority",
    "WorkspaceSemanticRendererInputAuthority",
    "WorkspaceSemanticSourceMovement",
]
