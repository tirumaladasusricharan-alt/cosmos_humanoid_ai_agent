"""Local screen capture and Windows OCR helpers."""

import asyncio
from io import BytesIO

from PIL import ImageGrab


MAX_OCR_CHARACTERS = 12000


def should_capture_screen(query):
    """Return whether a query clearly refers to visible screen content."""
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
    )
    if any(phrase in text for phrase in phrases):
        return True

    return any(word in text for word in ("screen", "display", "monitor"))


async def _recognize_text(image_bytes):
    from winrt.windows.graphics.imaging import BitmapDecoder
    from winrt.windows.media.ocr import OcrEngine
    from winrt.windows.storage.streams import DataWriter, InMemoryRandomAccessStream

    stream = InMemoryRandomAccessStream()
    writer = DataWriter(stream)
    writer.write_bytes(image_bytes)
    await writer.store_async()
    await writer.flush_async()
    writer.detach_stream()
    stream.seek(0)

    decoder = await BitmapDecoder.create_async(stream)
    bitmap = await decoder.get_software_bitmap_async()
    engine = OcrEngine.try_create_from_user_profile_languages()
    if engine is None:
        raise RuntimeError(
            "Windows OCR has no installed language pack. Install a Windows "
            "display language with OCR support and try again."
        )

    result = await engine.recognize_async(bitmap)
    text = result.text.strip()
    if not text:
        raise RuntimeError("No readable text was found on the screen.")
    return text[:MAX_OCR_CHARACTERS]


def capture_screen_text():
    """Capture the primary display and extract text using Windows OCR."""
    image = ImageGrab.grab()
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return asyncio.run(_recognize_text(buffer.getvalue()))
