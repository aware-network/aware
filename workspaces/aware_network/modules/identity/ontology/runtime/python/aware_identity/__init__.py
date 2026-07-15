"""Aware identity domain helpers.

This package intentionally avoids duplicating canonical `.aware` models.
Authoritative Identity/Actor/Role ORM facades are generated under:

- `aware_identity_ontology.*`
"""

from .representation import (
    CommitAttributionEntry,
    build_commit_attribution_entries,
    parse_actor_label_mappings,
    render_commit_timeline_lines,
    resolve_actor_labels,
)

__all__ = [
    "CommitAttributionEntry",
    "build_commit_attribution_entries",
    "parse_actor_label_mappings",
    "render_commit_timeline_lines",
    "resolve_actor_labels",
]
