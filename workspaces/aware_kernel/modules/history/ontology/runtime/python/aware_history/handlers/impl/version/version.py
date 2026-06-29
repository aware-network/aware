from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from uuid import UUID

# History Ontology
from aware_history_ontology.migration.migration_enums import MigrationStatus
from aware_history_ontology.migration.migration import Migration
from aware_history_ontology.version.version import Version

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def create_migration(
    version: Version,
    name: str,
    description: str | None = None,
    applied_at: datetime | None = None,
    status: MigrationStatus = MigrationStatus.pending,
) -> Migration:
    """
    Create one Migration under this Version.

    Contract:
    - Parent `version_id` is propagated by traversal lowering.
    - Stable identity is keyed by `(version_id, name)`.
    """

    # --- AWARE: LOGIC START create_migration
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_migration


async def create_via_branch(branch_id: UUID, version_number: int, head_commit_id: UUID | None = None) -> Version:
    """
    Create one Version under this Branch.
    """

    # --- AWARE: LOGIC START create_via_branch
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_via_branch
