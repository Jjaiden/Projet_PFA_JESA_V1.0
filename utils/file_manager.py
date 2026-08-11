# JESA_DMAT/utils/file_manager.py
"""
Generic file and directory management utilities for the JESA DMAT application.

Provides safe, logged functions for common filesystem operations such as
creating directories, copying, moving, deleting files, and reading/writing
text or binary content. All paths are handled as ``pathlib.Path`` objects.

**Symlink handling:**
- ``shutil.copy2`` follows symlinks (copies the target).
- ``path.unlink`` removes the symlink itself.
- ``shutil.rmtree`` follows symlinks by default.
- ``path.rename`` operates on the symlink, not the target.
- Module does not provide explicit ``follow_symlinks`` parameters.

**Platform differences:**
- ``rename()`` on Windows raises ``FileExistsError`` if destination exists;
  on Unix it silently overwrites. Use ``replace()`` (``os.replace``) for
  cross-platform atomic overwrite.
- ``shutil.move`` falls back to copy-then-delete across filesystems.

**Security:**
This module does not sanitize paths. When used with user-supplied input,
sanitize paths before calling these functions.

**Thread safety:**
Atomic write operations use ``tempfile.mkstemp`` to generate unique
temporary filenames, avoiding collisions between concurrent writers.

This module is **completely generic** and contains no business logic.
It can be reused in any Python project without modification.
"""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Union

from config.settings import settings

_logger = logging.getLogger(__name__)

__all__ = [
    # Frontend functions
    "exists",
    "is_file",
    "is_directory",
    "ensure_directory",
    "delete_file",
    "delete_directory",
    "copy_file",
    "copy_into_directory",
    "move_file",
    "move_into_directory",
    "rename",
    "replace",
    "read_text",
    "write_text",
    "read_bytes",
    "write_bytes",
    "file_size",
    "list_files",
    "list_directories",
    "resolve_path",
    "get_extension",
    "change_extension",
    "touch",
    # Backend functions (added)
    "directory_exists",
    "ensure_file_exists",
    "get_output_directory",
    "get_referentiel_path",
    "get_recommendations_path",
    "get_assessment_path",
    "sanitize_filename",
    "build_output_path",
    "is_empty_file",
    # Aliases for backward compatibility
    "file_exists",  # same as is_file
]


# ======================================================================
# Private validation helpers
# ======================================================================

def _to_path(obj: Union[str, Path, None], name: str = "path") -> Path:
    """Convert a string or Path to a Path, raising on invalid types."""
    if obj is None:
        raise TypeError(f"Expected a path-like object for '{name}', got None")
    if isinstance(obj, str):
        return Path(obj)
    if isinstance(obj, Path):
        return obj
    raise TypeError(f"Expected a Path or str for '{name}', got {type(obj).__name__}")


def _assert_path(obj: object, name: str = "path") -> Path:
    """Ensure ``obj`` is a path-like object (str or Path) and return a Path."""
    if isinstance(obj, str):
        return Path(obj)
    if isinstance(obj, Path):
        return obj
    raise TypeError(f"Expected a Path or str for '{name}', got {type(obj).__name__}")


def _assert_file(path: Path) -> None:
    """Ensure ``path`` exists and is a regular file."""
    if not path.is_file():
        if path.is_dir():
            raise IsADirectoryError(f"Expected a file, got a directory: {path}")
        raise FileNotFoundError(f"File not found: {path}")


def _assert_directory(path: Path) -> None:
    """Ensure ``path`` exists and is a directory."""
    if not path.is_dir():
        if path.exists():
            raise NotADirectoryError(f"Not a directory: {path}")
        raise FileNotFoundError(f"Directory not found: {path}")


def _ensure_parent(target: Path) -> Path:
    """Return the parent directory to create for a given target path."""
    if target.exists() and target.is_dir():
        return target
    return target.parent


def _fsync_parent(path: Path) -> None:
    """Flush the directory containing ``path`` to ensure durability.

    This is a best-effort operation; failures are logged but not raised.
    """
    try:
        fd = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except (OSError, AttributeError):
        # os.O_DIRECTORY not available on all platforms
        _logger.debug("Could not fsync parent directory of %s", path)


# ======================================================================
# Path inspection
# ======================================================================

