from pathlib import Path
from typing import Union

cache_path = Path("cache")


def set_cache_path(path: Union[str, Path]):
    global cache_path
    cache_path = Path(path)


def get_cache_path() -> Path:
    return cache_path
