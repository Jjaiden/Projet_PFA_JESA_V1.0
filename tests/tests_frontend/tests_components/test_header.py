import pytest

from components.header import render_header


class DummyStreamlit:
    def __init__(self) -> None:
        self.markdown_calls: list[tuple[str, dict[str, object]]] = []

    def markdown(self, body: str, **kwargs: object) -> None:
        self.markdown_calls.append((body, kwargs))


@pytest.fixture
def stub_streamlit(monkeypatch: pytest.MonkeyPatch) -> DummyStreamlit:
    dummy = DummyStreamlit()
    monkeypatch.setattr("components.header.st", dummy)
    return dummy


def test_render_header_renders_title_and_status(stub_streamlit: DummyStreamlit) -> None:
    render_header(
        title="Maturité",
        subtitle="Sous-titre",
        eyebrow="ASSESSMENT",
        icon="📊",
        status="warning",
        align="center",
        compact=True,
    )

    assert len(stub_streamlit.markdown_calls) == 1
    html = stub_streamlit.markdown_calls[0][0]
    assert "Maturité" in html
    assert "Sous-titre" in html
    assert "ASSESSMENT" in html
    assert "dmat-header" in html
    assert "dmat-status--warning" in html


def test_render_header_rejects_invalid_alignment(stub_streamlit: DummyStreamlit) -> None:
    with pytest.raises(ValueError, match="align"):
        render_header(title="Titre", align="invalid")
