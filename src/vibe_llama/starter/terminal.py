from prompt_toolkit.shortcuts import checkboxlist_dialog
from prompt_toolkit.shortcuts import yes_no_dialog
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from typing import Optional, Tuple, List, cast

from vibe_llama_core.docs.data import agent_rules, services, claude_code_skills

style = Style.from_dict(
    {
        "dialog": "bg:#F8E9D8",
        "dialog.body": "bg:#45DFF8",
        "dialog shadow": "bg:#a6a2ab",
        "button.focused": "bg:#FFA6EA",
    }
)

app1 = checkboxlist_dialog(
    title=HTML("<style fg='black'>Coding Agents</style>"),
    text="Which coding agents would you like to write instructions for?",
    values=[(agent_rules[agent], agent) for agent in agent_rules],
    style=style,
)

app2 = checkboxlist_dialog(
    title=HTML("<style fg='black'>Services</style>"),
    text="Which services would you like to get instructions for?",
    values=[(services[service], service) for service in services],
    cancel_text="Go Back",
    style=style,
)

app2a = checkboxlist_dialog(
    title=HTML("<style fg='black'>Donwload Skills</style>"),
    text="Since you chose Claude Code as your coding agent, would you also like to download any of these Claude Skills?",
    values=[(skill["name"], skill["name"]) for skill in claude_code_skills],
    cancel_text="Go Back",
    style=style,
)

app3 = yes_no_dialog(
    title=HTML("<style fg='black'>Overwrite</style>"),
    text="Do you want to overwrite existing files?",
    style=style,
)


async def run_terminal_interface() -> Optional[
    Tuple[List[str], List[str], List[str], bool]
]:
    results_array1 = None
    results_array2 = None
    overwrite = False
    download_skills = None

    while not results_array2:
        results_array1 = await app1.run_async()
        if not results_array1:
            return None
        results_array2 = await app2.run_async()
        if "CLAUDE.md" in results_array1:
            download_skills = await app2a.run_async()
        overwrite = await app3.run_async()
    return (
        cast(List[str], results_array1),
        results_array2,
        download_skills or [],
        overwrite,
    )
