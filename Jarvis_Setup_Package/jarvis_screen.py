"""Local screen capture and Windows OCR helpers."""

import asyncio
from io import BytesIO

from PIL import ImageGrab


MAX_OCR_CHARACTERS = 12000


def should_capture_screen(query):
    """Return whether a query clearly refers to visible screen content."""
    try:
        import cosmos_screen_vision
        if cosmos_screen_vision.needs_screen_context(query):
            return True
    except Exception:
        pass
    text = " ".join(query.lower().split())
    phrases = (
        "on my screen",
        "on the screen",
        "on screen",
        "on my display",
        "what am i looking at",
        "what's on my screen",
        "what's on my display",
        "what is on my screen",
        "what is on my display",
        "can you see my screen",
        "can u see my screen",
        "can you see the screen",
        "can u see the screen",
        "look at my screen",
        "look at the screen",
        "this page",
        "current page",
        "visible page",
        "this document",
        "current document",
        "this window",
        "this code",
        "this text",
        "this question",
        "this problem",
        "visible code",
        "code on screen",
        "review the code",
        "review this code",
        "review code",
        "review my code",
        "analyze the code",
        "analyse the code",
        "analyze my code",
        "analyse my code",
        "analyze the text",
        "analyse the text",
        "analyze this text",
        "analyse this text",
        "summarize the text",
        "summarise the text",
        "solve the question",
        "answer the question",
        "read this",
        "read the text",
        "review this",
        "analyze this",
        "analyse this",
        "summarize this",
        "summarise this",
        "solve this",
        "answer this",
        "explain this",
        "what does this say",
        "this screenshot",
        "the screenshot",
        "check my screen",
        "check the screen",
        "check screen",
        "read my screen",
        "read screen",
        "inspect my screen",
        "see my screen"
    )
    if any(phrase in text for phrase in phrases):
        return True

    return any(word in text for word in ("screen", "display", "monitor"))


def capture_screen_text(query: str = ""):
    """Capture the active screen, VS Code live buffer, and window context without blocking."""
    try:
        import cosmos_screen_vision
        vision_ctx = cosmos_screen_vision.capture_live_screen_context(query)
        if vision_ctx and len(vision_ctx.strip()) > 5:
            return vision_ctx.strip()[:MAX_OCR_CHARACTERS]
    except Exception:
        pass

    # Rich fallback: inspect active foreground window title and recent clipboard
    details = []
    try:
        import ctypes
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            if buff.value:
                details.append(f"Active Focused Window: {buff.value}")
    except Exception:
        pass

    try:
        import cosmos_screen_vision
        clip = cosmos_screen_vision.get_clipboard_text_safe()
        if clip and len(clip.strip()) > 3:
            details.append(f"Copied Content / Code: {clip[:2500]}")
    except Exception:
        pass

    if details:
        return "\n".join(details)
    return "User screen is active and tracking your workspace."
