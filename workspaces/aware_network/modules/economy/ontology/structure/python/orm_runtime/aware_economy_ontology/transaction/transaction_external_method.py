from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_economy_ontology.finance.finance_entity import FinanceEntity


class TransactionExternalMethod(ORMModel):
    # Relationships
    finance_entity: FinanceEntity | None = Field(default=None, exclude=True)

    # Attributes
    external_customer_id: str | None = Field(default=None)
    external_payment_method_id: str | None = Field(default=None)
    provider: str

    # Foreign Keys
    finance_entity_id: UUID = Field(description="Foreign key for TransactionExternalMethod.finance_entity")


FUNCTIONS = {
    "TransactionExternalMethod": {},
}

__all__ = [
    "TransactionExternalMethod",
    "FUNCTIONS",
]
