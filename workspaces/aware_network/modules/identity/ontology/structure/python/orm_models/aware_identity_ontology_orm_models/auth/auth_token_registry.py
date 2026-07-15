from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_identity_ontology_orm_models.auth.auth_token import AuthToken


class AuthTokenRegistry(ORMModel):
    """
    Registry for execution/session tokens.
    Contract:
    - AuthTokenRegistry is scoped to APT execution credentials.
    - Identity-owned API keys and publish credentials use credential.CredentialProfile.
    - Plaintext token material is returned once and never stored in commits.
    """

    # Relationships
    tokens: list[AuthToken] = Field(default_factory=list, exclude=True)

    # Attributes
    key: str = Field(default="v1")
