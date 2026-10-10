"""Deterministic source calculation over portable inputs, never nominal issuance."""

from dataclasses import fields
from posixpath import dirname
from typing import Any, NoReturn, cast

from aware_code_module_manifest_contract_runtime import (
    AwareModuleSpecV2,
    AwareModuleSpecV3,
    DeclarationTable,
    parse_module_manifest,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticContractCatalog,
)
from aware_code_semantic_contract_runtime.registry_policy import (
    RegistryPolicy,
    RegistryPolicyGrant,
)
from aware_code_semantic_contract_runtime.retained_scope_interfaces import (
    CodeRetainedScopeProjection,
    encode_retained_scope_projection,
)

FIXED_POLICY_PROFILE = "aware.code.retained-registry-policy.v3"


def _plain(value) -> Any:
    if type(value) is DeclarationTable:
        return {key: _plain(item) for key, item in value.entries}
    if type(value) is tuple:
        return [_plain(item) for item in value]
    return value


def _refuse(message) -> NoReturn:
    raise ContractViolation(message)


def _catalog_correspondence(registration, catalog, *, package_kind):
    """Portable exact profile/provider correspondence, not live catalog admission."""
    provider_key = registration["semantic_contract"]["provider_key"]
    for stage in registration["profiles"]:
        matches = [
            entry
            for entry in catalog.entries
            if entry.semantic_provider_key == provider_key
            and entry.profile_declaration.profile_ref == stage["profile_ref"]
            and entry.profile_declaration.version == stage["profile_version"]
            and entry.profile_declaration.digest.to_wire() == stage["profile_digest"]
        ]
        if len(matches) != 1:
            _refuse("exact stage catalog profile unavailable or ambiguous")
        _execution_entry_correspondence(
            registration, matches[0], package_kind=package_kind
        )


def _validate_declared_package_kind(registration, package_kind):
    """Use only the original provider declaration; omitted means identity only."""
    accepted = registration.get(
        "declared_package_kinds", [registration["semantic_package_kind"]]
    )
    if package_kind not in accepted:
        _refuse("package kind correspondence unavailable")


def _execution_entry_correspondence(registration, entry, *, package_kind):
    """Validate the selected executable entry; relationship grants do not do this."""
    provider_key = registration["semantic_contract"]["provider_key"]
    _validate_declared_package_kind(registration, package_kind)
    profile = entry.profile_declaration
    if (
        registration["semantic_package_family"] not in entry.package_families
        or registration["semantic_contract"]["role"] not in entry.package_roles
        or package_kind not in profile.package_kinds
    ):
        _refuse("registration catalog package correspondence differs")
    providers = [p for p in profile.providers if p.provider_key == provider_key]
    bindings = [
        b for b in entry.provider_execution_bindings if b.provider_key == provider_key
    ]
    if (
        len(providers) != 1
        or len(bindings) != 1
        or package_kind not in providers[0].package_kinds
    ):
        _refuse("catalog provider declaration or execution binding unavailable")


def calculate_registry_policy(
    scope: CodeRetainedScopeProjection,
    catalog: CodeSemanticContractCatalog,
) -> RegistryPolicy:
    """Return existing input-only policy; no callbacks, scans, grants or rules accepted.

    The trusted host must separately bind original scope validation, admitted
    catalog and exact live selected-provider machinery before nominal issuance.
    This function cannot establish module enumeration completeness from TOML alone.
    A valid host catalog is retained as an input, but relationship-only targets
    need not occur in that executable catalog. No returned grant authorizes an
    execution or fulfills a result demand.
    """
    encoded_scope = encode_retained_scope_projection(scope)
    if type(catalog) is not CodeSemanticContractCatalog:
        _refuse("exact Code catalog required")
    catalog.__post_init__()
    _, projected, declarations, participants = _scope_declarations(
        scope, versions=(AwareModuleSpecV2,)
    )
    grants = []
    for key, occurrence in participants.items():
        address = _plain(occurrence.registration.value)
        provider = declarations.get((address["module_id"], address["package_id"]))
        if provider is None:
            _refuse("registration target outside same scope")
        registrations = [
            _plain(reg)
            for reg in provider.registrations
            if _plain(reg)["key"] == address["registration_key"]
        ]
        if len(registrations) != 1:
            _refuse("exact retained registration unavailable")
        registration = registrations[0]
        package = projected[key]
        _validate_declared_package_kind(registration, package.package_kind)
        if package.manifest_relative_path != registration["manifest_filename"]:
            _refuse("registration manifest filename differs")
        # Grants authorize source relationship policy, not provider execution.
        # Registration is authenticated from the retained declaration above.
        # Original operation/target execution entrances validate exact catalog
        # and live selected-provider correspondence when execution is requested.
        for mapping in _plain(occurrence.dependency_targets.value):
            for target in mapping["targets"]:
                if (target["module_id"], target["package_id"]) not in participants:
                    _refuse("dependency target occurrence unavailable in same scope")
        grants.append(
            RegistryPolicyGrant(
                package.source_identity_digest,
                ContentDigest.of_bytes(canonical_json_bytes(registration)),
                package.package_kind,
                registration["semantic_package_kind"],
                cast(str, occurrence.namespace.value),
                cast(tuple[str, ...], occurrence.owned_roots.value),
            )
        )
    # Existing policy validation refuses all conflicts; no winner or partial result.
    return RegistryPolicy(
        ContentDigest.of_bytes(encoded_scope),
        tuple(
            sorted(
                grants,
                key=lambda g: (
                    g.source_identity_digest.value,
                    g.registration_declaration_digest.value,
                ),
            )
        ),
    )


def _scope_declarations(scope, *, versions):
    """Shared authored membership/participation checks; caller pins grammar versions."""
    projected = {(p.module_id, p.package_id): p for p in scope.packages}
    declarations = {}
    participants = {}
    models = {}
    for module in scope.modules:
        model = parse_module_manifest(module.manifest.body)
        if (
            not isinstance(model, (AwareModuleSpecV2, AwareModuleSpecV3))
            or type(model) not in versions
        ):
            _refuse("fixed policy requires all modules v2")
        models[module.module_id] = model
        prefix = dirname(module.manifest.relative_path)
        for package, declaration in zip(
            model.packages, model.package_declarations, strict=True
        ):
            key = (module.module_id, package.id)
            if key in declarations:
                _refuse("duplicate authored package")
            declarations[key] = declaration
            retained = projected.get(key)
            expected_path = (
                prefix + "/" + package.manifest if prefix else package.manifest
            )
            if (
                retained is None
                or retained.package_kind != package.kind
                or retained.manifest.relative_path != expected_path
                or retained.package_root != (dirname(expected_path) or ".")
            ):
                _refuse("authored package and retained membership differ")
            if declaration.occurrence_declared:
                occurrence = declaration.occurrence
                if any(
                    getattr(occurrence, f.name).state == "unavailable"
                    for f in fields(occurrence)
                ):
                    _refuse("incomplete authored participant")
                participants[key] = occurrence
    if set(declarations) != set(projected):
        _refuse("extra or missing scope packages")
    return models, projected, declarations, participants
