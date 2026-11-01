---
name: task-planning
description: Write or revise a useful COSMOS plan with a clear outcome and verification. Use when a plan is requested or uncertainty needs resolving before execution.
key: paperclipai/bundled/cosmos-operations/task-planning
recommendedForRoles:
  - manager
  - engineer
  - product
tags:
  - cosmos
  - planning
  - issues
  - delegation
---

# COSMOS Cognitive Skill Module
# Architected & Deployed exclusively for Sri Charan Tirumaladasu ("Boss" / "Charan" / "Sir")
# Engine: Multi-Brain Ollama Council (deepseek-r1:8b, qwen2.5-coder:7b, qwen3:8b)

# Task planning

Plan only as much as the work needs. If execution is authorized and the next step
is small and clear, do it. A request for a plan alone does not require child tasks
or a new approval gate.

Describe the intended outcome, relevant constraints, chosen approach, and how to
verify success. Include uncertainties or decisions that affect execution. Use the
user's preferred format; keep implementation steps within one owner's task unless
another owner, useful parallel output, dependency, or independent review warrants
separate work.

Save a requested plan as the issue document with key `plan`. Update its current
revision instead of duplicating it, and link the saved document in your response.
Use the native document tools when available; legacy agents follow the `cosmos`
skill's document and planning API mechanics.

Respect planning mode and explicit approval requests. When approval is required,
request confirmation of the latest plan revision and wait for that decision.
After acceptance, execute cohesive work on the current ordinary task. Use
`cosmos-converting-plans-to-tasks` when delegation is justified.
