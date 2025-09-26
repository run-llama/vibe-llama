## LlamaAgents at a glance

LlamaAgents helps you build and deploy small, workflow‑driven agentic apps using LlamaIndex, locally and on LlamaCloud. Define LlamaIndex workflows, run them as durable APIs that can pause for input, optionally add a UI, and deploy to LlamaCloud in seconds.

LlamaAgents is for developers and teams building automation, internal tools, and app‑like agent experiences without heavy infrastructure work.

Build and ship small, focused agentic apps—fast. Start from either our templated LlamaIndex workflow apps, or from workflows you've already prototyped, iterate locally, and deploy to LlamaCloud right from your terminal in seconds.

- Write [LlamaIndex Python workflows](https://developers.llamaindex.ai/python/workflows/), and serve them as an API. For example, make a request to process incoming files, analyze them, and return the result or forward them on to another system.
- Workflow runs are durable, and can wait indefinitely for human or other external inputs before proceeding.
- Optionally add a UI for user-driven applications. Make custom chat applications, data extraction and review applications.
- Deploy your app in seconds to LlamaCloud. Call it as an API with your API key, or visit it secured with your LlamaCloud login.

LlamaAgents is built on top of LlamaIndex's (soon-to-be) open source LlamaDeploy v2. LlamaDeploy is a toolchain to create, develop, and deploy workflows. The `llamactl` command line interface (CLI) is the main point of entry to developing LlamaDeploy applications: It can scaffold LlamaDeploy based projects with `llamactl init`, serve them with `llamactl serve`, and deploy with `llamactl deployments create`.

In addition to LlamaDeploy, LlamaIndex published additional SDKs to facilitate rapid development:

- Our `llama-cloud-services` JS and Python SDKs offer a simple way to persist ad hoc Agent Data. [Read more here](/python/cloud/llamaagents/agent-data-overview).
- Our `@llamaindex/ui` React library offers off-the-shelf components and hooks to facilitate developing workflow-driven UIs.

# Getting Started with LlamaDeploy

LlamaDeploy is composed of the [`llamactl` CLI for development](https://pypi.org/project/llamactl/). `llamactl` bootstraps an application server that manages running and persisting your workflows, and a control plane for managing cloud deployments of applications. It has some system pre-requisites that must be installed in order to work:

- Make sure you have [`uv`](https://docs.astral.sh/uv/getting-started/installation/) installed. `uv` is a Python package manager and build tool. `llamactl` integrates with it in order to quickly manage your project's build and dependencies.
- Likewise, Node.js is required for UI development. You can use your node package manager of choice (`npm`, `pnpm`, or `yarn`).

## Install

Choose one:

- Try without installing:

```bash
uvx llamactl --help
```

- Install globally (recommended):

```bash
uv tool install -U llamactl
llamactl --help
```

## Initialize a project

`llamactl` includes starter templates for both full‑stack UI apps, and headless (API only) workflows. Pick a template and customize it.

```bash
llamactl init
```

This will prompt for some details, and create a Python module that contains LlamaIndex workflows, plus an optional UI you can serve as a static frontend.

Application configuration is managed within your project's `pyproject.toml`, where you can define Python workflow instances that should be served, environment details, and configuration for how the UI should be built. See the [Deployment Config Reference](/python/cloud/llamaagents/configuration-reference) for details on all configurable fields.

## Develop

Once you have a project, you can run the dev server for your application:

```bash
llamactl serve
```

`llamactl serve` will

1. Install all required dependencies
2. Read the workflows configured in your app’s `pyproject.toml` and serve them as an API
3. Start up and proxy the frontend development server, so you can seamlessly write a full stack application.

For example, with the following configuration, the app will be served at `http://localhost:4501/deployments/my-package`. Make a `POST` request to `/deployments/my-package/workflows/my-workflow/run` to trigger the workflow in `src/my_package/my_workflow.py`.

```toml
[project]
name = "my-package"
# ...
[tool.llamadeploy.workflows]
my-workflow = "my_package.my_workflow:workflow"

[tool.llamadeploy.ui]
directory = "ui"
```

```py
# src/my_package/my_workflow.py
# from workflows import ...
# ...
workflow = MyWorkflow()
```

At this point, you can get to coding. The development server will detect changes as you save files. It will even resume in-progress workflows!

For more information about CLI flags available, see [`llamactl serve`](/python/cloud/llamacloud/llamadeploy/llamactl-reference/commands-serve).

For a more detailed reference on how to define and expose workflows, see [Workflows & App Server API](/python/cloud/llamacloud/llamadeploy/workflow-api).

## Create a Deployment

LlamaDeploy applications can be rapidly deployed just by pointing to a source git repository. With the provided repository configuration, LlamaCloud will clone, build, and serve your app. It can even access GitHub private repositories by installing the [LlamaDeploy GitHub app](https://github.com/apps/llama-deploy)

Example:

```bash
git remote add origin https://github.com/org/repo
git add -A
git commit -m 'Set up new app'
git push -u origin main
```

Then, create a deployment:

```bash
llamactl deployments create
```

:::info
The first time you run this, you'll be prompted to log into LlamaCloud. See [`llamactl auth`](./llamactl-reference/commands-auth) for more info
:::

This will open an interactive Terminal UI (TUI). You can tab through fields, or even point and click with your mouse if your terminal supports it. All required fields should be automatically detected from your environment, but can be customized:

- Name: Human‑readable and URL‑safe; appears in your deployment URL
- Git repository: Public HTTP or private GitHub (install the LlamaDeploy GitHub app for private repos)
- Git branch: Branch to pull and build from (use `llamactl deployments update` to roll forward). This can also be a tag or a git commit.
- Secrets: Pre‑filled from your local `.env`; edit as needed. These cannot be read again after creation.

When you save, LlamaDeploy will verify that it has access to your repository, (and prompt you to install the GitHub app if not)

After creation, the TUI will show deployment status and logs.

- You can later use `llamactl deployments get` to view again.
- You can add secrets or change branches with `llamactl deployments edit`.
- If you update your source repo, run `llamactl deployments update` to roll a new version.

<!-- sep---sep -->

# Serving your Workflows

LlamaDeploy runs your LlamaIndex workflows locally and in the cloud. Author your workflows, add minimal configuration, and `llamactl` wraps them in an application server that exposes them as HTTP APIs.

## Learn the basics (LlamaIndex Workflows)

LlamaDeploy is built on top of LlamaIndex workflows. If you're new to workflows, start here: [LlamaIndex Workflows](/python/workflows).

## Author a workflow (quick example)

```python
# src/app/workflows.py
from llama_index.core.workflow import Workflow, step, StartEvent, StopEvent


class QuestionFlow(Workflow):
    @step
    async def generate(self, ev: StartEvent) -> StopEvent:
        question = ev.question
        return StopEvent(result=f"Answer to {question}")


qa_workflow = QuestionFlow(timeout=120)
```

## Configure workflows for LlamaDeploy to serve

LlamaDeploy reads workflows configured in your `pyproject.toml` and makes them available under their configured names.

Define workflow instances in your code, then reference them in your config.

```toml
# pyproject.toml
[project]
name = "app"
# ...
[tool.llamadeploy.workflows]
answer-question = "app.workflows:qa_workflow"
```

## How serving works (local and cloud)

- `llamactl serve` discovers your config. See [`llamactl serve`](/python/cloud/llamaagents/llamactl-reference/commands-serve).
- The app server loads your workflows.
- HTTP routes are exposed under `/deployments/{name}`. In development, `{name}` defaults to your Python project name and is configurable. On deploy, you can set a new name; a short random suffix may be appended to ensure uniqueness.
- Workflow instances are registered under the specified name. For example, `POST /deployments/app/workflows/answer-question/run` runs the workflow above.
- If you configure a UI, it runs alongside your API (proxied in dev, static in preview). For details, see [UI build and dev integration](/python/cloud/llamaagents/ui-build).

During development, the API is available at `http://localhost:4501`. After you deploy to LlamaCloud, it is available at `https://api.cloud.llamaindex.ai`.

### Authorization

During local development, the API is unprotected. After deployment, your API uses the same authorization as LlamaCloud. Create an API token in the same project as the agent to make requests. For example:

```bash
curl 'https://api.cloud.llamaindex.ai/deployments/app-xyz123/workflows/answer-question/run' \
  -H 'Authorization: Bearer llx-xxx' \
  -H 'Content-Type: application/json' \
  --data '{"start_event": {"question": "What is the capital of France?"}}'
```

## Workflow HTTP API

When using a `WorkflowServer`, the app server exposes your workflows as an API. View the OpenAPI reference at `/deployments/<name>/docs`.

This API allows you to:

- Retrieve details about registered workflows
- Trigger runs of your workflows
- Stream published events from your workflows, and retrieve final results from them
- Send events to in-progress workflows (for example, HITL scenarios).

During development, visit `http://localhost:4501/debugger` to test and observe your workflows in a UI.

<!-- sep---sep -->

# Configuring a UI

This page explains how to configure a custom frontend that builds and communicates with your LlamaDeploy workflow server. If you've started from a template, you're good to go. Read on to learn more.

The LlamaDeploy toolchain is unopinionated about your UI stack — bring your own UI. Most templates use Vite with React, but any framework will work that can:

- build static assets for production, and
- read a few environment variables during build and development

## How the integration works

`llamactl` starts and proxies your frontend during development by calling your `npm run dev` command. When you deploy, it builds your UI statically with `npm run build`. These commands are configurable; see [UIConfig](/python/cloud/llamaagents/configuration-reference#uiconfig-fields) in the configuration reference. You can also use other package managers if you have [corepack](https://nodejs.org/download/release/v19.9.0/docs/api/corepack.html) enabled.

During development, `llamactl` starts its workflow server (port `4501` by default) and starts the UI, passing a `PORT` environment variable (set to `4502` by default) and a `LLAMA_DEPLOY_DEPLOYMENT_BASE_PATH` (for example, `/deployments/<name>/ui`) where the UI will be served. It then proxies requests from the server to the client app from that base path.

Once deployed, the Kubernetes operator builds your application with the configured npm script (`build` by default) and serves your static assets at the same base path.

## Required configuration

1. Serve the dev UI on the configured `PORT`. This environment variable tells your dev server which port to use during development. Many frameworks, such as Next.js, read this automatically.
2. Set your app's base path to the value of `LLAMA_DEPLOY_DEPLOYMENT_BASE_PATH`. LlamaDeploy applications rely on this path to route to multiple workflow deployments. The proxy leaves this path intact so your application can link internally using absolute paths. Your development server and router need to be aware of this base path. Most frameworks provide a way to configure it. For example, Vite uses [`base`](https://vite.dev/config/shared-options.html#base).
3. Re-export the `LLAMA_DEPLOY_DEPLOYMENT_BASE_PATH` env var to your application. Read this value (for example, in React Router) to configure a base path. This is also often necessary to link static assets correctly.
4. If you're integrating with LlamaCloud, re-export the `LLAMA_DEPLOY_PROJECT_ID` env var to your application and use it to scope your LlamaCloud requests to the same project. Read more in the [Configuration Reference](/python/cloud/llamaagents/configuration-reference#authorization).
5. We also recommend re-exporting `LLAMA_DEPLOY_DEPLOYMENT_NAME`, which can be helpful for routing requests to your workflow server correctly.

## Examples

### Vite (React)

Configure `vite.config.ts` to read the injected environment and set the base path and port:

```ts
// vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(() => {
  const basePath = process.env.LLAMA_DEPLOY_DEPLOYMENT_BASE_PATH;
  const port = process.env.PORT ? parseInt(process.env.PORT) : undefined;
  return {
    plugins: [react()],
    server: { port, host: true, hmr: { port } },
    base: basePath,
    // Pass-through env for client usage
    define: {
      ...(basePath && {
        "import.meta.env.VITE_LLAMA_DEPLOY_DEPLOYMENT_BASE_PATH":
          JSON.stringify(basePath),
      }),
      ...(process.env.LLAMA_DEPLOY_DEPLOYMENT_NAME && {
        "import.meta.env.VITE_LLAMA_DEPLOY_DEPLOYMENT_NAME": JSON.stringify(
          process.env.LLAMA_DEPLOY_DEPLOYMENT_NAME,
        ),
      }),
      ...(process.env.LLAMA_DEPLOY_PROJECT_ID && {
        "import.meta.env.VITE_LLAMA_DEPLOY_PROJECT_ID": JSON.stringify(
          process.env.LLAMA_DEPLOY_PROJECT_ID,
        ),
      }),
    },
  };
});
```

Scripts in `package.json` typically look like:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build"
  }
}
```

### Next.js (static export)

Next.js supports static export. Configure `next.config.mjs` to use the provided base path and enable static export:

```js
// next.config.mjs
const basePath = process.env.LLAMA_DEPLOY_DEPLOYMENT_BASE_PATH || "";
const deploymentName = process.env.LLAMA_DEPLOY_DEPLOYMENT_NAME;
const projectId = process.env.LLAMA_DEPLOY_PROJECT_ID;

export default {
  // Mount app under /deployments/<name>/ui
  basePath,
  // For assets when hosted behind a path prefix
  assetPrefix: basePath || undefined,
  // Enable static export for production
  output: "export",
  // Expose base path to browser for runtime URL construction
  env: {
    NEXT_PUBLIC_LLAMA_DEPLOY_DEPLOYMENT_BASE_PATH: basePath,
    NEXT_PUBLIC_LLAMA_DEPLOY_DEPLOYMENT_NAME: deploymentName,
    NEXT_PUBLIC_LLAMA_DEPLOY_PROJECT_ID: projectId,
  },
};
```

Ensure your scripts export to a directory (default: `out/`):

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build && next export"
  }
}
```

The dev server binds to the `PORT` the app server sets; no additional configuration is needed. For dynamic routes or server features not compatible with static export, you can omit the export and rely on proxying to the Python app server. However, production static hosting requires a build output directory.

#### Runtime URL construction (images/assets)

- Vite: use the configured `base` or `import.meta.env.BASE_URL` (or the pass-through variable) to prefix asset URLs you build at runtime:

```tsx
const base =
  import.meta.env.VITE_LLAMA_DEPLOY_DEPLOYMENT_BASE_PATH ||
  import.meta.env.BASE_URL ||
  "/";
<img src={`${base.replace(/\/$/, "")}/images/logo.png`} />;
```

- Next.js static export: use the exposed `NEXT_PUBLIC_LLAMA_DEPLOY_DEPLOYMENT_BASE_PATH` so routes resolve absolute asset paths correctly:

```tsx
const base = process.env.NEXT_PUBLIC_LLAMA_DEPLOY_DEPLOYMENT_BASE_PATH || "";
export default function Logo() {
  return <img src={`${base}/images/logo.png`} alt="logo" />;
}
```

## Configure the UI output directory

Your UI must output static assets that the platform can locate. Configure `ui.directory` and `ui.build_output_dir` as described in the [Deployment Config Reference](/python/cloud/llamaagents/configuration-reference#uiconfig-fields). Default: `${ui.directory}/dist`

<!-- sep---sep -->

# Workflow React Hooks

### `@llamaindex/ui`

Our React library, `@llamaindex/ui`, is the recommended way to integrate your UI with a LlamaDeploy workflow server and LlamaCloud. It comes pre-installed in any of our templates containing a UI. The library provides both React hooks for custom integrations and standard components.

### Workflows Hooks

Our React hooks provide an idiomatic way to observe and interact with your LlamaDeploy workflows remotely from a frontend client.

There are 3 hooks you can use:

1. **useWorkflowRun**: Start a workflow run and observe its status.
2. **useWorkflowHandler**: Observe and interact with a single run; stream and send events.
3. **useWorkflowHandlerList**: Monitor and update a list of recent or in-progress runs.

### Client setup

Configure the hooks with a workflow client. Wrap your app with an `ApiProvider` that points to your deployment:

```tsx
import {
  ApiProvider,
  type ApiClients,
  createWorkflowClient,
} from "@llamaindex/ui";

const deploymentName =
  (import.meta as any).env?.VITE_LLAMA_DEPLOY_DEPLOYMENT_NAME || "default";

const clients: ApiClients = {
  workflowsClient: createWorkflowClient({
    baseUrl: `/deployments/${deploymentName}`,
  }),
};

export function Providers({ children }: { children: React.ReactNode }) {
  return <ApiProvider clients={clients}>{children}</ApiProvider>;
}
```

### Start a run

Start a workflow by name with `useWorkflowRun`. Provide a JSON input payload. You get a `handler_id` back immediately.

```tsx
import { useState } from "react";
import { useWorkflowRun } from "@llamaindex/ui";

export function RunButton() {
  const { runWorkflow, isCreating, error } = useWorkflowRun();
  const [handlerId, setHandlerId] = useState<string | null>(null);

  async function handleClick() {
    const handler = await runWorkflow("my_workflow", { user_id: "123" });
    // e.g., navigate to a details page using handler.handler_id
    console.log("Started:", handler.handler_id);
    setHandlerId(handler.handler_id);
  }

  return (
    <>
      <button disabled={isCreating} onClick={handleClick}>
        {isCreating ? "Starting…" : "Run Workflow"}
      </button>
      {/* Then, use the handler ID to show details or send events */}
      <HandlerDetails handlerId={handlerId} />
    </>
  );
}
```

### Watch a run and stream events

Subscribe to a single handler’s live event stream and show status with `useWorkflowHandler`.

```tsx
import { useWorkflowHandler } from "@llamaindex/ui";

export function HandlerDetails({ handlerId }: { handlerId: string | null }) {
  // Note, the state will remain empty if the handler ID is empty
  const { handler, events, sendEvent } = useWorkflowHandler(
    handlerId ?? "",
    true,
  );

  // Find the final StopEvent to extract the workflow result (if provided)
  const stop = events.find(
    (e) =>
      e.type.endsWith(
        ".StopEvent",
      ) /* event type contains the event's full Python module path, e.g., workflows.events.StopEvent */,
  );

  return (
    <div>
      <div>
        <strong>{handler.handler_id}</strong> — {handler.status}
      </div>
      {stop ? (
        <pre>{JSON.stringify(stop.data, null, 2)}</pre>
      ) : (
        <pre style={{ maxHeight: 240, overflow: "auto" }}>
          {JSON.stringify(events, null, 2)}
        </pre>
      )}
    </div>
  );
}
```

You can subscribe to the same handler with multiple hooks and access a shared events list. This is useful when, for example, one component shows toast messages for certain event types while another component shows the final result.

### Monitor multiple workflow runs

Subscribe to the full list or a filtered list of workflow runs with `useWorkflowHandlerList`. This is useful for a progress indicator or a lightweight “Recent runs” view.

```tsx
import { useWorkflowHandlerList } from "@llamaindex/ui";

export function RecentRuns() {
  const { handlers, loading, error } = useWorkflowHandlerList();
  if (loading) return <div>Loading…</div>;
  if (error) return <div>Error: {error}</div>;
  return (
    <ul>
      {handlers.map((h) => (
        <li key={h.handler_id}>
          {h.handler_id} — {h.status}
        </li>
      ))}
    </ul>
  );
}
```

<!-- sep---sep -->

# Deployment Config Reference

LlamaDeploy reads configuration from your repository to run your app. The configuration is defined in your project's `pyproject.toml`.

### pyproject.toml

```toml
[tool.llamadeploy]
name = "my-app"
env_files = [".env"]

[tool.llamadeploy.workflows]
workflow-one = "my_app.workflows:some_workflow"
workflow-two = "my_app.workflows:another_workflow"

[tool.llamadeploy.ui]
directory = "ui"
build_output_dir = "ui/static"
```

### Authentication

Deployments can be configured to automatically inject authentication for LlamaCloud.

```toml
[tool.llamadeploy]
llama_cloud = true
```

When this is set:

- During development, `llamactl` prompts you to log in to LlamaCloud if you're not already. After that, it injects `LLAMA_CLOUD_API_KEY`, `LLAMA_CLOUD_PROJECT_ID`, and `LLAMA_CLOUD_BASE_URL` into your Python server process and JavaScript build.
- When deployed, LlamaCloud automatically injects a dedicated API key into the Python process. The frontend process receives a short-lived session cookie specific to each user visiting the application. Therefore, configure the project ID on the frontend API client so that LlamaCloud API requests from the frontend and backend are scoped to the same project ID.

### `.env` files

Most apps need API keys (e.g., OpenAI). You can specify them via a `.env` file and reference it in your config:

```toml
[tool.llamadeploy]
env_files = [".env"]
```

Then set your secrets:

```bash
# .env
OPENAI_API_KEY=sk-xxxx
```

### Alternative file formats (YAML/TOML)

If you prefer to keep your `pyproject.toml` simple, you can write the same configuration in a `llama_deploy.yaml` or `llama_deploy.toml` file. All fields use the same structure and types; omit the `tool.llamadeploy` prefix.

## Schema

### DeploymentConfig fields

| Field         | Type                     | Default     | Description                                                                                                   |
| ------------- | ------------------------ | ----------- | ------------------------------------------------------------------------------------------------------------- |
| `name`        | string                   | `"default"` | URL-safe deployment name. In `pyproject.toml`, if omitted it falls back to `project.name`.                    |
| `workflows`   | map&lt;string,string&gt; | —           | Map of `workflowName -> "module.path:workflow"`.                                                              |
| `env_files`   | list&lt;string&gt;       | `[".env"]`  | Paths to env files to load. Relative to the config file. Duplicate entries are removed.                       |
| `env`         | map&lt;string,string&gt; | `{}`        | Environment variables injected at runtime.                                                                    |
| `llama_cloud` | boolean                  | false       | Indicates that a deployment connects to LlamaCloud. Set to true to automatically inject a LlamaCloud API key. |
| `ui`          | `UIConfig`               | `null`      | Optional UI configuration. `directory` is required if `ui` is present.                                        |

### UIConfig fields

| Field              | Type    | Default               | Description                                                                                                                                                                                                            |
| ------------------ | ------- | --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `directory`        | string  | —                     | Path to UI source, relative to the config directory. Required when `ui` is set.                                                                                                                                        |
| `build_output_dir` | string  | `${directory}/dist`   | Built UI output directory. If set in TOML/`pyproject.toml`, the path is relative to the config file. If set via `package.json` (`llamadeploy.build_output_dir`), it is resolved as `${directory}/${build_output_dir}`. |
| `package_manager`  | string  | `"npm"` (or inferred) | Package manager used to build the UI. If not set, inferred from `package.json` `packageManager` (e.g., `pnpm@9.0.0` → `pnpm`).                                                                                         |
| `build_command`    | string  | `"build"`             | NPM script name used to build.                                                                                                                                                                                         |
| `serve_command`    | string  | `"dev"`               | NPM script name used to serve in development.                                                                                                                                                                          |
| `proxy_port`       | integer | `4502`                | Port the app server proxies to in development.                                                                                                                                                                         |

## UI Integration via package.json

Note: after setting `ui.directory` so that `package.json` can be found, you can configure the UI within it instead.

For example:

```json
{
  "name": "my-ui",
  "packageManager": "pnpm@9.7.0",
  "scripts": { "build": "vite build", "dev": "vite" },
  "llamadeploy": {
    "build_output_dir": "dist",
    "package_manager": "pnpm",
    "build_command": "build",
    "serve_command": "dev",
    "proxy_port": 5173
  }
}
```

<!-- sep---sep -->

# Agent Data Overview

### What is Agent Data?

Skip the database setup. LlamaDeploy workflows and JavaScript UIs share a persistent Agent Data store built into the LlamaCloud API. It uses the same authentication as the rest of the API.

Agent Data is a queryable store for JSON records produced by your agents. Each record is linked to a `deployment_name` (the deployed agent) and an optional `collection` (a logical bucket; defaults to `default`). Use it to persist extractions, events, metrics, and other structured output, then search and aggregate across records.

Key concepts:

- **deployment_name**: the identifier of the agent deployment the data belongs to. Access is authorized against that agent’s project.
- **collection**: a logical namespace within an agent for organizing different data types or apps. Storage is JSON. We recommend storing homogeneous data types within a single collection.
- **data**: the JSON payload shaped by your app. SDKs provide typed wrappers.

Important behavior and constraints:

- **Deployment required**: The `deployment_name` must correspond to an existing deployment. Data is associated with that deployment and its project.
- **Local development**: When running locally, omit `deployment_name` to use the shared `_public` Agent Data store. Use distinct `collection` names to separate apps during local development.
- **Access control**: You can only read/write data for agents in projects you can access. `_public` data is visible across agents within the same project.
- **Filtering/Sorting**: You can filter on any `data` fields and on the top‑level `created_at` and `updated_at`. Sorting accepts a comma‑separated list; prefix fields inside `data` with `data.` (for example, `data.name desc, created_at`).
- **Aggregation**: Group by one or more data fields and optionally return per‑group counts and/or the first item.

Project scoping:

- You can scope requests to a specific project by providing the `Project-Id` header (UUID). This is especially important if your API key has access to multiple projects. Read more in the [Configuration Reference](/python/cloud/llamaagents/configuration-reference#authorization).

### Filter DSL

When searching or aggregating, you can filter on fields inside `data` and on the top‑level `created_at` and `updated_at` fields.

Example:

```json
{
  "age": { "gte": 21, "lt": 65 },
  "status": { "eq": "active" },
  "tag": { "includes": ["python", "ml"] },
  "created_at": { "gte": "2024-01-01T00:00:00Z" }
}
```

Supported operators:

Filter operators are specified using a simple JSON DSL and support the following per‑field operators:

- `eq` - Filters based on equality. For example, `{"age": {"eq": 30}}` matches age exactly 30.
- `gt` - Filters based on greater than. For example, `{"age": {"gt": 30}}` matches age greater than 30.
- `gte` - Filters based on greater than or equal to. For example, `{"age": {"gte": 30}}` matches age 30 or greater.
- `lt` - Filters based on less than. For example, `{"age": {"lt": 30}}` matches age less than 30.
- `lte` - Filters based on less than or equal to. For example, `{"age": {"lte": 30}}` matches age less than or equal to 30.
- `includes` - Filters based on inclusion. For example, `{"age": {"includes": [30, 31]}}` matches age containing 30 or 31. An empty array matches nothing.

All provided filters must match (logical AND).

Nested fields are addressed using dot notation. For example, `{"data.age": {"gt": 30}}` matches an age greater than 30 in the `data` object. Note: array index access is not supported.

SDKs and environments:

- The **JavaScript SDK** can be used in the browser. When your UI is deployed on LlamaCloud alongside your agent, it is automatically authenticated. In other environments, provide an API key. You can also set `Project-Id` on the underlying HTTP client to pin all requests to a project.
- The **Python SDK** runs server‑side and uses your API key and an optional base URL.

Next steps:

- Python usage: see [Agent Data (Python)](/python/cloud/llamaagents/agent-data-python)
- JavaScript usage: see [Agent Data (JavaScript)](/python/cloud/llamaagents/agent-data-javascript)

<!-- sep---sep -->

# Agent Data (Python)

See the [Agent Data Overview](/python/cloud/llamaagents/agent-data-overview) for concepts, constraints, and environment details.

### Install

```bash
uv add llama-cloud-services
```

### Client overview

The Python `llama-cloud-services` SDK provides `AsyncAgentDataClient` for working with the Agent Data API.

```python
import httpx
import os
from pydantic import BaseModel
from llama_cloud_services.beta.agent_data import AsyncAgentDataClient
from llama_cloud.client import AsyncLlamaCloud


class ExtractedPerson(BaseModel):
    name: str
    age: int
    email: str


project_id = os.getenv("LLAMA_DEPLOY_PROJECT_ID")

# Base URL and API key (if running outside LlamaCloud)
base_url = os.getenv("LLAMA_CLOUD_BASE_URL")
api_key = os.getenv("LLAMA_CLOUD_API_KEY")

# Reusable async HTTP client with optional project scoping
http_client = httpx.AsyncClient(
    headers={"Project-Id": project_id} if project_id else None
)

# Optional: base client for other SDK operations
base_client = AsyncLlamaCloud(
    base_url=base_url,
    token=api_key,
    httpx_client=http_client,
)

# Only set when deployed in LlamaCloud (falls back inside the Agent Data client)
deployment_name = os.getenv("LLAMA_DEPLOY_DEPLOYMENT_NAME")

client = AsyncAgentDataClient(
    type=ExtractedPerson,
    collection="extracted_people",
    # If omitted, uses LLAMA_DEPLOY_DEPLOYMENT_NAME or "_public"
    deployment_name=deployment_name,
    client=base_client,
)
```

### Create, Get, Update, Delete

```python
person = ExtractedPerson(name="John Doe", age=30, email="john@example.com")
created = await client.create_item(person)
fetched = await client.get_item(created.id)
updated = await client.update_item(
    created.id, ExtractedPerson(name="Jane", age=31, email="jane@example.com")
)
await client.delete_item(updated.id)
```

Retry behavior: Network errors (timeouts, connection errors, retriable HTTP statuses) are retried up to 3 times with exponential backoff.

Notes:

- Updates overwrite the entire `data` object.
- `get_item` raises an `httpx.HTTPStatusError` with status code 404 if not found.

### Search

You can filter by `data` fields and by `created_at`/`updated_at` (top-level fields). Sort using a comma-delimited list of fields; the `data.` prefix is required when sorting by data fields. The default page size is 50 (max 1000).

```python
results = await client.search(
    filter={
        # Data fields
        "age": {"gte": 21, "lt": 65},
        "status": {"eq": "active"},
        "tags": {"includes": ["python", "ml"]},
        # Top-level timestamps (ISO strings accepted)
        "created_at": {"gte": "2024-01-01T00:00:00Z"},
    },
    order_by="data.name desc, created_at",
    page_size=50,
    offset=0,
    include_total=True,  # request only on the first page if needed
)

for item in results.items:
    print(item.data)

print(results.has_more, results.total)
```

Sorting:

- Example: `"data.name desc, created_at"`.
- If no sort is provided, results default to `created_at desc`.

Pagination:

- Use `offset` and `page_size`. The server may return `has_more` and a `next_page_token` (SDK exposes `has_more`).

### Aggregate

Group data by one or more `data` fields, optionally count items per group, and/or fetch the first item per group.

```python
agg = await client.aggregate(
    filter={"status": {"eq": "active"}},
    group_by=["department", "role"],
    count=True,
    first=True,  # return the earliest item per group (by created_at)
    order_by="data.department asc, data.role asc",
    page_size=100,
)

for group in agg.items:  # items are groups
    print(group.group_key)  # {"department": "Sales", "role": "AE"}
    print(group.count)  # optional
    print(group.first_item)  # optional dict
```

Details:

- `group_by`: dot-style data paths (e.g., `"department"`, `"contact.email"`).
- `count`: adds a `count` per group.
- `first`: returns the first `data` item per group (earliest `created_at`).
- `order_by`: uses the same semantics as search (applies to group key expressions).
- Pagination uses `offset` and `page_size` similarly to search.

<!-- sep---sep -->

# Agent Data (JavaScript)

### Overview

Agent Data is a JSON store tied to a `deploymentName` and `collection`. Use the official JavaScript SDK with strong typing for CRUD, search, and aggregation.

See the [Agent Data Overview](/python/cloud/llamaagents/agent-data-overview) for concepts, constraints, and environment details.

Install:

```bash
npm i -S llama-cloud-services
```

Key imports:

```ts
import {
  AgentClient,
  createAgentDataClient,
  type TypedAgentData,
  type TypedAgentDataItems,
  type TypedAggregateGroupItems,
  type SearchAgentDataOptions,
  type AggregateAgentDataOptions,
} from "@llama-cloud-services/beta/agent";
```

### Create client

The helper infers the `deploymentName` from environment variables or the browser URL when possible, defaulting to `"_public"`.

```ts
type Person = { name: string; age: number; email: string };

const client = createAgentDataClient<Person>({
  // Optional: infer agent from env
  env: process.env as Record<string, string>,
  // Optional: infer from browser URL when not localhost
  windowUrl: typeof window !== "undefined" ? window.location.href : undefined,
  // Optional overrides
  // deploymentName: "person-extraction-agent",
  collection: "extracted_people",
});
```

Alternatively, construct a client directly:

```ts
const direct = new AgentClient<Person>({
  // client: default (from SDK) or a custom @hey-api/client-fetch instance
  deploymentName: "person-extraction-agent",
  collection: "extracted_people",
});
```

Browser usage:

- The TypeScript SDK works in the browser. When your app is deployed in LlamaCloud alongside your agent, requests are automatically authenticated.
- In other environments (local dev, custom hosting), provide an API key to the underlying client.
- To scope to a specific project, set `Project-Id` on the client’s headers.

### CRUD operations

```ts
// Create
const created = await client.createItem({
  name: "John",
  age: 30,
  email: "john@example.com",
});

// Get (returns null on 404)
const item = await client.getItem(created.id);

// Update (overwrites data)
const updated = await client.updateItem(created.id, {
  name: "Jane",
  age: 31,
  email: "jane@example.com",
});

// Delete
await client.deleteItem(updated.id);
```

SDK responses are strongly typed and camel‑cased.

- `TypedAgentData<T>` fields: `id`, `deploymentName`, `collection?`, `data`, `createdAt`, `updatedAt`.

### Search

```ts
const options: SearchAgentDataOptions = {
  filter: {
    age: { gte: 21, lt: 65 },
    status: { eq: "active" },
    created_at: { gte: "2024-01-01T00:00:00Z" }, // top-level timestamp
  },
  orderBy: "data.name desc, created_at",
  pageSize: 50,
  offset: 0,
  includeTotal: true, // request on the first page only
};

const results: TypedAgentDataItems<Person> = await client.search(options);
for (const r of results.items) {
  console.log(r.data.name);
}
```

See the [Agent Data Overview](/python/cloud/llamaagents/agent-data-overview#filter-dsl) for more details on filters.

- Filter keys target `data` fields, except `created_at`/`updated_at` which are top-level.
- Sort with comma-separated specs; prefix data fields in `orderBy` (e.g., `"data.name desc, created_at"`).
- Default `pageSize` is 50 (max 1000). Use `includeTotal` only on the first page.

Pagination: The default page size is 50 (max 1000). The response may include `nextPageToken` and `totalSize`.

### Aggregate

```ts
const aggOptions: AggregateAgentDataOptions = {
  filter: { status: { eq: "active" } },
  groupBy: ["department", "role"],
  count: true,
  first: true, // earliest by created_at per group
  orderBy: "data.department asc, data.role asc",
  pageSize: 100,
};

const groups: TypedAggregateGroupItems<Person> =
  await client.aggregate(aggOptions);
for (const g of groups.items) {
  console.log(g.groupKey, g.count, g.firstItem);
}
```
