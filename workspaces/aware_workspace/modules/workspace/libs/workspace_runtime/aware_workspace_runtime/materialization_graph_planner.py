"""Deterministic Workspace semantic materialization graph planner."""

from __future__ import annotations

import hashlib
import inspect
import json
from collections.abc import Mapping
from dataclasses import dataclass
from heapq import heapify, heappop, heappush
from time import monotonic_ns
from typing import Protocol

from aware_code_semantic_contract_runtime import (
    CodeSemanticContractCatalogResolver,
    CodeSemanticContractMatch,
    CodeSemanticContractMatchAdmission,
    CodeSemanticMaterializationIntent,
    CodeSemanticPackagePlanningContext,
    CodeSemanticRequiredResultProduct,
    ContentDigest,
    ContractViolation,
    SemanticDependencyDemand,
    SemanticDependencyDemandSet,
    SemanticDependencyTargetConstraint,
)
from aware_code_semantic_contract_runtime.dependency_inputs import (
    SemanticDependencyPlanningInput,
    SemanticDependencySource,
)
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    DependencyPlanningInputCodec,
)

from .materialization_membership_catalog import (
    WorkspaceSemanticMaterializationMembershipResolver,
    WorkspaceSemanticMaterializationPackageEntry,
)
from .declaration_scope_admission import WorkspaceOriginalGraphTargetValidator
from .source_admission_catalog import WorkspaceV3GraphSourceCorrespondence
from .materialization_selection import (
    WORKSPACE_ADMITTED_PACKAGE_INTENT,
    WORKSPACE_MATERIALIZATION_ROOT_INTENT_ASSOCIATION,
    WORKSPACE_MATERIALIZATION_SELECTION_RESOLUTION,
    WorkspaceAdmittedPackageIntent,
    WorkspaceMaterializationRootIntentAssociation,
    WorkspaceMaterializationSelectionProposal,
    WorkspaceMaterializationSelectionResolution,
    WorkspaceSemanticMaterializationParticipationPolicy,
)
from .semantic_dependency_graph import (
    WORKSPACE_MATERIALIZATION_PLANNING_COUNTERS,
    WORKSPACE_MATERIALIZATION_PLANNING_TIMING_STAGES,
    WorkspaceDependencyTargetResolution,
    WorkspaceMaterializationPlanningCounterEntry,
    WorkspaceMaterializationPlanningTimingEntry,
    WorkspaceSemanticMaterializationGraphNode,
    WorkspaceSemanticMaterializationGraphPlanAdmission,
    WorkspaceSemanticMaterializationGraphPlanResult,
    WorkspaceSemanticMaterializationNodeExecutionBinding,
    WorkspaceSemanticPackageHeadObservation,
    WorkspaceSemanticPlannedDependencyInput,
    WorkspaceSemanticPlanningDemandClosure,
    _create_planner_graph,
    _create_planner_graph_edge,
    _create_planner_graph_execution_binding,
    _create_planner_graph_node,
    _create_planner_graph_plan_result,
    _create_planner_local_root_association,
    _create_planner_node_execution_binding,
    _create_planner_target_resolution,
)

WORKSPACE_SEMANTIC_ROOT_CODE_PLAN = "aware.workspace.semantic-root-code-plan.v1"
_WORKSPACE_SEMANTIC_ROOT_CODE_PLAN_V2 = "aware.workspace.semantic-root-code-plan.v2"
_INTERNAL_JSON_ENCODER = json.JSONEncoder(
    ensure_ascii=False,
    allow_nan=False,
    sort_keys=True,
    separators=(",", ":"),
)


def _digest(contract: str, body: Mapping[str, object]) -> ContentDigest:
    value = (
        "sha256:"
        + hashlib.sha256(
            _INTERNAL_JSON_ENCODER.encode({"contract": contract, **body}).encode(
                "utf-8"
            )
        ).hexdigest()
    )
    return _frozen_value(ContentDigest, value=value)


def _frozen_value[T](expected: type[T], **fields: object) -> T:
    result = object.__new__(expected)
    for name, value in fields.items():
        object.__setattr__(result, name, value)
    return result


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticRootCodePlan:
    package_ref: str
    code_intent: CodeSemanticMaterializationIntent
    required_result_products: tuple[CodeSemanticRequiredResultProduct, ...]
    root_plan_digest: ContentDigest
    required_semantic_provider_keys: tuple[str, ...] = ()

    @classmethod
    def create(
        cls,
        *,
        package_ref: str,
        code_intent: CodeSemanticMaterializationIntent,
        required_result_products: tuple[CodeSemanticRequiredResultProduct, ...],
        required_semantic_provider_keys: tuple[str, ...] = (),
    ) -> WorkspaceSemanticRootCodePlan:
        body = _root_plan_body(
            package_ref, code_intent, required_result_products,
            required_semantic_provider_keys,
        )
        contract = (
            _WORKSPACE_SEMANTIC_ROOT_CODE_PLAN_V2
            if required_semantic_provider_keys else WORKSPACE_SEMANTIC_ROOT_CODE_PLAN
        )
        return cls(
            package_ref=package_ref,
            code_intent=code_intent,
            required_result_products=required_result_products,
            root_plan_digest=_digest(contract, body),
            required_semantic_provider_keys=required_semantic_provider_keys,
        )

    def __post_init__(self) -> None:
        body = _root_plan_body(
            self.package_ref, self.code_intent, self.required_result_products,
            self.required_semantic_provider_keys,
        )
        contract = (
            _WORKSPACE_SEMANTIC_ROOT_CODE_PLAN_V2
            if self.required_semantic_provider_keys else WORKSPACE_SEMANTIC_ROOT_CODE_PLAN
        )
        if self.root_plan_digest != _digest(contract, body):
            raise ContractViolation("root Code plan digest mismatched")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": (
                _WORKSPACE_SEMANTIC_ROOT_CODE_PLAN_V2
                if self.required_semantic_provider_keys
                else WORKSPACE_SEMANTIC_ROOT_CODE_PLAN
            ),
            **_root_plan_body(
                self.package_ref, self.code_intent, self.required_result_products,
                self.required_semantic_provider_keys,
            ),
            "root_plan_digest": self.root_plan_digest.to_wire(),
        }


