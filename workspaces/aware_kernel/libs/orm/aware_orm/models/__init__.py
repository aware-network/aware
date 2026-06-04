"""
ORM Models module with modular architecture.

This module provides the new modular ORM architecture with clean separation of concerns:
- BaseORMModel: Core fields and ClassConfig binding
- CRUDMixin: Database operations using SQL runtime metadata
- RelationshipMixin: Relationship management and lazy loading
- BranchMixin: Branch awareness and overlay creation
- ORMModel: Complete model combining all capabilities

Backward compatibility is maintained through the ORMModel alias.
"""

from .base_model import BaseORMModel
from .crud_mixin import CRUDMixin
from .relationship_mixin import RelationshipMixin
from .branch_mixin import BranchMixin
from .orm_model import ORMModel

__all__ = [
    "BaseORMModel",
    "CRUDMixin",
    "RelationshipMixin",
    "BranchMixin",
    "ORMModel",
]
