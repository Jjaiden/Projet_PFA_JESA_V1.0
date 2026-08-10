"""Tests de validation des DataFrames et du chargement Excel."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from utils.excel_loader import get_sheet_names, read_sheet, read_multiple_sheets
from utils.validators import (
    validate_dataframe,
    validate_file_extension,
    validate_no_missing_values,
    validate_numeric_range,
    validate_required_columns,
)


def test_dataframe_validators_accept_valid_data_and_reject_invalid_data() -> None:
    dataframe = pd.DataFrame({"pillar": ["Data", "People"], "score": [60, 80]})

    validate_dataframe(dataframe)
    validate_required_columns(dataframe, ["pillar", "score"])
    validate_no_missing_values(dataframe)
    validate_numeric_range(80, 0, 100, "score")
    assert validate_file_extension(Path("assessment.XLSX"), (".xlsx",))

    with pytest.raises(ValueError, match="Missing required columns"):
        validate_required_columns(dataframe, ["missing"])

    with pytest.raises(ValueError, match="out of range"):
        validate_numeric_range(101, 0, 100, "score")


def test_excel_loader_reads_named_sheets(tmp_path: Path) -> None:
    workbook = tmp_path / "assessment.xlsx"
    with pd.ExcelWriter(workbook, engine="openpyxl") as writer:
        pd.DataFrame({"score": [70]}).to_excel(writer, sheet_name="Assessment", index=False)
        pd.DataFrame({"action": ["Train"]}).to_excel(writer, sheet_name="Roadmap", index=False)

    assert get_sheet_names(workbook) == ["Assessment", "Roadmap"]
    assert read_sheet(workbook, "Assessment").iloc[0]["score"] == 70
    assert set(read_multiple_sheets(workbook, ["Assessment", "Roadmap"])) == {"Assessment", "Roadmap"}