def _root_plan_body(
    package_ref: object,
    intent: object,
    requirements: object,
    provider_keys: object,
) -> dict[str, object]:
    if (
        type(package_ref) is not str
        or not package_ref
        or any(c.isspace() for c in package_ref)
    ):
        raise TypeError("root plan package ref must be token text")
    if type(intent) is not CodeSemanticMaterializationIntent:
        raise TypeError("root plan intent must be exact Code intent")
    if type(requirements) is not tuple:
        raise TypeError("root plan requirements must be exact tuple")
    if (
        type(provider_keys) is not tuple
        or any(type(key) is not str or not key or any(char.isspace() for char in key)
               for key in provider_keys)
        or provider_keys != tuple(sorted(set(provider_keys), key=str.encode))
    ):
        raise ContractViolation("root plan provider constraints must be canonical")
    intent.__post_init__()
    admitted: list[CodeSemanticRequiredResultProduct] = []
    for item in requirements:
        if type(item) is not CodeSemanticRequiredResultProduct:
            raise TypeError("root plan requirement must be exact Code requirement")
        item.__post_init__()
        admitted.append(item)
    roles = tuple(item.role for item in admitted)
    if (
        roles != tuple(sorted(set(roles), key=str.encode))
        or roles != intent.requested_terminal_output_roles
    ):
        raise ContractViolation("root plan requirement closure differs from intent")
    body = {
        "code_intent": intent.to_wire(),
        "package_ref": package_ref,
        "required_result_products": [item.to_wire() for item in admitted],
    }
    if provider_keys:
        body["required_semantic_provider_keys"] = list(provider_keys)
    return body


class WorkspaceSemanticPackageHeadReader(Protocol):
    async def observe(
        self,
        *,
        entry: WorkspaceSemanticMaterializationPackageEntry,
        local_code_match: CodeSemanticContractMatch,
        intent: CodeSemanticMaterializationIntent,
        planning_demand_closure: WorkspaceSemanticPlanningDemandClosure,
        planning_input_digest: ContentDigest,
    ) -> WorkspaceSemanticPackageHeadObservation: ...


class WorkspaceSemanticMaterializationPlanningError(ContractViolation):
    def __init__(self, code: str, stage: str) -> None:
        super().__init__(code)
        self.code = code
        self.stage = stage


@dataclass(slots=True)
class _State:
    entry: WorkspaceSemanticMaterializationPackageEntry
    root_plan: WorkspaceSemanticRootCodePlan | None
    demands: dict[str, SemanticDependencyDemand]
    context_digests: set[str]
    match: CodeSemanticContractMatch | None = None
    match_admission: CodeSemanticContractMatchAdmission | None = None
    intent: CodeSemanticMaterializationIntent | None = None
    requirements: tuple[CodeSemanticRequiredResultProduct, ...] = ()
    demand_set: SemanticDependencyDemandSet | None = None
    workspace_admission: WorkspaceAdmittedPackageIntent | None = None
    context: CodeSemanticPackagePlanningContext | None = None
    planning_input: SemanticDependencyPlanningInput | None = None
    planning_input_body: bytes | None = None
    planning_input_digest: ContentDigest | None = None


@dataclass(frozen=True, slots=True)
class _EdgeDemand:
    consumer_ref: str
    target_ref: str
    demand: SemanticDependencyDemand
    initial_target_match_digest: ContentDigest


def _validate_state_bound_head_occurrence(
    *,
    entry: WorkspaceSemanticMaterializationPackageEntry,
    head: WorkspaceSemanticPackageHeadObservation,
    correspondence: WorkspaceV3GraphSourceCorrespondence | None,
) -> None:
    """Join retained V4 head identity to the original selected source."""
    head.__post_init__()
    occurrence = head.stored_package_occurrence
    if occurrence is None:
        return
    if correspondence is None:
        raise WorkspaceSemanticMaterializationPlanningError(
            "head_observation_failed", "graph_derive"
        )
    source_runtime, source_admission = (
        correspondence.original_semantic_input_source(entry)
    )
    source_runtime.validate_publication_package_occurrence(
        source_admission, occurrence=occurrence
    )


