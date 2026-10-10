"""Consumer signatures only; Protocol matching never authenticates an issuer."""

from __future__ import annotations

from typing import Protocol, TypeVar

from .private_stage_contract import CodePrivateStagePlanV1
from .product_contribution import SelectedProviderProductContribution


class PrivateStagePlanProducer(Protocol):
    """Original public owner's registered factory function, retained by Code."""

    def __call__(
        self, original: SelectedProviderProductContribution
    ) -> CodePrivateStagePlanV1: ...


_Root = TypeVar("_Root", contravariant=True)
_Completion = TypeVar("_Completion", contravariant=True)
_Product = TypeVar("_Product", contravariant=True)


class CommittedPrivateProductValidator(Protocol[_Root, _Completion, _Product]):
    """Workspace-owned original receiver; Code must authenticate its origin."""

    def validate_committed_private_product(
        self,
        root_plan_use: _Root,
        private_completion: _Completion,
        committed_product: _Product,
    ) -> None:
        """Check original issuer, causal candidate, complete product and currentness."""
        ...

    def check_committed_private_product_locked(
        self,
        root_plan_use: _Root,
        private_completion: _Completion,
        committed_product: _Product,
    ) -> None:
        """In-place identity and coordinate check under the held parent guard."""
        ...


__all__ = ["CommittedPrivateProductValidator", "PrivateStagePlanProducer"]
