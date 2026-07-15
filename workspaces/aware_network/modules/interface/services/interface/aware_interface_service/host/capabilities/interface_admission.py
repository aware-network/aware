from __future__ import annotations

from aware_interface.host_capabilities import (
    InterfaceHostCapabilityAction,
    InterfaceHostCapabilityScreen,
    InterfaceHostCapabilitySnapshot,
    InterfaceHostPaneContribution,
)


INTERFACE_ADMISSION_SCREEN_KEY = "interface_admission"
INTERFACE_ADMISSION_PANE_KEY = "interface_admission"
CREATE_INTERFACE_ACTION_KEY = "interface_admission.create_interface"
SELECT_INTERFACE_ACTION_KEY = "interface_admission.select_interface"
REQUEST_PAIRING_ACTION_KEY = "interface_admission.request_pairing"
ACCEPT_PAIRING_ACTION_KEY = "interface_admission.accept_pairing"
RESUME_INTERFACE_ACTION_KEY = "interface_admission.resume_interface"

INTERFACE_ADMISSION_ACTION_KEYS = (
    CREATE_INTERFACE_ACTION_KEY,
    SELECT_INTERFACE_ACTION_KEY,
    REQUEST_PAIRING_ACTION_KEY,
    ACCEPT_PAIRING_ACTION_KEY,
    RESUME_INTERFACE_ACTION_KEY,
)

_PENDING_EXECUTION_REASON = (
    "Interface Admission action execution lands in the next action pass."
)
_TRANSPORT_REQUIRED_REASON = (
    "Select, pairing, and resume require Interface transport registration."
)
_CREATE_INTERFACE_REASON = "Create a canonical Interface to continue."
PAIRING_CONTRACT_VERSION = "2026-05-16"

PAIRING_CHALLENGE_FIELDS = (
    "pairing_challenge_id",
    "pairing_uri",
    "display_code",
    "matching_code",
    "expires_at",
    "allowed_methods",
)


def _action(
    action_key: str,
    *,
    label: str,
    payload_schema_hint: str,
    enabled: bool,
    reason: str | None,
) -> InterfaceHostCapabilityAction:
    return InterfaceHostCapabilityAction(
        action_key=action_key,
        label=label,
        enabled=enabled,
        reason=reason,
        payload_schema_hint=payload_schema_hint,
    )


def build_interface_admission_capability_snapshot(
    *,
    consumer_profile_active: bool,
    authenticated: bool,
    interface_admitted: bool,
    transport_bound: bool,
) -> InterfaceHostCapabilitySnapshot | None:
    if not consumer_profile_active or authenticated or interface_admitted:
        return None
    blocked_action_reason = (
        _PENDING_EXECUTION_REASON if transport_bound else _TRANSPORT_REQUIRED_REASON
    )
    return InterfaceHostCapabilitySnapshot(
        capability_id="interface_admission",
        kind="interface_admission",
        screen=InterfaceHostCapabilityScreen(
            screen_key=INTERFACE_ADMISSION_SCREEN_KEY,
            source_kind="gate",
            screen_kind="admission",
            title="Interface Admission",
            message=(
                "Create, select, pair, or resume a canonical Interface before "
                "loading Control or Identity."
            ),
            pane_key=INTERFACE_ADMISSION_PANE_KEY,
        ),
        actions=(
            _action(
                CREATE_INTERFACE_ACTION_KEY,
                label="Create interface",
                payload_schema_hint=(
                    "{display_name?: string, window_config_id?: uuid, "
                    "idempotency_key?: string}"
                ),
                enabled=True,
                reason=None,
            ),
            _action(
                SELECT_INTERFACE_ACTION_KEY,
                label="Select interface",
                payload_schema_hint="{interface_id: uuid}",
                enabled=False,
                reason=blocked_action_reason,
            ),
            _action(
                REQUEST_PAIRING_ACTION_KEY,
                label="Show pairing code",
                payload_schema_hint=(
                    "{interface_id?: uuid, method?: qr|code|link, "
                    "expires_in_seconds?: int, device_label?: string, "
                    "idempotency_key?: string}"
                ),
                enabled=False,
                reason=blocked_action_reason,
            ),
            _action(
                ACCEPT_PAIRING_ACTION_KEY,
                label="Pair with code",
                payload_schema_hint=(
                    "{pairing_token?: string, pairing_code?: string, "
                    "device_label?: string, idempotency_key?: string}"
                ),
                enabled=False,
                reason=blocked_action_reason,
            ),
            _action(
                RESUME_INTERFACE_ACTION_KEY,
                label="Resume interface",
                payload_schema_hint=(
                    "{interface_id?: uuid, interface_session_id?: uuid}"
                ),
                enabled=False,
                reason=blocked_action_reason,
            ),
        ),
        pane_contributions=(
            InterfaceHostPaneContribution(
                pane_key=INTERFACE_ADMISSION_PANE_KEY,
                pane_kind=INTERFACE_ADMISSION_PANE_KEY,
                section_key=INTERFACE_ADMISSION_PANE_KEY,
                title="Interface Admission",
                summary=(
                    "Create, select, pair, or resume a canonical Interface "
                    "before loading Control or Identity."
                ),
                status="not_admitted",
                readiness_reason=_CREATE_INTERFACE_REASON,
                narrative_key="bootstrap.panes.interface_admission",
                action_keys=INTERFACE_ADMISSION_ACTION_KEYS,
                machine_payload={
                    "capability_id": "interface_admission",
                    "capability_kind": "interface_admission",
                    "screen_key": INTERFACE_ADMISSION_SCREEN_KEY,
                    "source_kind": "gate",
                    "admission_status": "not_admitted",
                    "pairing_contract": {
                        "version": PAIRING_CONTRACT_VERSION,
                        "request_action_key": REQUEST_PAIRING_ACTION_KEY,
                        "accept_action_key": ACCEPT_PAIRING_ACTION_KEY,
                        "challenge_fields": list(PAIRING_CHALLENGE_FIELDS),
                        "display_methods": ["qr", "code", "link"],
                        "receipt": (
                            "accept_pairing commits InterfaceSession before "
                            "post-admission runtime boot"
                        ),
                    },
                },
            ),
        ),
    )


__all__ = [
    "ACCEPT_PAIRING_ACTION_KEY",
    "CREATE_INTERFACE_ACTION_KEY",
    "INTERFACE_ADMISSION_PANE_KEY",
    "INTERFACE_ADMISSION_ACTION_KEYS",
    "INTERFACE_ADMISSION_SCREEN_KEY",
    "PAIRING_CHALLENGE_FIELDS",
    "PAIRING_CONTRACT_VERSION",
    "REQUEST_PAIRING_ACTION_KEY",
    "RESUME_INTERFACE_ACTION_KEY",
    "SELECT_INTERFACE_ACTION_KEY",
    "build_interface_admission_capability_snapshot",
]
