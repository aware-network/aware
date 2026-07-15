from __future__ import annotations

# Standard
from enum import Enum


class OrganizationMemberRole(Enum):
    admin = "admin"
    guest = "guest"
    member = "member"
    owner = "owner"
