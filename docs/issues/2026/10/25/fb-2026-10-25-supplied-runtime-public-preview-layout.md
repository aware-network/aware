# Issue: Add exact supplied-runtime Linux preview without replacing the selected product

- Slug: supplied-runtime-public-preview-layout
- Tag: fb/2026-10-25/supplied-runtime-public-preview-layout
- Status: In Progress
- Owner: codex-01a14c86-b376-7e90-a06c-557188bdf1e7
- Priority: P1
- Goal: TBD
- Captured: 2026-10-25
- Recorder: codex-01a14c86-b376-7e90-a06c-557188bdf1e7
- Source: Customer-directed work through aware issue open

## Ownership Scope
- `docs/issues/2026/10/25/fb-2026-10-25-supplied-runtime-public-preview-layout.md`
- `releases/canonical-bounded-runtime-fs-internal-v1/DELIVERY.json`
- `releases/canonical-bounded-runtime-fs-internal-v1/DISCLOSURES.json`
- `releases/canonical-bounded-runtime-fs-internal-v1/ENTRANCE.json`
- `releases/canonical-bounded-runtime-fs-internal-v1/INSTALL.md`
- `releases/canonical-bounded-runtime-fs-internal-v1/README.md`
- `releases/canonical-bounded-runtime-fs-internal-v1/SHA256SUMS`
- `releases/canonical-bounded-runtime-fs-internal-v1/SPECIFICATION.md`
- `releases/canonical-bounded-runtime-fs-internal-v1/bootstrap.pyz`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/protocols/install.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/CONTROL-SOURCE.json`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/FILESYSTEM-LICENSE`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/RELEASE-LICENSE`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/archive_verifier.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/control-code/bootstrap_builder.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/control-code/driver.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/control-code/loader.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/control-code/observer.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/control-code/prepare.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/control-code/renderer.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/filesystem/_native_bootstrap_custody.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/filesystem/_native_library.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/filesystem/_observation_receipt.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/filesystem/_staging_guard_history.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/filesystem/confined_entry.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/filesystem/confined_mutation.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/filesystem/cooperative_source.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/filesystem/native_bootstrap_creation.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/filesystem/native_read_cleanup.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/filesystem/private_directory.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/filesystem/private_namespace.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/filesystem/private_namespace_values.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/filesystem/private_sequence_capacity.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/filesystem/retained_bootstrap.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/filesystem/retained_file_sequence.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/filesystem/retained_mutation.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/filesystem/staging_complete.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/filesystem/staging_member.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/filesystem/staging_partitioned_plan.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/filesystem/staging_plan.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/filesystem/staging_root.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/release/_product_bulk_consumption.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/release/_product_capture_mount.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/release/_product_catalog_flow.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/release/_product_catalog_receiving.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/release/_product_member_capture.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/release/_product_member_consumption.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/release/_product_member_receiving.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/release/_product_member_replay.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/release/_product_nested_bulk.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/release/_product_nested_mount.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/release/_product_parent_member_feed.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/release/_product_stream_catalog.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/release/_product_stream_flow.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/release/_product_stream_receiving.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/release/_product_tar_policy.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/release/product_staging.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/bundle/releases/canonical-bounded-runtime-fs-internal-v1/driver-sources/release/whole_envelope.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/configure_native_current_v1.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/entrance-producer.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/examples/prepare_draft_input.py`
- `releases/canonical-bounded-runtime-fs-internal-v1/install-aware`
- `releases/canonical-bounded-runtime-fs-internal-v1/native-current-descriptor.json`
- `releases/canonical-bounded-runtime-fs-internal-v1/native-current-resource-record.json`
- `releases/canonical-bounded-runtime-fs-internal-v1/runtime-bootstrap`
- `releases/canonical-bounded-runtime-fs-internal-v1/runtime-postimage.json`


## Problem
1. Private no-host-Python operation is accepted, but this exact bundle has no public additive acquisition entrance.



## Goal
1. Project the accepted original cold-entrance outputs into an additive named preview with whole-envelope release-asset bindings; preserve current default and contributor governance.



## Acceptance Checklist
- [ ] Exact 62 small original controls plus three authored delivery documents; byte/executable-mode projection checked without rebuilding or copying the large assets.
- [ ] Keep package-local legal gaps, bounded content disclosures, source/native limitations and assisted-private qualifications visible; no public or unassisted acceptance implied.
- [ ] Prepare exact outgoing commit and two existing release-asset identities for separate explicit target authorization; no push/tag/upload/deploy or consumer installation.
- [ ] Canonical generator is the accepted prepare_bounded_runtime_bootstrap.py cold result at /tmp/aware-cold-entrance.10e63dd955; imported outputs are exact byte projections, not hand-edited installers.



## Updates (append-only)
- Ensured through `issue_sdk.ensure_issue_snapshot`. (recorder: `codex-01a14c86-b376-7e90-a06c-557188bdf1e7`)
- Applied `issue_sdk.start_issue_progress`. (recorder: `codex-01a14c86-b376-7e90-a06c-557188bdf1e7`)
