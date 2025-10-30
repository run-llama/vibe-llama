import warnings
from typing import List, Optional
from rich.console import Console

from vibe_llama_core.docs.utils import (
    write_file,
    get_instructions,
    get_claude_code_skills,
    write_mcp_config,
)
from vibe_llama_core.docs.data import (
    LibraryName,
    agent_rules,
    services as service_to_url,
)
from vibe_llama_core.templates.scaffold import download_template, ProjectName
from .utils import print_verbose
from .errors import (
    FailedToWriteFilesError,
    FailedToWriteFileWarning,
    InstructionsUnavailableError,
)


class VibeLlamaStarter:
    """
    VibeLlamaStarter allows you to write instructions for coding agents related to LlamaIndex, LlamaCloud Services and llama-index-workflows.

    Attributes:
        agent_files: Path to rule files for the specified agents
        service_urls: URLs to fetch the instructions for the specified services
    """

    def __init__(
        self,
        agents: List[str],
        services: List[LibraryName],
        skills: List[str] = [],
        allow_mcp_config: bool = False,
        mcp_config_path: Optional[str] = None,
    ) -> None:
        """
        Initialize VibeLlamaStarter.

        Args:
            agents (List[str]): List of coding agents to write instructions for.
            services (List[LibraryName]): List of services to fetch instructions from.
            skills (List[str]): List of skills to download. Only applies if "Claude Code" is among the chosen agents.
            allow_mcp_config (bool): Whether or not to download a general MCP configuration for your coding agent.
            mcp_config_path (Optional[str]): Path to the MCP configuration. Only applies if `allow_mcp_config` is set to True.
        """
        self.agent_files = [agent_rules[agent] for agent in agents]
        self.service_urls = [service_to_url[service] for service in services]
        self.allow_mcp_config = allow_mcp_config
        self.mcp_config_path = mcp_config_path
        if "Claude Code" not in agents:
            warnings.warn(
                "Skills are not available for agents other than Claude Code.",
                UserWarning,
            )
            self.skills: Optional[list[str]] = None
        else:
            self.skills = skills

    async def write_instructions(
        self,
        max_retries: int = 10,
        retry_interval: float = 0.5,
        verbose: bool = False,
        overwrite: bool = False,
    ) -> None:
        """
        Fetch and write the instructions for the specified agents and services.

        Args:
            max_retries (int): Maximum number of times the method should retry fetching instructions.
            retry_interval (float): Interval, in seconds, between one retry and the following.
            verbose (bool): Print debugging information while the function is running.
            overwrite (bool): Overwrite current files without preserving their content.
        """
        inst: List[str] = []
        for service_url in self.service_urls:
            print_verbose(f"Fetching {service_url}", verbose)
            instructions = await get_instructions(
                service_url, max_retries, retry_interval
            )
            if instructions is None:
                print_verbose(
                    f"Erorr:\nunable to fetch {service_url} at this time, please check your connection and retry later.",
                    verbose,
                )
                raise InstructionsUnavailableError(
                    "Unable to fetch instructions at this time"
                )
            else:
                print_verbose("Fetched", verbose)
                inst.append(instructions)
        content = "\n\n---\n\n".join(inst)
        failed_files = []
        for agent_file in self.agent_files:
            print_verbose(f"Writing {agent_file}", verbose)
            try:
                write_file(agent_file, content, overwrite, ", ".join(self.service_urls))
            except Exception as e:
                print_verbose(
                    f"Warning:\nunable to write {agent_file} because of the following error: {str(e)}",
                    verbose,
                )
                failed_files.append(agent_file)
                warnings.warn(
                    FailedToWriteFileWarning(f"Failed to write file: {agent_file}")
                )
            else:
                print_verbose(f"{agent_file} successfully written!", verbose)
        if len(failed_files) == len(self.agent_files):
            print_verbose("Error:\nunable to write agent files", verbose)
            raise FailedToWriteFilesError(
                "Unable to write agent instructions files, please check that you have writing permission in the current environment."
            )
        print_verbose(
            "All the files have been successfully written, happy vibe-hacking!", verbose
        )
        if self.skills:
            await get_claude_code_skills(self.skills, overwrite, verbose)
        if self.allow_mcp_config:
            write_mcp_config(self.mcp_config_path, overwrite)
        return None


class VibeLlamaScaffold:
    """
    VibeLlamaScaffold allows you to download human-curated, end-to-end workflows templates for various use cases.

    Attributes:
        colored_output (bool): Print the output of the scaffold operation with color
    """

    def __init__(self, colored_output: bool = True) -> None:
        self.colored_output = colored_output
        self._console = Console()

    async def get_template(
        self,
        template_name: ProjectName = "basic",
        save_path: Optional[str] = None,
    ) -> None:
        """
        Download a template.

        Args:
            template_name (ProjectName): Name of the template. Defaults to `basic` if not provided
            save_path (Optional[str]): Path where to save the downloaded template. Defaults to `.vibe-llama/scaffold` if not provided
        """
        result = await download_template(template_name, save_path)
        if self.colored_output:
            self._console.log(result)
        else:
            result.replace("[bold red]", "").replace("[bold green]", "").replace(
                "[/]", ""
            )
            print(result)
