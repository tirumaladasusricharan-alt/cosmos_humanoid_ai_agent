"""
jarvis_popup.py - Native Windows Holographic Overlay with Global Hotkey
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Press Alt (quick tap), Alt + Space, or Ctrl + Alt anywhere on your desktop
to summon / dismiss COSMOS.
Runs silently in the background as a native Windows application.
No browser, no localhost — pure desktop integration.
"""

import os
import re
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

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
try:
    os.chdir(SCRIPT_DIR)
except Exception:
    pass

import time
import datetime
import threading
import ctypes
import queue
import math
from concurrent.futures import TimeoutError as FutureTimeoutError
from ctypes import wintypes
import tkinter as tk
import tkinter.font as tkfont

user32 = ctypes.windll.user32
WINDOW_TITLE = "COSMOS_OVERLAY_ROOT"
SINGLE_INSTANCE_MUTEX = None

if __name__ == "__main__":
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.argtypes = (
        ctypes.c_void_p,
        ctypes.c_bool,
        ctypes.c_wchar_p,
    )
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    SINGLE_INSTANCE_MUTEX = kernel32.CreateMutexW(
        None, False, "Local\\CosmosOverlaySingleton"
    )
    mutex_error = ctypes.get_last_error()
    if not SINGLE_INSTANCE_MUTEX:
        raise ctypes.WinError(mutex_error)
    if mutex_error == 183:
        existing = user32.FindWindowW(None, WINDOW_TITLE)
        if existing:
            user32.ShowWindow(existing, 5)
            user32.SetForegroundWindow(existing)
            user32.SetWindowPos(existing, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)
            sys.exit(0)

# ── COSMOS Engine Imports ────────────────────────────────────────────
import jarvis_actions
import jarvis_brain
import jarvis_voice
import jarvis_screen
from cosmos_human_voice import cosmos_speak, prepare_speech

_is_popup_already_open = False


