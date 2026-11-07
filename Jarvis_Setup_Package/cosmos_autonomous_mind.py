"""
cosmos_autonomous_mind.py - Autonomous Logical Thinking, ReAct Loop & Self-Reflection Engine for COSMOS
Architected & Exclusively Deployed for Sri Charan Tirumaladasu ("Boss" or "Sir")

Provides 100% additive capabilities:
1. Autonomous ReAct Decision Loop (Think -> Gather Context -> Solve -> Critique)
   - Auto-reads Windows clipboard if relevant
   - Auto-reads local file paths if referenced
   - Auto-searches web / fetches docs via cosmos_free_search on initiative
2. Chain-of-Thought Internal Monologue & Polyglot Coding
   - Local Ollama reasoning (qwen2.5-coder / qwen2.5 / deepseek-r1 / qwen3) with Groq cloud fallback
   - Edge case analysis, time/space complexity, and architecture planning
3. Autonomous Self-Reflection & Critique Pass
   - Syntax validation (ast.parse for Python, json.loads for JSON, delimiter balance for polyglot)
   - Self-critique check against user goals with autonomous self-refinement
4. Local Episodic Lesson Memory (cosmos_brain_memory.json)
   - Retains problem-solving lessons and injects relevant prior insights
5. Voice vs. Visual Separation
   - Displays full reasoning and code in UI/console, speaks ONLY the clean 1-2 sentence SPOKEN_SUMMARY
"""

import os
import sys

# Safeguard stdout/stderr for background pythonw.exe execution
if sys.stdout is None:
    try:
        sys.stdout = open(os.devnull, "w")
    except Exception:
        pass
if sys.stderr is None:
    try:
        sys.stderr = open(os.devnull, "w")
    except Exception:
        pass

import ast
import json
import re
import time
import datetime
import urllib.parse
import urllib.request
import ctypes
from ctypes import wintypes
from typing import Dict, Any, List, Optional, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(SCRIPT_DIR, "cosmos_brain_memory.json")
OLLAMA_BASE_URL = "http://localhost:11434"

# ═══════════════════════════════════════════════════════════════════════
# 1. VOICE-FIRST INTERFACE
# ═══════════════════════════════════════════════════════════════════════
def cosmos_speak(text: str):
    """Speaks clean text strictly via COSMOS female Edge-TTS."""
    try:
        from cosmos_human_voice import cosmos_speak as _cs
        _cs(text)
    except Exception as e:
        print(f"[COSMOS AUTONOMOUS VOICE ERROR] {e}")


# ═══════════════════════════════════════════════════════════════════════
# 2. WINDOWS CLIPBOARD CONTEXT GATHERER (Zero Dependency ctypes)
# ═══════════════════════════════════════════════════════════════════════
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

user32.OpenClipboard.argtypes = [wintypes.HWND]
user32.OpenClipboard.restype = wintypes.BOOL
user32.CloseClipboard.restype = wintypes.BOOL
user32.GetClipboardData.argtypes = [wintypes.UINT]
user32.GetClipboardData.restype = wintypes.HANDLE
kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalUnlock.restype = wintypes.BOOL

CF_UNICODETEXT = 13

def get_clipboard_content() -> str:
    """Safely extracts text currently held in the Windows clipboard."""
    if not user32.OpenClipboard(None):
        return ""
    try:
        h_clip = user32.GetClipboardData(CF_UNICODETEXT)
        if not h_clip:
            return ""
        p_text = kernel32.GlobalLock(h_clip)
        if not p_text:
            return ""
        try:
            return ctypes.c_wchar_p(p_text).value or ""
        finally:
            kernel32.GlobalUnlock(h_clip)
    except Exception:
        return ""
    finally:
        user32.CloseClipboard()


# ═══════════════════════════════════════════════════════════════════════
# 3. EPISODIC LESSON MEMORY (cosmos_brain_memory.json)
# ═══════════════════════════════════════════════════════════════════════
def load_episodic_memory() -> List[Dict[str, Any]]:
    """Loads past problem-solving lessons from local disk."""
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_episodic_lesson(query: str, lesson: str, keywords: List[str]):
    """Stores a concise takeaway from a solved problem into local memory."""
    if not lesson or not lesson.strip():
        return
    memories = load_episodic_memory()
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "query": query.strip(),
        "lesson": lesson.strip(),
        "keywords": [k.lower().strip() for k in keywords if len(k) > 2]
    }
    # Keep up to 60 most relevant recent lessons
    memories.append(entry)
    if len(memories) > 60:
        memories = memories[-60:]
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memories, f, indent=2)
    except Exception as e:
        print(f"[COSMOS MEMORY WRITE ERROR] {e}")

