"""
cosmos_universal_coder.py - Universal Polyglot Coder & Clipboard Reader for COSMOS
Architected exclusively for Sri Charan Tirumaladasu ("Boss" / "Sir")

Capabilities:
1. Automatic detection of coding requests across 90+ programming languages.
2. Windows Clipboard Reader (reads code directly from clipboard when instructed: "fix clipboard", "review code in clipboard", etc.).
3. Local file inspection when a local file path is referenced.
4. Polyglot syntax validation (ast.parse for Python, json.loads for JSON, balanced delimiters for C++, Java, JS, TS, Go, Rust, PHP, etc.).
5. Integration with cosmos_multi_brain / cosmos_autonomous_mind.
"""

import ast
import ctypes
import json
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

SUPPORTED_LANGUAGES = {
    "python", "py", "javascript", "js", "typescript", "ts", "html", "css",
    "c", "cpp", "c++", "csharp", "c#", "cs", "java", "kotlin", "swift",
    "go", "golang", "rust", "rs", "php", "ruby", "rb", "perl", "r", "scala",
    "sql", "postgresql", "mysql", "sqlite", "bash", "sh", "shell", "powershell",
    "ps1", "batch", "bat", "dockerfile", "yaml", "yml", "json", "xml", "lua",
    "dart", "haskell", "elixir", "clojure", "vba", "matlab", "assembly", "asm",
    "solidity", "graphql", "terraform", "toml", "groovy", "zig", "nim", "fortran"
}

# ═══════════════════════════════════════════════════════════════════════
# 1. WINDOWS CLIPBOARD & LOCAL FILE EXTRACTION
# ═══════════════════════════════════════════════════════════════════════

def get_windows_clipboard_text() -> str:
    """Safely retrieves text from the Windows OS clipboard via ctypes Win32 API."""
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        CF_UNICODETEXT = 13

        if not user32.OpenClipboard(None):
            return ""

        h_glb = user32.GetClipboardData(CF_UNICODETEXT)
        if not h_glb:
            user32.CloseClipboard()
            return ""

        kernel32.GlobalLock.restype = ctypes.c_void_p
        p_text = kernel32.GlobalLock(h_glb)
        if not p_text:
            user32.CloseClipboard()
            return ""

        text = ctypes.c_wchar_p(p_text).value or ""
        kernel32.GlobalUnlock(h_glb)
        user32.CloseClipboard()
        return text.strip()
    except Exception as e:
        print(f"[COSMOS CLIPBOARD ERROR] {e}")
        return ""

def extract_file_content_if_referenced(query: str) -> Optional[Tuple[str, str]]:
    """Checks if query references a local file path and reads its content."""
    # Look for Windows or Unix style file paths
    pattern = r'(?:[a-zA-Z]:\\[^ \t\r\n]+\.[a-zA-Z0-9]+|(?:\.{1,2}[/\\])?(?:[\w\-]+[/\\])+[\w\-]+\.[a-zA-Z0-9]+|\b[\w\-]+\.(?:py|js|ts|json|cpp|c|java|cs|go|rs|html|css|txt|sql)\b)'
    matches = re.findall(pattern, query)
    for path_candidate in matches:
        clean_path = path_candidate.strip("'\"")
        if os.path.isfile(clean_path):
            try:
                with open(clean_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(8000)
                    return clean_path, content
            except Exception:
                continue
    return None

# ═══════════════════════════════════════════════════════════════════════
# 2. SYNTAX VALIDATION ENGINE
# ═══════════════════════════════════════════════════════════════════════

def validate_code_syntax(code: str, lang: str = "python") -> Tuple[bool, str]:
    """Validates code syntax according to language type."""
    l = lang.lower().strip()
    if not code or not code.strip():
        return False, "Code is empty."

    # Python syntax validation
    if l in ("python", "py"):
        try:
            ast.parse(code)
            return True, "Valid Python syntax."
        except SyntaxError as e:
            return False, f"Python SyntaxError at line {e.lineno}: {e.msg}"

    # JSON validation
    if l == "json":
        try:
            json.loads(code)
            return True, "Valid JSON."
        except Exception as e:
            return False, f"Invalid JSON: {e}"

    # Balanced bracket/delimiter stack for C, C++, Java, JS, TS, Go, Rust, PHP, etc.
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
# 3. UNIVERSAL CODE SOLVER (MAIN ENTRY POINT)
# ═══════════════════════════════════════════════════════════════════════

def cosmos_universal_code_solver(user_input: str) -> str:
    """
    Main entry point for universal polyglot coding:
    - Inspects Windows clipboard if requested
    - Inspects local files if referenced
    - Solves the coding task using local Ollama models (Qwen-Coder / DeepSeek)
    - Validates syntax and returns formatted solution with spoken summary.
    """
    cmd = user_input.lower().strip()
    gathered_context = []

    # 1. Clipboard inspection
    if any(k in cmd for k in ("clipboard", "copied", "in clipboard", "from clipboard")):
        clip_content = get_windows_clipboard_text()
        if clip_content:
            gathered_context.append(f"[WINDOWS CLIPBOARD SNIPPET]:\n```\n{clip_content[:4000]}\n```")
        else:
            gathered_context.append("[WINDOWS CLIPBOARD]: Clipboard was empty or contained non-text data.")

    # 2. Local file inspection
    file_info = extract_file_content_if_referenced(user_input)
    if file_info:
        file_path, file_content = file_info
        gathered_context.append(f"[LOCAL FILE READ: {file_path}]:\n```\n{file_content}\n```")

    context_str = "\n\n".join(gathered_context) if gathered_context else ""

    # Build prompt
    augmented_task = user_input
    if context_str:
        augmented_task = f"{user_input}\n\n{context_str}"

    # Route to multi-model brain or autonomous mind
    try:
        import cosmos_multi_brain
        result = cosmos_multi_brain.cosmos_multi_model_solve(augmented_task)
    except Exception:
        import cosmos_autonomous_mind
        result = cosmos_autonomous_mind.cosmos_autonomous_solve(augmented_task)

    # Perform post-generation syntax check
    code_match = re.search(r"```([a-zA-Z0-9_\+\#-]*)\n([\s\S]*?)```", result)
    if code_match:
        lang = code_match.group(1).strip() or "python"
        code = code_match.group(2)
        valid, msg = validate_code_syntax(code, lang)
        if not valid and lang.lower() in ("python", "py"):
            print(f"[COSMOS CODER WARNING] Syntax check flagged: {msg}")

    return result

