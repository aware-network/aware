from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class ExternalCapitalWalletFundingSessionRequest(BaseModel):
    # Attributes
    operation: str = Field(default="create_wallet_funding_session")
    transaction_intent_id: UUID
    transaction_intent_commit_id: UUID


class ExternalCapitalWalletFundingSessionResponse(BaseModel):
    # Attributes
    operation: str = Field(default="create_wallet_funding_session")
    transaction_intent_id: UUID
    transaction_intent_commit_id: UUID
    provider_key: str
    provider_public_reference: str
    idempotency_key: str
    continuation_kind: str
    continuation_url: str
    continuation_expires_at: str | None = Field(default=None)
