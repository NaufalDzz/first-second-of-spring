#!/usr/bin/env python3
"""The First Second of Spring - offline make.fun image entry.

Writes the bundled artwork (artwork.jpg, a JPEG) byte-for-byte to
$MAKEFUN_OUTPUT_DIR/entry.png (default /output). The file's magic bytes,
not its extension, identify the format. Standard library only.
"""
import os
import stat
import sys
import tempfile
from pathlib import Path

ASSET = Path(__file__).resolve().parent / "artwork.jpg"
MAX_BYTES = 1048576
OUTPUT_NAME = "entry.png"
# World-readable so a grader running under a different UID can collect it.
# mkstemp() always creates 0600; fchmod() is not affected by the umask.
OUTPUT_MODE = 0o644


def output_dir():
    return Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")


def load_artwork(path=ASSET):
    if path.stat().st_size > MAX_BYTES:
        raise ValueError(f"artwork larger than {MAX_BYTES} bytes")
    data = path.read_bytes()
    if not 1 <= len(data) <= MAX_BYTES:
        raise ValueError(f"artwork size {len(data)} outside 1..{MAX_BYTES} bytes")
    if not (data.startswith(b"\xff\xd8") and data.endswith(b"\xff\xd9")):
        raise ValueError("artwork is not a complete JPEG (missing SOI/EOI)")
    return data


def write_atomic(target, data):
    """Write via a temp file in the same directory, then rename into place.

    The temp file is chmod'ed to OUTPUT_MODE through its descriptor before it
    is closed and renamed, so the final file is never published as 0600.
    """
    fd, tmp = tempfile.mkstemp(prefix=".entry-", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as fh:
            os.fchmod(fh.fileno(), OUTPUT_MODE)
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, target)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    if target.read_bytes() != data:
        raise OSError(f"verification failed for {target}")
    mode = stat.S_IMODE(target.stat().st_mode)
    if mode & 0o444 != 0o444:
        raise OSError(f"{target} has mode {mode:o}, not readable by other users")


def main():
    try:
        data = load_artwork()
        out = output_dir()
        if not out.is_dir():
            raise OSError(f"output directory does not exist: {out}")
        target = out / OUTPUT_NAME
        write_atomic(target, data)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"wrote {target} ({len(data)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
