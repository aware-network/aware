"""Public, lazy input/receipt projection; bootstrap authority stays in SDK."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aware_protocol_sdk.bootstrap import (
        ProtocolBootstrapClient,
        ProtocolBootstrapInput,
        ProtocolBootstrapRequest,
    )


def prepare_bootstrap_input(
    client: ProtocolBootstrapClient,
    *,
    issue_root: str,
    install_agent_contract: bool,
    dry_run: bool,
) -> tuple[ProtocolBootstrapRequest, ProtocolBootstrapInput]:
    """Delegate coordinates and exact content validation to the selected SDK."""
    request = client.prepare_bootstrap_request(
        issue_root=issue_root,
        install_agent_contract=install_agent_contract,
        dry_run=dry_run,
    )
    return request, client.render_bootstrap_input(request)


def bootstrap_evidence_payload(value: Any, *, summary: bool = False) -> dict[str, Any]:
    """Keep the owner codec; summaries omit rendered bodies only, not receipts."""
    from aware_protocol_sdk.bootstrap import (
        ProtocolBootstrapInput,
        protocol_bootstrap_value_to_payload,
    )

    payload = protocol_bootstrap_value_to_payload(value)
    if summary and type(value) is ProtocolBootstrapInput:
        for item in payload["files"]:
            del item["content_utf8"]
    return payload
