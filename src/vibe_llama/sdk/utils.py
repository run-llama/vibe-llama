import sys


def print_verbose(content: str, verbose: bool) -> None:
    if verbose:
        print(content, file=sys.stderr)
