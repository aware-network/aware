"""Workspace-owned immutable materialization membership and source catalog."""

from __future__ import annotations

import json
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from threading import RLock
from typing import Never, Protocol
from weakref import WeakKeyDictionary

from aware_code_semantic_contract_runtime import (
    CodeSemanticMaterializationIntent,
    ContentDigest,
    ContractViolation,
    SemanticContractRef,
    SemanticDependencyTargetConstraint,
    SemanticPackageCoordinate,
)

from .materialization_selection import (
    WorkspaceMaterializationRootSelector,
    WorkspaceSemanticMaterializationParticipationPolicy,
    _content_digest,
    _nonnegative,
    _preflight_exact,
    _preflight_tuple,
    _token,
    _token_tuple,
)

WORKSPACE_SEMANTIC_AUTHORED_DEPENDENCY = (
    "aware.workspace.semantic-authored-dependency.v1"
)
WORKSPACE_SEMANTIC_MATERIALIZATION_PACKAGE_ENTRY = (
    "aware.workspace.semantic-materialization-package-entry.v1"
)
WORKSPACE_SEMANTIC_MATERIALIZATION_MEMBERSHIP_CATALOG = (
    "aware.workspace.semantic-materialization-membership-catalog.v1"
)


def _digest(contract: str, payload: dict[str, object]) -> ContentDigest:
    return ContentDigest.of_bytes(
        json.dumps(
            {"contract": contract, **payload},
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    )


class _Validated(Protocol):
    def __post_init__(self) -> None: ...


def _frozen_value[T](expected: type[T], **fields: object) -> T:
    result = object.__new__(expected)
    for name, value in fields.items():
        object.__setattr__(result, name, value)
    return result


def _strict_tuple[T: _Validated](
    value: object, expected: type[T], path: str
) -> tuple[T, ...]:
    values = _preflight_tuple(value, expected, path)
    for item in values:
        item.__post_init__()
    return values


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticAuthoredDependency:
    dependency_kind: str
    dependency_ref: str
    admitted_target_package_refs: tuple[str, ...]
    allowed_target_constraints: tuple[SemanticDependencyTargetConstraint, ...]
    declaration_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        dependency_kind: str,
        dependency_ref: str,
        admitted_target_package_refs: tuple[str, ...],
        allowed_target_constraints: tuple[SemanticDependencyTargetConstraint, ...],
    ) -> WorkspaceSemanticAuthoredDependency:
        _preflight_tuple(
            allowed_target_constraints,
            SemanticDependencyTargetConstraint,
            "dependency.allowed_target_constraints",
        )
        payload = _dependency_payload(
            dependency_kind=dependency_kind,
            dependency_ref=dependency_ref,
            admitted_target_package_refs=admitted_target_package_refs,
            allowed_target_constraints=allowed_target_constraints,
        )
        return cls(
            dependency_kind=dependency_kind,
            dependency_ref=dependency_ref,
            admitted_target_package_refs=admitted_target_package_refs,
            allowed_target_constraints=allowed_target_constraints,
            declaration_digest=_digest(WORKSPACE_SEMANTIC_AUTHORED_DEPENDENCY, payload),
        )

    def __post_init__(self) -> None:
        payload = _dependency_payload(
            dependency_kind=self.dependency_kind,
            dependency_ref=self.dependency_ref,
            admitted_target_package_refs=self.admitted_target_package_refs,
            allowed_target_constraints=self.allowed_target_constraints,
        )
        if _content_digest(
            self.declaration_digest, "dependency.declaration_digest"
        ) != _digest(WORKSPACE_SEMANTIC_AUTHORED_DEPENDENCY, payload):
            raise ContractViolation("authored dependency digest mismatched")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_SEMANTIC_AUTHORED_DEPENDENCY,
            **_dependency_payload(
                dependency_kind=self.dependency_kind,
                dependency_ref=self.dependency_ref,
                admitted_target_package_refs=self.admitted_target_package_refs,
                allowed_target_constraints=self.allowed_target_constraints,
            ),
            "declaration_digest": self.declaration_digest.to_wire(),
        }


