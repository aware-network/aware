# External Capital Rail

## Canonical Direction

```text
External capital provider
  -> Aware external-capital provider Service
  -> Economy verified sensor
  -> FinanceEntity Wallet
  -> Economy smart-contract permits, escrows, settlements, and Service contracts
```

External capital funds a Wallet. Services consume wallet-backed Economy state.
No provider event grants membership, entitlement, role, or Service access.

## Consumer Flow

1. An admitted actor invokes `fund_wallet` with a target Wallet, target Coin,
   Aware amount, provider key, funding-intent key, and idempotency key.
2. Economy proves that the actor owns the FinanceEntity and target Wallet.
3. Economy resolves one active `ExternalCapitalProviderConfig` route for the
   provider key and target Coin.
4. Economy commits one `TransactionIntent` and one contained immutable
   `CapitalConversionQuote`.
5. The published TransactionIntent commit matches the authored Economy
   Experience event.
6. Reactivity creates a value-free ActionIntent.
7. Experience composes the provider request from `commit.branch_id` and
   `commit.commit_id` only.
8. The provider Service resolves exact context from Economy at that commit.
9. The provider adapter creates a hosted continuation.
10. Experience action feedback exposes the provider-neutral continuation to
    Interface.
11. A signed provider event is normalized into provider sensor evidence.
12. Economy correlates the evidence to the exact intent, quote, provider
    configuration, amount, currency, and event identity.
13. Economy creates or reuses one external-ingress Transaction, records
    `TransactionExternal` provenance, credits the Wallet once, and confirms
    the TransactionIntent.

## Economy Graph Truth

`ExternalCapitalProviderConfig` is an independently evolving configuration
projection. Its routes declare:

- provider FinanceEntity
- provider key
- target Coin
- external ISO currency
- minor-unit exponent
- conversion mode
- optional minimum and maximum external amount
- active status

`CapitalConversionQuote` is contained by `TransactionIntent`. It records:

- provider route
- external amount minor and currency
- target amount and Coin
- conversion mode and quote source
- quote hash
- capture time and optional expiry

V0 accepts `direct_denomination` only. The external ISO currency must match the
target fiat Coin symbol, and exact minor-unit arithmetic must equal the target
amount. Cross-currency and AWC conversion require an authenticated capital-rate
source.

## Action And Service Boundary

The provider API request is intentionally minimal:

```text
transaction_intent_id
transaction_intent_commit_id
```

The ActionIntent is a decision record, not a value carrier. The provider
Service calls the generated Economy SDK context endpoint and receives a strict
`ExternalCapitalWalletFundingContext`.

The context endpoint fails closed when:

- the exact TransactionIntent commit cannot be loaded
- provider configuration or route identity differs
- the recipient Wallet or FinanceEntity differs
- the quote is absent or malformed
- amount, currency, target amount, conversion mode, or quote source differs
- the intent is already terminal
- the admitted provider actor does not own the provider FinanceEntity

The provider Service has no direct Economy ORM import and no wallet mutation
capability.

## Hosted Continuation

The provider response is generic:

```text
transaction_intent_id
transaction_intent_commit_id
provider_key
provider_public_reference
idempotency_key
continuation_kind = open_external_url
continuation_url = https://...
continuation_expires_at?
```

Continuation state belongs to Experience/Reactivity action feedback. Economy
wallet-capital view state shows configured provider routes and committed
intent/quote status; it does not store or infer provider continuations.

## Stripe Adapter

Stripe uses `POST /v1/checkout/sessions` with:

- `mode=payment`
- inline one-time `line_items[0][price_data]`
- one quantity
- metadata on both Checkout Session and `payment_intent_data`
- an idempotency key derived from provider key, TransactionIntent id, and quote
  hash
- operator-owned HTTPS success and cancel URLs

Required metadata is limited to:

- `aware_provider_key`
- `aware_transaction_intent_id`
- `aware_transaction_intent_commit_id`
- `aware_capital_conversion_quote_id`
- `aware_quote_hash`
- `aware_external_amount_minor`
- `aware_external_currency`

The adapter rejects Service-contract, subscription, entitlement, and membership
metadata. Product catalog and recurring Price objects are not part of wallet
funding.

Pre-live operation requires `sk_test_...` and rejects live-mode Checkout
responses.

## Credit-Bearing Evidence

`payment_intent.succeeded` must provide:

- valid Stripe signature over the raw body
- `status=succeeded`
- required Aware correlation metadata
- amount received equal to the committed external amount
- currency equal to the committed external currency
- stable Stripe event id and PaymentIntent public id

The normalized sensor request contains provider facts only. Economy rehydrates
all wallet and target-capital coordinates from committed graph truth.

`TransactionExternal` identity is keyed by provider configuration plus
provider event. The same provider event cannot mint under another internal
Transaction.

## Terminal No-Credit Evidence

`checkout.session.expired` carries the same intent, commit, quote, and provider
correlation. Economy may transition the matching intent to cancelled after
verification. No external-ingress Transaction and no Wallet application are
created.

## Replay And Partial Failure

Funding replay is required at every stage:

1. external-ingress Transaction
2. TransactionExternal provenance
3. Wallet external-ingress application
4. TransactionIntent confirmation

Retries repair the first missing stage and reuse all prior identities. A third
delivery after completion is a true replay with no balance change.

## Operator Contract

The Stripe event destination for wallet funding listens to:

- `payment_intent.succeeded`
- `checkout.session.expired`
- refund, dispute, transfer reversal, and payout lifecycle events owned by the
  separate provider-lifecycle sensor

The webhook signing secret belongs to Node/operator secret storage. It is never
stored in Economy ontology, Experience bindings, API DTOs, logs, or fixtures.
