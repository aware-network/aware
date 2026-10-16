"""Original declaration/source correspondence for initial product participation.

This is catalog input, not package-authority completion or provider meaning.
It retains the existing Workspace issuer and Code product; no owner is imported.
"""

from __future__ import annotations

import inspect
import os
import threading
from collections.abc import Callable
from dataclasses import dataclass
from threading import RLock
from types import FunctionType, MethodType
from typing import cast
from weakref import WeakKeyDictionary

from aware_code_retained_registry_policy_runtime.declaration_product_projection import (
    DeclaredProductProjection,
    check_declared_product_origin,
    project_declared_inspect_product,
    project_declared_product,
)
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    SemanticPackageCoordinate,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.dependency_inputs import (
    SemanticDependencyPlanningInput,
)
from aware_code_semantic_contract_runtime.product_contribution import (
    SelectedProviderProductContribution,
)
from aware_code_semantic_contract_runtime.retained_declaration_scope import (
    CodeRetainedDependencyScopeClosureV3,
    CodeSelectedPackageSourceBinding,
)
from aware_code_semantic_contract_runtime.retained_input_projections import (
    CodeSemanticDeclarationTargetInventory,
    CodeSemanticPackageContextInput,
)
from aware_code_semantic_contract_runtime.selected_participant_scope import (
    CodeSelectedParticipantViewV1,
)

from .declaration_scope_admission import (
    WorkspaceDeclarationScope,
    WorkspaceDeclarationScopeRuntime,
    WorkspaceSelectedPackageSource,
)
from .materialization_membership_catalog import (
    WorkspaceSemanticAuthoredDependency,
    WorkspaceSemanticMaterializationPackageEntry,
)
from .materialization_selection import (
    WorkspaceSemanticMaterializationParticipationPolicy,
)


@dataclass(slots=True)
class _State:
    issuer: WorkspaceDeclarationScopeRuntime
    declaration: WorkspaceDeclarationScope
    selected: WorkspaceSelectedPackageSource
    product: SelectedProviderProductContribution
    methods: dict[str, tuple[FunctionType, Callable[..., object]]]
    binding: CodeSelectedPackageSourceBinding | None
    projection: DeclaredProductProjection | None
    entry: WorkspaceSemanticMaterializationPackageEntry | None
    pid: int
    thread: int
    terminal: bool = False
    operation_kind: str = "materialize"


class WorkspaceDeclarationProductCorrespondence:
    """Nominal correspondence issued from original Workspace resources only."""

    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls):
        raise TypeError("Workspace issues declaration product correspondences")

    def __reduce__(self):
        raise TypeError("declaration product correspondence is process-local")

    def package(self) -> SemanticPackageCoordinate:
        entry = _state(self).entry
        assert entry is not None
        return entry.package

    def validate_catalog_entry(self, entry: WorkspaceSemanticMaterializationPackageEntry) -> None:
        state = _state(self)
        try:
            if type(entry) is not WorkspaceSemanticMaterializationPackageEntry:
                raise TypeError("exact Workspace catalog entry required")
            current, binding, projection = _derive(state)
            if (
                type(entry) is not WorkspaceSemanticMaterializationPackageEntry
                or entry != state.entry
                or current != entry
                or binding != state.binding
                or projection != state.projection
            ):
                raise RuntimeError("declaration product catalog correspondence changed")
        except BaseException:
            state.terminal = True
            raise

    def check_catalog_entry_locked(self, entry: WorkspaceSemanticMaterializationPackageEntry, guard: object) -> None:
        state = _state(self)
        try:
            if type(entry) is not WorkspaceSemanticMaterializationPackageEntry or entry != state.entry:
                raise RuntimeError("declaration product catalog entry substituted")
            assert state.binding is not None and state.projection is not None
            _call(
                state, "check_selected_package_source_locked", state.selected,
                expectation=state.binding.expectation,
                binding_digest=state.binding.binding_digest, guard=guard,
            )
            check_declared_product_origin(state.product, state.projection)
        except BaseException:
            state.terminal = True
            raise


_STATES: WeakKeyDictionary[WorkspaceDeclarationProductCorrespondence, _State] = WeakKeyDictionary()
_LOCK = RLock()
_PID = os.getpid()
_VALIDATE = WorkspaceDeclarationProductCorrespondence.validate_catalog_entry
_CHECK = WorkspaceDeclarationProductCorrespondence.check_catalog_entry_locked
_PACKAGE = WorkspaceDeclarationProductCorrespondence.package
_METHODS = (
    "read_selected_package_source", "read_declaration_scope",
    "read_selected_participant_view", "inspect_inputs",
    "check_selected_package_source_locked",
)
_DESCRIPTORS = {
    name: cast(FunctionType, inspect.getattr_static(WorkspaceDeclarationScopeRuntime, name))
    for name in _METHODS
}


