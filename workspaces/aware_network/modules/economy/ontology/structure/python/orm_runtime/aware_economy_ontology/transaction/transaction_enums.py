from __future__ import annotations

# Standard
from enum import Enum


class TransactionKind(Enum):
    external_ingress = "external_ingress"
    transfer = "transfer"


class TransactionStatus(Enum):
    confirmed = "confirmed"
    created = "created"
    failed = "failed"
    failed_incoming = "failed_incoming"
    outgoing_applied = "outgoing_applied"
    sent = "sent"
    signed = "signed"
    validated = "validated"
