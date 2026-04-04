---
name: examples
description: "This skill should be used when learning how to deploy apps, provision databases, or set up Docker Compose stacks on Dokploy. Provides end-to-end workflow walkthroughs. Triggers: \"dokploy example\", \"how to deploy on dokploy\", \"dokploy tutorial\", \"dokploy walkthrough\", \"show me how to use dokploy\"."
---

# Dokploy Examples

Step-by-step walkthroughs covering the three most common Dokploy workflows. Each scenario uses MCP tools as the primary method, with equivalent curl commands shown alongside.

---

## Scenario 1: Deploy a Web Application

Deploy a web app from a GitHub repository to a running application with a custom domain and HTTPS.

Covers: project creation, application setup, GitHub integration, environment variables, domain configuration, and deployment.

See full walkthrough: [references/deploy-app.md](references/deploy-app.md)

---

## Scenario 2: Provision a Database

Create, configure, and expose a PostgreSQL database with external access and automated backups.

Covers: database creation, deployment, external port configuration, connection string construction, and backup scheduling.

See full walkthrough: [references/provision-database.md](references/provision-database.md)

---

## Scenario 3: Deploy a Docker Compose Stack

Deploy a multi-container application using a docker-compose.yml file with service-level domain routing.

Covers: compose service creation, compose file content, environment variables, deployment, and per-service domain assignment.

See full walkthrough: [references/compose-stack.md](references/compose-stack.md)
