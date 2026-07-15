"""In-memory ORM change collection (canonical, v0).

Goal
----
Handlers must not call `push()` and must not build commits directly. The runtime
needs a **deterministic** and **local** way to know what changed during handler
execution without relying on building a full OIG(post) snapshot.

This module provides a lightweight ContextVar-based change collector used by:
- ORM hooks (field assignment / tracked list mutation / identity-map add)
- Runtime coordinators (start scope → execute handler(s) → read collected changes)

SSOT for commits remains the canonical OIG Change graph models. This collector
is intentionally ORM-only and does not depend on OIG concepts.
"""

from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Iterator, SupportsIndex
from uuid import UUID

import operator

from aware_orm.session.execution_guard import is_read_only_scope
from aware_orm.session.execution_guard import current_mutation_owner
from aware_orm.session.execution_guard import is_domain_create_allowed
from aware_orm.session.execution_guard import current_constructor_create_scope


def stable_ref(value: Any) -> Any:
    """Convert common ORM-ish references to stable ids for baseline storage."""
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    # Avoid importing ORMModel/BaseORMModel to keep this module leaf-ish.
    obj_id = getattr(value, "id", None)
    if isinstance(obj_id, UUID):
        return obj_id
    return value


def snapshot_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        return []
    return [stable_ref(v) for v in list(value)]


@dataclass
class ORMChangeSet:
    """Immutable view of the changes collected within a scoped execution."""

    collected_at: datetime
    created_ids: frozenset[UUID]
    touched_ids: frozenset[UUID]
    deleted_ids: frozenset[UUID]
    objects_by_id: dict[UUID, Any]
    scalar_fields_by_id: dict[UUID, set[str]]
    list_fields_by_id: dict[UUID, set[str]]
    scalar_baseline: dict[tuple[UUID, str], Any]
    list_baseline: dict[tuple[UUID, str], list[Any]]
    list_added: dict[tuple[UUID, str], set[Any]]
    list_removed: dict[tuple[UUID, str], set[Any]]


