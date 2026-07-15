from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from .lane_materialization import LaneMaterialization
from .pane_registry import PaneMountContext, PaneProvider


class LanePaneMaterializer(Protocol):
    """Map commit-backed lane materialization into pane content."""

    def render(
        self,
        *,
        context: PaneMountContext,
        lane_materialization: LaneMaterialization | None,
    ) -> str:
        """Render pane content for the current lane state."""
        ...


LaneMaterializationLookup = Callable[[PaneMountContext], LaneMaterialization | None]


def build_materialized_pane_provider(
    *,
    materializer: LanePaneMaterializer,
    lane_lookup: LaneMaterializationLookup,
) -> PaneProvider:
    """Adapt lane materialization plus materializer into a pane provider."""

    def _provider(context: PaneMountContext) -> str:
        lane_materialization = lane_lookup(context)
        return materializer.render(
            context=context,
            lane_materialization=lane_materialization,
        )

    return _provider

