"""
Shared cleanup utility for per-request temporary files.

The summarization chain runs entirely in-memory for the POC, so no temp files
are created during normal operation. This utility is ready for any future path
where intermediate LLM outputs must be buffered to disk — in that case, they
must be written to the encrypted storage path defined in config.yaml.
"""

import os
import tempfile
from contextlib import asynccontextmanager

import yaml


def _get_encrypted_temp_dir() -> str:
    """Return the LUKS-encrypted storage path from config."""
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    with open(cfg_path) as f:
        cfg = yaml.safe_load(f)
    path = cfg.get("summarizer", {}).get("encrypted_storage_path")
    if not path:
        raise RuntimeError(
            "summarizer.encrypted_storage_path must be set in config.yaml — "
            "no /tmp fallback is permitted (FERPA requires LUKS-encrypted storage)."
        )
    return path


@asynccontextmanager
async def temp_file_context(suffix: str = "", prefix: str = "securepsych_sum_"):
    """
    Async context manager that yields a temp file path and guarantees deletion
    on exit — even if the block raises an exception.

    Usage:
        async with temp_file_context(suffix=".txt") as path:
            with open(path, "w") as f:
                f.write(intermediate_output)
            # ... process ...
        # file is deleted here automatically
    """
    tmp_path = None
    try:
        enc_dir = _get_encrypted_temp_dir()
        fd, tmp_path = tempfile.mkstemp(
            suffix=suffix, prefix=prefix, dir=enc_dir)
        os.close(fd)
        yield tmp_path
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def cleanup_dir(directory: str) -> int:
    """
    Delete all files inside a directory (non-recursive). Returns the count of
    files removed. Used to purge orphaned temp files after a session.
    """
    removed = 0
    if not os.path.isdir(directory):
        return removed
    for name in os.listdir(directory):
        path = os.path.join(directory, name)
        if os.path.isfile(path):
            os.remove(path)
            removed += 1
    return removed
