# Economy Wallet Capital Pane

`wallet_capital` is the Economy-owned pane package for the Experience view
`aware_economy.home.wallet_capital.v1`, backed by the API view
`economy.wallet_capital`.

The pane renders wallet-first capital state and binds only API-owned view action
keys:

- `refresh_wallet_capital`
- `fund_wallet`

It does not execute provider funding, create Stripe sessions, synthesize funding
requests, or decide post-funding navigation. Real funding continuation and
consumer E2E transitions remain service/SDK and Experience-owned work.
