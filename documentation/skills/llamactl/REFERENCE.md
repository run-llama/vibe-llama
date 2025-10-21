# `llamactl` reference

## `auth-env`

Manage environments (distinct control plane API URLs). Environments determine which profiles are shown and where auth/project actions apply.

### Usage

```bash
llamactl auth env [COMMAND] [options]
```

Commands:

- `list`: List known environments and mark the current one
- `add <API_URL> [--interactive/--no-interactive]`: Probe the server and upsert the environment
- `switch [API_URL] [--interactive/--no-interactive]`: Select the current environment (prompts if omitted)
- `delete [API_URL] [--interactive/--no-interactive]`: Remove an environment and its associated profiles

Notes:

- Probing reads `requires_auth` and `min_llamactl_version` from the server version endpoint.
- Switching environment filters profiles shown by `llamactl auth list` and used by other commands.

### Commands

#### List

```bash
llamactl auth env list
```

Shows a table of environments with API URL, whether auth is required, and the current marker.

#### Add

```bash
llamactl auth env add <API_URL>
```

Probes the server at `<API_URL>` and stores discovered settings. Interactive mode can prompt for the URL.

#### Switch

```bash
llamactl auth env switch [API_URL]
```

Sets the current environment. If omitted in interactive mode, you’ll be prompted to select one.

#### Delete

```bash
llamactl auth env delete [API_URL]
```

Deletes an environment and all associated profiles. If the deleted environment was current, the current environment is reset to the default.

### See also

- Profiles and tokens: [`llamactl auth`](/python/cloud/llamaagents/llamactl-reference/commands-auth)
- Getting started: [Introduction](/python/cloud/llamaagents/getting-started)
- Deployments: [`llamactl deployments`](/python/cloud/llamaagents/llamactl-reference/commands-deployments)

## `auth`

Authenticate and manage profiles for the current environment. Profiles store your control plane API URL, project, and optional API key.

### Usage

```bash
llamactl auth [COMMAND] [options]
```

Commands:

- `token [--project-id ID] [--api-key KEY] [--interactive/--no-interactive]`: Create profile from API key; validates token and selects a project
- `login`: Login via web browser (OIDC device flow) and create a profile
- `list`: List login profiles in the current environment
- `switch [NAME] [--interactive/--no-interactive]`: Set currently logged in user/token
- `logout [NAME] [--interactive/--no-interactive]`: Delete a login and its local data
- `project [PROJECT_ID] [--interactive/--no-interactive]`: Change the active project for the current profile

Notes:

- Profiles are filtered by the current environment (`llamactl auth env switch`).
- Non-interactive `token` requires both `--api-key` and `--project-id`.

### Commands

#### Token

```bash
llamactl auth token [--project-id ID] [--api-key KEY] [--interactive/--no-interactive]
```

- Interactive: Prompts for API key (masked), validates it by listing projects, then lets you choose a project. Creates an auto‑named profile and sets it current.
- Non‑interactive: Requires both `--api-key` and `--project-id`.

#### Login

```bash
llamactl auth login
```

Login via your browser using the OIDC device flow, select a project, and create a login profile set as current.

#### List

```bash
llamactl auth list
```

Shows a table of profiles for the current environment with name and active project. The current profile is marked with `*`.

#### Switch

```bash
llamactl auth switch [NAME] [--interactive/--no-interactive]
```

Set the current profile. If `NAME` is omitted in interactive mode, you will be prompted to select one.

#### Logout

```bash
llamactl auth logout [NAME] [--interactive/--no-interactive]
```

Delete a profile. If the deleted profile is current, the current selection is cleared.

#### Project

```bash
llamactl auth project [PROJECT_ID] [--interactive/--no-interactive]
```

Change the active project for the current profile. In interactive mode, select from server projects. In environments that don't require auth, you can also enter a project ID.

### See also

- Environments: [`llamactl auth env`](/python/cloud/llamaagents/llamactl-reference/commands-auth-env)
- Getting started: [Introduction](/python/cloud/llamaagents/getting-started)
- Deployments: [`llamactl deployments`](/python/cloud/llamaagents/llamactl-reference/commands-deployments)

## `deployments`

Deploy your app to the cloud and manage existing deployments. These commands operate on the project configured in your profile.

### Usage

```bash
llamactl deployments [COMMAND] [options]
```

Commands:

- `list`: List deployments for the configured project
- `get [DEPLOYMENT_ID] [--non-interactive]`: Show details; opens a live monitor unless `--non-interactive`
- `create`: Interactively create a new deployment
- `edit [DEPLOYMENT_ID]`: Interactively edit a deployment
- `delete [DEPLOYMENT_ID] [--confirm]`: Delete a deployment; `--confirm` skips the prompt
- `update [DEPLOYMENT_ID]`: Pull latest code from the configured branch and redeploy

Notes:

- If `DEPLOYMENT_ID` is omitted, you’ll be prompted to select one.
- All commands accept global options (profile, host, etc.).

### Commands

#### List

```bash
llamactl deployments list
```

Shows a table of deployments with name, id, status, repo, deployment file, git ref, and secrets summary.

#### Get

```bash
llamactl deployments get [DEPLOYMENT_ID] [--non-interactive]
```

- Default behavior opens a live monitor with status and streaming logs.
- Use `--non-interactive` to print details to the console instead of opening the monitor.

#### Create (interactive)

```bash
llamactl deployments create
```

Starts an interactive flow to create a deployment. You can provide values like repository, branch, deployment file path, and secrets. (Flags such as `--repo-url`, `--name`, `--deployment-file-path`, `--git-ref`, `--personal-access-token` exist but creation is currently interactive.)

#### Edit (interactive)

```bash
llamactl deployments edit [DEPLOYMENT_ID]
```

Opens an interactive form to update deployment settings.

#### Delete

```bash
llamactl deployments delete [DEPLOYMENT_ID] [--confirm]
```

Deletes a deployment. Without `--confirm`, you’ll be asked to confirm.

#### Update

```bash
llamactl deployments update [DEPLOYMENT_ID]
```

Refreshes the deployment to the latest commit on the configured branch and shows the resulting Git SHA change.

### See also

- Getting started: [Introduction](/python/cloud/llamaagents/getting-started)
- Configure names, env, and UI: [Deployment Config Reference](/python/cloud/llamaagents/configuration-reference)
- Local dev server: [`llamactl serve`](/python/cloud/llamaagents/llamactl-reference/commands-serve)

## `init`

Create a new app from a starter template, or update an existing app to the latest template version.

### Usage

```bash
llamactl init [--template <id>] [--dir <path>] [--force]
llamactl init --update
```

### Templates

- basic-ui: A basic starter workflow with a React Vite UI
- extraction-review: Extraction Agent with Review UI (Llama Cloud integration; review/correct extracted results)

If omitted, you will be prompted to choose interactively.

### Options

- `--update`: Update the current app to the latest template version. Ignores other options.
- `--template <id>`: Template to use (`basic-ui`, `extraction-review`).
- `--dir <path>`: Directory to create the new app in. Defaults to the template name.
- `--force`: Overwrite the directory if it already exists.

### What it does

- Copies the selected template into the target directory using [`copier`](https://copier.readthedocs.io/en/stable/)
- Adds assistant docs: `AGENTS.md` and symlinks `CLAUDE.md`/`GEMINI.md`
- initializes a Git repository if `git` is available
- Prints next steps to run locally and deploy

### Examples

- Interactive flow:

```bash
llamactl init
```

- Non‑interactive creation:

```bash
llamactl init --template basic-ui --dir my-app
```

- Overwrite an existing directory:

```bash
llamactl init --template basic-ui --dir ./basic-ui --force
```

- Update an existing app to the latest template:

```bash
llamactl init --update
```

See also: [Getting Started guide](/python/cloud/llamaagents/getting-started).

## `serve`

Serve your app locally for development and testing. Reads configuration from your project (e.g., `pyproject.toml` or `llama_deploy.yaml`) and starts the Python API server, optionally proxying your UI in dev.

See also: [Deployment Config Reference](/python/cloud/llamaagents/configuration-reference) and [UI build and dev integration](/python/cloud/llamaagents/ui-build).

### Usage

```bash
llamactl serve [DEPLOYMENT_FILE] [options]
```

- `DEPLOYMENT_FILE` defaults to `.` (current directory). Provide a path to a specific deployment file or directory if needed.

### Options

- `--no-install`: Skip installing Python and JS dependencies
- `--no-reload`: Disable API server auto‑reload on code changes
- `--no-open-browser`: Do not open the browser automatically
- `--preview`: Build the UI to static files and serve them (production‑like)
- `--port <int>`: Port for the API server
- `--ui-port <int>`: Port for the UI proxy in dev

### Behavior

- Prepares the server environment (installs dependencies unless `--no-install`)
- In dev mode (default), proxies your UI dev server and reloads on change
- In preview mode, builds the UI to static files and serves them without a proxy
