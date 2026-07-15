from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_economy_ontology_dto.finance.finance_entity import FinanceEntity


class TransactionExternalMethod(BaseModel):
    # Relationships
    finance_entity: FinanceEntity | None = Field(default=None)

    # Attributes
    external_customer_id: str | None = Field(default=None)
    external_payment_method_id: str | None = Field(default=None)
    provider: str
