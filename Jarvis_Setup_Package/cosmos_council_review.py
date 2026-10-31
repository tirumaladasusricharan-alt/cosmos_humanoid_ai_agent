"""
cosmos_council_review.py - Multi-Model Ollama Council & Automated Code Review
Architected exclusively for Sri Charan Tirumaladasu ("Boss" / "Sir")

Capabilities:
1. Dynamic routing across locally pulled Ollama models:
   - deepseek-r1:8b (Chief Architect & Logic Strategist)
   - qwen2.5-coder:7b (Master Polyglot Builder)
   - qwen3:8b / qwen2.5-coder:14b / qwen2.5-coder:3b / qwen2.5:latest
2. Council Mode:
   - Phase 1: DeepSeek-R1 formulates algorithm, edge cases, time/space complexity targets.
   - Phase 2: Qwen-Coder implements production-grade polyglot code.
   - Phase 3: Automated syntax validation (ast.parse, json.loads, balanced delimiters)
3. Outputs verified code with spoken summary for Boss.
"""

import ast
import json
import os
import re
import sys
import urllib.request
from typing import Dict, List, Optional, Tuple

OLLAMA_BASE_URL = "http://localhost:11434"

# ═══════════════════════════════════════════════════════════════════════
# 1. MODEL DISCOVERY & INFERENCE
# ═══════════════════════════════════════════════════════════════════════

def get_installed_models() -> List[str]:
    """Retrieves all installed model tags from Ollama."""
    try:
        url = f"{OLLAMA_BASE_URL}/api/tags"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=1.8) as resp:
            data = json.loads(resp.read().decode())
            return [m.get("name", "") for m in data.get("models", [])]
    except Exception:
        return []

def select_council_pair(installed: List[str]) -> Tuple[str, str]:
    """
    Selects the optimal (Architect, Builder) model pair from installed models:
    - Architect: deepseek-r1:8b -> qwen3:8b -> qwen2.5:latest
    - Builder: qwen2.5-coder:7b -> qwen2.5-coder:14b -> qwen2.5-coder:3b -> qwen2.5-coder:latest
    """
    installed_lower = [m.lower() for m in installed]

    architect_priority = ["deepseek-r1:8b", "deepseek-r1", "qwen3:8b", "qwen2.5:latest", "qwen2.5"]
    builder_priority = ["qwen2.5-coder:7b", "qwen2.5-coder:14b", "qwen2.5-coder:latest", "qwen2.5-coder:3b", "qwen2.5-coder:1.5b"]

    architect = None
    builder = None

    for pref in architect_priority:
        for idx, inst in enumerate(installed_lower):
            if pref in inst:
                architect = installed[idx]
                break
        if architect:
            break

    for pref in builder_priority:
        for idx, inst in enumerate(installed_lower):
            if pref in inst:
                builder = installed[idx]
                break
        if builder:
            break

    # Fallbacks if specific models missing
    if not architect and installed:
        architect = installed[0]
    if not builder and installed:
        builder = installed[-1]

    return architect or "deepseek-r1:8b", builder or "qwen2.5-coder:7b"

def query_ollama(model: str, prompt: str, timeout: int = 35) -> Optional[str]:
    """Queries an Ollama model."""
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
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            res_json = json.loads(resp.read().decode())
            return res_json.get("response", "").strip()
    except Exception as e:
        print(f"[COSMOS COUNCIL ERROR ({model})] {e}")
        return None

# ═══════════════════════════════════════════════════════════════════════
# 2. CODE SYNTAX VALIDATION
# ═══════════════════════════════════════════════════════════════════════

