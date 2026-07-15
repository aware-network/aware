from __future__ import annotations

# Standard
from enum import Enum


class HubAuthorityVisibility(Enum):
    public = "public"
    private = "private"


class HubArtifactStatus(Enum):
    published = "published"
    superseded = "superseded"
    rejected = "rejected"


class HubPublicationReceiptStatus(Enum):
    accepted = "accepted"
    rejected = "rejected"
