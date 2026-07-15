from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class ContentPartTextStyle(BaseModel):
    # Attributes
    background_color: str | None = Field(default=None)
    block_semantic_type: str | None = Field(default=None)
    bold: bool | None = Field(default=False)
    color: str | None = Field(default=None)
    font_family: str | None = Field(default=None)
    font_size: int | None = Field(default=0)
    italic: bool | None = Field(default=False)
    underline: bool | None = Field(default=False)