def _dependency_payload(**values: object) -> dict[str, object]:
    constraints = _strict_tuple(
        values["allowed_target_constraints"],
        SemanticDependencyTargetConstraint,
        "dependency.allowed_target_constraints",
    )
    constraint_wires = tuple(
        json.dumps(item.to_wire(), sort_keys=True, separators=(",", ":")).encode()
        for item in constraints
    )
    if constraint_wires != tuple(sorted(set(constraint_wires))):
        raise ContractViolation("allowed target constraints must be unique and ordered")
    targets = _token_tuple(
        values["admitted_target_package_refs"],
        "dependency.admitted_target_package_refs",
        nonempty=True,
    )
    return {
        "admitted_target_package_refs": list(targets),
        "allowed_target_constraints": [item.to_wire() for item in constraints],
        "dependency_kind": _token(values["dependency_kind"], "dependency.kind"),
        "dependency_ref": _token(values["dependency_ref"], "dependency.ref"),
    }


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationPackageEntry:
    repository_ref: str
    workspace_ref: str
    module_ref: str
    package: SemanticPackageCoordinate
    package_family: str
    package_role: str
    manifest_contract: SemanticContractRef
    manifest_relative_path: str
    source_authority_ref: str
    source_authority_digest: ContentDigest
    source_identity_digest: ContentDigest
    owned_semantic_root_refs: tuple[str, ...]
    authored_dependencies: tuple[WorkspaceSemanticAuthoredDependency, ...]
    participation_policy: WorkspaceSemanticMaterializationParticipationPolicy
    allowed_profile_refs: tuple[str, ...]
    entry_digest: ContentDigest

    @classmethod
    def create(cls, **values: object) -> WorkspaceSemanticMaterializationPackageEntry:
        _preflight_exact(values["package"], SemanticPackageCoordinate, "entry.package")
        _preflight_exact(
            values["manifest_contract"], SemanticContractRef, "entry.manifest_contract"
        )
        _preflight_exact(
            values["source_authority_digest"],
            ContentDigest,
            "entry.source_authority_digest",
        )
        _preflight_exact(
            values["participation_policy"],
            WorkspaceSemanticMaterializationParticipationPolicy,
            "entry.participation_policy",
        )
        _preflight_tuple(
            values["authored_dependencies"],
            WorkspaceSemanticAuthoredDependency,
            "entry.authored_dependencies",
        )
        source_identity = _source_identity(values)
        payload = _entry_payload(**values, source_identity_digest=source_identity)
        return _frozen_value(
            cls,
            **values,
            source_identity_digest=source_identity,
            entry_digest=_digest(
                WORKSPACE_SEMANTIC_MATERIALIZATION_PACKAGE_ENTRY, payload
            ),
        )

    def __post_init__(self) -> None:
        expected_source = _source_identity(
            {
                "package": self.package,
                "manifest_contract": self.manifest_contract,
                "manifest_relative_path": self.manifest_relative_path,
                "source_authority_ref": self.source_authority_ref,
                "source_authority_digest": self.source_authority_digest,
            }
        )
        if self.source_identity_digest != expected_source:
            raise ContractViolation("entry source identity mismatched")
        payload = _entry_payload(
            repository_ref=self.repository_ref,
            workspace_ref=self.workspace_ref,
            module_ref=self.module_ref,
            package=self.package,
            package_family=self.package_family,
            package_role=self.package_role,
            manifest_contract=self.manifest_contract,
            manifest_relative_path=self.manifest_relative_path,
            source_authority_ref=self.source_authority_ref,
            source_authority_digest=self.source_authority_digest,
            source_identity_digest=self.source_identity_digest,
            owned_semantic_root_refs=self.owned_semantic_root_refs,
            authored_dependencies=self.authored_dependencies,
            participation_policy=self.participation_policy,
            allowed_profile_refs=self.allowed_profile_refs,
        )
        if _content_digest(self.entry_digest, "entry.entry_digest") != _digest(
            WORKSPACE_SEMANTIC_MATERIALIZATION_PACKAGE_ENTRY, payload
        ):
            raise ContractViolation("membership entry digest mismatched")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_PACKAGE_ENTRY,
            **_entry_payload(
                repository_ref=self.repository_ref,
                workspace_ref=self.workspace_ref,
                module_ref=self.module_ref,
                package=self.package,
                package_family=self.package_family,
                package_role=self.package_role,
                manifest_contract=self.manifest_contract,
                manifest_relative_path=self.manifest_relative_path,
                source_authority_ref=self.source_authority_ref,
                source_authority_digest=self.source_authority_digest,
                source_identity_digest=self.source_identity_digest,
                owned_semantic_root_refs=self.owned_semantic_root_refs,
                authored_dependencies=self.authored_dependencies,
                participation_policy=self.participation_policy,
                allowed_profile_refs=self.allowed_profile_refs,
            ),
            "entry_digest": self.entry_digest.to_wire(),
        }


