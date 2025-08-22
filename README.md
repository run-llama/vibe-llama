# vibe-llama

**vibe-llama** is a set of tools that are designed to help developers build working and reliable applications with [LlamaIndex](https://github.com/run-llama/llama_index), [LlamaCloud Services](https://github.com/run-llama/llama_cloud_services) and [llama-index-workflows](https://github.com/run-llama/workflows-py).

This command-line tool aims to add the relevant context as rules to any coding agent of your choice (think Cursor, Claude Code, GitHub Copilot etc.):

1. You select a coding agent.
2. You select the LlamaIndex service (such as LlamaCloud, the LlamaIndex framework or the Workflows package)

Once you've made your choice, **vibe-llama** will generate a rule file for your coding agent. For example, if you selected Cursor, a new rule will be added to `.cursor/rules`. Now, all of the context and instructions about your chosen LlamaIndex service will be available to your coding agent of choice.

## Installation

**User settings**

You can install and run **vibe-llama** using `uv`:

```bash
uvx vibe-llama@latest --help
```

Or you can use `pip` to install it first and run it in a second moment:

```bash
pip install vibe-llama
```

**Developer settings**

Clone the GitHub repository:

```bash
git clone https://github.com/run-llama/vibe-llama
cd vibe-llama
```

Build and install the project:

```bash
uv build
```

For regular installation:

```bash
uv pip install dist/*.whl
```

For editable installation (development):

```bash
# Activate virtual environment first
uv venv
source .venv/bin/activate  # On Unix/macOS

# Then install in editable mode
uv pip install -e .
```

## Usage

**vibe-llama** is a CLI command, and has the following subcommands:

### starter

`starter` provides your coding agents with up-to-date documentation about LlamIndex, LlamaCloud Services and llama-index-workflows, so that they can build reliable and working applications! You can launch a terminal user interface by running `vibe-llama starter` and select your desired coding agents and services from there, or you can directly pass your agent (-a, --agent flag) and chosen service (-s, --service flag) from command line interface.

Use the `-v`/`--verbose` flag (independently from TUI or CLI) if you want verbose logging of what processes are being executed while the application runs.

**Example usage**

```bash
vibe-llama starter # launch a TUI
vibe-llama starter -a 'GitHub Copilot' -s LlamaIndex -v # Select GitHub Copilot and LlamaIndex and enable verbose logging
```

### More commands coming soon!🎉

## SDK

vibe-llama also comes with a programmatic interface that you can call within your python scripts.

### `VibeLlamaStarter`

To replicate the `starter` command on the CLI and fetch all the needed instructions for your coding agents, you can use the following code:

```python
from vibe_llama.sdk import VibeLlamaStarter

starter = VibeLlamaStarter(
    agents=["GitHub Copilot", "Cursor"],
    services=["LlamaIndex", "llama-index-workflows"],
)

await starter.write_instructions(
    verbose=True, max_retries=20, retry_interval=0.7
)
```

## Contributing

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md) to get started.

## License

This project is licensed under the [MIT License](./LICENSE).
