from __future__ import annotations

import copy
from datetime import datetime, timezone
import os
from collections.abc import Iterable
from uuid import UUID

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_history_ontology.commit.commit_enums import CommitStatus
from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_meta.graph.config.lane.telemetry import (
    SeedTimings,
    maybe_metric,
)
from aware_orm.session.autobind import disable_autobind

SYSTEM_ACTOR_ID = UUID(int=0)
SEED_CREATED_AT = datetime(1970, 1, 1, tzinfo=timezone.utc)
OCG_DELTA_HINT_VERSION = 1
DEFAULT_OCG_SOURCE_LANGUAGE = CodeLanguage("aware")
DEFAULT_OCG_COMMIT_STATUS = CommitStatus("local")


def clone_object_instance_graph_for_validation(
    graph: ObjectInstanceGraph,
    *,
    changes: Iterable[ObjectInstanceGraphChange] | None = None,
    timings: SeedTimings | None = None,
    metric_prefix: str = "ocg_delta_validation",
) -> ObjectInstanceGraph:
    """Clone OIG for apply+hash validation with a selective copy-on-write rail."""
    prefix = (metric_prefix or "").strip() or "ocg_delta_validation"

    changed_class_instance_ids: set[UUID] = set()
    has_relationship_changes = False
    if changes is not None:
        for change_tree in changes:
            for ci_change in change_tree.class_instance_changes or []:
                changed_class_instance_ids.add(ci_change.class_instance_id)
            if change_tree.class_instance_relationship_changes:
                has_relationship_changes = True

    if changed_class_instance_ids or has_relationship_changes:
        try:
            with disable_autobind():
                cloned = graph.model_copy(deep=False)
            cloned.class_instances = [
                copy.deepcopy(ci) if ci.id in changed_class_instance_ids else ci
                for ci in graph.class_instances
            ]
            # Relationship changes only create/delete rows; shallow-copy list is sufficient.
            cloned.class_instance_relationships = list(graph.class_instance_relationships)
            for ci in cloned.class_instances:
                if ci.id == cloned.root_class_instance_id:
                    cloned.root_class_instance = ci
                    break
            maybe_metric(timings, f"{prefix}_clone_mode", "selective")
            maybe_metric(
                timings,
                f"{prefix}_changed_class_instances",
                len(changed_class_instance_ids),
            )
            maybe_metric(
                timings,
                f"{prefix}_has_relationship_changes",
                has_relationship_changes,
            )
            return cloned
        except Exception:
            pass

    try:
        cloned = copy.deepcopy(graph)
        maybe_metric(timings, f"{prefix}_clone_mode", "deepcopy")
        return cloned
    except Exception:
        cloned = graph.model_copy(deep=True)
        maybe_metric(timings, f"{prefix}_clone_mode", "model_copy_deep")
        return cloned


def bool_env_default_true(name: str) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    if raw in {"0", "false", "no", "off"}:
        return False
    return True