def retrieve_relevant_lessons(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Finds past lessons relevant to the current query."""
    memories = load_episodic_memory()
    if not memories:
        return []
    q_words = set(re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", query.lower()))
    scored = []
    for m in memories:
        m_keywords = set(m.get("keywords", []))
        overlap = len(q_words & m_keywords)
        if overlap > 0:
            scored.append((overlap, m))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:limit]]


# ═══════════════════════════════════════════════════════════════════════
# 4. AUTONOMOUS CONTEXT EVALUATOR & GATHERER
# ═══════════════════════════════════════════════════════════════════════
def gather_autonomous_context(query: str) -> Dict[str, Any]:
    """
    Evaluates what context is missing and autonomously fetches it:
    - Clipboard text if mentioned or relevant
    - Local file content if path is referenced
    - Web search/documentation if live facts or library updates needed
    """
    q_lower = query.lower()
    context = {
        "clipboard": None,
        "files": {},
        "web_research": []
    }

    # 1. Explicit Clipboard Check only when specifically requested
    clipboard_triggers = ("clipboard", "from clipboard", "in clipboard", "copied code")
    if any(t in q_lower for t in clipboard_triggers):
        clip_text = get_clipboard_content().strip()
        if clip_text and len(clip_text) > 10:
            context["clipboard"] = clip_text[:8000]

    # 2. Local File Reference Check
    file_pattern = r"(?:[a-zA-Z]:\\[^\s\"<>|]+|\b[\w\.-]+\.(?:py|js|ts|json|txt|html|css|md|cpp|c|java|sql|bat|ps1|sh)\b)"
    file_matches = re.findall(file_pattern, query)
    for fm in file_matches:
        candidate = fm.strip("\"'.,; ")
        # Try absolute or relative path
        target_path = candidate if os.path.isabs(candidate) else os.path.join(SCRIPT_DIR, candidate)
        if os.path.exists(target_path) and os.path.isfile(target_path):
            try:
                with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                    context["files"][candidate] = f.read(8000)
            except Exception as e:
                print(f"[COSMOS FILE READ ERROR] {e}")

    # 3. Live Web Facts / Documentation Search Check
    research_triggers = ("latest", "docs", "documentation", "version", "library", "framework", "api", "recent", "how to install", "release", "rfc")
    if any(t in q_lower for t in research_triggers):
        try:
            import cosmos_free_search
            snippets = cosmos_free_search.cosmos_live_web_search(query, max_results=3)
            if snippets:
                context["web_research"] = snippets
        except Exception as e:
            print(f"[COSMOS AUTONOMOUS WEB SEARCH ERROR] {e}")

    return context


# ═══════════════════════════════════════════════════════════════════════
# 5. CODE SYNTAX VALIDATION & DELIMITER CHECK
# ═══════════════════════════════════════════════════════════════════════
def check_syntax(code: str, language: str) -> Tuple[bool, str]:
    """
    Verifies code syntax validity:
    - Python: ast.parse
    - JSON: json.loads
    - Polyglot (JS/TS/C++/Java/PHP/SQL): balanced delimiters check
    """
    lang = language.lower().strip()
    if not code or not code.strip():
        return True, "Empty code"

    # Python
    if lang in ("python", "py"):
        try:
            ast.parse(code)
            return True, "Valid Python syntax"
        except SyntaxError as e:
            return False, f"Python SyntaxError at line {e.lineno}: {e.msg}"

    # JSON
    if lang == "json":
        try:
            json.loads(code)
            return True, "Valid JSON"
        except Exception as e:
            return False, f"JSON SyntaxError: {e}"

    # Balanced Delimiters Check for JS, TS, C++, Java, Go, Rust, PHP, SQL
    stack = []
    pairs = {')': '(', '}': '{', ']': '['}
    in_single_quote = False
    in_double_quote = False
    in_backtick = False
    escape = False

    for idx, char in enumerate(code):
        if escape:
            escape = False
            continue
        if char == '\\':
            escape = True
            continue
        if char == "'" and not in_double_quote and not in_backtick:
            in_single_quote = not in_single_quote
            continue
        if char == '"' and not in_single_quote and not in_backtick:
            in_double_quote = not in_double_quote
            continue
        if char == '`' and not in_single_quote and not in_double_quote:
            in_backtick = not in_backtick
            continue
        if in_single_quote or in_double_quote or in_backtick:
            continue

        if char in '({[':
            stack.append((char, idx))
        elif char in ')}]':
            if not stack:
                return False, f"Unmatched closing delimiter '{char}' at position {idx}"
            open_char, open_idx = stack.pop()
            if pairs[char] != open_char:
                return False, f"Mismatched delimiter: expected closing for '{open_char}' (pos {open_idx}), got '{char}' (pos {idx})"

    if stack:
        open_char, open_idx = stack[-1]
        return False, f"Unclosed delimiter '{open_char}' opened at position {open_idx}"

    return True, "Valid delimiter structure"


# ═══════════════════════════════════════════════════════════════════════
# 6. LOCAL OLLAMA REASONING ENGINE WITH GROQ FAILOVER
# ═══════════════════════════════════════════════════════════════════════
def normalize_text_for_output(text: str) -> str:
    """Normalizes unicode whitespace, arrows, quotes, and hyphens for console, UI, and TTS stability."""
    if not text:
        return ""
    replacements = {
        '\u202f': ' ', '\u00a0': ' ',
        '\u2011': '-', '\u2013': '-', '\u2014': '--',
        '\u2018': "'", '\u2019': "'",
        '\u201c': '"', '\u201d': '"',
        '\u2192': '->', '\u2190': '<-',
        '\u2022': '-', '\u2026': '...',
        '\u200b': '', '\ufeff': '',
        '\u2713': '[PASS]', '\u2714': '[PASS]', '\u2717': '[FAIL]',
        '\u2726': '*', '\u2727': '*',
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    try:
        text.encode('cp1252')
    except UnicodeEncodeError:
        text = text.encode('ascii', 'ignore').decode('ascii')
    return text

def get_available_ollama_models(prompt: str = "") -> List[str]:
    """
    Detects all available models in local Ollama instance and orders them
    intelligently based on task requirements (coding vs deep reasoning).
    """
    try:
        url = f"{OLLAMA_BASE_URL}/api/tags"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            data = json.loads(resp.read().decode())
            installed = [m.get("name", "") for m in data.get("models", [])]
            if not installed:
                return []

            # Determine task context to prioritize specialized models
            is_pure_code = any(
                w in prompt.lower()
                for w in ("code", "function", "script", "algorithm", "debug", "python", "javascript", "implement", "class")
            )

            if is_pure_code:
                # Prioritize coding-specialized models first, then deep reasoning
                preferred = [
                    "qwen2.5-coder:7b",
                    "deepseek-r1:8b",
                    "deepseek-r1",
                    "qwen2.5-coder:latest",
                    "qwen2.5-coder:3b",
                    "qwen2.5:latest",
                    "qwen2.5",
                    "qwen2.5-coder:1.5b"
                ]
            else:
                # Prioritize deep reasoning first, then coder models
                preferred = [
                    "deepseek-r1:8b",
                    "deepseek-r1",
                    "qwen2.5-coder:7b",
                    "qwen2.5:latest",
                    "qwen2.5-coder:latest",
                    "qwen2.5-coder:3b",
                    "qwen2.5",
                    "qwen2.5-coder:1.5b"
                ]

            ordered = []
            for pref in preferred:
                for inst in installed:
                    if pref in inst.lower() and inst not in ordered:
                        ordered.append(inst)

            # Include any other installed models not explicitly in preferred list
            for inst in installed:
                if inst not in ordered:
                    ordered.append(inst)

            return ordered
    except Exception:
        pass
    return []

def get_available_ollama_model(prompt: str = "") -> Optional[str]:
    """Returns the top available model for backward compatibility."""
    models = get_available_ollama_models(prompt)
    return models[0] if models else None

_mind_ollama_cooldown = 0.0

def query_ollama(model: str, prompt: str, timeout: float = 2.0) -> Optional[str]:
    """Generates completion using local Ollama model with fast failover."""
    global _mind_ollama_cooldown
    if time.time() < _mind_ollama_cooldown:
        return None
    try:
        url = f"{OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_ctx": 4096
            }
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            res_json = json.loads(resp.read().decode())
            return res_json.get("response", "").strip()
    except Exception as e:
        _mind_ollama_cooldown = time.time() + 60.0
        print(f"[COSMOS OLLAMA GENERATE ERROR ({model})] {e}. Fast failing over to Groq for 60s.")
    return None

def query_groq_failover(prompt: str) -> Optional[str]:
    """High-speed cloud AI reasoning failover using existing Groq client."""
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
                            "content": (
                                "You are COSMOS, elite autonomous intelligence architected exclusively for Sri Charan Tirumaladasu ('Boss'). "
                                "Engage in deep, logical reasoning, multi-step planning, and rigorous edge-case analysis."
                            )
                        },
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1500,
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
        print(f"[COSMOS GROQ FAILOVER ERROR] {e}")
    return None

def generate_reasoning(prompt: str) -> str:
    """Executes prompt on local Ollama across installed models, falling back to Groq if local engine is slow or offline."""
    models_to_try = get_available_ollama_models(prompt)
    for model in models_to_try[:1]:
        print(f"[COSMOS MIND] Generating solution with local model: {model}")
        ollama_reply = query_ollama(model, prompt, timeout=2.0)
        if ollama_reply and len(ollama_reply.strip()) > 20:
            return ollama_reply
        break

    # Seamless fast failover to Groq
    print("[COSMOS MIND] Local Ollama models offline/timed out, invoking fast Groq failover...")
    groq_reply = query_groq_failover(prompt)
    if groq_reply:
        return groq_reply

    return "COSMOS reasoning engine could not connect to local Ollama or cloud failover."


# ═══════════════════════════════════════════════════════════════════════
# 7. PARSING & EXTRACTION HELPERS
# ═══════════════════════════════════════════════════════════════════════
def extract_code_blocks(text: str) -> List[Tuple[str, str]]:
    """Extracts all (language, code) blocks from markdown text."""
    pattern = r"```([a-zA-Z0-9_\+\#-]*)\n([\s\S]*?)```"
    matches = re.findall(pattern, text)
    results = []
    for lang, code in matches:
        clean_lang = lang.strip().lower() or "text"
        results.append((clean_lang, code.strip()))
    return results

def extract_spoken_summary(text: str) -> str:
    """Extracts clean 1-2 sentence spoken summary for voice output."""
    m = re.search(r"(?:\[SPOKEN_SUMMARY\]|\*\*\[SPOKEN_SUMMARY\]:\*\*|SPOKEN_SUMMARY:)\s*(.*?)(?=\n\s*\[|\Z)", text, re.IGNORECASE | re.DOTALL)
    if m:
        summary = m.group(1).strip()
        summary = re.sub(r"```[\s\S]*?```", "", summary)
        summary = re.sub(r"[\*\_#`]", "", summary)
        lines = [line.strip() for line in summary.split("\n") if line.strip()]
        if lines:
            # Join up to 2 sentences
            full_text = " ".join(lines)
            sents = re.split(r"(?<=[.!?])\s+", full_text)
            return " ".join(sents[:2]).strip()

    # Fallback to first clean sentence
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    clean_sents = [s for s in sentences if not s.startswith("[") and not s.startswith("`") and len(s) > 10]
    if clean_sents:
        return re.sub(r"[\*\_#`]", "", clean_sents[0]).strip()
    return "Sir, I have analyzed the problem and formulated the verified solution."


# ═══════════════════════════════════════════════════════════════════════
# 8. THE AUTONOMOUS REACT & SELF-REFLECTION PIPELINE
# ═══════════════════════════════════════════════════════════════════════
def cosmos_autonomous_solve(query: str) -> str:
    """
    Main Autonomous ReAct Execution Pipeline:
    1. Gather Context (Clipboard, Files, Web)
    2. Inject Relevant Episodic Lessons
    3. Generate Chain-of-Thought & Polyglot Solution
    4. Autonomous Self-Reflection & Critique Pass (Syntax & Edge cases)
    5. Save Epistemic Lesson
    6. Return Visual Output + Trigger Spoken Summary
    """
    # ── Step 1: Context Gathering ─────────────────────────────────────
    context = gather_autonomous_context(query)
    context_sections = []

    if context.get("clipboard"):
        context_sections.append(f"[WINDOWS CLIPBOARD DATA]:\n{context['clipboard']}")

    for file_name, file_content in context.get("files", {}).items():
        context_sections.append(f"[LOCAL FILE: {file_name}]:\n{file_content}")

    if context.get("web_research"):
        web_str = "\n".join(f"- {r['title']}: {r['snippet']}" for r in context["web_research"])
        context_sections.append(f"[LIVE WEB GROUND TRUTH]:\n{web_str}")

    gathered_context_str = "\n\n".join(context_sections) if context_sections else "None required."

    # ── Step 2: Episodic Lesson Retrieval ─────────────────────────────
    relevant_lessons = retrieve_relevant_lessons(query, limit=2)
    memory_str = ""
    if relevant_lessons:
        items = "\n".join(f"- Prior Lesson: {m['lesson']}" for m in relevant_lessons)
        memory_str = f"\n[RELEVANT LESSONS LEARNED IN PAST SESSIONS]:\n{items}\n"

    # ── Step 3: Chain-of-Thought Generation Prompt ────────────────────
    system_directive = (
        "You are COSMOS, the autonomous executive intelligence architected by Sri Charan Tirumaladasu ('Boss' / 'Sir'). "
        "Solve the requested problem using rigorous logical thinking, multi-step planning, and polyglot coding.\n\n"
        "OUTPUT FORMAT SPECIFICATION (STRICT):\n"
        "[VERIFIED CODE]:\n"
        "Provide the complete, elegant, production-grade code block enclosed in markdown ```<lang> ... ``` first.\n\n"
        "[REASONING & LOGICAL BREAKDOWN]:\n"
        "- Objective & Edge Cases Analyzed (empty, null, off-by-one, overflow, invalid input)\n"
        "- Time & Space Complexity Analysis\n"
        "- Architectural Strategy\n\n"
        "[SPOKEN_SUMMARY]:\n"
        "Provide exactly 1-2 concise, articulate spoken sentences addressed to 'sir' or 'Boss' summarizing the result."
    )

    full_prompt = (
        f"{system_directive}\n\n"
        f"{memory_str}"
        f"[USER QUERY / TASK]:\n{query}\n\n"
        f"[AUTONOMOUSLY GATHERED CONTEXT]:\n{gathered_context_str}\n\n"
        "Now execute your deep logical thinking and produce the structured response:"
    )

    draft_solution = generate_reasoning(full_prompt)

    # ── Step 4: Autonomous Self-Reflection & Critique Pass ─────────────
    code_blocks = extract_code_blocks(draft_solution)
    syntax_issues = []

    for lang, code in code_blocks:
        valid, msg = check_syntax(code, lang)
        if not valid:
            syntax_issues.append((lang, msg))

    # If syntax or structural issues detected, autonomously refine
    if syntax_issues:
        issue_desc = "; ".join(f"{lang} ({msg})" for lang, msg in syntax_issues)
        refinement_prompt = (
            f"You previously generated a draft solution, but an automated syntax verification detected flaws:\n"
            f"{issue_desc}\n\n"
            f"Original Task: {query}\n\n"
            f"Autonomously critique your code, fix all syntax errors and edge cases, and produce the corrected response adhering strictly to the required format:\n"
            f"[THOUGHT PROCESS]\n[VERIFIED SOLUTION]\n[SPOKEN_SUMMARY]"
        )
        refined_solution = generate_reasoning(refinement_prompt)
        if refined_solution and len(refined_solution) > 50:
            draft_solution = refined_solution

    # ── Step 5: Voice vs. Visual Separation ───────────────────────────
    spoken_summary = extract_spoken_summary(draft_solution)

    # ── Step 6: Save Epistemic Lesson to Memory ───────────────────────
    try:
        clean_words = [w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", query) if w.lower() not in ("the", "and", "for", "with", "this", "that")]
        lesson_text = ""
        m_lesson = re.search(r"(?:Prior Lesson:?|Takeaway:?|Architectural Strategy:?)\s*([^\n]+)", draft_solution, re.IGNORECASE)
        if m_lesson:
            lesson_text = re.sub(r"[\*\_#`]", "", m_lesson.group(1)).strip()
        if not lesson_text or len(lesson_text) < 10:
            lesson_text = re.sub(r"[\*\_#`]", "", spoken_summary).strip()
        if not lesson_text:
            lesson_text = f"Verified {query[:45]} with rigorous edge case analysis."
        save_episodic_lesson(query, lesson_text, clean_words[:6])
    except Exception as e:
        print(f"[COSMOS MEMORY LOG ERROR] {e}")

    # Strip any leaked prompt echo sections
    draft_solution = re.sub(r"\[RELEVANT LESSONS LEARNED IN PAST SESSIONS\]:[\s\S]*?(?=\n\n|\Z)", "", draft_solution, flags=re.IGNORECASE)
    draft_solution = re.sub(r"\[AUTONOMOUSLY GATHERED CONTEXT\]:[\s\S]*?(?=\n\n|\Z)", "", draft_solution, flags=re.IGNORECASE)
    draft_solution = re.sub(r"\[USER QUERY / TASK\]:[\s\S]*?(?=\n\n|\Z)", "", draft_solution, flags=re.IGNORECASE)
    draft_solution = re.sub(r"^\s*\[VERIFIED (?:CODE|SOLUTION)\]:?\s*", "", draft_solution, flags=re.IGNORECASE).strip()

    # Ensure format tags exist cleanly without duplicating
    if not re.search(r"\[SPOKEN_SUMMARY\]", draft_solution, re.IGNORECASE):
        draft_solution += f"\n\n[SPOKEN_SUMMARY]:\n{spoken_summary}"

    return normalize_text_for_output(draft_solution)


# ═══════════════════════════════════════════════════════════════════════
# 9. TRIGGER DETECTION FOR COMMAND ROUTING
# ═══════════════════════════════════════════════════════════════════════
def should_trigger_autonomous_mind(q_clean: str, q_raw: str = "") -> bool:
    """
    Determines whether a query is a complex logical problem, coding request,
    debugging task, or multi-step analysis requiring the Autonomous Mind.
    """
    q = q_clean.lower().strip()

    # Exclude basic chit-chat, greetings, app open launchers, and simple date/time lookups
    if any(q.startswith(prefix) for prefix in ("open ", "launch ", "start ", "call ", "dial ")):
        return False
    if q in ("hi", "hello", "namaste", "hey", "how are you", "who are you", "who created you", "who is cosmos", "what is cosmos", "who is jarvis", "what is jarvis", "what time is it"):
        return False
    if "news" in q and not any(k in q for k in ("code", "debug", "python", "script", "algorithm")):
        return False

    # 1. Explicit Autonomous & Coding Triggers
    coding_verbs = (
        "code", "write a code", "write code", "write a program", "write a script",
        "write a function", "implement", "solve", "algorithm", "debug", "fix this error",
        "fix the bug", "refactor", "optimize this", "time complexity", "space complexity",
        "leetcode", "regex for", "sql query", "rest api", "unit test", "test cases"
    )
    if any(v in q for v in coding_verbs):
        return True

    # 2. Programming Language & Architecture Signifiers
    languages_and_tech = (
        "python", "javascript", "typescript", "java", "c++", "golang", "rust",
        "react", "django", "fastapi", "flask", "dockerfile", "html", "css",
        "binary search", "recursion", "dynamic programming", "hashmap", "linked list",
        "syntax error", "traceback", "indexerror", "keyerror", "nullpointer"
    )
    if any(l in q for l in languages_and_tech):
        return True

    # 3. Contextual Inspection Triggers
    context_inspection = (
        "check clipboard", "from clipboard", "in clipboard", "copied code",
        "analyze this file", "debug this file", "review this code", "fix my code"
    )
    if any(c in q for c in context_inspection):
        return True

    return False


# Universal alias for autonomous solving
cosmos_think_and_solve = cosmos_autonomous_solve


if __name__ == "__main__":
    test_query = sys.argv[1] if len(sys.argv) > 1 else "write a python function to check if two strings are anagrams"
    print(f"=== TESTING COSMOS AUTONOMOUS MIND ===")
    print(f"Query: {test_query}\n")
    solution = cosmos_autonomous_solve(test_query)
    print("=== RESULT ===")
    print(solution)
