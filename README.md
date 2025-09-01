# vibe-llama

**vibe-llama** is a set of tools that are designed to help developers build working and reliable applications with [LlamaIndex](https://github.com/run-llama/llama_index), [LlamaCloud Services](https://github.com/run-llama/llama_cloud_services) and [llama-index-workflows](https://github.com/run-llama/workflows-py).

This command-line tool provides two main capabilities:

**Context Injection:** Add relevant LlamaIndex context as rules to any coding agent of your choice (think Cursor, Claude Code, GitHub Copilot etc.). You select a coding agent and the LlamaIndex services you're working with, and vibe-llama generates rule files that give your AI assistant up-to-date knowledge about APIs, best practices, and common patterns.

Once you've made your choice, `vibe-llama` will generate a rule file for your coding agent. For example, if you selected Cursor, a new rule will be added to `.cursor/rules`. Now, all of the context and instructions about your chosen LlamaIndex service will be available to your coding agent of choice.

**Workflow Generation:** An interactive CLI agent that helps you build document-processing workflows from scratch. Describe what you want in natural language, provide reference documents, and get complete workflow code with detailed explanations.

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

Use the `-w`/`--overwrite` flag (works only from CLI) if you want to overwrite local files with the incoming ones downloaded by `vibe-llama starter`. On the TUI, you will be prompted to choose whether you want to overwrite existing files or not.

With `starter`, you can also launch a local MCP server (at http://127.0.0.1:8000/mcp) using the `-m`/`--mcp` flag. This server exposes a tool (`get_relevant_context`) that allows you to retrieve relevant documentation content based on a specific query. If you are interested in interacting with vibe-llama MCP programmatically, you can check the [SDK guide](#vibellamamcpclient).

**Example usage**

```bash
vibe-llama starter # Launch a TUI
vibe-llama starter -a 'GitHub Copilot' -s LlamaIndex -v # Select GitHub Copilot and LlamaIndex and enable verbose logging
vibe-llama starter -a 'Claude Code' -s llama-index-workflows -w # Select Claude Code and llama-index-workflows and allow to overwrite the existing CLAUDE.md
vibe-llama starter --mcp # Launch an MCP server
```

### docuflows

`docuflows` is a CLI agent that enables you to build and edit workflows that are oriented to intelligent document processing (combining llama-index-workflows and LlamaCloud).

In order to use this command, you need to first set your OpenAI API key and your [LlamaCloud API key](https://cloud.llamaindex.ai) as environment variables. Optionally, if you wish to use Anthropic LLMs, you should also set the Anthropic API key in your environment.

**On MacOS/Linux**

```bash
export OPENAI_API_KEY="your-openai-api-key"
export LLAMA_CLOUD_API_KEY="your-llama-cloud-api-key"
# optionally, for Anthropic usage
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

**On Windows**

```powershell
Set-Location Env:
$Env:OPENAI_API_KEY="your-openai-api-key"
$Env:LLAMA_CLOUD_API_KEY="your-llama-cloud-api-key"
# optionally, for Anthropic usage
$Env:ANTHROPIC_API_KEY="your-anthropic-api-key"
```

Once you have the needed API keys in the environment, running `vibe-llama docuflows` will start a terminal interface where you will be able to interactively talk to the agent and create or edit document-centered workflows with the help of it.

**Example usage**

```bash
vibe-llama docuflows
```

> [!NOTE]
>
> _`vibe-llama docuflows` uses **AGENTS.md** as an instructions file (located under `.vibe-llama/rules/`). If you wish, you can directly create AGENTS.md with the `starter` command, by selecting `vibe-llama docuflows` as your agent. Alternatively, if an AGENTS.md is not present in your environment, `vibe-llama docuflows` will create one on the fly._

During an open session with `docuflows`, you will be prompted to configure your LlamaCloud settings (project and organization ID are required for this step), and then you will be able to create or edit workflows.

During the editing or generation process, you will be asked to provide reference files for your workflow (e.g. an invoice file if you are asking for an invoice-processing workflow), so make sure to prepare them.

Once the workflow generation/editing is finished, you will be able to save the code and the code-related explanation in a folder that will be created under `generated_workflows/`. In the folder you will find a `workflow.py` file, containing the code, and a `runbook.md` file, containing instructions and explanations related to the code.

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

### `VibeLlamaMCPClient`

> [!NOTE]
>
> _To interact with vibe-llama MCP server you can use any MCP client of your liking_.

This class implements an MCP client to interact directly and in a well-integrated way with vibe-llama MCP server.

You can use it as follows:

```python
from vibe_llama.sdk import VibeLlamaMCPClient

client = VibeLlamaMCPClient()

# list the available tools
await client.list_tools()

# retrieve specific documentation content
await client.retrieve_docs(query="Parsing pre-sets in LlamaParse")

# retrieve a certain number of matches
await client.retrieve_docs(query="Human in the loop", top_k=4)

# retrieve matches and parse the returned XML string
result = await client.retrieve_docs(
    query="Workflow Design Patterns", top_k=3, parse_xml=True
)
if "result" in result:
    print(result["result"])  # -> List of the top three matches for your query
else:
    print(result["error"])  # -> List of error messages
```

### `VibeLlamaDocsRetriever`

This class implements a retriever for vibe-llama documentation, leveraging BM25 (enhanced with stemming) for lightweight, on-disk indexing and retrieval.

You can use it as follows:

```python
retriever = VibeLlamaDocsRetriever()

# retrieve a maximum of 10 relevant documents pertaining to the query 'What is LlamaExtract?'
await retriever.retrieve(query="What is LlamaExtract?", top_k=10)
```

## Contributing

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md) to get started.

## License

This project is licensed under the [MIT License](./LICENSE).
