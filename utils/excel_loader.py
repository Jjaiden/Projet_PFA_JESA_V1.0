# JESA_DMAT/utils/excel_loader.py
"""
Generic Excel file loading utilities for the JESA DMAT application.

Provides read-only functions for inspecting and importing data from
Excel workbooks (.xlsx). All functions accept ``pathlib.Path`` objects.
No business logic, data transformation, or workbook modification is
performed here.

Convenience functions are also available to load the project's standard
reference files directly using paths defined in ``config.settings``.

Functions:
    file_exists(file_path: Path) -> bool
    validate_excel_file(file_path: Path) -> None
    load_workbook(file_path: Path) -> pd.ExcelFile
    get_workbook_info(file_path: Path) -> dict
    get_sheet_names(file_path: Path) -> list[str]
    sheet_exists(file_path: Path, sheet_name: str) -> bool
    read_sheet(file_path: Path, sheet_name: str | int = 0, **kwargs) -> pd.DataFrame
    read_multiple_sheets(file_path: Path, sheet_names: list[str | int]) -> dict[str, pd.DataFrame]
    read_all_sheets(file_path: Path) -> dict[str, pd.DataFrame]
    get_sheet_dimensions(file_path: Path, sheet_name: str | int = 0) -> tuple[int, int]
    get_sheet_columns(file_path: Path, sheet_name: str | int = 0) -> pd.Index
    load_assessment_workbook() -> pd.ExcelFile
    load_knowledge_base() -> pd.ExcelFile

Examples:
    >>> from pathlib import Path
    >>> from utils.excel_loader import load_assessment_workbook, read_sheet
    >>> wb = load_assessment_workbook()
    >>> df = read_sheet(Path("data/assessment.xlsx"), sheet_name="Pilier 1")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Tuple, Union

import pandas as pd  # type: ignore

from config.settings import settings

if TYPE_CHECKING:
    # Import for type checking only; some static analyzers may not resolve pandas
    import pandas as pd  # type: ignore

logger = logging.getLogger(__name__)

__all__ = [
    "file_exists",
    "validate_excel_file",
    "load_workbook",
    "get_workbook_info",
    "get_sheet_names",
    "sheet_exists",
    "read_sheet",
    "read_multiple_sheets",
    "read_all_sheets",
    "get_sheet_dimensions",
    "get_sheet_columns",
    "load_assessment_workbook",
    "load_knowledge_base",
]

# Allowed Excel extensions
_EXCEL_EXTENSIONS = (".xlsx", ".xlsm", ".xls")


def file_exists(file_path: Path) -> bool:
    """Check whether the given file path exists and is a file.

    Args:
        file_path: Absolute or relative path to a file.

    Returns:
        True if the path points to an existing file, False otherwise.
    """
    exists = file_path.is_file()
    if not exists:
        logger.warning("File not found: %s", file_path)
    return exists


def validate_excel_file(file_path: Path) -> None:
    """Validate that a file exists, has a proper Excel extension, and is not empty.

    Args:
        file_path: Path to the file to validate.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file extension is not recognised as Excel.
        ValueError: If the file is empty (zero bytes).
        PermissionError: If the file cannot be accessed.
    """
    if not file_exists(file_path):
        raise FileNotFoundError(f"Excel file not found: {file_path}")

    suffix = file_path.suffix.lower()
    if suffix not in _EXCEL_EXTENSIONS:
        raise ValueError(
            f"Invalid file extension '{suffix}'. Expected one of {_EXCEL_EXTENSIONS}"
        )

    try:
        size = file_path.stat().st_size
    except PermissionError:
        logger.exception("Permission denied accessing %s", file_path)
        raise

    if size == 0:
        raise ValueError(f"File is empty: {file_path}")


def load_workbook(file_path: Path) -> pd.ExcelFile:
    """Open an Excel workbook and return a ``pd.ExcelFile`` object.

    Validates the file before opening.

    Args:
        file_path: Path to the Excel file.

    Returns:
        A ready-to-use ``pd.ExcelFile`` instance.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a valid Excel file or is empty.
        PermissionError: If the file cannot be opened due to permissions.
    """
    validate_excel_file(file_path)

    try:
        xls = pd.ExcelFile(file_path, engine="openpyxl")
        logger.debug("Opened workbook: %s", file_path)
        return xls
    except PermissionError:
        logger.exception("Permission denied opening %s", file_path)
        raise
    except Exception as exc:
        logger.exception("Failed to open Excel workbook: %s", file_path)
        raise ValueError(f"Invalid Excel workbook: {file_path}") from exc


def get_workbook_info(file_path: Path) -> Dict[str, Any]:
    """Return basic information about an Excel workbook.

    Args:
        file_path: Path to the Excel file.

    Returns:
        Dictionary with keys:
        - ``file_name`` (str)
        - ``sheet_count`` (int)
        - ``sheet_names`` (list[str])

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is invalid or empty.
        PermissionError: If the file cannot be read.
    """
    with load_workbook(file_path) as xls:
        info = {
            "file_name": file_path.name,
            "sheet_count": len(xls.sheet_names),
            "sheet_names": xls.sheet_names,
        }
    logger.info("Workbook info for %s: %d sheets", file_path, info["sheet_count"])
    return info


def get_sheet_names(file_path: Path) -> List[str]:
    """Return a list of sheet names in an Excel workbook.

    Args:
        file_path: Path to the Excel file.

    Returns:
        List of sheet names.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is invalid or empty.
        PermissionError: If the file cannot be read.
    """
    return get_workbook_info(file_path)["sheet_names"]


def sheet_exists(file_path: Path, sheet_name: str) -> bool:
    """Check if a specific sheet exists in the workbook.

    Args:
        file_path: Path to the Excel file.
        sheet_name: Name of the sheet to look for.

    Returns:
        True if the sheet exists, False otherwise (including if the file itself does not exist).
    """
    try:
        return sheet_name in get_sheet_names(file_path)
    except Exception:
        return False


def read_sheet(
    file_path: Path,
    sheet_name: Union[str, int] = 0,
    **kwargs: Any,
) -> pd.DataFrame:
    """Read a single sheet into a pandas DataFrame.

    Args:
        file_path: Path to the Excel file.
        sheet_name: Name or index of the sheet (default 0, first sheet).
        **kwargs: Additional arguments passed to ``pd.read_excel``.

    Returns:
        DataFrame containing the sheet data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the sheet does not exist or the workbook is invalid.
        PermissionError: If the file cannot be read.

    Example:
        >>> df = read_sheet(Path("data/assessment.xlsx"), sheet_name="Pilier 1")
    """
    # Validation is delegated to load_workbook internally via pd.read_excel?
    # We'll keep direct pd.read_excel for simplicity, but it will still fail appropriately.
    if not file_exists(file_path):
        raise FileNotFoundError(f"Excel file not found: {file_path}")

    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine="openpyxl", **kwargs)
        logger.info(
            "Read sheet '%s' from %s – %d rows x %d columns",
            sheet_name,
            file_path,
            *df.shape,
        )
        return df
    except ValueError as exc:
        if isinstance(sheet_name, str):
            msg = f"Sheet '{sheet_name}' not found in workbook {file_path}"
            logger.warning(msg)
            raise ValueError(msg) from exc
        raise
    except PermissionError:
        logger.exception("Permission denied reading %s", file_path)
        raise
    except Exception as exc:
        logger.exception("Failed to read sheet '%s' from %s", sheet_name, file_path)
        raise ValueError(f"Could not read sheet '{sheet_name}' from {file_path}") from exc


def read_multiple_sheets(
    file_path: Path,
    sheet_names: List[Union[str, int]],
) -> Dict[str, pd.DataFrame]:
    """Read several named sheets into a dictionary of DataFrames.

    Opens the workbook only once for efficiency.

    Args:
        file_path: Path to the Excel file.
        sheet_names: List of sheet names or indices to read.

    Returns:
        Dictionary mapping sheet names to DataFrames.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If any sheet is missing or the workbook is invalid.
        PermissionError: If the file cannot be read.

    Example:
        >>> dfs = read_multiple_sheets(Path("data/assessment.xlsx"), ["Pilier 1", "Pilier 2"])
    """
    if not file_exists(file_path):
        raise FileNotFoundError(f"Excel file not found: {file_path}")

    with load_workbook(file_path) as xls:
        available = xls.sheet_names
        missing = [sn for sn in sheet_names if isinstance(sn, str) and sn not in available]
        if missing:
            raise ValueError(
                f"Sheets {missing} not found in {file_path}. Available: {available}"
            )

        result: Dict[str, pd.DataFrame] = {}
        for sn in sheet_names:
            result[str(sn)] = xls.parse(sheet_name=sn)
            logger.debug("Parsed sheet: %s", sn)
    logger.info("Read %d sheets from %s", len(result), file_path)
    return result


def read_all_sheets(file_path: Path) -> Dict[str, pd.DataFrame]:
    """Read all sheets from the workbook into a dictionary of DataFrames.

    Args:
        file_path: Path to the Excel file.

    Returns:
        Dictionary mapping every sheet name to a DataFrame.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the workbook is invalid or empty.
        PermissionError: If the file cannot be read.

    Example:
        >>> all_data = read_all_sheets(Path("data/assessment.xlsx"))
        >>> for name, df in all_data.items():
        ...     print(name, df.shape)
    """
    if not file_exists(file_path):
        raise FileNotFoundError(f"Excel file not found: {file_path}")

    with load_workbook(file_path) as xls:
        sheets_dict = xls.parse(sheet_name=None)
        logger.info("Read all %d sheets from %s", len(sheets_dict), file_path)
        return sheets_dict


def get_sheet_dimensions(
    file_path: Path,
    sheet_name: Union[str, int] = 0,
) -> Tuple[int, int]:
    """Return the (row_count, column_count) of a sheet.

    Args:
        file_path: Path to the Excel file.
        sheet_name: Name or index of the sheet (default 0).

    Returns:
        Tuple of (rows, columns).

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the sheet cannot be read.
        PermissionError: If the file cannot be accessed.

    Example:
        >>> rows, cols = get_sheet_dimensions(Path("data/assessment.xlsx"), "Pilier 1")
    """
    df = read_sheet(file_path, sheet_name=sheet_name)
    return df.shape


def get_sheet_columns(
    file_path: Path,
    sheet_name: Union[str, int] = 0,
) -> pd.Index:
    """Return the column names of a sheet.

    Args:
        file_path: Path to the Excel file.
        sheet_name: Name or index of the sheet (default 0).

    Returns:
        pandas Index object containing column names.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the sheet cannot be read.
        PermissionError: If the file cannot be accessed.

    Example:
        >>> cols = get_sheet_columns(Path("data/assessment.xlsx"), "Pilier 1")
        >>> print(cols.tolist())
    """
    df = read_sheet(file_path, sheet_name=sheet_name)
    return df.columns


def load_assessment_workbook() -> pd.ExcelFile:
    """Open the standard assessment workbook defined in ``settings.ASSESSMENT_FILE``.

    Returns:
        ``pd.ExcelFile`` object for the assessment data.

    Raises:
        FileNotFoundError: If the assessment file is missing.
        ValueError: If the file is invalid or empty.
        PermissionError: If the file cannot be read.
    """
    return load_workbook(settings.ASSESSMENT_FILE)


def load_knowledge_base() -> pd.ExcelFile:
    """Open the standard knowledge base workbook defined in ``settings.KNOWLEDGE_BASE_FILE``.

    Returns:
        ``pd.ExcelFile`` object for the knowledge base data.

    Raises:
        FileNotFoundError: If the knowledge base file is missing.
        ValueError: If the file is invalid or empty.
        PermissionError: If the file cannot be read.
    """
    return load_workbook(settings.KNOWLEDGE_BASE_FILE)
