#!/usr/bin/env python3

import argparse
import asyncio

from .starter import starter, agent_rules, services
from .logo import print_logo


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="vibe-llama",
        description="vibe-llama is a command-line tool to help you get started in the LlamIndex ecosystem with the help of vibe coding.",
    )

    subparsers = parser.add_subparsers(
        dest="command", help="Available commands", required=True
    )

    starter_parser = subparsers.add_parser(
        "starter",
        help="starter provides your coding agents with up-to-date documentation about LlamIndex, LlamaCloud Services and llama-index-workflows, so that they can build reliable and working applications! You can launch a terminal user interface by running `vibe-llama starter` or you can directly pass your agent (-a, --agent flag) and chosen service (-s, --service flag).",
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

    args = parser.parse_args()

    if args.command == "starter":
        print_logo()
        asyncio.run(starter(args.agent, args.service, args.verbose))

    return None
