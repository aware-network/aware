from __future__ import annotations

import json
from datetime import UTC as UTC_TZ, datetime
from hashlib import sha256
from typing import Any


def compute_args_hash(payload: Any) -> str:
    """Compute a deterministic JSON-based hash using sorted keys and no whitespace."""

    def default(o: Any) -> Any:
        # Ensure UUID and datetime are serialized deterministically.
        if hasattr(o, "hex"):
            return str(o)
        if isinstance(o, datetime):
            return o.replace(tzinfo=UTC_TZ).isoformat()
        return str(o)

    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=default)
    return sha256(canonical.encode()).hexdigest()


__all__ = ["compute_args_hash"]
