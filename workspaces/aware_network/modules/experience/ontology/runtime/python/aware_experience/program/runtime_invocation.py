from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
import importlib
import json
from pathlib import Path
from typing import Any, Protocol
from uuid import UUID

# Aware Grammar
from aware_experience.program.language import (
    InvocationPlan,
    PlanCall,
    PlanExpectEventConfig,
    PlanExpr,
    PlanInput,
    PlanInvoke,
    PlanIntentActionConfig,
    PlanLet,
    PlanLocalRef,
    PlanPortContract,
    PlanSymbolRef,
    decode_invocation_plan_artifact,
    compile_invocation_plans,
)
from aware_experience.program.language.stdlib import stable_ns_url, stable_uuid5

# Aware Code
from aware_code.types.json import JsonArray, JsonObject, JsonValue

# Aware Meta
from aware_meta_ontology.stable_ids import (
    stable_attribute_config_id,
    stable_class_config_id,
    stable_function_config_id,
)
from aware_meta.graph.config.stable_ids import stable_class_relationship_id
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore

# Environment Api
from aware_environment_service_dto.environment.environment import (
    InvokeFunctionCallTarget,
    InvokeFunctionRequest,
    CapabilityFunction,
    CapabilityObject,
)
from aware_experience.program import runtime_discovery as program_discovery


@dataclass(frozen=True, slots=True)
class OpgRef:
    opg_id: UUID
    projection_hash: str


@dataclass(frozen=True, slots=True)
class ProgramIntentRecord:
    event_id: UUID | None
    action_config_id: UUID
    event_config_id: UUID
    intent_key: str
    step_index: int
    program_turn_instruction_id: UUID
    program_impl_instruction_intent_id: UUID


class ProgramApplyError(RuntimeError):
    pass


class ProgramRegistryError(RuntimeError):
    pass


class ProgramContractValidator(Protocol):
    async def validate_event_action_contracts(
        self,
        *,
        event_expectations: Mapping[UUID, bool],
        action_intents: Iterable[tuple[UUID, UUID]],
    ) -> None: ...


class ProgramIntentRecorder(Protocol):
    async def record_program_intent(self, record: ProgramIntentRecord) -> None: ...


class CommitHeadStore(Protocol):
    async def head(
        self, *, branch_id: UUID, projection_hash: str
    ) -> Mapping[str, object] | None:
        """Read a projection lane head without requiring a concrete FS store."""
        ...


def _read_field(container: object, *, name: str) -> object:
    if isinstance(container, Mapping):
        return container.get(name)
    return getattr(container, name, None)


def coerce_uuid_or_none(raw_value: object) -> UUID | None:
    if raw_value is None:
        return None
    if isinstance(raw_value, UUID):
        return raw_value
    text = str(raw_value).strip()
    if not text:
        return None
    try:
        return UUID(text)
    except Exception:  # noqa: BLE001
        return None


def extract_lane_resolution_from_program_results(
    value: object,
) -> tuple[UUID, str] | None:
    if isinstance(value, Mapping):
        branch_id = coerce_uuid_or_none(value.get("branch_id"))
        projection_hash = str(value.get("projection_hash") or "").strip() or None
        if branch_id is not None and projection_hash is not None:
            return branch_id, projection_hash
        nested = value.get("results")
        if isinstance(nested, (list, tuple)):
            for item in nested:
                resolved = extract_lane_resolution_from_program_results(item)
                if resolved is not None:
                    return resolved
        return None
    if isinstance(value, (list, tuple)):
        for item in value:
            resolved = extract_lane_resolution_from_program_results(item)
            if resolved is not None:
                return resolved
    return None


def extract_lane_resolution_from_apply_response(
    apply_response: object,
    *,
    allow_nested_fallback: bool = True,
) -> tuple[UUID, str] | None:
    resolved_branch_id = coerce_uuid_or_none(
        _read_field(apply_response, name="resolved_branch_id")
    )
    resolved_projection_hash = (
        str(_read_field(apply_response, name="resolved_projection_hash") or "").strip()
        or None
    )
    if resolved_branch_id is not None and resolved_projection_hash is not None:
        return resolved_branch_id, resolved_projection_hash
    if not allow_nested_fallback:
        return None
    return extract_lane_resolution_from_program_results(
        _read_field(apply_response, name="results")
    )


def _coerce_int(value: object) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            return None
    return None


def parse_invoke_perf_logs(log_lines: object) -> dict[str, int]:
    """Parse canonical `perf.invoke.<name>=<int>` lines from invoke logs."""
    metrics: dict[str, int] = {}
    if not isinstance(log_lines, (list, tuple)):
        return metrics
    for line in log_lines:
        if not isinstance(line, str):
            continue
        text = line.strip()
        if not text.startswith("perf.invoke."):
            continue
        metric_expr = text[len("perf.invoke.") :]
        if "=" not in metric_expr:
            continue
        raw_name, raw_value = metric_expr.split("=", 1)
        metric_name = str(raw_name or "").strip()
        if not metric_name:
            continue
        try:
            metric_value = int(str(raw_value or "").strip())
        except Exception:  # noqa: BLE001
            continue
        metrics[metric_name] = max(metric_value, 0)
    return metrics


def aggregate_program_apply_metrics_from_results(value: object) -> dict[str, int]:
    """Aggregate invoke perf from program executor results into stable apply metrics."""
    aggregated: dict[str, int] = {}

    def _add_metric(*, name: str, value: object) -> None:
        coerced = _coerce_int(value)
        if coerced is None:
            return
        if coerced < 0:
            coerced = 0
        aggregated[name] = int(aggregated.get(name, 0)) + coerced

    def _walk(node: object) -> None:
        if isinstance(node, Mapping):
            invoke_perf = node.get("invoke_perf")
            if isinstance(invoke_perf, Mapping):
                _add_metric(name="apply_local_invoke_calls", value=1)
                for raw_name, raw_value in invoke_perf.items():
                    metric_name = str(raw_name or "").strip()
                    if not metric_name:
                        continue
                    _add_metric(
                        name=f"apply_local_invoke_{metric_name}",
                        value=raw_value,
                    )
            execution_time_ms = node.get("execution_time_ms")
            if execution_time_ms is not None:
                _add_metric(
                    name="apply_local_invoke_response_execution_ms",
                    value=execution_time_ms,
                )
            nested = node.get("results")
            if isinstance(nested, (list, tuple)):
                for item in nested:
                    _walk(item)
            return
        if isinstance(node, (list, tuple)):
            for item in node:
                _walk(item)

    _walk(value)
    return aggregated


