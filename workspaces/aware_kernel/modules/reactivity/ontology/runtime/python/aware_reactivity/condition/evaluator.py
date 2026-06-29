from __future__ import annotations

import asyncio
import json
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol, cast
from uuid import UUID

# Comms
from aware_meta.receipts.notifications import LaneCommitReceiptNotification

# Meta Ontology
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
    AttributeTypeDescriptorRole,
)
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.attribute.attribute import Attribute
from aware_meta_ontology.attribute.attribute_value import AttributeValue

# Meta Runtime
from aware_meta.graph.instance.builder import build_object_instance_graph_empty
from aware_meta.graph.instance.commit.fs_store import FSCommitStore, FSSnapshotStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex

# Reactivity API-owned DTOs
from aware_reactivity_service_dto.reactivity.event_action_binding import (
    EventActionBinding,
)
from aware_reactivity_service_dto.reactivity.event_condition_binding_resolution import (
    EventConditionBindingResolution,
)

# Utils
from aware_utils.logging import logger

_EVENT_CONDITION_BINDING_MODEL_READY = False


class _ConditionRuntimeInvoker(Protocol):
    async def ensure_index(self) -> None: ...

    def get_index(self) -> MetaGraphRuntimeIndex: ...


def _build_function_call_invoker(
    *,
    manifest_path: str | None,
) -> _ConditionRuntimeInvoker:
    _ = manifest_path
    raise RuntimeError(
        "LaneMaterializedConditionEvaluator requires an explicit Meta runtime "
        "invoker or index. The deprecated FunctionCallInvoker fallback has "
        "been removed from Reactivity."
    )


def _ensure_binding_resolution_model_ready() -> None:
    global _EVENT_CONDITION_BINDING_MODEL_READY
    if _EVENT_CONDITION_BINDING_MODEL_READY:
        return
    EventConditionBindingResolution.model_rebuild(
        _types_namespace={"EventActionBinding": EventActionBinding},
        force=True,
    )
    _EVENT_CONDITION_BINDING_MODEL_READY = True


def _resolve_projection_by_name(
    *,
    index: MetaGraphRuntimeIndex,
    projection_name: str,
) -> ObjectProjectionGraph | None:
    wanted = projection_name.strip()
    return next(
        (
            opg
            for opg in index.ocg.object_projection_graphs
            if (opg.name or "").strip() == wanted
        ),
        None,
    )


def _as_uuid(raw: object | None) -> UUID | None:
    if raw is None:
        return None
    if isinstance(raw, UUID):
        return raw
    text = str(raw).strip()
    if not text:
        return None
    try:
        return UUID(text)
    except Exception:
        return None


def _as_bool(raw: object | None, *, default: bool) -> bool:
    if raw is None:
        return default
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)):
        return bool(raw)
    text = str(raw).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _as_int(raw: object | None) -> int | None:
    if raw is None:
        return None
    if isinstance(raw, bool):
        return int(raw)
    if isinstance(raw, int):
        return raw
    try:
        return int(str(raw).strip())
    except Exception:
        return None


def _parse_jsonish(raw: object | None) -> object | None:
    if raw is None:
        return None
    if not isinstance(raw, str):
        return raw
    text = raw.strip()
    if not text:
        return ""
    try:
        return json.loads(text)
    except Exception:
        return raw


def _to_decimal(value: object | None) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        if value != value:  # nan
            return None
        return Decimal(str(value))
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return Decimal(text)
        except (InvalidOperation, ValueError):
            return None
    return None


def _coerced_equal(lhs: object | None, rhs: object | None) -> bool:
    ldec = _to_decimal(lhs)
    rdec = _to_decimal(rhs)
    if ldec is not None and rdec is not None:
        return ldec == rdec
    return lhs == rhs


def _compare(lhs: object | None, rhs: object | None) -> int | None:
    ldec = _to_decimal(lhs)
    rdec = _to_decimal(rhs)
    if ldec is not None and rdec is not None:
        if ldec < rdec:
            return -1
        if ldec > rdec:
            return 1
        return 0

    if lhs is None or rhs is None:
        return None

    try:
        lhs_cmp = cast(Any, lhs)
        rhs_cmp = cast(Any, rhs)
        if lhs_cmp < rhs_cmp:
            return -1
        if lhs_cmp > rhs_cmp:
            return 1
        return 0
    except Exception:
        lhs_s = str(lhs)
        rhs_s = str(rhs)
        if lhs_s < rhs_s:
            return -1
        if lhs_s > rhs_s:
            return 1
        return 0


def _iter_values(raw: object | None) -> list[object]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return list(raw)
    if isinstance(raw, tuple):
        return list(raw)
    if isinstance(raw, set):
        return list(raw)
    return [raw]


def _nonempty_text(raw: object | None) -> str | None:
    if raw is None:
        return None
    text = str(raw)
    if not text.strip():
        return None
    return text


def _contains(*, haystack: object | None, needle: object | None) -> bool:
    if haystack is None or needle is None:
        return False
    if isinstance(haystack, str):
        needle_text = _nonempty_text(needle)
        return needle_text is not None and needle_text in haystack
    if isinstance(haystack, dict):
        return needle in haystack or str(needle) in haystack
    if isinstance(haystack, (list, tuple, set)):
        return needle in haystack
    return False


def _evaluate_operator(
    *,
    operator: str,
    pre_value: object | None,
    post_value: object | None,
    pre_exists: bool,
    post_exists: bool,
    changed: bool,
    expected: object | None = None,
    range_min: object | None = None,
    range_max: object | None = None,
) -> bool:
    op = (operator or "").strip().lower()
    if op in {"create", "created"}:
        return (not pre_exists) and post_exists
    if op == "changed":
        return changed
    if op == "not_changed":
        return not changed
    if op == "exists":
        return post_exists
    if op == "not_exists":
        return not post_exists
    if op == "is_null":
        return post_value is None
    if op == "is_not_null":
        return post_value is not None

    if op == "contains":
        return _contains(haystack=post_value, needle=expected)
    if op == "not_contains":
        if expected is None or (
            isinstance(post_value, str) and _nonempty_text(expected) is None
        ):
            return False
        return not _contains(haystack=post_value, needle=expected)

    if op == "starts_with":
        expected_text = _nonempty_text(expected)
        return expected_text is not None and str(post_value or "").startswith(
            expected_text
        )
    if op == "ends_with":
        expected_text = _nonempty_text(expected)
        return expected_text is not None and str(post_value or "").endswith(
            expected_text
        )
    if op == "matches_regex":
        expected_text = _nonempty_text(expected)
        if expected_text is None:
            return False
        try:
            return re.search(expected_text, str(post_value or "")) is not None
        except re.error:
            return False

    if op == "in":
        expected_values = _iter_values(expected)
        return bool(expected_values) and post_value in expected_values
    if op == "not_in":
        expected_values = _iter_values(expected)
        return bool(expected_values) and post_value not in expected_values

    if op == "increased":
        cmp = _compare(post_value, pre_value)
        return cmp is not None and cmp > 0 and pre_exists and post_exists
    if op == "decreased":
        cmp = _compare(post_value, pre_value)
        return cmp is not None and cmp < 0 and pre_exists and post_exists

    if (
        op
        in {
            "equals",
            "not_equals",
            "greater_than",
            "greater_or_equal",
            "less_than",
            "less_or_equal",
        }
        and expected is None
    ):
        return False

    if op == "equals":
        result = _coerced_equal(post_value, expected)
    elif op == "not_equals":
        result = not _coerced_equal(post_value, expected)
    elif op == "greater_than":
        cmp = _compare(post_value, expected)
        result = cmp is not None and cmp > 0
    elif op == "greater_or_equal":
        cmp = _compare(post_value, expected)
        result = cmp is not None and cmp >= 0
    elif op == "less_than":
        cmp = _compare(post_value, expected)
        result = cmp is not None and cmp < 0
    elif op == "less_or_equal":
        cmp = _compare(post_value, expected)
        result = cmp is not None and cmp <= 0
    else:
        return False

    if not result:
        return False

    post_num = _to_decimal(post_value)
    if post_num is None:
        return result

    min_num = _to_decimal(range_min)
    if min_num is not None and post_num < min_num:
        return False
    max_num = _to_decimal(range_max)
    if max_num is not None and post_num > max_num:
        return False
    return True


@dataclass(frozen=True, slots=True)
class _PrimitivePolicy:
    primitive_value: object | None
    range_min: object | None
    range_max: object | None


@dataclass(frozen=True, slots=True)
class _EnumPolicy:
    option_values: tuple[str, ...]
    match_mode: str


@dataclass(frozen=True, slots=True)
class _RelationshipPolicy:
    class_config_relationship_id: UUID
    eval_mode: str
    count_threshold: int | None
    nested_condition_config_id: UUID | None


@dataclass(frozen=True, slots=True)
class _AttributePolicy:
    id: UUID
    attribute_config_id: UUID
    operator: str
    negate: bool
    primitive: _PrimitivePolicy | None
    enum: _EnumPolicy | None
    relationship: _RelationshipPolicy | None


@dataclass(frozen=True, slots=True)
class _ClassPolicy:
    id: UUID
    class_config_id: UUID
    class_selection: str
    class_logic: str
    require_existence: bool
    attributes: tuple[_AttributePolicy, ...]


@dataclass(frozen=True, slots=True)
class _ConditionPolicy:
    id: UUID
    is_enabled: bool
    logic_strategy: str
    classes: tuple[_ClassPolicy, ...]


