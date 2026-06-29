"""Compatibility facade for compiler-owned OCG commit rail helpers.

The canonical owner for OCG-via-OIG lane policy is `aware_meta.graph.config.lane`.
This module preserves the historical import surface while callers migrate.
"""

from __future__ import annotations

from aware_meta.graph.config.lane import (
    GraphIdentitySeedError,
    GraphIdentitySeedPlan,
    OCGDeltaCommitPlan,
    OCGSeedPlan,
    OcgLaneCommitError,
    OcgSeedError,
    build_ocg_seed_plan,
    commit_ocg_delta_to_lane,
    ensure_graph_identity_seeded_lane,
    ensure_ocg_seeded_lane,
    resolve_ocg_seed_projection_context,
    resolve_ocg_seed_schema_view,
)
from aware_meta.graph.config.lane.delta_support import (
    OigFingerprintDiffScope,
    collect_stale_schema_owned_type_descriptor_mismatches,
    expand_delta_scoped_candidate_ids,
    is_volatile_source_reference_attribute_name,
    load_post_oig_diff_index_sidecar,
    load_pre_oig_from_snapshot_fast_path,
    oig_diff_index_post_sidecar_path,
    oig_diff_index_sidecar_path,
    oig_fingerprint_diff_scope,
    should_skip_oig_scoped_diff_by_relationship_scope,
    strip_volatile_source_reference_attrs_from_oig,
    write_post_oig_diff_index_sidecar,
    write_pre_oig_diff_index_sidecar,
)
from aware_meta.graph.instance.scoped_index import build_oig_graph_diff_index

_collect_stale_schema_owned_type_descriptor_mismatches = (
    collect_stale_schema_owned_type_descriptor_mismatches
)
_expand_delta_scoped_candidate_ids = expand_delta_scoped_candidate_ids
_is_volatile_source_reference_attribute_name = is_volatile_source_reference_attribute_name
_load_pre_oig_from_snapshot_fast_path = load_pre_oig_from_snapshot_fast_path
_oig_fingerprint_diff_scope = oig_fingerprint_diff_scope
_should_skip_oig_scoped_diff_by_relationship_scope = (
    should_skip_oig_scoped_diff_by_relationship_scope
)
_strip_volatile_source_reference_attrs_from_oig = (
    strip_volatile_source_reference_attrs_from_oig
)
_write_post_oig_diff_index_sidecar = write_post_oig_diff_index_sidecar
_write_pre_oig_diff_index_sidecar = write_pre_oig_diff_index_sidecar

__all__ = [
    "GraphIdentitySeedError",
    "GraphIdentitySeedPlan",
    "OCGDeltaCommitPlan",
    "OCGSeedPlan",
    "OigFingerprintDiffScope",
    "OcgLaneCommitError",
    "OcgSeedError",
    "build_ocg_seed_plan",
    "build_oig_graph_diff_index",
    "commit_ocg_delta_to_lane",
    "ensure_graph_identity_seeded_lane",
    "ensure_ocg_seeded_lane",
    "expand_delta_scoped_candidate_ids",
    "load_post_oig_diff_index_sidecar",
    "load_pre_oig_from_snapshot_fast_path",
    "oig_diff_index_post_sidecar_path",
    "oig_diff_index_sidecar_path",
    "oig_fingerprint_diff_scope",
    "resolve_ocg_seed_projection_context",
    "resolve_ocg_seed_schema_view",
    "should_skip_oig_scoped_diff_by_relationship_scope",
    "write_post_oig_diff_index_sidecar",
    "write_pre_oig_diff_index_sidecar",
]
