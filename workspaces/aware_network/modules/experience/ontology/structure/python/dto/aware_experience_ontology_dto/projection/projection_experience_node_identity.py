from __future__ import annotations

# Third-party
from pydantic import BaseModel


class ProjectionExperienceNodeIdentity(BaseModel):
    """
    ProjectionExperience node identity contract.
    Contract:
    - Declares one human-stable identity name under a ProjectionExperienceNode.
    - Parent->child identity traversal is declared via ProjectionExperienceNodeIdentityEdge.
    """

    # Attributes
    key: str
