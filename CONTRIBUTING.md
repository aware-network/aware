# Contributing to Aware

This repository owns public consumer protocols, neutral SDK/provider/CLI
surfaces, versioned agent documentation and installable distribution evidence.
It is not a development monorepo export or an ontology/service release.

Workflow contracts, profiles, delivery and evaluation live in `protocols/`.
Reviewed neutral domain/SDK/provider/CLI source lives in `workspaces/`; see its
[source boundary and build procedure](workspaces/README.md). Do not restore
retired internal exports or broaden dependencies without explicit review.

Use the same issue-first workflow customers consume: read `AGENTS.md`, install
the pinned tooling through `protocols/agent/install.py`, and use the installed
`aware` command. Add its venv `bin` to PATH or retain its absolute path. This
checkout already has `aware.protocol.toml`; do not rerun setup over it.
Open one approved exact-scope Issue, record real checks, dry-run/apply scoped
publication and close with the actual receipt. No resident service, internal
checkout import or raw Git lifecycle workaround is required.

Canonical templates are under `protocols/contracts/`; change authored versions,
not generated scaffolds or installed packages. Generators require explicit
Issue scope. Preserve immutable candidate bytes; publish a new version for a
changed payload. Report exact revision/candidate, command and expected/observed
behavior with private records redacted. Remote pushes need maintainer approval.

## License

Unless you explicitly state otherwise, every contribution intentionally
submitted for inclusion in Aware is licensed under Apache License 2.0, matching
the project's inbound and outbound license. No copyright assignment or
separate Contributor License Agreement is required at this stage.

## Developer Certificate of Origin

Every commit must include a `Signed-off-by` trailer certifying the Developer
Certificate of Origin 1.1: <https://developercertificate.org/>.

Use your real name and an email address you control:

```text
Signed-off-by: Your Name <you@example.com>
```

The sign-off states that you have the right to submit the contribution under
the project's license. It is not a copyright assignment.

## Third-party material

Do not submit copied, generated, binary, or vendored material without recording
its source, version, license, notices, and build or acquisition provenance.
Copyleft dependencies must be called out explicitly before inclusion in a
release profile.
