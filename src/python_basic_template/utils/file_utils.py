import os, json
from pathlib import Path
from typing import Union, Any, List

def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure the directory exists (create parents as needed) and return the Path."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_as_json(data: Any, file_path: str, indent: int = 4, ensure_ascii: bool = False) -> None:
    """Write JSON-serializable data to file_path, creating parent dirs as needed, with errors clarified."""
    try:
        file_dir = os.path.dirname(file_path)
        ensure_dir(file_dir)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
    
    except TypeError as e:
        raise TypeError(f"Data is not JSON serializable: {e}")
    except PermissionError as e:
        raise PermissionError(f"Permission denied when writing to {file_path}: {e}")
    except Exception as e:
        raise Exception(f"Failed to save JSON file: {e}")


def open_json(file_path: str) -> Any:
    """Read JSON from file_path and return parsed data, with clear errors."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data

    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in file {file_path}: {e}", e.doc, e.pos)
    except PermissionError as e:
        raise PermissionError(f"Permission denied when reading {file_path}: {e}")
    except Exception as e:
        raise Exception(f"Failed to read JSON file: {e}")


def get_directory_files_list(directory: Path) -> List[Path]:
    """Get a list of files in a directory."""
    return [f.name for f in directory.iterdir() if f.is_file()]