def exists(path: Union[str, Path]) -> bool:
    """Check whether a path exists (file or directory)."""
    return _assert_path(path).exists()


def is_file(path: Union[str, Path]) -> bool:
    """Check whether a path exists and is a regular file."""
    return _assert_path(path).is_file()


def is_directory(path: Union[str, Path]) -> bool:
    """Check whether a path exists and is a directory."""
    return _assert_path(path).is_dir()


def directory_exists(path: Union[str, Path]) -> bool:
    """Alias for is_directory: check whether a path exists and is a directory."""
    return is_directory(path)


def file_exists(path: Union[str, Path]) -> bool:
    """Alias for is_file: check whether a path exists and is a regular file."""
    return is_file(path)


# ======================================================================
# Directory management
# ======================================================================

def ensure_directory(path: Union[str, Path]) -> Path:
    """Create a directory recursively if it does not exist.

    Uses ``path.mkdir(parents=True, exist_ok=True)`` which is atomic
    at the OS level for directory creation.

    Args:
        path: Directory path to create (str or Path).

    Returns:
        The resolved ``Path`` object for the created directory.

    Raises:
        TypeError: If ``path`` is not a path-like object.
        NotADirectoryError: If a file already exists at ``path``.
        OSError: Re-raised if directory creation fails.
    """
    path_obj = _assert_path(path)

    try:
        path_obj.mkdir(parents=True, exist_ok=True)
    except OSError:
        _logger.exception("Failed to create directory: %s", path_obj)
        raise

    if not path_obj.is_dir():
        raise NotADirectoryError(f"Cannot create directory: a file already exists at {path_obj}")

    _logger.debug("Directory ensured: %s", path_obj)
    return path_obj


def delete_directory(path: Union[str, Path], recursive: bool = False) -> Path:
    """Delete a directory.

    By default only removes empty directories. Set ``recursive=True``
    to remove the entire directory tree using :func:`shutil.rmtree`.

    **Warning:** ``recursive=True`` will delete the entire directory tree
    without confirmation. Ensure the path is correct before calling.

    Args:
        path: Directory path to delete.
        recursive: If ``True``, delete recursively (default ``False``).

    Returns:
        The ``Path`` of the deleted directory.

    Raises:
        TypeError: If ``path`` is not a path-like object.
        FileNotFoundError: If the directory does not exist.
        NotADirectoryError: If ``path`` points to a file, not a directory.
        OSError: Re-raised if deletion fails.
    """
    path_obj = _assert_path(path)
    _assert_directory(path_obj)

    try:
        if recursive:
            _logger.debug("Recursively deleting directory: %s", path_obj)
            shutil.rmtree(path_obj)
        else:
            _logger.debug("Removing empty directory: %s", path_obj)
            path_obj.rmdir()
    except OSError:
        _logger.exception("Failed to delete directory: %s", path_obj)
        raise

    _logger.info("Directory deleted: %s", path_obj)
    return path_obj


# ======================================================================
# File deletion
# ======================================================================

def delete_file(path: Union[str, Path], missing_ok: bool = True) -> Path:
    """Delete a file safely.

    Uses atomic approach: attempts ``path.unlink()`` and catches
    ``FileNotFoundError`` to avoid race conditions.

    Args:
        path: File path to delete.
        missing_ok: If True, do not raise if the file does not exist.

    Returns:
        The ``Path`` of the deleted file (or the input path if missing).

    Raises:
        TypeError: If ``path`` is not a path-like object.
        IsADirectoryError: If ``path`` points to a directory.
        OSError: Re-raised if deletion fails for permissions or other reasons.
    """
    path_obj = _assert_path(path)

    if path_obj.is_dir():
        raise IsADirectoryError(f"Expected a file, got a directory: {path_obj}")

    try:
        path_obj.unlink()
    except FileNotFoundError:
        if missing_ok:
            _logger.debug("File not found (ignored): %s", path_obj)
            return path_obj
        raise
    except OSError:
        _logger.exception("Failed to delete file: %s", path_obj)
        raise

    _logger.info("File deleted: %s", path_obj)
    return path_obj


# ======================================================================
# File copy
# ======================================================================

