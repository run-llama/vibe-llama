#!/usr/bin/env python3

import argparse
import asyncio
from rich.console import Console

from vibe_llama.scaffold.scaffold import PROJECTS

from .starter import starter, agent_rules, services, mcp_server
from .docuflows import run_cli
from .logo import print_logo
from .scaffold import create_scaffold, run_scaffold_interface


def main() -> None:
    console = Console()

    parser = argparse.ArgumentParser(
        prog="vibe-llama",
        description="vibe-llama is a command-line tool to help you get started in the LlamIndex ecosystem with the help of vibe coding.",
    )

    subparsers = parser.add_subparsers(
        dest="command", help="Available commands", required=True
    )

    starter_parser = subparsers.add_parser(
        "starter",
        help="starter provides your coding agents with up-to-date documentation about LlamIndex, LlamaCloud Services and llama-index-workflows, so that they can build reliable and working applications! You can launch a terminal user interface by running `vibe-llama starter` or you can directly pass your agent (-a, --agent flag) and chosen service (-s, --service flag). If you already have local files and you wish them to be overwritten by the new file you are about to download with starter, use the -w, --overwrite flag.",
    )

    scaffold_parser = subparsers.add_parser(
        "scaffold",
        help="scaffold is a command that allows you to generate working examples of AI-powered workflows for a variety of use cases. Use the -u/--use-case flag to select the use case and -p/--path flag to define the path where the example workflow will be stored (defaults to '.vibe-llama/scaffold')",
    )

    _ = subparsers.add_parser(
        "docuflows",
        help="docuflows is a CLI agent that enables you to build workflows that are oriented to intelligent document processing (combining llama-index-workflows and LlamCloud). Running `vibe-llama docuflows` will start the agent.",
    )

    starter_parser.add_argument(
        "-a",
        "--agent",
        required=False,
        help="Specify the coding agent you want to write instructions for",
        choices=[agent for agent in agent_rules],
        default=None,
    )

    starter_parser.add_argument(
        "-s",
        "--service",
        required=False,
        help="Specify the service to fetch the documentation for",
        choices=[service for service in services],
        default=None,
    )

    starter_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
        required=False,
        default=False,
    )

    starter_parser.add_argument(
        "-m",
        "--mcp",
        action="store_true",
        help="Launch a local MCP server that allows you to retrieve relevant documentation",
    )

    starter_parser.add_argument(
        "-w",
        "--overwrite",
        action="store_true",
        help="Overwrite current files",
        required=False,
        default=False,
    )

    scaffold_parser.add_argument(
        "-u",
        "--use_case",
        help="Use case you would like to see an example of",
        required=False,
        default=None,
        choices=list(PROJECTS),
    )

    scaffold_parser.add_argument(
        "-p",
        "--path",
        help="Path where to save the workflow code",
        required=False,
        default=None,
    )

    args = parser.parse_args()

    if args.command == "starter":
        print_logo()
        if not args.mcp:
            t = asyncio.run(
                starter(args.agent, args.service, args.overwrite, args.verbose)
            )
            if t:
                start_docuflows = console.input(
                    "We noticed you downloaded a rule file for [code]vibe-llama docuflows[/]: would you like to start the [bold]DocuFlows Agent[/] right away? [yes/no]"
                )
                if start_docuflows.strip().lower() == "yes":
                    try:
                        asyncio.run(run_cli())
                    except KeyboardInterrupt:
                        console.print("\n👋 Goodbye!", style="bold yellow")
                else:
                    console.print("\nOk, happy vibe-hacking!👋", style="bold yellow")
        else:
            asyncio.run(mcp_server.run_async("streamable-http"))
    elif args.command == "docuflows":
        print_logo()
        try:
            asyncio.run(run_cli())
        except KeyboardInterrupt:
            console.print("\n👋 Goodbye!", style="bold yellow")
    elif args.command == "scaffold":
        print_logo()
        if not args.use_case and not args.path:
            template_name, path = asyncio.run(run_scaffold_interface())
            if template_name is None and path is None:
                console.log("[bold red]ERROR[/]\tNo use case chosen, exiting...")
                return None
            result = asyncio.run(
                create_scaffold(request=(template_name or "basic"), path=path)  # type: ignore
            )
        else:
            result = asyncio.run(
                create_scaffold(request=(args.use_case or "basic"), path=args.path)
            )
        console.log(result)
        start_docuflows = console.input(
            "Would you like to start the [bold]DocuFlows Agent[/] right away to edit the workflow scaffold you just downloaded? [yes/no]"
        )
        if start_docuflows.strip().lower() == "yes":
            try:
                asyncio.run(run_cli())
            except KeyboardInterrupt:
                console.print("\n👋 Goodbye!", style="bold yellow")
            else:
                console.print("\nOk, happy vibe-hacking!👋", style="bold yellow")

    return None
