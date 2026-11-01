"""
cosmos_screen_vision.py — Zero-Screenshot Live Screen Perception Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Architected exclusively for Sri Charan Tirumaladasu ("Boss" / "Sir")

Gives COSMOS real-time eyes on Boss's screen WITHOUT requiring screenshots:
1. Foreground window & app detection via ctypes.windll.user32
2. Direct VS Code live buffer reader (parses filename from title, reads from disk)
3. Universal in-memory screen text extraction (PIL.ImageGrab + Windows OCR, 0 bytes to disk)
4. Automatic deictic triggering on "what is this", "look at this", "this error", etc.

0 MB DISK IMPACT: All captures stay in io.BytesIO RAM buffers.
"""

import os
import re
import sys
import ctypes
import io

# ═══════════════════════════════════════════════════════════════════════
#  1. FOREGROUND WINDOW & APP DETECTION
# ═══════════════════════════════════════════════════════════════════════

def get_active_window_title() -> str:
    """Instantly detects the active foreground window title via user32."""
    if sys.platform != "win32":
        return ""
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            return buff.value or ""
    except Exception:
        pass
    return ""


def get_active_app_name() -> str:
    """Returns a normalized app identifier from the window title."""
    title = get_active_window_title().lower()
    if "visual studio code" in title or "- vscode" in title or "code.exe" in title:
        return "vscode"
    if "chrome" in title or "chromium" in title:
        return "chrome"
    if "edge" in title or "msedge" in title:
        return "edge"
    if "firefox" in title:
        return "firefox"
    if "powershell" in title or "cmd.exe" in title or "terminal" in title or "windows terminal" in title:
        return "terminal"
    if "notepad" in title:
        return "notepad"
    if "explorer" in title:
        return "explorer"
    if "pdf" in title or "acrobat" in title:
        return "pdf"
    return "unknown"


# ═══════════════════════════════════════════════════════════════════════
#  2. VS CODE LIVE BUFFER READER
# ═══════════════════════════════════════════════════════════════════════

def _extract_vscode_filepath(title: str) -> str:
    """
    Parses the active file path from VS Code window title.
    VS Code titles follow patterns like:
      - "filename.py — FolderName — Visual Studio Code"
      - "filename.py - FolderName - Visual Studio Code"
      - "● filename.py — FolderName — Visual Studio Code"  (unsaved changes)
    """
    if not title:
        return ""
    # Strip VS Code suffix
    clean = re.sub(r"\s*[-—]\s*Visual Studio Code\s*$", "", title, flags=re.IGNORECASE).strip()
    # Strip unsaved indicator (● or •)
    clean = re.sub(r"^[●•]\s*", "", clean).strip()
    
    # Try to split on " — " or " - " to get filename and workspace
    parts = re.split(r"\s*[-—]\s*", clean)
    if not parts:
        return ""
    
    filename = parts[0].strip()
    workspace = parts[1].strip() if len(parts) > 1 else ""
    
    # Try to find the full path on disk
    # 1. Check if the filename itself is an absolute path
    if os.path.isabs(filename) and os.path.isfile(filename):
        return filename
    
    # 2. Search common workspace roots
    search_roots = []
    if workspace:
        # Try common project locations
        for base in [
            os.path.expanduser("~\\OneDrive\\Desktop"),
            os.path.expanduser("~\\Desktop"),
            os.path.expanduser("~\\Documents"),
            os.path.expanduser("~"),
            "C:\\",
        ]:
            candidate = os.path.join(base, workspace, filename)
            if os.path.isfile(candidate):
                return candidate
            # Also try nested directories
            candidate2 = os.path.join(base, workspace, workspace, filename)
            if os.path.isfile(candidate2):
                return candidate2
    
    # 3. Walk from current working directory
    try:
        cwd = os.getcwd()
        candidate = os.path.join(cwd, filename)
        if os.path.isfile(candidate):
            return candidate
        # Search one level deeper
        for d in os.listdir(cwd):
            deep = os.path.join(cwd, d, filename)
            if os.path.isfile(deep):
                return deep
    except Exception:
        pass
    
    return ""


def inspect_vscode_active_file(max_lines: int = 120) -> str:
    """
    When Boss is in VS Code, reads the active file directly from disk
    and returns its content for AI context injection.
    0 screenshots needed — pure filesystem read.
    """
    title = get_active_window_title()
    if "visual studio code" not in title.lower() and "- vscode" not in title.lower():
        return ""
    
    filepath = _extract_vscode_filepath(title)
    if not filepath or not os.path.isfile(filepath):
        return f"[VS Code Active Window]: {title}\n(Could not locate file on disk for direct reading)"
    
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        
        total = len(lines)
        # Return up to max_lines from the file (centered if file is long)
        if total <= max_lines:
            content = "".join(lines)
        else:
            # Return first max_lines lines for context
            content = "".join(lines[:max_lines])
            content += f"\n... [{total - max_lines} more lines truncated] ..."
        
        return (
            f"[VS Code Live File: {os.path.basename(filepath)}]\n"
            f"[Full Path: {filepath}]\n"
            f"[Total Lines: {total}]\n"
            f"```\n{content}\n```"
        )
    except Exception as e:
        return f"[VS Code Active File]: {filepath}\n(Read error: {e})"


