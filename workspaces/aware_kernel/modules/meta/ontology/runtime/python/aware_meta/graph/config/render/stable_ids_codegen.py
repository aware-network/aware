from __future__ import annotations

"""Deprecated stable-id renderer adapter module.

Stable-id ownership/resolution contracts moved to:
- `aware_meta.graph.config.stable_ids_resolution`
- `aware_meta.graph.config.stable_ids_spec`

This module is intentionally kept as a no-API marker to prevent accidental
re-coupling of stable-id resolution logic into renderer rails.
"""

__all__: list[str] = []