def _source_identity(values: dict[str, object]) -> ContentDigest:
    package = _preflight_exact(
        values["package"], SemanticPackageCoordinate, "entry.package"
    )
    manifest = _preflight_exact(
        values["manifest_contract"], SemanticContractRef, "entry.manifest_contract"
    )
    authority_digest = _content_digest(
        values["source_authority_digest"], "entry.source_authority_digest"
    )
    package.__post_init__()
    manifest.__post_init__()
    return _digest(
        "aware.workspace.semantic-source-identity.v1",
        {
            "manifest_contract": manifest.to_wire(),
            "manifest_relative_path": _token(
                values["manifest_relative_path"], "entry.manifest_relative_path"
            ),
            "package": package.to_wire(),
            "source_authority_digest": authority_digest.to_wire(),
            "source_authority_ref": _token(
                values["source_authority_ref"], "entry.source_authority_ref"
            ),
        },
    )


def _entry_payload(**values: object) -> dict[str, object]:
    package = _preflight_exact(
        values["package"], SemanticPackageCoordinate, "entry.package"
    )
    manifest = _preflight_exact(
        values["manifest_contract"], SemanticContractRef, "entry.manifest_contract"
    )
    policy = _preflight_exact(
        values["participation_policy"],
        WorkspaceSemanticMaterializationParticipationPolicy,
        "entry.participation_policy",
    )
    package.__post_init__()
    manifest.__post_init__()
    policy.__post_init__()
    if policy.package_ref != package.package_ref:
        raise ContractViolation("entry policy package differs")
    dependencies = _strict_tuple(
        values["authored_dependencies"],
        WorkspaceSemanticAuthoredDependency,
        "entry.authored_dependencies",
    )
    dependency_keys = tuple(
        (item.dependency_kind, item.dependency_ref) for item in dependencies
    )
    if dependency_keys != tuple(sorted(set(dependency_keys))):
        raise ContractViolation("authored dependencies must be unique and ordered")
    source_identity = _content_digest(
        values["source_identity_digest"], "entry.source_identity_digest"
    )
    return {
        "allowed_profile_refs": list(
            _token_tuple(
                values["allowed_profile_refs"],
                "entry.allowed_profile_refs",
                nonempty=True,
            )
        ),
        "authored_dependencies": [item.to_wire() for item in dependencies],
        "manifest_contract": manifest.to_wire(),
        "manifest_relative_path": _token(
            values["manifest_relative_path"], "entry.manifest_relative_path"
        ),
        "module_ref": _token(values["module_ref"], "entry.module_ref"),
        "owned_semantic_root_refs": list(
            _token_tuple(
                values["owned_semantic_root_refs"],
                "entry.owned_semantic_root_refs",
                nonempty=True,
            )
        ),
        "package": package.to_wire(),
        "package_family": _token(values["package_family"], "entry.package_family"),
        "package_role": _token(values["package_role"], "entry.package_role"),
        "participation_policy": policy.to_wire(),
        "repository_ref": _token(values["repository_ref"], "entry.repository_ref"),
        "source_authority_digest": _content_digest(
            values["source_authority_digest"], "entry.source_authority_digest"
        ).to_wire(),
        "source_authority_ref": _token(
            values["source_authority_ref"], "entry.source_authority_ref"
        ),
        "source_identity_digest": source_identity.to_wire(),
        "workspace_ref": _token(values["workspace_ref"], "entry.workspace_ref"),
    }


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationMembershipCatalog:
    catalog_ref: str
    catalog_generation: int
    entries: tuple[WorkspaceSemanticMaterializationPackageEntry, ...]
    catalog_root_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        catalog_ref: str,
        catalog_generation: int,
        entries: tuple[WorkspaceSemanticMaterializationPackageEntry, ...],
    ) -> WorkspaceSemanticMaterializationMembershipCatalog:
        payload = _catalog_payload(
            catalog_ref=catalog_ref,
            catalog_generation=catalog_generation,
            entries=entries,
        )
        return cls(
            catalog_ref=catalog_ref,
            catalog_generation=catalog_generation,
            entries=entries,
            catalog_root_digest=_digest(
                WORKSPACE_SEMANTIC_MATERIALIZATION_MEMBERSHIP_CATALOG, payload
            ),
        )

    def __post_init__(self) -> None:
        payload = _catalog_payload(
            catalog_ref=self.catalog_ref,
            catalog_generation=self.catalog_generation,
            entries=self.entries,
        )
        if _content_digest(self.catalog_root_digest, "catalog.root") != _digest(
            WORKSPACE_SEMANTIC_MATERIALIZATION_MEMBERSHIP_CATALOG, payload
        ):
            raise ContractViolation("membership catalog root mismatched")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_MEMBERSHIP_CATALOG,
            **_catalog_payload(
                catalog_ref=self.catalog_ref,
                catalog_generation=self.catalog_generation,
                entries=self.entries,
            ),
            "catalog_root_digest": self.catalog_root_digest.to_wire(),
        }