class WorkspaceSemanticMaterializationGraphPlanner:
    def __init__(
        self,
        *,
        workspace_catalog: WorkspaceSemanticMaterializationMembershipResolver,
        code_catalog: CodeSemanticContractCatalogResolver,
        head_reader: WorkspaceSemanticPackageHeadReader,
        planning_source: SemanticDependencySource,
        source_only_target_validator: WorkspaceOriginalGraphTargetValidator | None = None,
        source_correspondences: tuple[WorkspaceV3GraphSourceCorrespondence, ...] = (),
    ) -> None:
        if (
            type(workspace_catalog)
            is not WorkspaceSemanticMaterializationMembershipResolver
        ):
            raise TypeError("Workspace catalog resolver must be exact")
        if type(code_catalog) is not CodeSemanticContractCatalogResolver:
            raise TypeError("Code catalog resolver must be exact")
        self._workspace = workspace_catalog
        self._code = code_catalog
        self._head_reader = head_reader
        # Fixed host supplies the original admitted owner source. Protocol matching
        # alone does not establish provenance; no membership-derived fallback.
        self._planning_source = planning_source
        if (
            source_only_target_validator is not None
            and type(source_only_target_validator)
            is not WorkspaceOriginalGraphTargetValidator
        ):
            raise TypeError("original Workspace graph target validator required")
        self._source_only_targets = source_only_target_validator
        if type(source_correspondences) is not tuple:
            raise TypeError("original source correspondence tuple required")
        self._source_correspondences = {}
        for item in source_correspondences:
            if type(item) is not WorkspaceV3GraphSourceCorrespondence:
                raise TypeError("original v3 source correspondence required")
            package_ref = item.package().package_ref
            if package_ref in self._source_correspondences:
                raise ContractViolation("duplicate graph source correspondence")
            self._source_correspondences[package_ref] = item
        self._planning_descriptor = inspect.getattr_static(
            planning_source, "read_dependencies"
        )
        self._planning_reader = planning_source.read_dependencies
        if (
            not inspect.ismethod(self._planning_reader)
            or self._planning_reader.__self__ is not planning_source
        ):
            raise TypeError("original owner planning reader required")
        self._workspace_admission_cache: dict[
            tuple[str, str],
            tuple[WorkspaceAdmittedPackageIntent, dict[str, object]],
        ] = {}
        self._node_execution_binding_digest_cache: dict[
            tuple[object, ...], ContentDigest
        ] = {}
        self._graph_execution_binding_digest_cache: dict[
            tuple[object, ...], ContentDigest
        ] = {}

    def _read_owner_planning(self, entry):
        if (
            inspect.getattr_static(self._planning_source, "read_dependencies")
            is not self._planning_descriptor
        ):
            raise ContractViolation("owner planning reader substituted")
        value = self._planning_reader(entry.package)
        if type(value) is not SemanticDependencyPlanningInput:
            raise TypeError("exact owner planning input required")
        value.__post_init__()
        if value.package != entry.package:
            raise ContractViolation("owner planning package/source differs")
        correspondence = self._source_correspondences.get(entry.package.package_ref)
        if correspondence is not None:
            correspondence.validate(entry, value)
        elif self._source_correspondences or (
            value.source_identity_digest != entry.source_identity_digest
        ):
            raise ContractViolation("owner planning package/source differs")
        declarations = {
            (d.dependency_kind, d.dependency_ref): d
            for d in entry.authored_dependencies
        }
        if set(declarations) != {
            (d.dependency_kind, d.dependency_ref) for d in value.dependencies
        }:
            raise ContractViolation("owner planning declaration scope differs")
        for dependency in value.dependencies:
            declaration = declarations[
                (dependency.dependency_kind, dependency.dependency_ref)
            ]
            if (
                tuple(t.package.package_ref for t in dependency.targets)
                != declaration.admitted_target_package_refs
                or dependency.target_constraints
                != declaration.allowed_target_constraints
            ):
                raise ContractViolation("owner planning target correspondence differs")
            for target in dependency.targets:
                if self._source_only_targets is not None:
                    self._source_only_targets.validate_target(
                        package=entry.package,
                        dependency_kind=dependency.dependency_kind,
                        dependency_ref=dependency.dependency_ref,
                        target=target,
                    )
                admitted = self._workspace.package_if_present(
                    target.package.package_ref
                )
                if admitted is None:
                    if self._source_only_targets is None:
                        raise ContractViolation("owner planning target membership absent")
                elif (
                    target.package != admitted.package
                    or target.semantic_root_refs != admitted.owned_semantic_root_refs
                ):
                    raise ContractViolation("owner planning target membership differs")
        if self._workspace.package(entry.package.package_ref) != entry:
            raise ContractViolation("planning membership changed")
        if (
            inspect.getattr_static(self._planning_source, "read_dependencies")
            is not self._planning_descriptor
        ):
            raise ContractViolation("owner planning reader substituted")
        return value

    async def plan(
        self,
        *,
        selection_proposal: WorkspaceMaterializationSelectionProposal,
        requested_root_code_plans: tuple[WorkspaceSemanticRootCodePlan, ...],
    ) -> WorkspaceSemanticMaterializationGraphPlanResult:
        if type(selection_proposal) is not WorkspaceMaterializationSelectionProposal:
            raise TypeError("selection proposal must be exact")
        if type(requested_root_code_plans) is not tuple:
            raise TypeError("root plans must be exact tuple")
        self._workspace._assert_valid()
        self._code._assert_valid()
        (
            workspace_catalog_ref,
            workspace_catalog_generation,
            workspace_catalog_root_digest,
        ) = self._workspace._catalog_coordinates()
        (
            code_catalog_ref,
            code_catalog_generation,
            code_catalog_root_digest,
        ) = self._code._catalog_coordinates()
        selection_proposal.__post_init__()
        plans: list[WorkspaceSemanticRootCodePlan] = []
        for item in requested_root_code_plans:
            if type(item) is not WorkspaceSemanticRootCodePlan:
                raise TypeError("root plan must be exact")
            item.__post_init__()
            plans.append(item)
        if tuple(item.package_ref for item in plans) != tuple(
            sorted({item.package_ref for item in plans}, key=str.encode)
        ):
            raise ContractViolation("root plans must be package-ref unique and ordered")

        started = monotonic_ns()
        selection_started = started
        root_entries: dict[str, WorkspaceSemanticMaterializationPackageEntry] = {}
        catalog_lookups = 0
        for selector in selection_proposal.selectors:
            catalog_lookups += 1
            for entry in self._workspace.expand_selector(selector):
                root_entries[entry.package.package_ref] = entry
        if set(root_entries) != {item.package_ref for item in plans}:
            raise WorkspaceSemanticMaterializationPlanningError(
                "selection_failed", "selection_expand"
            )
        selection_elapsed = monotonic_ns() - selection_started

        plans_by_ref = {item.package_ref: item for item in plans}
        states = {
            ref: _State(
                entry=entry,
                root_plan=plans_by_ref[ref],
                demands={},
                context_digests=set(),
            )
            for ref, entry in root_entries.items()
        }
        queue = sorted(states, key=str.encode)
        heapify(queue)
        queued = set(queue)
        edges: dict[tuple[str, str, str], _EdgeDemand] = {}
        context_cache: dict[
            str,
            tuple[
                CodeSemanticContractMatch,
                CodeSemanticContractMatchAdmission,
                SemanticDependencyDemandSet,
            ],
        ] = {}
        context_match_cache: dict[
            str,
            tuple[CodeSemanticContractMatch, CodeSemanticContractMatchAdmission],
        ] = {}
        provider_match_count = 0
        planner_invocations = 0
        equal_context_reuse = 0
        iterations = 0
        lattice_additions = len(states)
        provider_elapsed = 0
        dependency_elapsed = 0

        def resolve_context_match(
            context: CodeSemanticPackagePlanningContext,
        ) -> tuple[CodeSemanticContractMatch, CodeSemanticContractMatchAdmission]:
            nonlocal provider_elapsed, provider_match_count
            key = context.context_digest.value
            cached_match = context_match_cache.get(key)
            if cached_match is not None:
                return cached_match
            matching_started = monotonic_ns()
            resolved = self._code._resolve_prevalidated_context(context)
            provider_elapsed += monotonic_ns() - matching_started
            provider_match_count += 1
            context_match_cache[key] = resolved
            return resolved

        while True:
            iterations += 1
            if not queue:
                break
            package_ref = heappop(queue)
            queued.remove(package_ref)
            state = states[package_ref]
            intent, requirements = _compose_state(state, self._code)
            admission_cache_key = (
                state.entry.entry_digest.value,
                intent.intent_digest.value,
            )
            cached_workspace_admission = self._workspace_admission_cache.get(
                admission_cache_key
            )
            if cached_workspace_admission is None:
                try:
                    intent_wire, policy_wire = self._workspace._policy_admission_parts(
                        entry=state.entry, intent=intent
                    )
                    workspace_admission = _create_planner_workspace_admission(
                        package_ref=package_ref,
                        code_intent_body=intent,
                        code_intent_wire=intent_wire,
                        catalog_root_digest=workspace_catalog_root_digest,
                        catalog_generation=workspace_catalog_generation,
                        participation_policy_body=state.entry.participation_policy,
                        participation_policy_wire=policy_wire,
                    )
                except (ContractViolation, TypeError) as error:
                    raise WorkspaceSemanticMaterializationPlanningError(
                        "workspace_intent_admission_failed", "selection_expand"
                    ) from error
                self._workspace_admission_cache[admission_cache_key] = (
                    workspace_admission,
                    intent_wire,
                )
            else:
                workspace_admission, intent_wire = cached_workspace_admission
            provider_keys = tuple(
                sorted(
                    {
                        constraint.constraint_value
                        for demand in state.demands.values()
                        for constraint in demand.target_constraints
                        if constraint.constraint_kind == "semantic_provider_key"
                    } | set(
                        state.root_plan.required_semantic_provider_keys
                        if state.root_plan is not None else ()
                    ),
                    key=str.encode,
                )
            )
            context = self._code._create_prevalidated_context(
                package=state.entry.package,
                package_family=state.entry.package_family,
                package_role=state.entry.package_role,
                manifest_contract=state.entry.manifest_contract,
                code_intent=intent,
                code_intent_wire=intent_wire,
                required_result_products=requirements,
                required_semantic_provider_keys=provider_keys,
            )
            observed_planning_input = self._read_owner_planning(state.entry)
            if state.planning_input is None:
                planning_body = DependencyPlanningInputCodec().encode(
                    observed_planning_input
                )
                # Code decodes this canonical body into the provider-facing
                # detached value. Retain the owner value only for exact
                # before/after comparison; decoding it here would duplicate
                # Code's authority boundary for every graph node.
                state.planning_input = observed_planning_input
                state.planning_input_body = planning_body
                state.planning_input_digest = ContentDigest.of_bytes(planning_body)
            elif observed_planning_input != state.planning_input:
                raise ContractViolation("owner planning input changed within graph")
            planning_input = state.planning_input
            planning_digest = state.planning_input_digest
            assert planning_input is not None
            assert state.planning_input_body is not None
            assert planning_digest is not None
            cache_key = (
                f"{code_catalog_root_digest.value}:{context.context_digest.value}:"
                f"{planning_digest.value}"
            )
            cached = context_cache.get(cache_key)
            if cached is None:
                try:
                    match, match_admission = resolve_context_match(context)
                except ContractViolation as error:
                    raise WorkspaceSemanticMaterializationPlanningError(
                        str(error), "provider_match"
                    ) from error
                if (
                    match.selected_binding.profile_declaration.profile_ref
                    not in state.entry.allowed_profile_refs
                ):
                    raise WorkspaceSemanticMaterializationPlanningError(
                        "workspace_intent_admission_failed", "provider_match"
                    )
                planning_started = monotonic_ns()
                try:
                    demand_set = (
                        await self._code._plan_dependencies_for_prevalidated_context(
                            context=context,
                            match=match,
                            planning_input=planning_input,
                            planning_input_body=state.planning_input_body,
                        )
                    )
                except (ContractViolation, TypeError) as error:
                    raise WorkspaceSemanticMaterializationPlanningError(
                        "dependency_planning_failed", "dependency_plan"
                    ) from error
                dependency_elapsed += monotonic_ns() - planning_started
                planner_invocations += 1
                context_cache[cache_key] = (match, match_admission, demand_set)
            else:
                match, match_admission, demand_set = cached
            if self._read_owner_planning(state.entry) != planning_input:
                raise ContractViolation("owner planning input changed during planning")
            previous = state.demand_set
            if previous is not None:
                prior = {item.demand_digest: item for item in previous.demands}
                current = {item.demand_digest: item for item in demand_set.demands}
                if not prior.items() <= current.items():
                    raise WorkspaceSemanticMaterializationPlanningError(
                        "non_monotonic_dependency_plan", "dependency_plan"
                    )
                if (
                    state.match is not None
                    and state.match.selected_entry_digest != match.selected_entry_digest
                ):
                    raise WorkspaceSemanticMaterializationPlanningError(
                        "dependency_target_binding_conflict", "provider_match"
                    )
            context_is_new = context.context_digest.value not in state.context_digests
            if context_is_new:
                state.context_digests.add(context.context_digest.value)
                lattice_additions += 1
            elif previous is not None:
                equal_context_reuse += 1
            state.match = match
            state.match_admission = match_admission
            state.intent = intent
            state.requirements = requirements
            state.demand_set = demand_set
            state.workspace_admission = workspace_admission
            state.context = context

            declarations = {
                (item.dependency_kind, item.dependency_ref): item
                for item in state.entry.authored_dependencies
            }
            for demand in demand_set.demands:
                declaration = declarations.get(
                    (demand.authored_dependency_kind, demand.authored_dependency_ref)
                )
                if declaration is None or not _constraints_admitted(
                    demand, declaration.allowed_target_constraints
                ):
                    raise WorkspaceSemanticMaterializationPlanningError(
                        "authored_dependency_mismatch", "dependency_plan"
                    )
                catalog_lookups += 1
                candidates = self._workspace._candidates_prevalidated(
                    admitted_package_refs=declaration.admitted_target_package_refs,
                    constraints=demand.target_constraints,
                )
                survivors: list[
                    tuple[
                        WorkspaceSemanticMaterializationPackageEntry,
                        CodeSemanticContractMatch,
                    ]
                ] = []
                requirement = CodeSemanticRequiredResultProduct.create(
                    role=demand.required_result_role,
                    contract=demand.result_product_contract,
                )
                provider_constraints = tuple(
                    sorted(
                        {
                            item.constraint_value
                            for item in demand.target_constraints
                            if item.constraint_kind == "semantic_provider_key"
                        },
                        key=str.encode,
                    )
                )
                candidate_intent_wire = demand.target_intent.to_wire()
                for candidate in candidates:
                    candidate_context = self._code._create_prevalidated_context(
                        package=candidate.package,
                        package_family=candidate.package_family,
                        package_role=candidate.package_role,
                        manifest_contract=candidate.manifest_contract,
                        code_intent=demand.target_intent,
                        code_intent_wire=candidate_intent_wire,
                        required_result_products=(requirement,),
                        required_semantic_provider_keys=provider_constraints,
                    )
                    try:
                        candidate_match, _ = resolve_context_match(candidate_context)
                    except ContractViolation as error:
                        if str(error) == "semantic_contract_match_absent":
                            continue
                        raise WorkspaceSemanticMaterializationPlanningError(
                            str(error), "provider_match"
                        ) from error
                    survivors.append((candidate, candidate_match))
                if len(survivors) > 1 or (
                    not survivors and demand.cardinality == "required"
                ):
                    code = (
                        "dependency_target_ambiguous"
                        if survivors
                        else "dependency_target_absent"
                    )
                    raise WorkspaceSemanticMaterializationPlanningError(
                        code, "dependency_plan"
                    )
                if not survivors:
                    continue
                target, initial_match = survivors[0]
                target_ref = target.package.package_ref
                if target_ref == package_ref:
                    raise WorkspaceSemanticMaterializationPlanningError(
                        "dependency_cycle", "graph_derive"
                    )
                edge_key = (package_ref, demand.demand_digest.value, target_ref)
                if edge_key not in edges:
                    edges[edge_key] = _EdgeDemand(
                        consumer_ref=package_ref,
                        target_ref=target_ref,
                        demand=demand,
                        initial_target_match_digest=initial_match.selected_entry_digest,
                    )
                    lattice_additions += 1
                target_state = states.get(target_ref)
                if target_state is None:
                    target_state = _State(
                        entry=target,
                        root_plan=None,
                        demands={},
                        context_digests=set(),
                    )
                    states[target_ref] = target_state
                    lattice_additions += 1
                existing = target_state.demands.get(demand.demand_digest.value)
                if existing is None:
                    target_state.demands[demand.demand_digest.value] = demand
                    lattice_additions += 1
                    if target_ref not in queued:
                        heappush(queue, target_ref)
                        queued.add(target_ref)
                elif existing != demand:
                    raise WorkspaceSemanticMaterializationPlanningError(
                        "non_monotonic_dependency_plan", "dependency_plan"
                    )
        order = _topological_package_order(tuple(states), tuple(edges.values()))
        edges_by_consumer: dict[str, list[_EdgeDemand]] = {}
        for edge in edges.values():
            edges_by_consumer.setdefault(edge.consumer_ref, []).append(edge)
        for values in edges_by_consumer.values():
            values.sort(key=lambda item: item.demand.demand_digest.value)
        heads: dict[str, WorkspaceSemanticPackageHeadObservation] = {}
        head_wires: dict[str, dict[str, object]] = {}
        closures: dict[str, WorkspaceSemanticPlanningDemandClosure] = {}
        target_resolutions: dict[
            tuple[str, str, str], WorkspaceDependencyTargetResolution
        ] = {}
        target_resolution_wire_bytes: dict[str, bytes] = {}
        graph_nodes: dict[str, WorkspaceSemanticMaterializationGraphNode] = {}
        graph_node_wires: dict[str, dict[str, object]] = {}
        graph_node_wire_bytes: dict[str, bytes] = {}
        graph_started = monotonic_ns()
        for package_ref in order:
            state = states[package_ref]
            assert (
                state.match is not None
                and state.intent is not None
                and state.demand_set is not None
            )
            inbound = edges_by_consumer.get(package_ref, ())
            planned_inputs: list[WorkspaceSemanticPlannedDependencyInput] = []
            for item in inbound:
                target_state = states[item.target_ref]
                assert (
                    target_state.match is not None and target_state.intent is not None
                )
                if (
                    target_state.match.selected_entry_digest
                    != item.initial_target_match_digest
                ):
                    raise WorkspaceSemanticMaterializationPlanningError(
                        "dependency_target_binding_conflict", "provider_match"
                    )
                target_head = heads[item.target_ref]
                resolution, resolution_wire_bytes = _create_planner_target_resolution(
                    demand_digest=item.demand.demand_digest,
                    target_package_entry_digest=target_state.entry.entry_digest,
                    target_local_code_match_digest=target_state.match.match_digest,
                    composed_target_intent_digest=target_state.intent.intent_digest,
                    participation_policy_digest=target_state.entry.participation_policy.policy_digest,
                    required_result_role=item.demand.required_result_role,
                    result_product_contract=item.demand.result_product_contract,
                    head_observation=target_head,
                    head_observation_wire=head_wires[item.target_ref],
                )
                target_resolutions[
                    (
                        item.consumer_ref,
                        item.demand.demand_digest.value,
                        item.target_ref,
                    )
                ] = resolution
                target_resolution_wire_bytes[resolution.resolution_digest.value] = (
                    resolution_wire_bytes
                )
                planned_inputs.append(
                    WorkspaceSemanticPlannedDependencyInput.create(
                        demand_digest=item.demand.demand_digest,
                        target_resolution_digest=resolution.resolution_digest,
                        required_result_role=item.demand.required_result_role,
                        result_product_contract=item.demand.result_product_contract,
                    )
                )
            closure = WorkspaceSemanticPlanningDemandClosure.create(
                consumer_package=state.entry.package,
                planned_dependency_inputs=tuple(planned_inputs),
            )
            closures[package_ref] = closure
            assert state.planning_input_digest is not None
            head = await self._head_reader.observe(
                entry=state.entry,
                local_code_match=state.match,
                intent=state.intent,
                planning_demand_closure=closure,
                planning_input_digest=state.planning_input_digest,
            )
            if type(head) is not WorkspaceSemanticPackageHeadObservation:
                raise TypeError("head reader result must be exact head observation")
            head_wire = head.to_wire()
            if (
                head.package != state.entry.package
                or head.source_identity_digest != state.entry.source_identity_digest
                or head.profile_binding_digest != state.match.selected_entry_digest
            ):
                raise WorkspaceSemanticMaterializationPlanningError(
                    "head_observation_failed", "graph_derive"
                )
            _validate_state_bound_head_occurrence(
                entry=state.entry,
                head=head,
                correspondence=self._source_correspondences.get(package_ref),
            )
            heads[package_ref] = head
            head_wires[package_ref] = head_wire
            node, node_wire, node_wire_bytes = _create_planner_graph_node(
                package=state.entry.package,
                package_entry_digest=state.entry.entry_digest,
                participation_policy_digest=state.entry.participation_policy.policy_digest,
                source_identity_digest=state.entry.source_identity_digest,
                local_code_match_digest=state.match.match_digest,
                composed_intent_digest=state.intent.intent_digest,
                demand_set_digest=state.demand_set.demand_set_digest,
                planning_demand_closure_digest=closure.planning_demand_closure_digest,
                head_observation=head,
                head_observation_wire=head_wire,
            )
            graph_nodes[package_ref] = node
            graph_node_wires[package_ref] = node_wire
            graph_node_wire_bytes[package_ref] = node_wire_bytes
        node_values = tuple(graph_nodes.values())
        node_wires = tuple(graph_node_wires.values())
        node_wire_bytes = tuple(graph_node_wire_bytes.values())
        graph_edges = tuple(
            _create_planner_graph_edge(
                consumer_node_digest=graph_nodes[item.consumer_ref].node_digest,
                target_node_digest=graph_nodes[item.target_ref].node_digest,
                demand_digest=item.demand.demand_digest,
                target_resolution_digest=target_resolutions[
                    (
                        item.consumer_ref,
                        item.demand.demand_digest.value,
                        item.target_ref,
                    )
                ].resolution_digest,
            )
            for item in edges.values()
        )
        edge_values = tuple(item[0] for item in graph_edges)
        edge_wires = tuple(item[1] for item in graph_edges)
        edge_wire_bytes = tuple(item[2] for item in graph_edges)
        graph_root_associations = tuple(
            _create_planner_local_root_association(
                package_entry_digest=states[item.package_ref].entry.entry_digest,
                participation_policy_digest=states[
                    item.package_ref
                ].entry.participation_policy.policy_digest,
                code_intent_digest=item.code_intent.intent_digest,
                required_result_product_digests=tuple(
                    product.requirement_digest
                    for product in item.required_result_products
                ),
                node_digest=graph_nodes[item.package_ref].node_digest,
            )
            for item in plans
        )
        root_associations = tuple(item[0] for item in graph_root_associations)
        root_association_wires = tuple(item[1] for item in graph_root_associations)
        root_association_wire_bytes = tuple(item[2] for item in graph_root_associations)
        graph = _create_planner_graph(
            local_root_associations=root_associations,
            local_root_association_wires=root_association_wires,
            local_root_association_wire_bytes=root_association_wire_bytes,
            nodes=node_values,
            node_wires=node_wires,
            node_wire_bytes=node_wire_bytes,
            edges=edge_values,
            edge_wires=edge_wires,
            edge_wire_bytes=edge_wire_bytes,
        )
        graph_elapsed = monotonic_ns() - graph_started

        selection_association_values: list[
            WorkspaceMaterializationRootIntentAssociation
        ] = []
        for item in plans:
            workspace_admission = states[item.package_ref].workspace_admission
            assert workspace_admission is not None
            selection_association_values.append(
                _create_planner_root_intent_association(
                    package_ref=item.package_ref,
                    intent=item.code_intent,
                    admission=workspace_admission,
                )
            )
        selection_associations = tuple(selection_association_values)
        selection = _create_planner_selection_resolution(
            proposal=selection_proposal,
            catalog_root_digest=workspace_catalog_root_digest,
            catalog_generation=workspace_catalog_generation,
            expanded_package_refs=tuple(item.package_ref for item in plans),
            root_intent_associations=selection_associations,
        )
        match_admissions = tuple(
            sorted(
                {
                    state.match_admission.admission_digest
                    for state in states.values()
                    if state.match_admission is not None
                },
                key=lambda item: item.value,
            )
        )
        admission = WorkspaceSemanticMaterializationGraphPlanAdmission.create(
            selection_resolution_digest=selection.resolution_digest,
            workspace_catalog_ref=workspace_catalog_ref,
            workspace_catalog_generation=workspace_catalog_generation,
            workspace_catalog_root_digest=workspace_catalog_root_digest,
            code_catalog_ref=code_catalog_ref,
            code_catalog_generation=code_catalog_generation,
            code_catalog_root_digest=code_catalog_root_digest,
            code_catalog_match_admission_digests=match_admissions,
            graph_digest=graph.graph_digest,
        )
        package_ref_by_node_digest = {
            node.node_digest: package_ref for package_ref, node in graph_nodes.items()
        }
        resolutions_by_consumer: dict[
            str, list[WorkspaceDependencyTargetResolution]
        ] = {}
        for (consumer_ref, _, _), value in target_resolutions.items():
            resolutions_by_consumer.setdefault(consumer_ref, []).append(value)
        for values in resolutions_by_consumer.values():
            values.sort(
                key=lambda item: target_resolution_wire_bytes[
                    item.resolution_digest.value
                ]
            )
        node_bindings: list[WorkspaceSemanticMaterializationNodeExecutionBinding] = []
        for node_digest in (
            item for layer in graph.topological_layers for item in layer
        ):
            package_ref = package_ref_by_node_digest[node_digest]
            state = states[package_ref]
            assert (
                state.intent is not None
                and state.workspace_admission is not None
                and state.context is not None
                and state.match is not None
                and state.match_admission is not None
                and state.demand_set is not None
            )
            # The owner source was validated immediately before and after its
            # awaited planner call. Graph binding below performs no further
            # owner call, so bind that exact validated digest without a third
            # source read for every node.
            final_input_digest = state.planning_input_digest
            assert final_input_digest is not None
            resolutions = tuple(resolutions_by_consumer.get(package_ref, ()))
            binding_values: dict[str, object] = {
                "node_digest": node_digest,
                "package": state.entry.package,
                "package_entry": state.entry,
                "code_intent": state.intent,
                "workspace_admitted_intent": state.workspace_admission,
                "planning_context": state.context,
                "code_match": state.match,
                "code_match_admission": state.match_admission,
                "dependency_demand_set": state.demand_set,
                "planning_input_digest": final_input_digest,
                "planning_demand_closure": closures[package_ref],
                "incoming_target_resolutions": resolutions,
                "required_result_products": state.requirements,
            }
            binding_key = (
                node_digest.value,
                state.entry.entry_digest.value,
                state.intent.intent_digest.value,
                state.workspace_admission.admission_digest.value,
                state.context.context_digest.value,
                state.match.match_digest.value,
                state.match_admission.admission_digest.value,
                state.demand_set.demand_set_digest.value,
                final_input_digest.value,
                closures[package_ref].planning_demand_closure_digest.value,
                tuple(item.resolution_digest.value for item in resolutions),
                tuple(item.requirement_digest.value for item in state.requirements),
            )
            cached_binding_digest = self._node_execution_binding_digest_cache.get(
                binding_key
            )
            binding = _create_planner_node_execution_binding(
                **binding_values, binding_digest=cached_binding_digest
            )
            if cached_binding_digest is None:
                self._node_execution_binding_digest_cache[binding_key] = (
                    binding.binding_digest
                )
            node_bindings.append(binding)
        graph_binding_key = (
            graph.graph_digest.value,
            tuple(item.binding_digest.value for item in node_bindings),
        )
        cached_graph_binding_digest = self._graph_execution_binding_digest_cache.get(
            graph_binding_key
        )
        execution_binding = _create_planner_graph_execution_binding(
            graph=graph,
            ordered_node_bindings=tuple(node_bindings),
            binding_digest=cached_graph_binding_digest,
        )
        if cached_graph_binding_digest is None:
            self._graph_execution_binding_digest_cache[graph_binding_key] = (
                execution_binding.binding_digest
            )
        total = monotonic_ns() - started
        timings = _timings(
            selection_elapsed,
            provider_elapsed,
            dependency_elapsed,
            graph_elapsed,
            total,
        )
        counters = _counters(
            catalog_lookup_count=catalog_lookups,
            provider_match_count=provider_match_count,
            demand_planner_invocation_count=planner_invocations,
            fan_in_context_count=planner_invocations,
            fan_in_iteration_count=iterations,
            fan_in_lattice_addition_count=lattice_additions,
            fan_in_equal_context_reuse_count=equal_context_reuse,
            node_count=len(node_values),
            edge_count=len(edge_values),
            head_read_count=len(node_values),
            dependency_body_read_count=0,
        )
        return _create_planner_graph_plan_result(
            selection_resolution=selection,
            graph=graph,
            graph_plan_admission=admission,
            graph_execution_binding=execution_binding,
            timing_entries=timings,
            counter_entries=counters,
        )


