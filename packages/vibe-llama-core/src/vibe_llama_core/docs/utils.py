import os
import warnings
import httpx
import asyncio

from typing import Optional
from pathlib import Path
from vibe_llama_core.constants import CHUNKS_SEPARATOR
from .data import services, agent_rules, LibraryName, claude_code_skills

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

async def get_agent_rules(
    agent: str,
    service: LibraryName,
    skills: list[str] = [],
    overwrite_files: Optional[bool] = None,
    verbose: Optional[bool] = None,
) -> None:
    """
    Get agent rules for a specific agent and library.

    Args:
        agent (str): Coding agent for which rules should be downloaded
        service (LibraryName): Service for which rules should be downloaded (LlamaIndex, LlamaIndex Workflows, LlamaCloud Services)
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
    return None
