import argparse
import os
import tempfile
from pathlib import Path
from typing import Any

from aware_file_system.utils import script as script_utils
from aware_file_system.config import Config


def get_user_input(prompt: str, default: Any = None) -> str:
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else str(default)
    return input(f"{prompt}: ").strip()


def get_tmp_dir() -> str:
    tmp_root = Path(tempfile.gettempdir()) / "aware"
    tmp_root.mkdir(parents=True, exist_ok=True)
    return str(tmp_root)


def setup(description: str) -> Config:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--root_path",
        help="Path to the root directory of the project to analyze",
    )
    parser.add_argument(
        "--config_file_name",
        default="default.yaml",
        help="Path to the configuration file",
    )
    args = parser.parse_args()

    config = Config.load_from_file_name(args.config_file_name)
    if not args.root_path:
        config.file_system.root_path = script_utils.get_user_input(
            "Enter the root directory path",
            config.file_system.root_path,
        )
    else:
        config.file_system.root_path = args.root_path

    if not os.path.isdir(config.file_system.root_path):
        print(f"Error: {config.file_system.root_path} is not a valid directory")
        raise ValueError

    return config
