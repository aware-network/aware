from __future__ import annotations

from aware_orm.db.contracts import (
    DBBootExecutionError as OwnerDBBootExecutionError,
    DBBootPlanError as OwnerDBBootPlanError,
    SQLBootStep as OwnerSQLBootStep,
)
from aware_orm.runtime.db_boot import (
    DBBootExecutionError,
    DBBootPlanError,
    SQLBootStep,
)


def test_runtime_db_boot_reexports_owner_contract_errors() -> None:
    assert DBBootPlanError is OwnerDBBootPlanError
    assert DBBootExecutionError is OwnerDBBootExecutionError


def test_runtime_db_boot_reexports_owner_contract_dataclasses() -> None:
    assert SQLBootStep is OwnerSQLBootStep
