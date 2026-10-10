"""Private stage retention mechanics, not original bootstrap or policy admission.

Fixed host composition must retain this record under its original parent guard.
Its expected references and declared-profile check cannot authenticate source,
parent, occurrence or registration-declaration membership. No public gate opens.
"""

import os
from copy import deepcopy
from dataclasses import dataclass

from aware_code_semantic_contract_runtime.contracts import (
    ContractViolation,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.direct_origin_interfaces import (
    DirectCommandExpectedContext,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticContractCatalogResolver,
)
from aware_code_semantic_contract_runtime.runtime import SemanticContractRuntime
from aware_code_semantic_contract_runtime.selected_provider import (
    _registration_state,
    validate_selected_provider_registration,
)


@dataclass(frozen=True)
class _StageRuntimeRetention:
    expected: DirectCommandExpectedContext
    identities: tuple
    resources: tuple
    stages: tuple
    entries: tuple
    catalog_digest: object
    resolver: CodeSemanticContractCatalogResolver
    pid: int
    current_catalog: object = None

    def check_identities(self):
        # No owner I/O or provider call; usable inside the original parent guard.
        if self.pid != os.getpid():
            raise ContractViolation("stage retention belongs to another process")
        expected = self.expected
        expected.__post_init__()
        observed = (
            expected.invocation_identity,
            expected.epoch_identity,
            expected.runtime,
            expected.catalog,
        )
        if expected.process_id != self.pid or any(
            a is not b for a, b in zip(observed, self.identities, strict=True)
        ):
            raise ContractViolation("stage retention parent/runtime identities changed")
        if len(expected.resources) != len(self.resources):
            raise ContractViolation("stage retention resource closure changed")
        for actual, (role, resource, disposition) in zip(
            expected.resources, self.resources, strict=True
        ):
            if (
                actual.role != role
                or actual.resource is not resource
                or actual.disposition != disposition
            ):
                raise ContractViolation("stage retention resource changed")
        if len(expected.stage_runtime_bindings) != len(self.stages):
            raise ContractViolation("stage runtime bindings changed")
        for actual, (stage, runtime, registration) in zip(
            expected.stage_runtime_bindings, self.stages, strict=True
        ):
            if (
                actual.stage != stage
                or actual.runtime is not runtime
                or actual.registration is not registration
            ):
                raise ContractViolation("original stage runtime/registration changed")
            # Nominal liveness only, no provider property, codec or owner call.
            # Full registration correspondence remains the owning validator's job.
            if _registration_state(registration).runtime is not runtime:
                raise ContractViolation("original stage registration runtime changed")

    def validate(self):
        """Original catalog and selected registration checks; never executes owners."""
        self.check_identities()
        if self.resolver._admission is not (
            self.current_catalog
            if self.current_catalog is not None
            else self.expected.catalog
        ):
            raise ContractViolation("retained stage catalog admission changed")
        self.resolver.validate_catalog()
        if self.resolver._catalog_coordinates()[2] != self.catalog_digest:
            raise ContractViolation("retained stage catalog changed")
        keys = []
        for (_, runtime, registration), retained in zip(
            self.stages, self.entries, strict=True
        ):
            provider_key, profile, declaration, binding, entry_digest = retained
            entry = self.resolver.read_profile_binding(
                profile=profile, semantic_provider_key=provider_key
            )
            if entry.binding_digest != entry_digest:
                raise ContractViolation("retained stage catalog entry unavailable")
            if (
                entry.semantic_provider_key != provider_key
                or entry.profile_declaration != profile
                or binding not in entry.provider_execution_bindings
            ):
                raise ContractViolation("retained stage catalog correspondence changed")
            validate_selected_provider_registration(
                runtime,
                registration,
                expected_profile=profile,
                expected_declaration=declaration,
                expected_binding=binding,
            )
            keys.append(provider_key)
        if len(keys) % 2 or any(
            keys[offset] != keys[offset + 1]
            for offset in range(0, len(keys), 2)
        ):
            raise ContractViolation("stage pair selects different semantic owners")
        if len(set(keys[::2])) != len(keys) // 2:
            raise ContractViolation("duplicate semantic owner stage pair")
        self.check_identities()

    def validate_declared_profiles(self, declaration):
        """Comparison only; caller must supply original authenticated declaration.

        This accepts canonical Code declaration meaning, not owner manifests.
        The later host/policy join must bind its digest to the original occurrence.
        """
        from .calculation import _plain

        self.validate()
        value = _plain(declaration)
        stages = value["profiles"]
        provider_key = value["semantic_contract"]["provider_key"]
        selected = [
            (stage, entry)
            for stage, entry in zip(self.stages, self.entries, strict=True)
            if entry[0] == provider_key
        ]
        if len(selected) != 2 or len(stages) != 2:
            raise ContractViolation("declared stage owner/profile set differs")
        for (stage, _, _), (_, profile, _, _, _) in selected:
            matches = [s for s in stages if s["stage"] == stage]
            if len(matches) != 1 or matches[0] != {
                "stage": stage,
                "profile_ref": profile.profile_ref,
                "profile_version": profile.version,
                "profile_digest": profile.digest.to_wire(),
            }:
                raise ContractViolation("declared stage profile differs")
        return canonical_json_bytes(value)

    def authority_stage_for(self, planning_registration):
        """Select the original paired authority stage by planning identity."""
        self.check_identities()
        matches = [
            (
                self.stages[offset + 1][1],
                self.stages[offset + 1][2],
                self.entries[offset + 1],
            )
            for offset in range(0, len(self.stages), 2)
            if self.stages[offset][2] is planning_registration
        ]
        if len(matches) != 1:
            raise ContractViolation("original planning stage pair unavailable")
        return matches[0]


def _capture_stage_runtime_retention(expected):
    """Private capture, not a host admission or caller-authenticated factory."""
    if type(expected) is not DirectCommandExpectedContext:
        raise TypeError("exact original stage context required")
    expected.__post_init__()
    if expected.process_id != os.getpid():
        raise ContractViolation("foreign stage context process")
    if not expected.stage_runtime_bindings:
        raise ContractViolation("complete original stage bindings required")
    resolver = CodeSemanticContractCatalogResolver(expected.catalog)
    catalog = resolver.catalog
    stages = tuple(
        (s.stage, s.runtime, s.registration) for s in expected.stage_runtime_bindings
    )
    # _registration_state checks exact nominal type before object-hash identity
    # is used; arbitrary caller objects never reach the set operation.
    for _, _, registration in stages:
        _registration_state(registration)
    if len({registration for _, _, registration in stages}) != len(stages):
        raise ContractViolation("duplicate original stage registration")
    retained = []
    for _, runtime, registration in stages:
        if type(runtime) is not SemanticContractRuntime:
            raise TypeError("exact stage Code runtime required")
        original = _registration_state(registration)
        entries = [
            e
            for e in catalog.entries
            if e.profile_declaration == runtime.profile
            and e.semantic_provider_key == original.provider_key
        ]
        if len(entries) != 1:
            raise ContractViolation("unique live stage catalog entry required")
        entry = entries[0]
        providers = [
            p
            for p in entry.profile_declaration.providers
            if p.provider_key == original.provider_key
        ]
        bindings = [
            b
            for b in entry.provider_execution_bindings
            if b.provider_key == original.provider_key
        ]
        if len(providers) != 1 or len(bindings) != 1:
            raise ContractViolation("exact stage declaration/binding required")
        retained.append(
            deepcopy(
                (
                    original.provider_key,
                    entry.profile_declaration,
                    providers[0],
                    bindings[0],
                    entry.binding_digest,
                )
            )
        )
    record = _StageRuntimeRetention(
        expected,
        (
            expected.invocation_identity,
            expected.epoch_identity,
            expected.runtime,
            expected.catalog,
        ),
        tuple((b.role, b.resource, b.disposition) for b in expected.resources),
        stages,
        tuple(retained),
        catalog.catalog_root_digest,
        resolver,
        os.getpid(),
    )
    record.validate()
    return record
