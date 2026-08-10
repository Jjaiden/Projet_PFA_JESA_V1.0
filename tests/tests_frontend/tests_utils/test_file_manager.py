"""Tests des opérations de fichiers isolées dans un répertoire temporaire.

Ce test couvre les fonctions unifiées du module file_manager, incluant
les fonctionnalités frontend et backend.
"""

from __future__ import annotations

import pytest
from pathlib import Path

from utils.file_manager import (
    # Frontend functions
    copy_file,
    file_size,
    get_extension,
    move_file,
    read_bytes,
    read_text,
    write_bytes,
    write_text,
    # Additional functions (frontend + backend)
    ensure_directory,
    delete_file,
    delete_directory,
    rename,
    replace,
    list_files,
    list_directories,
    resolve_path,
    change_extension,
    touch,
    # Backend functions
    directory_exists,
    ensure_file_exists,
    get_output_directory,
    get_referentiel_path,
    get_recommendations_path,
    get_assessment_path,
    sanitize_filename,
    build_output_path,
    is_empty_file,
    file_exists,
    is_file,
    is_directory,
)


def test_basic_file_operations(tmp_path: Path) -> None:
    """Test read/write, copy, move, extension, size."""
    source = tmp_path / "nested" / "source.txt"
    copied = tmp_path / "copied.txt"
    moved = tmp_path / "archive" / "moved.txt"

    write_text(source, "maturity", atomic=True)
    assert read_text(source) == "maturity"
    assert get_extension(source) == ".txt"
    assert file_size(source) == len("maturity")

    copy_file(source, copied)
    move_file(copied, moved)
    assert read_text(moved) == "maturity"
    assert not copied.exists()

    binary = tmp_path / "payload.bin"
    write_bytes(binary, b"\x00\x01", atomic=True)
    assert read_bytes(binary) == b"\x00\x01"


def test_ensure_directory(tmp_path: Path) -> None:
    """Test directory creation."""
    dir_path = tmp_path / "foo" / "bar"
    result = ensure_directory(dir_path)
    assert result == dir_path
    assert dir_path.is_dir()

    # Already exists
    ensure_directory(dir_path)  # no error


