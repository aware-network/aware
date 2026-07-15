from __future__ import annotations

# Third-party
from pydantic import BaseModel


class WalletPrivate(BaseModel):
    # Attributes
    private_key_encrypted: str
