import pandas as pd
import pytest

from components.tables import render_data_table, render_score_table, render_status_table


class DummyColumnConfig:
    class TextColumn:
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.args = args
            self.kwargs = kwargs

    class NumberColumn:
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.args = args
            self.kwargs = kwargs


class DummyStreamlit:
    def __init__(self) -> None:
        self.dataframe_calls: list[dict[str, object]] = []
        self.markdown_calls: list[tuple[str, dict[str, object]]] = []
        self.column_config = DummyColumnConfig()

    def markdown(self, body: str, **kwargs: object) -> None:
        self.markdown_calls.append((body, kwargs))

    def dataframe(self, data: object, **kwargs: object) -> None:
        self.dataframe_calls.append({"data": data, "kwargs": kwargs})

    @property
    def column_config(self) -> object:
        return self._column_config

    @column_config.setter
    def column_config(self, value: object) -> None:
        self._column_config = value


@pytest.fixture
def stub_streamlit(monkeypatch: pytest.MonkeyPatch) -> DummyStreamlit:
    dummy = DummyStreamlit()
    monkeypatch.setattr("components.tables.st", dummy)
    return dummy


def test_render_data_table_raises_for_empty_dataframe() -> None:
    with pytest.raises(ValueError, match="vide"):
        render_data_table(pd.DataFrame())


def test_render_status_table_validates_column(stub_streamlit: DummyStreamlit) -> None:
    df = pd.DataFrame({"Task": ["A"], "Status": ["Done"]})
    render_status_table(df, status_column="Status", title="Tasks")

    assert len(stub_streamlit.dataframe_calls) == 1
    assert stub_streamlit.markdown_calls[0][0] == "### Tasks"


def test_render_status_table_raises_for_missing_column() -> None:
    df = pd.DataFrame({"Task": ["A"]})
    with pytest.raises(ValueError, match="status_column"):
        render_status_table(df, status_column="Status")


def test_render_score_table_formats_scores_and_validates_decimals(stub_streamlit: DummyStreamlit) -> None:
    df = pd.DataFrame({"Score": [0.85], "Level": ["Advanced"]})
    render_score_table(
        df,
        score_column="Score",
        level_column="Level",
        decimals=1,
        score_scale="ratio",
        height=300,
    )

    assert len(stub_streamlit.dataframe_calls) == 1
    assert stub_streamlit.dataframe_calls[0]["kwargs"]["column_config"]["Score"] is not None

    with pytest.raises(ValueError, match="décimales"):
        render_score_table(df, score_column="Score", decimals=-1, height=300)