def _state(handle: object) -> _State:
    # Before inherited lock acquisition. Never dispatch equality/hash on a
    # foreign or restamped holder; recognized restamping is terminal.
    if os.getpid() != _PID:
        raise RuntimeError("declaration product correspondence process changed")
    with _LOCK:
        state = next((record for original, record in _STATES.items() if original is handle), None)
    if type(handle) is not WorkspaceDeclarationProductCorrespondence:
        if state is not None:
            state.terminal = True
        raise TypeError("original declaration product correspondence required")
    if state is None or state.terminal:
        raise RuntimeError("declaration product correspondence unavailable")
    if state.pid != os.getpid() or state.thread != threading.get_ident():
        raise RuntimeError("declaration product correspondence execution changed")
    return state


def validate_declaration_product_correspondence(
    handle: WorkspaceDeclarationProductCorrespondence,
    entry: WorkspaceSemanticMaterializationPackageEntry,
) -> None:
    state = _state(handle)
    if inspect.getattr_static(handle, "validate_catalog_entry") is not _VALIDATE:
        state.terminal = True
        raise RuntimeError("declaration product validator substituted")
    _VALIDATE(handle, entry)


def read_declaration_product_correspondence_package(
    handle: WorkspaceDeclarationProductCorrespondence,
) -> SemanticPackageCoordinate:
    state = _state(handle)
    if inspect.getattr_static(handle, "package") is not _PACKAGE:
        state.terminal = True
        raise RuntimeError("declaration product package reader substituted")
    return _PACKAGE(handle)


def validate_declaration_product_planning_input(
    handle: WorkspaceDeclarationProductCorrespondence,
    entry: WorkspaceSemanticMaterializationPackageEntry,
    planning_input: SemanticDependencyPlanningInput,
) -> None:
    """Bridge original selected-source and catalog identities, never equate them."""
    state = _state(handle)
    try:
        validate_declaration_product_correspondence(handle, entry)
        if type(planning_input) is not SemanticDependencyPlanningInput:
            raise TypeError("exact original planning input required")
        planning_input.__post_init__()
        assert state.binding is not None
        if (
            planning_input.package != entry.package
            or planning_input.source_identity_digest
            != state.binding.expectation.source_identity_digest
        ):
            raise RuntimeError("original product planning source differs")
    except BaseException:
        state.terminal = True
        raise


def check_declaration_product_correspondence_locked(
    handle: WorkspaceDeclarationProductCorrespondence,
    entry: WorkspaceSemanticMaterializationPackageEntry,
    guard: object,
) -> None:
    state = _state(handle)
    if inspect.getattr_static(handle, "check_catalog_entry_locked") is not _CHECK:
        state.terminal = True
        raise RuntimeError("declaration product locked validator substituted")
    _CHECK(handle, entry, guard)


def _call(state: _State, name: str, *args: object, **kwargs: object) -> object:
    descriptor, method = state.methods[name]
    if inspect.getattr_static(state.issuer, name) is not descriptor:
        raise RuntimeError("original declaration product source method substituted")
    result = method(*args, **kwargs)
    if inspect.getattr_static(state.issuer, name) is not descriptor:
        raise RuntimeError("original declaration product source method substituted")
    return result


def _derive(state: _State) -> tuple[WorkspaceSemanticMaterializationPackageEntry, CodeSelectedPackageSourceBinding, DeclaredProductProjection]:
    if type(state.operation_kind) is not str or state.operation_kind not in ("materialize", "inspect"):
        raise RuntimeError("original declaration product operation unavailable")
    binding = _call(state, "read_selected_package_source", state.selected)
    closure = _call(state, "read_declaration_scope", state.declaration)
    view = _call(
        state, "read_selected_participant_view", state.declaration, state.selected
    )
    inputs = _call(state, "inspect_inputs", state.selected)
    if (
        type(binding) is not CodeSelectedPackageSourceBinding
        or type(closure) is not CodeRetainedDependencyScopeClosureV3
        or type(view) is not CodeSelectedParticipantViewV1
        or type(inputs) is not tuple or len(inputs) != 2
    ):
        raise TypeError("exact original Workspace input projections required")
    context, inventory = cast(tuple[object, object], inputs)
    if type(context) is not CodeSemanticPackageContextInput or type(inventory) is not CodeSemanticDeclarationTargetInventory:
        raise TypeError("exact original Workspace package/inventory required")
    if state.operation_kind == "materialize":
        projection = project_declared_product(closure, view, state.product)
    elif state.operation_kind == "inspect":
        projection = project_declared_inspect_product(closure, view, state.product)
    choice = binding.expectation
    if (
        projection.package.occurrence_key
        != (choice.scope_key, choice.module_id, choice.package_id)
        or context.package.manifest_digest != choice.manifest_content_digest
        or context.source_identity_digest != choice.source_identity_digest
        or inventory.package != context.package
        or inventory.source_identity_digest != context.source_identity_digest
    ):
        raise RuntimeError("original product source correspondence differs")
    if context.config_id is not None or context.config_key is not None:
        raise RuntimeError("configured participation coordinate unavailable")
    if len(projection.manifest_contracts) != 1:
        raise RuntimeError("product manifest matcher contract ambiguous")
    source_digest = binding.binding_digest
    # Explicit original Workspace declaration/candidate binding. This is not an
    # owner-produced authority coordinate and never labels raw TOML as JSON.
    source_ref = "workspace-selected-source:" + source_digest.value
    policy_core = {
        "selected_source_binding": source_digest.to_wire(),
        "registration": projection.package.registration_declaration_digest.to_wire(),
        "profile": projection.registry.profile_digest.to_wire(),
        "roles": list(projection.terminal_roles),
    }
    if state.operation_kind == "inspect":
        policy_core["operation_kind"] = "inspect"
    policy_digest = ContentDigest.of_bytes(canonical_json_bytes(policy_core))
    policy = WorkspaceSemanticMaterializationParticipationPolicy.create(
        policy_ref="workspace-declared-product-policy:" + policy_digest.value,
        policy_revision=2, package_ref=context.package.package_ref,
        allowed_operation_kinds=(state.operation_kind,),
        allowed_semantic_root_refs=projection.package.owned_roots,
        allowed_terminal_output_roles=projection.terminal_roles,
        allow_unconfigured=True, allowed_semantic_configuration_coordinates=(),
    )
    dependencies = tuple(
        WorkspaceSemanticAuthoredDependency.create(
            dependency_kind=item.dependency_kind, dependency_ref=item.dependency_ref,
            admitted_target_package_refs=tuple(target.package.package_ref for target in item.targets),
            allowed_target_constraints=item.target_constraints,
        ) for item in inventory.entries
    )
    entry = WorkspaceSemanticMaterializationPackageEntry.create(
        repository_ref=closure.repository_binding_ref,
        workspace_ref=choice.scope_key, module_ref=choice.module_id,
        package=context.package, package_family=projection.registry.semantic_package_family,
        package_role=projection.registry.semantic_contract.role,
        manifest_contract=projection.manifest_contracts[0],
        manifest_relative_path=context.manifest_relative_path,
        source_authority_ref=source_ref, source_authority_digest=source_digest,
        owned_semantic_root_refs=projection.package.owned_roots,
        authored_dependencies=dependencies, participation_policy=policy,
        allowed_profile_refs=(projection.registry.profile_ref,),
    )
    if _call(state, "read_selected_package_source", state.selected) != binding:
        raise RuntimeError("selected product source moved during projection")
    return entry, binding, projection


