"""Derive one bounded v3 participant set from complete retained declarations.

Unselected v1 declarations stay in the original closure. This portable result
cannot authenticate Workspace membership, selected source, or execution.
"""

from __future__ import annotations

from dataclasses import fields
from pathlib import PurePosixPath

from aware_code_module_manifest_contract_runtime import AwareModuleSpecV3
from aware_code_module_manifest_contract_runtime.parser import parse_module_manifest
from aware_code_module_manifest_contract_runtime.profile_parser import parse_profile_manifest
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.retained_declaration_scope import (
    CodeRetainedDependencyScopeClosureV3,
)
from aware_code_semantic_contract_runtime.selected_participant_scope import (
    MAX_SELECTED_PARTICIPANTS,
    CodeSelectedParticipant,
    CodeSelectedParticipantRelationship,
    CodeSelectedParticipantViewV1,
    CodeSelectedProfileRelationship,
)

from .calculation import _plain, _validate_declared_package_kind
from .qualified_calculation import _address_scope
from .qualified_scope import validate_selected_scope_graph_v3


def derive_selected_participant_view(
    closure: CodeRetainedDependencyScopeClosureV3,
    *,
    scope_key: str,
    module_id: str,
    package_id: str,
) -> CodeSelectedParticipantViewV1:
    """Follow exact v3 registration and dependency arrows from one root.

    Every retained module is parsed and checked against complete projected
    membership. Only reached occurrences must carry complete v3 semantic
    declarations. Profile associations are interpreted only for reached
    imported registrations; unrelated v1 modules remain nonparticipants.
    """
    if type(closure) is not CodeRetainedDependencyScopeClosureV3:
        raise TypeError("exact retained declaration closure required")
    validate_selected_scope_graph_v3(closure)
    root = CodeSelectedParticipant(scope_key, module_id, package_id)
    models = {}
    packages = {}
    declarations = {}
    for scope in closure.scopes:
        projection = scope.projection
        projected = {(p.module_id, p.package_id): p for p in projection.packages}
        authored = set()
        for module in projection.modules:
            model = parse_module_manifest(module.manifest.body)
            models[(scope.scope_key, module.module_id)] = model
            directory = str(PurePosixPath(module.manifest.relative_path).parent)
            prefix = "" if directory == "." else directory + "/"
            v3_declarations = (
                model.package_declarations if type(model) is AwareModuleSpecV3
                else (None,) * len(model.packages)
            )
            for package, declaration in zip(
                model.packages, v3_declarations, strict=True
            ):
                key = (scope.scope_key, module.module_id, package.id)
                expected = projected.get((module.module_id, package.id))
                expected_path = prefix + package.manifest
                if (
                    key in authored
                    or expected is None
                    or expected.package_kind != package.kind
                    or expected.manifest.relative_path != expected_path
                    or expected.module_manifest_path != module.manifest.relative_path
                    or expected.package_root
                    != (str(PurePosixPath(expected_path).parent) or ".")
                ):
                    raise ContractViolation("complete authored package membership differs")
                authored.add(key)
                packages[key] = expected
                declarations[key] = declaration
        if authored != {(scope.scope_key, *key) for key in projected}:
            raise ContractViolation("complete retained package membership differs")

    if (root.scope_key, root.module_id, root.package_id) not in packages:
        raise ContractViolation("selected package absent from complete declarations")
    pending = [root]
    selected: set[CodeSelectedParticipant] = set()
    occurrence_required = {root}
    relationships: set[CodeSelectedParticipantRelationship] = set()
    profiles: set[CodeSelectedProfileRelationship] = set()
    while pending:
        current = pending.pop()
        if current in selected:
            continue
        if len(selected) >= MAX_SELECTED_PARTICIPANTS:
            raise ContractViolation("selected participant count bound")
        key = (current.scope_key, current.module_id, current.package_id)
        model = models.get((current.scope_key, current.module_id))
        declaration = declarations.get(key)
        if type(model) is not AwareModuleSpecV3 or declaration is None:
            raise ContractViolation("selected participant requires v3 declaration")
        if not declaration.occurrence_declared:
            if current in occurrence_required:
                raise ContractViolation("selected semantic occurrence unavailable")
            selected.add(current)
            continue
        if any(
            getattr(declaration.occurrence, field.name).state == "unavailable"
            for field in fields(declaration.occurrence)
        ):
            raise ContractViolation("selected v3 participant incomplete")
        selected.add(current)
        occurrence = declaration.occurrence
        address = _plain(occurrence.registration.value)
        target_scope = _address_scope(closure, current.scope_key, model, address)
        target = CodeSelectedParticipant(
            target_scope, address["module_id"], address["package_id"]
        )
        target_key = (target.scope_key, target.module_id, target.package_id)
        target_declaration = declarations.get(target_key)
        if target_declaration is None:
            raise ContractViolation("selected registration package must be v3")
        registration = [
            item for item in target_declaration.registrations
            if _plain(item)["key"] == address["registration_key"]
        ]
        if len(registration) != 1:
            raise ContractViolation("selected registration declaration unavailable")
        provider_key = _plain(registration[0])["semantic_contract"]["provider_key"]
        if target_scope != current.scope_key:
            matching_edges = [
                (edge, association)
                for edge, association in zip(
                    closure.edges, closure.profile_associations, strict=True
                )
                if edge.declaring_scope_key == current.scope_key
                and edge.target_scope_key == target_scope
                and provider_key in edge.semantic_contract_provider_keys.value
            ]
            if not matching_edges:
                raise ContractViolation("selected import lacks direct profile edge")
            entitled = False
            for edge, association in matching_edges:
                profile_key = edge.profile_key.value
                if type(profile_key) is not str:
                    raise ContractViolation("exact imported profile key required")
                meaning = parse_profile_manifest(
                    association.manifest.body,
                    source_label=association.manifest.relative_path,
                )
                if (
                    meaning.aware_semantic_contract_profile != 1
                    or meaning.profile.key != profile_key
                    or meaning.profile.status != "active"
                ):
                    raise ContractViolation("selected imported profile differs")
                restrictions = edge.semantic_contract_provider_keys.value
                if type(restrictions) is not tuple:
                    raise ContractViolation("exact imported provider restrictions required")
                requested = set(restrictions)
                found = set()
                members = set()
                for member in meaning.providers:
                    if member.provider_key not in requested:
                        continue
                    if member.status != "active":
                        raise ContractViolation("selected profile member inactive")
                    for candidate_key, candidate in declarations.items():
                        if candidate_key[0:2] != (target_scope, member.module_id) or candidate is None:
                            continue
                        if any(
                            _plain(item)["semantic_contract"]["provider_key"]
                            == member.provider_key
                            for item in candidate.registrations
                        ):
                            members.add(CodeSelectedParticipant(*candidate_key))
                            found.add(member.provider_key)
                if found != requested:
                    raise ContractViolation("selected profile member unavailable")
                if target in members:
                    entitled = True
                pending.extend(members)
                profiles.add(CodeSelectedProfileRelationship(
                    edge.declaring_scope_key,
                    edge.declaration.dependency_index,
                    edge.declaration.profile_package_index,
                    edge.target_scope_key,
                    profile_key,
                    association.manifest.content_digest,
                ))
            if not entitled:
                raise ContractViolation("selected registration not entitled by profile")
        relationships.add(CodeSelectedParticipantRelationship(
            "registration", current, target
        ))
        pending.append(target)
        for mapping in _plain(occurrence.dependency_targets.value):
            for address in mapping["targets"]:
                dependency_scope = _address_scope(
                    closure, current.scope_key, model, address
                )
                dependency = CodeSelectedParticipant(
                    dependency_scope, address["module_id"], address["package_id"]
                )
                if (dependency.scope_key, dependency.module_id, dependency.package_id) not in packages:
                    raise ContractViolation("selected direct target absent")
                relationships.add(CodeSelectedParticipantRelationship(
                    "direct_dependency", current, dependency
                ))
                occurrence_required.add(dependency)
                pending.append(dependency)

    for participant in occurrence_required:
        declaration = declarations.get((
            participant.scope_key, participant.module_id, participant.package_id
        ))
        if declaration is None or not declaration.occurrence_declared:
            raise ContractViolation("selected direct target lacks v3 occurrence")

    return CodeSelectedParticipantViewV1(
        closure.closure_digest,
        root,
        tuple(sorted(selected)),
        tuple(sorted(relationships, key=lambda item: item.ordering_key)),
        tuple(sorted(profiles, key=lambda item: item.ordering_key)),
    )


