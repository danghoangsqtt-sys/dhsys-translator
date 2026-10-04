"""Guard deletion of per-task scratch data."""

import shutil
from pathlib import Path

from videotrans.configure import config


def _clear_managed_cache(cache_folder):
    """Delete a task cache strictly inside the application's temp directory."""
    configured_root = Path(config.TEMP_DIR)
    root = configured_root.resolve()
    supplied = Path(cache_folder).absolute()
    cache = supplied.resolve()
    if cache == root or not cache.is_relative_to(root):
        raise ValueError(f"Refusing to clear cache outside the managed temp directory: {cache_folder}")

    current = supplied
    while current != root and current != current.parent:
        if current.is_symlink():
            raise ValueError(f"Refusing to clear symlinked cache: {cache_folder}")
        current = current.parent
    if current != root or configured_root.is_symlink():
        raise ValueError(f"Refusing to clear cache outside the managed temp directory: {cache_folder}")

    if cache.is_dir():
        shutil.rmtree(cache)
