# Changelog

All notable changes to `aware-comms` are documented here. Dates use UTC.

## [0.1.0] - 2025-10-12
- Initialized project structure (`pyproject.toml`, `README.md`, tests scaffold) for the shared communications package.
- Preparing to extract websocket transport helpers and NetworkOperation models from internal modules into publicly distributable code.

## [0.1.1] - 2025-10-13
- Migrated websocket frame, registry, messenger, and duplex client helpers from internal modules to `aware_comms`.
- Added unit tests for frame validation and messenger flow; drafted CLI integration test harness.
- Updated messenger to decode JSON responses and allow per-instance timeout overrides.