@dataclass
class ORMChangeCollector:
    """Collect in-memory changes to ORM models during a runtime execution scope."""

    should_track: Callable[[Any], bool] | None = None
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_ids: set[UUID] = field(default_factory=set)
    touched_ids: set[UUID] = field(default_factory=set)
    deleted_ids: set[UUID] = field(default_factory=set)
    objects_by_id: dict[UUID, Any] = field(default_factory=dict)

    scalar_fields_by_id: dict[UUID, set[str]] = field(default_factory=dict)
    list_fields_by_id: dict[UUID, set[str]] = field(default_factory=dict)

    # Baseline values captured at first mutation within the current scope.
    scalar_baseline: dict[tuple[UUID, str], Any] = field(default_factory=dict)
    list_baseline: dict[tuple[UUID, str], list[Any]] = field(default_factory=dict)

    # Incremental list membership deltas captured during the scope. These are used by
    # the ORM→OIG translator to avoid re-scanning large relationship lists.
    list_added: dict[tuple[UUID, str], set[Any]] = field(default_factory=dict)
    list_removed: dict[tuple[UUID, str], set[Any]] = field(default_factory=dict)

    def _register_object(self, obj: Any, *, enforce_mutation_owner: bool = True) -> UUID | None:
        if self.should_track is not None:
            try:
                if not self.should_track(obj):
                    return None
            except Exception:
                return None
        obj_id = getattr(obj, "id", None)
        if not isinstance(obj_id, UUID):
            return None

        if is_read_only_scope():
            raise PermissionError(
                "Mutation is not allowed in a read-only function invocation scope. "
                "Ontology function calls are mutation-oriented; use service views for reads."
            )
        if enforce_mutation_owner:
            owner = current_mutation_owner()
            if owner is not None and owner != obj_id:
                raise PermissionError(
                    f"Cross-object mutation detected: owner={owner} target={obj_id}. "
                    "Call the object's public method instead."
                )
        self.touched_ids.add(obj_id)
        self.objects_by_id.setdefault(obj_id, obj)
        return obj_id

    def record_create(self, obj: Any) -> None:
        obj_id = self._register_object(obj, enforce_mutation_owner=False)
        if obj_id is None:
            return

        # Same-scope delete -> recreate with the same deterministic id is a replacement,
        # not a net delete. Keep the surviving object visible to downstream diff builders.
        self.deleted_ids.discard(obj_id)

        owner = current_mutation_owner()
        if self.should_track is not None:
            constructor_scope = current_constructor_create_scope()
            if constructor_scope is not None:
                class_config_id = None
                try:
                    class_config_id = obj.try_class_config_id()
                except Exception:
                    class_config_id = None
                if owner is not None:
                    raise PermissionError(
                        "Constructor object creation requires constructor mutation scope: "
                        f"owner={owner} target={obj_id}."
                    )
                if class_config_id != constructor_scope.target_class_config_id:
                    raise PermissionError(
                        "Constructor object creation target class mismatch: "
                        + f"expected_class_config_id={constructor_scope.target_class_config_id} "
                        + f"actual_class_config_id={class_config_id} instance_id={obj_id}."
                    )
                if obj_id != constructor_scope.expected_instance_id:
                    raise PermissionError(
                        "Constructor object creation target id mismatch: "
                        + f"expected_instance_id={constructor_scope.expected_instance_id} "
                        + f"actual_instance_id={obj_id} "
                        + f"target_class_config_id={constructor_scope.target_class_config_id}."
                    )
            elif owner is not None or not is_domain_create_allowed():
                raise PermissionError(
                    "Domain object creation is only allowed via constructor handlers: "
                    f"class={type(obj).__module__}.{type(obj).__name__} instance_id={obj_id}. "
                    f"Please ensure Function Call propagation by invoking {type(obj).__module__} constructor function."
                )
        self.created_ids.add(obj_id)

    def record_reference(self, obj: Any) -> None:
        """Register an object for lookup (objects_by_id) without marking it as mutated.

        This is used for association-edge list deltas where the list stores edge
        objects and the ORM→OIG translator needs to read their FK fields.
        """
        if self.should_track is not None:
            try:
                if not self.should_track(obj):
                    return
            except Exception:
                return
        obj_id = getattr(obj, "id", None)
        if not isinstance(obj_id, UUID):
            return
        if obj_id in self.deleted_ids:
            return
        self.objects_by_id.setdefault(obj_id, obj)

    def record_delete(self, obj: Any) -> None:
        """Mark an instance as explicitly deleted in this scope."""
        obj_id = self._register_object(obj)
        if obj_id is None:
            return

        # create+delete in one scope leaves no net create. If the same stable id is
        # created again later in the scope, record_create(...) clears deleted_ids.
        self.created_ids.discard(obj_id)
        self.deleted_ids.add(obj_id)

        # Deleting an instance should omit it from the reconstructed "after" subset.
        self.objects_by_id.pop(obj_id, None)

    def record_scalar_set(self, *, obj: Any, field_name: str, old_value: Any) -> None:
        obj_id = self._register_object(obj)
        if obj_id is None:
            return
        self.scalar_fields_by_id.setdefault(obj_id, set()).add(field_name)
        key = (obj_id, field_name)
        if key not in self.scalar_baseline:
            self.scalar_baseline[key] = stable_ref(old_value)

    def record_list_touch(self, *, obj: Any, field_name: str) -> None:
        """Mark a list field as mutated without capturing a baseline snapshot."""
        obj_id = self._register_object(obj)
        if obj_id is None:
            return
        self.list_fields_by_id.setdefault(obj_id, set()).add(field_name)

    def record_list_mutation(self, *, obj: Any, field_name: str, before: list[Any]) -> None:
        obj_id = self._register_object(obj)
        if obj_id is None:
            return
        self.list_fields_by_id.setdefault(obj_id, set()).add(field_name)
        key = (obj_id, field_name)
        if key not in self.list_baseline:
            self.list_baseline[key] = list(before)

    def record_list_item_add(self, *, obj: Any, field_name: str, value: Any) -> None:
        obj_id = self._register_object(obj)
        if obj_id is None:
            return
        self.list_fields_by_id.setdefault(obj_id, set()).add(field_name)
        key = (obj_id, field_name)
        removed = self.list_removed.get(key)
        if removed is not None and value in removed:
            removed.discard(value)
            if not removed:
                self.list_removed.pop(key, None)
            return
        self.list_added.setdefault(key, set()).add(value)

    def record_list_item_remove(self, *, obj: Any, field_name: str, value: Any) -> None:
        obj_id = self._register_object(obj)
        if obj_id is None:
            return
        self.list_fields_by_id.setdefault(obj_id, set()).add(field_name)
        key = (obj_id, field_name)
        added = self.list_added.get(key)
        if added is not None and value in added:
            added.discard(value)
            if not added:
                self.list_added.pop(key, None)
            return
        self.list_removed.setdefault(key, set()).add(value)

    def record_list_set(self, *, obj: Any, field_name: str, before: list[Any], after: list[Any]) -> None:
        """Record a list field replacement (assignment) as incremental membership deltas."""
        obj_id = self._register_object(obj)
        if obj_id is None:
            return
        self.list_fields_by_id.setdefault(obj_id, set()).add(field_name)
        key = (obj_id, field_name)
        if key not in self.list_baseline:
            self.list_baseline[key] = list(before)

        before_ids = {v for v in before if isinstance(v, UUID)}
        after_ids = {v for v in after if isinstance(v, UUID)}

        for v in sorted(after_ids - before_ids, key=str):
            self.record_list_item_add(obj=obj, field_name=field_name, value=v)
        for v in sorted(before_ids - after_ids, key=str):
            self.record_list_item_remove(obj=obj, field_name=field_name, value=v)

    def snapshot(self) -> ORMChangeSet:
        alias_by_tracked_id: dict[UUID, UUID] = {}
        objects_by_id: dict[UUID, Any] = {}

        for tracked_id, obj in self.objects_by_id.items():
            current_id = getattr(obj, "id", None)
            normalized_id = current_id if isinstance(current_id, UUID) else tracked_id
            alias_by_tracked_id[tracked_id] = normalized_id
            objects_by_id.setdefault(normalized_id, obj)

        def normalize_id(value: UUID) -> UUID:
            return alias_by_tracked_id.get(value, value)

        def normalize_value(value: Any) -> Any:
            if isinstance(value, UUID):
                return normalize_id(value)
            return value

        scalar_fields_by_id: dict[UUID, set[str]] = {}
        for obj_id, field_names in self.scalar_fields_by_id.items():
            scalar_fields_by_id.setdefault(normalize_id(obj_id), set()).update(field_names)

        list_fields_by_id: dict[UUID, set[str]] = {}
        for obj_id, field_names in self.list_fields_by_id.items():
            list_fields_by_id.setdefault(normalize_id(obj_id), set()).update(field_names)

        scalar_baseline: dict[tuple[UUID, str], Any] = {}
        for (obj_id, field_name), value in self.scalar_baseline.items():
            key = (normalize_id(obj_id), field_name)
            scalar_baseline.setdefault(key, normalize_value(value))

        list_baseline: dict[tuple[UUID, str], list[Any]] = {}
        for (obj_id, field_name), values in self.list_baseline.items():
            key = (normalize_id(obj_id), field_name)
            list_baseline.setdefault(key, [normalize_value(value) for value in values])

        list_added: dict[tuple[UUID, str], set[Any]] = {}
        for (obj_id, field_name), values in self.list_added.items():
            key = (normalize_id(obj_id), field_name)
            list_added.setdefault(key, set()).update(normalize_value(value) for value in values)

        list_removed: dict[tuple[UUID, str], set[Any]] = {}
        for (obj_id, field_name), values in self.list_removed.items():
            key = (normalize_id(obj_id), field_name)
            list_removed.setdefault(key, set()).update(normalize_value(value) for value in values)

        return ORMChangeSet(
            collected_at=self.collected_at,
            created_ids=frozenset(normalize_id(obj_id) for obj_id in self.created_ids),
            touched_ids=frozenset(normalize_id(obj_id) for obj_id in self.touched_ids),
            deleted_ids=frozenset(normalize_id(obj_id) for obj_id in self.deleted_ids),
            objects_by_id=objects_by_id,
            scalar_fields_by_id=scalar_fields_by_id,
            list_fields_by_id=list_fields_by_id,
            scalar_baseline=scalar_baseline,
            list_baseline=list_baseline,
            list_added=list_added,
            list_removed=list_removed,
        )


