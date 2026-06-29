from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal

from aware_meta.graph.config.stable_ids_spec.spec import StableIdsSpec


StableIdsOwnershipMode = Literal["authored", "compiler"]
StableIdsResolutionPolicy = Literal["class_strict"]


@dataclass(frozen=True, slots=True)
class StableIdsServiceHooks:
    """Dependency hooks for stable-id resolution orchestration.

    Hooks keep path/spec resolution explicit and testable without repo-global assumptions.
    """

    resolve_spec_path_for_fqn_prefix: Callable[[str], Path | None]
    load_spec_from_path: Callable[[Path], StableIdsSpec]
    count_authored_functions_in_path: Callable[[Path], int]


__all__ = [
    "StableIdsOwnershipMode",
    "StableIdsResolutionPolicy",
    "StableIdsServiceHooks",
]