def _extract_latest_metrics_from_feedback_rows(
    feedback_rows: object,
    *,
    payload_key: str,
) -> dict[str, int]:
    """Resolve latest metric mapping from turn feedback payload rows."""
    if not isinstance(feedback_rows, (list, tuple)):
        return {}

    latest_sequence = -1
    resolved: dict[str, int] = {}
    for row in feedback_rows:
        if not isinstance(row, Mapping):
            continue
        payload = row.get("payload")
        if not isinstance(payload, Mapping):
            continue
        raw_metrics = payload.get(payload_key)
        if not isinstance(raw_metrics, Mapping):
            continue
        sequence = _coerce_int(row.get("sequence")) or 0
        if sequence < latest_sequence:
            continue
        normalized: dict[str, int] = {}
        for raw_name, raw_value in raw_metrics.items():
            metric_name = str(raw_name or "").strip()
            if not metric_name:
                continue
            metric_value = _coerce_int(raw_value)
            if metric_value is None:
                continue
            normalized[metric_name] = max(metric_value, 0)
        resolved = normalized
        latest_sequence = sequence
    return resolved


def extract_program_apply_metrics_from_feedback_rows(
    feedback_rows: object,
) -> dict[str, int]:
    """Resolve latest canonical apply metrics from turn feedback payload rows."""
    return _extract_latest_metrics_from_feedback_rows(
        feedback_rows,
        payload_key="program_apply_metrics",
    )


def extract_turn_orchestration_metrics_from_feedback_rows(
    feedback_rows: object,
) -> dict[str, int]:
    """Resolve latest runtime turn orchestration metrics from feedback payload."""
    return _extract_latest_metrics_from_feedback_rows(
        feedback_rows,
        payload_key="turn_orchestration_metrics",
    )


def _lower_key(value: str) -> str:
    return (value or "").strip().casefold()


def _coerce_json_value(value: object) -> JsonValue:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _coerce_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_coerce_json_value(item) for item in value]
    return str(value)


def _coerce_json_array(values: list[object]) -> JsonArray:
    return JsonArray([_coerce_json_value(value) for value in values])


def _coerce_json_object(values: dict[str, object]) -> JsonObject:
    return JsonObject({key: _coerce_json_value(value) for key, value in values.items()})


def _split_call_target(target: str) -> tuple[str, str]:
    raw = (target or "").strip()
    if not raw or "." not in raw:
        raise ProgramApplyError(f"Invalid call target: {target!r}")
    owner, fn = raw.rsplit(".", 1)
    owner = owner.strip()
    fn = fn.strip()
    if not owner or not fn:
        raise ProgramApplyError(f"Invalid call target: {target!r}")
    return owner, fn


def _get_call_arg(
    call: PlanCall, *, name: str, default: PlanExpr | None = None
) -> PlanExpr | None:
    for arg in call.args:
        if arg.name == name:
            return arg.value
    return default


def _resolve_bundle_root_from_manifest_path(manifest_path: Path) -> Path:
    """Resolve the bundle root as the parent of the nearest Aware artifact directory."""
    aware_dir = next(
        (p for p in manifest_path.parents if p.name in {".aware", "_aware"}), None
    )
    if aware_dir is None:
        # Tests may write ad-hoc manifests outside Aware artifact roots; fall back to manifest dir.
        return manifest_path.parent
    return aware_dir.parent


def resolve_bundle_root_from_manifest_path(manifest_path: Path) -> Path:
    return _resolve_bundle_root_from_manifest_path(manifest_path)


def validate_required_symbols(
    *,
    required_symbols: Iterable[str] | None,
    provided_symbols: dict[str, object] | None,
    actor_id: UUID,
    environment_id: UUID,
    process_id: UUID | None,
    thread_id: UUID,
    program_ref: str,
    context: str,
) -> None:
    required = [
        (raw or "").strip()
        for raw in list(required_symbols or [])
        if (raw or "").strip()
    ]
    if not required:
        return

    available = dict(provided_symbols or {})
    missing: list[str] = []
    for name in required:
        if _is_required_symbol_bound(
            symbol_name=name,
            provided_symbols=available,
            actor_id=actor_id,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
        ):
            continue
        missing.append(name)

    if not missing:
        return
    raise ProgramApplyError(
        f"{context} missing required symbols for {program_ref}: {sorted(set(missing))}"
    )


def _is_required_symbol_bound(
    *,
    symbol_name: str,
    provided_symbols: dict[str, object],
    actor_id: UUID,
    environment_id: UUID,
    process_id: UUID | None,
    thread_id: UUID,
) -> bool:
    key = (symbol_name or "").strip()
    if not key:
        return True
    if key in provided_symbols:
        return True
    if key == "plan.actor_id":
        return actor_id is not None
    if key == "plan.environment_id":
        return environment_id is not None
    if key == "plan.process_id":
        return process_id is not None
    if key == "plan.thread_id":
        return thread_id is not None
    return False


def required_symbols_from_invocation_plan(*, plan: InvocationPlan) -> list[str]:
    required: list[str] = []
    for step in list(plan.steps or ()):
        if not isinstance(step, PlanInput):
            continue
        if not bool(step.required):
            continue
        if step.default is not None:
            continue
        if not isinstance(step.source, PlanSymbolRef):
            continue
        symbol_name = (step.source.name or "").strip()
        if not symbol_name:
            continue
        required.append(symbol_name)
    return sorted(set(required))