_collector_ctx: ContextVar[ORMChangeCollector | None] = ContextVar("aware_orm_change_collector", default=None)
_tracked_list_wrapping_enabled: ContextVar[bool] = ContextVar(
    "aware_orm_tracked_list_wrapping_enabled",
    default=True,
)
_change_tracking_hooks_enabled: ContextVar[bool] = ContextVar(
    "aware_orm_change_tracking_hooks_enabled",
    default=True,
)


def current_change_collector() -> ORMChangeCollector | None:
    return _collector_ctx.get()


def is_tracked_list_wrapping_enabled() -> bool:
    return _tracked_list_wrapping_enabled.get()


def is_change_tracking_hooks_enabled() -> bool:
    return _change_tracking_hooks_enabled.get()


def _set_change_collector(
    value: ORMChangeCollector | None,
) -> Token[ORMChangeCollector | None]:
    return _collector_ctx.set(value)


def _reset_change_collector(token: Token[ORMChangeCollector | None]) -> None:
    _collector_ctx.reset(token)


@contextmanager
def scoped_change_collection(*, should_track: Callable[[Any], bool] | None = None) -> Iterator[ORMChangeCollector]:
    """Start a fresh change collection scope (nested scopes override)."""
    collector = ORMChangeCollector(should_track=should_track, collected_at=datetime.now(timezone.utc))
    token = _set_change_collector(collector)
    try:
        yield collector
    finally:
        _reset_change_collector(token)


