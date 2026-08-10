import pytest

from components.cards import render_card, render_metric_card


class DummyStreamlit:
    def __init__(self) -> None:
        self.markdown_calls: list[tuple[str, dict[str, object]]] = []

    def markdown(self, body: str, **kwargs: object) -> None:
        self.markdown_calls.append((body, kwargs))


@pytest.fixture
def stub_streamlit(monkeypatch: pytest.MonkeyPatch) -> DummyStreamlit:
    dummy = DummyStreamlit()
    monkeypatch.setattr("components.cards.st", dummy)
    return dummy


def test_render_card_renders_html_and_children(stub_streamlit: DummyStreamlit) -> None:
    called = False

    def child() -> None:
        nonlocal called
        called = True

    render_card(
        title="Titre",
        value="72",
        subtitle="Sous-titre",
        description="Description",
        icon="📊",
        status="warning",
        variant="custom",
        action="Voir",
        children=child,
        highlighted=True,
    )

    assert called is True
    assert len(stub_streamlit.markdown_calls) == 1
    html = stub_streamlit.markdown_calls[0][0]
    assert "dmat-card" in html
    assert "Titre" in html
    assert "72" in html
    assert "Description" in html
    assert "dmat-status--warning" in html
    assert "dmat-card--custom" in html
    assert "dmat-card--highlighted" in html


def test_render_metric_card_formats_value_and_status(stub_streamlit: DummyStreamlit) -> None:
    render_metric_card(
        label="Infrastructure",
        value=85.5,
        unit="%",
        delta="+5%",
        icon="🏭",
        status="success",
        variant="neutral",
        precision=1,
    )

    assert len(stub_streamlit.markdown_calls) == 1
    html = stub_streamlit.markdown_calls[0][0]
    assert "Infrastructure" in html
    assert "85.5" in html
    assert "%" in html
    assert "+5%" in html
    assert "dmat-metric--success" in html