def test_delete_file(tmp_path: Path) -> None:
    """Test file deletion with missing_ok."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("content")

    # Normal deletion
    result = delete_file(file_path)
    assert result == file_path
    assert not file_path.exists()

    # missing_ok=True (default)
    result = delete_file(file_path, missing_ok=True)
    assert result == file_path  # returns path even if missing

    # missing_ok=False should raise
    with pytest.raises(FileNotFoundError):
        delete_file(file_path, missing_ok=False)

    # Cannot delete a directory
    dir_path = tmp_path / "adir"
    dir_path.mkdir()
    with pytest.raises(IsADirectoryError):
        delete_file(dir_path)


def test_delete_directory(tmp_path: Path) -> None:
    """Test directory deletion."""
    dir_path = tmp_path / "mydir"
    dir_path.mkdir()
    (dir_path / "file.txt").touch()

    # Non-recursive should fail because directory not empty
    with pytest.raises(OSError):
        delete_directory(dir_path, recursive=False)

    # Recursive works
    delete_directory(dir_path, recursive=True)
    assert not dir_path.exists()


def test_rename_and_replace(tmp_path: Path) -> None:
    """Test rename and replace."""
    src = tmp_path / "old.txt"
    dst = tmp_path / "new.txt"
    src.write_text("content")

    rename(src, dst)
    assert dst.is_file()
    assert not src.exists()

    # replace
    src2 = tmp_path / "other.txt"
    src2.write_text("other")
    replace(src2, dst)
    assert dst.read_text() == "other"
    assert not src2.exists()


def test_list_files_and_directories(tmp_path: Path) -> None:
    """Test listing files and directories."""
    (tmp_path / "file1.txt").touch()
    (tmp_path / "file2.log").touch()
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "file3.txt").touch()

    files = list_files(tmp_path, pattern="*.txt")
    assert set(files) == {tmp_path / "file1.txt", tmp_path / "subdir" / "file3.txt"}

    files_all = list_files(tmp_path)
    assert set(files_all) == {tmp_path / "file1.txt", tmp_path / "file2.log", tmp_path / "subdir" / "file3.txt"}

    dirs = list_directories(tmp_path)
    assert dirs == [tmp_path / "subdir"]


def test_resolve_path(tmp_path: Path) -> None:
    """Test path resolution with base_dir."""
    rel = Path("some/file.txt")
    resolved = resolve_path(rel, base_dir=tmp_path)
    assert resolved == (tmp_path / "some/file.txt").resolve()

    # Without base_dir, uses current working directory
    # We can't easily assert, but should not raise
    resolve_path(rel)


def test_change_extension(tmp_path: Path) -> None:
    """Test changing file extension."""
    original = tmp_path / "data.csv"
    new = change_extension(original, ".xlsx")
    assert new == tmp_path / "data.xlsx"

    # Without leading dot
    new2 = change_extension(original, "xlsx")
    assert new2 == tmp_path / "data.xlsx"

    with pytest.raises(ValueError):
        change_extension(original, ".")


def test_touch(tmp_path: Path) -> None:
    """Test touch creates file and parent directories."""
    file_path = tmp_path / "deep" / "file.txt"
    touched = touch(file_path)
    assert touched == file_path
    assert file_path.is_file()

    # Touch existing file updates mtime (we can't easily test, but no error)
    touch(file_path)


def test_backend_functions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test backend-specific functions: directory_exists, ensure_file_exists, etc."""
    # Monkeypatch settings to use tmp_path
    import config.settings as settings
    monkeypatch.setattr(settings, "OUTPUT_DIR", str(tmp_path / "output"))
    monkeypatch.setattr(settings, "REFERENTIEL_FILE", str(tmp_path / "referentiel.xlsx"))
    monkeypatch.setattr(settings, "RECOMMENDATIONS_FILE", str(tmp_path / "recommendations.xlsx"))
    monkeypatch.setattr(settings, "ASSESSMENT_FILE", str(tmp_path / "assessment.xlsx"))

    # Test directory_exists
    dir_path = tmp_path / "mydir"
    assert not directory_exists(dir_path)
    dir_path.mkdir()
    assert directory_exists(dir_path)

    # Test file_exists alias
    file_path = tmp_path / "file.txt"
    assert not file_exists(file_path)
    file_path.touch()
    assert file_exists(file_path)

    # Test is_file and is_directory
    assert is_file(file_path)
    assert is_directory(dir_path)

    # Test ensure_file_exists
    with pytest.raises(FileNotFoundError):
        ensure_file_exists(tmp_path / "nonexistent.txt")

    ensure_file_exists(file_path)  # should not raise

    # Test get_output_directory
    output = get_output_directory(create=True)
    assert output == (tmp_path / "output").resolve()
    assert output.is_dir()

    # Test path getters
    assert get_referentiel_path() == tmp_path / "referentiel.xlsx"
    assert get_recommendations_path() == tmp_path / "recommendations.xlsx"
    assert get_assessment_path() == tmp_path / "assessment.xlsx"

    # Test sanitize_filename
    assert sanitize_filename("valid.txt") == "valid.txt"
    assert sanitize_filename("invalid:name?") == "invalid_name_"
    with pytest.raises(ValueError):
        sanitize_filename("")

    # Test build_output_path
    out_path = build_output_path("report.pdf", create_directory=True)
    assert out_path.parent == output
    assert out_path.name == "report.pdf"

    # Test is_empty_file
    empty = tmp_path / "empty.txt"
    empty.touch()
    assert is_empty_file(empty) is True
    empty.write_text("hello")
    assert is_empty_file(empty) is False


def test_copy_and_move_with_create_parent(tmp_path: Path) -> None:
    """Test copy_file and move_file with create_parent parameter."""
    src = tmp_path / "src.txt"
    src.write_text("data")
    dst = tmp_path / "deep" / "dst.txt"

    # create_parent=True (default)
    copy_file(src, dst, create_parent=True)
    assert dst.is_file()
    assert dst.read_text() == "data"

    # Move with create_parent=False should fail if parent missing
    dst2 = tmp_path / "another" / "dst2.txt"
    with pytest.raises(FileNotFoundError):
        move_file(src, dst2, create_parent=False)

    # Move with create_parent=True
    move_file(src, dst2, create_parent=True)
    assert dst2.is_file()
    assert not src.exists()