@dataclass(slots=True)
class _GraphState:
    class_instances_by_id: dict[UUID, ClassInstance]
    class_instance_ids_by_class_config: dict[UUID, set[UUID]]
    attribute_by_id: dict[UUID, Attribute]
    attribute_id_by_instance_and_config: dict[tuple[UUID, UUID], UUID]
    value_by_instance_and_config: dict[tuple[UUID, UUID], object]
    relationships_by_source_and_config: dict[tuple[UUID, UUID], list[UUID]]


@dataclass(slots=True)
class _CommitChangeSet:
    class_instance_ids: set[UUID]
    changed_attribute_ids: set[UUID]
    changed_instance_attr_configs: set[tuple[UUID, UUID]]
    changed_relationship_keys: set[tuple[UUID, UUID]]


@dataclass(slots=True)
class _ReceiptContext:
    pre: _GraphState
    post: _GraphState
    changes: _CommitChangeSet
    trigger_candidate_instance_ids: set[UUID]


@dataclass(frozen=True, slots=True)
class ConditionEvaluationTraceEntry:
    kind: str
    path: str
    result: bool
    reason: str
    metadata: dict[str, object]


@dataclass(frozen=True, slots=True)
class ConditionEvaluationTrace:
    result: bool
    entries: tuple[ConditionEvaluationTraceEntry, ...]


def _trace_entry(
    entries: list[ConditionEvaluationTraceEntry],
    *,
    kind: str,
    path: str,
    result: bool,
    reason: str,
    metadata: dict[str, object] | None = None,
) -> None:
    entries.append(
        ConditionEvaluationTraceEntry(
            kind=kind,
            path=path,
            result=result,
            reason=reason,
            metadata=metadata or {},
        )
    )