class RuntimeInvocationPlanExecutor:
    """Server-side `.aware program` executor (commit-backed, invoker-only).

    This mirrors the CLI executor contract (capability-backed resolution), but runs
    inside the ENVIRONMENT service boundary so clients can call by ref.
    """

    def __init__(
        self,
        *,
        invoker: Any,
        index: Any,
        actor_id: UUID,
        environment_id: UUID,
        process_id: UUID | None,
        thread_id: UUID,
        commit: bool,
        publish: bool,
        symbols: dict[str, object] | None = None,
        program_ref_stack: tuple[str, ...] = (),
        contract_validator: ProgramContractValidator | None = None,
        intent_recorder: ProgramIntentRecorder | None = None,
        store: CommitHeadStore | None = None,
    ) -> None:
        self._invoker = invoker
        self._index = index
        self._actor_id = actor_id
        self._environment_id = environment_id
        self._process_id = process_id
        self._thread_id = thread_id
        self._commit = bool(commit)
        self._publish = bool(publish)

        self._base_symbols: dict[str, object] = dict(symbols or {})
        self._symbols: dict[str, object] = dict(self._base_symbols)
        self._locals: dict[str, object] = {}
        self._program_ref_stack: tuple[str, ...] = tuple(program_ref_stack)
        self._contract_validator = contract_validator
        self._intent_recorder = intent_recorder

        self._opgs_by_name: dict[str, OpgRef] | None = None
        self._objects_by_name: dict[str, list[CapabilityObject]] | None = None

        self._dynamic_pure_fn_cache: dict[str, Callable[..., object]] = {}

        # Execution context (mutable)
        self._current_lane_branch_id: UUID | None = None
        self._current_lane_opg: OpgRef | None = None
        self._current_lane_head_commit_id: UUID | None = None
        self._skip_calls_in_lane: bool = False
        self._resolved_lane_branch_id: UUID | None = None
        self._resolved_lane_projection_hash: str | None = None
        self._event_expectations: dict[UUID, bool] = {}
        self._action_intents: list[tuple[UUID, UUID]] = []
        self._bound_node_aliases: set[str] = set()

        self._store = store

        self._pure_fns: dict[str, Callable[..., object]] = {
            # Generic stable-id helpers. Module-owned stable-id functions are resolved dynamically:
            # `<module_id>.stable_<fn_name>` -> `aware_<module_id>_ontology.stable_ids.<fn_name>`
            # (fallback: `aware_<module_id>.stable_ids`).
            "stable.ns_url": stable_ns_url,
            "stable.uuid5": stable_uuid5,
            "kernel.list": self._fn_kernel_list,
            "kernel.symbols": self._fn_kernel_symbols,
            # Meta (OCG plane) stable ids (single canonical source).
            "meta.stable_class_config_id": stable_class_config_id,
            "meta.stable_attribute_config_id": stable_attribute_config_id,
            "meta.stable_class_relationship_id": stable_class_relationship_id,
            "meta.stable_function_config_id": stable_function_config_id,
            "meta.resolve_class_config_id": self._fn_meta_resolve_class_config_id,
            "meta.resolve_function_config_id": self._fn_meta_resolve_function_config_id,
        }

    # ------------------------------------------------------------------

    def _commit_store(self) -> CommitHeadStore:
        if self._store is None:
            self._store = FSCommitStore()
        return self._store

    # ------------------------------------------------------------------
    # Expression evaluation
    # ------------------------------------------------------------------

    def _eval_symbol(self, name: str) -> object:
        key = (name or "").strip()
        if key in self._symbols:
            return self._symbols[key]
        if key.startswith("plan."):
            if key == "plan.actor_id":
                return self._actor_id
            if key == "plan.environment_id":
                return self._environment_id
            if key == "plan.process_id":
                return self._process_id
            if key == "plan.thread_id":
                return self._thread_id
        # Default: treat as a symbolic literal (enum/value name).
        return key

    def _eval_expr(self, expr: PlanExpr) -> object:
        if isinstance(expr, PlanLocalRef):
            if expr.name not in self._locals:
                raise ProgramApplyError(f"Undefined local reference: {expr.name!r}")
            return self._locals[expr.name]

        if isinstance(expr, PlanSymbolRef):
            return self._eval_symbol(expr.name)

        if isinstance(expr, PlanCall):
            fn = self._resolve_pure_fn(expr.target)
            if fn is None:
                available = sorted(self._pure_fns.keys())
                raise ProgramApplyError(
                    f"Unsupported pure function call in program: {expr.target!r} (available={available})"
                )
            args, kwargs = self._eval_call_args(expr)
            return fn(*args, **kwargs)

        return expr

    def _try_eval_symbol_strict(self, name: str) -> tuple[bool, object | None]:
        key = (name or "").strip()
        if key in self._symbols:
            return True, self._symbols[key]
        if key.startswith("plan."):
            if key == "plan.actor_id":
                return True, self._actor_id
            if key == "plan.environment_id":
                return True, self._environment_id
            if key == "plan.process_id":
                return True, self._process_id
            if key == "plan.thread_id":
                return True, self._thread_id
        return False, None

    def _try_eval_input_source(self, expr: PlanExpr) -> tuple[bool, object | None]:
        if isinstance(expr, PlanLocalRef):
            if expr.name in self._locals:
                return True, self._locals[expr.name]
            return False, None
        if isinstance(expr, PlanSymbolRef):
            return self._try_eval_symbol_strict(expr.name)
        return True, self._eval_expr(expr)

    def _resolve_pure_fn(self, target: str) -> Callable[..., object] | None:
        fn = self._pure_fns.get(target)
        if fn is not None:
            return fn

        cached = self._dynamic_pure_fn_cache.get(target)
        if cached is not None:
            return cached

        raw = (target or "").strip()
        if "." not in raw:
            return None
        module_id, fn_name = raw.split(".", 1)
        module_id = module_id.strip()
        fn_name = fn_name.strip()
        if not module_id or not fn_name.startswith("stable_"):
            return None
        if not all(ch.isalnum() or ch == "_" for ch in module_id):
            return None

        module_candidates = (
            f"aware_{module_id}_ontology.stable_ids",
            f"aware_{module_id}.stable_ids",
        )
        for module_name in module_candidates:
            try:
                mod = importlib.import_module(module_name)
            except ModuleNotFoundError:
                continue
            attr = getattr(mod, fn_name, None)
            if callable(attr):
                self._dynamic_pure_fn_cache[target] = attr
                return attr

        return None

    def _eval_call_args(self, call: PlanCall) -> tuple[list[object], dict[str, object]]:
        args: list[object] = []
        kwargs: dict[str, object] = {}
        for arg in call.args:
            value = self._eval_expr(arg.value)
            if arg.name is None:
                args.append(value)
            else:
                kwargs[arg.name] = value
        return args, kwargs

    @staticmethod
    def _fn_kernel_list(*values: object) -> list[object]:
        return list(values)

    @staticmethod
    def _fn_kernel_symbols(*items: object) -> dict[str, object]:
        if len(items) % 2 != 0:
            raise ProgramApplyError(
                "kernel.symbols requires an even number of arguments (key/value pairs)"
            )
        out: dict[str, object] = {}
        idx = 0
        while idx < len(items):
            key = str(items[idx]).strip()
            if not key:
                raise ProgramApplyError("kernel.symbols keys must be non-empty strings")
            out[key] = items[idx + 1]
            idx += 2
        return out

    def _fn_meta_resolve_class_config_id(self, *, class_name: str) -> UUID:
        self._ensure_capability_index()
        assert self._objects_by_name is not None

        key = _lower_key(class_name)
        matches = list(self._objects_by_name.get(key, []))
        if not matches:
            available = sorted(self._objects_by_name.keys())
            raise ProgramApplyError(
                f"Unknown capability object for class_name={class_name!r} (available={available})"
            )
        if len(matches) > 1:
            ids = sorted(str(obj.id) for obj in matches)
            raise ProgramApplyError(
                f"Ambiguous capability object for class_name={class_name!r} (ids={ids})"
            )
        return matches[0].id

    def _fn_meta_resolve_function_config_id(
        self, *, class_name: str, function_name: str
    ) -> UUID:
        self._ensure_capability_index()
        assert self._objects_by_name is not None

        key = _lower_key(class_name)
        matches = list(self._objects_by_name.get(key, []))
        if not matches:
            available = sorted(self._objects_by_name.keys())
            raise ProgramApplyError(
                f"Unknown capability object for class_name={class_name!r} (available={available})"
            )
        if len(matches) > 1:
            ids = sorted(str(obj.id) for obj in matches)
            raise ProgramApplyError(
                f"Ambiguous capability object for class_name={class_name!r} (ids={ids})"
            )

        obj = matches[0]
        fn = next(
            (f for f in list(obj.functions or []) if f.name == function_name), None
        )
        if fn is None:
            available = sorted({f.name for f in list(obj.functions or [])})
            raise ProgramApplyError(
                f"Function not found for class_name={class_name!r} function_name={function_name!r} "
                f"(available={available})"
            )
        return fn.id

    # ------------------------------------------------------------------
    # Directives (program statements)
    # ------------------------------------------------------------------

    def _ensure_opg_index(self) -> None:
        if self._opgs_by_name is not None:
            return
        opgs_by_name: dict[str, OpgRef] = {}
        for opg in program_discovery.build_program_describe_environment_opgs(
            index=self._index
        ):
            name = (getattr(opg, "name", None) or "").strip()
            if not name:
                continue
            projection_hash = (getattr(opg, "projection_hash", None) or "").strip()
            if not projection_hash:
                continue
            opgs_by_name[_lower_key(name)] = OpgRef(
                opg_id=getattr(opg, "id"),
                projection_hash=projection_hash,
            )
        if not opgs_by_name:
            raise ProgramApplyError("Hosted config returned no resolvable OPGs")
        self._opgs_by_name = opgs_by_name

    def _ensure_capability_index(self) -> None:
        if self._objects_by_name is not None:
            return
        objects_by_name: dict[str, list[CapabilityObject]] = {}
        for obj in list(
            program_discovery.build_program_capability_objects(index=self._index)
        ):
            name = (obj.name or "").strip()
            if not name:
                continue
            objects_by_name.setdefault(_lower_key(name), []).append(obj)
        if not objects_by_name:
            raise ProgramApplyError(
                "Hosted config returned no resolvable capability objects"
            )
        self._objects_by_name = objects_by_name

    async def _activate_lane(
        self,
        *,
        branch_id: UUID,
        opg_name: str,
        port_contract: Mapping[str, object] | None = None,
        require_head: bool = False,
        skip_if_head: bool = False,
    ) -> None:
        self._ensure_opg_index()
        assert self._opgs_by_name is not None
        opg_key = _lower_key(opg_name)
        opg = self._opgs_by_name.get(opg_key)
        if opg is None and port_contract is not None:
            alias_candidates = self._resolve_bind_projection_alias_candidates(
                port_contract=port_contract
            )
            if len(alias_candidates) == 1:
                opg_key = alias_candidates[0]
                opg = self._opgs_by_name.get(opg_key)
            elif len(alias_candidates) > 1:
                raise ProgramApplyError(
                    "Ambiguous projection alias in bind contract: "
                    + f"{opg_name!r} (candidates={list(alias_candidates)})"
                )
        if opg is None:
            available = sorted(self._opgs_by_name.keys())
            raise ProgramApplyError(
                f"Unknown projection in bind contract: {opg_name!r} (available={available})"
            )

        self._current_lane_branch_id = branch_id
        self._current_lane_opg = opg
        self._resolved_lane_branch_id = branch_id
        self._resolved_lane_projection_hash = opg.projection_hash

        head = await self._commit_store().head(
            branch_id=branch_id,
            projection_hash=opg.projection_hash,
        )
        head_commit_id = head.get("commit_id") if head else None
        self._current_lane_head_commit_id = (
            UUID(str(head_commit_id)) if head_commit_id else None
        )

        if require_head and self._current_lane_head_commit_id is None:
            raise ProgramApplyError(
                "Required lane HEAD is missing for bind (empty lane). "
                "If this lane is compiler-owned, ensure compilation emitted the seed commit and "
                "the node commit store contains the lane HEAD before applying programs. "
                f"branch_id={branch_id} opg={opg_name!r} projection_hash={opg.projection_hash}"
            )

        self._skip_calls_in_lane = bool(
            skip_if_head and self._current_lane_head_commit_id is not None
        )

    def _seed_compiled_port_contracts(
        self,
        *,
        ports: tuple[PlanPortContract, ...],
    ) -> None:
        for port in ports:
            key = (port.key or "").strip()
            if not key:
                raise ProgramApplyError("Compiled port contract key cannot be empty")
            projection = str(port.projection or "").strip()
            if not projection:
                raise ProgramApplyError(
                    f"Compiled port contract projection is required: {key!r}"
                )

            port_ref = f"program.port.{key}"
            node_contracts: dict[str, dict[str, object]] = {}
            for projection_node in port.projection_nodes:
                node_key = (projection_node.key or "").strip()
                if not node_key:
                    raise ProgramApplyError(
                        f"Compiled port contract node key cannot be empty: {key!r}"
                    )
                node_ref = str(projection_node.node or "").strip()
                if not node_ref:
                    raise ProgramApplyError(
                        f"Compiled port contract node ref is required: {key!r}.{node_key}"
                    )
                node_keys: dict[str, object] = {}
                for node_arg in projection_node.keys:
                    arg_name = (node_arg.name or "").strip()
                    if not arg_name:
                        raise ProgramApplyError(
                            f"Compiled port contract node key name cannot be empty: {key!r}.{node_key}"
                        )
                    node_keys[arg_name] = node_arg.value_expr
                node_contracts[node_key] = {
                    "node": node_ref,
                    "keys": node_keys,
                }
            contract: dict[str, object] = {
                "projection": projection,
                "projection_nodes": node_contracts,
            }
            if port.intent:
                contract["intent"] = str(port.intent).strip()

            self._symbols[port_ref] = contract
            self._symbols[f"{port_ref}.projection"] = projection
            for node_key, node_contract in node_contracts.items():
                node_ref_value = node_contract.get("node")
                if isinstance(node_ref_value, str):
                    self._symbols[f"{port_ref}.node.{node_key}.node"] = node_ref_value
                node_keys_value = node_contract.get("keys")
                if isinstance(node_keys_value, Mapping):
                    for arg_name, arg_expr in node_keys_value.items():
                        self._symbols[f"{port_ref}.node.{node_key}.key.{arg_name}"] = (
                            arg_expr
                        )
            if port.intent:
                self._symbols[f"{port_ref}.intent"] = str(port.intent).strip()

    def _materialize_port_contract(
        self,
        *,
        port_ref: str,
        port_value: object,
    ) -> dict[str, object]:
        if isinstance(port_value, dict):
            return dict(port_value)
        from_symbol = self._symbols.get(port_ref)
        if isinstance(from_symbol, dict):
            return dict(from_symbol)
        return {
            "projection": self._symbols.get(f"{port_ref}.projection"),
        }

    def _resolve_bind_projection_alias_candidates(
        self,
        *,
        port_contract: Mapping[str, object],
    ) -> tuple[str, ...]:
        self._ensure_opg_index()
        assert self._opgs_by_name is not None
        projection_nodes = port_contract.get("projection_nodes")
        if not isinstance(projection_nodes, Mapping):
            return ()
        candidates: set[str] = set()
        for raw_node_contract in projection_nodes.values():
            if not isinstance(raw_node_contract, Mapping):
                continue
            node_ref = str(raw_node_contract.get("node") or "").strip()
            if not node_ref:
                continue
            node_prefix = node_ref.split(".", 1)[0].strip()
            if not node_prefix:
                continue
            normalized = _lower_key(node_prefix)
            if normalized in self._opgs_by_name:
                candidates.add(normalized)
        return tuple(sorted(candidates))

    def _clear_bound_node_alias_symbols(self) -> None:
        if not self._bound_node_aliases:
            return
        for alias in tuple(self._bound_node_aliases):
            self._symbols.pop(alias, None)
        self._bound_node_aliases.clear()

    def _seed_bound_node_alias_symbols(
        self,
        *,
        port_ref: str,
        port_value: object,
    ) -> None:
        contract: Mapping[str, object]
        if isinstance(port_value, Mapping):
            contract = port_value
        else:
            from_symbol = self._symbols.get(port_ref)
            if not isinstance(from_symbol, Mapping):
                self._clear_bound_node_alias_symbols()
                return
            contract = from_symbol

        projection_nodes = contract.get("projection_nodes")
        if not isinstance(projection_nodes, Mapping):
            self._clear_bound_node_alias_symbols()
            return

        self._clear_bound_node_alias_symbols()
        projection_node_ids_by_alias: dict[str, UUID] = {}
        for raw_alias, raw_node_contract in projection_nodes.items():
            node_alias = str(raw_alias or "").strip()
            if not node_alias:
                raise ProgramApplyError(
                    "bind unresolved node alias in port contract; empty projection node key"
                )
            if not isinstance(raw_node_contract, Mapping):
                continue
            raw_keys = raw_node_contract.get("keys")
            if not isinstance(raw_keys, Mapping):
                continue
            class_instance_identity_expr = raw_keys.get("class_instance_identity_id")
            if class_instance_identity_expr is None:
                # Backward-compatible fallback:
                # when the node contract carries a single key argument (the
                # common root-node identity shape), use it as projection-node id.
                key_values = list(raw_keys.values())
                if len(key_values) != 1:
                    continue
                class_instance_identity_expr = key_values[0]
            if isinstance(
                class_instance_identity_expr, (PlanLocalRef, PlanSymbolRef, PlanCall)
            ):
                class_instance_identity_expr = self._eval_expr(
                    class_instance_identity_expr
                )
            elif isinstance(class_instance_identity_expr, str):
                raw_symbol = class_instance_identity_expr.strip()
                if raw_symbol:
                    if raw_symbol in self._locals:
                        class_instance_identity_expr = self._locals[raw_symbol]
                    elif raw_symbol in self._symbols:
                        class_instance_identity_expr = self._symbols[raw_symbol]
                    else:
                        resolved, resolved_value = self._try_eval_symbol_strict(
                            raw_symbol
                        )
                        if resolved:
                            class_instance_identity_expr = resolved_value
            class_instance_identity_id = self._coerce_uuid(
                value=class_instance_identity_expr,
                label=f"bind class_instance_identity_id for node alias {node_alias}",
            )
            self._symbols[node_alias] = class_instance_identity_id
            self._bound_node_aliases.add(node_alias)
            projection_symbol = f"{port_ref}.projection_node.{node_alias}"
            self._symbols[projection_symbol] = class_instance_identity_id
            self._bound_node_aliases.add(projection_symbol)
            projection_node_ids_by_alias[node_alias] = class_instance_identity_id

        if "main" in projection_node_ids_by_alias:
            default_id = projection_node_ids_by_alias["main"]
            default_symbol = f"{port_ref}.projection_node"
            self._symbols[default_symbol] = default_id
            self._bound_node_aliases.add(default_symbol)
        elif len(projection_node_ids_by_alias) == 1:
            default_id = next(iter(projection_node_ids_by_alias.values()))
            default_symbol = f"{port_ref}.projection_node"
            self._symbols[default_symbol] = default_id
            self._bound_node_aliases.add(default_symbol)

    def _resolve_bind_port_contract(
        self,
        *,
        port_ref: str,
        contract: Mapping[str, object],
    ) -> tuple[UUID, str]:
        projection = str(contract.get("projection") or "").strip()
        if not projection:
            raise ProgramApplyError(
                "bind unresolved port contract; expected projection on declared port"
            )

        port_key = ""
        if port_ref.startswith("program.port."):
            port_key = port_ref.removeprefix("program.port.").strip()
        projection_key = projection.replace(".", "_")
        candidate_symbol_names: tuple[str, ...] = (
            f"plan.{projection_key}_branch_id",
            f"plan.{port_key}_branch_id" if port_key else "",
            f"{projection_key}_branch_id",
            f"{port_key}_branch_id" if port_key else "",
            "plan.branch_id",
            "branch_id",
        )
        branch_value: object | None = None
        for symbol_name in candidate_symbol_names:
            if not symbol_name:
                continue
            if symbol_name in self._symbols:
                branch_value = self._symbols[symbol_name]
                break
            resolved, value = self._try_eval_symbol_strict(symbol_name)
            if resolved:
                branch_value = value
                break
        if branch_value is None:
            projection_nodes = contract.get("projection_nodes")
            if isinstance(projection_nodes, Mapping):
                main_contract = projection_nodes.get("main")
                if isinstance(main_contract, Mapping):
                    raw_keys = main_contract.get("keys")
                    if isinstance(raw_keys, Mapping):
                        key_values = list(raw_keys.values())
                        if len(key_values) == 1:
                            branch_value = key_values[0]
                if branch_value is None:
                    inferred_branch_values: list[object] = []
                    for raw_alias, raw_node_contract in projection_nodes.items():
                        node_alias = str(raw_alias or "").strip()
                        if not node_alias or not isinstance(raw_node_contract, Mapping):
                            continue
                        node_ref = str(raw_node_contract.get("node") or "").strip()
                        node_prefix = node_ref.split(".", 1)[0].strip()
                        if _lower_key(node_prefix) != _lower_key(node_alias):
                            continue
                        raw_keys = raw_node_contract.get("keys")
                        if not isinstance(raw_keys, Mapping):
                            continue
                        candidate_value = raw_keys.get("class_instance_identity_id")
                        if candidate_value is None:
                            key_values = list(raw_keys.values())
                            if len(key_values) != 1:
                                continue
                            candidate_value = key_values[0]
                        inferred_branch_values.append(candidate_value)
                    if len(inferred_branch_values) == 1:
                        branch_value = inferred_branch_values[0]
                    elif len(inferred_branch_values) > 1:
                        raise ProgramApplyError(
                            "bind ambiguous branch contract inferred from projection nodes; "
                            + "multiple root candidates matched alias==node-prefix"
                        )
        if branch_value is None:
            raise ProgramApplyError(
                "bind unresolved branch contract; expected one of "
                + ", ".join(name for name in candidate_symbol_names if name)
            )
        if isinstance(branch_value, (PlanLocalRef, PlanSymbolRef, PlanCall)):
            branch_value = self._eval_expr(branch_value)

        branch_id = self._coerce_uuid(
            value=branch_value,
            label=f"bind branch id for projection {projection}",
        )
        return branch_id, projection

    async def _apply_bind_directive(self, call: PlanCall) -> None:
        raw_port = _get_call_arg(call, name="port")
        if raw_port is None:
            raw_port = _get_call_arg(call, name="port_ref")
        if raw_port is None:
            raw_port = _get_call_arg(call, name="program_config_port")
        if raw_port is None:
            raw_port = _get_call_arg(call, name="program_config_port_ref")
        if raw_port is None:
            raise ProgramApplyError(
                "bind requires `port` (aliases: `port_ref`, `program_config_port`, `program_config_port_ref`)"
            )

        raw_view_key = _get_call_arg(call, name="view_key")
        if raw_view_key is None:
            raw_view_key = _get_call_arg(call, name="view")
        if raw_view_key is None:
            raise ProgramApplyError("bind requires `view_key` (alias: `view`)")
        view_key = str(self._eval_expr(raw_view_key)).strip()
        if not view_key:
            raise ProgramApplyError("bind view_key cannot be empty")

        raw_is_active = _get_call_arg(call, name="is_active", default=True)
        is_active = self._eval_expr(raw_is_active)
        if not isinstance(is_active, bool):
            raise ProgramApplyError("bind is_active must be a boolean")

        self._symbols["plan.current_view_key"] = view_key
        if not is_active:
            self._clear_bound_node_alias_symbols()
            self._current_lane_branch_id = None
            self._current_lane_opg = None
            self._current_lane_head_commit_id = None
            self._skip_calls_in_lane = False
            self._resolved_lane_branch_id = None
            self._resolved_lane_projection_hash = None
            return

        port_value = self._eval_expr(raw_port)
        port_ref = ""
        if isinstance(raw_port, PlanSymbolRef):
            port_ref = (raw_port.name or "").strip()
        elif isinstance(port_value, str):
            port_ref = port_value.strip()
        if not port_ref:
            raise ProgramApplyError(
                "bind port must be provided as a symbolic reference (for example `program.port.main`)"
            )

        port_contract = self._materialize_port_contract(
            port_ref=port_ref,
            port_value=port_value,
        )
        branch_id, opg_name = self._resolve_bind_port_contract(
            port_ref=port_ref,
            contract=port_contract,
        )
        raw_require_head = _get_call_arg(call, name="require_head", default=False)
        raw_skip_if_head = _get_call_arg(call, name="skip_if_head", default=False)
        require_head = bool(self._eval_expr(raw_require_head))
        skip_if_head = bool(self._eval_expr(raw_skip_if_head))
        await self._activate_lane(
            branch_id=branch_id,
            opg_name=opg_name,
            port_contract=port_contract,
            require_head=require_head,
            skip_if_head=skip_if_head,
        )
        self._symbols["plan.current_port_ref"] = port_ref
        self._seed_bound_node_alias_symbols(
            port_ref=port_ref,
            port_value=port_contract,
        )

    @staticmethod
    def _coerce_uuid(*, value: object, label: str) -> UUID:
        if isinstance(value, UUID):
            return value
        try:
            return UUID(str(value))
        except Exception as exc:  # noqa: BLE001
            raise ProgramApplyError(
                f"{label} must resolve to UUID, got {value!r}"
            ) from exc

    def _apply_input_contract(self, step: PlanInput) -> None:
        resolved, value = self._try_eval_input_source(step.source)
        if not resolved:
            if step.default is not None:
                value = self._eval_expr(step.default)
                resolved = True
            elif step.required:
                raise ProgramApplyError(f"Required input unresolved: {step.name!r}")
        if not resolved:
            return
        self._locals[step.name] = value
        self._symbols[step.name] = value

    def _apply_expect_contract(self, step: PlanExpectEventConfig) -> None:
        raw_ref = self._eval_expr(step.ref)
        event_config_id = self._coerce_uuid(
            value=raw_ref,
            label="expect event_config ref",
        )
        previous_required = self._event_expectations.get(event_config_id, False)
        self._event_expectations[event_config_id] = previous_required or bool(
            step.required
        )

    def _intent_symbol(self, *, step_index: int, suffix: str) -> object | None:
        scoped_key = f"plan.intent.{step_index}.{suffix}"
        if scoped_key in self._symbols:
            return self._symbols[scoped_key]
        generic_key = f"plan.{suffix}"
        return self._symbols.get(generic_key)

    def _resolve_program_intent_record(
        self,
        *,
        action_config_id: UUID,
        event_config_id: UUID,
        step_index: int,
    ) -> ProgramIntentRecord:
        raw_turn_instruction_id = self._intent_symbol(
            step_index=step_index,
            suffix="program_turn_instruction_id",
        )
        program_turn_instruction_id = coerce_uuid_or_none(raw_turn_instruction_id)
        if program_turn_instruction_id is None:
            raise ProgramApplyError(
                "program intent recording requires "
                f"plan.intent.{step_index}.program_turn_instruction_id"
            )

        raw_instruction_intent_id = self._intent_symbol(
            step_index=step_index,
            suffix="program_impl_instruction_intent_id",
        )
        program_impl_instruction_intent_id = coerce_uuid_or_none(
            raw_instruction_intent_id
        )
        if program_impl_instruction_intent_id is None:
            raise ProgramApplyError(
                "program intent recording requires "
                f"plan.intent.{step_index}.program_impl_instruction_intent_id"
            )

        raw_intent_key = self._intent_symbol(
            step_index=step_index,
            suffix="intent_key",
        )
        intent_key = str(raw_intent_key or "").strip()
        if not intent_key:
            intent_key = (
                f"program_turn_instruction:{program_turn_instruction_id}:"
                f"intent:{program_impl_instruction_intent_id}"
            )

        raw_event_id = self._intent_symbol(step_index=step_index, suffix="event_id")
        event_id = coerce_uuid_or_none(raw_event_id)

        return ProgramIntentRecord(
            event_id=event_id,
            action_config_id=action_config_id,
            event_config_id=event_config_id,
            intent_key=intent_key,
            step_index=step_index,
            program_turn_instruction_id=program_turn_instruction_id,
            program_impl_instruction_intent_id=program_impl_instruction_intent_id,
        )

    async def _apply_intent_contract(
        self,
        step: PlanIntentActionConfig,
        *,
        step_index: int,
        validate_only: bool,
    ) -> None:
        action_raw = self._eval_expr(step.action_ref)
        event_raw = self._eval_expr(step.event_ref)
        action_config_id = self._coerce_uuid(
            value=action_raw,
            label="intent action_config ref",
        )
        event_config_id = self._coerce_uuid(
            value=event_raw,
            label="intent event_config ref",
        )
        self._action_intents.append((action_config_id, event_config_id))
        if validate_only or self._intent_recorder is None:
            return

        record = self._resolve_program_intent_record(
            action_config_id=action_config_id,
            event_config_id=event_config_id,
            step_index=step_index,
        )
        await self._intent_recorder.record_program_intent(record)

    async def _validate_contracts(self) -> None:
        if not self._event_expectations and not self._action_intents:
            return
        if self._contract_validator is None:
            raise ProgramApplyError(
                "Program contract validation unavailable for input/expect/intent steps"
            )
        await self._contract_validator.validate_event_action_contracts(
            event_expectations=self._event_expectations,
            action_intents=self._action_intents,
        )

    async def _apply_program_ref_directive(
        self,
        call: PlanCall,
        *,
        validate_only: bool,
        results: list[dict[str, object]],
    ) -> None:
        raw_program_ref = _get_call_arg(call, name="program_ref")
        if raw_program_ref is None:
            raise ProgramApplyError("plan.apply_program_ref requires program_ref")

        target_ref = str(self._eval_expr(raw_program_ref)).strip()
        if not target_ref:
            raise ProgramApplyError("plan.apply_program_ref program_ref is empty")

        if target_ref in self._program_ref_stack:
            chain = " -> ".join([*self._program_ref_stack, target_ref])
            raise ProgramApplyError(
                "Cycle detected in plan.apply_program_ref chain: " f"{chain}"
            )

        target_ref = _normalize_program_ref(raw=target_ref)

        nested_symbols: dict[str, object] = {}
        raw_symbols = _get_call_arg(call, name="symbols", default=None)
        if raw_symbols is not None:
            evaluated = self._eval_expr(raw_symbols)
            if not isinstance(evaluated, dict):
                raise ProgramApplyError(
                    "plan.apply_program_ref symbols must evaluate to an object/map"
                )
            nested_symbols = {
                str(k): v for k, v in dict(evaluated).items() if str(k).strip()
            }

        nested_plan_symbol = nested_symbols.get("plan.invocation_plan_artifact")
        if nested_plan_symbol is None:
            raise ProgramApplyError(
                "plan.apply_program_ref requires symbols.plan.invocation_plan_artifact"
            )
        try:
            nested_plan = load_invocation_plan_from_symbol_payload(
                symbol_value=nested_plan_symbol,
                program_ref=target_ref,
                symbol_name="plan.apply_program_ref.symbols.plan.invocation_plan_artifact",
            )
        except ProgramRegistryError as exc:
            raise ProgramApplyError(str(exc)) from exc
        validate_required_symbols(
            required_symbols=required_symbols_from_invocation_plan(plan=nested_plan),
            provided_symbols=nested_symbols,
            actor_id=self._actor_id,
            environment_id=self._environment_id,
            process_id=self._process_id,
            thread_id=self._thread_id,
            program_ref=target_ref,
            context="plan.apply_program_ref",
        )

        raw_validate_only = _get_call_arg(call, name="validate_only", default=None)
        nested_validate_only = validate_only
        if raw_validate_only is not None:
            nested_validate_only = bool(self._eval_expr(raw_validate_only))

        nested_executor = RuntimeInvocationPlanExecutor(
            invoker=self._invoker,
            index=self._index,
            actor_id=self._actor_id,
            environment_id=self._environment_id,
            process_id=self._process_id,
            thread_id=self._thread_id,
            commit=self._commit,
            publish=self._publish,
            symbols=nested_symbols,
            program_ref_stack=(*self._program_ref_stack, target_ref),
            contract_validator=self._contract_validator,
            intent_recorder=self._intent_recorder,
            store=self._store,
        )
        nested_results = await nested_executor.execute(
            nested_plan,
            symbols=nested_symbols,
            validate_only=nested_validate_only,
        )
        results.append(
            {
                "target": "plan.apply_program_ref",
                "program_ref": target_ref,
                "skipped": False,
                "validate_only": nested_validate_only,
                "results": nested_results,
            }
        )

    # ------------------------------------------------------------------
    # Capability resolution + invocation
    # ------------------------------------------------------------------

    def _resolve_function_descriptor(
        self, *, owner: str, fn_name: str
    ) -> CapabilityFunction:
        self._ensure_capability_index()
        assert self._objects_by_name is not None

        object_name = (owner or "").strip().split(".")[-1]
        object_key = _lower_key(object_name)
        matches = list(self._objects_by_name.get(object_key, []))
        if not matches:
            available = sorted(self._objects_by_name.keys())
            raise ProgramApplyError(
                f"Unknown capability object: {object_name!r} (available={available})"
            )
        if len(matches) > 1:
            ids = sorted(str(obj.id) for obj in matches)
            raise ProgramApplyError(
                f"Ambiguous capability object: {object_name!r} (ids={ids})"
            )
        obj = matches[0]
        fn = next(
            (f for f in list(obj.functions or []) if f.name == fn_name),
            None,
        )
        if fn is None:
            available = sorted({f.name for f in list(obj.functions or [])})
            raise ProgramApplyError(
                f"Function not found on {object_name}: {fn_name!r} (available={available})"
            )
        return fn

    async def _invoke_call(
        self,
        call: PlanCall,
        *,
        validate_only: bool,
        results: list[dict[str, object]],
    ) -> None:
        if self._skip_calls_in_lane:
            results.append(
                {
                    "target": call.target,
                    "skipped": True,
                    "reason": "skip_if_head",
                }
            )
            return
        if self._current_lane_branch_id is None or self._current_lane_opg is None:
            raise ProgramApplyError("Invocation requires an active lane (bind)")

        owner, fn_name = _split_call_target(call.target)
        fn = self._resolve_function_descriptor(owner=owner, fn_name=fn_name)
        args, kwargs = self._eval_call_args(call)

        is_constructor = fn.is_constructor
        if is_constructor and self._current_lane_head_commit_id is not None:
            results.append(
                {
                    "target": call.target,
                    "skipped": True,
                    "reason": "constructor_lane_has_head",
                }
            )
            return

        if is_constructor:
            if call.object_expr is not None:
                raise ProgramApplyError(
                    f"Constructor call must not include inline object selector: {call.target}"
                )
            req = InvokeFunctionRequest(
                actor_id=self._actor_id,
                environment_id=self._environment_id,
                process_id=self._process_id,
                thread_id=self._thread_id,
                branch_id=self._current_lane_branch_id,
                projection_hash=self._current_lane_opg.projection_hash,
                call_target=InvokeFunctionCallTarget.opg_constructor,
                object_id=None,
                object_projection_graph_id=self._current_lane_opg.opg_id,
                function_id=fn.id,
                args=_coerce_json_array(list(args)),
                kwargs=_coerce_json_object(dict(kwargs)),
                commit=self._commit,
                publish=self._publish,
            )
        else:
            if call.object_expr is None:
                raise ProgramApplyError(
                    f"Instance call requires inline object selector `call <object_id> {call.target}(...)`"
                )
            object_value = self._eval_expr(call.object_expr)
            object_id = self._coerce_uuid(
                value=object_value,
                label=f"inline object selector for {call.target}",
            )
            req = InvokeFunctionRequest(
                actor_id=self._actor_id,
                environment_id=self._environment_id,
                process_id=self._process_id,
                thread_id=self._thread_id,
                branch_id=self._current_lane_branch_id,
                projection_hash=self._current_lane_opg.projection_hash,
                call_target=InvokeFunctionCallTarget.instance,
                object_id=object_id,
                object_projection_graph_id=None,
                function_id=fn.id,
                args=_coerce_json_array(list(args)),
                kwargs=_coerce_json_object(dict(kwargs)),
                commit=self._commit,
                publish=self._publish,
            )

        result_entry: dict[str, object] = {
            "target": call.target,
            "skipped": False,
            "branch_id": str(self._current_lane_branch_id),
            "projection_hash": self._current_lane_opg.projection_hash,
            "function_id": str(fn.id),
            "call_target": req.call_target.value,
        }
        results.append(result_entry)

        if validate_only:
            return

        resp = await self._invoker.invoke_function(req)
        if getattr(resp, "status", None) != "succeeded":
            raise ProgramApplyError(
                getattr(resp, "error", None) or "invoke_function failed"
            )
        invoke_perf = parse_invoke_perf_logs(getattr(resp, "logs", None))
        if invoke_perf:
            result_entry["invoke_perf"] = invoke_perf
        try:
            execution_time_ms = int(getattr(resp, "execution_time_ms", 0) or 0)
        except Exception:  # noqa: BLE001
            execution_time_ms = 0
        if execution_time_ms > 0:
            result_entry["execution_time_ms"] = execution_time_ms

    # ------------------------------------------------------------------
    # Plan execution
    # ------------------------------------------------------------------

    def _reset_program_state(self) -> None:
        self._symbols = dict(self._base_symbols)
        self._locals.clear()
        self._current_lane_branch_id = None
        self._current_lane_opg = None
        self._current_lane_head_commit_id = None
        self._skip_calls_in_lane = False
        self._resolved_lane_branch_id = None
        self._resolved_lane_projection_hash = None
        self._event_expectations.clear()
        self._action_intents.clear()
        self._bound_node_aliases.clear()

    def resolved_lane(self) -> tuple[UUID, str] | None:
        if (
            self._resolved_lane_branch_id is None
            or self._resolved_lane_projection_hash is None
        ):
            return None
        return self._resolved_lane_branch_id, self._resolved_lane_projection_hash

    async def execute(
        self,
        plan: InvocationPlan,
        *,
        symbols: dict[str, object] | None = None,
        validate_only: bool = False,
    ) -> list[dict[str, object]]:
        self._reset_program_state()
        if symbols:
            self._symbols.update(symbols)
        self._seed_compiled_port_contracts(ports=plan.ports)

        results: list[dict[str, object]] = []
        for step_index, step in enumerate(plan.steps):
            if isinstance(step, PlanInput):
                self._apply_input_contract(step)
                continue

            if isinstance(step, PlanLet):
                value = self._eval_expr(step.value)
                self._locals[step.name] = value
                self._symbols[step.name] = value
                continue

            if isinstance(step, PlanExpectEventConfig):
                self._apply_expect_contract(step)
                continue

            if isinstance(step, PlanIntentActionConfig):
                await self._apply_intent_contract(
                    step,
                    step_index=step_index,
                    validate_only=validate_only,
                )
                continue

            if isinstance(step, PlanInvoke):
                if step.call.target == "bind":
                    await self._apply_bind_directive(step.call)
                    continue
                if step.call.target == "plan.apply_program_ref":
                    await self._apply_program_ref_directive(
                        step.call,
                        validate_only=validate_only,
                        results=results,
                    )
                    continue

                await self._invoke_call(
                    step.call, validate_only=validate_only, results=results
                )
                continue

            raise ProgramApplyError(f"Unsupported plan step: {type(step).__name__}")

        await self._validate_contracts()
        return results