def copy_file(
    src: Union[str, Path],
    dst: Union[str, Path],
    create_parent: bool = True,
) -> Path:
    """Copy a file to a new file path.

    ``dst`` is always treated as the target **file** path, never as a
    directory. If you need to copy a file into a directory, use
    :func:`copy_into_directory`.

    Creates destination parent directories automatically unless
    ``create_parent=False``.
    Uses :func:`shutil.copy2` to preserve metadata.

    Args:
        src: Source file path.
        dst: Target file path (not a directory).
        create_parent: If True, create missing parent directories of dst.

    Returns:
        The destination ``Path`` of the copied file.

    Raises:
        TypeError: If any argument is not a path-like object.
        FileNotFoundError: If the source file does not exist.
        IsADirectoryError: If ``src`` is a directory or ``dst`` exists
            and is a directory.
        OSError: Re-raised if the copy operation fails.
    """
    src_path = _assert_path(src, "src")
    dst_path = _assert_path(dst, "dst")
    _assert_file(src_path)

    if dst_path.exists() and dst_path.is_dir():
        raise IsADirectoryError(
            f"dst must be a file path, got a directory: {dst_path}. "
            f"Use copy_into_directory() instead."
        )

    if create_parent:
        ensure_directory(_ensure_parent(dst_path))

    try:
        result = shutil.copy2(src_path, dst_path)
    except OSError:
        _logger.exception("Failed to copy file: %s -> %s", src_path, dst_path)
        raise

    _logger.info("File copied: %s -> %s", src_path, dst_path)
    return Path(result)


def copy_into_directory(src: Union[str, Path], directory: Union[str, Path]) -> Path:
    """Copy a file into a directory, preserving the source filename.

    Args:
        src: Source file path.
        directory: Target directory. Will be created if missing.

    Returns:
        The ``Path`` of the copied file inside the directory.

    Raises:
        TypeError: If any argument is not a path-like object.
        FileNotFoundError: If the source file does not exist.
        IsADirectoryError: If ``src`` is a directory.
        NotADirectoryError: If a file exists at ``directory``.
        OSError: Re-raised if the copy operation fails.
    """
    src_path = _assert_path(src, "src")
    dir_path = _assert_path(directory, "directory")
    _assert_file(src_path)

    ensure_directory(dir_path)
    dst = dir_path / src_path.name

    try:
        result = shutil.copy2(src_path, dst)
    except OSError:
        _logger.exception("Failed to copy file: %s -> %s", src_path, dst)
        raise

    _logger.info("File copied: %s -> %s", src_path, dst)
    return Path(result)


# ======================================================================
# File move
# ======================================================================

def move_file(
    src: Union[str, Path],
    dst: Union[str, Path],
    create_parent: bool = True,
) -> Path:
    """Move a file to a new file path.

    ``dst`` is always treated as the target **file** path, never as a
    directory. If you need to move a file into a directory, use
    :func:`move_into_directory`.

    Creates destination parent directories automatically unless
    ``create_parent=False``.

    **Cross-filesystem moves:**
    If source and destination are on different filesystems,
    :func:`shutil.move` falls back to copy-then-delete, which is not atomic.

    Args:
        src: Source file path.
        dst: Target file path (not a directory).
        create_parent: If True, create missing parent directories of dst.

    Returns:
        The actual destination ``Path`` of the moved file.

    Raises:
        TypeError: If any argument is not a path-like object.
        FileNotFoundError: If the source file does not exist.
        IsADirectoryError: If ``src`` is a directory or ``dst`` exists
            and is a directory.
        OSError: Re-raised if the move operation fails.
    """
    src_path = _assert_path(src, "src")
    dst_path = _assert_path(dst, "dst")
    _assert_file(src_path)

    if dst_path.exists() and dst_path.is_dir():
        raise IsADirectoryError(
            f"dst must be a file path, got a directory: {dst_path}. "
            f"Use move_into_directory() instead."
        )

    if create_parent:
        ensure_directory(_ensure_parent(dst_path))

    try:
        result = shutil.move(src_path, dst_path)
    except OSError:
        _logger.exception("Failed to move file: %s -> %s", src_path, dst_path)
        raise

    _logger.info("File moved: %s -> %s", src_path, dst_path)
    return Path(result)


