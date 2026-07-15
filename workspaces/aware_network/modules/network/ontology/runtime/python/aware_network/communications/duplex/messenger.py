"""Compatibility wrapper for duplex messenger.

The canonical messenger implementation lives in `aware_comms`. The network
package re-exports it so node/runtime code shares the same request/response
correlation behaviour as public clients.
"""

from aware_comms.duplex.messenger import (
    DuplexFuture,
    DuplexFutureStatus,
    DuplexMessenger,
)

NetworkDuplexMessenger = DuplexMessenger

__all__ = ["DuplexFuture", "DuplexFutureStatus", "NetworkDuplexMessenger"]