def _compose_state(
    state: _State,
    code_catalog: CodeSemanticContractCatalogResolver,
) -> tuple[
    CodeSemanticMaterializationIntent, tuple[CodeSemanticRequiredResultProduct, ...]
]:
    demands = tuple(
        sorted(state.demands.values(), key=lambda item: item.demand_digest.value)
    )
    if demands:
        composition = code_catalog._compose_prevalidated_target_intent(
            target_package=state.entry.package, demands=demands
        )
        intent = composition.composed_intent
        requirements = composition.required_result_products
    elif state.root_plan is not None:
        return state.root_plan.code_intent, state.root_plan.required_result_products
    else:
        raise WorkspaceSemanticMaterializationPlanningError(
            "fan_in_nonprogress", "dependency_plan"
        )
    if state.root_plan is None:
        return intent, requirements
    root = state.root_plan
    if (
        root.code_intent.operation_kind != intent.operation_kind
        or root.code_intent.semantic_configuration_coordinate
        != intent.semantic_configuration_coordinate
    ):
        raise WorkspaceSemanticMaterializationPlanningError(
            "dependency_target_intent_conflict", "dependency_plan"
        )
    by_role = {item.role: item for item in requirements}
    for item in root.required_result_products:
        existing = by_role.get(item.role)
        if existing is not None and existing.contract != item.contract:
            raise WorkspaceSemanticMaterializationPlanningError(
                "dependency_result_contract_conflict", "dependency_plan"
            )
        by_role[item.role] = item
    requirements = tuple(by_role[key] for key in sorted(by_role, key=str.encode))
    intent = CodeSemanticMaterializationIntent.create(
        operation_kind=intent.operation_kind,
        requested_semantic_root_refs=tuple(
            sorted(
                set(intent.requested_semantic_root_refs)
                | set(root.code_intent.requested_semantic_root_refs),
                key=str.encode,
            )
        ),
        requested_terminal_output_roles=tuple(item.role for item in requirements),
        semantic_configuration_coordinate=intent.semantic_configuration_coordinate,
    )
    return intent, requirements


