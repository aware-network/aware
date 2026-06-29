"""Overlay version with additional private methods and attributes."""

from __future__ import annotations

# Core
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid


class AccessLevelType(Enum):
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


class Status(Enum):
    """Status enumeration for posts."""

    active = "active"
    inactive = "inactive"
    pending = "pending"


class Comment(BaseModel):
    """A comment on a post."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.fromisoformat("2023-01-01T00:00:00Z"))
    is_approved: bool = False
    text: str
    # Private attribute that should be merged
    _internal_score: float = 0.0


class Image(BaseModel):
    """An image file."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    height: int
    url: str = Field(unique=True)
    width: int


@intelligent_object(object_type="user")
class User(BaseModel):
    """A user account."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: Optional[str] = Field(default=None, unique=True)
    is_active: bool = True
    login_count: int = 0
    name: str = "Anonymous User"
    registered_at: datetime = Field(default_factory=lambda: datetime.fromisoformat("2023-01-01T00:00:00Z"))
    posts: list[Post] = Field(default_factory=list, unique=True)
    profile_picture: Optional[Image] = Field(default=None, unique=True)
    # Private attributes that should be merged
    _password_hash: Optional[str] = None
    _last_login_ip: Optional[str] = None

    def get_full_name(self) -> str:
        """Return user's full name."""
        return self.name

    @network(required_access=AccessLevelType.write)
    async def send_email(self, subject: str, body: str) -> bool:
        """Send an email to the user."""
        # Implementation would go here
        return True

    def _validate_password(self, password: str) -> bool:
        """Private method to validate password."""
        # This private method should be merged
        return len(password) >= 8

    def _update_login_tracking(self, ip_address: str) -> None:
        """Private method to update login tracking."""
        # This private method should be merged
        self._last_login_ip = ip_address
        self.login_count += 1


@intelligent_object(object_type="post")
class Post(BaseModel):
    """A blog post."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    content: str
    is_draft: bool = True
    published_at: Optional[datetime] = None
    status: Status
    title: str = Field(unique=True)
    view_count: int = 0
    author: User = Field(foreign_key="User.id")
    comments: list[Comment] = Field(default_factory=list, unique=True)
    # Private attribute that should be merged
    _content_hash: Optional[str] = None

    @network(required_access=AccessLevelType.write)
    def publish(self) -> bool:
        """Publish the post."""
        # Implementation would go here
        return True

    def increment_views(self) -> int:
        """Increment the view count and return the new count."""
        self.view_count += 1
        return self.view_count

    def _calculate_content_hash(self) -> str:
        """Private method to calculate content hash."""
        # This private method should be merged
        import hashlib

        return hashlib.md5(self.content.encode()).hexdigest()


class UserComment(BaseModel):
    """Relationship between user and comment."""

    user: User = Field(foreign_key="User.id")
    comment: Comment = Field(foreign_key="Comment.id")
    likes: int = 0
    # Private attribute that should be merged
    _moderation_flags: int = 0


class UserPost(BaseModel):
    """Relationship between user and post."""

    user: User = Field(foreign_key="User.id")
    post: Post = Field(foreign_key="Post.id")
    created_at: datetime = Field(default_factory=lambda: datetime.fromisoformat("2023-01-01T00:00:00Z"))
    is_pinned: bool = False

    def pin(self) -> bool:
        """Pin the post for the user."""
        self.is_pinned = True
        return True

    def _check_pin_permissions(self) -> bool:
        """Private method to check pin permissions."""
        # This private method should be merged
        return True


@network(required_access=AccessLevelType.read)
def validate_email(email: str) -> bool:
    """Validate email address format."""
    return "@" in email and "." in email


@network(required_access=AccessLevelType.admin, timeout=60)
async def send_notification(user_id: uuid.UUID, message: str) -> bool:
    """Send a notification to a user."""
    return True
