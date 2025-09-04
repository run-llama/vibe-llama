from prompt_toolkit.shortcuts import radiolist_dialog, input_dialog
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from typing import Optional, Tuple

from vibe_llama.scaffold.scaffold import PROJECTS


style = Style.from_dict(
    {
        "dialog": "bg:#F8E9D8",
        "dialog.body": "bg:#45DFF8",
        "dialog shadow": "bg:#a6a2ab",
        "button.focused": "bg:#FFA6EA",
    }
)

app1 = radiolist_dialog(
    title=HTML("<style fg='black'>Use Case</style>"),
    text="Which use case would you like to download an example of?",
    values=[(key, " ".join(key.split("_")).capitalize()) for key in list(PROJECTS)],
    style=style,
)

app2 = input_dialog(
    title=HTML("<style fg='black'>Path</style>"),
    text=HTML(
        "Which path would you like to save the example code to? (leave blank to save to <style bg='gray'>.vibe-llama/scaffold/</style>)"
    ),
    cancel_text="Go Back",
    style=style,
)


async def run_scaffold_interface() -> Tuple[Optional[str], Optional[str]]:
    template = None
    path = None

    while path is None:
        template = await app1.run_async()
        if not template:
            return None, None
        path = await app2.run_async()
    if path == "":
        path = None
    return template, path
