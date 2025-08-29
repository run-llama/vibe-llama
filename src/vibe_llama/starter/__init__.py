from typing import Optional
from rich.console import Console

from .terminal import run_terminal_interface
from .utils import write_file, get_instructions
from .data import agent_rules, services
from .mcp import mcp_server


async def starter(
    agent: Optional[str] = None,
    service: Optional[str] = None,
    overwrite_files: Optional[bool] = None,
    verbose: Optional[bool] = None,
) -> None:
    cs = Console(stderr=True)
    if agent is None and service is None:
        term_res = await run_terminal_interface()
        if not term_res:
            cs.log(
                "[bold red]ERROR[/]\tYou need to choose at least one agent and one service before continuining. Exiting..."
            )
            return None
        agent_files, service_urls, overwrite_files = term_res
        if agent_files is None or service_urls is None:
            cs.log(
                "[bold red]ERROR[/]\tYou need to choose at least one agent and one service before continuining. Exiting..."
            )
            return None
    elif agent is not None and service is not None:
        agent_files = [agent_rules[agent]]
        service_urls = [services[service]]
    else:
        cs.log(
            "[bold red]ERROR[/]\tEither you pass the options from command line or you choose them from terminal interface, you can't mix the two."
        )
        return None
    instructions = ""
    for serv_url in service_urls:
        if verbose:
            cs.log(f"[bold cyan]FETCHING[/]\t{serv_url}")
        instr = await get_instructions(instructions_url=serv_url)
        if instr is None:
            cs.log(
                f"[bold yellow]WARNING[/]\tIt was not possible to retrieve instructions for {serv_url}, please try again later"
            )
            continue
        instructions += instr + "\n\n---\n\n"
        if verbose:
            cs.log("[bold green]FETCHED✅[/]")
    if not instructions:
        cs.log(
            "[bold red]ERROR[/]\tIt was not possible to retrieve instructions at this time, please try again later"
        )
        return None
    for fl in agent_files:
        if verbose:
            cs.log(f"[bold cyan]WRITING[/]\t{fl}")
        write_file(fl, instructions, overwrite_files or False, ", ".join(service_urls))
        if verbose:
            cs.log("[bold green]WRITTEN✅[/]")
    cs.log(
        "[bold green]SUCCESS✅[/]\tAll the instructions files have been written, happy vibe-hacking!"
    )
    return None


__all__ = ["starter", "agent_rules", "services", "mcp_server"]
