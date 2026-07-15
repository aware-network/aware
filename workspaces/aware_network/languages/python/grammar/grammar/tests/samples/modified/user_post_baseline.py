"""Baseline Python models for surgical renderer integration tests."""










from __future__ import annotations

# Standard Imports
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid

# ORM
from aware_orm.models.orm_model import ORMModel


class User(ORMModel):
    """
    User account with minimal fields.
    """

    email: Optional[str] = None
    id: uuid.UUID
    is_active: bool = True
    joined_at: datetime
    last_login: Optional[datetime] = None
    name: str
    posts: list[Post]

    def mark_inactive(self) -> None:
        """Deactivate the user account."""
        self.is_active = False

    def track_login(self) -> None:
        """Record the latest login timestamp."""
        self.last_login = datetime.utcnow()


# tests
from tests.samples.baseline.user_post_baseline import User


class Post(ORMModel):
    """
    Blog post with basic author relationship.
    """

    author: User
    content: Optional[str] = None
    content_notes: Optional[str] = None
    contributors: list[User]
    id: uuid.UUID
    published_at: Optional[datetime] = None
    status: Status
    summary: Optional[str] = None
    title: str

    def touch(self) -> None:
        """Update the modification timestamp."""
        self.updated_at = datetime.utcnow()

    def clear_notes(self) -> None:
        """Reset editorial notes while preserving content."""
        self.content_notes = None


class Status(Enum):
    """Minimal status enumeration."""

    archived = "archived"
    draft = "draft"
    published = "published"


def send_digest(users: list[User]) -> int:
    """Helper method retained to ensure non-ORM content survives surgery."""
    return len(users)