class LaneMaterializedConditionEvaluator:
    """Canonical condition evaluator over lane receipts + materialized policy graphs."""

    def __init__(
        self,
        *,
        manifest_path: str | None = None,
        event_projection_name: str = "EventConfig",
        condition_projection_name: str = "ConditionConfig",
        event_projection_hash_override: str | None = None,
        condition_projection_hash_override: str | None = None,
        refresh_seconds: float = 1.0,
        invoker: _ConditionRuntimeInvoker | None = None,
        commits: FSCommitStore | None = None,
        snapshots: FSSnapshotStore | None = None,
    ) -> None:
        _ensure_binding_resolution_model_ready()
        self._invoker = invoker or _build_function_call_invoker(
            manifest_path=manifest_path
        )
        self._event_projection_name = event_projection_name.strip() or "EventConfig"
        self._condition_projection_name = (
            condition_projection_name.strip() or "ConditionConfig"
        )
        self._event_projection_hash_override = (
            event_projection_hash_override.strip()
            if event_projection_hash_override
            else None
        )
        self._condition_projection_hash_override = (
            condition_projection_hash_override.strip()
            if condition_projection_hash_override
            else None
        )
        self._refresh_seconds = max(float(refresh_seconds), 0.0)

        self._commits = commits or FSCommitStore()
        self._snapshots = snapshots or FSSnapshotStore()
        self._materializer = OIGMaterializer(
            commits=self._commits,
            snaps=self._snapshots,
        )

        self._event_projection_hash: str | None = None
        self._condition_projection_hash: str | None = None

        self._bindings_by_id: dict[UUID, EventConditionBindingResolution] = {}
        self._condition_policies_by_id: dict[UUID, _ConditionPolicy] = {}

        self._descendants_by_class_config: dict[UUID, set[UUID]] = {}
        self._attribute_name_by_id: dict[UUID, str] = {}
        self._class_name_by_id: dict[UUID, str] = {}
        self._enum_option_value_by_id: dict[UUID, str] = {}

        self._last_loaded_unix_s: float = 0.0
        self._load_lock = asyncio.Lock()
        self._init_error_logged = False

    async def evaluate(
        self,
        *,
        receipt: LaneCommitReceiptNotification,
        event_config_condition_config_id: UUID,
    ) -> bool:
        trace = await self.evaluate_with_trace(
            receipt=receipt,
            event_config_condition_config_id=event_config_condition_config_id,
        )
        return trace.result

    async def evaluate_with_trace(
        self,
        *,
        receipt: LaneCommitReceiptNotification,
        event_config_condition_config_id: UUID,
    ) -> ConditionEvaluationTrace:
        entries: list[ConditionEvaluationTraceEntry] = []
        force_refresh = False
        trigger_projection_hash = (receipt.projection_hash or "").strip()
        if trigger_projection_hash and (
            trigger_projection_hash == self._event_projection_hash
            or trigger_projection_hash == self._condition_projection_hash
        ):
            force_refresh = True

        try:
            await self._ensure_loaded(force_refresh=force_refresh)
        except Exception as exc:
            if not self._init_error_logged:
                logger.warning(
                    "[reactivity-bridge] canonical ConditionConfig evaluator unavailable: %s",
                    exc,
                )
                self._init_error_logged = True
            _trace_entry(
                entries,
                kind="evaluator",
                path="evaluator",
                result=False,
                reason="policy_load_failed",
                metadata={"error": str(exc)},
            )
            return ConditionEvaluationTrace(result=False, entries=tuple(entries))

        binding = self._bindings_by_id.get(event_config_condition_config_id)
        if binding is None:
            logger.warning(
                "[reactivity-bridge] event condition binding not found: %s",
                event_config_condition_config_id,
            )
            _trace_entry(
                entries,
                kind="binding",
                path=f"binding:{event_config_condition_config_id}",
                result=False,
                reason="binding_missing",
            )
            return ConditionEvaluationTrace(result=False, entries=tuple(entries))
        if not binding.is_enabled:
            _trace_entry(
                entries,
                kind="binding",
                path=f"binding:{binding.id}",
                result=False,
                reason="binding_disabled",
                metadata={"condition_config_id": str(binding.condition_config_id)},
            )
            return ConditionEvaluationTrace(result=False, entries=tuple(entries))

        try:
            ctx = await self._build_receipt_context(receipt=receipt)
            result = self._evaluate_condition_policy_trace(
                condition_config_id=binding.condition_config_id,
                ctx=ctx,
                allowed_instance_ids=None,
                visited=set(),
                entries=entries,
                path=f"binding:{binding.id}",
            )
            _trace_entry(
                entries,
                kind="binding",
                path=f"binding:{binding.id}",
                result=result,
                reason="binding_evaluated",
                metadata={
                    "condition_config_id": str(binding.condition_config_id),
                    "trigger_candidate_instance_ids": sorted(
                        str(item) for item in ctx.trigger_candidate_instance_ids
                    ),
                },
            )
            return ConditionEvaluationTrace(result=result, entries=tuple(entries))
        except Exception as exc:
            if binding.continue_on_fail:
                logger.warning(
                    "[reactivity-bridge] condition evaluation failed but continue_on_fail=1 "
                    "(binding=%s): %s",
                    binding.id,
                    exc,
                )
                _trace_entry(
                    entries,
                    kind="binding",
                    path=f"binding:{binding.id}",
                    result=True,
                    reason="evaluation_failed_continue_on_fail",
                    metadata={"error": str(exc)},
                )
                return ConditionEvaluationTrace(result=True, entries=tuple(entries))
            logger.warning(
                "[reactivity-bridge] condition evaluation failed (binding=%s): %s",
                binding.id,
                exc,
            )
            _trace_entry(
                entries,
                kind="binding",
                path=f"binding:{binding.id}",
                result=False,
                reason="evaluation_failed",
                metadata={"error": str(exc)},
            )
            return ConditionEvaluationTrace(result=False, entries=tuple(entries))

    async def resolve_binding(
        self, *, event_config_condition_config_id: UUID
    ) -> EventConditionBindingResolution | None:
        try:
            await self._ensure_loaded(force_refresh=False)
        except Exception as exc:
            if not self._init_error_logged:
                logger.warning(
                    "[reactivity-bridge] canonical ConditionConfig binding resolution unavailable: %s",
                    exc,
                )
                self._init_error_logged = True
            return None
        return self._bindings_by_id.get(event_config_condition_config_id)

    async def resolve_bindings_for_class_config_ids(
        self,
        *,
        class_config_ids: set[UUID],
        include_disabled: bool = False,
        force_refresh: bool = False,
    ) -> list[EventConditionBindingResolution]:
        """
        Resolve EventConfigConditionConfig bindings whose ConditionConfig targets at
        least one provided ClassConfig id.

        Contract:
        - Deterministic policy lookup over materialized event/condition lanes.
        - `class_selection` semantics are respected (`specific_class` vs `base_class`).
        - Disabled bindings/policies are filtered unless `include_disabled=True`.
        """

        if not class_config_ids:
            return []

        try:
            await self._ensure_loaded(force_refresh=force_refresh)
        except Exception as exc:
            if not self._init_error_logged:
                logger.warning(
                    "[reactivity-bridge] class-config binding resolution unavailable: %s",
                    exc,
                )
                self._init_error_logged = True
            return []

        out: list[EventConditionBindingResolution] = []
        for binding in self._bindings_by_id.values():
            if not include_disabled and not binding.is_enabled:
                continue
            policy = self._condition_policies_by_id.get(binding.condition_config_id)
            if policy is None:
                continue
            if not include_disabled and not policy.is_enabled:
                continue
            if self._condition_policy_targets_class_configs(
                policy=policy,
                class_config_ids=class_config_ids,
            ):
                out.append(binding)

        out.sort(key=lambda item: str(item.id))
        return out

    async def resolve_bindings_for_event_config_ids(
        self,
        *,
        event_config_ids: set[UUID],
        include_disabled: bool = False,
        force_refresh: bool = False,
    ) -> dict[UUID, list[EventConditionBindingResolution]]:
        """
        Resolve EventConfigConditionConfig bindings grouped by EventConfig id.

        Contract:
        - Deterministic policy lookup over materialized event/condition lanes.
        - Disabled bindings/policies are filtered unless `include_disabled=True`.
        """

        if not event_config_ids:
            return {}

        try:
            await self._ensure_loaded(force_refresh=force_refresh)
        except Exception as exc:
            if not self._init_error_logged:
                logger.warning(
                    "[reactivity-bridge] event-config binding resolution unavailable: %s",
                    exc,
                )
                self._init_error_logged = True
            return {}

        out: dict[UUID, list[EventConditionBindingResolution]] = defaultdict(list)
        for binding in self._bindings_by_id.values():
            if binding.event_config_id not in event_config_ids:
                continue
            if not include_disabled and not binding.is_enabled:
                continue
            policy = self._condition_policies_by_id.get(binding.condition_config_id)
            if policy is None:
                continue
            if not include_disabled and not policy.is_enabled:
                continue
            out[binding.event_config_id].append(binding)

        for event_config_id in list(out.keys()):
            out[event_config_id] = sorted(
                out[event_config_id],
                key=lambda item: str(item.id),
            )
        return dict(out)

    async def _ensure_loaded(self, *, force_refresh: bool) -> None:
        now = time.time()
        if (
            not force_refresh
            and self._bindings_by_id
            and self._condition_policies_by_id
            and (now - self._last_loaded_unix_s) < self._refresh_seconds
        ):
            return

        async with self._load_lock:
            now = time.time()
            if (
                not force_refresh
                and self._bindings_by_id
                and self._condition_policies_by_id
                and (now - self._last_loaded_unix_s) < self._refresh_seconds
            ):
                return
            await self._load()
            self._last_loaded_unix_s = now
            self._init_error_logged = False

    async def _load(self) -> None:
        await self._invoker.ensure_index()
        index = self._invoker.get_index()

        event_opg, condition_opg = self._resolve_projections(index=index)
        self._event_projection_hash = event_opg.projection_hash
        self._condition_projection_hash = condition_opg.projection_hash

        self._class_name_by_id = {
            cc.id: (cc.name or "").strip() for cc in index.class_configs_by_id.values()
        }
        self._attribute_name_by_id = {}
        for cc in index.class_configs_by_id.values():
            for link in cc.class_config_attribute_configs:
                if link.attribute_config is None:
                    continue
                self._attribute_name_by_id[link.attribute_config.id] = (
                    link.attribute_config.name
                )

        self._descendants_by_class_config = self._build_descendants_map(index=index)
        self._enum_option_value_by_id = self._build_enum_option_value_map(index=index)

        action_type_by_action_config_id: dict[UUID, str] = {}
        action_opg = _resolve_projection_by_name(
            index=index,
            projection_name="ActionConfig",
        )
        if action_opg is not None:
            action_type_by_action_config_id = (
                await self._load_action_type_by_action_config_id(
                    index=index,
                    action_opg=action_opg,
                )
            )

        self._bindings_by_id = await self._load_bindings(
            index=index,
            event_opg=event_opg,
            action_type_by_action_config_id=action_type_by_action_config_id,
        )
        self._condition_policies_by_id = await self._load_condition_policies(
            index=index,
            condition_opg=condition_opg,
        )

    def _resolve_projections(
        self, *, index: MetaGraphRuntimeIndex
    ) -> tuple[ObjectProjectionGraph, ObjectProjectionGraph]:
        if self._event_projection_hash_override:
            event_opg = index.opg_by_hash.get(self._event_projection_hash_override)
            if event_opg is None:
                raise RuntimeError(
                    "Configured event projection hash not found: "
                    f"{self._event_projection_hash_override}"
                )
        else:
            event_opg = _resolve_projection_by_name(
                index=index, projection_name=self._event_projection_name
            )
            if event_opg is None:
                available = sorted(
                    {
                        (opg.name or "").strip()
                        for opg in index.ocg.object_projection_graphs
                    }
                )
                raise RuntimeError(
                    "Event projection not found: "
                    f"{self._event_projection_name!r} available={available}"
                )

        if self._condition_projection_hash_override:
            condition_opg = index.opg_by_hash.get(
                self._condition_projection_hash_override
            )
            if condition_opg is None:
                raise RuntimeError(
                    "Configured condition projection hash not found: "
                    f"{self._condition_projection_hash_override}"
                )
        else:
            condition_opg = _resolve_projection_by_name(
                index=index, projection_name=self._condition_projection_name
            )
            if condition_opg is None:
                available = sorted(
                    {
                        (opg.name or "").strip()
                        for opg in index.ocg.object_projection_graphs
                    }
                )
                raise RuntimeError(
                    "Condition projection not found: "
                    f"{self._condition_projection_name!r} available={available}"
                )

        return event_opg, condition_opg

    @staticmethod
    def _build_descendants_map(
        *, index: MetaGraphRuntimeIndex
    ) -> dict[UUID, set[UUID]]:
        children: dict[UUID, set[UUID]] = defaultdict(set)
        class_ids: set[UUID] = set()
        for cc in index.class_configs_by_id.values():
            class_ids.add(cc.id)
            if cc.parent_class_id is not None:
                children[cc.parent_class_id].add(cc.id)

        descendants: dict[UUID, set[UUID]] = {}
        for class_id in class_ids:
            out = {class_id}
            queue = list(children.get(class_id, set()))
            while queue:
                child = queue.pop(0)
                if child in out:
                    continue
                out.add(child)
                queue.extend(children.get(child, set()))
            descendants[class_id] = out
        return descendants

    def _condition_policy_targets_class_configs(
        self,
        *,
        policy: _ConditionPolicy,
        class_config_ids: set[UUID],
    ) -> bool:
        for class_policy in policy.classes:
            mode = (class_policy.class_selection or "").strip().lower()
            if mode == "specific_class":
                if class_policy.class_config_id in class_config_ids:
                    return True
                continue

            descendants = self._descendants_by_class_config.get(
                class_policy.class_config_id,
                {class_policy.class_config_id},
            )
            if descendants & class_config_ids:
                return True
        return False

    @staticmethod
    def _build_enum_option_value_map(
        *, index: MetaGraphRuntimeIndex
    ) -> dict[UUID, str]:
        out: dict[UUID, str] = {}
        for node in index.ocg.object_config_graph_nodes:
            enum_cfg = node.enum_config
            if enum_cfg is None:
                continue
            for option in enum_cfg.enum_options:
                if option.id is None:
                    continue
                out[option.id] = option.value
        return out

    async def _load_action_type_by_action_config_id(
        self,
        *,
        index: MetaGraphRuntimeIndex,
        action_opg: ObjectProjectionGraph,
    ) -> dict[UUID, str]:
        action_config_class_id = self._resolve_projection_class_config_id(
            index=index,
            opg=action_opg,
            class_name="ActionConfig",
        )
        out: dict[UUID, str] = {}
        async for branch_id, head in self._commits.iter_lane_heads_by_projection(
            projection_hash=action_opg.projection_hash
        ):
            commit_id_raw = head.get("commit_id")
            commit_id = _as_uuid(commit_id_raw)
            if commit_id is None:
                continue
            try:
                oig, _ = await self._materializer.get(
                    branch_id=branch_id,
                    ocg=index.ocg,
                    opg=action_opg,
                    commit_id=commit_id,
                    class_configs_by_id=index.class_configs_by_id,
                    attribute_configs_by_id=index.attribute_configs_by_id,
                )
            except Exception as exc:
                logger.warning(
                    "[reactivity-bridge] failed materializing action_config lane "
                    "(branch_id=%s projection_hash=%s commit_id=%s): %s",
                    branch_id,
                    action_opg.projection_hash,
                    commit_id,
                    exc,
                )
                continue

            for ci in oig.class_instances:
                if ci.class_config_id != action_config_class_id or ci.id is None:
                    continue
                attrs = self._decode_class_instance_attributes(ci)
                action_type = str(attrs.get("action_type") or "").strip()
                if action_type:
                    out[ci.id] = action_type
        return out

    async def _load_bindings(
        self,
        *,
        index: MetaGraphRuntimeIndex,
        event_opg: ObjectProjectionGraph,
        action_type_by_action_config_id: dict[UUID, str] | None = None,
    ) -> dict[UUID, EventConditionBindingResolution]:
        event_condition_class_id = self._resolve_projection_class_config_id(
            index=index,
            opg=event_opg,
            class_name="EventConfigConditionConfig",
        )
        event_config_class_id = self._resolve_projection_class_config_id(
            index=index,
            opg=event_opg,
            class_name="EventConfig",
        )
        event_action_class_id = self._resolve_projection_class_config_id(
            index=index,
            opg=event_opg,
            class_name="EventConfigActionConfig",
        )
        out: dict[UUID, EventConditionBindingResolution] = {}
        action_type_map = action_type_by_action_config_id or {}

        async for branch_id, head in self._commits.iter_lane_heads_by_projection(
            projection_hash=event_opg.projection_hash
        ):
            commit_id_raw = head.get("commit_id")
            commit_id = _as_uuid(commit_id_raw)
            if commit_id is None:
                continue

            try:
                oig, _ = await self._materializer.get(
                    branch_id=branch_id,
                    ocg=index.ocg,
                    opg=event_opg,
                    commit_id=commit_id,
                    class_configs_by_id=index.class_configs_by_id,
                    attribute_configs_by_id=index.attribute_configs_by_id,
                )
            except Exception as exc:
                logger.warning(
                    "[reactivity-bridge] failed materializing event_config lane "
                    "(branch_id=%s projection_hash=%s commit_id=%s): %s",
                    branch_id,
                    event_opg.projection_hash,
                    commit_id,
                    exc,
                )
                continue

            class_instance_by_id = {
                ci.id: ci for ci in oig.class_instances if ci.id is not None
            }
            parent_event_config_by_condition_id: dict[UUID, UUID] = {}
            parent_event_config_by_action_id: dict[UUID, UUID] = {}
            relationships = oig.class_instance_relationships
            for rel in relationships:
                source_id = rel.source_class_instance_id
                target_id = rel.target_class_instance_id
                source_ci = class_instance_by_id.get(source_id)
                target_ci = class_instance_by_id.get(target_id)
                if source_ci is None or target_ci is None:
                    continue
                if source_ci.class_config_id != event_config_class_id:
                    continue
                if target_ci.class_config_id == event_condition_class_id:
                    parent_event_config_by_condition_id[target_id] = source_id
                elif target_ci.class_config_id == event_action_class_id:
                    parent_event_config_by_action_id[target_id] = source_id

            action_bindings_by_event_config_id: dict[UUID, list[EventActionBinding]] = (
                defaultdict(list)
            )
            for ci in oig.class_instances:
                if ci.class_config_id != event_action_class_id or ci.id is None:
                    continue
                attrs = self._decode_class_instance_attributes(ci)
                event_config_id = _as_uuid(
                    attrs.get("event_config_id") or attrs.get("event_config")
                )
                if event_config_id is None:
                    event_config_id = parent_event_config_by_action_id.get(ci.id)
                action_config_id = _as_uuid(
                    attrs.get("action_config_id") or attrs.get("action_config")
                )
                if event_config_id is None or action_config_id is None:
                    continue
                action_type = str(attrs.get("action_type") or "").strip() or None
                if action_type is None:
                    action_type = action_type_map.get(action_config_id)
                action_bindings_by_event_config_id[event_config_id].append(
                    EventActionBinding(
                        id=ci.id,
                        action_config_id=action_config_id,
                        action_type=action_type,
                        execution_order=_as_int(attrs.get("execution_order")) or 0,
                        priority=_as_int(attrs.get("priority")) or 0,
                        is_enabled=_as_bool(attrs.get("is_enabled"), default=True),
                        is_required=_as_bool(attrs.get("is_required"), default=False),
                        continue_on_fail=_as_bool(
                            attrs.get("continue_on_fail"),
                            default=True,
                        ),
                    )
                )

            sorted_actions_by_event_config_id: dict[UUID, list[EventActionBinding]] = {}
            for (
                event_config_id,
                action_bindings,
            ) in action_bindings_by_event_config_id.items():
                sorted_actions_by_event_config_id[event_config_id] = list(
                    sorted(
                        action_bindings,
                        key=lambda item: (
                            item.execution_order,
                            -item.priority,
                            str(item.id),
                        ),
                    )
                )

            for ci in oig.class_instances:
                if ci.class_config_id != event_condition_class_id or ci.id is None:
                    continue
                attrs = self._decode_class_instance_attributes(ci)
                event_config_id = _as_uuid(
                    attrs.get("event_config_id") or attrs.get("event_config")
                )
                if event_config_id is None:
                    event_config_id = parent_event_config_by_condition_id.get(ci.id)
                condition_config_id = _as_uuid(
                    attrs.get("condition_config_id") or attrs.get("condition_config")
                )
                if event_config_id is None or condition_config_id is None:
                    continue

                candidate = EventConditionBindingResolution(
                    id=ci.id,
                    event_config_id=event_config_id,
                    condition_config_id=condition_config_id,
                    is_enabled=_as_bool(attrs.get("is_enabled"), default=True),
                    continue_on_fail=_as_bool(
                        attrs.get("continue_on_fail"),
                        default=True,
                    ),
                    is_required=_as_bool(attrs.get("is_required"), default=False),
                    action_bindings=sorted_actions_by_event_config_id.get(
                        event_config_id,
                        [],
                    ),
                )
                existing = out.get(candidate.id)
                if existing is None:
                    out[candidate.id] = candidate
                    continue
                if existing != candidate:
                    logger.warning(
                        "[reactivity-bridge] duplicate EventConfigConditionConfig id with conflicting payload: %s",
                        candidate.id,
                    )
        return out

    async def _load_condition_policies(
        self,
        *,
        index: MetaGraphRuntimeIndex,
        condition_opg: ObjectProjectionGraph,
    ) -> dict[UUID, _ConditionPolicy]:
        class_ids = {
            "ConditionConfig": self._resolve_projection_class_config_id(
                index=index,
                opg=condition_opg,
                class_name="ConditionConfig",
            ),
            "ConditionConfigClassConfig": self._resolve_projection_class_config_id(
                index=index,
                opg=condition_opg,
                class_name="ConditionConfigClassConfig",
            ),
            "ConditionConfigAttributeConfig": self._resolve_projection_class_config_id(
                index=index,
                opg=condition_opg,
                class_name="ConditionConfigAttributeConfig",
            ),
            "ConditionConfigPrimitiveConfig": self._resolve_projection_class_config_id(
                index=index,
                opg=condition_opg,
                class_name="ConditionConfigPrimitiveConfig",
            ),
            "ConditionConfigEnumConfig": self._resolve_projection_class_config_id(
                index=index,
                opg=condition_opg,
                class_name="ConditionConfigEnumConfig",
            ),
            "ConditionConfigEnumOption": self._resolve_projection_class_config_id(
                index=index,
                opg=condition_opg,
                class_name="ConditionConfigEnumOption",
            ),
            "ConditionConfigRelationshipConfig": self._resolve_projection_class_config_id(
                index=index,
                opg=condition_opg,
                class_name="ConditionConfigRelationshipConfig",
            ),
        }

        out: dict[UUID, _ConditionPolicy] = {}
        async for branch_id, head in self._commits.iter_lane_heads_by_projection(
            projection_hash=condition_opg.projection_hash
        ):
            commit_id = _as_uuid(head.get("commit_id"))
            if commit_id is None:
                continue

            try:
                oig, _ = await self._materializer.get(
                    branch_id=branch_id,
                    ocg=index.ocg,
                    opg=condition_opg,
                    commit_id=commit_id,
                    class_configs_by_id=index.class_configs_by_id,
                    attribute_configs_by_id=index.attribute_configs_by_id,
                )
            except Exception as exc:
                logger.warning(
                    "[reactivity-bridge] failed materializing condition_config lane "
                    "(branch_id=%s projection_hash=%s commit_id=%s): %s",
                    branch_id,
                    condition_opg.projection_hash,
                    commit_id,
                    exc,
                )
                continue

            lane_policies = self._build_condition_policies_from_oig(
                class_ids=class_ids,
                oig=oig,
            )
            for condition_id, policy in lane_policies.items():
                existing = out.get(condition_id)
                if existing is None:
                    out[condition_id] = policy
                    continue
                if existing != policy:
                    logger.warning(
                        "[reactivity-bridge] duplicate ConditionConfig id with conflicting payload: %s",
                        condition_id,
                    )
        return out

    @staticmethod
    def _resolve_projection_class_config_id(
        *,
        index: MetaGraphRuntimeIndex,
        opg: ObjectProjectionGraph,
        class_name: str,
    ) -> UUID:
        candidates: list[UUID] = []
        for node in opg.object_projection_graph_nodes:
            cc = index.class_configs_by_id.get(node.class_config_id)
            if cc is None:
                continue
            if (cc.name or "").strip() == class_name:
                candidates.append(cc.id)
        if len(candidates) != 1:
            raise RuntimeError(
                f"projection={opg.name!r} expected one class {class_name!r}, found {len(candidates)}"
            )
        return candidates[0]

    def _build_condition_policies_from_oig(
        self,
        *,
        class_ids: dict[str, UUID],
        oig,  # noqa: ANN001
    ) -> dict[UUID, _ConditionPolicy]:
        roots: dict[UUID, dict[str, object]] = {}
        class_nodes: dict[UUID, dict[str, object]] = {}
        attribute_nodes: dict[UUID, dict[str, object]] = {}
        primitive_nodes: dict[UUID, dict[str, object]] = {}
        enum_nodes: dict[UUID, dict[str, object]] = {}
        enum_option_nodes: dict[UUID, dict[str, object]] = {}
        relationship_nodes: dict[UUID, dict[str, object]] = {}
        class_config_id_by_instance_id: dict[UUID, UUID] = {}

        for ci in oig.class_instances:
            if ci.id is None:
                continue
            class_config_id_by_instance_id[ci.id] = ci.class_config_id
            attrs = self._decode_class_instance_attributes(ci)
            if ci.class_config_id == class_ids["ConditionConfig"]:
                roots[ci.id] = attrs
            elif ci.class_config_id == class_ids["ConditionConfigClassConfig"]:
                class_nodes[ci.id] = attrs
            elif ci.class_config_id == class_ids["ConditionConfigAttributeConfig"]:
                attribute_nodes[ci.id] = attrs
            elif ci.class_config_id == class_ids["ConditionConfigPrimitiveConfig"]:
                primitive_nodes[ci.id] = attrs
            elif ci.class_config_id == class_ids["ConditionConfigEnumConfig"]:
                enum_nodes[ci.id] = attrs
            elif ci.class_config_id == class_ids["ConditionConfigEnumOption"]:
                enum_option_nodes[ci.id] = attrs
            elif ci.class_config_id == class_ids["ConditionConfigRelationshipConfig"]:
                relationship_nodes[ci.id] = attrs

        # Canonical structural reconstruction is edge-driven.
        class_ids_by_condition_id: dict[UUID, list[UUID]] = defaultdict(list)
        attr_ids_by_class_node_id: dict[UUID, list[UUID]] = defaultdict(list)
        primitive_by_attr_node_id: dict[UUID, UUID] = {}
        enum_by_attr_node_id: dict[UUID, UUID] = {}
        relationship_by_attr_node_id: dict[UUID, UUID] = {}
        option_node_ids_by_enum_node_id: dict[UUID, list[UUID]] = defaultdict(list)
        nested_condition_by_relationship_node_id: dict[UUID, UUID] = {}

        rel_items = sorted(
            oig.class_instance_relationships,
            key=lambda rel: (
                str(rel.source_class_instance_id),
                str(rel.target_class_instance_id),
                str(rel.class_config_relationship_id),
            ),
        )
        for rel in rel_items:
            src_id = rel.source_class_instance_id
            tgt_id = rel.target_class_instance_id
            src_cc_id = class_config_id_by_instance_id.get(src_id)
            tgt_cc_id = class_config_id_by_instance_id.get(tgt_id)
            if src_cc_id is None or tgt_cc_id is None:
                continue

            if (
                src_cc_id == class_ids["ConditionConfig"]
                and tgt_cc_id == class_ids["ConditionConfigClassConfig"]
            ):
                class_ids_by_condition_id[src_id].append(tgt_id)
                continue
            if (
                src_cc_id == class_ids["ConditionConfigClassConfig"]
                and tgt_cc_id == class_ids["ConditionConfigAttributeConfig"]
            ):
                attr_ids_by_class_node_id[src_id].append(tgt_id)
                continue
            if (
                src_cc_id == class_ids["ConditionConfigAttributeConfig"]
                and tgt_cc_id == class_ids["ConditionConfigPrimitiveConfig"]
            ):
                primitive_by_attr_node_id[src_id] = tgt_id
                continue
            if (
                src_cc_id == class_ids["ConditionConfigAttributeConfig"]
                and tgt_cc_id == class_ids["ConditionConfigEnumConfig"]
            ):
                enum_by_attr_node_id[src_id] = tgt_id
                continue
            if (
                src_cc_id == class_ids["ConditionConfigAttributeConfig"]
                and tgt_cc_id == class_ids["ConditionConfigRelationshipConfig"]
            ):
                relationship_by_attr_node_id[src_id] = tgt_id
                continue
            if (
                src_cc_id == class_ids["ConditionConfigEnumConfig"]
                and tgt_cc_id == class_ids["ConditionConfigEnumOption"]
            ):
                option_node_ids_by_enum_node_id[src_id].append(tgt_id)
                continue
            if (
                src_cc_id == class_ids["ConditionConfigRelationshipConfig"]
                and tgt_cc_id == class_ids["ConditionConfig"]
            ):
                nested_condition_by_relationship_node_id[src_id] = tgt_id
                continue

        option_ids_by_enum_node_id: dict[UUID, list[UUID]] = defaultdict(list)
        for enum_node_id, option_node_ids in option_node_ids_by_enum_node_id.items():
            for option_node_id in option_node_ids:
                option_attrs = enum_option_nodes.get(option_node_id)
                if option_attrs is None:
                    continue
                enum_option_id = _as_uuid(option_attrs.get("enum_option_id"))
                if enum_option_id is None:
                    continue
                option_ids_by_enum_node_id[enum_node_id].append(enum_option_id)

        out: dict[UUID, _ConditionPolicy] = {}
        for condition_id, root_attrs in roots.items():
            class_policies: list[_ClassPolicy] = []
            for class_node_id in sorted(
                class_ids_by_condition_id.get(condition_id, []),
                key=str,
            ):
                class_attrs = class_nodes.get(class_node_id)
                if class_attrs is None:
                    continue
                class_config_id = _as_uuid(class_attrs.get("class_config_id"))
                if class_config_id is None:
                    continue

                attribute_policies: list[_AttributePolicy] = []
                for attr_node_id in sorted(
                    attr_ids_by_class_node_id.get(class_node_id, []),
                    key=str,
                ):
                    attr_attrs = attribute_nodes.get(attr_node_id)
                    if attr_attrs is None:
                        continue
                    attribute_config_id = _as_uuid(
                        attr_attrs.get("attribute_config_id")
                    )
                    if attribute_config_id is None:
                        continue

                    primitive_policy: _PrimitivePolicy | None = None
                    primitive_node_id = primitive_by_attr_node_id.get(attr_node_id)
                    if primitive_node_id is not None:
                        primitive_attrs = primitive_nodes.get(primitive_node_id, {})
                        primitive_policy = _PrimitivePolicy(
                            primitive_value=_parse_jsonish(
                                primitive_attrs.get("primitive_value")
                            ),
                            range_min=_parse_jsonish(primitive_attrs.get("range_min")),
                            range_max=_parse_jsonish(primitive_attrs.get("range_max")),
                        )

                    enum_policy: _EnumPolicy | None = None
                    enum_node_id = enum_by_attr_node_id.get(attr_node_id)
                    if enum_node_id is not None:
                        enum_attrs = enum_nodes.get(enum_node_id, {})
                        option_values: list[str] = []
                        for enum_option_id in option_ids_by_enum_node_id.get(
                            enum_node_id, []
                        ):
                            option_values.append(
                                self._enum_option_value_by_id.get(
                                    enum_option_id,
                                    str(enum_option_id),
                                )
                            )
                        enum_policy = _EnumPolicy(
                            option_values=tuple(sorted(set(option_values))),
                            match_mode=str(enum_attrs.get("match_mode") or "any_of"),
                        )

                    relationship_policy: _RelationshipPolicy | None = None
                    relationship_node_id = relationship_by_attr_node_id.get(
                        attr_node_id
                    )
                    if relationship_node_id is not None:
                        rel_attrs = relationship_nodes.get(relationship_node_id, {})
                        class_config_relationship_id = _as_uuid(
                            rel_attrs.get("class_config_relationship_id")
                        )
                        if class_config_relationship_id is not None:
                            relationship_policy = _RelationshipPolicy(
                                class_config_relationship_id=class_config_relationship_id,
                                eval_mode=str(rel_attrs.get("eval_mode") or "exists"),
                                count_threshold=_as_int(
                                    rel_attrs.get("count_threshold")
                                ),
                                nested_condition_config_id=nested_condition_by_relationship_node_id.get(
                                    relationship_node_id
                                ),
                            )

                    attribute_policies.append(
                        _AttributePolicy(
                            id=attr_node_id,
                            attribute_config_id=attribute_config_id,
                            operator=str(attr_attrs.get("operator") or "equals"),
                            negate=_as_bool(attr_attrs.get("negate"), default=False),
                            primitive=primitive_policy,
                            enum=enum_policy,
                            relationship=relationship_policy,
                        )
                    )

                class_policies.append(
                    _ClassPolicy(
                        id=class_node_id,
                        class_config_id=class_config_id,
                        class_selection=str(
                            class_attrs.get("class_selection") or "base_class"
                        ),
                        class_logic=str(class_attrs.get("class_logic") or "all"),
                        require_existence=_as_bool(
                            class_attrs.get("require_existence"),
                            default=True,
                        ),
                        attributes=tuple(
                            sorted(attribute_policies, key=lambda item: str(item.id))
                        ),
                    )
                )

            out[condition_id] = _ConditionPolicy(
                id=condition_id,
                is_enabled=_as_bool(root_attrs.get("is_enabled"), default=True),
                logic_strategy=str(root_attrs.get("logic_strategy") or "all"),
                classes=tuple(sorted(class_policies, key=lambda item: str(item.id))),
            )

        return out

    def _decode_class_instance_attributes(self, ci: ClassInstance) -> dict[str, object]:
        attrs: dict[str, object] = {}
        for attr in ci.attributes:
            name = self._attribute_name_by_id.get(attr.attribute_config_id)
            if not name:
                continue
            attrs[name] = self._decode_attribute_value(attr.value_root)
        return attrs

    def _decode_attribute_value(self, value_root: AttributeValue | None) -> object:
        if value_root is None:
            return None

        kind = value_root.type_descriptor.kind
        if kind == AttributeTypeDescriptorKind.primitive:
            raw = value_root.primitive_value
            if isinstance(raw, dict) and "value" in raw:
                return raw["value"]
            return raw
        if kind == AttributeTypeDescriptorKind.enum:
            if value_root.enum_option is not None:
                return value_root.enum_option.value
            enum_option_id = _as_uuid(getattr(value_root, "enum_option_id", None))
            if enum_option_id is not None:
                mapped = self._enum_option_value_by_id.get(enum_option_id)
                if mapped is not None:
                    return mapped
            return None
        if kind == AttributeTypeDescriptorKind.class_:
            if (
                value_root.class_instance is not None
                and value_root.class_instance.id is not None
            ):
                return str(value_root.class_instance.id)
            return (
                str(value_root.class_instance_id)
                if value_root.class_instance_id
                else None
            )
        if kind == AttributeTypeDescriptorKind.collection:
            links = sorted(
                value_root.child_links,
                key=lambda link: (
                    link.position if link.position is not None else 10**9,
                    link.identity_key or "",
                ),
            )
            return [self._decode_attribute_value(link.child) for link in links]
        if kind == AttributeTypeDescriptorKind.tuple:
            links = sorted(
                value_root.child_links,
                key=lambda link: (
                    link.position if link.position is not None else 10**9,
                    link.identity_key or "",
                ),
            )
            return [self._decode_attribute_value(link.child) for link in links]
        if kind == AttributeTypeDescriptorKind.mapping:
            key_by_identity: dict[str, object] = {}
            val_by_identity: dict[str, object] = {}
            for link in value_root.child_links:
                identity = str(link.identity_key or "")
                decoded = self._decode_attribute_value(link.child)
                if link.role == AttributeTypeDescriptorRole.key:
                    key_by_identity[identity] = decoded
                elif link.role == AttributeTypeDescriptorRole.value_:
                    val_by_identity[identity] = decoded
            out: dict[str, object] = {}
            for identity, key_val in key_by_identity.items():
                key = str(key_val)
                out[key] = val_by_identity.get(identity)
            return out
        if kind == AttributeTypeDescriptorKind.union:
            if not value_root.child_links:
                return None
            child = sorted(
                value_root.child_links,
                key=lambda link: (
                    link.position if link.position is not None else 10**9,
                    link.identity_key or "",
                ),
            )[0]
            return self._decode_attribute_value(child.child)
        return None

    async def _build_receipt_context(
        self,
        *,
        receipt: LaneCommitReceiptNotification,
    ) -> _ReceiptContext:
        if receipt.branch_id is None:
            raise ValueError("receipt.branch_id is required")
        projection_hash = (receipt.projection_hash or "").strip()
        if not projection_hash:
            raise ValueError("receipt.projection_hash is required")
        if receipt.commit_id is None:
            raise ValueError("receipt.commit_id is required")

        await self._invoker.ensure_index()
        index = self._invoker.get_index()
        opg = index.opg_by_hash.get(projection_hash)
        if opg is None:
            raise ValueError(
                f"projection_hash not found in runtime index: {projection_hash}"
            )

        commit = await self._commits.get_commit(
            branch_id=receipt.branch_id,
            projection_hash=projection_hash,
            commit_id=receipt.commit_id,
        )
        if commit is None:
            raise ValueError(
                "commit not found for receipt lane "
                f"(branch_id={receipt.branch_id}, projection_hash={projection_hash}, commit_id={receipt.commit_id})"
            )

        parent_commit_id: UUID | None = None
        if commit.commit is not None and commit.commit.commit_parents:
            parent_commit_id = commit.commit.commit_parents[0].parent_commit_id

        post_oig, _ = await self._materializer.get(
            branch_id=receipt.branch_id,
            ocg=index.ocg,
            opg=opg,
            commit_id=receipt.commit_id,
            class_configs_by_id=index.class_configs_by_id,
            attribute_configs_by_id=index.attribute_configs_by_id,
        )

        if parent_commit_id is not None:
            pre_oig, _ = await self._materializer.get(
                branch_id=receipt.branch_id,
                ocg=index.ocg,
                opg=opg,
                commit_id=parent_commit_id,
                class_configs_by_id=index.class_configs_by_id,
                attribute_configs_by_id=index.attribute_configs_by_id,
            )
        else:
            pre_oig = build_object_instance_graph_empty(
                name="EMPTY",
                description="EMPTY",
                object_config_graph=index.ocg,
                object_projection_graph=opg,
                oig_id=post_oig.id,
            )

        pre_state = self._build_graph_state(pre_oig)
        post_state = self._build_graph_state(post_oig)
        change_set = self._build_change_set(
            commit=commit,
            pre=pre_state,
            post=post_state,
        )
        trigger_candidate_instance_ids = self._trigger_candidate_instance_ids(
            receipt_root_object_id=receipt.root_object_id,
            pre=pre_state,
            post=post_state,
            changes=change_set,
        )
        return _ReceiptContext(
            pre=pre_state,
            post=post_state,
            changes=change_set,
            trigger_candidate_instance_ids=trigger_candidate_instance_ids,
        )

    def _build_graph_state(
        self, oig: ObjectInstanceGraph
    ) -> _GraphState:  # noqa: ANN001
        class_instances_by_id: dict[UUID, ClassInstance] = {}
        class_instance_ids_by_class_config: dict[UUID, set[UUID]] = defaultdict(set)
        attribute_by_id: dict[UUID, Attribute] = {}
        attribute_id_by_instance_and_config: dict[tuple[UUID, UUID], UUID] = {}
        value_by_instance_and_config: dict[tuple[UUID, UUID], object] = {}
        relationships_by_source_and_config: dict[tuple[UUID, UUID], list[UUID]] = (
            defaultdict(list)
        )

        for ci in oig.class_instances:
            if ci.id is None:
                continue
            class_instances_by_id[ci.id] = ci
            class_instance_ids_by_class_config[ci.class_config_id].add(ci.id)

            for attr in ci.attributes:
                if attr.id is None:
                    continue
                key = (ci.id, attr.attribute_config_id)
                attribute_by_id[attr.id] = attr
                attribute_id_by_instance_and_config[key] = attr.id
                value_by_instance_and_config[key] = self._decode_attribute_value(
                    attr.value_root
                )

        for rel in oig.class_instance_relationships:
            key = (rel.source_class_instance_id, rel.class_config_relationship_id)
            relationships_by_source_and_config[key].append(rel.target_class_instance_id)

        for key in list(relationships_by_source_and_config.keys()):
            relationships_by_source_and_config[key] = sorted(
                set(relationships_by_source_and_config[key]),
                key=str,
            )

        return _GraphState(
            class_instances_by_id=class_instances_by_id,
            class_instance_ids_by_class_config=dict(class_instance_ids_by_class_config),
            attribute_by_id=attribute_by_id,
            attribute_id_by_instance_and_config=attribute_id_by_instance_and_config,
            value_by_instance_and_config=value_by_instance_and_config,
            relationships_by_source_and_config=dict(relationships_by_source_and_config),
        )

    @staticmethod
    def _build_change_set(
        *,
        commit,
        pre: _GraphState,
        post: _GraphState,
    ) -> _CommitChangeSet:
        changed_class_instance_ids: set[UUID] = set()
        changed_attribute_ids: set[UUID] = set()
        changed_relationship_keys: set[tuple[UUID, UUID]] = set()

        for graph_change in commit.object_instance_graph_changes:
            for class_change in graph_change.class_instance_changes:
                changed_class_instance_ids.add(class_change.class_instance_id)
                for attr_change in class_change.attribute_changes:
                    changed_attribute_ids.add(attr_change.attribute_id)
            for rel_change in graph_change.class_instance_relationship_changes:
                changed_relationship_keys.add(
                    (
                        rel_change.source_class_instance_id,
                        rel_change.class_config_relationship_id,
                    )
                )

        changed_instance_attr_configs: set[tuple[UUID, UUID]] = set()
        for attr_id in changed_attribute_ids:
            attr = post.attribute_by_id.get(attr_id) or pre.attribute_by_id.get(attr_id)
            if attr is None:
                continue
            key = (attr.class_instance_id, attr.attribute_config_id)
            changed_instance_attr_configs.add(key)

        # Class create/delete/update implicitly impacts all known attributes on that
        # instance id for the commit evaluation window.
        for class_instance_id in changed_class_instance_ids:
            for graph in (pre, post):
                for key in graph.attribute_id_by_instance_and_config:
                    if key[0] == class_instance_id:
                        changed_instance_attr_configs.add(key)

        return _CommitChangeSet(
            class_instance_ids=changed_class_instance_ids,
            changed_attribute_ids=changed_attribute_ids,
            changed_instance_attr_configs=changed_instance_attr_configs,
            changed_relationship_keys=changed_relationship_keys,
        )

    @staticmethod
    def _trigger_candidate_instance_ids(
        *,
        receipt_root_object_id: UUID | None,
        pre: _GraphState,
        post: _GraphState,
        changes: _CommitChangeSet,
    ) -> set[UUID]:
        """
        Default top-level condition scope for a lane receipt.

        Static predicates must not scan every post-state instance. Until a
        first-class/global condition scope exists, top-level evaluation is tied
        to the receipt root object, changed instances, and changed relationship
        endpoints. Nested relationship policies pass their target ids explicitly.
        """

        known_instance_ids = set(pre.class_instances_by_id) | set(
            post.class_instances_by_id
        )
        candidates: set[UUID] = set(changes.class_instance_ids)
        if receipt_root_object_id is not None:
            candidates.add(receipt_root_object_id)
        candidates.update(
            instance_id for instance_id, _ in changes.changed_instance_attr_configs
        )

        for source_id, relationship_config_id in changes.changed_relationship_keys:
            candidates.add(source_id)
            key = (source_id, relationship_config_id)
            candidates.update(pre.relationships_by_source_and_config.get(key, ()))
            candidates.update(post.relationships_by_source_and_config.get(key, ()))

        if known_instance_ids:
            candidates &= known_instance_ids
        return candidates

    def _evaluate_condition_policy(
        self,
        *,
        condition_config_id: UUID,
        ctx: _ReceiptContext,
        allowed_instance_ids: set[UUID] | None,
        visited: set[UUID],
    ) -> bool:
        return self._evaluate_condition_policy_trace(
            condition_config_id=condition_config_id,
            ctx=ctx,
            allowed_instance_ids=allowed_instance_ids,
            visited=visited,
            entries=[],
            path="condition",
        )

    def _evaluate_condition_policy_trace(
        self,
        *,
        condition_config_id: UUID,
        ctx: _ReceiptContext,
        allowed_instance_ids: set[UUID] | None,
        visited: set[UUID],
        entries: list[ConditionEvaluationTraceEntry],
        path: str,
    ) -> bool:
        condition_path = f"{path}/condition:{condition_config_id}"
        if condition_config_id in visited:
            _trace_entry(
                entries,
                kind="condition",
                path=condition_path,
                result=False,
                reason="condition_cycle_detected",
            )
            return False

        policy = self._condition_policies_by_id.get(condition_config_id)
        if policy is None:
            _trace_entry(
                entries,
                kind="condition",
                path=condition_path,
                result=False,
                reason="condition_policy_missing",
            )
            return False
        if not policy.is_enabled:
            _trace_entry(
                entries,
                kind="condition",
                path=condition_path,
                result=False,
                reason="condition_disabled",
            )
            return False

        next_visited = set(visited)
        next_visited.add(condition_config_id)

        class_results: list[bool] = []
        for class_policy in policy.classes:
            class_results.append(
                self._evaluate_class_policy_trace(
                    class_policy=class_policy,
                    ctx=ctx,
                    allowed_instance_ids=allowed_instance_ids,
                    visited=next_visited,
                    entries=entries,
                    path=condition_path,
                )
            )
        result = self._apply_logic(policy.logic_strategy, class_results)
        _trace_entry(
            entries,
            kind="condition",
            path=condition_path,
            result=result,
            reason=_logic_reason(policy.logic_strategy),
            metadata={
                "logic_strategy": (policy.logic_strategy or "all").strip().lower(),
                "class_results": list(class_results),
                "allowed_instance_ids": (
                    sorted(str(item) for item in allowed_instance_ids)
                    if allowed_instance_ids is not None
                    else None
                ),
            },
        )
        return result

    def _evaluate_class_policy(
        self,
        *,
        class_policy: _ClassPolicy,
        ctx: _ReceiptContext,
        allowed_instance_ids: set[UUID] | None,
        visited: set[UUID],
    ) -> bool:
        return self._evaluate_class_policy_trace(
            class_policy=class_policy,
            ctx=ctx,
            allowed_instance_ids=allowed_instance_ids,
            visited=visited,
            entries=[],
            path="class",
        )

    def _evaluate_class_policy_trace(
        self,
        *,
        class_policy: _ClassPolicy,
        ctx: _ReceiptContext,
        allowed_instance_ids: set[UUID] | None,
        visited: set[UUID],
        entries: list[ConditionEvaluationTraceEntry],
        path: str,
    ) -> bool:
        class_path = f"{path}/class:{class_policy.id}"
        base_candidate_ids, candidate_ids, scope_reason = (
            self._candidate_instance_id_sets(
                class_policy=class_policy,
                ctx=ctx,
                allowed_instance_ids=allowed_instance_ids,
            )
        )
        if not candidate_ids:
            result = not class_policy.require_existence
            _trace_entry(
                entries,
                kind="class",
                path=class_path,
                result=result,
                reason=(
                    "no_scoped_candidates"
                    if base_candidate_ids
                    else "no_class_candidates"
                ),
                metadata={
                    "class_config_id": str(class_policy.class_config_id),
                    "class_selection": class_policy.class_selection,
                    "scope_reason": scope_reason,
                    "require_existence": class_policy.require_existence,
                    "base_candidate_instance_ids": sorted(
                        str(item) for item in base_candidate_ids
                    ),
                    "scoped_candidate_instance_ids": [],
                    "trigger_candidate_instance_ids": sorted(
                        str(item) for item in ctx.trigger_candidate_instance_ids
                    ),
                },
            )
            return result

        candidate_results: list[bool] = []
        for instance_id in sorted(candidate_ids, key=str):
            attr_results = [
                self._evaluate_attribute_policy_trace(
                    attribute_policy=attr_policy,
                    instance_id=instance_id,
                    ctx=ctx,
                    visited=visited,
                    entries=entries,
                    path=f"{class_path}/instance:{instance_id}",
                )
                for attr_policy in class_policy.attributes
            ]
            candidate_results.append(
                self._apply_logic(class_policy.class_logic, attr_results)
            )

        selection = (class_policy.class_selection or "").strip().lower()
        if selection == "all_classes":
            result = all(candidate_results)
        else:
            result = any(candidate_results)
        _trace_entry(
            entries,
            kind="class",
            path=class_path,
            result=result,
            reason=_logic_reason(class_policy.class_logic),
            metadata={
                "class_config_id": str(class_policy.class_config_id),
                "class_selection": class_policy.class_selection,
                "scope_reason": scope_reason,
                "base_candidate_instance_ids": sorted(
                    str(item) for item in base_candidate_ids
                ),
                "scoped_candidate_instance_ids": sorted(
                    str(item) for item in candidate_ids
                ),
                "candidate_results": list(candidate_results),
            },
        )
        return result

    def _candidate_instance_ids(
        self,
        *,
        class_policy: _ClassPolicy,
        ctx: _ReceiptContext,
        allowed_instance_ids: set[UUID] | None,
    ) -> set[UUID]:
        _, candidates, _ = self._candidate_instance_id_sets(
            class_policy=class_policy,
            ctx=ctx,
            allowed_instance_ids=allowed_instance_ids,
        )
        return candidates

    def _candidate_instance_id_sets(
        self,
        *,
        class_policy: _ClassPolicy,
        ctx: _ReceiptContext,
        allowed_instance_ids: set[UUID] | None,
    ) -> tuple[set[UUID], set[UUID], str]:
        selection = (class_policy.class_selection or "").strip().lower()
        if selection == "all_classes":
            candidates = set(ctx.pre.class_instances_by_id) | set(
                ctx.post.class_instances_by_id
            )
        elif selection == "specific_class":
            candidates = set(
                ctx.pre.class_instance_ids_by_class_config.get(
                    class_policy.class_config_id,
                    set(),
                )
            ) | set(
                ctx.post.class_instance_ids_by_class_config.get(
                    class_policy.class_config_id,
                    set(),
                )
            )
        else:
            descendants = self._descendants_by_class_config.get(
                class_policy.class_config_id,
                {class_policy.class_config_id},
            )
            candidates = set()
            for class_config_id in descendants:
                candidates |= ctx.pre.class_instance_ids_by_class_config.get(
                    class_config_id,
                    set(),
                )
                candidates |= ctx.post.class_instance_ids_by_class_config.get(
                    class_config_id,
                    set(),
                )

        base_candidates = set(candidates)
        if allowed_instance_ids is not None:
            candidates &= allowed_instance_ids
            scope_reason = "relationship_target_scope"
        else:
            candidates &= ctx.trigger_candidate_instance_ids
            scope_reason = "trigger_candidate_scope"
        return base_candidates, candidates, scope_reason

    def _evaluate_attribute_policy(
        self,
        *,
        attribute_policy: _AttributePolicy,
        instance_id: UUID,
        ctx: _ReceiptContext,
        visited: set[UUID],
    ) -> bool:
        return self._evaluate_attribute_policy_trace(
            attribute_policy=attribute_policy,
            instance_id=instance_id,
            ctx=ctx,
            visited=visited,
            entries=[],
            path="attribute",
        )

    def _evaluate_attribute_policy_trace(
        self,
        *,
        attribute_policy: _AttributePolicy,
        instance_id: UUID,
        ctx: _ReceiptContext,
        visited: set[UUID],
        entries: list[ConditionEvaluationTraceEntry],
        path: str,
    ) -> bool:
        attribute_path = f"{path}/attribute:{attribute_policy.id}"
        key = (instance_id, attribute_policy.attribute_config_id)
        pre_exists = key in ctx.pre.attribute_id_by_instance_and_config
        post_exists = key in ctx.post.attribute_id_by_instance_and_config
        pre_value = ctx.pre.value_by_instance_and_config.get(key)
        post_value = ctx.post.value_by_instance_and_config.get(key)
        changed = key in ctx.changes.changed_instance_attr_configs

        operator = (attribute_policy.operator or "equals").strip().lower()
        if attribute_policy.relationship is not None:
            result = self._evaluate_relationship_policy_trace(
                relationship_policy=attribute_policy.relationship,
                operator=operator,
                instance_id=instance_id,
                ctx=ctx,
                visited=visited,
                entries=entries,
                path=attribute_path,
            )
            reason = "relationship_policy"
        elif attribute_policy.enum is not None and operator not in {
            "changed",
            "not_changed",
        }:
            result = self._evaluate_enum_policy(
                enum_policy=attribute_policy.enum,
                operator=operator,
                post_value=post_value,
                post_exists=post_exists,
            )
            reason = "enum_policy"
        elif attribute_policy.primitive is not None:
            primitive = attribute_policy.primitive
            result = _evaluate_operator(
                operator=operator,
                pre_value=pre_value,
                post_value=post_value,
                pre_exists=pre_exists,
                post_exists=post_exists,
                changed=changed,
                expected=primitive.primitive_value,
                range_min=primitive.range_min,
                range_max=primitive.range_max,
            )
            reason = "primitive_operator"
        else:
            result = _evaluate_operator(
                operator=operator,
                pre_value=pre_value,
                post_value=post_value,
                pre_exists=pre_exists,
                post_exists=post_exists,
                changed=changed,
                expected=None,
                range_min=None,
                range_max=None,
            )
            reason = "operator"

        final_result = not result if attribute_policy.negate else result
        _trace_entry(
            entries,
            kind="attribute",
            path=attribute_path,
            result=final_result,
            reason=reason,
            metadata={
                "instance_id": str(instance_id),
                "attribute_config_id": str(attribute_policy.attribute_config_id),
                "operator": operator,
                "negate": attribute_policy.negate,
                "raw_result": result,
                "pre_exists": pre_exists,
                "post_exists": post_exists,
                "changed": changed,
                "pre_value": pre_value,
                "post_value": post_value,
            },
        )
        return final_result

    @staticmethod
    def _evaluate_enum_policy(
        *,
        enum_policy: _EnumPolicy,
        operator: str,
        post_value: object | None,
        post_exists: bool,
    ) -> bool:
        allowed = set(enum_policy.option_values)
        actual_values: set[str] = set()
        if isinstance(post_value, list):
            actual_values = {str(v) for v in post_value}
        elif post_value is not None:
            actual_values = {str(post_value)}

        match_mode = (enum_policy.match_mode or "any_of").strip().lower()
        if match_mode == "all_of":
            payload_match = bool(allowed) and allowed.issubset(actual_values)
        elif match_mode == "none_of":
            payload_match = allowed.isdisjoint(actual_values)
        else:
            payload_match = bool(actual_values & allowed)

        if operator in {"not_equals", "not_in", "not_contains"}:
            return not payload_match
        if operator in {"exists", "is_not_null"}:
            return post_exists and bool(actual_values)
        if operator in {"not_exists", "is_null"}:
            return not post_exists or not bool(actual_values)
        return payload_match

    def _evaluate_relationship_policy(
        self,
        *,
        relationship_policy: _RelationshipPolicy,
        operator: str,
        instance_id: UUID,
        ctx: _ReceiptContext,
        visited: set[UUID],
    ) -> bool:
        return self._evaluate_relationship_policy_trace(
            relationship_policy=relationship_policy,
            operator=operator,
            instance_id=instance_id,
            ctx=ctx,
            visited=visited,
            entries=[],
            path="relationship",
        )

    def _evaluate_relationship_policy_trace(
        self,
        *,
        relationship_policy: _RelationshipPolicy,
        operator: str,
        instance_id: UUID,
        ctx: _ReceiptContext,
        visited: set[UUID],
        entries: list[ConditionEvaluationTraceEntry],
        path: str,
    ) -> bool:
        relationship_path = (
            f"{path}/relationship:{relationship_policy.class_config_relationship_id}"
        )
        key = (instance_id, relationship_policy.class_config_relationship_id)
        changed = key in ctx.changes.changed_relationship_keys
        if operator == "changed":
            _trace_entry(
                entries,
                kind="relationship",
                path=relationship_path,
                result=changed,
                reason="relationship_changed_operator",
                metadata={"instance_id": str(instance_id), "changed": changed},
            )
            return changed
        if operator == "not_changed":
            result = not changed
            _trace_entry(
                entries,
                kind="relationship",
                path=relationship_path,
                result=result,
                reason="relationship_not_changed_operator",
                metadata={"instance_id": str(instance_id), "changed": changed},
            )
            return result

        targets = ctx.post.relationships_by_source_and_config.get(key, [])
        target_count = len(targets)
        eval_mode = (relationship_policy.eval_mode or "exists").strip().lower()

        if eval_mode == "exists":
            result = target_count > 0
            reason = "relationship_exists"
            return self._trace_relationship_result(
                entries=entries,
                path=relationship_path,
                result=result,
                reason=reason,
                instance_id=instance_id,
                targets=targets,
                relationship_policy=relationship_policy,
            )
        if eval_mode == "not_exists":
            result = target_count == 0
            return self._trace_relationship_result(
                entries=entries,
                path=relationship_path,
                result=result,
                reason="relationship_not_exists",
                instance_id=instance_id,
                targets=targets,
                relationship_policy=relationship_policy,
            )
        if eval_mode == "count_equals":
            threshold = relationship_policy.count_threshold
            result = threshold is not None and target_count == threshold
            return self._trace_relationship_result(
                entries=entries,
                path=relationship_path,
                result=result,
                reason="relationship_count_equals",
                instance_id=instance_id,
                targets=targets,
                relationship_policy=relationship_policy,
            )
        if eval_mode == "count_greater":
            threshold = relationship_policy.count_threshold
            result = threshold is not None and target_count > threshold
            return self._trace_relationship_result(
                entries=entries,
                path=relationship_path,
                result=result,
                reason="relationship_count_greater",
                instance_id=instance_id,
                targets=targets,
                relationship_policy=relationship_policy,
            )
        if eval_mode == "count_less":
            threshold = relationship_policy.count_threshold
            result = threshold is not None and target_count < threshold
            return self._trace_relationship_result(
                entries=entries,
                path=relationship_path,
                result=result,
                reason="relationship_count_less",
                instance_id=instance_id,
                targets=targets,
                relationship_policy=relationship_policy,
            )

        nested_condition_id = relationship_policy.nested_condition_config_id
        if nested_condition_id is None:
            if eval_mode == "any_match":
                result = target_count > 0
                reason = "relationship_any_match_without_nested"
            elif eval_mode == "all_match":
                result = target_count > 0
                reason = "relationship_all_match_without_nested"
            elif eval_mode == "none_match":
                result = target_count == 0
                reason = "relationship_none_match_without_nested"
            else:
                result = False
                reason = "relationship_unknown_eval_mode"
            return self._trace_relationship_result(
                entries=entries,
                path=relationship_path,
                result=result,
                reason=reason,
                instance_id=instance_id,
                targets=targets,
                relationship_policy=relationship_policy,
            )

        if not targets:
            result = eval_mode == "none_match"
            return self._trace_relationship_result(
                entries=entries,
                path=relationship_path,
                result=result,
                reason="relationship_nested_no_targets",
                instance_id=instance_id,
                targets=targets,
                relationship_policy=relationship_policy,
            )

        nested_results = [
            self._evaluate_condition_policy_trace(
                condition_config_id=nested_condition_id,
                ctx=ctx,
                allowed_instance_ids={target_id},
                visited=visited,
                entries=entries,
                path=f"{relationship_path}/target:{target_id}",
            )
            for target_id in targets
        ]
        if eval_mode == "any_match":
            result = any(nested_results)
            reason = "relationship_nested_any_match"
        elif eval_mode == "all_match":
            result = all(nested_results)
            reason = "relationship_nested_all_match"
        elif eval_mode == "none_match":
            result = not any(nested_results)
            reason = "relationship_nested_none_match"
        else:
            result = False
            reason = "relationship_unknown_eval_mode"
        return self._trace_relationship_result(
            entries=entries,
            path=relationship_path,
            result=result,
            reason=reason,
            instance_id=instance_id,
            targets=targets,
            relationship_policy=relationship_policy,
            nested_results=nested_results,
        )

    @staticmethod
    def _trace_relationship_result(
        *,
        entries: list[ConditionEvaluationTraceEntry],
        path: str,
        result: bool,
        reason: str,
        instance_id: UUID,
        targets: list[UUID],
        relationship_policy: _RelationshipPolicy,
        nested_results: list[bool] | None = None,
    ) -> bool:
        _trace_entry(
            entries,
            kind="relationship",
            path=path,
            result=result,
            reason=reason,
            metadata={
                "instance_id": str(instance_id),
                "class_config_relationship_id": str(
                    relationship_policy.class_config_relationship_id
                ),
                "eval_mode": relationship_policy.eval_mode,
                "target_instance_ids": [str(item) for item in targets],
                "target_count": len(targets),
                "count_threshold": relationship_policy.count_threshold,
                "nested_condition_config_id": (
                    str(relationship_policy.nested_condition_config_id)
                    if relationship_policy.nested_condition_config_id is not None
                    else None
                ),
                "nested_results": list(nested_results or []),
            },
        )
        return result

    @staticmethod
    def _apply_logic(strategy: str, values: list[bool]) -> bool:
        logic = (strategy or "all").strip().lower()
        if logic == "any":
            return any(values)
        if logic == "none":
            return not any(values)
        # sequence currently behaves as ordered-all.
        return all(values)


def _logic_reason(strategy: str) -> str:
    logic = (strategy or "all").strip().lower()
    if logic == "any":
        return "logic_any"
    if logic == "none":
        return "logic_none"
    if logic == "sequence":
        return "sequence_ordered_all"
    return "logic_all"


__all__ = [
    "ConditionEvaluationTrace",
    "ConditionEvaluationTraceEntry",
    "LaneMaterializedConditionEvaluator",
]
