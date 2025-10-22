from vibe_llama.scaffold.terminal import app1, app2
from prompt_toolkit.application import Application


def test_terminal_apps() -> None:
    assert isinstance(app1, Application)
    assert isinstance(app2, Application)
