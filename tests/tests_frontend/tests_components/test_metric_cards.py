import pytest

from components.metric_cards import (
    render_maturity_metric,
    render_pillar_metric,
    render_trend_metric,
)


class DummyStreamlit:
    def __init__(self) -> None:
        self.markdown_calls: list[tuple[str, dict[str, object]]] = []

    def markdown(self, body: str, **kwargs: object) -> None:
        self.markdown_calls.append((body, kwargs))


@pytest.fixture
def stub_streamlit(monkeypatch: pytest.MonkeyPatch) -> DummyStreamlit:
    dummy = DummyStreamlit()
    monkeypatch.setattr("components.metric_cards.st", dummy)
    return dummy


def test_render_maturity_metric_formats_value_and_level(stub_streamlit: DummyStreamlit) -> None:
    render_maturity_metric(
        label="Maturité globale",
        value=72.4,
        unit="%",
        level="Advanced",
        icon="📊",
        status="success",
        precision=1,
    )

    assert len(stub_streamlit.markdown_calls) == 1
    html = stub_streamlit.markdown_calls[0][0]
    assert "Maturité globale" in html
    assert "72.4" in html
    assert "Advanced" in html
    assert "dmat-metric--positive" in html


def test_render_pillar_metric_and_trend_metric(stub_streamlit: DummyStreamlit) -> None:
    render_pillar_metric(label="Infrastructure", value=85, unit="%", status="warning", icon="🏭")
    render_trend_metric(label="Progression", value=72, unit="%", delta="+5%", trend="negative", icon="📈")

    assert len(stub_streamlit.markdown_calls) == 2
    first = stub_streamlit.markdown_calls[0][0]
    second = stub_streamlit.markdown_calls[1][0]
    assert "Infrastructure" in first
    assert "dmat-metric--warning" in first
    assert "Progression" in second
    assert "dmat-metric--negative" in second
