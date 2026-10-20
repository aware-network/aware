# Public whole-envelope installer payload correction

The installer at public revision `545c72753964a91f1f74a997e9adf488f20bfe3e`
requested the old `payload/aware-canonical-neutral-fs-internal-v1.tar.gz`
member. The accepted envelope actually carries
`payload/aware-canonical-project-goal-fs-internal-v1.tar.gz`. This lookup
failed before environment creation; the external installation failure and
all four unrun client evaluations remain frozen, not repaired into passes.

This local correction changes only that exact member literal in the original
`protocols/install.py`. Archive digests, verification, new-target guards,
offline inner installer, package selection, software, sources/notices and
historical records are unchanged. There is no member search, fallback,
renaming workaround, alternate installer or retry.

Envelope: `edaab985f57541928effb038c825fa3af6ec6afbffda45249099a64bf1120898`.
Payload: `f5b5062aeefec2db2ce660e533342ef9b0df59b9ef7a1b02661d467239da4522`.
Corrected wrapper: `3d6da7b29caf09f83a795f85fc05126192b6eeb12d957d7224429b945b58376d`.

`test_public_installer.py` checks the actual envelope and inner digest up to
an intercepted pre-retention boundary, reproduces the original wrong-member
failure and tests target/digest/no-fallback guards. These tests dispatch no
installation. They are not a substitute for the separately recorded one-fresh-
installation proof through the actual corrected public wrapper.

Earlier qualification installed the inner bundle directly; later retained reads
and published-byte checks did not establish public-wrapper installation success.
Historical instruction records retain those checkpoint bytes. Their 24 current
rows do not pin `protocols/install.py`; this correction has its own exact wrapper
digest and original Issue publication receipts. Do not rewrite old freezes.

Whole-envelope carriage remains mandatory. Nine legal gaps, thirteen findings,
native/header/toolchain/linkage limits and primary matrix/composition receiving
qualifications remain unchanged. Optional Project/Goal is direction, not work
authority. Historical observation does not establish completion or retry authority.

This is a local review candidate, not an authorized additional public release.
Independent source/installation review and separate publication authorization
must precede fresh successor client evaluations. No customer-run retry, wheel
rebuild, activation or GC change follows from this correction.

## Actual public-wrapper installation proof

One invocation of the actual corrected `protocols/install.py` succeeded with
Python 3.12.3 on Linux x86-64, networking disabled and development/supplier
checkouts hidden. Only the exact wrapper/current release were exposed read-only;
one new proof root was writable. Exit 0; no retry or alternate installer.

The original receipt binds the unchanged envelope and payload hashes. Read-only
accounting verifies 49 payload distributions plus separately seeded pip, all
49 wheel hashes, 1,270 installed member bytes (excluding generated RECORD files),
800 Aware payload members and all 2,185 retained outer-member bytes. Dependency
checks cover 102 active base requirements, not the historical 234 extra-aware
checks; `pip check` passes. No editable/direct-URL installs. Four read-only help
entrances pass; no owner journey or customer evaluation is claimed.

Installation receipt SHA256:
`7a35238527c29b91bd6ba6e06e00704bf1fb7ffd36e5ca09c16dcfc6420aead0`.
Installed account SHA256:
`1d7d1bde23a5ba12b42878236151638e71a07fc85d5215059568d1a6493b6a58`.

Nine regression tests pass. Initial six-pass/three-failure test evidence remains:
the test harness intercepted its own interpreter-version probe before reaching
archive lookup. Its isolated version response was corrected; the actual single
installation used the real Python interpreter. Earlier evidence is not erased.