def validate_selected_participant_view(
    closure: CodeRetainedDependencyScopeClosureV3,
    view: CodeSelectedParticipantViewV1,
) -> None:
    """Recompute the complete set; a decoded or copied view is never admission."""
    if type(view) is not CodeSelectedParticipantViewV1:
        raise TypeError("exact selected participant view required")
    view.__post_init__()
    expected = derive_selected_participant_view(
        closure,
        scope_key=view.root.scope_key,
        module_id=view.root.module_id,
        package_id=view.root.package_id,
    )
    if view != expected:
        raise ContractViolation("selected participant set differs from declarations")


def selected_qualified_occurrences(
    closure: CodeRetainedDependencyScopeClosureV3,
    view: CodeSelectedParticipantViewV1,
):
    """Interpret only the complete Code-selected v3 occurrence set.

    The full closure remains the input to validation. The view is portable
    meaning and must still be authenticated by the original Workspace issuer
    before any host can use these rows as policy evidence.
    """
    validate_selected_participant_view(closure, view)
    packages = {
        (scope.scope_key, package.module_id, package.package_id): package
        for scope in closure.scopes
        for package in scope.projection.packages
    }
    declarations = {}
    models = {}
    for scope in closure.scopes:
        for module in scope.projection.modules:
            model = parse_module_manifest(module.manifest.body)
            models[(scope.scope_key, module.module_id)] = model
            if type(model) is AwareModuleSpecV3:
                declarations.update({
                    (scope.scope_key, module.module_id, item.package_id): item
                    for item in model.package_declarations
                })
    rows = []
    for participant in view.participants:
        key = (participant.scope_key, participant.module_id, participant.package_id)
        declaration = declarations.get(key)
        if declaration is None:
            raise ContractViolation("selected v3 package declaration unavailable")
        if not declaration.occurrence_declared:
            continue
        occurrence = declaration.occurrence
        model = models[(participant.scope_key, participant.module_id)]
        address = _plain(occurrence.registration.value)
        target_scope = _address_scope(closure, participant.scope_key, model, address)
        target = declarations.get((
            target_scope, address["module_id"], address["package_id"]
        ))
        if target is None:
            raise ContractViolation("selected v3 registration unavailable")
        matches = [
            item for item in target.registrations
            if _plain(item)["key"] == address["registration_key"]
        ]
        if len(matches) != 1:
            raise ContractViolation("selected v3 registration ambiguous")
        registration = matches[0]
        package = packages[key]
        meaning = _plain(registration)
        _validate_declared_package_kind(meaning, package.package_kind)
        if package.manifest_relative_path != meaning["manifest_filename"]:
            raise ContractViolation("selected registration manifest filename differs")
        rows.append((key, package, occurrence, registration))
    return tuple(rows)


def selected_qualified_occurrence(
    closure: CodeRetainedDependencyScopeClosureV3,
    view: CodeSelectedParticipantViewV1,
    key: tuple[str, str, str],
):
    matches = [row for row in selected_qualified_occurrences(closure, view) if row[0] == key]
    if len(matches) != 1:
        raise ContractViolation("selected v3 occurrence unavailable")
    return matches[0]


__all__ = [
    "derive_selected_participant_view",
    "selected_qualified_occurrence",
    "selected_qualified_occurrences",
    "validate_selected_participant_view",
]
