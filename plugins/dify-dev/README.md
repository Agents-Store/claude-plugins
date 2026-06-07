# dify-dev

Developer plugin for the **Dify API**. Complete, file-based reference and assistant for building integrations against Dify apps — the **App Service API** (chat, completion, workflows, conversations, files, audio, annotations) and the **Knowledge Base / Datasets API** (datasets, documents, segments, tags, retrieve).

All examples are **curl** and work against both Dify Cloud (`https://api.dify.ai/v1`) and self-hosted (`https://{your-host}/v1`).

> For self-hosted Dify *update / Docker operations*, see the companion **`dify-ops`** plugin. `dify-dev` is about calling the API; `dify-ops` is about running the server.

## Skills

| Skill | Description |
|-------|-------------|
| `setup` | Authentication model, base URL (cloud/self-hosted), per-app API keys, the mandatory `user` field, blocking vs streaming response modes, file transfer methods, and app metadata endpoints (`/info`, `/parameters`, `/meta`, `/site`) |
| `chat-completion` | Send messages to chat/agent/chatflow apps (`/chat-messages`) and completion apps (`/completion-messages`); stop generation, suggested questions, message feedback, app feedbacks; SSE event reference |
| `workflows` | Run workflow apps (`/workflows/run`, run-by-id), get run detail, list logs, stop a running task, and chatflow workflow events |
| `conversations` | List / rename / delete conversations, get & update conversation variables, list conversation messages |
| `files-audio` | Upload & preview files for multimodal input, speech-to-text (`/audio-to-text`), text-to-speech (`/text-to-audio`) |
| `annotations` | Manage annotations (list/create/update/delete) and annotation-reply settings (enable/disable/status) |
| `knowledge-base` | Datasets, documents, segments/chunks, tags, metadata, and retrieval testing for the standalone Knowledge Base / Datasets API |
| `examples` | End-to-end curl walkthroughs — chatbot integration, running a workflow, and a knowledge-base RAG pipeline |
| `troubleshoot` | HTTP/error codes, rate-limit headers, blocking-mode timeout, conversation isolation, `user` mismatch, and file-transfer pitfalls |

## Agent

**dify-developer** — Builds and debugs integrations against the Dify API. Writes client code, diagnoses API errors, and routes to the right skill for each endpoint group.

## Commands

| Command | Description |
|---------|-------------|
| `/dify-dev:api [endpoint-or-keyword]` | Look up any Dify endpoint — HTTP method, path, parameters, response shape, and a ready curl example |
| `/dify-dev:generate-client` | Generate copy-paste curl scripts for a chosen operation (chat, completion, workflow run, file upload, KB ingest/retrieve) |
| `/dify-dev:quickstart` | Guided walkthrough — find your app API key, determine the base URL, send a first test call, verify the response |

## Installation

Install via Agents Store, or add this plugin directory to your Claude Code plugins.

## Prerequisites

- A Dify app (Chatbot, Agent, Chatflow, Workflow, or Completion) — or a Knowledge Base — in Dify Cloud or a self-hosted instance.
- The app's **API key** (Dify Studio → your app → **API Access** → API Key). Knowledge Base operations use a **Knowledge API key** (Knowledge → API).
- The **base URL**: `https://api.dify.ai/v1` for Cloud, or `https://{your-host}/v1` for self-hosted.