def move_into_directory(src: Union[str, Path], directory: Union[str, Path]) -> Path:
    """Move a file into a directory, preserving the source filename.

    Args:
        src: Source file path.
        directory: Target directory. Will be created if missing.

    Returns:
        The ``Path`` of the moved file inside the directory.

    Raises:
        TypeError: If any argument is not a path-like object.
        FileNotFoundError: If the source file does not exist.
        IsADirectoryError: If ``src`` is a directory.
        NotADirectoryError: If a file exists at ``directory``.
        OSError: Re-raised if the move operation fails.
    """
    src_path = _assert_path(src, "src")
    dir_path = _assert_path(directory, "directory")
    _assert_file(src_path)

    ensure_directory(dir_path)
    dst = dir_path / src_path.name

    try:
        result = shutil.move(src_path, dst)
    except OSError:
        _logger.exception("Failed to move file: %s -> %s", src_path, dst)
        raise

    _logger.info("File moved: %s -> %s", src_path, dst)
    return Path(result)


# ======================================================================
# Rename & Replace
# ======================================================================

def rename(src: Union[str, Path], dst: Union[str, Path]) -> Path:
    """Rename a file or directory.

    Creates destination parent directories automatically.

    **Platform difference:** ``path.rename`` on Windows raises
    ``FileExistsError`` if the destination exists; on Unix it silently
    overwrites. For cross-platform atomic overwrite, use :func:`replace`.

    Args:
        src: Source path (file or directory).
        dst: Target path (not a directory).

    Returns:
        The destination ``Path``.

    Raises:
        TypeError: If any argument is not a path-like object.
        FileNotFoundError: If the source does not exist.
        IsADirectoryError: If ``dst`` exists and is a directory while
            ``src`` is a file, or vice versa.
        OSError: Re-raised if the rename fails.
    """
    src_path = _assert_path(src, "src")
    dst_path = _assert_path(dst, "dst")

    if not src_path.exists():
        raise FileNotFoundError(f"Source not found: {src_path}")

    if dst_path.exists():
        if src_path.is_dir() and dst_path.is_file():
            raise IsADirectoryError(f"Cannot rename directory {src_path} to file {dst_path}")
        if src_path.is_file() and dst_path.is_dir():
            raise IsADirectoryError(
                f"Cannot rename file {src_path} to directory {dst_path}. "
                f"Use move_into_directory() instead."
            )

    ensure_directory(_ensure_parent(dst_path))

    try:
        result = src_path.rename(dst_path)
    except OSError:
        _logger.exception("Failed to rename: %s -> %s", src_path, dst_path)
        raise

    _logger.info("Renamed: %s -> %s", src_path, dst_path)
    return Path(result)


def replace(src: Union[str, Path], dst: Union[str, Path]) -> Path:
    """Atomically replace a file or directory.

    Uses :func:`os.replace` which is atomic and cross-platform when source
    and destination are on the same filesystem. If ``dst`` exists, it is
    silently replaced.

    Creates destination parent directories automatically.

    Args:
        src: Source path (file or directory).
        dst: Target path.

    Returns:
        The destination ``Path``.

    Raises:
        TypeError: If any argument is not a path-like object.
        FileNotFoundError: If the source does not exist.
        IsADirectoryError: If ``src`` is a file and ``dst`` is an existing
            directory, or vice versa.
        OSError: Re-raised if the replace fails (e.g. cross-filesystem).
    """
    src_path = _assert_path(src, "src")
    dst_path = _assert_path(dst, "dst")

    if not src_path.exists():
        raise FileNotFoundError(f"Source not found: {src_path}")

    if dst_path.exists():
        if src_path.is_dir() != dst_path.is_dir():
            raise IsADirectoryError(
                f"Cannot replace {'directory' if src_path.is_dir() else 'file'} "
                f"with {'directory' if dst_path.is_dir() else 'file'}"
            )

    ensure_directory(_ensure_parent(dst_path))

    try:
        os.replace(src_path, dst_path)
    except OSError:
        _logger.exception("Failed to replace: %s -> %s", src_path, dst_path)
        raise

    _logger.info("Replaced: %s -> %s", src_path, dst_path)
    return dst_path


# ======================================================================
# Content I/O
# ======================================================================

