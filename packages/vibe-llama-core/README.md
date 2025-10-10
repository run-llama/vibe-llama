# vibe-llama-core

`vibe-llama-core` is a reduced version of `vibe-llama` containing only the code for downloading documentation and templates.

## Installation

**User settings**

Or you can use `pip` to install the package:

```bash
pip install vibe-llama-core
```

**Developer settings**

Clone the GitHub repository:

```bash
git clone https://github.com/run-llama/vibe-llama
cd vibe-llama/packages/vibe-llama-core
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

### `docs` module

You can use the `docs` module to download agent rules files:

```python
import asyncio

from pathlib import Path
from vibe_llama_core.docs import get_agent_rules


async def main():
    await get_agent_rules(agent="GitHub Copilot", service="LlamaIndex")
    # check that rule file exists
    assert Path(".github/copilot-instructions.md").is_file()


if __name__ == "__main__":
    asyncio.run(main())
```

### `templates` module

You can use the `templates` module to download workflows templates:

```python
import asyncio

from vibe_llama_core.templates import download_template


async def main():
    await download_template(
        request="web_scraping", path="./workflows-templates/"
    )


if __name__ == "__main__":
    asyncio.run(main())
```

## Contributing

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md) to get started.

## License

This project is licensed under the [MIT License](../LICENSE).
