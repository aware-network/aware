from aware_utils.logging import logger

from aware_economy.bootstrap import EconomyMaterializationContext, bootstrap_economy


async def setup_economy(
    *,
    context: EconomyMaterializationContext | None = None,
    repo_root: object | None = None,
    aware_root: object | None = None,
) -> None:
    """Set up the canonical Economy bootstrap surface for the active runtime."""
    logger.info("Setting up economy (delegating to bootstrap)...")
    _ = await bootstrap_economy(
        context=context,
        repo_root=repo_root,
        aware_root=aware_root,
    )
    logger.info("Economy setup complete.")
