# Aware Economy Providers

Provider adapters connect external capital systems to the Aware Economy without
owning wallet balances, service access, or internal transaction semantics.

The only capital-ingress direction is:

```text
external provider
  -> verified provider evidence
  -> TransactionIntent + CapitalConversionQuote
  -> external-ingress Transaction + TransactionExternal
  -> FinanceEntity Wallet
  -> wallet-backed Service contracts
```

Clients fund an Aware Wallet. They do not pay a Service directly through an
external provider.

## Authority Boundary

- Economy owns provider configuration, routes, wallet ownership, funding
  intents, conversion quotes, ingress transactions, balances, and replay.
- Experience/Reactivity owns event-to-action activation and action feedback.
- The provider Service owns external API calls and provider webhook
  normalization.
- Interface consumes provider-neutral actions and continuations.

The external-capital action request contains exactly:

- `transaction_intent_id`
- `transaction_intent_commit_id`

The provider Service resolves the exact committed context through
`economy.wallet_funding_context_resolve.resolve_wallet_funding_context`.
Amounts, wallet coordinates, provider selection, and quote data never travel
through the ActionIntent or caller request.

## Provider-Neutral API

`ExternalCapitalProviderApi.create_wallet_funding_session(context)` accepts an
`ExternalCapitalWalletFundingContext` resolved from Economy and returns an
`ExternalCapitalWalletFundingSessionReceipt`:

- exact TransactionIntent branch and commit
- provider key and public reference
- provider idempotency key
- `open_external_url`
- HTTPS continuation URL
- optional expiry

The fake provider is deterministic and is the default local proof rail.

## Stripe

Stripe creates a one-time hosted Checkout Session with inline `price_data`:

- `mode=payment`
- amount and currency from the committed quote
- minimal correlation metadata copied to the Checkout Session and underlying
  PaymentIntent
- test-mode secret and test-mode response only
- generic HTTPS continuation returned to Interface

Required configuration:

- `AWARE_STRIPE_WALLET_FUNDING_SECRET_KEY=sk_test_...`
- `AWARE_STRIPE_WALLET_FUNDING_SUCCESS_URL=https://...`
- `AWARE_STRIPE_WALLET_FUNDING_CANCEL_URL=https://...`

Optional configuration:

- `AWARE_STRIPE_WALLET_FUNDING_CHECKOUT_SESSIONS_ENDPOINT`
- `AWARE_STRIPE_WALLET_FUNDING_REQUEST_TIMEOUT_S`

No live Stripe call belongs in this package's tests.

## Sensor Evidence

`payment_intent.succeeded` is the credit-bearing Stripe event. The adapter
verifies the signature and requires exact agreement between provider facts and
the committed Economy context:

- TransactionIntent branch and commit
- CapitalConversionQuote id and hash
- external amount minor and currency
- provider event id and public reference
- payload hash and provider timestamp

`checkout.session.expired` is terminal no-credit evidence. It may cancel the
intent through Economy after exact correlation; it never mutates a wallet.

Refund and dispute side effects correlate the Stripe Refund/Dispute object's
native `payment_intent` to exactly one committed `TransactionExternal`.
Stripe metadata never supplies Wallet, FinanceEntity, Coin, or Aware amount
coordinates. Economy converts the provider minor-unit effect through the
committed direct-denomination route and derives every internal reference.

The Stripe event destination for this rail must select exactly:

- `payment_intent.succeeded`
- `checkout.session.expired`
- `refund.created`
- `refund.updated`
- `charge.dispute.created`
- `charge.dispute.closed`

Non-terminal refunds are acknowledged without wallet mutation; a later
terminal `refund.updated` may apply the effect. `refund.created` and
`refund.updated` dedupe by Refund object plus effect stage, not by webhook
delivery id.

Do not select `charge.refunded`, `payout.*`, `transfer.*`, or
`transfer.reversal.*` for wallet funding. `charge.refunded` duplicates
refund-object evidence, while payout and transfer events belong to treasury or
Connect accounting and require separate graph models.

Provider event replay is idempotent. Economy is the only component that can
create the external-ingress transaction, credit the Wallet, or apply a
correlated refund/dispute effect.
