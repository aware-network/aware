from __future__ import annotations

import logging

from aware_economy.ontology.materialization import (
    EconomyMaterializationContext,
    MaterializedCoinCatalogEntry,
    bootstrap_default_coin_catalog,
)

logger = logging.getLogger(__name__)


async def bootstrap_economy(
    *,
    context: EconomyMaterializationContext | None = None,
    repo_root: object | None = None,
    aware_root: object | None = None,
) -> tuple[MaterializedCoinCatalogEntry, ...]:
    """Bootstrap the canonical Economy coin catalog via ontology materialization."""
    logger.info("Bootstrapping economy coin catalog...")
    entries = await bootstrap_default_coin_catalog(
        context=context,
        repo_root=repo_root,
        aware_root=aware_root,
    )
    logger.info("Economy bootstrap complete: materialized %d coin declarations.", len(entries))
    return entries
