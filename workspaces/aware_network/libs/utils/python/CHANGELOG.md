# Changelog

All notable changes to `aware-utils` are documented here. Dates use UTC.

## [1.2.0] - 2025-10-11
- Added advanced logging profiles (`rotating`, `json`, `queue_console`), queue-based metrics hooks, and environment-driven tuning.
- Introduced structured JSON formatter, rotating file helpers, and queue listener lifecycle management.
- Documented usage patterns in `docs/logging.md` and `docs/USAGE.md`; expanded tests to cover new profiles.

## [1.1.0] - 2025-10-11
- Re-architected `aware_utils.logging` into a package with typed configuration models, profiles, registry hooks, and environment overrides while retaining the `logger` import contract.
- Added extensible logging helpers (`configure_logging`, `register_profile`, `register_logger`, `reset_logging_state`) and refreshed tests/docs to follow validation rules.
- Introduced dedicated logging docs (`docs/logging.md`) and stable suite coverage for the new configuration pipeline.

## [1.0.0] - 2025-10-11
- Initial extraction of utility modules from `aware_core` into the standalone `aware-utils` package with workspace integration and focused tests.
