"""Sample Python file with Pydantic models for testing Python adapters."""

from __future__ import annotations

# Core
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid

# Test imports
import os
import sys as system
from datetime import timezone as tz
from typing import *
from . import local_module


# Custom decorators for testing
class AccessLevelType(str, Enum):
    read = "read"
    write = "write"
    admin = "admin"


def network(required_access: AccessLevelType, timeout: int = 30):
    """Network decorator for testing adapter."""

    def decorator(func):
        return func

    return decorator


def intelligent_object(object_type: str = "default"):
    """Intelligent object decorator for testing adapter."""

    def decorator(cls):
        return cls

    return decorator


class Status(str, Enum):
    """Status enumeration for posts."""

    active = "active"
    inactive = "inactive"
    pending = "pending"


class Comment(BaseModel):
    """A comment on a post."""

    created_at: datetime = Field(default_factory=lambda: datetime.fromisoformat("2023-01-01T00:00:00Z"))
    is_approved: bool = False
    text: str
    # Self-referential replies
    replies: list[Comment] = Field(default_factory=list)


class Image(BaseModel):
    """An image file."""

    height: int
    url: str
    width: int
    # Backref to User
    user: Optional[User] = None


@intelligent_object(object_type="user")
class User(BaseModel):
    """A user account."""

    email: Optional[str] = Field(default=None)
    is_active: bool = True
    login_count: int = 0
    name: str = "Anonymous User"
    registered_at: datetime = Field(default_factory=lambda: datetime.fromisoformat("2023-01-01T00:00:00Z"))
    posts: list[Post] = Field(default_factory=list, exclude=True)
    profile_picture: Optional[Image] = Field(default=None)
    roles: set[str] = Field(default_factory=set)
    aliases: Optional[list[str]] = None

    def get_full_name(self) -> str:
        """Return user's full name."""
        return self.name

    @network(required_access=AccessLevelType.write)
    async def send_email(self, subject: str, body: str) -> bool:
        """Send an email to the user."""
        # Implementation would go here
        return True

    @classmethod
    def build_default(cls) -> "User":
        """Build a default user (classmethod)."""
        return User(name="Default User")

    @staticmethod
    def double(x: int) -> int:
        """Double a number (staticmethod)."""
        return x * 2

    def _internal(self) -> bool:
        """Private/internal instance method."""
        return True

    def profile_and_count(self) -> tuple["User", int]:
        """Return a tuple of (self, count)."""
        return self, 1

    def optional_user(self) -> Optional["User"]:
        """Return an optional user (forward ref)."""
        return None

    def union_return(self) -> str | int:
        """Return union of str or int."""
        return 1

    def dict_return(self) -> dict[str, int]:
        """Return a simple mapping."""
        return {"a": 1}

    def list_union_return(self) -> list[str | int]:
        """Return a list of union primitives."""
        return []


@intelligent_object(object_type="post")
class Post(BaseModel):
    """A blog post."""

    content: str
    is_draft: bool = True
    published_at: Optional[datetime] = None
    status: Status
    title: str
    user_id: uuid.UUID
    view_count: int = 0
    author: User
    comments: list[Comment] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)

    @network(required_access=AccessLevelType.write)
    def publish(self) -> bool:
        """Publish the post."""
        # Implementation would go here
        return True

    def increment_views(self) -> int:
        """Increment the view count and return the new count."""
        # Implementation would go here
        self.view_count += 1
        return self.view_count


class UserComment(BaseModel):
    """Relationship between user and comment."""

    user_id: uuid.UUID
    comment_id: uuid.UUID
    user: User
    comment: Comment
    likes: int = 0


class UserPost(BaseModel):
    """Relationship between user and post."""

    user_id: uuid.UUID
    post_id: uuid.UUID
    user: User
    post: Post
    created_at: datetime = Field(default_factory=lambda: datetime.fromisoformat("2023-01-01T00:00:00Z"))
    is_pinned: bool = False

    def pin(self) -> bool:
        """Pin the post for the user."""
        # Implementation would go here
        self.is_pinned = True
        return True


@network(required_access=AccessLevelType.read)
def validate_email(email: str) -> bool:
    """Validate email address format."""
    # Basic implementation
    return "@" in email and "." in email


@network(required_access=AccessLevelType.admin, timeout=60)
async def send_notification(user_id: uuid.UUID, message: str) -> bool:
    """Send a notification to a user."""
    # Implementation would go here
    return True
