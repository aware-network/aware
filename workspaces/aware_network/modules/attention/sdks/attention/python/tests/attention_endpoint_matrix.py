from __future__ import annotations

from dataclasses import dataclass


ATTENTION_API_PACKAGE_NAME = "attention-service-api"
ENVIRONMENT_API_PACKAGE_NAME = "environment-service-api"


@dataclass(frozen=True, slots=True)
class AttentionSdkEndpointProofRow:
    endpoint_ref: str
    sdk_surface: str
    request_model_count: int
    status: str
    proof: str


ATTENTION_ENDPOINT_MATRIX: tuple[AttentionSdkEndpointProofRow, ...] = (
    AttentionSdkEndpointProofRow(
        "attention.activate_section_observable.activate_section_observable",
        "AttentionSdkClient.activate_section_observable",
        2,
        "green",
        "activates one section-scoped observable through Attention-owned focus state",
    ),
    AttentionSdkEndpointProofRow(
        "attention.get_runtime_mount.get_runtime_mount",
        "AttentionSdkClient.get_runtime_mount",
        1,
        "green",
        "resolves layout sections and active observable snapshots for a runtime mount",
    ),
    AttentionSdkEndpointProofRow(
        "attention.get_section_state.get_section_state",
        "AttentionSdkClient.get_section_state",
        1,
        "green",
        "reads Attention section -> FocusScope -> observable state",
    ),
    AttentionSdkEndpointProofRow(
        "attention.get_focus_scope_commits.get_focus_scope_commits",
        "AttentionSdkClient.get_focus_scope_commits",
        2,
        "green",
        "reads OIG commit pointers observed by one Attention focus scope",
    ),
    AttentionSdkEndpointProofRow(
        "attention.describe_attention_session.describe_attention_session",
        "AttentionSdkClient.describe_attention_session",
        1,
        "green",
        "reads one AttentionSession and active layout/section/transition pins",
    ),
    AttentionSdkEndpointProofRow(
        "attention.start_attention_session.start_attention_session",
        "AttentionSdkClient.start_attention_session",
        1,
        "green",
        "constructs one AttentionSession over verified Identity Session truth",
    ),
    AttentionSdkEndpointProofRow(
        "attention.mount_attention_session_layout.mount_attention_session_layout",
        "AttentionSdkClient.mount_attention_session_layout",
        1,
        "green",
        "mounts one layout on an existing committed AttentionSession lane",
    ),
    AttentionSdkEndpointProofRow(
        "attention.mount_attention_session_section.mount_attention_session_section",
        "AttentionSdkClient.mount_attention_session_section",
        1,
        "green",
        "mounts one section anchor on an existing committed session layout",
    ),
    AttentionSdkEndpointProofRow(
        "attention.apply_session_layout_transition.apply_session_layout_transition",
        "AttentionSdkClient.apply_session_layout_transition",
        1,
        "green",
        "commits one atomic typed full-vector layout transition with conflict reconciliation",
    ),
    AttentionSdkEndpointProofRow(
        "attention.apply_session_layout_topology_transition.apply_session_layout_topology_transition",
        "AttentionSdkClient.apply_session_layout_topology_transition",
        1,
        "green",
        "commits one atomic active-membership/order vector with conflict reconciliation",
    ),
    AttentionSdkEndpointProofRow(
        "attention.describe_attention_transition.describe_attention_transition",
        "AttentionSdkClient.describe_attention_transition",
        1,
        "green",
        "reads one AttentionFocusTransition plus its parent session chain",
    ),
    AttentionSdkEndpointProofRow(
        "attention.list_attention_transitions.list_attention_transitions",
        "AttentionSdkClient.list_attention_transitions",
        1,
        "green",
        "lists AttentionFocusTransition pins by session, section, focus, or kind",
    ),
    AttentionSdkEndpointProofRow(
        "attention.validate_attention_transition.validate_attention_transition",
        "AttentionSdkClient.validate_attention_transition",
        1,
        "green",
        "validates one AttentionFocusTransition against expected session coordinates",
    ),
    AttentionSdkEndpointProofRow(
        "attention.watch_runtime_mount.watch_runtime_mount",
        "generated stream_watch_runtime_mount",
        2,
        "green",
        "streams typed runtime-mount snapshot events through generated API streaming",
    ),
)