def _create_planner_root_intent_association(
    *,
    package_ref: str,
    intent: CodeSemanticMaterializationIntent,
    admission: WorkspaceAdmittedPackageIntent,
) -> WorkspaceMaterializationRootIntentAssociation:
    if type(intent) is not CodeSemanticMaterializationIntent:
        raise TypeError("planner root intent must be exact")
    if type(admission) is not WorkspaceAdmittedPackageIntent:
        raise TypeError("planner root admission must be exact")
    if (
        admission.package_ref != package_ref
        or admission.code_intent_digest != intent.intent_digest
    ):
        raise ContractViolation("planner root association context differs")
    payload = {
        "code_intent_digest": intent.intent_digest.to_wire(),
        "package_ref": package_ref,
        "workspace_intent_admission_digest": admission.admission_digest.to_wire(),
    }
    return _frozen_value(
        WorkspaceMaterializationRootIntentAssociation,
        package_ref=package_ref,
        code_intent_digest=intent.intent_digest,
        workspace_intent_admission_digest=admission.admission_digest,
        association_digest=_digest(
            WORKSPACE_MATERIALIZATION_ROOT_INTENT_ASSOCIATION, payload
        ),
    )


def _create_planner_workspace_admission(
    *,
    package_ref: str,
    code_intent_body: CodeSemanticMaterializationIntent,
    code_intent_wire: dict[str, object],
    catalog_root_digest: ContentDigest,
    catalog_generation: int,
    participation_policy_body: WorkspaceSemanticMaterializationParticipationPolicy,
    participation_policy_wire: dict[str, object],
) -> WorkspaceAdmittedPackageIntent:
    if type(code_intent_body) is not CodeSemanticMaterializationIntent:
        raise TypeError("planner admission intent must be exact")
    if type(catalog_root_digest) is not ContentDigest:
        raise TypeError("planner admission catalog root must be exact")
    if type(catalog_generation) is not int or catalog_generation < 0:
        raise TypeError("planner admission catalog generation must be nonnegative")
    if (
        type(participation_policy_body)
        is not WorkspaceSemanticMaterializationParticipationPolicy
    ):
        raise TypeError("planner participation policy must be exact")
    if (
        type(code_intent_wire) is not dict
        or type(participation_policy_wire) is not dict
    ):
        raise TypeError("planner admission wires must be exact dicts")
    if participation_policy_body.package_ref != package_ref:
        raise ContractViolation("participation policy package differs")
    payload = {
        "catalog_generation": catalog_generation,
        "catalog_root_digest": catalog_root_digest.to_wire(),
        "code_intent_body": code_intent_wire,
        "code_intent_digest": code_intent_body.intent_digest.to_wire(),
        "package_ref": package_ref,
        "participation_policy_body": participation_policy_wire,
        "participation_policy_digest": participation_policy_body.policy_digest.to_wire(),
    }
    return _frozen_value(
        WorkspaceAdmittedPackageIntent,
        package_ref=package_ref,
        code_intent_body=code_intent_body,
        code_intent_digest=code_intent_body.intent_digest,
        catalog_root_digest=catalog_root_digest,
        catalog_generation=catalog_generation,
        participation_policy_body=participation_policy_body,
        participation_policy_digest=participation_policy_body.policy_digest,
        admission_digest=_digest(WORKSPACE_ADMITTED_PACKAGE_INTENT, payload),
    )


