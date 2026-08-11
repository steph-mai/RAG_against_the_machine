"""Cache utilities for the processed index."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.core.errors import RagLoadError


@lru_cache(maxsize=1)
def load_index(
        index_path: str = "data/processed/index.json") -> dict[str, Any]:
    """Load the index from disk and cache it in memory.

    Args:
        index_path: Path to the processed index file.

    Returns:
        A dictionary containing the loaded index data.

    Raises:
        RagLoadError: If the index file does not exist.
    """
    path = Path(index_path)
    if not path.exists():
        raise RagLoadError(f"Index not found at {index_path}.")

    with open(path, "r", encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
        return data


def clear_index_cache() -> None:
    """Clear the cached index from memory.

    Call this function after regenerating the index so the next access
    reloads the updated data from disk.
    """
    load_index.cache_clear()
