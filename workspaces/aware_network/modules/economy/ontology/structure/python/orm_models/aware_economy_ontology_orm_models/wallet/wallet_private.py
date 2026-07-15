from __future__ import annotations

# Orm
from aware_orm.models.orm_model import ORMModel


class WalletPrivate(ORMModel):
    # Attributes
    private_key_encrypted: str