def compile_program_by_ref(*, src: str, program_name: str) -> InvocationPlan:
    plans = compile_invocation_plans(src)
    if not plans:
        raise ProgramApplyError("No program declarations found in source")
    matches = [p for p in plans if p.name == program_name]
    if not matches:
        available = sorted({p.name for p in plans})
        raise ProgramApplyError(
            f"Program not found in source: {program_name!r} (available={available})"
        )
    if len(matches) > 1:
        raise ProgramApplyError(f"Ambiguous program name: {program_name!r}")
    return matches[0]


def _normalize_program_ref(*, raw: str) -> str:
    text = (raw or "").strip()
    if not text or ":" not in text:
        raise ProgramApplyError(
            "Invalid program ref "
            f"{text!r}; expected '<program_ref_namespace>:<program_name>'"
        )
    namespace, name = text.split(":", 1)
    namespace = namespace.strip()
    name = name.strip()
    if not namespace or not name:
        raise ProgramApplyError(
            "Invalid program ref "
            f"{text!r}; expected '<program_ref_namespace>:<program_name>'"
        )
    return f"{namespace}:{name}"


def load_invocation_plan_from_symbol_payload(
    *,
    symbol_value: object,
    program_ref: str,
    symbol_name: str = "plan.invocation_plan_artifact",
) -> InvocationPlan:
    payload: object = symbol_value
    if isinstance(payload, bytes):
        try:
            payload = payload.decode("utf-8")
        except Exception as exc:  # noqa: BLE001
            raise ProgramRegistryError(
                "Invalid invocation plan symbol payload bytes "
                f"(ref={program_ref!r} symbol={symbol_name!r})"
            ) from exc
    if isinstance(payload, str):
        text = payload.strip()
        if not text:
            raise ProgramRegistryError(
                "Empty invocation plan symbol payload "
                f"(ref={program_ref!r} symbol={symbol_name!r})"
            )
        try:
            payload = json.loads(text)
        except Exception as exc:  # noqa: BLE001
            raise ProgramRegistryError(
                "Invalid invocation plan symbol payload JSON "
                f"(ref={program_ref!r} symbol={symbol_name!r})"
            ) from exc

    if not isinstance(payload, Mapping):
        raise ProgramRegistryError(
            "Invocation plan symbol payload must be an object "
            f"(ref={program_ref!r} symbol={symbol_name!r})"
        )
    try:
        return decode_invocation_plan_artifact(dict(payload))
    except Exception as exc:  # noqa: BLE001
        raise ProgramRegistryError(
            "Invalid invocation plan symbol payload "
            f"(ref={program_ref!r} symbol={symbol_name!r})"
        ) from exc


__all__ = [
    "ProgramApplyError",
    "ProgramContractValidator",
    "ProgramIntentRecord",
    "ProgramIntentRecorder",
    "ProgramRegistryError",
    "RuntimeInvocationPlanExecutor",
    "compile_program_by_ref",
    "load_invocation_plan_from_symbol_payload",
    "required_symbols_from_invocation_plan",
    "resolve_bundle_root_from_manifest_path",
    "validate_required_symbols",
    "_resolve_bundle_root_from_manifest_path",
]