def read_text(path: Union[str, Path], encoding: str = "utf-8") -> str:
    """Read the entire contents of a text file.

    **Note:** Loads the entire file into memory. Not suitable for files
    larger than ~100 MB.

    Args:
        path: Path to the text file.
        encoding: Text encoding (default ``utf-8``).

    Returns:
        The file contents as a string.

    Raises:
        TypeError: If ``path`` is not a path-like object.
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If ``path`` points to a directory.
        OSError: Re-raised if the read operation fails.
    """
    path_obj = _assert_path(path)
    _assert_file(path_obj)

    try:
        data = path_obj.read_text(encoding=encoding)
    except OSError:
        _logger.exception("Failed to read text file: %s", path_obj)
        raise

    _logger.debug("Text file read: %s", path_obj)
    return data


def write_text(
    path: Union[str, Path],
    text: str,
    encoding: str = "utf-8",
    atomic: bool = False,
) -> Path:
    """Write a string to a text file, overwriting if it exists.

    Automatically creates missing parent directories.

    Args:
        path: Path to the output file.
        text: String content to write.
        encoding: Text encoding (default ``utf-8``).
        atomic: If ``True``, write to a temporary file then atomically
            replace the destination. This prevents corruption if the
            process crashes mid-write and avoids collisions between
            concurrent writers (default ``False``).

    Returns:
        The ``Path`` of the written file.

    Raises:
        TypeError: If ``path`` is not a path-like object or
            ``text`` is not a string.
        OSError: Re-raised if the write operation fails.
    """
    path_obj = _assert_path(path)
    if not isinstance(text, str):
        raise TypeError(f"Expected a string for text, got {type(text).__name__}")

    ensure_directory(path_obj.parent)

    if atomic:
        _write_atomic_text(path_obj, text, encoding)
    else:
        try:
            path_obj.write_text(text, encoding=encoding)
        except OSError:
            _logger.exception("Failed to write text file: %s", path_obj)
            raise

    _logger.info("Text file written: %s", path_obj)
    return path_obj


def read_bytes(path: Union[str, Path]) -> bytes:
    """Read the entire contents of a binary file.

    **Note:** Loads the entire file into memory. Not suitable for files
    larger than ~100 MB.

    Args:
        path: Path to the binary file.

    Returns:
        The file contents as :class:`bytes`.

    Raises:
        TypeError: If ``path`` is not a path-like object.
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If ``path`` points to a directory.
        OSError: Re-raised if the read operation fails.
    """
    path_obj = _assert_path(path)
    _assert_file(path_obj)

    try:
        data = path_obj.read_bytes()
    except OSError:
        _logger.exception("Failed to read binary file: %s", path_obj)
        raise

    _logger.debug("Binary file read: %s", path_obj)
    return data


def write_bytes(path: Union[str, Path], data: bytes, atomic: bool = False) -> Path:
    """Write binary data to a file, overwriting if it exists.

    Automatically creates missing parent directories.

    Args:
        path: Path to the output file.
        data: Binary content to write.
        atomic: If ``True``, write to a temporary file then atomically
            replace the destination (default ``False``).

    Returns:
        The ``Path`` of the written file.

    Raises:
        TypeError: If ``path`` is not a path-like object or
            ``data`` is not :class:`bytes`.
        OSError: Re-raised if the write operation fails.
    """
    path_obj = _assert_path(path)
    if not isinstance(data, bytes):
        raise TypeError(f"Expected bytes for data, got {type(data).__name__}")

    ensure_directory(path_obj.parent)

    if atomic:
        _write_atomic_bytes(path_obj, data)
    else:
        try:
            path_obj.write_bytes(data)
        except OSError:
            _logger.exception("Failed to write binary file: %s", path_obj)
            raise

    _logger.info("Binary file written: %s", path_obj)
    return path_obj


# ======================================================================
# Atomic write helpers
# ======================================================================

def _write_atomic_text(path: Path, text: str, encoding: str) -> None:
    """Write text atomically using a temporary file + os.replace()."""
    fd, tmp_path = tempfile.mkstemp(
        suffix=".tmp",
        prefix=path.name + ".",
        dir=path.parent,
    )
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
        _fsync_parent(path)
    except OSError:
        _logger.exception("Failed atomic write to: %s", path)
        raise
    finally:
        # Ensure temp file is removed even on unexpected errors
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except OSError:
            pass


