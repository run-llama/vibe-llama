from typing import Optional
from rich.console import Console

from .terminal import SelectAgentApp, SelectServiceApp
from .utils import write_file, get_instructions
from .data import agent_rules, services


async def starter(
    agent: Optional[str] = None,
    service: Optional[str] = None,
    verbose: Optional[bool] = None,
) -> None:
    cs = Console(stderr=True)
    if agent is None and service is None:
        agent_app = SelectAgentApp()
        await agent_app.run_async()
        agent_files = agent_app.selected
        if len(agent_files) == 0:
            raise ValueError("You need to choose a coding agent")
        service_app = SelectServiceApp()
        await service_app.run_async()
        service_url = service_app.selected
        if service_url is None:
            raise ValueError("You need to choose a service")
    elif agent is not None and service is not None:
        agent_files = [agent_rules[agent]]
        service_url = services[service]
    else:
        raise ValueError(
            "Either you pass the options from command line or you choose them from terminal interface, you can't mix the two."
        )
    if verbose:
        cs.log(f"[bold cyan]FETCHING[/]\t{service_url}")
    instructions = await get_instructions(instructions_url=service_url)
    if instructions is None:
        raise ValueError(
            "It was not possible to retrieve instructions, please try again later"
        )
    if verbose:
        cs.log("[bold green]FETCHED✅[/]")
    for fl in agent_files:
        if verbose:
            cs.log(f"[bold cyan]WRITING[/]\t{fl}")
        write_file(fl, instructions)
        if verbose:
            cs.log("[bold green]WRITTEN✅[/]")
    cs.log(
        "[bold green]SUCCESS✅[/]\tAll the instructions files have been written, happy vibe-hacking!"
    )
    return None


__all__ = ["starter", "agent_rules", "services"]
