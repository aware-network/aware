from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Attention Ontology
from aware_attention_ontology.session.attention_layout_topology_transition import AttentionLayoutTopologyTransition
from aware_attention_ontology.session.attention_layout_transition import AttentionLayoutTransition
from aware_attention_ontology.session.attention_session_layout import AttentionSessionLayout
from aware_attention_ontology.session.attention_session_section import AttentionSessionSection

# Code
from aware_code.types import JsonObject

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_attention_ontology.session.attention_layout_transition_section import (
    AttentionLayoutTransitionSection,
)
from aware_attention_ontology.session.attention_layout_topology_transition_section import (
    AttentionLayoutTopologyTransitionSection,
)
from aware_attention_ontology.stable_ids import (
    stable_attention_layout_topology_transition_id,
    stable_attention_layout_transition_id,
    stable_attention_session_layout_id,
)

# --- AWARE: USER_IMPORTS END


async def attach_section(
    attention_session_layout: AttentionSessionLayout,
    layout_section_id: UUID,
    section_id: UUID,
    section_key: str | None = None,
    order: int = 0,
    is_active: bool = True,
) -> AttentionSessionSection:
    """
    Add one session-local section state row.

    Contract:
    - The row is grounded by LayoutSection and Section.
    - Focus transition history must hang under this section row.
    """

    # --- AWARE: LOGIC START attach_section
    session_section = await AttentionSessionSection.create_via_attention_session_layout(
        attention_session_layout_id=attention_session_layout.id,
        layout_section_id=layout_section_id,
        section_id=section_id,
        section_key=section_key,
        order=order,
        is_active=is_active,
    )
    if all(existing.id != session_section.id for existing in attention_session_layout.sections):
        attention_session_layout.sections.append(session_section)
    if is_active:
        attention_session_layout.active_section = session_section
    return session_section
    # --- AWARE: LOGIC END attach_section


async def set_active_section(
    attention_session_layout: AttentionSessionLayout, attention_session_section_id: UUID
) -> AttentionSessionSection:
    """
    Select the active session-local section.
    """

    # --- AWARE: LOGIC START set_active_section
    session_section = next(
        (existing for existing in attention_session_layout.sections if existing.id == attention_session_section_id),
        None,
    )
    if session_section is None:
        session_section = AttentionSessionSection.by_id_cached(attention_session_section_id)
    if session_section is None:
        raise RuntimeError(
            "AttentionSessionLayout.set_active_section requires a known session section: "
            f"attention_session_section_id={attention_session_section_id}"
        )
    attention_session_layout.active_section = session_section
    return session_section
    # --- AWARE: LOGIC END set_active_section


