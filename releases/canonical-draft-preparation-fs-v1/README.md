# Draft-preparation whole distribution

Publicly delivered software at
[revision 2b0194bcde26](https://github.com/aware-network/aware/tree/2b0194bcde2643f04886e309d08587cde71dfd24).
The original freeze has independent acceptance. See
[successor instruction pins](PUBLIC-INSTRUCTIONS.json),
[delivery and alignment status](PUBLIC-STATUS.md) and [freeze evidence](INSTRUCTION-FREEZE.md).
See [local selection](LOCAL-SELECTION.md). Envelope `canonical-draft-preparation-source-notice-review-v1.tar.gz`
has SHA-256 `3e1fab9a79c19476ece55a1f0d62aa7784e911d52a01d32b65655617bacdb9f8`; its payload is `f2ef55bd871ee054e2f707189537ea533c46d013e8fdbc676a830f9968b94513`.
Use the [whole-envelope installer](../../protocols/install.py) through
[the entrance](../../README.md). Six package-local legal gaps remain unrepaired:
detached wheels, stripped inner bundles and registry publication are unaccepted.

Read [LICENSE](LICENSE), [NOTICE](NOTICE),
[corresponding source and upstream terms](source-history/THIRD_PARTY_NOTICES.md),
[source index](SOURCE-INDEX.json), [source mapping](SOURCE-MAP.json),
[notice bindings](NOTICE-BINDINGS.json) and [delivery mapping](DELIVERY-MAP.json).
All 1,392 envelope members remain attached, including 236 inherited notices and
the upstream source/terms inputs. Installation retains and prints their directory
as `retained_source_and_notices`; keep it with the software. Set the workflow's
`aware_envelope_root` to that exact returned absolute directory before running
its typed example; `aware_init_env` is the chosen fresh installation directory.
The original jsonschema source archive is not attached: its source-derived recipe,
constraints and publisher URL/hash are carried.

[Review status](REVIEW-STATUS.md) records exact-envelope bounded decisions.
[The raw audit](CONTENT-AUDIT.json) keeps twelve relative-fixture findings and
its original labels. Conservative component coverage is not exact binary linkage;
bounded disclosure is not exhaustive secret detection or a legal warranty.
Historical source READMEs and earlier pending labels are not customer directions.