def capture_declaration_product_correspondence(
    *, issuer: WorkspaceDeclarationScopeRuntime, declaration: WorkspaceDeclarationScope,
    selected: WorkspaceSelectedPackageSource, product: SelectedProviderProductContribution,
) -> tuple[WorkspaceDeclarationProductCorrespondence, WorkspaceSemanticMaterializationPackageEntry]:
    """Prepare outside parent exclusion; original locked checks finish admission."""
    if (
        type(issuer) is not WorkspaceDeclarationScopeRuntime
        or type(declaration) is not WorkspaceDeclarationScope
        or type(selected) is not WorkspaceSelectedPackageSource
    ):
        raise TypeError("original Workspace declaration and selected source required")
    methods: dict[str, tuple[FunctionType, Callable[..., object]]] = {}
    for name in _METHODS:
        descriptor = cast(object, inspect.getattr_static(issuer, name))
        if descriptor is not _DESCRIPTORS[name] or not inspect.isfunction(descriptor):
            raise TypeError("original Workspace source method required")
        methods[name] = descriptor, cast(Callable[..., object], MethodType(descriptor, issuer))
    state = _State(
        issuer, declaration, selected, product, methods, None, None, None,
        os.getpid(), threading.get_ident(),
    )
    entry, state.binding, state.projection = _derive(state)
    state.entry = entry
    handle = object.__new__(WorkspaceDeclarationProductCorrespondence)
    with _LOCK:
        _STATES[handle] = state
    return handle, entry


def capture_declaration_inspect_product_correspondence(
    *, issuer: WorkspaceDeclarationScopeRuntime, declaration: WorkspaceDeclarationScope,
    selected: WorkspaceSelectedPackageSource, product: SelectedProviderProductContribution,
) -> tuple[WorkspaceDeclarationProductCorrespondence, WorkspaceSemanticMaterializationPackageEntry]:
    """Issue inspect-only correspondence from the same original declarations/product."""
    if (
        type(issuer) is not WorkspaceDeclarationScopeRuntime
        or type(declaration) is not WorkspaceDeclarationScope
        or type(selected) is not WorkspaceSelectedPackageSource
    ):
        raise TypeError("original Workspace declaration and selected source required")
    methods: dict[str, tuple[FunctionType, Callable[..., object]]] = {}
    for name in _METHODS:
        descriptor = cast(object, inspect.getattr_static(issuer, name))
        if descriptor is not _DESCRIPTORS[name] or not inspect.isfunction(descriptor):
            raise TypeError("original Workspace source method required")
        methods[name] = descriptor, cast(Callable[..., object], MethodType(descriptor, issuer))
    state = _State(
        issuer, declaration, selected, product, methods, None, None, None,
        os.getpid(), threading.get_ident(),
    )
    state.operation_kind = "inspect"
    entry, state.binding, state.projection = _derive(state)
    state.entry = entry
    handle = object.__new__(WorkspaceDeclarationProductCorrespondence)
    with _LOCK:
        _STATES[handle] = state
    return handle, entry