def _create_planner_selection_resolution(
    *,
    proposal: WorkspaceMaterializationSelectionProposal,
    catalog_root_digest: ContentDigest,
    catalog_generation: int,
    expanded_package_refs: tuple[str, ...],
    root_intent_associations: tuple[WorkspaceMaterializationRootIntentAssociation, ...],
) -> WorkspaceMaterializationSelectionResolution:
    if type(proposal) is not WorkspaceMaterializationSelectionProposal:
        raise TypeError("planner selection proposal must be exact")
    if type(catalog_root_digest) is not ContentDigest:
        raise TypeError("planner catalog root must be exact")
    if type(catalog_generation) is not int or catalog_generation < 0:
        raise TypeError("planner catalog generation must be nonnegative integer")
    if (
        type(expanded_package_refs) is not tuple
        or type(root_intent_associations) is not tuple
    ):
        raise TypeError("planner selection closures must be exact tuples")
    if (
        tuple(sorted(set(expanded_package_refs), key=str.encode))
        != expanded_package_refs
    ):
        raise ContractViolation("planner expanded packages must be unique and ordered")
    if any(
        type(item) is not WorkspaceMaterializationRootIntentAssociation
        for item in root_intent_associations
    ):
        raise TypeError("planner root associations must be exact")
    if len(expanded_package_refs) != len(root_intent_associations) or any(
        package_ref != association.package_ref
        for package_ref, association in zip(
            expanded_package_refs, root_intent_associations, strict=True
        )
    ):
        raise ContractViolation("planner package and root association closure differs")
    payload = {
        "catalog_generation": catalog_generation,
        "catalog_root_digest": catalog_root_digest.to_wire(),
        "expanded_package_refs": list(expanded_package_refs),
        "proposal_digest": proposal.proposal_digest.to_wire(),
        "root_intent_associations": [
            item.to_wire() for item in root_intent_associations
        ],
    }
    return _frozen_value(
        WorkspaceMaterializationSelectionResolution,
        proposal_digest=proposal.proposal_digest,
        catalog_root_digest=catalog_root_digest,
        catalog_generation=catalog_generation,
        expanded_package_refs=expanded_package_refs,
        root_intent_associations=root_intent_associations,
        resolution_digest=_digest(
            WORKSPACE_MATERIALIZATION_SELECTION_RESOLUTION, payload
        ),
    )


