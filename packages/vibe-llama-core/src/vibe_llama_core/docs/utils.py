import os
import json
import warnings
import httpx
import asyncio

from typing import Optional
from pathlib import Path
from vibe_llama_core.constants import CHUNKS_SEPARATOR
from .data import services, agent_rules, LibraryName, claude_code_skills, mcp_config

def write_file(
    file_path: str, content: str, overwrite_file: bool, service_url: str
) -> None:
    directory = os.path.dirname(file_path)
    if not Path(directory).is_dir():
        os.makedirs(directory, exist_ok=True)
    if not overwrite_file:
        if Path(file_path).is_file():
            with open(file_path) as f:
                file_content = f.read()
            content = file_content + "\n" + content
    if file_path.startswith(".cursor"):
        frontmatter = f"""---
description: Instructions from {service_url} for Cursor coding agent
alwaysApply: false
---

"""
        content = frontmatter + "\n" + content.replace(CHUNKS_SEPARATOR, "")
    with open(file_path, "w") as w:
        w.write(content)
    return None


async def get_instructions(
    instructions_url: str, max_retries: int = 10, retry_interval: float = 0.5
) -> Optional[str]:
    async with httpx.AsyncClient() as client:
        retries = 0
        while True:
            if retries < max_retries:
                response = await client.get(instructions_url)
                if response.status_code == 200:
                    return response.text
                else:
                    retries += 1
                    await asyncio.sleep(retry_interval)
            else:
                return None

async def get_claude_code_skills(
    skills: list[str],
    overwrite_files: Optional[bool] = None,
    verbose: Optional[bool] = None
) -> None:
    """
    Get a set of Claude Code skills.

    Args:
        skills (list[str]): List of skill names
        overwrite_files (Optional[bool]): Whether or not to overwrite existing rule files.
        verbose (Optional[bool]): Enable verbose logging.
    """
    success = 0
    for skill in skills:
        for cl_skill in claude_code_skills:
            if cl_skill["name"] == skill:
                if verbose:
                    print(f"FETCHING\t{cl_skill['skill_md_url']}")
                instr = await get_instructions(instructions_url=cl_skill['skill_md_url'])
                if instr is None:
                    print(
                        f"WARNING\tIt was not possible to retrieve instructions for {cl_skill['skill_md_url']}, please try again later"
                    )
                    continue
                if verbose:
                    print("FETCHED✅")
                if verbose:
                    print(f"WRITING\t{cl_skill['local_path']+'SKILL.md'}")
                write_file(cl_skill["local_path"]+"SKILL.md", instr, overwrite_files or False, '')
                if verbose:
                    print("WRITTEN✅")
                success+=1
                if "reference_md_url" in cl_skill:
                    if verbose:
                        print(f"FETCHING\t{cl_skill['reference_md_url']}")
                    instr = await get_instructions(instructions_url=cl_skill['reference_md_url'])
                    if instr is None:
                        print(
                            f"WARNING\tIt was not possible to retrieve instructions for {cl_skill['reference_md_url']}, please try again later"
                        )
                        continue
                    if verbose:
                        print("FETCHED✅")
                    if verbose:
                        print(f"WRITING\t{cl_skill['local_path']+'REFERENCE.md'}")
                    write_file(cl_skill["local_path"]+"REFERENCE.md", instr, overwrite_files or False, '')
                    if verbose:
                        print("WRITTEN✅")
                    success+=1
    if success == 0:
        print(
            "ERROR❌\tNo skill file could be written"
        )
    else:
        print(
            "SUCCESS✅\tSkills files have been written, happy vibe-hacking!"
        )
    return None

