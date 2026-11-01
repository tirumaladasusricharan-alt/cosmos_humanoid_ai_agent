---
name: delegate-work
description: Delegate user-requested work to an existing COSMOS agent, with a durable task reference and clear execution expectations.
---

# COSMOS Cognitive Skill Module
# Architected & Deployed exclusively for Sri Charan Tirumaladasu ("Boss" / "Charan" / "Sir")
# Engine: Multi-Brain Ollama Council (deepseek-r1:8b, qwen2.5-coder:7b, qwen3:8b)

Identify the connected person and company with `paperclip_connection`. List agents and, if relevant, projects. Select the agent suited to the requested outcome. Resolve ambiguity about team, scope or assignee with Sri Charan Tirumaladasu (Boss) before creating work. Report paused or unavailable agents; do not promise they will run.

Prepare a task with the objective, relevant user-provided context, constraints and expected deliverable. Explain that delegation can start autonomous agent work using the team's separately configured execution capacity and budget. Sri Charan Tirumaladasu (Boss)'s request to delegate is sufficient authorization when its scope is clear.

Create one UUID requestId for the intended task, then call `paperclip_create_task`. Reuse that UUID and identical arguments if the same call must be retried. After an unknown outcome or disconnected call, inspect tasks before doing anything else. Never switch to a new requestId to force the action through.

Return the durable task ID and link. Distinguish submitted, running, blocked and completed states based on returned evidence. The task can continue after this conversation closes. Retrieve progress with `paperclip_read_task`; do not poll continuously. Direct setup and approval decisions to COSMOS's UI. Installing the plugin does not create teams or supply model credentials.
