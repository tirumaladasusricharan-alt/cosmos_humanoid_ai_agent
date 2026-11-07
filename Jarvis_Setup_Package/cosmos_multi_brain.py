"""
cosmos_multi_brain.py - Multi-Model Local Brain & Council Mode for COSMOS
Architected exclusively for Sri Charan Tirumaladasu ("Boss" / "Sir")

Capabilities:
1. Dynamic detection of all locally pulled Ollama models:
   - deepseek-r1:8b (Deep Logical Reasoning & Architectural Blueprints)
   - qwen2.5-coder:7b (High-Precision Polyglot Code Generation)
   - qwen2.5-coder:3b & qwen2.5-coder:latest (Fast Polyglot Coders)
   - qwen2.5:latest (General Purpose Agent Reasoning)
   - qwen3:8b / qwen2.5-coder:1.5b
2. Council Mode (DeepSeek-R1 Blueprint + Qwen-Coder Implementation):
   - Pass 1: DeepSeek-R1 formulates algorithm, edge cases, time/space complexity.
   - Pass 2: Qwen-Coder generates production-grade, verified polyglot implementation.
3. Automatic Cloud AI Failover (Groq) if local models are offline or slow.
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Tuple

OLLAMA_BASE_URL = "http://localhost:11434"

# ═══════════════════════════════════════════════════════════════════════
# 1. MODEL DISCOVERY & SELECTION
# ═══════════════════════════════════════════════════════════════════════

def get_installed_ollama_models() -> List[str]:
    """Retrieves all installed model tags from the local Ollama instance."""
    try:
        url = f"{OLLAMA_BASE_URL}/api/tags"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            data = json.loads(resp.read().decode())
            return [m.get("name", "") for m in data.get("models", [])]
    except Exception:
        return []

def select_best_model_for_task(task_type: str, installed: List[str]) -> Optional[str]:
    """
    Selects the optimal local model based on task type:
    - 'coding': prefers qwen2.5-coder:7b -> qwen2.5-coder:latest -> qwen2.5-coder:3b -> deepseek-r1:8b
    - 'reasoning': prefers deepseek-r1:8b -> qwen3:8b -> qwen2.5:latest -> qwen2.5-coder:7b
    - 'fast': prefers qwen2.5-coder:3b -> qwen2.5-coder:1.5b
    """
    installed_lower = [m.lower() for m in installed]

    if task_type == "coding":
        priority = [
            "qwen2.5-coder:7b",
            "qwen2.5-coder:latest",
            "qwen2.5-coder:3b",
            "deepseek-r1:8b",
            "qwen2.5:latest",
            "qwen2.5-coder:1.5b"
        ]
    elif task_type == "reasoning":
        priority = [
            "deepseek-r1:8b",
            "deepseek-r1",
            "qwen3:8b",
            "qwen2.5:latest",
            "qwen2.5-coder:7b",
            "qwen2.5-coder:3b"
        ]
    else:
        priority = [
            "deepseek-r1:8b",
            "qwen2.5-coder:7b",
            "qwen2.5:latest",
            "qwen2.5-coder:3b",
            "qwen2.5-coder:latest"
        ]

    for pref in priority:
        for idx, inst in enumerate(installed_lower):
            if pref in inst:
                return installed[idx]

    return installed[0] if installed else None

# ═══════════════════════════════════════════════════════════════════════
# 2. LOCAL OLLAMA INFERENCE & GROQ FAILOVER
# ═══════════════════════════════════════════════════════════════════════

_ollama_cooldown_until = 0.0

def query_ollama(model: str, prompt: str, timeout: float = 1.8, system_prompt: str = "") -> Optional[str]:
    """Queries a specific local Ollama model with fast failover."""
    global _ollama_cooldown_until
    if time.time() < _ollama_cooldown_until:
        return None
    try:
        url = f"{OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.25,
                "num_ctx": 4096
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            res_json = json.loads(resp.read().decode())
            return res_json.get("response", "").strip()
    except Exception as e:
        _ollama_cooldown_until = time.time() + 60.0
        print(f"[COSMOS MULTI-BRAIN] Ollama ({model}) error: {e}. Fast failover to Groq cloud for 60s.")
        return None

def query_groq_failover(prompt: str, system_prompt: str = "") -> Optional[str]:
    """Cloud AI failover using existing Groq client."""
    try:
        import jarvis_brain
        from openai import OpenAI
        key = jarvis_brain._get_api_key()
        if not key:
            return None
        client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
        for model in jarvis_brain.MODELS:
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt or (
                                "You are COSMOS, the autonomous OS-level intelligence built by Sri Charan Tirumaladasu ('Boss' / 'Sir'). "
                                "Provide rigorous solutions, clear code, and concise spoken summaries."
                            )
                        },
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1800,
                    temperature=0.3
                )
                raw = resp.choices[0].message.content or ""
                if not raw.strip() and hasattr(resp.choices[0].message, "reasoning"):
                    raw = getattr(resp.choices[0].message, "reasoning") or ""
                if raw.strip():
                    return raw.strip()
            except Exception:
                continue
    except Exception as e:
        print(f"[COSMOS MULTI-BRAIN] Groq failover error: {e}")
    return None

# ═══════════════════════════════════════════════════════════════════════
# 3. COUNCIL MODE (DEEPSEEK REASONING + QWEN-CODER IMPLEMENTATION)
# ═══════════════════════════════════════════════════════════════════════

def is_complex_architectural_task(query: str) -> bool:
    """Detects whether a query warrants dual-model Council Mode."""
    q = query.lower()
    triggers = (
        "architecture", "architectural", "system design", "council", "dual model",
        "complex", "multi-step", "full stack", "data structure", "concurrency",
        "multithreading", "distributed", "optimize", "refactor whole", "microservice",
        "database schema", "compiler", "parser", "websocket server"
    )
    return any(t in q for t in triggers)

def run_council_mode(query: str, installed_models: List[str]) -> str:
    """
    Executes Council Mode:
    - Pass 1 (DeepSeek-R1:8b): Deep logical analysis, architectural blueprint, edge cases.
    - Pass 2 (Qwen2.5-Coder:7b): Production-grade code generation adhering to the blueprint.
    """
    print("[COSMOS COUNCIL MODE] Activating Dual-Brain Reasoning (DeepSeek + Qwen-Coder)...")
    deepseek_model = select_best_model_for_task("reasoning", installed_models) or "deepseek-r1:8b"
    coder_model = select_best_model_for_task("coding", installed_models) or "qwen2.5-coder:7b"

    # Pass 1: DeepSeek Blueprint
    pass1_prompt = (
        f"You are the Chief Architectural Mind of COSMOS, serving Sri Charan Tirumaladasu ('Boss' / 'Sir').\n"
        f"Analyze this task thoroughly:\n"
        f"Task: {query}\n\n"
        f"Provide:\n"
        f"1. Core Architectural Strategy & Algorithm\n"
        f"2. Critical Edge Cases (null, empty, boundary, overflow, concurrency)\n"
        f"3. Time & Space Complexity Target\n"
        f"Be precise, concise, and technical."
    )
    blueprint = query_ollama(deepseek_model, pass1_prompt, timeout=1.8)
    if not blueprint:
        blueprint = query_groq_failover(pass1_prompt)

    # Pass 2: Qwen Coder Implementation
    pass2_prompt = (
        f"You are the Polyglot Implementation Engine of COSMOS for Boss Sri Charan Tirumaladasu.\n"
        f"Implement the complete, production-grade code adhering strictly to this architectural blueprint:\n\n"
        f"[ARCHITECTURAL BLUEPRINT]:\n{blueprint or 'Standard best-practice architecture.'}\n\n"
        f"[ORIGINAL TASK]:\n{query}\n\n"
        f"OUTPUT FORMAT (STRICT):\n"
        f"Provide the complete verified code block in markdown ```<language> ... ``` first.\n\n"
        f"[ARCHITECTURAL HIGHLIGHTS]:\n"
        f"- 2-3 bullet points on how edge cases and complexity were resolved.\n\n"
        f"[SPOKEN_SUMMARY]:\n"
        f"1-2 concise, articulate sentences addressed to 'Boss' or 'sir' summarizing the resolution."
    )
    code_solution = query_ollama(coder_model, pass2_prompt, timeout=1.8)
    if not code_solution:
        code_solution = query_groq_failover(pass2_prompt)

    if code_solution:
        return code_solution

    # Fallback to single-pass if council pipeline fails
    return cosmos_multi_model_solve(query)

# ═══════════════════════════════════════════════════════════════════════
# 4. MAIN MULTI-MODEL SOLVER
# ═══════════════════════════════════════════════════════════════════════

def cosmos_multi_model_solve(user_input: str) -> str:
    """
    Main entry point for multi-model solving:
    - Routes to Council Mode if complex/architectural
    - Routes to Qwen-Coder for standard coding
    - Routes to DeepSeek-R1 for logic & problem solving
    - Seamlessly falls back across installed models and Groq
    """
    installed = get_installed_ollama_models()

    # Council Mode check
    if is_complex_architectural_task(user_input) and len(installed) >= 2:
        return run_council_mode(user_input, installed)

    q = user_input.lower()
    is_coding = any(
        w in q
        for w in ("code", "function", "script", "algorithm", "debug", "python", "javascript", "class", "fix", "write")
    )
    task_type = "coding" if is_coding else "reasoning"

    # Select primary and secondary models
    primary_model = select_best_model_for_task(task_type, installed)
    ordered_models = []
    if primary_model:
        ordered_models.append(primary_model)
    for m in installed:
        if m not in ordered_models:
            ordered_models.append(m)

    system_prompt = (
        "You are COSMOS, the autonomous OS-level intelligence built by Sri Charan Tirumaladasu ('Boss' / 'Sir'). "
        "Provide elegant, production-grade solutions. If code is requested, enclose the complete code in markdown ```<lang> ... ``` first, "
        "followed by a logical breakdown, and conclude with [SPOKEN_SUMMARY]: 1-2 articulate spoken sentences addressed to 'Boss' or 'sir'."
    )

    full_prompt = (
        f"[TASK / QUERY]:\n{user_input}\n\n"
        f"Solve the problem thoroughly adhering to the required format."
    )

    # Try the best local model with a fast 1.8s timeout; failover instantly if slow or cold
    for model in ordered_models[:1]:
        print(f"[COSMOS MULTI-BRAIN] Querying local model: {model}")
        res = query_ollama(model, full_prompt, timeout=1.8, system_prompt=system_prompt)
        if res and len(res.strip()) > 30:
            return res
        break

    # Failover to cloud Groq
    print("[COSMOS MULTI-BRAIN] Falling back to Groq cloud failover...")
    groq_res = query_groq_failover(full_prompt, system_prompt=system_prompt)
    if groq_res:
        return groq_res

    # Final fallback to autonomous mind
    try:
        import cosmos_autonomous_mind
        return cosmos_autonomous_mind.cosmos_autonomous_solve(user_input)
    except Exception as e:
        return f"Boss, I encountered an error across all neural models: {e}"

