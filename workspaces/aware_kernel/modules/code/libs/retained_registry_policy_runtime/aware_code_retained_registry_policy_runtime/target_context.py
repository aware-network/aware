"""Original Code target correspondence; no target matching or Workspace imports."""

import inspect
import os
from contextlib import nullcontext
from copy import deepcopy
from dataclasses import dataclass, field
from weakref import WeakKeyDictionary

from aware_code_module_manifest_contract_runtime import (
    AwareModuleSpecV2,
    parse_module_manifest,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    SemanticPackageCoordinate,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.retained_scope_interfaces import (
    CodeRetainedScopeProjection,
)
from aware_code_semantic_contract_runtime.retained_declaration_scope import (
    CodeSelectedPackageSourceBinding,
)
from aware_code_semantic_contract_runtime.selected_participant_scope import (
    CodeSelectedParticipantViewV1,
)
from aware_code_semantic_contract_runtime.target_context_interfaces import (
    RetainedTargetExpectation,
    SourceTargetRegistrationFields,
    TargetContextFields,
)

from . import direct_host as direct
from . import operation_context as contexts
from .calculation import _catalog_correspondence, _plain
from .retained_input_admission import _publication


class TargetContextAdmission(direct._Opaque):
    def __init_subclass__(cls, **kwargs):
        raise TypeError("target context is sealed")


class SourceTargetContextAdmission(direct._Opaque):
    """Original relationship-only context; cannot enter the capability reader."""

    def __init_subclass__(cls, **kwargs):
        raise TypeError("source target context is sealed")


@dataclass
class _State:
    host: object
    issuer: object
    method: direct._Entrance
    resources: tuple
    pid: int
    admissions: WeakKeyDictionary = field(default_factory=WeakKeyDictionary)

    def check(self):
        if self.pid != os.getpid():
            raise ContractViolation("target context process changed")
        state = direct._state(self.host)
        self.method.check()
        for name, resource, descriptor in self.resources:
            if (
                inspect.getattr_static(self.issuer, name) is not descriptor
                or getattr(self.issuer, name) is not resource
            ):
                raise ContractViolation("original target resource substituted")
        return state


@dataclass(frozen=True)
class _Record:
    source_context: object
    inventory: object
    target: object
    source_identity: ContentDigest
    package: SemanticPackageCoordinate
    evidence: tuple
    fields: TargetContextFields | SourceTargetRegistrationFields
    source_only: bool


_ORIGINS = WeakKeyDictionary()
_INSTALLED = WeakKeyDictionary()


def _state(origin):
    if type(origin) is not TargetContextOrigin:
        raise TypeError("exact target origin required")
    state = _ORIGINS.get(origin)
    if state is None:
        raise ContractViolation("foreign target origin")
    for name, method in _METHODS.items():
        if inspect.getattr_static(origin, name) is not method:
            raise ContractViolation("original target entrance substituted")
    state.check()
    return state


def _derive(
    state, context, inventory, target, source_identity, package, *, source_only=False
):
    host = state.check()
    if getattr(host, "source_rail", None) == "declaration_v3":
        from .declaration_host import _selected_policy_source, _selected_policy_view

        original = contexts._CONTEXTS.get(context)
        if original is None or original.host is not state.host:
            raise ContractViolation("original source context unavailable")
        with (
            contexts._synchronous_validation_window(state.host, context),
            _selected_policy_source(state.host, original.policy) as source,
        ):
            return _derive_body(
                state, context, inventory, target, source_identity, package,
                source_only=source_only, v3_source=source,
                v3_view=_selected_policy_view(state.host, original.policy),
            )
    if host.qualified:
        from .qualified_host import (
            _ACTIVE_READ_SESSION,
            operation_local_read_session,
            policy_source,
        )

        original = contexts._CONTEXTS.get(context)
        if original is None or original.host is not state.host:
            raise ContractViolation("original source context unavailable")
        session = (
            nullcontext()
            if _ACTIVE_READ_SESSION.get() is not None
            else operation_local_read_session(state.host, original.policy)
        )
        with (
            contexts._synchronous_validation_window(state.host, context),
            session,
            policy_source(
                state.host, original.policy, purpose="source_planning"
            ) as source,
        ):
            return _derive_body(
                state,
                context,
                inventory,
                target,
                source_identity,
                package,
                source_only=source_only,
                qualified=source,
            )
    return _derive_body(
        state,
        context,
        inventory,
        target,
        source_identity,
        package,
        source_only=source_only,
    )


def _derive_body(
    state,
    context,
    inventory,
    target,
    source_identity,
    package,
    *,
    source_only=False,
    qualified=None,
    v3_source=None,
    v3_view=None,
):
    snapshot = None
    if (
        type(source_identity) is not ContentDigest
        or type(package) is not SemanticPackageCoordinate
    ):
        raise TypeError("exact target coordinates required")
    source_identity.__post_init__()
    package.__post_init__()
    expected = contexts.source_planning_expectation(state.host, context)
    original = contexts._CONTEXTS.get(context)
    if original is None or original.host is not state.host:
        raise ContractViolation("original source context unavailable")
    comparison = RetainedTargetExpectation(
        expected, deepcopy(source_identity), deepcopy(package)
    )
    expected_copy = contexts.source_planning_expectation(state.host, context)
    if (
        state.method.call(target, inventory_admission=inventory, expected=comparison)
        is not None
    ):
        raise ContractViolation("target validator returned non-None")
    contexts._equal(comparison.source_planning, expected_copy)
    if (
        comparison.target_source_identity_digest != source_identity
        or comparison.target_package != package
    ):
        raise ContractViolation("target validator changed expected coordinates")
    target_binding = None
    if v3_source is not None:
        from .declaration_eligibility import calculate_declaration_eligibility
        from .declaration_host import selected_source_grant_candidate
        from .selected_participant_calculation import selected_qualified_occurrence

        host, scope, policy, _root = v3_source
        if type(v3_view) is not CodeSelectedParticipantViewV1:
            raise ContractViolation("original selected participant view required")
        prepared = host.declaration_binding
        if prepared is None or prepared.closure is not scope:
            raise ContractViolation("original target declaration unavailable")
        target_binding = host.methods["selected_read"].call(target)
        if type(target_binding) is not CodeSelectedPackageSourceBinding:
            raise ContractViolation("original selected target source required")
        target_binding.__post_init__()
        selected = target_binding.expectation
        if (
            selected.declaration != prepared.expectation
            or selected.closure_digest != scope.closure_digest
            or selected.source_identity_digest != source_identity
            or selected.manifest_content_digest != package.manifest_digest
        ):
            raise ContractViolation("selected target belongs to another declaration")
        host.methods["selected_validate"].call(
            target, expectation=selected,
            binding_digest=target_binding.binding_digest,
        )
        _, retained, _, registration = selected_qualified_occurrence(
            scope, v3_view,
            (selected.scope_key, selected.module_id, selected.package_id),
        )
        declared = _plain(registration)
        if retained.manifest_relative_path != selected.manifest_relative_path:
            raise ContractViolation("selected target manifest path differs")
        grant = selected_source_grant_candidate(
            scope, calculate_declaration_eligibility(scope, selected_view=v3_view),
            target_binding,
        )
        if (
            grant.source_identity_digest != source_identity
            or grant.registration_declaration_digest
            != ContentDigest.of_bytes(canonical_json_bytes(declared))
        ):
            raise ContractViolation("selected target registration differs")
        digest = scope.closure_digest
    elif qualified is not None:
        from .qualified_calculation import qualified_occurrence

        host, scope, policy = qualified
        retained, _, declaration = qualified_occurrence(scope, source_identity)
        declared = _plain(declaration)
        digest = scope.closure_digest
    else:
        policy = direct.validate_admitted_registry_policy(state.host, original.policy)
        host = state.check()
        retained_policy = direct._POLICIES.get(original.policy)
        if retained_policy is None or retained_policy[0] is not state.host:
            raise ContractViolation("original target policy unavailable")
        _, snapshot, digest, _ = retained_policy
        scope = host.methods["read"].call(snapshot)
        if (
            type(scope) is not CodeRetainedScopeProjection
            or scope.projection_digest != digest
        ):
            raise ContractViolation("target scope changed")
        matches = [
            p for p in scope.packages if p.source_identity_digest == source_identity
        ]
        if len(matches) != 1:
            raise ContractViolation("unique target source required")
        retained = matches[0]
        if (
            retained.manifest.content_digest != package.manifest_digest
            or retained.package_kind != package.package_kind
        ):
            raise ContractViolation("target manifest or kind differs")
        declarations = {}
        for module in scope.modules:
            model = parse_module_manifest(module.manifest.body)
            if type(model) is not AwareModuleSpecV2:
                raise ContractViolation("target requires original v2 scope")
            for declaration in model.package_declarations:
                key = (module.module_id, declaration.package_id)
                if key in declarations:
                    raise ContractViolation("duplicate target declaration")
                declarations[key] = declaration
        occurrence = declarations[(retained.module_id, retained.package_id)].occurrence
        address = _plain(occurrence.registration.value)
        owner = declarations[(address["module_id"], address["package_id"])]
        registrations = [
            _plain(r)
            for r in owner.registrations
            if _plain(r)["key"] == address["registration_key"]
        ]
        if len(registrations) != 1:
            raise ContractViolation("original target registration unavailable")
        declared = registrations[0]
    if (
        retained.manifest.content_digest != package.manifest_digest
        or retained.package_kind != package.package_kind
    ):
        raise ContractViolation("target manifest or kind differs")
    declaration_digest = ContentDigest.of_bytes(canonical_json_bytes(declared))
    if v3_source is None:
        grants = [
            g
            for g in policy.grants
            if g.source_identity_digest == source_identity
            and g.registration_declaration_digest == declaration_digest
        ]
        if len(grants) != 1:
            raise ContractViolation("original target policy grant unavailable")
    elif grant.registration_declaration_digest != declaration_digest:
        raise ContractViolation("original target declaration changed")
    if source_only:
        result = SourceTargetRegistrationFields(
            declared["semantic_package_family"],
            declared["semantic_contract"]["role"],
            declared["semantic_contract"]["provider_key"],
            declared["semantic_package_kind"],
            declared["manifest_contract_kind"],
            declared["manifest_filename"],
        )
        evidence = (digest, declaration_digest)
    else:
        catalog = host.check()
        _catalog_correspondence(declared, catalog, package_kind=retained.package_kind)
        stages = [s for s in declared["profiles"] if s["stage"] == "source_planning"]
        if len(stages) != 1:
            raise ContractViolation("target source-planning stage unavailable")
        stage = stages[0]
        entries = [
            e
            for e in catalog.entries
            if e.semantic_provider_key == declared["semantic_contract"]["provider_key"]
            and (
                e.profile_declaration.profile_ref,
                e.profile_declaration.version,
                e.profile_declaration.digest.to_wire(),
            )
            == (stage["profile_ref"], stage["profile_version"], stage["profile_digest"])
        ]
        if len(entries) != 1:
            raise ContractViolation("original target profile unavailable")
        entry = entries[0]
        inputs = [
            i for i in entry.profile_declaration.inputs if i.role == "manifest_source"
        ]
        if len(inputs) != 1 or inputs[0].contract not in entry.manifest_contracts:
            raise ContractViolation("target manifest_source correspondence unavailable")
        result = TargetContextFields(
            declared["semantic_package_family"],
            declared["semantic_contract"]["role"],
            inputs[0].contract,
        )
        evidence = (
            digest,
            declaration_digest,
            entry.binding_digest,
            catalog.catalog_root_digest,
        )
    # Original owner and scope are checked again after all retained interpretation.
    if (
        state.method.call(target, inventory_admission=inventory, expected=comparison)
        is not None
    ):
        raise ContractViolation("target validator returned non-None")
    contexts._equal(comparison.source_planning, expected_copy)
    if (
        comparison.target_source_identity_digest != source_identity
        or comparison.target_package != package
    ):
        raise ContractViolation("target validator changed expected coordinates")
    if qualified is None:
        if v3_source is None:
            assert snapshot is not None
            host.methods["scope"].call(snapshot, projection_digest=digest)
        else:
            assert target_binding is not None
            host.methods["selected_validate"].call(
                target, expectation=target_binding.expectation,
                binding_digest=target_binding.binding_digest,
            )
    contexts._equal(
        expected_copy, contexts.source_planning_expectation(state.host, context)
    )
    state.check()
    if contexts._CONTEXTS.get(context) is not original:
        raise ContractViolation("original target source context revoked")
    return deepcopy(result), evidence


class TargetContextOrigin(direct._Opaque):
    """Fixed composition retains this original issuer/reader for Workspace."""

    def __init_subclass__(cls, **kwargs):
        raise TypeError("target origin is sealed")

    def issue(
        self,
        source_context,
        inventory_admission,
        target_admission,
        *,
        target_source_identity_digest,
        target_package,
    ):
        return self._issue(
            source_context,
            inventory_admission,
            target_admission,
            target_source_identity_digest=target_source_identity_digest,
            target_package=target_package,
            source_only=False,
        )

    def issue_source(
        self,
        source_context,
        inventory_admission,
        target_admission,
        *,
        target_source_identity_digest,
        target_package,
    ):
        return self._issue(
            source_context,
            inventory_admission,
            target_admission,
            target_source_identity_digest=target_source_identity_digest,
            target_package=target_package,
            source_only=True,
        )

    def read(self, admission, *, source_context, inventory_admission, target_admission):
        return self._read(
            admission,
            source_context=source_context,
            inventory_admission=inventory_admission,
            target_admission=target_admission,
            source_only=False,
        )

    def read_source(
        self, admission, *, source_context, inventory_admission, target_admission
    ):
        return self._read(
            admission,
            source_context=source_context,
            inventory_admission=inventory_admission,
            target_admission=target_admission,
            source_only=True,
        )

    def _issue(
        self,
        source_context,
        inventory_admission,
        target_admission,
        *,
        target_source_identity_digest,
        target_package,
        source_only,
    ):
        state = _state(self)
        identity, package = (
            deepcopy(target_source_identity_digest),
            deepcopy(target_package),
        )
        value, evidence = _derive(
            state,
            source_context,
            inventory_admission,
            target_admission,
            identity,
            package,
            source_only=source_only,
        )
        record = _Record(
            source_context,
            inventory_admission,
            target_admission,
            identity,
            package,
            evidence,
            value,
            source_only,
        )
        result = object.__new__(
            SourceTargetContextAdmission if source_only else TargetContextAdmission
        )
        try:
            with _publication(state), direct._LOCK:
                if len(state.admissions) >= 128:
                    raise ContractViolation("target context capacity exceeded")
                state.admissions[result] = record
        except BaseException:
            state.admissions.pop(result, None)
            raise
        return result

    def _read(
        self,
        admission,
        *,
        source_context,
        inventory_admission,
        target_admission,
        source_only,
    ):
        state = _state(self)
        if type(admission) is not (
            SourceTargetContextAdmission if source_only else TargetContextAdmission
        ):
            raise TypeError("exact target context required")
        record = state.admissions.get(admission)
        if (
            record is None
            or record.source_only is not source_only
            or record.source_context is not source_context
            or record.inventory is not inventory_admission
            or record.target is not target_admission
        ):
            raise ContractViolation("foreign target context or original handles")
        try:
            value, evidence = _derive(
                state,
                source_context,
                inventory_admission,
                target_admission,
                record.source_identity,
                record.package,
                source_only=source_only,
            )
            if evidence != record.evidence or value != record.fields:
                raise ContractViolation("target correspondence changed")
            with _publication(state), direct._LOCK:
                if state.admissions.get(admission) is not record:
                    raise ContractViolation("target context revoked during validation")
                return deepcopy(value)
        except BaseException:
            state.admissions.pop(admission, None)
            raise


_METHODS = {
    name: getattr(TargetContextOrigin, name)
    for name in ("issue", "read", "issue_source", "read_source", "_issue", "_read")
}


def assemble_target_context_origin(host):
    """Fixed Code assembly; no caller-provided issuer, reader or validator."""
    current = direct._state(host)
    resources = {r.role: r.resource for r in current.expected.resources}
    declaration_v3 = current.source_rail == "declaration_v3"
    issuer = resources[
        "declaration_scope_runtime" if declaration_v3 else "semantic_issuer"
    ]
    method = direct._capture(issuer, "validate_dependency_target_admission")
    bound = () if declaration_v3 else tuple(
        (name, resources[name], inspect.getattr_static(issuer, name))
        for name in ("observation_runtime", "membership_runtime")
    )
    state = _State(host, issuer, method, bound, os.getpid())
    state.check()
    origin = object.__new__(TargetContextOrigin)
    with _publication(state), direct._LOCK:
        if host in _INSTALLED:
            raise ContractViolation("target origin already installed")
        _INSTALLED[host] = True
        _ORIGINS[origin] = state
    return origin