def _write_atomic_bytes(path: Path, data: bytes) -> None:
    """Write bytes atomically using a temporary file + os.replace()."""
    fd, tmp_path = tempfile.mkstemp(
        suffix=".tmp",
        prefix=path.name + ".",
        dir=path.parent,
    )
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
        _fsync_parent(path)
    except OSError:
        _logger.exception("Failed atomic write to: %s", path)
        raise
    finally:
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except OSError:
            pass


# ======================================================================
# Information
# ======================================================================

def file_size(path: Union[str, Path]) -> int:
    """Return the file size in bytes.

    Args:
        path: Path to the file.

    Returns:
        File size as an integer (bytes).

    Raises:
        TypeError: If ``path`` is not a path-like object.
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If ``path`` points to a directory.
        OSError: Re-raised if the stat operation fails.
    """
    path_obj = _assert_path(path)
    _assert_file(path_obj)

    try:
        size = path_obj.stat().st_size
    except OSError:
        _logger.exception("Failed to get file size: %s", path_obj)
        raise

    _logger.debug("File size for %s: %d bytes", path_obj, size)
    return size


def list_files(directory: Union[str, Path], pattern: str = "*") -> list[Path]:
    """List files in a directory, optionally filtered by a glob pattern.

    The pattern follows :meth:`pathlib.Path.glob` rules (supports ``*``,
    ``?``, ``**`` for recursive matching).

    Args:
        directory: Directory to scan. Must exist.
        pattern: Glob pattern to filter files (default ``"*"`` for all).

    Returns:
        A sorted list of file paths matching the pattern.

    Raises:
        TypeError: If ``directory`` is not a path-like object.
        FileNotFoundError: If ``directory`` does not exist.
        NotADirectoryError: If ``directory`` is not a directory.
    """
    dir_obj = _assert_path(directory, "directory")
    _assert_directory(dir_obj)

    files = sorted(p for p in dir_obj.rglob(pattern) if p.is_file())
    _logger.debug("Listed %d files in %s (pattern='%s')", len(files), dir_obj, pattern)
    return files


def list_directories(directory: Union[str, Path]) -> list[Path]:
    """List subdirectories in a directory, sorted alphabetically.

    Args:
        directory: Directory to scan. Must exist.

    Returns:
        A sorted list of subdirectory paths.

    Raises:
        TypeError: If ``directory`` is not a path-like object.
        FileNotFoundError: If ``directory`` does not exist.
        NotADirectoryError: If ``directory`` is not a directory.
    """
    dir_obj = _assert_path(directory, "directory")
    _assert_directory(dir_obj)

    dirs = sorted(p for p in dir_obj.iterdir() if p.is_dir())
    _logger.debug("Listed %d subdirectories in %s", len(dirs), dir_obj)
    return dirs


# ======================================================================
# Path manipulation helpers
# ======================================================================

def resolve_path(path: Union[str, Path], base_dir: Optional[Union[str, Path]] = None) -> Path:
    """Return the absolute, resolved version of a path.

    Uses ``resolve(strict=False)`` to avoid errors for non-existent paths.
    If ``base_dir`` is provided and the path is relative, it is resolved
    relative to that directory.

    **Platform note:** Under Windows, resolving a path on a non-existent
    drive (e.g. ``Z:\\foo``) may still raise an ``OSError``.

    Args:
        path: Path to resolve.
        base_dir: Optional base directory for relative paths.

    Returns:
        Absolute :class:`pathlib.Path` with all symlinks resolved.

    Raises:
        TypeError: If ``path`` is not a path-like object.
        OSError: On Windows, if the drive does not exist.
    """
    candidate = _assert_path(path)

    if not candidate.is_absolute() and base_dir is not None:
        base = _assert_path(base_dir, "base_dir")
        candidate = base / candidate

    try:
        resolved = candidate.resolve(strict=False)
    except OSError:
        _logger.exception("Failed to resolve path: %s", candidate)
        raise

    _logger.debug("Resolved path: %s -> %s", candidate, resolved)
    return resolved


def get_extension(path: Union[str, Path]) -> str:
    """Return the lowercase file extension, including the leading dot.

    Args:
        path: File path.

    Returns:
        Lowercase extension string (e.g. ``".xlsx"``).

    Raises:
        TypeError: If ``path`` is not a path-like object.
    """
    return _assert_path(path).suffix.lower()


