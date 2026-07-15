from __future__ import annotations

import importlib.util

from aware_orm.db.boot import (
    DBBootExecutionError,
    DBBootPlanError,
    SQLBootStep,
)
from aware_orm.db.contracts import (
    DBBootExecutionError as OwnerDBBootExecutionError,
    DBBootPlanError as OwnerDBBootPlanError,
    SQLBootStep as OwnerSQLBootStep,
)


def test_db_boot_owner_exports_contract_errors() -> None:
    assert DBBootPlanError is OwnerDBBootPlanError
    assert DBBootExecutionError is OwnerDBBootExecutionError


def test_db_boot_owner_exports_contract_dataclasses() -> None:
    assert SQLBootStep is OwnerSQLBootStep


def test_runtime_db_boot_shim_is_removed() -> None:
    assert importlib.util.find_spec("aware_orm.runtime.db_boot") is None
