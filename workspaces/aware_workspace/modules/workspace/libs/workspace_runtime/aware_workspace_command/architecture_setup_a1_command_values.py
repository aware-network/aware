"""Compatibility import for the original public SDK command values and codecs."""

from aware_workspace_sdk import architecture_setup_command_values as _owner
from aware_workspace_sdk.architecture_setup_command_values import *


def __getattr__(name):
    return getattr(_owner, name)
