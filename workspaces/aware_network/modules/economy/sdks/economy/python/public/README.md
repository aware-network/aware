# Aware Economy SDK

Consumer ergonomics over the generated Economy service API client.

This SDK is the public facade for Economy primitives and proofs. It does not
own provider checkout, Service activation, subscription state, entitlement
state, or `membership_*` operations.

## Canonical Rail

```text
External Provider
-> FinanceEntity Wallet funding
-> ServiceContract / SmartContractPermit / PriceReservation
-> Service operation execution
-> Escrow / Settlement / Transaction
```

The SDK should grow wallet-first operations:

- finance/wallet readiness
- refresh wallet-capital view state from the Economy ORM-backed frame read
- prepare wallet funding
- fund wallet through the provider-neutral `fund_wallet` view action helper
- record verified external wallet funding
- wallet balance and wallet activity read models
- price reservation reserve/finalize
- permit/reservation/escrow/settlement proof helpers
- service capital contract compiler facade over public price reservation plus
  smart-contract reservation endpoints

It must not grow direct ServiceContract activation, Stripe checkout, Payment Link
activation, subscription entitlement, or membership helpers.

Provider-specific Stripe code belongs at the server-side provider boundary.
Service-specific contract access belongs in Service APIs/SDKs, after Economy has
wallet-backed capital and settlement receipts.
