from pathlib import Path


def get_server_logger_path():
    return Path(__file__).parent / "logs"
