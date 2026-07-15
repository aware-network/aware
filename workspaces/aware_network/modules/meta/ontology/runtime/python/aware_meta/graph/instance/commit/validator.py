"""Canonical validators for OIG commit payloads.

These validators enforce the v0 SSOT contract:

ObjectInstanceGraphCommit
→ ObjectInstanceGraphChange[]
→ Change(type=CREATE|UPDATE|DELETE)
→ ChangeDelta[] (delta-only; v0 supports SCALAR_SET only)

Design goals:
- Fail fast with precise paths for debugging.
- Do not perform any DB lookups.
- Validate only what the graph commit/applier pipeline requires today.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Iterable
from uuid import UUID

from aware_history_ontology.change.change import Change
from aware_history_ontology.change.change_delta import ChangeDelta
from aware_history_ontology.change.change_enums import ChangeDeltaKind, ChangeType
from aware_meta_ontology.attribute.attribute_change import AttributeChange
from aware_meta_ontology.attribute.attribute_value_change import AttributeValueChange
from aware_meta_ontology.attribute.attribute_value_link_change import (
    AttributeValueLinkChange,
)
from aware_meta_ontology.class_.class_instance_change import ClassInstanceChange
from aware_meta_ontology.class_.class_instance_relationship_change import (
    ClassInstanceRelationshipChange,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change_enums import (
    ObjectInstanceGraphChangeType,
)
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)


class OigCommitValidationError(ValueError):
    pass


@dataclass(frozen=True)
class _Ctx:
    path: str

    def child(self, part: str) -> "_Ctx":
        return _Ctx(path=f"{self.path}.{part}" if self.path else part)


def validate_object_instance_graph_commit(
    *,
    commit: ObjectInstanceGraphCommit,
    expected_object_instance_graph_identity_id: UUID | None = None,
    expected_object_instance_graph_id: UUID | None = None,
    expected_projection_hash: str | None = None,
    require_linear_history: bool = True,
) -> None:
    ctx = _Ctx("commit")

    if commit.commit is None:
        raise OigCommitValidationError(f"{ctx.path}: missing history Commit relationship")
    if commit.commit.id is None:
        raise OigCommitValidationError(f"{ctx.path}.commit: missing id")
    if commit.commit_id is not None and commit.commit_id != commit.commit.id:
        raise OigCommitValidationError(
            f"{ctx.path}.commit_id: mismatch (field={commit.commit_id} rel={commit.commit.id})"
        )
    if commit.commit.created_at is None:
        raise OigCommitValidationError(f"{ctx.path}.commit.created_at: required")
    if commit.commit.created_at.tzinfo is None or commit.commit.created_at.utcoffset() is None:
        raise OigCommitValidationError(f"{ctx.path}.commit.created_at: timezone-aware UTC required")
    if commit.commit.created_at.utcoffset() != timedelta(0):
        raise OigCommitValidationError(f"{ctx.path}.commit.created_at: must be UTC")

    if require_linear_history and len(commit.commit.commit_parents) > 1:
        raise OigCommitValidationError(
            f"{ctx.path}.commit.commit_parents: non-linear (len={len(commit.commit.commit_parents)})"
        )

    for idx, parent in enumerate(commit.commit.commit_parents):
        pctx = ctx.child(f"commit.commit_parents[{idx}]")
        if parent.commit_id != commit.commit.id:
            raise OigCommitValidationError(
                f"{pctx.path}.commit_id: must equal commit.commit.id ({commit.commit.id}), got {parent.commit_id}"
            )
        if parent.parent_commit_id == commit.commit.id:
            raise OigCommitValidationError(f"{pctx.path}.parent_commit_id: cannot point to self")

    if not commit.projection_hash:
        raise OigCommitValidationError(f"{ctx.path}.projection_hash: required for lane commits")
    if expected_projection_hash is not None and commit.projection_hash != expected_projection_hash:
        raise OigCommitValidationError(
            f"{ctx.path}.projection_hash: expected {expected_projection_hash}, got {commit.projection_hash}"
        )

    if (
        expected_object_instance_graph_identity_id is not None
        and commit.object_instance_graph_identity_id != expected_object_instance_graph_identity_id
    ):
        raise OigCommitValidationError(
            f"{ctx.path}.object_instance_graph_identity_id: expected {expected_object_instance_graph_identity_id}, got {commit.object_instance_graph_identity_id}"
        )

    if commit.object_instance_graph_id is None:
        raise OigCommitValidationError(f"{ctx.path}.object_instance_graph_id: required")
    if (
        expected_object_instance_graph_id is not None
        and commit.object_instance_graph_id != expected_object_instance_graph_id
    ):
        raise OigCommitValidationError(
            f"{ctx.path}.object_instance_graph_id: expected {expected_object_instance_graph_id}, got {commit.object_instance_graph_id}"
        )

    if not commit.graph_hash_pre:
        raise OigCommitValidationError(f"{ctx.path}.graph_hash_pre: required")
    if not commit.graph_hash_post:
        raise OigCommitValidationError(f"{ctx.path}.graph_hash_post: required")
    if not commit.object_instance_graph_key:
        raise OigCommitValidationError(f"{ctx.path}.object_instance_graph_key: required")
    if commit.root_class_config_id is None:
        raise OigCommitValidationError(f"{ctx.path}.root_class_config_id: required")
    if commit.root_source_object_id is None:
        raise OigCommitValidationError(f"{ctx.path}.root_source_object_id: required")

    if not commit.object_instance_graph_changes:
        if commit.commit.commit_parents:
            raise OigCommitValidationError(
                f"{ctx.path}.object_instance_graph_changes: empty payload allowed only for parentless rooted seed commits"
            )
        if commit.graph_hash_pre != commit.graph_hash_post:
            raise OigCommitValidationError(
                f"{ctx.path}.object_instance_graph_changes: empty payload requires graph_hash_pre == graph_hash_post"
            )
        return

    _validate_oig_change_trees(
        changes=commit.object_instance_graph_changes,
        ctx=ctx.child("object_instance_graph_changes"),
        expected_object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
        expected_object_instance_graph_id=commit.object_instance_graph_id,
    )


def _validate_oig_change_trees(
    *,
    changes: Iterable[ObjectInstanceGraphChange],
    ctx: _Ctx,
    expected_object_instance_graph_identity_id: UUID,
    expected_object_instance_graph_id: UUID,
) -> None:
    seen_root_keys: set[tuple[ObjectInstanceGraphChangeType, UUID]] = set()
    for idx, tree in enumerate(changes):
        tctx = ctx.child(f"[{idx}]")
        if tree.object_instance_graph_identity_id != expected_object_instance_graph_identity_id:
            raise OigCommitValidationError(
                f"{tctx.path}.object_instance_graph_identity_id: expected {expected_object_instance_graph_identity_id}, got {tree.object_instance_graph_identity_id}"
            )
        if tree.object_instance_graph_id != expected_object_instance_graph_id:
            raise OigCommitValidationError(
                f"{tctx.path}.object_instance_graph_id: expected {expected_object_instance_graph_id}, got {tree.object_instance_graph_id}"
            )

        if tree.change is None:
            raise OigCommitValidationError(f"{tctx.path}.change: required (root Change envelope)")
        if tree.change_id != tree.change.id:
            raise OigCommitValidationError(
                f"{tctx.path}.change_id: mismatch (field={tree.change_id} rel={tree.change.id})"
            )
        _validate_change(tree.change, ctx=tctx.child("change"))

        if tree.change.type != ChangeType.update:
            raise OigCommitValidationError(f"{tctx.path}.change.type: root must be UPDATE, got {tree.change.type}")
        if tree.change.change_deltas:
            raise OigCommitValidationError(f"{tctx.path}.change.change_deltas: root must not carry deltas (v0)")

        key = (tree.type, tree.change_id)
        if key in seen_root_keys:
            raise OigCommitValidationError(f"{tctx.path}: duplicate root change key {key}")
        seen_root_keys.add(key)

        if tree.type == ObjectInstanceGraphChangeType.object_instance:
            if not tree.class_instance_changes:
                raise OigCommitValidationError(
                    f"{tctx.path}.class_instance_changes: must be non-empty for OBJECT_INSTANCE"
                )
            if tree.class_instance_relationship_changes:
                raise OigCommitValidationError(
                    f"{tctx.path}.class_instance_relationship_changes: must be empty for OBJECT_INSTANCE"
                )
            _validate_class_instance_changes(tree.class_instance_changes, ctx=tctx.child("class_instance_changes"))
            continue

        if tree.type == ObjectInstanceGraphChangeType.object_instance_relationship:
            if not tree.class_instance_relationship_changes:
                raise OigCommitValidationError(
                    f"{tctx.path}.class_instance_relationship_changes: must be non-empty for OBJECT_INSTANCE_RELATIONSHIP"
                )
            if tree.class_instance_changes:
                raise OigCommitValidationError(
                    f"{tctx.path}.class_instance_changes: must be empty for OBJECT_INSTANCE_RELATIONSHIP"
                )
            _validate_relationship_changes(
                tree.class_instance_relationship_changes,
                ctx=tctx.child("class_instance_relationship_changes"),
            )
            continue

        raise OigCommitValidationError(f"{tctx.path}.type: unsupported {tree.type}")


def _validate_change(change: Change, *, ctx: _Ctx) -> None:
    if change.id is None:
        raise OigCommitValidationError(f"{ctx.path}.id: missing")
    if change.type not in (ChangeType.create, ChangeType.update, ChangeType.delete):
        raise OigCommitValidationError(f"{ctx.path}.type: invalid {change.type}")
    if change.created_at is None:
        raise OigCommitValidationError(f"{ctx.path}.created_at: required")
    if change.created_at.tzinfo is None or change.created_at.utcoffset() is None:
        raise OigCommitValidationError(f"{ctx.path}.created_at: timezone-aware UTC required")
    if change.created_at.utcoffset() != timedelta(0):
        raise OigCommitValidationError(f"{ctx.path}.created_at: must be UTC")

    seen_props: set[str] = set()
    for idx, d in enumerate(change.change_deltas):
        dctx = ctx.child(f"change_deltas[{idx}]")
        _validate_change_delta(d, ctx=dctx, expected_change_id=change.id)
        if d.property is None:
            raise OigCommitValidationError(f"{dctx.path}.property: required")
        if d.property in seen_props:
            raise OigCommitValidationError(f"{dctx.path}.property: duplicate {d.property!r}")
        seen_props.add(d.property)


def _validate_change_delta(delta: ChangeDelta, *, ctx: _Ctx, expected_change_id: UUID) -> None:
    if delta.change_id != expected_change_id:
        raise OigCommitValidationError(f"{ctx.path}.change_id: expected {expected_change_id}, got {delta.change_id}")
    if delta.kind != ChangeDeltaKind.scalar_set:
        raise OigCommitValidationError(f"{ctx.path}.kind: unsupported {delta.kind} (v0 expects SCALAR_SET)")
    payload = delta.payload
    if not isinstance(payload, dict):
        raise OigCommitValidationError(f"{ctx.path}.payload: expected dict-backed Json, got {type(payload).__name__}")
    if "value" not in payload:
        raise OigCommitValidationError(f"{ctx.path}.payload: missing 'value' key")


def _require_scalar_set(change: Change, *, ctx: _Ctx, prop: str) -> None:
    for d in change.change_deltas:
        if d.kind == ChangeDeltaKind.scalar_set and d.property == prop:
            return
    raise OigCommitValidationError(f"{ctx.path}: missing required SCALAR_SET delta {prop!r}")


def _require_only_props(change: Change, *, ctx: _Ctx, allowed: set[str]) -> None:
    for idx, d in enumerate(change.change_deltas):
        if d.property not in allowed:
            raise OigCommitValidationError(
                f"{ctx.path}.change_deltas[{idx}].property: unsupported {d.property!r}; allowed={sorted(allowed)}"
            )


def _validate_class_instance_changes(changes: Iterable[ClassInstanceChange], *, ctx: _Ctx) -> None:
    seen_ci: set[UUID] = set()
    for idx, ci_change in enumerate(changes):
        cctx = ctx.child(f"[{idx}]")
        if ci_change.class_instance_id in seen_ci:
            raise OigCommitValidationError(f"{cctx.path}.class_instance_id: duplicate {ci_change.class_instance_id}")
        seen_ci.add(ci_change.class_instance_id)

        if ci_change.change is None:
            raise OigCommitValidationError(f"{cctx.path}.change: required")
        if ci_change.change_id != ci_change.change.id:
            raise OigCommitValidationError(
                f"{cctx.path}.change_id: mismatch (field={ci_change.change_id} rel={ci_change.change.id})"
            )
        _validate_change(ci_change.change, ctx=cctx.child("change"))

        op = ci_change.change.type
        if op == ChangeType.create:
            _require_only_props(
                ci_change.change,
                ctx=cctx.child("change"),
                allowed={"class_config_id", "source_object_id"},
            )
            _require_scalar_set(ci_change.change, ctx=cctx.child("change"), prop="class_config_id")
            _require_scalar_set(ci_change.change, ctx=cctx.child("change"), prop="source_object_id")
        elif op == ChangeType.delete:
            if ci_change.change.change_deltas:
                raise OigCommitValidationError(f"{cctx.path}.change.change_deltas: DELETE must not carry deltas (v0)")
            if ci_change.attribute_changes:
                raise OigCommitValidationError(f"{cctx.path}.attribute_changes: DELETE must not carry children (v0)")
        elif op == ChangeType.update:
            _require_only_props(
                ci_change.change,
                ctx=cctx.child("change"),
                allowed={"class_config_id", "source_object_id"},
            )

        _validate_attribute_changes(
            changes=ci_change.attribute_changes,
            ctx=cctx.child("attribute_changes"),
            parent=ci_change,
        )


def _validate_attribute_changes(*, changes: Iterable[AttributeChange], ctx: _Ctx, parent: ClassInstanceChange) -> None:
    seen_attr: set[UUID] = set()
    for idx, attr_change in enumerate(changes):
        actx = ctx.child(f"[{idx}]")
        if attr_change.attribute_id in seen_attr:
            raise OigCommitValidationError(f"{actx.path}.attribute_id: duplicate {attr_change.attribute_id}")
        seen_attr.add(attr_change.attribute_id)

        if attr_change.class_instance_change_id != parent.id:
            raise OigCommitValidationError(
                f"{actx.path}.class_instance_change_id: expected {parent.id}, got {attr_change.class_instance_change_id}"
            )

        if attr_change.change is None:
            raise OigCommitValidationError(f"{actx.path}.change: required")
        if attr_change.change_id is not None and attr_change.change_id != attr_change.change.id:
            raise OigCommitValidationError(
                f"{actx.path}.change_id: mismatch (field={attr_change.change_id} rel={attr_change.change.id})"
            )
        _validate_change(attr_change.change, ctx=actx.child("change"))

        op = attr_change.change.type
        if op == ChangeType.create:
            _require_only_props(
                attr_change.change,
                ctx=actx.child("change"),
                allowed={"attribute_config_id"},
            )
            _require_scalar_set(attr_change.change, ctx=actx.child("change"), prop="attribute_config_id")
        elif op == ChangeType.delete:
            if attr_change.change.change_deltas:
                raise OigCommitValidationError(f"{actx.path}.change.change_deltas: DELETE must not carry deltas (v0)")
            if attr_change.value_root_change is not None:
                raise OigCommitValidationError(f"{actx.path}.value_root_change: DELETE must not carry children (v0)")
        elif op == ChangeType.update:
            _require_only_props(
                attr_change.change,
                ctx=actx.child("change"),
                allowed={"attribute_config_id"},
            )

        if attr_change.value_root_change is not None:
            if (
                attr_change.value_root_change_id is not None
                and attr_change.value_root_change_id != attr_change.value_root_change.id
            ):
                raise OigCommitValidationError(
                    f"{actx.path}.value_root_change_id: mismatch (field={attr_change.value_root_change_id} rel={attr_change.value_root_change.id})"
                )
            _validate_attribute_value_change(
                change=attr_change.value_root_change,
                ctx=actx.child("value_root_change"),
            )


def _validate_attribute_value_change(*, change: AttributeValueChange, ctx: _Ctx) -> None:
    if change.change is None:
        raise OigCommitValidationError(f"{ctx.path}.change: required")
    if change.change_id is not None and change.change_id != change.change.id:
        raise OigCommitValidationError(
            f"{ctx.path}.change_id: mismatch (field={change.change_id} rel={change.change.id})"
        )
    _validate_change(change.change, ctx=ctx.child("change"))

    op = change.change.type
    if op in (ChangeType.create, ChangeType.update):
        _require_only_props(
            change.change,
            ctx=ctx.child("change"),
            allowed={"primitive_value", "enum_option_id", "class_instance_id", "inline_value_instance_id"},
        )
    elif op == ChangeType.delete and change.change.change_deltas:
        raise OigCommitValidationError(f"{ctx.path}.change.change_deltas: DELETE must not carry deltas (v0)")
    if op == ChangeType.delete and change.attribute_value_link_changes:
        raise OigCommitValidationError(f"{ctx.path}.attribute_value_link_changes: DELETE must not carry children (v0)")

    seen_link: set[UUID] = set()
    for idx, link_change in enumerate(change.attribute_value_link_changes):
        lctx = ctx.child(f"attribute_value_link_changes[{idx}]")
        if link_change.attribute_value_change_id != change.id:
            raise OigCommitValidationError(
                f"{lctx.path}.attribute_value_change_id: expected {change.id}, got {link_change.attribute_value_change_id}"
            )
        if link_change.attribute_value_link_id in seen_link:
            raise OigCommitValidationError(
                f"{lctx.path}.attribute_value_link_id: duplicate {link_change.attribute_value_link_id}"
            )
        seen_link.add(link_change.attribute_value_link_id)
        _validate_attribute_value_link_change(change=link_change, ctx=lctx)


def _validate_attribute_value_link_change(*, change: AttributeValueLinkChange, ctx: _Ctx) -> None:
    if change.change is None:
        raise OigCommitValidationError(f"{ctx.path}.change: required")
    if change.change_id is not None and change.change_id != change.change.id:
        raise OigCommitValidationError(
            f"{ctx.path}.change_id: mismatch (field={change.change_id} rel={change.change.id})"
        )
    _validate_change(change.change, ctx=ctx.child("change"))

    op = change.change.type
    if op in (ChangeType.create, ChangeType.update):
        allowed_props = {"role", "position", "identity_key"}
        for d in change.change.change_deltas:
            if d.property not in allowed_props:
                raise OigCommitValidationError(
                    f"{ctx.path}.change.change_deltas: unsupported property {d.property!r} for AttributeValueLinkChange"
                )

    if op == ChangeType.create:
        _require_scalar_set(change.change, ctx=ctx.child("change"), prop="role")
        if change.child_attribute_value_change is None:
            raise OigCommitValidationError(f"{ctx.path}.child_attribute_value_change: required for {op}")
        if (
            change.child_attribute_value_change_id is not None
            and change.child_attribute_value_change_id != change.child_attribute_value_change.id
        ):
            raise OigCommitValidationError(
                f"{ctx.path}.child_attribute_value_change_id: mismatch "
                f"(field={change.child_attribute_value_change_id} rel={change.child_attribute_value_change.id})"
            )
        _validate_attribute_value_change(
            change=change.child_attribute_value_change,
            ctx=ctx.child("child_attribute_value_change"),
        )
        return

    if op == ChangeType.update:
        # UPDATE is a carrier for child value updates; link slot identity is immutable (v0).
        if change.change.change_deltas:
            raise OigCommitValidationError(f"{ctx.path}.change.change_deltas: UPDATE must not carry deltas (v0)")
        if change.child_attribute_value_change is None:
            raise OigCommitValidationError(f"{ctx.path}.child_attribute_value_change: required for UPDATE")
        if (
            change.child_attribute_value_change_id is not None
            and change.child_attribute_value_change_id != change.child_attribute_value_change.id
        ):
            raise OigCommitValidationError(
                f"{ctx.path}.child_attribute_value_change_id: mismatch "
                f"(field={change.child_attribute_value_change_id} rel={change.child_attribute_value_change.id})"
            )
        _validate_attribute_value_change(
            change=change.child_attribute_value_change,
            ctx=ctx.child("child_attribute_value_change"),
        )
        return

    if op == ChangeType.delete:
        if change.child_attribute_value_change is not None:
            raise OigCommitValidationError(f"{ctx.path}.child_attribute_value_change: must be None for DELETE (v0)")
        if change.change.change_deltas:
            raise OigCommitValidationError(f"{ctx.path}.change.change_deltas: DELETE link must not carry deltas (v0)")
        return

    raise OigCommitValidationError(f"{ctx.path}.change.type: unsupported {op}")


def _validate_relationship_changes(changes: Iterable[ClassInstanceRelationshipChange], *, ctx: _Ctx) -> None:
    seen: set[tuple[UUID, UUID, UUID]] = set()
    for idx, rel_change in enumerate(changes):
        rctx = ctx.child(f"[{idx}]")
        if rel_change.change is None:
            raise OigCommitValidationError(f"{rctx.path}.change: required")
        if rel_change.change_id is not None and rel_change.change_id != rel_change.change.id:
            raise OigCommitValidationError(
                f"{rctx.path}.change_id: mismatch (field={rel_change.change_id} rel={rel_change.change.id})"
            )
        _validate_change(rel_change.change, ctx=rctx.child("change"))

        op = rel_change.change.type
        if op not in (ChangeType.create, ChangeType.delete):
            raise OigCommitValidationError(f"{rctx.path}.change.type: unsupported {op} (v0)")
        if rel_change.change.change_deltas:
            raise OigCommitValidationError(
                f"{rctx.path}.change.change_deltas: relationships must not carry deltas (v0)"
            )

        key = (
            rel_change.class_config_relationship_id,
            rel_change.source_class_instance_id,
            rel_change.target_class_instance_id,
        )
        if key in seen:
            raise OigCommitValidationError(f"{rctx.path}: duplicate relationship key {key}")
        seen.add(key)


__all__ = [
    "OigCommitValidationError",
    "validate_object_instance_graph_commit",
]
