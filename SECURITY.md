# Security policy

## Reporting a vulnerability

Do not open a public issue for an undisclosed vulnerability. Use GitHub's
private vulnerability reporting flow for this repository:

<https://github.com/aware-network/aware/security/advisories/new>

Include affected revisions, reproduction steps, impact, and any proposed
mitigation. Please avoid accessing data that is not yours, disrupting services,
or publishing details before a fix and coordinated disclosure are ready.

## Supported releases

Aware has not announced a stable release. Support targets the exact current
filesystem previews in `protocols/agent/release.json` and the independent
`protocols/publication/receipt.json`, on their documented platform/Python.
Historical internal workspace snapshots are not the current public product.

The tools check declared owner, record freshness, lifecycle and publication
scope. They do not authenticate actor identity or isolate arbitrary processes
with filesystem access. Report an operator refusal bypass separately from raw
filesystem access. Preserve revision, archive/wheel hash and sanitized evidence.
