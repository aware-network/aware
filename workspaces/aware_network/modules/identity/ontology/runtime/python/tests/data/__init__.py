from pathlib import Path


def get_file_path(file_name: str) -> str:
    """Get the path of a file"""
    return str(Path(__file__).parent / file_name)
