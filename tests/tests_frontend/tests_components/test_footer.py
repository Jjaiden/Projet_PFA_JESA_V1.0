import pytest

from components.footer import render_footer


class DummyStreamlit:
    def __init__(self) -> None:
        self.markdown_calls: list[tuple[str, dict[str, object]]] = []
        self.divider_calls = 0

    def markdown(self, body: str, **kwargs: object) -> None:
        self.markdown_calls.append((body, kwargs))

    def divider(self) -> None:
        self.divider_calls += 1


@pytest.fixture
def stub_streamlit(monkeypatch: pytest.MonkeyPatch) -> DummyStreamlit:
    dummy = DummyStreamlit()
    monkeypatch.setattr("components.footer.st", dummy)
    return dummy


def test_render_footer_builds_html_and_validates_align(stub_streamlit: DummyStreamlit) -> None:
    render_footer(
        product_name="JESA DMAT",
        version="v1.2",
        organization="JESA",
        tagline="Digital maturity",
        links=[{"label": "Docs", "url": "https://example.com"}],
        align="center",
        compact=True,
    )

    assert stub_streamlit.divider_calls == 1
    assert len(stub_streamlit.markdown_calls) == 1
    html = stub_streamlit.markdown_calls[0][0]
    assert "JESA DMAT" in html
    assert "v1.2" in html
    assert "Digital maturity" in html
    assert "https://example.com" in html
    assert "dmat-footer" in html


def test_render_footer_rejects_invalid_alignment(stub_streamlit: DummyStreamlit) -> None:
    with pytest.raises(ValueError, match="align"):
        render_footer(align="invalid")