async def apply_topology_transition(
    attention_session_layout: AttentionSessionLayout,
    client_intent_id: str,
    section_states_json: JsonObject,
    expected_previous_topology_transition_id: UUID | None = None,
    transition_kind: str = "topology",
    source_kind: str | None = None,
    source_ref: str | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> AttentionLayoutTopologyTransition:
    """
    Atomically append one immutable full-vector layout topology transition.

    Contract:
    - AttentionSessionSection rows are stable admitted anchors.
    - The complete ordered active membership is supplied on every intent.
    - Omitted anchors remain available to history and may be re-added.
    - expected_previous_topology_transition_id is an exact active-head CAS.
    - Repeating the active client intent with the identical payload is a
      no-op; reusing it with different content fails closed.
    """

    # --- AWARE: LOGIC START apply_topology_transition
    def _validation_error(detail: str) -> ValueError:
        return ValueError(
            "AttentionSessionLayout.apply_topology_transition rejected the " "full-vector intent: " + detail
        )

    def _required_uuid(value: object, *, field: str) -> UUID:
        if isinstance(value, UUID):
            return value
        if not isinstance(value, str) or not value.strip():
            raise _validation_error(f"{field} must be a UUID string")
        try:
            return UUID(value)
        except ValueError as exc:
            raise _validation_error(f"{field} must be a UUID string") from exc

    normalized_intent_id = (client_intent_id or "").strip().casefold()
    if not normalized_intent_id:
        raise _validation_error("client_intent_id must be non-empty")
    normalized_transition_kind = (transition_kind or "").strip()
    if not normalized_transition_kind:
        raise _validation_error("transition_kind must be non-empty")
    normalized_source_kind = (source_kind or "").strip() or None
    normalized_source_ref = (source_ref or "").strip() or None
    normalized_metadata = JsonObject(metadata_json or {})

    if not isinstance(section_states_json, dict):
        raise _validation_error("section_states_json must be an object")
    if set(section_states_json) != {"sections"}:
        raise _validation_error("section_states_json must contain exactly the 'sections' field")
    raw_sections = section_states_json["sections"]
    if not isinstance(raw_sections, list) or not raw_sections:
        raise _validation_error("section_states_json.sections must be a non-empty list")

    admitted_section_ids = [section.id for section in attention_session_layout.sections]
    admitted_section_id_set = set(admitted_section_ids)
    if not admitted_section_ids:
        raise _validation_error("the session layout must admit at least one section anchor")
    if len(admitted_section_ids) != len(admitted_section_id_set):
        raise RuntimeError(
            "AttentionSessionLayout contains duplicate admitted section ids; " "topology transition cannot proceed"
        )

    normalized_rows: list[tuple[UUID, int]] = []
    seen_section_ids: set[UUID] = set()
    seen_orders: set[int] = set()
    for row_index, raw_row in enumerate(raw_sections):
        if not isinstance(raw_row, dict):
            raise _validation_error(f"sections[{row_index}] must be an object")
        if set(raw_row) != {"attention_session_section_id", "order"}:
            raise _validation_error(
                f"sections[{row_index}] must contain exactly " "['attention_session_section_id', 'order']"
            )
        section_id = _required_uuid(
            raw_row["attention_session_section_id"],
            field=f"sections[{row_index}].attention_session_section_id",
        )
        order = raw_row["order"]
        if type(order) is not int or order < 0:
            raise _validation_error(f"sections[{row_index}].order must be a non-negative integer")
        if section_id in seen_section_ids:
            raise _validation_error(f"duplicate admitted section id: {section_id}")
        if order in seen_orders:
            raise _validation_error(f"duplicate section order: {order}")
        if section_id not in admitted_section_id_set:
            raise _validation_error(f"unknown admitted section id: {section_id}")
        seen_section_ids.add(section_id)
        seen_orders.add(order)
        normalized_rows.append((section_id, order))

    expected_orders = set(range(len(normalized_rows)))
    if seen_orders != expected_orders:
        raise _validation_error(f"section orders must be contiguous 0..{len(normalized_rows) - 1}")
    active_section = attention_session_layout.active_section
    active_section_id = active_section.id if active_section is not None else attention_session_layout.active_section_id
    if active_section_id is not None and active_section_id not in seen_section_ids:
        raise _validation_error(
            "the current active section must survive the topology transition; " "select a surviving section first"
        )
    normalized_rows.sort(key=lambda row: row[1])

    topology_transition_id = stable_attention_layout_topology_transition_id(
        attention_session_layout_id=attention_session_layout.id,
        client_intent_id=normalized_intent_id,
    )
    active_transition = attention_session_layout.active_topology_transition
    active_transition_id = (
        active_transition.id
        if active_transition is not None
        else attention_session_layout.active_topology_transition_id
    )
    existing_transition = next(
        (
            existing
            for existing in attention_session_layout.topology_transitions
            if existing.id == topology_transition_id
        ),
        None,
    )
    if existing_transition is None:
        existing_transition = AttentionLayoutTopologyTransition.by_id_cached(topology_transition_id)
    if existing_transition is not None:
        if active_transition_id != existing_transition.id:
            raise _validation_error(
                "client_intent_id already identifies a non-active historical " "topology transition"
            )
        existing_rows = sorted(
            [(state.attention_session_section_id, state.order) for state in existing_transition.section_states],
            key=lambda row: row[1],
        )
        if (
            existing_transition.previous_topology_transition_id != expected_previous_topology_transition_id
            or existing_transition.client_intent_id != normalized_intent_id
            or existing_transition.transition_kind != normalized_transition_kind
            or existing_transition.source_kind != normalized_source_kind
            or existing_transition.source_ref != normalized_source_ref
            or dict(existing_transition.metadata_json or {}) != dict(normalized_metadata)
            or existing_rows != normalized_rows
        ):
            raise _validation_error("client_intent_id collides with a different active topology " "transition payload")
        return existing_transition

    if expected_previous_topology_transition_id != active_transition_id:
        raise _validation_error(
            "stale expected previous topology transition id; "
            f"have={expected_previous_topology_transition_id} "
            f"expected={active_transition_id}"
        )
    if active_transition_id is not None and active_transition is None:
        active_transition = AttentionLayoutTopologyTransition.by_id_cached(active_transition_id)
        if active_transition is None:
            raise RuntimeError("AttentionSessionLayout active topology transition is not " "hydrated or cached")
    sequence = 0 if active_transition is None else active_transition.sequence + 1
    topology_transition = await AttentionLayoutTopologyTransition.create_via_attention_session_layout(
        attention_session_layout_id=attention_session_layout.id,
        client_intent_id=normalized_intent_id,
        previous_topology_transition_id=active_transition_id,
        sequence=sequence,
        transition_kind=normalized_transition_kind,
        source_kind=normalized_source_kind,
        source_ref=normalized_source_ref,
        metadata_json=normalized_metadata,
    )
    for section_id, order in normalized_rows:
        state = await AttentionLayoutTopologyTransitionSection.create_via_attention_layout_topology_transition(
            attention_layout_topology_transition_id=topology_transition.id,
            attention_session_section_id=section_id,
            order=order,
        )
        topology_transition.section_states.append(state)
    attention_session_layout.topology_transitions.append(topology_transition)
    attention_session_layout.active_topology_transition = topology_transition
    attention_session_layout.active_layout_transition = None
    return topology_transition
    # --- AWARE: LOGIC END apply_topology_transition


async def apply_layout_transition(
    attention_session_layout: AttentionSessionLayout,
    client_intent_id: str,
    section_states_json: JsonObject,
    expected_previous_layout_transition_id: UUID | None = None,
    topology_transition_id: UUID | None = None,
    transition_kind: str = "layout",
    source_kind: str | None = None,
    source_ref: str | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> AttentionLayoutTransition:
    """
    Atomically append one immutable full-vector shared-layout transition.

    Contract:
    - The invocation envelope is validated before construction and is not
      persisted as shared layout authority.
    - One typed state row is committed for every mounted session section.
    - expected_previous_layout_transition_id is an exact active-head CAS.
    - topology_transition_id must exactly pin the active explicit topology;
      legacy fixed layouts use a null topology pin.
    - Repeating the active client intent with the identical payload is a
      no-op; reusing it with different content fails closed.
    """

    # --- AWARE: LOGIC START apply_layout_transition
    def _validation_error(detail: str) -> ValueError:
        return ValueError("AttentionSessionLayout.apply_layout_transition rejected the full-vector intent: " + detail)

    def _required_uuid(value: object, *, field: str) -> UUID:
        if isinstance(value, UUID):
            return value
        if not isinstance(value, str) or not value.strip():
            raise _validation_error(f"{field} must be a UUID string")
        try:
            return UUID(value)
        except ValueError as exc:
            raise _validation_error(f"{field} must be a UUID string") from exc

    normalized_intent_id = (client_intent_id or "").strip().casefold()
    if not normalized_intent_id:
        raise _validation_error("client_intent_id must be non-empty")

    normalized_transition_kind = (transition_kind or "").strip()
    if not normalized_transition_kind:
        raise _validation_error("transition_kind must be non-empty")
    normalized_source_kind = (source_kind or "").strip() or None
    normalized_source_ref = (source_ref or "").strip() or None
    normalized_metadata = JsonObject(metadata_json or {})

    if not isinstance(section_states_json, dict):
        raise _validation_error("section_states_json must be an object")
    if set(section_states_json) != {"sections"}:
        raise _validation_error("section_states_json must contain exactly the 'sections' field")
    raw_sections = section_states_json["sections"]
    if not isinstance(raw_sections, list):
        raise _validation_error("section_states_json.sections must be a list")

    admitted_section_ids = [section.id for section in attention_session_layout.sections]
    admitted_section_id_set = set(admitted_section_ids)
    if not admitted_section_ids:
        raise _validation_error("the session layout must mount at least one section")
    if len(admitted_section_ids) != len(admitted_section_id_set):
        raise RuntimeError(
            "AttentionSessionLayout contains duplicate mounted section ids; layout transition cannot proceed"
        )
    active_topology_transition = attention_session_layout.active_topology_transition
    active_topology_transition_id = (
        active_topology_transition.id
        if active_topology_transition is not None
        else attention_session_layout.active_topology_transition_id
    )
    if topology_transition_id != active_topology_transition_id:
        raise _validation_error(
            "topology_transition_id must exactly pin the active topology; "
            f"have={topology_transition_id} "
            f"expected={active_topology_transition_id}"
        )
    if active_topology_transition_id is not None and active_topology_transition is None:
        active_topology_transition = AttentionLayoutTopologyTransition.by_id_cached(active_topology_transition_id)
        if active_topology_transition is None:
            raise RuntimeError("AttentionSessionLayout active topology transition is not " "hydrated or cached")
    if active_topology_transition is None:
        mounted_section_ids = admitted_section_ids
    else:
        mounted_section_ids = [
            state.attention_session_section_id
            for state in sorted(
                active_topology_transition.section_states,
                key=lambda state: state.order,
            )
        ]
        if not mounted_section_ids:
            raise RuntimeError("AttentionSessionLayout active topology transition has no " "section membership")
        if not set(mounted_section_ids).issubset(admitted_section_id_set):
            raise RuntimeError(
                "AttentionSessionLayout active topology transition references " "an unadmitted section anchor"
            )
    mounted_section_id_set = set(mounted_section_ids)
    if len(mounted_section_ids) != len(mounted_section_id_set):
        raise RuntimeError(
            "AttentionSessionLayout active topology contains duplicate section " "ids; layout transition cannot proceed"
        )

    allowed_row_fields = {
        "attention_session_section_id",
        "order",
        "weight_micros",
        "is_visible",
        "is_collapsed",
    }
    normalized_rows: list[tuple[UUID, int, int, bool, bool]] = []
    seen_section_ids: set[UUID] = set()
    seen_orders: set[int] = set()
    for row_index, raw_row in enumerate(raw_sections):
        if not isinstance(raw_row, dict):
            raise _validation_error(f"sections[{row_index}] must be an object")
        if set(raw_row) != allowed_row_fields:
            raise _validation_error(f"sections[{row_index}] must contain exactly {sorted(allowed_row_fields)}")
        section_id = _required_uuid(
            raw_row["attention_session_section_id"],
            field=f"sections[{row_index}].attention_session_section_id",
        )
        order = raw_row["order"]
        weight_micros = raw_row["weight_micros"]
        is_visible = raw_row["is_visible"]
        is_collapsed = raw_row["is_collapsed"]
        if type(order) is not int or order < 0:
            raise _validation_error(f"sections[{row_index}].order must be a non-negative integer")
        if type(weight_micros) is not int or weight_micros < 0:
            raise _validation_error(f"sections[{row_index}].weight_micros must be a non-negative integer")
        if type(is_visible) is not bool:
            raise _validation_error(f"sections[{row_index}].is_visible must be a boolean")
        if type(is_collapsed) is not bool:
            raise _validation_error(f"sections[{row_index}].is_collapsed must be a boolean")
        if section_id in seen_section_ids:
            raise _validation_error(f"duplicate mounted section id: {section_id}")
        if order in seen_orders:
            raise _validation_error(f"duplicate section order: {order}")
        if (not is_visible or is_collapsed) and weight_micros != 0:
            raise _validation_error(f"sections[{row_index}] is hidden or collapsed and must have zero weight_micros")
        if is_visible and not is_collapsed and weight_micros <= 0:
            raise _validation_error(
                f"sections[{row_index}] is visible and non-collapsed and must have positive weight_micros"
            )
        seen_section_ids.add(section_id)
        seen_orders.add(order)
        normalized_rows.append((section_id, order, weight_micros, is_visible, is_collapsed))

    if seen_section_ids != mounted_section_id_set:
        missing_ids = sorted(str(value) for value in mounted_section_id_set - seen_section_ids)
        unknown_ids = sorted(str(value) for value in seen_section_ids - mounted_section_id_set)
        raise _validation_error(
            f"section membership must exactly match mounted sections; missing={missing_ids} unknown={unknown_ids}"
        )
    expected_orders = set(range(len(mounted_section_ids)))
    if seen_orders != expected_orders:
        raise _validation_error(f"section orders must be contiguous 0..{len(mounted_section_ids) - 1}")
    active_weight_sum = sum(
        weight_micros
        for _, _, weight_micros, is_visible, is_collapsed in normalized_rows
        if is_visible and not is_collapsed
    )
    if active_weight_sum != 1_000_000:
        raise _validation_error(f"visible non-collapsed weight_micros must sum to 1000000; have={active_weight_sum}")
    normalized_rows.sort(key=lambda row: row[1])

    transition_id = stable_attention_layout_transition_id(
        attention_session_layout_id=attention_session_layout.id,
        client_intent_id=normalized_intent_id,
    )
    active_transition = attention_session_layout.active_layout_transition
    active_transition_id = (
        active_transition.id if active_transition is not None else attention_session_layout.active_layout_transition_id
    )
    existing_transition = next(
        (existing for existing in attention_session_layout.layout_transitions if existing.id == transition_id),
        None,
    )
    if existing_transition is None:
        existing_transition = AttentionLayoutTransition.by_id_cached(transition_id)

    if existing_transition is not None:
        if active_transition_id != existing_transition.id:
            raise _validation_error("client_intent_id already identifies a non-active historical transition")
        existing_rows = sorted(
            [
                (
                    state.attention_session_section_id,
                    state.order,
                    state.weight_micros,
                    state.is_visible,
                    state.is_collapsed,
                )
                for state in existing_transition.section_states
            ],
            key=lambda row: row[1],
        )
        if (
            existing_transition.previous_transition_id != expected_previous_layout_transition_id
            or existing_transition.topology_transition_id != active_topology_transition_id
            or existing_transition.client_intent_id != normalized_intent_id
            or existing_transition.transition_kind != normalized_transition_kind
            or existing_transition.source_kind != normalized_source_kind
            or existing_transition.source_ref != normalized_source_ref
            or dict(existing_transition.metadata_json or {}) != dict(normalized_metadata)
            or existing_rows != normalized_rows
        ):
            raise _validation_error("client_intent_id collides with a different active transition payload")
        return existing_transition

    if expected_previous_layout_transition_id != active_transition_id:
        raise _validation_error(
            "stale expected previous transition id; "
            f"have={expected_previous_layout_transition_id} expected={active_transition_id}"
        )
    if active_transition_id is not None and active_transition is None:
        active_transition = AttentionLayoutTransition.by_id_cached(active_transition_id)
        if active_transition is None:
            raise RuntimeError("AttentionSessionLayout active layout transition is not hydrated or cached")
    sequence = 0 if active_transition is None else active_transition.sequence + 1

    transition = await AttentionLayoutTransition.create_via_attention_session_layout(
        attention_session_layout_id=attention_session_layout.id,
        client_intent_id=normalized_intent_id,
        previous_transition_id=active_transition_id,
        topology_transition_id=active_topology_transition_id,
        sequence=sequence,
        transition_kind=normalized_transition_kind,
        source_kind=normalized_source_kind,
        source_ref=normalized_source_ref,
        metadata_json=normalized_metadata,
    )
    for section_id, order, weight_micros, is_visible, is_collapsed in normalized_rows:
        state = await AttentionLayoutTransitionSection.create_via_attention_layout_transition(
            attention_layout_transition_id=transition.id,
            attention_session_section_id=section_id,
            order=order,
            weight_micros=weight_micros,
            is_visible=is_visible,
            is_collapsed=is_collapsed,
        )
        transition.section_states.append(state)
    attention_session_layout.layout_transitions.append(transition)
    attention_session_layout.active_layout_transition = transition
    return transition
    # --- AWARE: LOGIC END apply_layout_transition


async def create_via_attention_session(
    attention_session_id: UUID,
    layout_id: UUID,
    layout_config_id: UUID | None = None,
    key: str | None = None,
    order: int = 0,
    is_active: bool = True,
) -> AttentionSessionLayout:
    """
    Create a session-local mounted layout.
    """

    # --- AWARE: LOGIC START create_via_attention_session
    return AttentionSessionLayout(
        id=stable_attention_session_layout_id(
            attention_session_id=attention_session_id,
            layout_id=layout_id,
        ),
        attention_session_id=attention_session_id,
        layout_id=layout_id,
        layout_config_id=layout_config_id,
        key=key,
        order=order,
        is_active=is_active,
    )
    # --- AWARE: LOGIC END create_via_attention_session
