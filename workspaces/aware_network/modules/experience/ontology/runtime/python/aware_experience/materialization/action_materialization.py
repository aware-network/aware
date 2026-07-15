from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import UUID

from aware_code.types.json import JsonValue
from aware_environment_service_dto.environment.environment import InvokeFunctionResponse
from aware_experience import stable_ids as experience_stable_ids
from aware_experience.environment_profile.runtime_support import (
    invoke_support,
    ocg_support,
)
from aware_experience.materialization.compile_plan_payloads import (
    _expect_list,
    _expect_mapping,
    _optional_payload_token,
    load_experience_compile_plan_payloads,
)
from aware_experience.program.registry_index import find_repo_root
from aware_meta.materialization import (
    MaterializationExecutor,
    MaterializationLaneContext,
    MaterializationPlan,
    MaterializationRunReceipt,
    MaterializationStep,
    MaterializationStepResult,
)
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_reactivity_ontology.stable_ids import stable_action_config_id


class RuntimeProtocol(Protocol):
    @property
    def manifest_path(self) -> Path: ...


class ConstructorEnvironmentFunctionInvoker(Protocol):
    async def __call__(
        self,
        *,
        runtime: RuntimeProtocol,
        index: MetaGraphRuntimeIndex,
        actor_id: UUID | None,
        lane: MaterializationLaneContext,
        function_id: UUID,
        args: list[JsonValue],
        environment_id: UUID | None = None,
        process_id: UUID | None = None,
        thread_id: UUID | None = None,
    ) -> InvokeFunctionResponse: ...


@dataclass(frozen=True, slots=True)
class ActionMaterializationDependencies:
    invoke_constructor_environment_function: ConstructorEnvironmentFunctionInvoker


def _normalize_action_symbol(raw: str) -> str:
    token = (raw or "").strip()
    if not token:
        return ""
    if "." in token:
        token = token.split(".")[-1]
    return token.strip()


@dataclass(frozen=True, slots=True)
class ActionMaterializationSpec:
    action_name: str
    program_keys: tuple[str, ...]
    is_dependency: bool = False


def resolve_action_materialization_specs(
    *,
    compile_plan_payloads: Sequence[Mapping[str, object]],
) -> tuple[ActionMaterializationSpec, ...]:
    if not compile_plan_payloads:
        return ()

    action_rows_by_ref: dict[str, Mapping[str, object]] = {}
    environment_rows: list[Mapping[str, object]] = []
    for payload in compile_plan_payloads:
        action_ownership_raw = _expect_list(
            payload.get("action_ownership", []),
            field_name="action_ownership",
        )
        for action_row_obj in action_ownership_raw:
            action_row = _expect_mapping(
                action_row_obj, field_name="action_ownership[]"
            )
            if not bool(action_row.get("is_dependency", False)):
                _register_action_row_reference(
                    reference=str(action_row.get("symbol") or ""),
                    row=action_row,
                    catalog=action_rows_by_ref,
                )
                _register_action_row_reference(
                    reference=str(action_row.get("action_name") or ""),
                    row=action_row,
                    catalog=action_rows_by_ref,
                )
            for reference in _qualified_action_row_references(action_row=action_row):
                _register_action_row_reference(
                    reference=reference,
                    row=action_row,
                    catalog=action_rows_by_ref,
                )

        environment_ownership_raw = _expect_list(
            payload.get("environment_ownership", []),
            field_name="environment_ownership",
        )
        for environment_row_obj in environment_ownership_raw:
            environment_row = _expect_mapping(
                environment_row_obj, field_name="environment_ownership[]"
            )
            environment_rows.append(environment_row)

    if not environment_rows:
        return ()
    if len(environment_rows) != 1:
        raise RuntimeError(
            "provision_environment_experience currently requires exactly one environment ownership declaration "
            + f"across compiled experience packages. Found {len(environment_rows)} entries."
        )

    environment_row = environment_rows[0]
    programs_raw = _expect_list(
        environment_row.get("programs", []), field_name="environment.programs"
    )
    events_raw = _expect_list(
        environment_row.get("events", []), field_name="environment.events"
    )

    environment_program_config_symbols: set[str] = set()
    for program_row_obj in programs_raw:
        program_row = _expect_mapping(
            program_row_obj, field_name="environment.programs[]"
        )
        config_symbol = _normalize_action_symbol(
            str(program_row.get("program_config") or "")
        )
        if config_symbol:
            environment_program_config_symbols.add(config_symbol)

    action_program_keys_by_name: dict[str, set[str]] = {}
    action_dependency_by_name: dict[str, bool] = {}
    for event_row_obj in events_raw:
        event_row = _expect_mapping(event_row_obj, field_name="environment.events[]")
        actions_raw = _expect_list(
            event_row.get("actions", []), field_name="environment.events[].actions"
        )
        for action_ref_obj in actions_raw:
            action_ref = _expect_mapping(
                action_ref_obj, field_name="environment.events[].actions[]"
            )
            action_ref_raw = str(action_ref.get("action") or "").strip()
            action_ref_key = _action_reference_key(action_ref_raw)
            if not action_ref_key:
                continue
            action_row = action_rows_by_ref.get(action_ref_key)
            if action_row is None:
                raise RuntimeError(
                    "Invalid experience compile plan: environment action reference has no matching action "
                    + f"ownership entry: {action_ref_raw!r}"
                )
            action_name = (
                str(action_row.get("action_name") or action_ref_raw).strip()
                or action_ref_raw
            )
            action_dependency_by_name[action_name] = bool(
                action_row.get("is_dependency", False)
            )
            bindings_raw = _expect_list(
                action_row.get("program_bindings", []),
                field_name="action_ownership[].program_bindings",
            )
            key_bucket = action_program_keys_by_name.setdefault(action_name, set())
            for binding_obj in bindings_raw:
                binding = _expect_mapping(
                    binding_obj, field_name="action_ownership[].program_bindings[]"
                )
                program_symbol = _normalize_action_symbol(
                    str(binding.get("program") or "")
                )
                if not program_symbol:
                    continue
                if program_symbol not in environment_program_config_symbols:
                    raise RuntimeError(
                        "Invalid experience compile plan for provisioning: action binding program "
                        + f"{program_symbol!r} is not declared in environment program_config catalog"
                    )
                key_bucket.add(program_symbol)

    return tuple(
        ActionMaterializationSpec(
            action_name=action_name,
            program_keys=tuple(sorted(program_keys)),
            is_dependency=action_dependency_by_name.get(action_name, False),
        )
        for action_name, program_keys in sorted(action_program_keys_by_name.items())
    )


