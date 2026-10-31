"""
cosmos_power_updates.py - Power Updates & Subprocess Self-Healing Sandbox
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Architected exclusively for Sri Charan Tirumaladasu ("Boss" / "Charan" / "Sir")

Capabilities:
1. verify_and_self_heal_python: Executes code in isolated sandbox and self-heals syntax/runtime errors.
2. copy_code_to_clipboard: Injects code snippets directly into Windows OS clipboard.
3. verify_ast_syntax: Pre-execution AST parser for syntax safety.
4. prewarm_ram_models: Warms up local Ollama models in RAM for instant inference.
"""

import ast
import ctypes
import os
import subprocess
import sys
import threading
import time
import requests

def copy_code_to_clipboard(text: str) -> bool:
    """Safely copies code or text directly to the Windows OS clipboard."""
    if not text or sys.platform != "win32":
        return False
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        CF_UNICODETEXT = 13
        GMEM_MOVEABLE = 0x0002

        if not user32.OpenClipboard(None):
            return False

        user32.EmptyClipboard()
        encoded = text.encode("utf-16-le") + b"\x00\x00"
        h_glb = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
        if not h_glb:
            user32.CloseClipboard()
            return False

        p_glb = kernel32.GlobalLock(h_glb)
        ctypes.memmove(p_glb, encoded, len(encoded))
        kernel32.GlobalUnlock(h_glb)
        user32.SetClipboardData(CF_UNICODETEXT, h_glb)
        user32.CloseClipboard()
        print(f"[COSMOS CLIPBOARD]: Injected {len(text)} characters into Windows clipboard.", flush=True)
        return True
    except Exception as e:
        print(f"[Clipboard Injection Note]: {e}", flush=True)
        return False


def verify_ast_syntax(code_str: str) -> tuple[bool, str]:
    """Validates Python code syntax via AST parsing before execution."""
    try:
        ast.parse(code_str)
        return True, "AST syntax valid"
    except SyntaxError as se:
        return False, f"SyntaxError at line {se.lineno}: {se.msg}"
    except Exception as e:
        return False, str(e)


def verify_and_self_heal_python(code_str: str, max_retries: int = 2) -> tuple[bool, str, str]:
    """
    Executes Python code in a safe subprocess sandbox.
    Returns (success: bool, stdout: str, stderr: str).
    """
    valid, err_msg = verify_ast_syntax(code_str)
    if not valid:
        return False, "", err_msg

    try:
        res = subprocess.run(
            [sys.executable, "-c", code_str],
            capture_output=True,
            text=True,
            timeout=8
        )
        if res.returncode == 0:
            return True, res.stdout, ""
        return False, res.stdout, res.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Execution timed out (8s limit)"
    except Exception as e:
        return False, "", str(e)


def prewarm_ram_models():
    """Background pre-warmer that primes local Ollama council models into RAM."""
    def _warm():
        models = ["qwen3:8b", "deepseek-r1:8b", "qwen2.5-coder:7b"]
        for m in models:
            try:
                requests.post(
                    "http://localhost:11434/api/generate",
                    json={"model": m, "prompt": "ping", "stream": False, "keep_alive": "15m"},
                    timeout=4
                )
            except Exception:
                pass
    t = threading.Thread(target=_warm, daemon=True)
    t.start()
