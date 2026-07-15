from __future__ import annotations

# Standard
from enum import Enum


class ServiceOperationStatus(Enum):
    failed = "failed"
    queued = "queued"
    running = "running"
    skipped = "skipped"
    succeeded = "succeeded"


class ServiceOperationFulfillmentKind(Enum):
    actuation = "actuation"
    coordination = "coordination"
    view = "view"


class ServiceOperationSettlementPolicy(Enum):
    none = "none"
    reserve_and_finalize = "reserve_and_finalize"
    reserve_before_execute = "reserve_before_execute"


class ServiceOperationReceiptPolicy(Enum):
    committed = "committed"
    read_model = "read_model"


class ServiceOperationAdmissionMode(Enum):
    contract_and_permit_required = "contract_and_permit_required"
    contract_required = "contract_required"
    identity_required = "identity_required"
    metered_settlement_required = "metered_settlement_required"
    public_read = "public_read"


class ServiceContractKind(Enum):
    metered = "metered"
    one_time = "one_time"
    subscription = "subscription"


class ServiceConfigCodePackageConfigCardinality(Enum):
    many = "many"
    one = "one"


class ServiceContractStatus(Enum):
    active = "active"
    canceled = "canceled"
    expired = "expired"
    pending = "pending"
    suspended = "suspended"


class ServiceContractOperationQuotaUnit(Enum):
    artifact = "artifact"
    byte = "byte"
    custom = "custom"
    operation = "operation"
    request = "request"
    token = "token"


class ServiceContractOperationQuotaWindow(Enum):
    billing_period = "billing_period"
    day = "day"
    hour = "hour"
    minute = "minute"
    month = "month"
    none = "none"


class ServiceContractOperationQuotaOverLimitBehavior(Enum):
    allow_metered = "allow_metered"
    deny = "deny"
    throttle = "throttle"


class ServiceContractOperationPermitScope(Enum):
    contract = "contract"
    operation = "operation"
    session = "session"


class ServiceContractOperationPermitIdempotencyScope(Enum):
    none = "none"
    operation_nonce = "operation_nonce"
    request_hash = "request_hash"


class ServiceContractOperationPriceSource(Enum):
    contract_override = "contract_override"
    operation_default = "operation_default"


class ServicePlanCycle(Enum):
    annual = "annual"
    monthly = "monthly"
    one_time = "one_time"


class ServiceSubscriptionCycleStatus(Enum):
    failed = "failed"
    paid = "paid"
    pending = "pending"


class ServiceSubscriptionInvoiceStatus(Enum):
    open = "open"
    paid = "paid"
    uncollectible = "uncollectible"
    void = "void"


class ServiceSubscriptionStatus(Enum):
    active = "active"
    canceled = "canceled"
    past_due = "past_due"
    trial = "trial"
