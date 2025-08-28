import warnings
from typing import Literal, List

from vibe_llama.starter.utils import write_file, get_instructions
from vibe_llama.starter.data import agent_rules, services as service_to_url
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
        services: List[
            Literal["LlamaIndex", "LlamaCloud Services", "llama-index-workflows"]
        ],
    ) -> None:
        """
        Initialize VibeLlamaStarter.

        Args:
            agents (List[str]): List of coding agents to write instructions for.
            services ( List[Literal["LlamaIndex", "LlamaCloud Services", "llama-index-workflows"]]): List of services to fetch instructions from.
        """
        self.agent_files = [agent_rules[agent] for agent in agents]
        self.service_urls = [service_to_url[service] for service in services]

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
        return None
