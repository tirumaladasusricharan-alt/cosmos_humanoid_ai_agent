---
name: ruflo-arena
description: Competitive multi-model tournament evaluating candidates on syntax validity, completeness, and latency to serve the winning solution.
tags:
  - arena
  - tournament
  - multi-model
  - competitive
---

# Ruflo Arena Multi-Model Tournament
# Creator: Sri Charan Tirumaladasu

Dispatches queries across dual models (Groq vs Ollama `qwen2.5-coder:7b` / `deepseek-r1:8b`).
Scores outputs based on AST syntax validity, completeness, and latency, returning the winning response.
