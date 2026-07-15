from __future__ import annotations

# Third-party
from pydantic import BaseModel


class ContentPartTextSegmentTranslation(BaseModel):
    # Attributes
    language: str
    text: str
