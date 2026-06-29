"""Baseline Python models for surgical renderer integration tests."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
import uuid

from aware_orm.models.orm_model import ORMModel


class Status(Enum):
    """Minimal status enumeration."""

    draft = "draft"
    published = "published"


class User(ORMModel):
    """User account with minimal fields."""

    id: uuid.UUID
    email: Optional[str] = None
    name: str
    joined_at: datetime


class Post(ORMModel):
    """Blog post with basic author relationship."""

    id: uuid.UUID
    title: str
    status: Status
    author: "User"
    published_at: Optional[datetime] = None
