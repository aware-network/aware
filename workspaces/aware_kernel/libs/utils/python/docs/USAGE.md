# Aware Utils Logging Usage Guide

This guide summarises recommended patterns for configuring logging with `aware_utils.logging`.

## Profiles at a Glance

| Profile | Handler | When to use |
|---------|---------|-------------|
| `console` (default) | Colourised stdout | Local development, CLI tools |
| `plain` | Plain stdout | CI pipelines, log aggregators that dislike ANSI |
| `rotating` | Rotating file in `~/aware_logs/aware.log` | Long-lived services needing persistent logs |
| `json` | Structured JSON stdout | Centralised log ingestion (e.g., Loki, Datadog) |
| `queue_console` | Queue + colourised stdout | High-volume, low-latency producers |

## Typical Boot Sequence

```python
from aware_utils.logging import configure_logging, LogHelper

configure_logging(profile="queue_console")
LogHelper.section("Bootstrap", "Starting services")
```

### Registering Custom Loggers

```python
from aware_utils.logging import configure_logging, register_logger

register_logger("aware.worker", level="DEBUG", propagate=False)
configure_logging()
```

## Environment-First Configuration

| Variable | Effect |
|----------|--------|
| `AWARE_LOG_PROFILE` | Select profile (`console`, `plain`, `rotating`, `json`, `queue_console`). |
| `AWARE_LOG_LEVEL` | Override root level. |
| `AWARE_LOG_OVERRIDES` | Comma-separated list of `logger=LEVEL` pairs. |
| `AWARE_LOG_FILE` | Path for rotating profile (`~/aware_logs/aware.log` default). |
| `AWARE_LOG_MAX_BYTES` | Rotate when file exceeds this size (bytes). |
| `AWARE_LOG_BACKUP_COUNT` | Number of rotated files to keep. |
| `AWARE_LOG_FILE_LEVEL` | Level for rotating handler. |
| `AWARE_LOG_METRICS` | `stdout` prints queue metrics, `none` disables callbacks. |

Example deployment snippet:

```bash
export AWARE_LOG_PROFILE=rotating
export AWARE_LOG_FILE=/var/log/aware/aware.log
export AWARE_LOG_MAX_BYTES=$((50 * 1024 * 1024))
export AWARE_LOG_BACKUP_COUNT=7
export AWARE_LOG_METRICS=stdout
```

## Metrics Hooks

Queue-based profiles can publish metrics through `set_logging_metrics_callback`:

```python
from aware_utils.logging import configure_logging, set_logging_metrics_callback

metrics = []

set_logging_metrics_callback(lambda metric: metrics.append(metric))
configure_logging(profile="queue_console")
```

Each callback receives `LoggingMetric(handler_name, emitted, dropped, queue_size)`.

## Testing Tips

- Use `reset_logging_state()` in fixtures to avoid handler leakage.
- Monkeypatch `logging.Logger.info` or handler `emit` methods to capture outputs for assertions.
- When testing rotating profile behaviour, point `AWARE_LOG_FILE` to a temporary directory.

## Additional Resources

- Module docs: `docs/logging.md`
- Tests: `tests/logging/test_logging_configuration.py`
