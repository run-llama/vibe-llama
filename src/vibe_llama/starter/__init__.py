from typing import Optional
from rich.console import Console

from .terminal import run_terminal_interface
from .mcp import mcp_server
from vibe_llama_core.docs.utils import (
    write_file,
    get_instructions,
    get_claude_code_skills,
    write_mcp_config,
)
from vibe_llama_core.docs.data import agent_rules, services, LibraryName


async def starter(
    agent: Optional[str] = None,
    service: Optional[LibraryName] = None,
    download_skills: Optional[list[str]] = None,
    allow_mcp_config: Optional[bool] = None,
    mcp_config_path: Optional[str] = None,
    overwrite_files: Optional[bool] = None,
    verbose: Optional[bool] = None,
) -> bool:
    cs = Console(stderr=True)
    if agent is None and service is None:
        term_res = await run_terminal_interface()
        if not term_res:
            cs.log(
                "[bold red]ERROR[/]\tYou need to choose at least one agent and one service before continuining. Exiting..."
            )
            return False
        (
            agent_files,
            service_urls,
            download_skills,
            overwrite_files,
            allow_mcp_config,
            mcp_config_path,
        ) = term_res
        if agent_files is None or service_urls is None:
            cs.log(
                "[bold red]ERROR[/]\tYou need to choose at least one agent and one service before continuining. Exiting..."
            )
            return False
    elif agent is not None and service is not None:
        agent_files = [agent_rules[agent]]
        service_urls = [services[service]]
    else:
        cs.log(
            "[bold red]ERROR[/]\tEither you pass the options from command line or you choose them from terminal interface, you can't mix the two."
        )
        return False
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
        return False
    for fl in agent_files:
        if verbose:
            cs.log(f"[bold cyan]WRITING[/]\t{fl}")
        write_file(fl, instructions, overwrite_files or False, ", ".join(service_urls))
        if verbose:
            cs.log("[bold green]WRITTEN✅[/]")
    cs.log(
        "[bold green]SUCCESS✅[/]\tAll the instructions files have been written, happy vibe-hacking!"
    )
    if download_skills:
        if "CLAUDE.md" in agent_files:
            await get_claude_code_skills(download_skills, overwrite_files, verbose)
        else:
            cs.log(
                "[bold yellow]WARNING:[/]\tSkills are not available for agents other than Claude Code."
            )
    if allow_mcp_config:
        write_mcp_config(mcp_config_path, overwrite_files)
    return ".vibe-llama/rules/AGENTS.md" in agent_files


__all__ = ["starter", "mcp_server"]
