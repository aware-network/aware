"""Graph member protocol for unified graph infrastructure.

This module defines the minimal *view* contract that any graph node must
implement in order to participate in the Meta graph support pipeline
(indexing, reconciliation, diffing, policy evaluation, merge, etc.).

Deliberately, this contract is **read-only**:

- Identity exposure (`get_id`, `node_kind`, `get_path_key`)
- Content exposure (`get_content_fields`)

Change construction / application (`build_change`, `apply_change`,
`create_from_change`, ...) are handled by higher-level protocols and are
intentionally *not* part of this base interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Generic, Mapping, TypeVar
from uuid import UUID

from pydantic import BaseModel


# Type variable for node kind enum
T_Kind = TypeVar("T_Kind", bound=Enum)


class GraphMember(BaseModel, ABC, Generic[T_Kind]):
    """
    Minimal structural contract every graph node must satisfy.

    This protocol enables generic graph infrastructure (index, reconciler, diff)
    to work with any graph type without per-graph boilerplate.

    Responsibilities:
    - Identity: expose a primary identifier and node kind.
    - Path semantics: provide a stable, human-readable path key.
    - Content view: list mutable fields that matter for diffing.

    Non-responsibilities:
    - Change construction or application.
    - Knowledge of graph-specific change models.
    - Knowledge of persistence layers.
    """

    # --- Identity & classification ---

    @abstractmethod
    def get_id(self) -> UUID | None:
        """
        Return the underlying entity identifier, if any.

        The core graph infrastructure treats this as an opaque primary key used
        only for fast lookups and reconciliation; semantic identity comes from
        (node_kind, path_key) via the fingerprinting protocol.
        """
        ...

    @abstractmethod
    def node_kind(self) -> T_Kind:
        """
        Get the node kind for this entity.

        Returns:
            The enum value representing this node's type in the graph.
        """
        ...

    # --- Structural view: path + content + children ---

    @abstractmethod
    def get_path_key(self) -> str:
        """
        Single-source-of-truth semantic identity within the graph.

        Returns:
            Stable, deterministic, human-readable identity string.
            This should *not* be a raw UUID; prefer domain keys instead.
        """
        ...

    @abstractmethod
    def get_content_fields(self) -> Mapping[str, Any]:
        """
        Get the content view for this node.

        The returned mapping is used for:
        - Deciding what changes trigger UPDATE operations.
        - Populating field-level ChangeDelta entries.
        - Computing the CONTENT fingerprint.

        Keys are logical property names, values are already-resolved content
        values (the member is responsible for reading from its underlying
        entity or context; callers never reach into the entity directly).
        """
        ...


__all__ = ["GraphMember", "T_Kind"]
