#!/usr/bin/env python3

import argparse
import asyncio
from rich.console import Console

from .starter import starter, agent_rules, services, mcp_server
from .docuflows import run_cli
from .logo import print_logo


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

    args = parser.parse_args()

    if args.command == "starter":
        print_logo()
        if not args.mcp:
            asyncio.run(starter(args.agent, args.service, args.overwrite, args.verbose))
        else:
            asyncio.run(mcp_server.run_async("streamable-http"))
    elif args.command == "docuflows":
        print_logo()
        try:
            asyncio.run(run_cli())
        except KeyboardInterrupt:
            console.print("\n👋 Goodbye!", style="bold yellow")

    return None