def _constraints_admitted(
    demand: SemanticDependencyDemand,
    allowed: tuple[SemanticDependencyTargetConstraint, ...],
) -> bool:
    return {
        (item.constraint_kind, item.constraint_value)
        for item in demand.target_constraints
    } <= {(item.constraint_kind, item.constraint_value) for item in allowed}


def _topological_package_order(
    package_refs: tuple[str, ...], edge_demands: tuple[_EdgeDemand, ...]
) -> tuple[str, ...]:
    dependencies = {ref: set() for ref in package_refs}
    for edge in edge_demands:
        dependencies[edge.consumer_ref].add(edge.target_ref)
    remaining = {key: set(value) for key, value in dependencies.items()}
    result: list[str] = []
    while remaining:
        ready = sorted(
            (key for key, value in remaining.items() if not value), key=str.encode
        )
        if not ready:
            raise WorkspaceSemanticMaterializationPlanningError(
                "dependency_cycle", "graph_derive"
            )
        for key in ready:
            result.append(key)
            del remaining[key]
            for value in remaining.values():
                value.discard(key)
    return tuple(result)


def _timings(*values: int) -> tuple[WorkspaceMaterializationPlanningTimingEntry, ...]:
    return tuple(
        WorkspaceMaterializationPlanningTimingEntry(stage=stage, elapsed_ns=value)
        for stage, value in zip(
            WORKSPACE_MATERIALIZATION_PLANNING_TIMING_STAGES, values, strict=True
        )
    )


def _counters(
    **values: int,
) -> tuple[WorkspaceMaterializationPlanningCounterEntry, ...]:
    return tuple(
        WorkspaceMaterializationPlanningCounterEntry(
            counter=counter, value=values[counter]
        )
        for counter in WORKSPACE_MATERIALIZATION_PLANNING_COUNTERS
    )


__all__ = [
    "WORKSPACE_SEMANTIC_ROOT_CODE_PLAN",
    "WorkspaceSemanticMaterializationGraphPlanner",
    "WorkspaceSemanticMaterializationPlanningError",
    "WorkspaceSemanticPackageHeadReader",
    "WorkspaceSemanticRootCodePlan",
]