def get_clipboard_text_safe() -> str:
    """Safely retrieves clipboard text without blocking or launching Tkinter."""
    if sys.platform != "win32":
        return ""
    try:
        import win32clipboard
        import win32con
        win32clipboard.OpenClipboard()
        try:
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                return data or ""
        finally:
            win32clipboard.CloseClipboard()
    except Exception:
        pass
    return ""


# ═══════════════════════════════════════════════════════════════════════
#  3. UNIVERSAL IN-MEMORY SCREEN & UI INSPECTOR
# ═══════════════════════════════════════════════════════════════════════

def read_screen_text_in_ram() -> str:
    """
    For any non-VS Code window: extracts visible text from the focused window
    using in-memory PIL.ImageGrab + Windows OCR (0 bytes to disk).
    Falls back to window title + clipboard if OCR is unavailable.
    """
    context_parts = []
    
    # A. Window title for app context
    title = get_active_window_title()
    if title:
        context_parts.append(f"Active Window: {title}")
    
    # B. Try Windows native OCR on in-memory screenshot
    try:
        from PIL import ImageGrab
        import asyncio
        
        # Set DPI awareness for accurate capture
        if hasattr(ctypes, "windll"):
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass
        
        image = ImageGrab.grab()
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image.close()
        
        # Use Windows native OCR (no pytesseract dependency)
        try:
            from winrt.windows.graphics.imaging import BitmapDecoder
            from winrt.windows.media.ocr import OcrEngine
            from winrt.windows.storage.streams import DataWriter, InMemoryRandomAccessStream

            async def _ocr_from_bytes(img_bytes: bytes) -> str:
                stream = InMemoryRandomAccessStream()
                writer = DataWriter(stream)
                writer.write_bytes(img_bytes)
                await writer.store_async()
                await writer.flush_async()
                writer.detach_stream()
                stream.seek(0)
                decoder = await BitmapDecoder.create_async(stream)
                bitmap = await decoder.get_software_bitmap_async()
                engine = OcrEngine.try_create_from_user_profile_languages()
                if engine is None:
                    return ""
                result = await engine.recognize_async(bitmap)
                return result.text.strip()
            
            try:
                ocr_text = asyncio.run(asyncio.wait_for(_ocr_from_bytes(buffer.getvalue()), timeout=2.5))
                if ocr_text and len(ocr_text) > 10:
                    context_parts.append(f"Screen Text (OCR):\n{ocr_text[:8000]}")
            except Exception:
                pass
        except Exception:
            pass
        
        buffer.close()
    except Exception:
        pass
    
    # C. Clipboard fallback for code/text context
    if len(context_parts) < 2:  # OCR didn't yield useful text
        clip = get_clipboard_text_safe()
        if clip and len(clip.strip()) > 5:
            context_parts.append(f"Clipboard Content:\n{clip[:3000]}")
    
    return "\n\n".join(context_parts) if context_parts else ""


# ═══════════════════════════════════════════════════════════════════════
#  4. AUTOMATIC DEICTIC TRIGGER — "what is this", "look at this", etc.
# ═══════════════════════════════════════════════════════════════════════

# Phrases that trigger automatic live screen context injection
DEICTIC_PHRASES = (
    "what is this",
    "what's this",
    "whats this",
    "what am i looking at",
    "what am i doing",
    "look at this",
    "look at my screen",
    "this error",
    "this bug",
    "this code",
    "this file",
    "on my screen",
    "on the screen",
    "what is on my screen",
    "explain this",
    "explain this code",
    "fix this",
    "fix this bug",
    "fix this error",
    "fix this code",
    "debug this",
    "what does this do",
    "what does this mean",
    "help me with this",
    "what went wrong",
    "this warning",
    "this message",
    "read this",
    "check this",
    "review this",
    "analyze this",
    "analyse this",
    "solve this",
    "answer this",
)


def needs_screen_context(query: str) -> bool:
    """Returns True if the user's query implies they want COSMOS to look at their screen."""
    q = " ".join(query.lower().strip().split())
    return any(phrase in q for phrase in DEICTIC_PHRASES)


def capture_live_screen_context(user_prompt: str) -> str:
    """
    Master entry point: automatically inspects the Boss's screen based on what app is active.
    - VS Code → reads the live code file directly from disk (no screenshot)
    - Everything else → in-memory screen OCR + window title + clipboard
    Returns enriched context string for injection into the AI prompt.
    """
    app = get_active_app_name()
    context_parts = []
    
    # For VS Code: read the actual file (superior to OCR for code)
    if app == "vscode":
        vscode_ctx = inspect_vscode_active_file(max_lines=150)
        if vscode_ctx:
            context_parts.append(vscode_ctx)
    
    # For all apps: also get screen text / UI state
    screen_ctx = read_screen_text_in_ram()
    if screen_ctx:
        context_parts.append(screen_ctx)
    
    if not context_parts:
        title = get_active_window_title()
        return f"[Screen Context]: Boss's active window is: {title}" if title else ""
    
    return "\n\n".join(context_parts)


# ═══════════════════════════════════════════════════════════════════════
#  5. QUICK TEST
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"Active Window: {get_active_window_title()}")
    print(f"Active App: {get_active_app_name()}")
    print(f"\nDeictic trigger 'what is this': {needs_screen_context('what is this')}")
    print(f"Deictic trigger 'hello': {needs_screen_context('hello')}")
    print(f"\n--- Live Screen Context ---")
    ctx = capture_live_screen_context("what is this code doing")
    print(ctx[:2000] if ctx else "(no context captured)")