def change_extension(path: Union[str, Path], extension: str) -> Path:
    """Return a new path with the file extension replaced.

    If ``extension`` does not start with a dot, one is automatically
    added.

    Args:
        path: Original file path.
        extension: New extension (e.g. ``".csv"`` or ``"csv"``).
            Must not be empty or ``"."`` only.

    Returns:
        A new ``Path`` with the extension changed.

    Raises:
        TypeError: If ``path`` is not a path-like object or
            ``extension`` is not a string.
        ValueError: If ``extension`` is empty or ``"."`` only.
    """
    path_obj = _assert_path(path)
    if not isinstance(extension, str):
        raise TypeError(f"Expected a string for extension, got {type(extension).__name__}")

    if not extension.startswith("."):
        extension = "." + extension
    if extension == ".":
        raise ValueError("Extension cannot be '.' only")

    return path_obj.with_suffix(extension)


def touch(path: Union[str, Path]) -> Path:
    """Create an empty file if it does not exist.

    Creates parent directories automatically. Updates the modification
    time if the file already exists.

    Args:
        path: File path to touch.

    Returns:
        The ``Path`` of the touched file.

    Raises:
        TypeError: If ``path`` is not a path-like object.
        IsADirectoryError: If ``path`` points to an existing directory.
        OSError: Re-raised if the operation fails.
    """
    path_obj = _assert_path(path)

    if path_obj.is_dir():
        raise IsADirectoryError(f"Cannot touch a directory: {path_obj}")

    ensure_directory(path_obj.parent)

    try:
        path_obj.touch(exist_ok=True)
    except OSError:
        _logger.exception("Failed to touch file: %s", path_obj)
        raise

    _logger.debug("File touched: %s", path_obj)
    return path_obj


# ======================================================================
# Backend-specific functions (rely on config.settings)
# ======================================================================

def get_output_directory(create: bool = True) -> Path:
    """
    Return the output directory configured in settings.py.

    By default, the directory is created if it does not exist.
    """
    output_dir = Path(settings.OUTPUT_DIR)

    if create:
        ensure_directory(output_dir)

    return output_dir


def ensure_file_exists(
    path: Union[str, Path],
    description: Optional[str] = None,
) -> Path:
    """
    Ensure that a file exists.

    Raises FileNotFoundError if the file does not exist.
    """
    file_path = _assert_path(path)

    if not file_path.is_file():
        label = description or "File"
        raise FileNotFoundError(f"{label} not found: {file_path}")

    return file_path


def get_referentiel_path() -> Path:
    """Return the path to the referentiel workbook."""
    return Path(settings.REFERENTIEL_FILE)


def get_recommendations_path() -> Path:
    """Return the path to the recommendations knowledge base."""
    return Path(settings.RECOMMENDATIONS_FILE)


def get_assessment_path() -> Path:
    """Return the path to the Assessment.xlsx file."""
    return Path(settings.ASSESSMENT_FILE)


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """
    Sanitize a filename by replacing invalid characters.

    This function does not create or move any file.
    """
    if not isinstance(filename, str) or not filename.strip():
        raise ValueError("filename cannot be empty.")

    invalid_characters = '<>:"/\\|?*'

    if (
        not isinstance(replacement, str)
        or not replacement
        or any(c in invalid_characters for c in replacement)
    ):
        raise ValueError(
            "replacement must be a non-empty string without invalid path characters."
        )

    sanitized = "".join(
        replacement if c in invalid_characters else c
        for c in filename
    )

    sanitized = sanitized.strip()

    if not sanitized or sanitized in {".", ".."}:
        raise ValueError("Filename is invalid after sanitization.")

    return sanitized


def build_output_path(
    filename: str,
    create_directory: bool = True,
) -> Path:
    """
    Construct a path within the output directory.
    """
    safe_filename = sanitize_filename(filename)
    output_dir = get_output_directory(create=create_directory)
    return output_dir / safe_filename


def is_empty_file(path: Union[str, Path]) -> bool:
    """
    Check if a file exists and contains 0 bytes.
    """
    return file_size(path) == 0