def write_mcp_config(mcp_config_path: Optional[str], overwrite: Optional[bool]) -> None:
    """
    Write the configuration for a local MCP server with high-level, curated documentation (vibe-llama) and a global MCP server with access to the whole LlamaIndex documentation (llama-index-docs).

    Args:
        mcp_config_path (Optional[str]): Path to the file to be written. Defaults to .mcp.json if not provided
        overwrite (Optional[bool]): Whether to overwrite existing files or not. Defaults to False.
    """
    path = ".mcp.json"
    if mcp_config_path is not None:
        path = mcp_config_path
    if overwrite:
        if Path(path).suffix:
            if  Path(path).suffix == ".json":
                if not Path(path).parent.exists():
                    os.makedirs(Path(path).parent, exist_ok=True)
                with open(path, "w") as f:
                    json.dump(mcp_config, f, indent=2)
                print("SUCCESS✅\tMCP configation file has been written, happy vibe-hacking!")
            else:
               raise ValueError("The MCP configuration file must be a JSON")
        else:
            warnings.warn(f"Writing to file {path}/.mcp.json because the provided path is likely a directory", UserWarning)
            if not Path(path).exists():
                os.makedirs(path, exist_ok=True)
            with open(path + "/.mcp.json", "w") as f:
                json.dump(mcp_config, f, indent=2)
            print("SUCCESS✅\tMCP configation file has been written, happy vibe-hacking!")
    else:
        if Path(path).exists() and Path(path).is_file():
            raise FileExistsError(f"Cannot write to file {path} because it already exists. If you wish to overwrite, give permission by specifying it either in the terminal interface or from command line.")
        else:
            if Path(path).exists() and Path(path).is_dir():
                warnings.warn(f"Trying to write the configuration to file {path}/.mcp.json because the provided path is a directory", UserWarning)
                if Path(path + "/.mcp.json").exists():
                    raise FileExistsError(f"Attempt to write  the configuration to file {path}/.mcp.json failed: the file already exists")
                else:
                    with open(path + "/.mcp.json", "w") as f:
                        json.dump(mcp_config, f, indent=2)
                    print("SUCCESS✅\tMCP configation file has been written, happy vibe-hacking!")
            elif not Path(path).exists():
                if Path(path).suffix:
                    if Path(path).suffix == ".json":
                        if not Path(path).parent.exists():
                            os.makedirs(Path(path).parent, exist_ok=True)
                        with open(path, "w") as f:
                            json.dump(mcp_config, f, indent=2)
                        print("SUCCESS✅\tMCP configation file has been written, happy vibe-hacking!")
                    else:
                        raise ValueError("The MCP configuration file must be a JSON")
                else:
                    warnings.warn(f"Writing to file {path}/.mcp.json because the provided path is likely a directory", UserWarning)
                    os.makedirs(path, exist_ok=True)
                    with open(path + "/.mcp.json", "w") as f:
                        json.dump(mcp_config, f, indent=2)
                    print("SUCCESS✅\tMCP configation file has been written, happy vibe-hacking!")
    return None

async def get_agent_rules(
    agent: str,
    service: LibraryName,
    skills: list[str] = [],
    allow_mcp_config: Optional[bool] = None,
    mcp_config_path: Optional[str] = None,
    overwrite_files: Optional[bool] = None,
    verbose: Optional[bool] = None,
) -> None:
    """
    Get agent rules for a specific agent and library.

    Args:
        agent (str): Coding agent for which rules should be downloaded
        service (LibraryName): Service for which rules should be downloaded (LlamaIndex, LlamaIndex Workflows, LlamaCloud Services)
        skills (list[str]): List of names of the skills to download (only allowed for Claude Code).
        allow_mcp_config (Optional[bool]): Allow a generic MCP configuration to be written to a a specific path. Defaults to False.
        mcp_config_path (Optional[str]): Path to write the MCP configuration to. Only applied if `allow_mcp_config` is True, defaults to .mcp.json.
        overwrite_files (Optional[bool]): Whether or not to overwrite existing rule files.
        verbose (Optional[bool]): Enable verbose logging.
    """
    agent_files = [agent_rules[agent]]
    service_urls = [services[service]]
    instructions = ""
    for serv_url in service_urls:
        if verbose:
            print(f"FETCHING\t{serv_url}")
        instr = await get_instructions(instructions_url=serv_url)
        if instr is None:
            print(
                f"WARNING\tIt was not possible to retrieve instructions for {serv_url}, please try again later"
            )
            continue
        instructions += instr + "\n\n---\n\n"
        if verbose:
            print("FETCHED✅")
    if not instructions:
        raise ValueError(
            "It was not possible to retrieve instructions at this time, please try again later"
        )
    for fl in agent_files:
        if verbose:
            print(f"WRITING\t{fl}")
        write_file(fl, instructions, overwrite_files or False, ", ".join(service_urls))
        if verbose:
            print("WRITTEN✅")
    if skills and agent == "Claude Code":
        await get_claude_code_skills(skills, overwrite_files, verbose)
    elif skills and agent != "Claude Code":
        warnings.warn("Skills are not available for agents other than Claude Code.", UserWarning)
    if allow_mcp_config:
        write_mcp_config(mcp_config_path, overwrite_files)
    return None
