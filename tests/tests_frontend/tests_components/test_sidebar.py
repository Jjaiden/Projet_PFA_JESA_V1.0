import pytest

from components.sidebar import render_sidebar


class DummyStreamlit:
    def __init__(self) -> None:
        self.sidebar_markdown_calls: list[tuple[str, dict[str, object]]] = []
        self.sidebar_divider_calls = 0
        self.sidebar_page_link_calls: list[dict[str, object]] = []
        self.sidebar_image_calls: list[tuple[object, dict[str, object]]] = []

    def markdown(self, body: str, **kwargs: object) -> None:
        self.sidebar_markdown_calls.append((body, kwargs))

    def divider(self) -> None:
        self.sidebar_divider_calls += 1

    def page_link(self, **kwargs: object) -> None:
        self.sidebar_page_link_calls.append(kwargs)

    def image(self, *args: object, **kwargs: object) -> None:
        self.sidebar_image_calls.append((args, kwargs))


class DummySidebar:
    def __init__(self) -> None:
        self._dummy = DummyStreamlit()

    def __getattr__(self, name: str) -> object:
        return getattr(self._dummy, name)


@pytest.fixture
def stub_streamlit(monkeypatch: pytest.MonkeyPatch) -> DummyStreamlit:
    dummy = DummyStreamlit()
    monkeypatch.setattr("components.sidebar.st", type("DummyRoot", (), {"sidebar": dummy})())
    return dummy


def test_render_sidebar_renders_branding_navigation_and_footer(stub_streamlit: DummyStreamlit) -> None:
    render_sidebar(
        title="JESA DMAT",
        subtitle="Assessment tool",
        logo="logo.png",
        navigation=[{"label": "Home", "page": "app.py", "icon": "🏠"}],
        assessment_name="Site A",
        assessment_status="In progress",
        show_footer=True,
        version="v2",
    )

    assert stub_streamlit.sidebar_divider_calls == 3
    assert len(stub_streamlit.sidebar_markdown_calls) >= 3
    assert stub_streamlit.sidebar_page_link_calls[0]["page"] == "app.py"
    assert stub_streamlit.sidebar_image_calls[0][0][0] == "logo.png"
