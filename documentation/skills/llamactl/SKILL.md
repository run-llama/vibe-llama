---
name: Use llamactl - a CLI tool for LlamaAgents
description: Use llamactl to initialize, locally preview, deploy and manage LlamaIndex workflows as LlamaAgents. Required llama-index-workflows and llamactl to be installed in the environment.
---

# Use llamactl - a CLI tool for LlamaAgents

`llamactl` is a CLI tool for developing and deploying LlamaIndex workflows as LlamaAgents. It provides commands to initialize projects, run local development servers, and manage cloud deployments.

## Prerequisites

Before using `llamactl`, ensure you have:

- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) - Python package manager and build tool
- Node.js - Required for UI development (supports `npm`, `pnpm`, or `yarn`)
- `llama-index-workflows` and `llamactl` installed in your environment

## Installation

Install `llamactl` globally using `uv`:

```bash
uv tool install -U llamactl
llamactl --help
```

Or try it without installing:

```bash
uvx llamactl --help
```

## Initialize a Project

Create a new LlamaAgents project with starter templates:

```bash
llamactl init
```

This creates a Python module with LlamaIndex workflows and an optional UI frontend. Configuration is managed in `pyproject.toml`, where you define workflow instances, environment settings, and UI build options.

## Local Development

Start the local development server:

```bash
llamactl serve
```

This command:

1. Installs dependencies
2. Serves workflows as an API (configured in `pyproject.toml`)
3. Starts the frontend development server

The server automatically detects file changes and can resume in-progress workflows.

## Deploy to LlamaCloud

Push your code to a git repository:

```bash
git remote add origin https://github.com/org/repo
git add -A
git commit -m 'Set up new app'
git push -u origin main
```

Create a cloud deployment:

```bash
llamactl deployments create
```

This opens an interactive Terminal UI to configure:

- Deployment name
- Git repository (supports private GitHub repos via the LlamaDeploy GitHub app)
- Git branch/tag/commit
- Environment secrets

## Manage Deployments

- View deployment status: `llamactl deployments get`
- Update secrets or branch: `llamactl deployments edit`
- Deploy new version: `llamactl deployments update`

For detailed configuration options, see the [Deployment Config Reference](https://developers.llamaindex.ai/python/cloud/llamaagents/configuration-reference).