def _catalog_payload(**values: object) -> dict[str, object]:
    entries = _strict_tuple(
        values["entries"],
        WorkspaceSemanticMaterializationPackageEntry,
        "catalog.entries",
    )
    refs = tuple(item.package.package_ref for item in entries)
    if refs != tuple(sorted(set(refs), key=str.encode)):
        raise ContractViolation(
            "catalog entries must be package-ref unique and ordered"
        )
    return {
        "catalog_generation": _nonnegative(
            values["catalog_generation"], "catalog.generation"
        ),
        "catalog_ref": _token(values["catalog_ref"], "catalog.ref"),
        "entries": [item.to_wire() for item in entries],
    }


@dataclass(frozen=True, slots=True)
class _AdmissionState:
    catalog: WorkspaceSemanticMaterializationMembershipCatalog
    host_liveness: Callable[[], bool]


_ADMISSIONS: WeakKeyDictionary[
    AdmittedWorkspaceSemanticMaterializationMembershipCatalog, _AdmissionState
] = WeakKeyDictionary()
_ADMISSION_LOCK = RLock()


class AdmittedWorkspaceSemanticMaterializationMembershipCatalog:
    def __new__(cls) -> AdmittedWorkspaceSemanticMaterializationMembershipCatalog:  # noqa: PYI034
        raise TypeError("Workspace membership catalog admission is module-issued only")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("Workspace membership catalog admission is sealed")

    def __reduce__(self) -> Never:
        raise TypeError("Workspace membership catalog admission is not serializable")


def _issue_workspace_semantic_materialization_membership_catalog(
    *,
    catalog: WorkspaceSemanticMaterializationMembershipCatalog,
    host_liveness: Callable[[], bool],
) -> AdmittedWorkspaceSemanticMaterializationMembershipCatalog:
    catalog = _detached_catalog_snapshot(catalog)
    if not callable(host_liveness) or host_liveness() is not True:
        raise ContractViolation("Workspace membership host admission is not live")
    result = object.__new__(AdmittedWorkspaceSemanticMaterializationMembershipCatalog)
    if host_liveness() is not True:
        raise ContractViolation("Workspace membership host admission moved")
    with _ADMISSION_LOCK:
        _ADMISSIONS[result] = _AdmissionState(
            catalog=catalog,
            host_liveness=host_liveness,
        )
    return result


