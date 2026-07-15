from __future__ import annotations

from typing import Dict, Any, List
import hmac
import hashlib
import time


class StripeSignatureError(Exception):
    pass


def _parse_signature_header(sig: str) -> tuple[int, List[str]]:
    parts = [p.strip() for p in sig.split(",") if p.strip()]
    t = None
    sigs: List[str] = []
    for p in parts:
        if p.startswith("t="):
            try:
                t = int(p[2:])
            except Exception:
                raise StripeSignatureError("Invalid timestamp in signature header")
        elif p.startswith("v1="):
            sigs.append(p[3:])
    if t is None or not sigs:
        raise StripeSignatureError("Missing timestamp or signature")
    return t, sigs


def _compute_signature(signing_secret: str, timestamp: int, payload: bytes) -> str:
    signed_payload = f"{timestamp}.".encode("utf-8") + payload
    mac = hmac.new(signing_secret.encode("utf-8"), signed_payload, hashlib.sha256)
    return mac.hexdigest()


def verify_and_construct_event(
    raw_body: bytes,
    headers: Dict[str, str],
    signing_secret: str,
    tolerance_seconds: int = 300,
) -> Dict[str, Any]:
    """
    Verify Stripe signature (HMAC-SHA256) and return parsed event.
    Header format: "t=timestamp,v1=signature"
    Signature computed over "{t}.{raw_body}" with secret.
    """
    import json

    sig_header = headers.get("Stripe-Signature") or ""
    if not sig_header:
        raise StripeSignatureError("Missing Stripe-Signature header")

    t, signatures = _parse_signature_header(sig_header)
    expected = _compute_signature(signing_secret, t, raw_body)

    # timing-safe compare against any v1 signature
    valid = any(hmac.compare_digest(expected, s) for s in signatures)
    if not valid:
        raise StripeSignatureError("Invalid signature")

    # timestamp tolerance
    if tolerance_seconds is not None:
        now = int(time.time())
        if abs(now - t) > tolerance_seconds:
            raise StripeSignatureError("Timestamp outside tolerance")

    event = json.loads(raw_body.decode("utf-8"))
    if not isinstance(event, dict) or "type" not in event or "id" not in event:
        raise StripeSignatureError("Invalid event payload")
    return event
