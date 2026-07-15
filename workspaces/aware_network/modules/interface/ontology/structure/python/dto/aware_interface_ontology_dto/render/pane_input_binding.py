from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class PaneInputBinding(BaseModel):
    # Attributes
    payload_path: str
    source_node_key: str | None = Field(default=None)
    source_json_path: str | None = Field(default=None)
    literal_value: str | None = Field(default=None)