def validate_syntax(code: str, lang: str = "python") -> Tuple[bool, str]:
    """Validates code syntax according to language type."""
    l = lang.lower().strip()
    if not code or not code.strip():
        return False, "Code is empty."

    if l in ("python", "py"):
        try:
            ast.parse(code)
            return True, "Valid Python syntax."
        except SyntaxError as e:
            return False, f"Python SyntaxError at line {e.lineno}: {e.msg}"

    if l == "json":
        try:
            json.loads(code)
            return True, "Valid JSON."
        except Exception as e:
            return False, f"Invalid JSON: {e}"

    # Balanced bracket/delimiter stack for C++, Java, JS, TS, Go, Rust, PHP, etc.
    stack = []
    pairs = {')': '(', ']': '[', '}': '{'}
    in_single = False
    in_double = False
    escaped = False

    for ch in code:
        if escaped:
            escaped = False
            continue
        if ch == '\\':
            escaped = True
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            continue
        if in_single or in_double:
            continue

        if ch in pairs.values():
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack[-1] != pairs[ch]:
                return False, f"Mismatched delimiter: '{ch}'."
            stack.pop()

    if stack:
        return False, f"Unclosed delimiters: {''.join(stack)}."
    return True, f"Valid {lang.capitalize()} structure."

# ═══════════════════════════════════════════════════════════════════════
# 3. DUAL-PASS COUNCIL REVIEW EXECUTION
# ═══════════════════════════════════════════════════════════════════════

def run_council_review(query: str) -> str:
    """
    Executes Council Mode:
    - Pass 1 (DeepSeek-R1 Architect): Formulates algorithm & edge cases.
    - Pass 2 (Qwen-Coder Builder): Writes verified polyglot implementation.
    - Pass 3: Syntax check & formatting.
    """
    installed = get_installed_models()
    architect_model, builder_model = select_council_pair(installed)

    print(f"[COSMOS COUNCIL] Architect: {architect_model} | Builder: {builder_model}")

    # Pass 1: Architect Blueprint
    blueprint_prompt = (
        f"You are the Chief Architectural Mind of COSMOS, serving Sri Charan Tirumaladasu ('Boss' / 'Sir').\n"
        f"Analyze this problem thoroughly:\n"
        f"Task: {query}\n\n"
        f"Provide:\n"
        f"1. Core Algorithm Strategy\n"
        f"2. Edge Cases (empty, null, boundary, overflow, concurrency)\n"
        f"3. Time and Space Complexity Target\n"
        f"Be razor-sharp, concise, and structured."
    )
    blueprint = query_ollama(architect_model, blueprint_prompt, timeout=30)
    if not blueprint:
        # Cloud failover if local architect times out
        import cosmos_multi_brain
        blueprint = cosmos_multi_brain.query_groq_failover(blueprint_prompt)

    # Pass 2: Builder Implementation
    builder_prompt = (
        f"You are the Polyglot Builder Engine of COSMOS for Boss Sri Charan Tirumaladasu.\n"
        f"Implement the complete, production-grade code adhering strictly to this blueprint:\n\n"
        f"[ARCHITECTURAL BLUEPRINT]:\n{blueprint or 'Standard production architecture.'}\n\n"
        f"[ORIGINAL TASK]:\n{query}\n\n"
        f"OUTPUT FORMAT (STRICT):\n"
        f"Provide the complete code block in markdown ```<lang> ... ``` first.\n\n"
        f"[ARCHITECTURAL HIGHLIGHTS]:\n"
        f"- Resolution of edge cases and complexity.\n\n"
        f"[SPOKEN_SUMMARY]:\n"
        f"1-2 concise, articulate spoken sentences addressed to 'Boss' or 'sir'."
    )
    solution = query_ollama(builder_model, builder_prompt, timeout=35)
    if not solution:
        import cosmos_multi_brain
        solution = cosmos_multi_brain.query_groq_failover(builder_prompt)

    if not solution:
        import cosmos_autonomous_mind
        return cosmos_autonomous_mind.cosmos_autonomous_solve(query)

    # Pass 3: Syntax verification
    m_code = re.search(r"```([a-zA-Z0-9_\+\#-]*)\n([\s\S]*?)```", solution)
    if m_code:
        lang = m_code.group(1).strip() or "python"
        code = m_code.group(2)
        valid, msg = validate_syntax(code, lang)
        if not valid and lang.lower() in ("python", "py"):
            print(f"[COSMOS COUNCIL] Syntax refinement needed: {msg}")

    return solution

