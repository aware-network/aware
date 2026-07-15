"""
Aware Utilities

Common utility helpers shared across Aware projects. This package provides the
logging helpers, text normalization, serialization helpers,
and strict Aware state-root helpers.
"""

from pkgutil import extend_path

from .decimal_normalizer import (
    normalize_decimal,
    DECIMAL_CONTEXT,
    DECIMAL_PRECISION,
    MAX_DIGITS,
)
from .description_normalizer import DescriptionNormalizer
from .logging import (
    LogHelper,
    logger,
    configure_logging,
    get_active_config,
    register_profile,
    list_profiles,
    register_logger,
    clear_registry,
    set_logging_metrics_callback,
    reset_logging_state,
    log_section,
    log_stage,
    log_substage,
    log_progress,
    log_success,
    log_warning,
    log_error,
    log_summary,
    log_metrics,
    log_file_ops,
    log_changes,
    log_debug,
    log_separator,
)
from .path_utils import normalize_ci_path, normalize_ci_path_obj
from .rotating_log_config import setup_rotating_logs, get_log_tail
from .safe_copy import safe_deep_copy, deep_copy_context
from .string_transform import (
    normalize_identifier,
    pluralize,
    singularize,
    strip_fk_suffix,
    to_snake_case,
    to_camel_case,
    to_pascal_case,
)
from .secrets import (
    SecretSpec,
    SecretResolutionInfo,
    resolve_secret,
    resolve_secret_info,
    require_secret,
    register_secret,
    register_resolver,
    use_dotenv,
    use_secrets_dir,
    list_secrets,
    describe_secret,
)

__path__ = extend_path(__path__, __name__)

__all__ = [
    "DECIMAL_CONTEXT",
    "DECIMAL_PRECISION",
    "MAX_DIGITS",
    "DescriptionNormalizer",
    "LogHelper",
    "configure_logging",
    "get_active_config",
    "register_profile",
    "list_profiles",
    "register_logger",
    "clear_registry",
    "set_logging_metrics_callback",
    "reset_logging_state",
    "deep_copy_context",
    "get_log_tail",
    "log_changes",
    "log_debug",
    "log_error",
    "log_file_ops",
    "log_metrics",
    "log_progress",
    "log_section",
    "log_separator",
    "log_stage",
    "log_substage",
    "log_success",
    "log_summary",
    "log_warning",
    "logger",
    "normalize_decimal",
    "normalize_identifier",
    "normalize_ci_path",
    "normalize_ci_path_obj",
    "pluralize",
    "setup_rotating_logs",
    "singularize",
    "safe_deep_copy",
    "strip_fk_suffix",
    "to_snake_case",
    "to_camel_case",
    "to_pascal_case",
    "SecretSpec",
    "SecretResolutionInfo",
    "describe_secret",
    "list_secrets",
    "register_resolver",
    "register_secret",
    "require_secret",
    "resolve_secret",
    "resolve_secret_info",
    "use_dotenv",
    "use_secrets_dir",
]