def _register_action_row_reference(
    *,
    reference: str,
    row: Mapping[str, object],
    catalog: dict[str, Mapping[str, object]],
) -> None:
    ref_key = _action_reference_key(reference)
    if not ref_key:
        return
    prior = catalog.get(ref_key)
    if prior is None or prior == row:
        catalog[ref_key] = row
        return
    raise RuntimeError(
        "Invalid experience compile plan: ambiguous action reference key "
        + f"{ref_key!r}; use a dependency-qualified action ref"
    )


def _qualified_action_row_references(
    *,
    action_row: Mapping[str, object],
) -> tuple[str, ...]:
    prefixes = _action_row_prefixes(action_row=action_row)
    symbol = str(action_row.get("symbol") or "").strip()
    action_name = str(action_row.get("action_name") or "").strip()
    references: list[str] = []
    for prefix in prefixes:
        if symbol:
            references.append(f"{prefix}.{symbol}")
        if action_name:
            references.append(f"{prefix}.{action_name}")
    return tuple(dict.fromkeys(references))


def _action_row_prefixes(
    *,
    action_row: Mapping[str, object],
) -> tuple[str, ...]:
    prefixes: list[str] = []
    for raw in (
        _optional_payload_token(action_row.get("fqn_prefix")),
        _optional_payload_token(action_row.get("package_name")),
    ):
        token = _action_owner_prefix(raw)
        if token:
            prefixes.append(token)
    return tuple(dict.fromkeys(prefixes))


def _action_reference_key(raw: str) -> str:
    token = (raw or "").strip()
    if not token:
        return ""
    return "".join(ch for ch in token.casefold() if ch.isalnum())


def _action_owner_prefix(raw: str | None) -> str:
    return (raw or "").strip().replace("-", "_")


def build_action_materialization_plan(
    *,
    lane: MaterializationLaneContext,
    specs: Sequence[ActionMaterializationSpec],
) -> MaterializationPlan:
    steps = tuple(
        MaterializationStep(
            step_id=f"action:{spec.action_name}",
            step_kind="experience.action",
            payload={
                "action_name": spec.action_name,
                "program_keys": list(spec.program_keys),
            },
            commit_requested=True,
        )
        for spec in specs
    )
    return MaterializationPlan(
        module_id="experience",
        pipeline_id="experience.compile_plan.action",
        lane=lane,
        steps=steps,
    )