@contextmanager
def disable_tracked_list_wrapping() -> Iterator[None]:
    token = _tracked_list_wrapping_enabled.set(False)
    try:
        yield
    finally:
        _tracked_list_wrapping_enabled.reset(token)


@contextmanager
def disable_change_tracking_hooks() -> Iterator[None]:
    hooks_token = _change_tracking_hooks_enabled.set(False)
    wrapping_token = _tracked_list_wrapping_enabled.set(False)
    try:
        yield
    finally:
        _tracked_list_wrapping_enabled.reset(wrapping_token)
        _change_tracking_hooks_enabled.reset(hooks_token)


class TrackedList(list[Any]):
    """List wrapper that records mutations into the current ORMChangeCollector."""

    __slots__ = ("_owner", "_field_name", "_uuid_member_counts")

    def __init__(self, owner: Any, field_name: str, initial: list[Any] | None = None) -> None:
        super().__init__(initial or [])
        self._owner = owner
        self._field_name = field_name
        self._uuid_member_counts: dict[UUID, int] | None = None

    def _collector(self) -> ORMChangeCollector | None:
        collector = current_change_collector()
        if collector is None:
            return None
        owner = self._owner
        if collector.should_track is not None:
            try:
                if not collector.should_track(owner):
                    return None
            except Exception:
                return None
        return collector

    def _ensure_uuid_member_counts(self) -> dict[UUID, int]:
        counts = self._uuid_member_counts
        if counts is not None:
            return counts
        counts = {}
        for item in self:
            item_ref = stable_ref(item)
            if not isinstance(item_ref, UUID):
                continue
            counts[item_ref] = counts.get(item_ref, 0) + 1
        self._uuid_member_counts = counts
        return counts

    def _touch(self, collector: ORMChangeCollector) -> None:
        collector.record_list_touch(obj=self._owner, field_name=self._field_name)

    @staticmethod
    def _record_reference(collector: ORMChangeCollector, item: Any) -> None:
        if item is None or isinstance(item, UUID):
            return
        try:
            collector.record_reference(item)
        except Exception:
            return

    @staticmethod
    def _record_added_reference(collector: ORMChangeCollector, item: Any) -> None:
        if item is None or isinstance(item, UUID):
            return
        try:
            is_new = bool(getattr(item, "is_new", False))
        except Exception:
            is_new = False
        if is_new:
            collector.record_create(item)
            return
        TrackedList._record_reference(collector, item)

    def append(self, item: Any) -> None:  # type: ignore[override]
        collector = self._collector()
        if collector is None:
            item_ref = stable_ref(item)
            super().append(item)
            if isinstance(item_ref, UUID) and self._uuid_member_counts is not None:
                self._uuid_member_counts[item_ref] = self._uuid_member_counts.get(item_ref, 0) + 1
            return None

        self._touch(collector)
        self._record_added_reference(collector, item)
        item_ref = stable_ref(item)
        counts: dict[UUID, int] | None = None
        prev = 0
        if isinstance(item_ref, UUID):
            counts = self._ensure_uuid_member_counts()
            prev = counts.get(item_ref, 0)

        super().append(item)

        if counts is not None and isinstance(item_ref, UUID):
            counts[item_ref] = prev + 1
            if prev == 0:
                collector.record_list_item_add(obj=self._owner, field_name=self._field_name, value=item_ref)

    def extend(self, items: Iterable[Any]) -> None:
        collector = self._collector()
        if collector is None:
            if self._uuid_member_counts is None:
                super().extend(items)
                return None

            items_list = list(items)
            super().extend(items_list)
            for item in items_list:
                item_ref = stable_ref(item)
                if isinstance(item_ref, UUID):
                    self._uuid_member_counts[item_ref] = self._uuid_member_counts.get(item_ref, 0) + 1
            return None

        items_list = list(items)
        self._touch(collector)

        refs_to_add: set[UUID] = set()
        counts: dict[UUID, int] | None = None
        for item in items_list:
            self._record_added_reference(collector, item)
            item_ref = stable_ref(item)
            if not isinstance(item_ref, UUID):
                continue
            if counts is None:
                counts = self._ensure_uuid_member_counts()
            prev = counts.get(item_ref, 0)
            counts[item_ref] = prev + 1
            if prev == 0:
                refs_to_add.add(item_ref)

        super().extend(items_list)

        for item_ref in sorted(refs_to_add, key=str):
            collector.record_list_item_add(obj=self._owner, field_name=self._field_name, value=item_ref)

    def __iadd__(self, other):  # type: ignore[override]
        self.extend(other)
        return self

    def __imul__(self, n):  # type: ignore[override]
        multiplier = operator.index(n)
        collector = self._collector()

        if collector is None:
            super().__imul__(multiplier)
            if self._uuid_member_counts is not None:
                if multiplier <= 0:
                    self._uuid_member_counts.clear()
                else:
                    for key in list(self._uuid_member_counts.keys()):
                        self._uuid_member_counts[key] *= multiplier
            return self

        if multiplier == 1:
            return self

        self._touch(collector)

        if multiplier <= 0:
            counts = self._ensure_uuid_member_counts()
            removed = sorted(counts.keys(), key=str)
            super().__imul__(multiplier)
            counts.clear()
            for value_ref in removed:
                collector.record_list_item_remove(obj=self._owner, field_name=self._field_name, value=value_ref)
            return self

        super().__imul__(multiplier)
        if self._uuid_member_counts is not None:
            for key in list(self._uuid_member_counts.keys()):
                self._uuid_member_counts[key] *= multiplier
        return self

    def insert(self, index: SupportsIndex, item: Any) -> None:
        collector = self._collector()
        if collector is None:
            item_ref = stable_ref(item)
            super().insert(index, item)
            if isinstance(item_ref, UUID) and self._uuid_member_counts is not None:
                self._uuid_member_counts[item_ref] = self._uuid_member_counts.get(item_ref, 0) + 1
            return None

        self._touch(collector)
        self._record_added_reference(collector, item)
        item_ref = stable_ref(item)
        counts: dict[UUID, int] | None = None
        prev = 0
        if isinstance(item_ref, UUID):
            counts = self._ensure_uuid_member_counts()
            prev = counts.get(item_ref, 0)

        super().insert(index, item)

        if counts is not None and isinstance(item_ref, UUID):
            counts[item_ref] = prev + 1
            if prev == 0:
                collector.record_list_item_add(obj=self._owner, field_name=self._field_name, value=item_ref)

    def remove(self, item: Any) -> None:  # type: ignore[override]
        collector = self._collector()
        if collector is None:
            item_ref = stable_ref(item)
            super().remove(item)
            if isinstance(item_ref, UUID) and self._uuid_member_counts is not None:
                prev = self._uuid_member_counts.get(item_ref, 0)
                if prev <= 1:
                    self._uuid_member_counts.pop(item_ref, None)
                else:
                    self._uuid_member_counts[item_ref] = prev - 1
            return None

        self._touch(collector)
        self._record_reference(collector, item)
        item_ref = stable_ref(item)
        counts: dict[UUID, int] | None = None
        prev = 0
        if isinstance(item_ref, UUID):
            counts = self._ensure_uuid_member_counts()
            prev = counts.get(item_ref, 0)

        super().remove(item)

        if counts is not None and isinstance(item_ref, UUID):
            new_count = prev - 1
            if new_count <= 0:
                counts.pop(item_ref, None)
                collector.record_list_item_remove(obj=self._owner, field_name=self._field_name, value=item_ref)
            else:
                counts[item_ref] = new_count

    def pop(self, index: SupportsIndex = -1) -> Any:
        collector = self._collector()
        if collector is None:
            value = super().pop(index)
            value_ref = stable_ref(value)
            if isinstance(value_ref, UUID) and self._uuid_member_counts is not None:
                prev = self._uuid_member_counts.get(value_ref, 0)
                if prev <= 1:
                    self._uuid_member_counts.pop(value_ref, None)
                else:
                    self._uuid_member_counts[value_ref] = prev - 1
            return value

        self._touch(collector)
        value = self[index]
        self._record_reference(collector, value)
        value_ref = stable_ref(value)
        counts: dict[UUID, int] | None = None
        prev = 0
        if isinstance(value_ref, UUID):
            counts = self._ensure_uuid_member_counts()
            prev = counts.get(value_ref, 0)

        value = super().pop(index)

        if counts is not None and isinstance(value_ref, UUID):
            new_count = prev - 1
            if new_count <= 0:
                counts.pop(value_ref, None)
                collector.record_list_item_remove(obj=self._owner, field_name=self._field_name, value=value_ref)
            else:
                counts[value_ref] = new_count
        return value

    def clear(self) -> None:  # type: ignore[override]
        collector = self._collector()
        if collector is None:
            super().clear()
            if self._uuid_member_counts is not None:
                self._uuid_member_counts.clear()
            return None

        self._touch(collector)
        for item in list(self):
            self._record_reference(collector, item)
        counts = self._ensure_uuid_member_counts()
        removed = sorted(counts.keys(), key=str)

        super().clear()
        counts.clear()

        for value_ref in removed:
            collector.record_list_item_remove(obj=self._owner, field_name=self._field_name, value=value_ref)

    def __setitem__(self, key, value) -> None:  # type: ignore[override]
        collector = self._collector()
        if isinstance(key, slice):
            old_values = list(self[key])
            new_values = list(value)
            value_for_set = new_values
        else:
            old_values = [self[key]]
            new_values = [value]
            value_for_set = value

        if collector is not None:
            for item in old_values:
                self._record_reference(collector, item)
            for item in new_values:
                self._record_added_reference(collector, item)

        old_uuid_refs = [ref for ref in (stable_ref(v) for v in old_values) if isinstance(ref, UUID)]
        new_uuid_refs = [ref for ref in (stable_ref(v) for v in new_values) if isinstance(ref, UUID)]

        if collector is None:
            super().__setitem__(key, value_for_set)
            if self._uuid_member_counts is not None and (old_uuid_refs or new_uuid_refs):
                counts = self._uuid_member_counts
                for ref in old_uuid_refs:
                    prev = counts.get(ref, 0)
                    if prev <= 1:
                        counts.pop(ref, None)
                    else:
                        counts[ref] = prev - 1
                for ref in new_uuid_refs:
                    counts[ref] = counts.get(ref, 0) + 1
            return None

        self._touch(collector)
        counts: dict[UUID, int] | None = None
        if old_uuid_refs or new_uuid_refs:
            counts = self._ensure_uuid_member_counts()

        super().__setitem__(key, value_for_set)

        if counts is None:
            return None

        for ref in old_uuid_refs:
            prev = counts.get(ref, 0)
            new_count = prev - 1
            if new_count <= 0:
                counts.pop(ref, None)
                collector.record_list_item_remove(obj=self._owner, field_name=self._field_name, value=ref)
            else:
                counts[ref] = new_count

        for ref in new_uuid_refs:
            prev = counts.get(ref, 0)
            counts[ref] = prev + 1
            if prev == 0:
                collector.record_list_item_add(obj=self._owner, field_name=self._field_name, value=ref)

    def __delitem__(self, key) -> None:  # type: ignore[override]
        collector = self._collector()
        if isinstance(key, slice):
            old_values = list(self[key])
        else:
            old_values = [self[key]]

        if collector is not None:
            for item in old_values:
                self._record_reference(collector, item)

        removed_uuid_refs = [ref for ref in (stable_ref(v) for v in old_values) if isinstance(ref, UUID)]

        if collector is None:
            super().__delitem__(key)
            if self._uuid_member_counts is not None and removed_uuid_refs:
                counts = self._uuid_member_counts
                for ref in removed_uuid_refs:
                    prev = counts.get(ref, 0)
                    if prev <= 1:
                        counts.pop(ref, None)
                    else:
                        counts[ref] = prev - 1
            return None

        self._touch(collector)
        counts: dict[UUID, int] | None = None
        if removed_uuid_refs:
            counts = self._ensure_uuid_member_counts()

        super().__delitem__(key)

        if counts is None:
            return None

        for ref in removed_uuid_refs:
            prev = counts.get(ref, 0)
            new_count = prev - 1
            if new_count <= 0:
                counts.pop(ref, None)
                collector.record_list_item_remove(obj=self._owner, field_name=self._field_name, value=ref)
            else:
                counts[ref] = new_count

    def sort(self, *args, **kwargs) -> None:  # type: ignore[override]
        collector = self._collector()
        if collector is not None:
            self._touch(collector)
        super().sort(*args, **kwargs)

    def reverse(self) -> None:  # type: ignore[override]
        collector = self._collector()
        if collector is not None:
            self._touch(collector)
        super().reverse()


def wrap_tracked_list(*, owner: Any, field_name: str, value: Any) -> Any:
    if isinstance(value, TrackedList):
        if getattr(value, "_owner", None) is owner and getattr(value, "_field_name", None) == field_name:
            return value
        return TrackedList(owner=owner, field_name=field_name, initial=list(value))
    if isinstance(value, list):
        return TrackedList(owner=owner, field_name=field_name, initial=value)
    return value


__all__ = [
    "ORMChangeCollector",
    "ORMChangeSet",
    "TrackedList",
    "current_change_collector",
    "disable_change_tracking_hooks",
    "disable_tracked_list_wrapping",
    "is_change_tracking_hooks_enabled",
    "is_tracked_list_wrapping_enabled",
    "scoped_change_collection",
    "snapshot_list",
    "stable_ref",
    "wrap_tracked_list",
]