def _catalog_snapshot_bytes(value: object, path: str) -> bytes:
    catalog = _preflight_exact(
        value, WorkspaceSemanticMaterializationMembershipCatalog, path
    )
    return json.dumps(
        catalog.to_wire(),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def _detached_catalog_snapshot(
    catalog: WorkspaceSemanticMaterializationMembershipCatalog,
) -> WorkspaceSemanticMaterializationMembershipCatalog:
    """Capture one byte-stable catalog graph without retaining caller aliases."""

    initial = _catalog_snapshot_bytes(catalog, "catalog")
    snapshot = deepcopy(catalog)
    admitted = _preflight_exact(
        snapshot,
        WorkspaceSemanticMaterializationMembershipCatalog,
        "catalog.snapshot",
    )
    if _catalog_snapshot_bytes(admitted, "catalog.snapshot") != initial:
        raise ContractViolation("Workspace membership catalog changed while snapshotting")
    if _catalog_snapshot_bytes(catalog, "catalog") != initial:
        raise ContractViolation("Workspace membership catalog changed while snapshotting")
    return admitted


def _revoke_workspace_semantic_materialization_membership_catalog(
    admission: AdmittedWorkspaceSemanticMaterializationMembershipCatalog,
) -> None:
    if type(admission) is not AdmittedWorkspaceSemanticMaterializationMembershipCatalog:
        raise TypeError("membership catalog admission must be exact")
    with _ADMISSION_LOCK:
        _ADMISSIONS.pop(admission, None)


class WorkspaceSemanticMaterializationMembershipResolver:
    def __init__(
        self, admission: AdmittedWorkspaceSemanticMaterializationMembershipCatalog
    ) -> None:
        if (
            type(admission)
            is not AdmittedWorkspaceSemanticMaterializationMembershipCatalog
        ):
            raise TypeError("catalog admission must be exact")
        with _ADMISSION_LOCK:
            state = _ADMISSIONS.get(admission)
        if state is None:
            raise ContractViolation("membership catalog admission is not registered")
        if state.host_liveness() is not True:
            raise ContractViolation("Workspace membership host admission is not live")
        self._admission = admission
        self._catalog = state.catalog
        self._by_package = {
            item.package.package_ref: item for item in state.catalog.entries
        }
        self._by_module = _index(state.catalog.entries, "module_ref")
        self._by_workspace = _index(state.catalog.entries, "workspace_ref")
        self._policy_wires = {
            item.package.package_ref: item.participation_policy.to_wire()
            for item in state.catalog.entries
        }
        self._policy_sets = {
            item.package.package_ref: (
                frozenset(item.participation_policy.allowed_operation_kinds),
                frozenset(item.participation_policy.allowed_semantic_root_refs),
                frozenset(item.participation_policy.allowed_terminal_output_roles),
                frozenset(
                    item.participation_policy.allowed_semantic_configuration_coordinates
                ),
            )
            for item in state.catalog.entries
        }

    @property
    def catalog(self) -> WorkspaceSemanticMaterializationMembershipCatalog:
        self._assert_live()
        return _detached_catalog_snapshot(self._catalog)

    def _assert_live(self) -> None:
        with _ADMISSION_LOCK:
            state = _ADMISSIONS.get(self._admission)
        if state is None or state.host_liveness() is not True:
            raise ContractViolation("Workspace membership host admission is not live")

    def _assert_valid(self) -> None:
        self._assert_live()

    def _catalog_coordinates(self) -> tuple[str, int, ContentDigest]:
        self._assert_live()
        return (
            self._catalog.catalog_ref,
            self._catalog.catalog_generation,
            self._catalog.catalog_root_digest,
        )

    def expand_selector(
        self, selector: WorkspaceMaterializationRootSelector
    ) -> tuple[WorkspaceSemanticMaterializationPackageEntry, ...]:
        self._assert_live()
        _preflight_exact(
            selector, WorkspaceMaterializationRootSelector, "selector"
        ).__post_init__()
        if selector.selector_kind == "package":
            item = self._by_package.get(selector.selector_ref)
            return () if item is None else (item,)
        if selector.selector_kind == "module":
            return self._by_module.get(selector.selector_ref, ())
        if selector.selector_kind == "workspace":
            return self._by_workspace.get(selector.selector_ref, ())
        raise ContractViolation("repository selector held until 07F-F")

    def package(self, package_ref: str) -> WorkspaceSemanticMaterializationPackageEntry:
        self._assert_live()
        result = self._by_package.get(_token(package_ref, "package_ref"))
        if result is None:
            raise ContractViolation("materialization package absent")
        return result

    def package_if_present(
        self, package_ref: str
    ) -> WorkspaceSemanticMaterializationPackageEntry | None:
        """Read a result-capable entry without promoting declaration-only targets."""
        self._assert_live()
        return self._by_package.get(_token(package_ref, "package_ref"))

    def candidates(
        self,
        *,
        admitted_package_refs: tuple[str, ...],
        constraints: tuple[SemanticDependencyTargetConstraint, ...],
    ) -> tuple[WorkspaceSemanticMaterializationPackageEntry, ...]:
        self._assert_live()
        admitted = set(
            _token_tuple(admitted_package_refs, "admitted_package_refs", nonempty=True)
        )
        values = [
            self._by_package[package_ref]
            for package_ref in sorted(admitted, key=str.encode)
            if package_ref in self._by_package
        ]
        for constraint in _strict_tuple(
            constraints, SemanticDependencyTargetConstraint, "constraints"
        ):
            kind, value = constraint.constraint_kind, constraint.constraint_value
            if kind == "semantic_provider_key":
                continue
            values = [item for item in values if _entry_constraint(item, kind, value)]
        return tuple(values)

    def _candidates_prevalidated(
        self,
        *,
        admitted_package_refs: tuple[str, ...],
        constraints: tuple[SemanticDependencyTargetConstraint, ...],
    ) -> tuple[WorkspaceSemanticMaterializationPackageEntry, ...]:
        self._assert_live()
        values = [
            self._by_package[package_ref]
            for package_ref in admitted_package_refs
            if package_ref in self._by_package
        ]
        for constraint in constraints:
            if constraint.constraint_kind == "semantic_provider_key":
                continue
            values = [
                item
                for item in values
                if _entry_constraint(
                    item,
                    constraint.constraint_kind,
                    constraint.constraint_value,
                )
            ]
        return tuple(values)

    def _policy_admission_parts(
        self,
        *,
        entry: WorkspaceSemanticMaterializationPackageEntry,
        intent: CodeSemanticMaterializationIntent,
    ) -> tuple[dict[str, object], dict[str, object]]:
        self._assert_live()
        if type(entry) is not WorkspaceSemanticMaterializationPackageEntry:
            raise TypeError("membership entry must be exact")
        if type(intent) is not CodeSemanticMaterializationIntent:
            raise TypeError("Code intent must be exact")
        admitted = self._by_package.get(entry.package.package_ref)
        if admitted is not entry:
            raise ContractViolation("membership entry is not host-admitted")
        operations, roots, roles, configurations = self._policy_sets[
            entry.package.package_ref
        ]
        configuration = intent.semantic_configuration_coordinate
        configuration_admitted = (
            entry.participation_policy.allow_unconfigured
            if configuration is None
            else configuration in configurations
        )
        if (
            intent.operation_kind not in operations
            or not set(intent.requested_semantic_root_refs) <= roots
            or not set(intent.requested_terminal_output_roles) <= roles
            or not configuration_admitted
        ):
            raise ContractViolation("participation policy does not admit Code intent")
        return intent.to_wire(), self._policy_wires[entry.package.package_ref]


def _index(
    entries: tuple[WorkspaceSemanticMaterializationPackageEntry, ...], attribute: str
) -> dict[str, tuple[WorkspaceSemanticMaterializationPackageEntry, ...]]:
    result: dict[str, list[WorkspaceSemanticMaterializationPackageEntry]] = {}
    for item in entries:
        result.setdefault(getattr(item, attribute), []).append(item)
    return {key: tuple(value) for key, value in result.items()}


def _entry_constraint(
    entry: WorkspaceSemanticMaterializationPackageEntry, kind: str, value: str
) -> bool:
    if kind == "package_ref":
        return entry.package.package_ref == value
    if kind == "package_kind":
        return entry.package.package_kind == value
    if kind == "package_family":
        return entry.package_family == value
    if kind == "module_ref":
        return entry.module_ref == value
    if kind == "semantic_root_ref":
        return value in entry.owned_semantic_root_refs
    raise ContractViolation("Workspace target constraint unsupported")


__all__ = [
    "WORKSPACE_SEMANTIC_AUTHORED_DEPENDENCY",
    "WORKSPACE_SEMANTIC_MATERIALIZATION_MEMBERSHIP_CATALOG",
    "WORKSPACE_SEMANTIC_MATERIALIZATION_PACKAGE_ENTRY",
    "AdmittedWorkspaceSemanticMaterializationMembershipCatalog",
    "WorkspaceSemanticAuthoredDependency",
    "WorkspaceSemanticMaterializationMembershipCatalog",
    "WorkspaceSemanticMaterializationMembershipResolver",
    "WorkspaceSemanticMaterializationPackageEntry",
]
