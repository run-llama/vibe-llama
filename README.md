# vibe-llama

**vibe-llama** is a set of tools that are designed to help developers build working and reliable applications with [LlamaIndex](https://github.com/run-llama/llama_index), [LlamaCloud Services](https://github.com/run-llama/llama_cloud_services) and [llama-index-workflows](https://github.com/run-llama/workflows-py).

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
uv pip install [-e] dist/*.whl
```

Use the `-e` flag if you want your local installation to be editable.

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

## Contributing

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md) to get started.

## License

This project is licensed under the [MIT License](./LICENSE).
