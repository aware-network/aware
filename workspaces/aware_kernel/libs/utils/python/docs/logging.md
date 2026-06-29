---
title: "Aware Utils Logging"
code_path: ../aware_utils/logging/__init__.py
test_path: ../tests/logging/test_logging_configuration.py
code_sha: d6a0424b91c9016c70725b13aafc8163601520b5
last_validated: "2025-10-11T15:29:53Z"
---

# Aware Utils Logging

The `aware_utils.logging` package provides the default logging entry point for Aware applications. It exposes the canonical `logger` instance while offering a modern configuration pipeline built on typed profiles and environment-aware overrides.

## Key Concepts

- **Profiles**: Named presets (`console`, `plain`, `rotating`, `json`, `queue_console`) choose handler/formatter combinations. Use `configure_logging(profile="json")` to switch behaviour at runtime.
- **Registry**: Call `register_logger("aware.worker", level="DEBUG")` before `configure_logging` to seed custom logger settings across profiles.
- **Environment Overrides**: Adjust behaviour without code changes via `AWARE_LOG_PROFILE`, `AWARE_LOG_LEVEL`, `AWARE_LOG_OVERRIDES`, and profile-specific variables.
- **Helpers**: `LogHelper` retains the existing emoji-rich helpers (`section`, `success`, etc.) and works with whichever profile is active.
- **Metrics Hooks**: Optional callbacks report queue handler statistics; enable via `set_logging_metrics_callback` or `AWARE_LOG_METRICS=stdout`.

## Profiles

### Console *(default)*
- Stream to stdout with colourised formatting.
- Best for local development and CLI tools.

### Plain
- Stream to stdout using plain ANSI-free formatting.
- Recommended for CI logs and environments without colour support.

### Rotating
- File-based handler writing to `~/aware_logs/aware.log`.
- Override location/limits with `AWARE_LOG_FILE`, `AWARE_LOG_MAX_BYTES`, `AWARE_LOG_BACKUP_COUNT`, and `AWARE_LOG_FILE_LEVEL`.

### JSON
- Structured JSON output on stdout for ingestion into log pipelines.
- Inject additional fields (`request_id`, `trace_id`, etc.) via `LoggerAdapter` or `extra` dictionary.

### Queue Console
- High-throughput profile decoupling producers via `QueueHandler`/`QueueListener`.
- Pair with metrics hooks to monitor backlog/dropped records.

## Quick Start

```python
from aware_utils.logging import configure_logging, logger, LogHelper

# Optional: customize profile or levels
configure_logging(profile="console")

logger.info("Aware logging ready")
LogHelper.section("Bootstrap", "Initialized services")
```

### Environment Overrides

```bash
# Profile selection and base level
export AWARE_LOG_PROFILE=json
export AWARE_LOG_LEVEL=DEBUG
export AWARE_LOG_OVERRIDES="aware.worker=INFO,aware.utils=WARNING"

# Rotating profile options
export AWARE_LOG_FILE=/var/log/aware/aware.log
export AWARE_LOG_MAX_BYTES=$((20 * 1024 * 1024))
export AWARE_LOG_BACKUP_COUNT=10
export AWARE_LOG_FILE_LEVEL=INFO

# Queue profile metrics
export AWARE_LOG_METRICS=stdout
```

Key env variables:

| Variable | Description |
| --- | --- |
| `AWARE_LOG_PROFILE` | Selects profile (`console`, `plain`, `rotating`, `json`, `queue_console`). |
| `AWARE_LOG_LEVEL` | Overrides root level. |
| `AWARE_LOG_OVERRIDES` | Comma-separated logger=LEVEL pairs. |
| `AWARE_LOG_FILE`, `AWARE_LOG_MAX_BYTES`, `AWARE_LOG_BACKUP_COUNT`, `AWARE_LOG_FILE_LEVEL` | Rotating file tuning. |
| `AWARE_LOG_METRICS` | `stdout` prints queue metrics, `none` disables callbacks. |

## Testing Hooks

- `reset_logging_state()` clears handlers, stops queue listeners, and resets metrics callbacks between tests.
- `configure_logging(..., reset=True)` reconfigures the logging tree deterministically.
- `set_logging_metrics_callback(...)` registers custom metrics sinks for queue profiles.

See `docs/USAGE.md` for best practices and `tests/logging/test_logging_configuration.py` for concrete usage examples.