def extract_spoken_text(text: str) -> str:
    """Extracts a clean, crisp 1-2 sentence spoken summary, eliminating code and prompt tokens."""
    if not text:
        return ""
    m = re.search(
        r"(?:\[SPOKEN_SUMMARY\]|\*\*\[SPOKEN_SUMMARY\]:\*\*|SPOKEN_SUMMARY:?)\s*(.*?)(?=\n\s*\[|\Z)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if m:
        summary = m.group(1).strip()
    else:
        summary = text
    # Strip markdown code blocks
    summary = re.sub(r"```[\s\S]*?```", "", summary)
    # Strip markdown formatting
    summary = re.sub(r"[\*\_#`]", "", summary)
    lines = [l.strip() for l in summary.splitlines() if l.strip()]
    if lines:
        full_text = " ".join(lines)
        sents = re.split(r"(?<=[.!?])\s+", full_text)
        return " ".join(sents[:2]).strip()
    return summary.strip()

# ═══════════════════════════════════════════════════════════════════════
#  COLOR PALETTE — Holographic Cyan Theme
# ═══════════════════════════════════════════════════════════════════════
C = {
    "bg_deep":      "#06121c",
    "bg_panel":     "#071722",
    "bg_header":    "#091d2a",
    "bg_input":     "#0a1e2b",
    "bg_actions":   "#091a26",
    "border":       "#24d7e8",
    "border_dim":   "#174153",
    "accent":       "#49e6f2",
    "accent_glow":  "#a4f8ff",
    "text":         "#c5e3e9",
    "text_bright":  "#f2fbff",
    "text_dim":     "#7895a3",
    "green":        "#57f0c2",
    "yellow":       "#ffd08a",
    "red":          "#ff7182",
}


# ═══════════════════════════════════════════════════════════════════════
#  COSMOS OVERLAY WINDOW
# ═══════════════════════════════════════════════════════════════════════
class CosmosOverlay:
    """Native Windows overlay — summoned by Alt tap, Alt+Space, or Ctrl+Alt."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.ui_events = queue.Queue()
        self.visible = False
        self.voice_stop_event = threading.Event()
        self.voice_enabled_event = threading.Event()
        self.voice_ready_event = threading.Event()
        self.voice_ready_event.set()
        self.voice_enabled = False
        self.isUserMicManuallyOff = False
        self.voice_thread = None
        self.pending_screen_context = None
        self.processing = False
        self.screen_capture_in_progress = False
        self._response_counter = 0
        self.latest_response = None
        self._copy_feedback = set()
        self._copy_feedback_after = {}
        self._console_copy_widgets = []
        self._hud_scroll_offset = 0
        self._hud_animation_after = None
        self._hud_animation_started = time.monotonic()

        # ── Window Chrome ────────────────────────────────────────────
        self.root.overrideredirect(True)          # frameless
        self.root.attributes("-topmost", True)    # always on top
        self.root.configure(bg=C["bg_deep"])
        self.root.update_idletasks()
        try:
            top_hwnd = user32.GetParent(self.root.winfo_id()) or self.root.winfo_id()
            user32.SetWindowTextW(top_hwnd, WINDOW_TITLE)
        except Exception:
            pass

        # ── Size & Position (upper-center of screen) ─────────────────
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.w = min(1120, sw - 48)
        self.h = min(650, sh - 72)
        self.x = (sw - self.w) // 2
        self.y = (sh - self.h) // 2
        self.root.geometry(f"{self.w}x{self.h}+{self.x}+{self.y}")

        self._build_ui()
        self._bind_events()

        # ── Background hotkey thread ─────────────────────────────────
        self._start_hotkey_thread()

    # ─────────────────────────────────────────────────────────────────
    #  UI CONSTRUCTION
    # ─────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Outer glow border
        self.border_frame = tk.Frame(self.root, bg=C["border"], padx=1, pady=1)
        self.border_frame.pack(fill=tk.BOTH, expand=True)

        self.body = tk.Frame(self.border_frame, bg=C["bg_deep"])
        self.body.pack(fill=tk.BOTH, expand=True)

        self._build_header()
        self._build_input()
        self._build_output()
        self._build_actions()

    # ── Header ───────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self.body, bg=C["bg_header"], height=58)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        hdr.bind("<ButtonPress-1>", self._drag_start)
        hdr.bind("<B1-Motion>",     self._drag_move)

        rail = tk.Frame(hdr, bg=C["border_dim"], height=1)
        rail.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Frame(rail, bg=C["accent"], height=1).place(
            relx=0.43, relwidth=0.14, relheight=1
        )

        left = tk.Frame(hdr, bg=C["bg_header"])
        left.pack(side=tk.LEFT, padx=20, pady=0)
        left.bind("<ButtonPress-1>", self._drag_start)
        left.bind("<B1-Motion>",     self._drag_move)

        tk.Label(left, text="⚡", font=("Segoe UI Emoji", 19),
                 fg=C["accent"], bg=C["bg_header"]).pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(left, text="COSMOS  ·  EXECUTIVE AI ASSISTANT",
                 font=("Segoe UI", 12, "bold"),
                 fg=C["text_bright"], bg=C["bg_header"]).pack(side=tk.LEFT)

        self.status_lbl = tk.Label(
            hdr, text="● COSMOS ONLINE", font=("Consolas", 9, "bold"),
            fg=C["green"], bg="#10353d", padx=12, pady=5)
        self.status_lbl.pack(side=tk.LEFT, padx=18)

        close_btn = tk.Label(hdr, text=" ✕ ", font=("Segoe UI", 12, "bold"),
                             fg=C["text_dim"], bg=C["bg_header"], cursor="hand2")
        close_btn.pack(side=tk.RIGHT, padx=14)
        close_btn.bind("<Button-1>", lambda e: self.hide())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg=C["red"]))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=C["text_dim"]))

        tk.Label(hdr, text="Alt or Alt+Space to toggle   ·   Esc to close",
                 font=("Consolas", 9), fg=C["text_dim"],
                 bg=C["bg_header"]).pack(side=tk.RIGHT, padx=14)

    # ── Input Bar ────────────────────────────────────────────────────
    def _build_input(self):
        wrap = tk.Frame(self.body, bg=C["bg_header"], padx=24, pady=14)
        wrap.pack(fill=tk.X)

        rail = tk.Frame(wrap, bg=C["border_dim"], height=1)
        rail.pack(fill=tk.X, pady=(0, 10))
        tk.Frame(rail, bg=C["accent"], height=1).place(
            relx=0.43, relwidth=0.14, relheight=1
        )

        border = tk.Frame(wrap, bg=C["border_dim"],
                          highlightthickness=1, highlightbackground="#387488",
                          padx=2, pady=2)
        border.pack(fill=tk.X)

        inner = tk.Frame(border, bg=C["bg_input"])
        inner.pack(fill=tk.X)

        tk.Label(inner, text="  ❯ ", font=("Segoe UI", 18, "bold"),
                 fg=C["accent"], bg=C["bg_input"]).pack(side=tk.LEFT)

        self.query_var = tk.StringVar()
        self.entry = tk.Entry(
            inner, textvariable=self.query_var,
            font=("Segoe UI", 14), fg=C["text_bright"], bg=C["bg_input"],
            insertbackground=C["accent"], relief=tk.FLAT, bd=9)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind("<Return>", self._on_submit)

        self.exec_btn = tk.Button(
            inner, text=" EXECUTE ", font=("Segoe UI", 10, "bold"),
            fg=C["bg_deep"], bg=C["accent"], activebackground=C["accent_glow"],
            activeforeground=C["bg_deep"], relief=tk.FLAT, cursor="hand2",
            command=self._on_submit, padx=16, pady=7)
        self.exec_btn.pack(side=tk.RIGHT, padx=6, pady=5)

        self.screen_btn = tk.Button(
            inner, text=" SCREEN ", font=("Segoe UI", 9, "bold"),
            fg=C["text"], bg="#122c3a", activebackground="#1b4554",
            activeforeground=C["accent"], relief=tk.FLAT, cursor="hand2",
            command=self._capture_screen, padx=10, pady=7)
        self.screen_btn.pack(side=tk.RIGHT, padx=3, pady=4)

        self.mic_btn = tk.Button(
            inner, text=" MIC OFF ", font=("Segoe UI", 9, "bold"),
            fg=C["text"], bg="#122c3a", activebackground="#1b4554",
            activeforeground=C["accent"], relief=tk.FLAT, cursor="hand2",
            command=self._toggle_microphone, padx=10, pady=7)
        self.mic_btn.pack(side=tk.RIGHT, padx=3, pady=4)

    # ── Output Console ───────────────────────────────────────────────
    def _build_output(self):
        wrap = tk.Frame(self.body, bg=C["bg_panel"], padx=10, pady=0)
        wrap.pack(fill=tk.BOTH, expand=True)

        self.console = tk.Canvas(
            wrap, bg=C["bg_panel"], highlightthickness=0, bd=0,
            yscrollincrement=20)
        self.console.pack(fill=tk.BOTH, expand=True)
        self.console.bind("<MouseWheel>", self._scroll_console)
        self.console.bind("<Configure>", self._redraw_console)
        self.console_fonts = {
            "user": tkfont.Font(family="Consolas", size=11, weight="bold"),
            "cosmos": tkfont.Font(family="Consolas", size=11),
            "sys": tkfont.Font(family="Consolas", size=10, slant="italic"),
            "err": tkfont.Font(family="Consolas", size=10),
        }
        self.console_colors = {
            "user": C["yellow"],
            "cosmos": "#b7e5eb",
            "sys": "#86eacb",
            "err": C["red"],
        }
        self.console_history = []

        self._print("sys", f"[COSMOS OVERLAY READY] {datetime.datetime.now().strftime('%I:%M %p · %A, %B %d')}\n")
        self._print("cosmos", "COSMOS: Ready, sir. Say COSMOS or press Alt to summon me.\n\n")

    def _draw_console_hud(self, width, height):
        cx = width * 0.52
        cy = height * 0.53
        radius = min(height * 0.48, width * 0.31)

        self.console.create_rectangle(
            0, 0, width, height, fill="#071722", outline="", tags="hud"
        )
        self.console.create_rectangle(
            0, height * 0.76, width, height,
            fill="#081b27", outline="", tags="hud"
        )

        for offset in range(0, int(width), 42):
            self.console.create_line(
                offset, height * 0.08, offset, height * 0.94,
                fill="#102b37", width=1, tags="hud"
            )
        for offset in range(int(height * 0.08), int(height), 34):
            self.console.create_line(
                0, offset, width, offset,
                fill="#102b37", width=1, tags="hud"
            )

        for fraction, color, line_width in (
            (1.0, "#173d48", 1),
            (0.96, "#1b3943", 1),
            (0.92, "#176477", 2),
            (0.89, "#123846", 1),
            (0.81, "#2a99a6", 2),
            (0.77, "#18434e", 1),
            (0.72, "#1c5866", 1),
            (0.67, "#214a52", 1),
            (0.62, "#194653", 1),
        ):
            radius_px = radius * fraction
            self.console.create_oval(
                cx - radius_px, cy - radius_px,
                cx + radius_px, cy + radius_px,
                outline=color, width=line_width, tags=("hud", "reactor")
            )

        for start, extent, color, line_width in (
            (205, 112, "#35d6e4", 4),
            (32, 74, "#e4b85e", 3),
            (105, 61, "#32b8c5", 3),
            (284, 48, "#d5aa5d", 3),
        ):
            bounds = (
                cx - radius * 0.88, cy - radius * 0.88,
                cx + radius * 0.88, cy + radius * 0.88,
            )
            self.console.create_arc(
                *bounds, start=start, extent=extent, style=tk.ARC,
                outline="#102f39", width=11, tags="hud"
            )
            self.console.create_arc(
                *bounds, start=start, extent=extent, style=tk.ARC,
                outline="#1c5963", width=6, tags="hud"
            )
            self.console.create_arc(
                *bounds,
                start=start, extent=extent, style=tk.ARC,
                outline=color, width=line_width, tags=("hud", "reactor")
            )

        for tick in range(120):
            radians = tick * math.pi / 60
            major_tick = tick % 10 == 0
            inner_radius = radius * (0.94 if major_tick else 0.978)
            outer_radius = radius * 1.01
            self.console.create_line(
                cx + inner_radius * math.cos(radians),
                cy + inner_radius * math.sin(radians),
                cx + outer_radius * math.cos(radians),
                cy + outer_radius * math.sin(radians),
                fill="#7aa2a5" if major_tick else "#35545b",
                width=2 if major_tick else 1,
                tags=("hud", "reactor"),
            )

        wave_width = min(width * 0.3, 250)
        points = []
        samples = 100
        for sample in range(samples + 1):
            relative = sample / samples * 2 - 1
            envelope = max(0, 1 - abs(relative)) ** 1.5
            wave = (
                math.sin(relative * 31)
                + 0.45 * math.sin(relative * 59)
            ) * envelope
            points.extend((cx + relative * wave_width, cy + wave * radius * 0.16))
        self.waveform_items = [
            self.console.create_line(
                *points, fill="#164a55", width=12, smooth=True,
                tags=("hud", "waveform")
            ),
            self.console.create_line(
                *points, fill="#c6a960", width=5, smooth=True,
                tags=("hud", "waveform")
            ),
            self.console.create_line(
                *points, fill="#63e8eb", width=2, smooth=True,
                tags=("hud", "waveform")
            ),
            self.console.create_line(
                *points, fill="#d8ffff", width=1, smooth=True,
                tags=("hud", "waveform")
            ),
        ]
        self.waveform_layout = (cx, cy, wave_width, radius)
        self.console.create_line(
            cx - wave_width, cy, cx + wave_width, cy,
            fill="#528c91", width=1, tags=("hud", "waveform-axis")
        )

    def _wrap_console_line(self, text, font, max_width):
        if not text:
            return [""]
        words = text.split()
        if not words:
            return [""]

        lines = []
        line = words[0]
        for word in words[1:]:
            candidate = f"{line} {word}"
            if font.measure(candidate) <= max_width:
                line = candidate
            else:
                lines.append(line)
                line = word
        lines.append(line)
        return lines

    def _format_lang(self, raw_lang):
        if not raw_lang:
            return "Code"
        l = raw_lang.strip().lower()
        mapping = {
            "py": "Python", "python": "Python", "python3": "Python",
            "js": "JavaScript", "javascript": "JavaScript", "node": "JavaScript",
            "ts": "TypeScript", "typescript": "TypeScript",
            "cpp": "C++", "c++": "C++", "c": "C", "csharp": "C#", "cs": "C#",
            "java": "Java", "html": "HTML", "htm": "HTML", "css": "CSS",
            "sql": "SQL", "psql": "PostgreSQL", "mysql": "MySQL",
            "bash": "Bash", "sh": "Shell", "powershell": "PowerShell", "ps1": "PowerShell",
            "json": "JSON", "yaml": "YAML", "yml": "YAML", "xml": "XML",
            "rust": "Rust", "rs": "Rust", "go": "Go", "golang": "Go",
            "php": "PHP", "rb": "Ruby", "ruby": "Ruby", "swift": "Swift", "kotlin": "Kotlin"
        }
        return mapping.get(l, raw_lang.strip().capitalize() or "Code")

    def _redraw_console(self, event=None):
        width = max(1, self.console.winfo_width())
        height = max(1, self.console.winfo_height())
        self.console.delete("all")
        self._hud_scroll_offset = 0
        self._draw_console_hud(width, height)

        for button in self._console_copy_widgets:
            button.destroy()
        self._console_copy_widgets.clear()

        y = 16
        last_cosmos_entry_start = None
        has_code = False
        for entry in self.console_history:
            tag, text = entry[:2]
            response_id = entry[2] if len(entry) > 2 else None
            font = self.console_fonts[tag]
            if tag == "cosmos" and response_id is not None:
                last_cosmos_entry_start = y
                copy_text = self._extract_response_text(text)
                if "```" in copy_text or self._looks_like_technical_output(copy_text):
                    has_code = True
                self._draw_cosmos_entry(
                    copy_text.strip(), response_id, width, y, copy_text
                )
                y += self._last_cosmos_entry_height
            else:
                for source_line in text.splitlines():
                    for line in self._wrap_console_line(
                        source_line, font, max(40, width - 36)
                    ):
                        self.console.create_text(
                            20, y, anchor="nw", text=line,
                            fill=self.console_colors[tag], font=font, tags="transcript"
                        )
                        y += font.metrics("linespace") + 3
                y += 3

        total_h = max(height, y + 12)
        self.console.configure(scrollregion=(0, 0, width, total_h))
        # Keep the beginning of tall responses or code blocks visible so they aren't hidden
        if last_cosmos_entry_start is not None and (has_code or (y - last_cosmos_entry_start) > height * 0.5):
            fraction = max(0.0, min(1.0, (last_cosmos_entry_start - 12) / total_h))
            self.console.yview_moveto(fraction)
        else:
            self.console.yview_moveto(1.0)
        self._pin_console_hud()

    def _draw_cosmos_entry(self, body, response_id, width, y, copy_text=None):
        entry_start = y
        message_key = ("message", response_id)
        self._add_copy_button(
            width - 16, y, "COPY", body if copy_text is None else copy_text,
            message_key, anchor="ne"
        )
        line_height = self.console_fonts["cosmos"].metrics("linespace") + 3
        content = re.sub(r"\n{3,}", "\n\n", body)
        segments = []
        cursor = 0
        pattern = re.compile(r"```([^\n`]*)\n?(.*?)```", re.DOTALL)
        for match in pattern.finditer(content):
            if match.start() > cursor:
                segments.append(("text", content[cursor:match.start()], None))
            raw_lang = match.group(1).strip()
            segments.append(("code", match.group(2), raw_lang))
            cursor = match.end()
        if cursor < len(content):
            trailing = content[cursor:]
            if "```" in trailing:
                opening = trailing.find("```")
                if opening:
                    segments.append(("text", trailing[:opening], None))
                language_and_code = trailing[opening + 3:]
                raw_lang, separator, code = language_and_code.partition("\n")
                segments.append(("code", code if separator else language_and_code, raw_lang.strip()))
            else:
                segments.append(("text", trailing, None))
        if not segments:
            segments = [("text", content, None)]

        if not re.search(r"```", content) and self._looks_like_technical_output(content):
            segments = [("code", content, "Python")]

        first_text = True
        code_index = 0
        for item in segments:
            kind = item[0]
            segment = item[1]
            raw_lang = item[2] if len(item) > 2 else None

            if kind == "text":
                display = re.sub(r"^\s*\[VERIFIED (?:CODE|SOLUTION)\]:?\s*", "", segment, flags=re.IGNORECASE)
                display = display.strip("\n")
                if not display:
                    continue
                if first_text:
                    display = "COSMOS: " + display
                    first_text = False
                for source_line in display.splitlines() or [""]:
                    for line in self._wrap_console_line(
                        source_line,
                        self.console_fonts["cosmos"],
                        max(40, width - 150),
                    ):
                        self.console.create_text(
                            20, y, anchor="nw", text=line,
                            fill=self.console_colors["cosmos"],
                            font=self.console_fonts["cosmos"],
                            tags="transcript",
                        )
                        y += line_height
                y += 2
                continue

            if first_text:
                self.console.create_text(
                    20, y, anchor="nw", text="COSMOS:",
                    fill=self.console_colors["cosmos"],
                    font=self.console_fonts["cosmos"],
                    tags="transcript",
                )
                y += line_height
                first_text = False

            code_index += 1
            code_key = ("code", response_id, code_index)
            code_font = self.console_fonts["cosmos"]
            max_code_width = max(40, width - 76)
            code_lines = []
            for source_line in segment.rstrip("\n").splitlines() or [""]:
                wrapped = self._wrap_code_line(source_line, code_font, max_code_width)
                code_lines.extend(wrapped)

            lang_label = self._format_lang(raw_lang)
            header_height = 32
            code_line_height = code_font.metrics("linespace") + 2
            block_total_height = header_height + len(code_lines) * code_line_height + 16

            # Dark modern code card matching reference
            self.console.create_rectangle(
                24, y, width - 24, y + block_total_height,
                fill="#0d1117", outline="#30363d", width=1,
                tags=("transcript", "code-block"),
            )
            # Distinct card header strip
            self.console.create_rectangle(
                24, y, width - 24, y + header_height,
                fill="#161b22", outline="#30363d", width=1,
                tags=("transcript", "code-header"),
            )
            # Language name (e.g. Python)
            self.console.create_text(
                36, y + 8, anchor="nw", text=lang_label,
                fill="#f0f6fc", font=("Segoe UI", 9, "bold"),
                tags="transcript",
            )
            # Prominent COPY CODE button
            self._add_copy_button(
                width - 32, y + 4, "COPY CODE", segment.rstrip("\n"),
                code_key, anchor="ne",
            )
            # Code lines in clean high-contrast text
            self.console.create_text(
                36, y + header_height + 8, anchor="nw", text="\n".join(code_lines),
                fill="#e6edf3", font=code_font, tags=("transcript", "code-text"),
            )
            y += block_total_height + 8

        self._last_cosmos_entry_height = max(line_height, y - entry_start + 3)

    def _wrap_code_line(self, text, font, max_width):
        if not text:
            return [""]
        lines = []
        current = ""
        for character in text:
            candidate = current + character
            if current and font.measure(candidate) > max_width:
                lines.append(current)
                current = character
            else:
                current = candidate
        lines.append(current)
        return lines

    def _looks_like_technical_output(self, text):
        lines = [line for line in text.splitlines() if line.strip()]
        if len(lines) < 2:
            return False
        indicators = re.compile(
            r"^\s*(?:import\s|from\s|def\s|class\s|return\b|"
            r"(?:const|let|var|function)\s|Traceback\b|"
            r"[\{\}\[\];]|[A-Za-z_]\w*\s*=\s*|(?:GET|POST|PUT|DELETE)\s+/)",
            re.IGNORECASE,
        )
        if sum(bool(indicators.search(line)) for line in lines) >= 2:
            return True
        return (
            any(line.lstrip().startswith("Traceback") for line in lines)
            and any(re.search(r"\b(?:Error|Exception):", line) for line in lines)
        )

    def _add_copy_button(self, x, y, label, text, feedback_key, anchor="nw"):
        copied = feedback_key in self._copy_feedback
        is_code = (label == "COPY CODE")
        button = tk.Button(
            self.console,
            text="✓ COPIED" if copied else ("⧉  COPY CODE" if is_code else label),
            font=("Consolas", 8, "bold"),
            fg=C["green"] if copied else ("#58a6ff" if is_code else C["accent"]),
            bg="#161b22" if is_code else "#0b2936",
            activebackground="#21262d" if is_code else "#123c49",
            activeforeground="#79c0ff" if is_code else C["accent_glow"],
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            padx=7 if is_code else 5,
            pady=2,
            command=lambda value=text, key=feedback_key: self._copy_text(value, key),
        )
        self._console_copy_widgets.append(button)
        self.console.create_window(x, y, anchor=anchor, window=button)

    def _copy_text(self, text, feedback_key):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update_idletasks()
        except tk.TclError as error:
            self._print("err", f"[CLIPBOARD ERROR] {error}\n")
            return
        previous_after = self._copy_feedback_after.pop(feedback_key, None)
        if previous_after is not None:
            self.root.after_cancel(previous_after)
        self._copy_feedback.add(feedback_key)
        if hasattr(self, "copy_last_btn"):
            self._refresh_copy_last_button()
        self._redraw_console()
        after_id = self.root.after(
            2000, lambda key=feedback_key: self._clear_copy_feedback(key)
        )
        self._copy_feedback_after[feedback_key] = after_id

    def _clear_copy_feedback(self, feedback_key):
        self._copy_feedback.discard(feedback_key)
        self._copy_feedback_after.pop(feedback_key, None)
        if hasattr(self, "copy_last_btn"):
            self._refresh_copy_last_button()
        self._redraw_console()

    def _extract_response_text(self, text):
        response = text
        if response.startswith("COSMOS:"):
            response = response[len("COSMOS:"):]
            if response.startswith(" "):
                response = response[1:]
        if response.endswith("\n\n"):
            return response[:-2]
        return response.rstrip("\n")

    def _copy_latest(self):
        if self.latest_response is None:
            self._print("err", "[COPY ERROR] No COSMOS response is available yet.\n")
            return
        response_id, text = self.latest_response
        self._copy_text(text, ("message", response_id))

    def _refresh_copy_last_button(self):
        is_copied = (
            self.latest_response is not None
            and ("message", self.latest_response[0]) in self._copy_feedback
        )
        self.copy_last_btn.config(
            text=" ✓ COPIED " if is_copied else " COPY LAST ",
            fg=C["green"] if is_copied else C["accent"],
        )

    def _animate_hud(self):
        self._hud_animation_after = None
        if not self.root.winfo_exists():
            return

        delay = 250
        if self._is_window_visible() and hasattr(self, "waveform_items"):
            now = time.monotonic() - self._hud_animation_started
            self._update_waveform(now)
            delay = 40

        self._hud_animation_after = self.root.after(delay, self._animate_hud)

    def _update_waveform(self, elapsed):
        cx, cy, wave_width, radius = self.waveform_layout
        samples = 120
        points = []
        for sample in range(samples + 1):
            relative = sample / samples * 2 - 1
            envelope = max(0, 1 - abs(relative)) ** 1.35
            phase = elapsed * 8.5
            carrier = (
                math.sin(relative * 27 + phase)
                + 0.52 * math.sin(relative * 51 - phase * 0.68)
                + 0.2 * math.sin(relative * 83 + phase * 0.43)
            )
            peaks = 0.42 + 0.58 * (0.5 + 0.5 * math.sin(phase * 0.37))
            modulation = 0.82 + 0.18 * math.sin(elapsed * 1.7 + relative * 5)
            y = (
                cy + self._hud_scroll_offset
                + carrier * envelope * radius * 0.21 * peaks * modulation
            )
            points.extend((cx + relative * wave_width, y))

        for item in self.waveform_items:
            self.console.coords(item, *points)

    def _scroll_console(self, event):
        self.console.yview_scroll(-1 if event.delta > 0 else 1, "units")
        self._pin_console_hud()
        return "break"

    def _pin_console_hud(self):
        offset = self.console.canvasy(0)
        self.console.move("hud", 0, offset - self._hud_scroll_offset)
        self._hud_scroll_offset = offset

    # ── Quick Action Bar ─────────────────────────────────────────────
    def _build_actions(self):
        bar = tk.Frame(self.body, bg=C["bg_header"], padx=18, pady=12)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        rail = tk.Frame(bar, bg=C["border_dim"], height=1)
        rail.place(relx=0, rely=0, relwidth=1, height=1)
        tk.Frame(rail, bg=C["accent"], height=1).place(
            relx=0.43, relwidth=0.14, relheight=1
        )

        buttons = [
            ("📈 Market Report",   "stock market report"),
            ("🕒 Time",            "what time is it"),
            ("📅 Date",            "what is the date today"),
            ("📧 Email Brief",     "check unread emails"),
            ("🎵 Play Lofi",       "play lofi on youtube"),
            ("💻 Open VS Code",    "open vs code"),
        ]

        for label, cmd in buttons:
            b = tk.Button(
                bar, text=label, font=("Segoe UI", 9, "bold"),
                fg="#b8e4ed", bg="#102a38", activebackground="#174656",
                activeforeground=C["accent"], relief=tk.FLAT, cursor="hand2",
                padx=12, pady=7, highlightthickness=1,
                highlightbackground="#387283", highlightcolor=C["accent"],
                command=lambda c=cmd: self._quick(c))
            b.pack(side=tk.LEFT, padx=5)

        self.copy_last_btn = tk.Button(
            bar, text=" COPY LAST ", font=("Segoe UI", 9, "bold"),
            fg=C["accent"], bg="#102a38", activebackground="#174656",
            activeforeground=C["accent_glow"], relief=tk.FLAT, cursor="hand2",
            padx=12, pady=7, highlightthickness=1,
            highlightbackground="#387283", highlightcolor=C["accent"],
            command=self._copy_latest,
        )
        self.copy_last_btn.pack(side=tk.RIGHT, padx=5)

    # ─────────────────────────────────────────────────────────────────
    #  CORE LOGIC
    # ─────────────────────────────────────────────────────────────────
    def _print(self, tag, text):
        if tag == "cosmos":
            self._response_counter += 1
            response_id = self._response_counter
            copy_text = self._extract_response_text(text)
            self.latest_response = (response_id, copy_text)
            self.console_history.append((tag, text, response_id))
            if hasattr(self, "copy_last_btn"):
                self._refresh_copy_last_button()
        else:
            self.console_history.append((tag, text))
        self._redraw_console()

    def _quick(self, q):
        self.query_var.set(q)
        self._on_submit()

    def _on_submit(self, event=None):
        q = self.query_var.get().strip()
        return self._submit_query(q)

    def _submit_query(self, q):
        if jarvis_voice.is_close_command(q):
            self._print("user", f"You: {q}\n")
            self._close_from_voice()
            return "break"

        if self.processing or self.screen_capture_in_progress:
            if self.screen_capture_in_progress:
                self.voice_ready_event.set()
            return "break"
        if not q:
            return "break"
        self.query_var.set("")
        self._print("user", f"You: {q}\n")

        self.processing = True
        screen_context = self.pending_screen_context
        self.pending_screen_context = None
        self.voice_ready_event.clear()
        self.exec_btn.config(text=" THINKING… ", state=tk.DISABLED)
        self.screen_btn.config(state=tk.DISABLED)
        self.status_lbl.config(text="● COSMOS PROCESSING", fg=C["yellow"])

        def worker():
            try:
                context = screen_context
                if context is None and jarvis_screen.should_capture_screen(q):
                    self._post_to_ui(lambda: self.status_lbl.config(
                        text="● COSMOS READING SCREEN", fg=C["yellow"]))
                    context = self._capture_screen_text()
                prompt = q
                if context:
                    prompt += (
                        "\n\n[SCREEN TEXT EXTRACTED FROM THE CURRENT DISPLAY BY LOCAL OCR]\n"
                        + context
                        + "\n[END SCREEN TEXT]"
                    )
                reply = jarvis_brain.think(
                    prompt,
                    action_query=q,
                    remember=not bool(context),
                    screen_context=bool(context),
                )
                if context:
                    self._post_to_ui(
                        lambda length=len(context): self._print(
                            "sys", f"[SCREEN OCR READ {length} CHARACTERS]\n"
                        ),
                    )
            except Exception as e:
                reply = f"Error: {e}"
            if not reply or not reply.strip():
                reply = (
                    "Could you please specify a bit more, sir? "
                    "Let me know what you'd like to look up or do, and I'll assist you right away."
                )
            speech_target = extract_spoken_text(reply)
            prepared_audio = prepare_speech(speech_target)
            # Instantly display the reply on screen without blocking on audio generation
            self._post_to_ui(
                lambda: self._show_reply(reply, prepared_audio)
            )

        threading.Thread(target=worker, daemon=True).start()
        return "break"

    def _capture_screen_text(self):
        hidden = threading.Event()

        def hide_overlay():
            self.hide()
            hidden.set()

        self._post_to_ui(hide_overlay)
        if not hidden.wait(timeout=2):
            raise RuntimeError("Could not hide the COSMOS overlay before screen capture.")
        try:
            time.sleep(0.25)
            return jarvis_screen.capture_screen_text()
        finally:
            self._post_to_ui(self.show)

    def _capture_screen(self):
        if self.processing or self.screen_capture_in_progress:
            return
        self.screen_capture_in_progress = True
        self.screen_btn.config(state=tk.DISABLED)
        self.exec_btn.config(state=tk.DISABLED)
        self.status_lbl.config(text="● COSMOS READING SCREEN", fg=C["yellow"])

        def worker():
            try:
                text = self._capture_screen_text()
            except Exception as e:
                self._post_to_ui(lambda error=e: self._screen_capture_failed(error))
                return
            self._post_to_ui(lambda: self._screen_capture_ready(text))

        threading.Thread(target=worker, daemon=True).start()

    def _screen_capture_ready(self, text):
        self.screen_capture_in_progress = False
        self.pending_screen_context = text
        self.screen_btn.config(state=tk.NORMAL)
        self.exec_btn.config(state=tk.NORMAL)
        self.status_lbl.config(text="● COSMOS SCREEN READY", fg=C["green"])
        self._print("sys", "[SCREEN CONTEXT READY] Ask a question about the captured screen.\n")

    def _screen_capture_failed(self, error):
        self.screen_capture_in_progress = False
        self.screen_btn.config(state=tk.NORMAL)
        self.exec_btn.config(state=tk.NORMAL)
        self.status_lbl.config(text="● COSMOS ONLINE", fg=C["green"])
        self._print("err", f"[SCREEN CAPTURE ERROR] {error}\n")

    def _toggle_microphone(self):
        if self.voice_enabled:
            self.voice_enabled = False
            self.isUserMicManuallyOff = True
            self.voice_enabled_event.clear()
            self.voice_ready_event.set()
            self.mic_btn.config(text=" MIC OFF ", fg=C["text"], bg="#08243a")
            self.status_lbl.config(text="● COSMOS ONLINE", fg=C["green"])
            return

        self.isUserMicManuallyOff = False
        self.voice_enabled = True
        self.voice_enabled_event.set()
        self.mic_btn.config(text=" MIC ON ", fg=C["bg_deep"], bg=C["accent"])
        self.status_lbl.config(text="● COSMOS MIC ON", fg=C["yellow"])

        def on_transcript(query):
            self._post_to_ui(
                lambda transcript=query: self._handle_voice_transcript(transcript)
            )

        def on_error(error):
            self._post_to_ui(lambda: self._microphone_failed(error))

        if self.voice_thread is None or not self.voice_thread.is_alive():
            self.voice_thread = threading.Thread(
                target=self._listen_for_voice,
                args=(on_transcript, on_error),
                daemon=True,
            )
            self.voice_thread.start()

    def _listen_for_voice(self, on_transcript, on_error):
        try:
            jarvis_voice.listen_for_input(
                self.voice_stop_event,
                self.voice_enabled_event,
                self.voice_ready_event,
                on_transcript,
                on_error,
            )
        except Exception as e:
            on_error(e)

    def _handle_voice_transcript(self, query):
        has_wake_word, command = jarvis_voice.parse_wake_command(query)
        ambiguous_wake = re.fullmatch(
            r"\s*(?:close|quit|exit|shut down)\s+(?:the\s+)?"
            r"(?:cosmo(?:s)?|kosmos)\s*[.!?]*\s*",
            query,
            re.IGNORECASE,
        ) is not None
        if jarvis_voice.is_close_command(query) and not ambiguous_wake:
            self._close_from_voice()
            return

        if ambiguous_wake:
            command = ""

        window_visible = self._is_window_visible()
        if not window_visible and not has_wake_word:
            self.voice_ready_event.set()
            return

        was_already_open = _is_popup_already_open

        if has_wake_word:
            self.show()

        if command:
            self._submit_query(command)
            return

        self._print("cosmos", "COSMOS: I'm listening, sir.\n\n")

        def acknowledge():
            global _is_popup_already_open
            try:
                if not was_already_open:
                    _is_popup_already_open = True
                    cosmos_speak("Namaste boss, welcome to your world again.")
                else:
                    cosmos_speak("Tell me sir, what you want to say?")
            finally:
                self.voice_ready_event.set()

        threading.Thread(target=acknowledge, daemon=True).start()

    def _close_from_voice(self):
        global _is_popup_already_open
        _is_popup_already_open = False
        self.voice_ready_event.clear()
        self.hide()

        def acknowledge():
            try:
                cosmos_speak("Ok boss, I will wait for you, until your next order.")
            finally:
                self.voice_ready_event.set()

        threading.Thread(target=acknowledge, daemon=True).start()

    def _microphone_failed(self, error):
        self._print("err", f"[MICROPHONE ERROR] {error}\n")

    def _show_reply(self, reply, prepared_audio=None):
        self.processing = False
        self._print("cosmos", f"COSMOS: {reply}\n\n")
        self.exec_btn.config(text=" EXECUTE ", state=tk.NORMAL)
        self.screen_btn.config(state=tk.NORMAL)
        self.status_lbl.config(text="● COSMOS ONLINE", fg=C["green"])

        def speak_reply():
            try:
                speech_target = extract_spoken_text(reply)
                cosmos_speak(speech_target, prepared_audio)
            finally:
                self.voice_ready_event.set()

        threading.Thread(target=speak_reply, daemon=True).start()

    # ─────────────────────────────────────────────────────────────────
    #  SHOW / HIDE
    # ─────────────────────────────────────────────────────────────────
    def show(self):
        global _is_popup_already_open
        _is_popup_already_open = True
        self.visible = True
        self.root.deiconify()
        self.root.attributes("-alpha", 0.96)
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.update_idletasks()

        # Force Windows foreground focus
        try:
            top_hwnd = user32.GetParent(self.root.winfo_id()) or self.root.winfo_id()
            user32.SetWindowTextW(top_hwnd, WINDOW_TITLE)
            user32.ShowWindow(top_hwnd, 5)  # SW_SHOW
            user32.SetForegroundWindow(top_hwnd)
            user32.SetWindowPos(top_hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)
        except Exception:
            hwnd = user32.FindWindowW(None, WINDOW_TITLE)
            if hwnd:
                user32.ShowWindow(hwnd, 5)
                user32.SetForegroundWindow(hwnd)
                user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)

        self.root.focus_force()
        self.entry.focus_set()
        self.entry.select_range(0, tk.END)
        if self._hud_animation_after is None:
            self._hud_animation_after = self.root.after(40, self._animate_hud)

    def hide(self):
        global _is_popup_already_open
        _is_popup_already_open = False
        self.visible = False
        self.root.focus_set()
        self.root.withdraw()

    def _is_window_visible(self):
        try:
            if hasattr(self, "root") and self.root and self.root.winfo_exists():
                return bool(self.visible and self.root.winfo_viewable())
        except Exception:
            pass
        return bool(self.visible)

    def toggle(self):
        if self._is_window_visible():
            self.hide()
        else:
            self.show()

    # ─────────────────────────────────────────────────────────────────
    #  DRAGGING
    # ─────────────────────────────────────────────────────────────────
    def _drag_start(self, e):
        self._dx = e.x
        self._dy = e.y

    def _drag_move(self, e):
        self.x += e.x - self._dx
        self.y += e.y - self._dy
        self.root.geometry(f"+{self.x}+{self.y}")

    # ─────────────────────────────────────────────────────────────────
    #  KEY BINDINGS
    # ─────────────────────────────────────────────────────────────────
    def _bind_events(self):
        self.root.bind("<Escape>", lambda e: self.hide())
        self.root.bind("<Control-Shift-c>", lambda e: self._copy_latest())

    def _post_to_ui(self, callback):
        self.ui_events.put(callback)

    def _process_ui_events(self):
        self.root.after(25, self._process_ui_events)
        while True:
            try:
                callback = self.ui_events.get_nowait()
            except queue.Empty:
                break
            callback()

    # ─────────────────────────────────────────────────────────────────
    #  GLOBAL HOTKEY THREAD
    #  Uses a low-level keyboard hook so quick Alt taps are not missed.
    # ─────────────────────────────────────────────────────────────────
    def _start_hotkey_thread(self):
        def _listen():
            WH_KEYBOARD_LL = 13
            WM_KEYDOWN = 0x0100
            WM_KEYUP = 0x0101
            WM_SYSKEYDOWN = 0x0104
            WM_SYSKEYUP = 0x0105
            VK_ALT_KEYS = {0x12, 0xA4, 0xA5}
            VK_CTRL_KEYS = {0x11, 0xA2, 0xA3}
            VK_SPACE = 0x20
            VK_TAB = 0x09
            VK_F4 = 0x73

            class KeyboardEvent(ctypes.Structure):
                _fields_ = [
                    ("vk_code", wintypes.DWORD),
                    ("scan_code", wintypes.DWORD),
                    ("flags", wintypes.DWORD),
                    ("time", wintypes.DWORD),
                    ("extra_info", ctypes.c_size_t),
                ]

            hook_proc_type = ctypes.WINFUNCTYPE(
                ctypes.c_ssize_t,
                ctypes.c_int,
                ctypes.c_size_t,
                ctypes.c_void_p,
            )
            get_module_handle = ctypes.windll.kernel32.GetModuleHandleW
            get_module_handle.argtypes = (wintypes.LPCWSTR,)
            get_module_handle.restype = ctypes.c_void_p
            pressed_keys = set()
            alt_press_time = 0.0
            alt_combo_used = False
            combo_was_down = False
            hook_handle = None

            def keyboard_hook(code, message, data):
                nonlocal alt_press_time, alt_combo_used, combo_was_down
                try:
                    if code == 0 and message in (
                        WM_KEYDOWN,
                        WM_SYSKEYDOWN,
                        WM_KEYUP,
                        WM_SYSKEYUP,
                    ):
                        event = ctypes.cast(
                            data, ctypes.POINTER(KeyboardEvent)
                        ).contents
                        key = event.vk_code
                        was_alt_down = bool(pressed_keys & VK_ALT_KEYS)
                        if message in (WM_KEYDOWN, WM_SYSKEYDOWN):
                            pressed_keys.add(key)
                        else:
                            pressed_keys.discard(key)

                        alt_down = bool(pressed_keys & VK_ALT_KEYS)
                        ctrl_down = bool(pressed_keys & VK_CTRL_KEYS)
                        space_down = VK_SPACE in pressed_keys
                        tab_down = VK_TAB in pressed_keys
                        f4_down = VK_F4 in pressed_keys

                        if alt_down and not was_alt_down:
                            alt_press_time = time.monotonic()
                            alt_combo_used = any(
                                pressed_key not in VK_ALT_KEYS
                                for pressed_key in pressed_keys
                            )
                        elif alt_down and key not in VK_ALT_KEYS:
                            alt_combo_used = True

                        combo_down = (
                            (alt_down and space_down)
                            or (ctrl_down and alt_down and not (tab_down or f4_down))
                            or (ctrl_down and space_down)
                        )
                        if combo_down and not combo_was_down:
                            self._post_to_ui(self.toggle)
                        combo_was_down = combo_down

                        if was_alt_down and not alt_down:
                            held = time.monotonic() - alt_press_time
                            if not alt_combo_used and 0.05 < held < 0.55:
                                self._post_to_ui(self.toggle)
                            alt_combo_used = False
                except Exception:
                    pass
                finally:
                    return user32.CallNextHookEx(hook_handle, code, message, data)

            hook_callback = hook_proc_type(keyboard_hook)
            user32.SetWindowsHookExW.argtypes = (
                ctypes.c_int,
                hook_proc_type,
                ctypes.c_void_p,
                wintypes.DWORD,
            )
            user32.SetWindowsHookExW.restype = ctypes.c_void_p
            user32.CallNextHookEx.argtypes = (
                ctypes.c_void_p,
                ctypes.c_int,
                ctypes.c_size_t,
                ctypes.c_void_p,
            )
            user32.CallNextHookEx.restype = ctypes.c_ssize_t
            hook_handle = user32.SetWindowsHookExW(
                WH_KEYBOARD_LL,
                hook_callback,
                get_module_handle(None),
                0,
            )
            if not hook_handle:
                error = ctypes.WinError(ctypes.get_last_error())
                self._post_to_ui(
                    lambda error=error: self._print(
                        "err", f"[HOTKEY ERROR] {error}\n"
                    )
                )
                return

            message = wintypes.MSG()
            while not self.voice_stop_event.is_set():
                result = user32.GetMessageW(ctypes.byref(message), None, 0, 0)
                if result == -1:
                    error = ctypes.WinError(ctypes.get_last_error())
                    self._post_to_ui(
                        lambda error=error: self._print(
                            "err", f"[HOTKEY ERROR] {error}\n"
                        )
                    )
                    break
                if result == 0:
                    break
                user32.TranslateMessage(ctypes.byref(message))
                user32.DispatchMessageW(ctypes.byref(message))

            user32.UnhookWindowsHookEx(hook_handle)

        t = threading.Thread(target=_listen, daemon=True)
        t.start()

    # ─────────────────────────────────────────────────────────────────
    #  RUN
    # ─────────────────────────────────────────────────────────────────
    def run(self):
        # Display immediately on launch
        self.show()
        self.root.after(25, self._process_ui_events)
        self.root.after(0, self._toggle_microphone)

        threading.Thread(
            target=cosmos_speak,
            args=("Namaste boss, welcome to your world again.",),
            daemon=True,
        ).start()
        self.root.mainloop()


# ═══════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # Also handle an older instance that did not create the singleton mutex.
    existing = user32.FindWindowW(None, WINDOW_TITLE)
    if existing:
        user32.ShowWindow(existing, 5)
        user32.SetForegroundWindow(existing)
        user32.SetWindowPos(existing, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)
        sys.exit(0)

    overlay = CosmosOverlay()
    overlay.run()
