from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from uuid import UUID

# History Ontology
from aware_history_ontology.migration.migration_enums import MigrationStatus
from aware_history_ontology.migration.migration import Migration

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def create_via_version(
    version_id: UUID,
    name: str,
    description: str | None = None,
    applied_at: datetime | None = None,
    status: MigrationStatus = MigrationStatus.pending,
) -> Migration:
    """
    Create one Migration under this Version.
    """

    # --- AWARE: LOGIC START create_via_version
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_via_version