def _has_planned_threads(*, planned_processes: Sequence[Mapping[str, object]]) -> bool:
    for process_plan in planned_processes:
        threads = process_plan.get("threads")
        if isinstance(threads, list) and threads:
            return True
    return False


async def materialize_experience_compile_plan_actions(
    *,
    runtime: RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    planned_processes: Sequence[Mapping[str, object]],
    dependencies: ActionMaterializationDependencies,
) -> MaterializationRunReceipt | None:
    if not _has_planned_threads(planned_processes=planned_processes):
        return None

    repo_root = find_repo_root(start=runtime.manifest_path.parent)
    compile_plan_payloads = load_experience_compile_plan_payloads(repo_root=repo_root)
    action_specs = resolve_action_materialization_specs(
        compile_plan_payloads=compile_plan_payloads
    )
    if not action_specs:
        return None

    action_experience_projection_hash = ocg_support.find_projection_hash_by_name(
        index=index,
        projection_name="ActionExperience",
    )
    action_experience_build_fn_id = ocg_support.resolve_public_function_id(
        index=index,
        class_name_suffix="aware_experience_ontology.action.action_experience.ActionExperience",
        function_name="build",
    )
    action_experience_add_program_config_fn_id = ocg_support.resolve_public_function_id(
        index=index,
        class_name_suffix="aware_experience_ontology.action.action_experience.ActionExperience",
        function_name="add_program_config",
    )

    action_lane = MaterializationLaneContext(
        branch_id=lane.branch_id,
        projection_hash=action_experience_projection_hash,
    )
    plan = build_action_materialization_plan(lane=action_lane, specs=action_specs)

    async def _runner(
        *, plan: MaterializationPlan, step: MaterializationStep
    ) -> MaterializationStepResult:
        action_name = str(step.payload.get("action_name") or "").strip()
        if not action_name:
            raise ValueError(
                f"materialization action_name is required: step_id={step.step_id!r}"
            )

        program_keys_raw = step.payload.get("program_keys")
        program_keys_list = _expect_list(
            program_keys_raw, field_name=f"{step.step_id}.program_keys"
        )
        program_keys = [
            str(item).strip() for item in program_keys_list if str(item).strip()
        ]

        action_config_id = stable_action_config_id(name=action_name)
        action_experience_id = experience_stable_ids.stable_action_experience_id(
            action_config_id=action_config_id,
        )
        action_build_result = (
            await dependencies.invoke_constructor_environment_function(
                runtime=runtime,
                index=index,
                actor_id=actor_id,
                lane=plan.lane,
                function_id=action_experience_build_fn_id,
                args=[str(action_config_id)],
            )
        )
        invoke_support.assert_invoke_succeeded(
            response=action_build_result,
            label=f"ActionExperience.build({action_name})",
        )

        commit_id: UUID | None = action_build_result.commit_id
        head_commit_id: UUID | None = (
            action_build_result.object_instance_graph_commit_id
        )

        for program_key in program_keys:
            program_config_id = experience_stable_ids.stable_program_config_id(
                key=program_key
            )
            add_program_result = (
                await invoke_support.invoke_instance_environment_function(
                    runtime=runtime,
                    index=index,
                    actor_id=actor_id,
                    environment_id=None,
                    process_id=None,
                    thread_id=None,
                    branch_id=plan.lane.branch_id,
                    projection_hash=plan.lane.projection_hash,
                    object_id=action_experience_id,
                    function_id=action_experience_add_program_config_fn_id,
                    args=[str(program_config_id)],
                    commit=True,
                )
            )
            invoke_support.assert_invoke_succeeded(
                response=add_program_result,
                label=f"ActionExperience.add_program_config({action_name}:{program_key})",
            )
            if add_program_result.commit_id is not None:
                commit_id = add_program_result.commit_id
            if add_program_result.object_instance_graph_commit_id is not None:
                head_commit_id = add_program_result.object_instance_graph_commit_id

        return MaterializationStepResult(
            details={
                "action_name": action_name,
                "program_keys": program_keys,
            },
            commit_id=commit_id,
            head_commit_id=head_commit_id,
        )

    executor = MaterializationExecutor()
    return await executor.run(plan=plan, runner=_runner)
