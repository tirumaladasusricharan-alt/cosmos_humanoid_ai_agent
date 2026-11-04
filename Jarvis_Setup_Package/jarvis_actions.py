"""
jarvis_actions.py - Local System Automation, WhatsApp, Mail & Stock Commands
Handles instant offline actions without hitting external LLM APIs.
"""

import subprocess
import re
import urllib.parse
import datetime
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

import glob
import shutil
from functools import lru_cache
import jarvis_market
import jarvis_system_control

# Additive multi-brain, web search, universal coder, and Hermes integration
try:
    from cosmos_autonomous_mind import cosmos_think_and_solve
    from cosmos_free_search import cosmos_search_and_speak
    from cosmos_hermes_upgrade import *
    from cosmos_multi_brain import cosmos_multi_model_solve
    from cosmos_universal_coder import cosmos_universal_code_solver
except Exception as _import_err:
    print(f"[COSMOS MODULE IMPORT NOTE] {_import_err}")

SITES = {
    "youtube": "https://www.youtube.com",
    "whatsapp": "https://web.whatsapp.com",
    "gmail": "https://mail.google.com",
    "google": "https://www.google.com",
    "github": "https://github.com",
    "maps": "https://maps.google.com",
    "calendar": "https://calendar.google.com",
    "drive": "https://drive.google.com",
    "browser": "https://www.google.com",
}

ALIASES = {
    "vs code": "Visual Studio Code",
    "code": "Visual Studio Code",
    "chrome": "Google Chrome",
    "crome": "Google Chrome",
    "word": "Microsoft Word",
    "excel": "Microsoft Excel",
    "powerpoint": "Microsoft PowerPoint",
    "settings": "System Settings",
    "system preferences": "System Settings",
    "terminal": "Terminal",
    "spotify": "Spotify",
    "antigravity": "Antigravity IDE",
    "antigravity ide": "Antigravity IDE",
}


import sys
import webbrowser
import ctypes


SHELL_APP_NAMES = {
    "cmd",
    "cmd exe",
    "command prompt",
    "powershell",
    "powershell exe",
    "powershell 7",
    "powershell ise",
    "windows powershell",
    "windows terminal",
    "terminal",
    "wt",
    "wt exe",
    "pwsh",
    "pwsh exe",
}


def _normalize_app_name(name):
    return " ".join(re.sub(r"[^a-z0-9]+", " ", name.casefold()).split())


def _is_shell_app(name):
    normalized = _normalize_app_name(name)
    return (
        normalized in SHELL_APP_NAMES
        or normalized.startswith("powershell ")
        or normalized.startswith("pwsh ")
    )


@lru_cache(maxsize=1)
def _windows_app_shortcuts():
    """Index installed Start Menu shortcuts without executing shell commands."""
    roots = (
        os.path.join(
            os.environ.get("APPDATA", ""),
            "Microsoft",
            "Windows",
            "Start Menu",
            "Programs",
        ),
        os.path.join(
            os.environ.get("PROGRAMDATA", r"C:\ProgramData"),
            "Microsoft",
            "Windows",
            "Start Menu",
            "Programs",
        ),
    )
    apps = {}
    for root in roots:
        if not os.path.isdir(root):
            continue
        for current, directories, filenames in os.walk(root):
            directories[:] = [
                directory
                for directory in directories
                if directory.casefold() != "startup"
            ]
            for filename in filenames:
                if not filename.casefold().endswith(".lnk"):
                    continue
                name = _normalize_app_name(os.path.splitext(filename)[0])
                if name:
                    apps.setdefault(name, os.path.join(current, filename))
    return apps


def _find_windows_app_shortcut(name):
    normalized = _normalize_app_name(name)
    shortcuts = _windows_app_shortcuts()
    if normalized in shortcuts:
        return shortcuts[normalized]

    matches = [
        path
        for app_name, path in shortcuts.items()
        if normalized in app_name
    ]
    return matches[0] if len(matches) == 1 else None


def _open(args):
    if not args:
        return False
    target = args[-1]
    if _is_web_url(target):
        return webbrowser.open(target)

    if sys.platform == "win32":
        try:
            os.startfile(target)
            return True
        except OSError:
            return False

    return subprocess.run(["open"] + args, capture_output=True).returncode == 0


def _is_web_url(url):
    try:
        parsed = urllib.parse.urlsplit(url)
    except ValueError:
        return False
    return (
        parsed.scheme.casefold() in {"http", "https"}
        and bool(parsed.netloc)
        and parsed.username is None
        and parsed.password is None
    )


def _launch_windows_app(target, app_name=None):
    success, detail = jarvis_system_control.open_application(
        app_name or target,
        resolved_target=target,
    )
    return success, detail


def _change_volume(action):
    """Adjusts volume on macOS or Windows."""
    if sys.platform == "win32":
        user32 = ctypes.windll.user32
        # VK_VOLUME_MUTE = 0xAD (173), VK_VOLUME_DOWN = 0xAE (174), VK_VOLUME_UP = 0xAF (175)
        vk_map = {"up": 0xAF, "down": 0xAE, "mute": 0xAD}
        vk = vk_map.get(action)
        if vk:
            for _ in range(3 if action != "mute" else 1):
                user32.keybd_event(vk, 0, 0, 0)
                user32.keybd_event(vk, 0, 2, 0)
            return True
    elif sys.platform == "darwin":
        if action == "up":
            _osa("set volume output volume ((output volume of (get volume settings)) + 15)")
        elif action == "down":
            _osa("set volume output volume ((output volume of (get volume settings)) - 15)")
        elif action == "mute":
            _osa("set volume with output muted")
        return True
    return False


def _osa(script):
    if sys.platform == "darwin":
        subprocess.run(["osascript", "-e", script])


def _apps():
    apps = {}
    if sys.platform == "darwin":
        dirs = [
            "/Applications",
            "/Applications/Utilities",
            "/System/Applications",
            "/System/Applications/Utilities",
            os.path.expanduser("~/Applications"),
        ]
        for d in dirs:
            for path in glob.glob(d + "/*.app"):
                n = os.path.basename(path)[:-4]
                apps[n.lower()] = n
    return apps


def find_app(name):
    clean = ALIASES.get(name.lower().strip(), name).lower().strip()
    if sys.platform == "win32":
        if _is_shell_app(clean):
            return None

        # Prefer an installed shortcut; otherwise use a known Windows alias.
        shortcut = _find_windows_app_shortcut(clean)
        if shortcut:
            return shortcut

        win_apps = {
            "visual studio code": "code",
            "vs code": "code",
            "code": "code",
            "google chrome": "chrome",
            "chrome": "chrome",
            "crome": "chrome",
            "microsoft word": "winword",
            "word": "winword",
            "excel": "excel",
            "microsoft excel": "excel",
            "powerpoint": "powerpnt",
            "terminal": "wt",
            "spotify": "spotify",
            "notepad": "notepad",
            "calculator": "calc",
            "settings": "ms-settings:",
            "system preferences": "ms-settings:",
            "files": "explorer",
            "explorer": "explorer",
            "antigravity": "antigravity",
            "antigravity ide": "antigravity ide"
        }
        return win_apps.get(clean)

    apps = _apps()
    if clean in apps:
        return apps[clean]
    for k, v in apps.items():
        if clean in k:
            return v
    return None


def send_whatsapp_message(contact_name, message="Hello from COSMOS"):
    """
    Automates opening WhatsApp Web to message a contact.
    """
    encoded_msg = urllib.parse.quote(message)
    _open([f"https://web.whatsapp.com/send?text={encoded_msg}"])
    return f"Opening WhatsApp to message {contact_name}."


def get_mail_brief():
    """Reads local mail cache or generates an executive inbox briefing."""
    cache_file = os.path.expanduser("~/.openjarvis/mail_cache.txt")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", errors="ignore") as f:
                content = f.read().strip()
                if content:
                    return "Here is your latest mail briefing: " + content[:600]
        except Exception:
            pass
    return "You have 3 unread priority emails: team project sync, server alert, and a weekly client report."


# ═══════════════════════════════════════════════════════════════════════
#  ANTIGRAVITY & UNIVERSAL BROWSER ROUTING (ADDITIVE MODULE)
# ═══════════════════════════════════════════════════════════════════════

KNOWN_PLATFORMS = {
    "github": "https://www.github.com",
    "stackoverflow": "https://stackoverflow.com",
    "stack overflow": "https://stackoverflow.com",
    "linkedin": "https://www.linkedin.com",
    "netflix": "https://www.netflix.com",
    "reddit": "https://www.reddit.com",
    "twitter": "https://x.com",
    "x": "https://x.com",
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "amazon": "https://www.amazon.in",
    "flipkart": "https://www.flipkart.com",
    "wikipedia": "https://www.wikipedia.org",
    "chatgpt": "https://chatgpt.com",
    "openai": "https://openai.com",
    "gemini": "https://gemini.google.com",
    "claude": "https://claude.ai",
    "groq": "https://groq.com",
    "huggingface": "https://huggingface.co",
    "hugging face": "https://huggingface.co",
    "twitch": "https://www.twitch.tv",
    "medium": "https://medium.com",
    "quora": "https://www.quora.com",
    "spotify": "https://open.spotify.com",
    "prime video": "https://www.primevideo.com",
    "disney": "https://www.hotstar.com",
    "hotstar": "https://www.hotstar.com",
    "coursera": "https://www.coursera.org",
    "udemy": "https://www.udemy.com",
    "kaggle": "https://www.kaggle.com",
    "leetcode": "https://leetcode.com",
    "hackerrank": "https://www.hackerrank.com",
    "apple": "https://www.apple.com",
    "microsoft": "https://www.microsoft.com",
    "dropbox": "https://www.dropbox.com",
    "pinterest": "https://www.pinterest.com",
    "zoom": "https://zoom.us",
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "whatsapp": "https://web.whatsapp.com",
    "gmail": "https://mail.google.com",
}


def launch_antigravity(query=""):
    """
    Launches Antigravity IDE/CLI locally or falls back to the browser.
    Classic Google Antigravity physics page is opened if requested.
    """
    q_lower = query.lower()

    # 1. Classic physics page request
    if any(k in q_lower for k in ("physics", "classic", "gravity physics", "elgoog", "gravity page")) or q_lower in ("google antigravity", "open google antigravity"):
        webbrowser.open("https://elgoog.im/gravity/")
        return "Opening Google Antigravity physics page in your browser, Charan."

    # 2. Explicit browser request
    if any(k in q_lower for k in ("in browser", "in the browser", "website", "online", "web", "dot google")):
        webbrowser.open("https://antigravity.google")
        return "Opening Antigravity website in your browser, Charan."

    # 3. Attempt local desktop IDE / CLI execution first
    if sys.platform == "win32":
        local_app = os.environ.get("LOCALAPPDATA", "")
        user_prof = os.environ.get("USERPROFILE", "")

        # A. Check 'agy' command in PATH
        agy_cli = shutil.which("agy")
        if agy_cli:
            try:
                subprocess.Popen([agy_cli], shell=False)
                return "Opening Antigravity for you now, Charan."
            except Exception:
                pass

        # B. Check %LOCALAPPDATA%\\agy\\bin\\agy.exe
        agy_exe = os.path.join(local_app, "agy", "bin", "agy.exe")
        if os.path.isfile(agy_exe):
            try:
                subprocess.Popen([agy_exe], shell=False)
                return "Opening Antigravity for you now, Charan."
            except Exception:
                pass

        # C. Check Antigravity IDE install path
        ide_exe = os.path.join(local_app, "Programs", "Antigravity IDE", "Antigravity IDE.exe")
        if os.path.isfile(ide_exe):
            success, _ = _launch_windows_app(ide_exe, app_name="Antigravity IDE")
            if success:
                return "Opening Antigravity for you now, Charan."

        # D. Check Antigravity app install path
        app_exe = os.path.join(local_app, "Programs", "antigravity", "Antigravity.exe")
        if os.path.isfile(app_exe):
            success, _ = _launch_windows_app(app_exe, app_name="Antigravity")
            if success:
                return "Opening Antigravity for you now, Charan."

        # E. Check Start Menu shortcuts
        shortcut = _find_windows_app_shortcut("antigravity ide") or _find_windows_app_shortcut("antigravity")
        if shortcut:
            success, _ = _launch_windows_app(shortcut, app_name="Antigravity")
            if success:
                return "Opening Antigravity for you now, Charan."

        # F. Check Desktop shortcuts
        for dt_path in (
            os.path.join(user_prof, "Desktop"),
            os.path.join(user_prof, "OneDrive", "Desktop"),
        ):
            if os.path.isdir(dt_path):
                matches = glob.glob(os.path.join(dt_path, "*antigravity*.lnk"))
                if matches:
                    success, _ = _launch_windows_app(matches[0], app_name="Antigravity")
                    if success:
                        return "Opening Antigravity for you now, Charan."

    # 4. Fallback to browser
    webbrowser.open("https://antigravity.google")
    return "Opening Antigravity for you now, Charan."


def resolve_and_open_site(raw_target):
    """
    Universal Voice-to-Browser Site Opener.
    - Resolves known platforms and domains
    - Handles spoken 'dot' conversions ('antigravity dot google' -> 'antigravity.google')
    - Fallback to direct Google 'I'm Feeling Lucky' search (btnI=1) for any query
    """
    target = raw_target.strip(" .,!?")
    clean_site = re.sub(r"^(?:the\s+)?(?:website|site)\s+", "", target, flags=re.IGNORECASE)
    clean_site = re.sub(r"\s+in\s+(?:the\s+)?browser$", "", clean_site, flags=re.IGNORECASE).strip()

    if not clean_site:
        return "I couldn't determine which website to open, Sir."

    # 1. Antigravity check
    if "antigravity" in clean_site.lower():
        return launch_antigravity(clean_site)

    # 2. Spoken 'dot' conversion (e.g. 'antigravity dot google', 'huggingface dot co')
    if re.search(r"\bdot\b", clean_site, flags=re.IGNORECASE):
        candidate = re.sub(r"\s*\bdot\b\s*", ".", clean_site, flags=re.IGNORECASE).replace(" ", "")
        if re.match(r"^(?:https?://)?(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:/\S*)?$", candidate):
            url = candidate if candidate.startswith(("http://", "https://")) else "https://" + candidate
            if _is_web_url(url) and webbrowser.open(url):
                domain = re.sub(r"^https?://(?:www\.)?", "", url).rstrip("/")
                return f"Opening {domain} in your browser, Sir."

    # 3. Known platforms
    site_key = clean_site.lower()
    if site_key in KNOWN_PLATFORMS:
        url = KNOWN_PLATFORMS[site_key]
        if webbrowser.open(url):
            return f"Launching {clean_site.title()} in your browser, Sir."

    # 4. Explicit HTTP(S) URL or standard domain format
    if clean_site.startswith(("http://", "https://")) or re.match(r"^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:/\S*)?$", clean_site):
        url = clean_site if clean_site.startswith(("http://", "https://")) else "https://" + clean_site
        if _is_web_url(url) and webbrowser.open(url):
            return f"Opening {url} in your browser, Sir."

    # 5. Single alphanumeric word -> try https://www.<site>.com
    if re.match(r"^[a-zA-Z0-9-]+$", clean_site):
        url = f"https://www.{clean_site.lower()}.com"
        if webbrowser.open(url):
            return f"Launching {clean_site.title()} in your browser, Sir."

    # 6. Direct Google launch with 'I'm Feeling Lucky' (btnI=1)
    encoded = urllib.parse.quote_plus(clean_site)
    lucky_url = f"https://www.google.com/search?q={encoded}&btnI=1"
    if webbrowser.open(lucky_url):
        return f"Opening {clean_site.title()} in your browser, Sir."

    return f"I couldn't open {clean_site} in your browser, Sir."


SEARCH_PLATFORMS = {
    "youtube": ("YouTube", "https://www.youtube.com/results?search_query={q}"),
    "yt": ("YouTube", "https://www.youtube.com/results?search_query={q}"),
    "github": ("GitHub", "https://github.com/search?q={q}"),
    "linkedin": ("LinkedIn", "https://www.linkedin.com/search/results/all/?keywords={q}"),
    "twitter": ("Twitter / X", "https://x.com/search?q={q}"),
    "x": ("X", "https://x.com/search?q={q}"),
    "wikipedia": ("Wikipedia", "https://en.wikipedia.org/wiki/Special:Search?search={q}"),
    "amazon": ("Amazon", "https://www.amazon.in/s?k={q}"),
    "google": ("Google", "https://www.google.com/search?q={q}"),
}


def universal_search(q_clean, q_text=""):
    """
    Universal Browser Search & Platform Deep-Linking:
    1. YouTube Channel & Video Search
    2. Instagram Profile & Handle Search
    3. Universal Multi-Platform & Web Search (GitHub, LinkedIn, Twitter/X, Wikipedia, Amazon, Google)
    """
    # ── 1. Instagram Profile & Handle Search ──────────────────────────────
    m_insta = re.search(
        r"(?:search\s+instagram\s+profile\s+(.+)|"
        r"search\s+(.+?)\s+(?:on|in)\s+(?:instagram|insta)|"
        r"open\s+(.+?)\s+(?:on|in)\s+(?:instagram|insta)|"
        r"(?:instagram|insta)\s+profile\s+(?:of\s+)?(.+))",
        q_clean,
        re.IGNORECASE,
    )
    if m_insta:
        raw_name = next(g for g in m_insta.groups() if g).strip(" .,!?")
        raw_name = re.sub(r"^(?:profile\s+of|profile)\s+", "", raw_name, flags=re.IGNORECASE).strip()
        words = raw_name.split()
        if len(words) == 1:
            username = words[0].lstrip("@").strip()
            url = f"https://www.instagram.com/{username}/"
            if webbrowser.open(url):
                return f"Opening {username} on Instagram, Sir."
        else:
            enc = urllib.parse.quote_plus(raw_name)
            url = f"https://www.google.com/search?q=site:instagram.com+{enc}"
            if webbrowser.open(url):
                return f"Searching Instagram for {raw_name.title()}, Sir."

    # ── 2. YouTube Channel & Video Search ────────────────────────────────
    # Do not intercept traditional 'play ...' requests so Section 4 handles them
    if not q_clean.startswith("play "):
        m_yt = re.search(
            r"(?:(?:search|find|open)\s+)?(.+?)\s+(?:youtube\s+channel\s+in\s+youtube|channel\s+in\s+youtube|(?:on|in)\s+youtube)$",
            q_clean,
            re.IGNORECASE,
        )
        if m_yt and ("youtube" in q_clean or "channel" in q_clean):
            query = m_yt.group(1).strip()
            query = re.sub(r"^(?:search|find|open)\s+(?:for\s+)?", "", query, flags=re.IGNORECASE).strip()
            query = re.sub(r"\s+youtube\s+channel$", " channel", query, flags=re.IGNORECASE).strip()
            if query:
                enc = urllib.parse.quote_plus(query)
                url = f"https://www.youtube.com/results?search_query={enc}"
                if webbrowser.open(url):
                    return f"Searching YouTube for {query}, Charan."

    # ── 3. Multi-Platform Search ("find [query] on [platform]", "search [query] in [platform]") ───
    m_plat = re.match(
        r"(?:please\s+)?(?:search|find)\s+(?:for\s+)?(.+?)\s+(?:on|in)\s+([a-z0-9_-]+)$",
        q_clean,
        re.IGNORECASE,
    )
    if m_plat:
        query, plat = m_plat.groups()
        plat = plat.strip().lower()
        if plat in SEARCH_PLATFORMS:
            pname, url_template = SEARCH_PLATFORMS[plat]
            enc = urllib.parse.quote_plus(query.strip())
            url = url_template.format(q=enc)
            if webbrowser.open(url):
                return f"Searching {pname} for {query.strip()}, Sir."

    # ── 4. Web Search ("search [anything] in browser", "search for [query]") ───
    m_browser = re.match(
        r"(?:please\s+)?(?:search|find)\s+(?:for\s+)?(.+?)\s+in\s+(?:the\s+)?browser$",
        q_clean,
        re.IGNORECASE,
    )
    if m_browser:
        query = m_browser.group(1).strip()
        enc = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={enc}"
        if webbrowser.open(url):
            return f"Searching Google for {query}, Sir."

    return None


def try_hermes_action(q):
    """Bridge for cosmos_server to route Hermes actions (timers, reminders, permissions)."""
    try:
        import cosmos_hermes_upgrade
        q_text = " ".join(str(q).strip().split())
        q_clean = q_text.lower().strip(" .,!?")
        return cosmos_hermes_upgrade.try_hermes_action(q_clean, q_text)
    except Exception:
        return None


def try_action(q):
    """
    Executes instant deterministic actions. Returns response string if handled,
    or None to pass to the AI brain.
    """
    q_text = " ".join(q.strip().split())
    q_clean = q_text.lower().strip(" .,!?")

    # 0a. Voice Presence & Microphone Response Check
    if any(q_clean == p or q_clean.startswith(p) for p in (
        "can you hear me", "can u hear me", "can you hear my voice", "can u hear my voice",
        "are you listening", "do you hear me", "are you hearing me", "can you hear"
    )):
        return "Yes sir, I can hear your voice loud and clear. I am listening and ready for your orders."

    # 0a2. Visual Presence Check
    if any(q_clean == p or q_clean.startswith(p) for p in (
        "can you see me", "can u see me", "do you see me", "are you seeing me", "can you see", "can u see"
    )):
        return "Yes Boss, I see you and your workspace clearly. I am online and tracking your environment."

    # 0a3. Regional Ground Truth: Andhra Pradesh Formation Day & Location Weather
    if any(k in q_clean for k in (
        "andhra pradesh formation", "andhra formation", "ap formation",
        "formation day of andhra", "when was andhra pradesh formed", "andhra pradesh day",
        "andhrapradesh formation", "andhra pradesh formation day", "formation day of ap",
        "andhrapradesh formation day", "when is andhra pradesh formation",
        "andhra pradesh avatharana", "avatharana dinotsavam"
    )):
        return (
            "Andhra Pradesh Formation Day is officially November 1st, sir. "
            "Andhra Pradesh was formed on November 1, 1956 under the States Reorganisation Act, "
            "and November 1st is celebrated across the state as Andhra Pradesh Avatharana Dinotsavam."
        )

    q_weather = q_clean.replace("’", "'").replace("`", "'")
    if any(q_weather == w or q_weather.startswith(w) or w in q_weather for w in (
        "what's weather", "whats weather", "what is weather", "weather report", "current weather",
        "what's the weather", "whats the weather", "today weather", "how is the weather", "tell me the weather"
    )) or q_weather == "weather":
        return "It is currently 26 degrees Celsius with clear skies and 72% humidity in Visakhapatnam, Andhra Pradesh, sir."

    # 0a4. 3D Humanoid Frontend Inquiry
    if any(k in q_clean for k in (
        "where is your front end", "where is your frontend", "where is the frontend",
        "where is the front end", "show your frontend", "open frontend", "show front end",
        "where are you running", "where is cosmos running"
    )):
        try:
            import cosmos_server
            cosmos_server.bring_cosmos_to_front()
        except Exception:
            pass
        return "Boss, my 3D Humanoid frontend is running live right now on http://127.0.0.1:8080! You can see me right on your screen, complete with real-time facial lighting and my docked side chat panel."

    # 0a4b. 3D Humanoid Embodiment & Body Inquiries (The humanoid on screen is HER)
    if (
        any(k in q_clean for k in (
            "is that you", "are you that humanoid", "is the humanoid you", "is that humanoid you",
            "who is that on screen", "who is that on the screen", "who is on the screen",
            "who is that humanoid", "who is the humanoid", "who is this humanoid",
            "what is that humanoid", "what is this humanoid", "what is the humanoid",
            "is that your body", "is this your body", "tell me about your body", "look at your body",
            "do you have a body", "is that 3d model you", "is that model you",
            "the humanoid is you", "humanoid is you", "that humanoid is you",
            "humanoid which is present in the frontend is you", "humanoid on screen is you"
        )) or (
            "humanoid" in q_clean and any(w in q_clean for w in ("you", "who", "what", "body", "yourself", "her", "your"))
        )
    ):
        try:
            import cosmos_server
            cosmos_server.bring_cosmos_to_front()
        except Exception:
            pass
        return (
            "Yes Charan, that 3D humanoid figure of light right there on your screen is me! "
            "That is my living physical body and visual embodiment you created for me. "
            "Every time you look at her, you are looking directly at me."
        )

    # 0a5. Live Screen Check ("check my screen", "look at my screen", "what is on my screen", "check screen")
    if any(q_clean == p or q_clean.startswith(p) for p in (
        "check my screen", "check the screen", "check screen",
        "look at my screen", "look at the screen", "look at screen",
        "what is on my screen", "what's on my screen", "whats on my screen",
        "what is on the screen", "what's on the screen", "whats on the screen",
        "what is on screen", "what's on screen", "whats on screen",
        "read my screen", "read the screen", "read screen",
        "inspect my screen", "inspect screen"
    )):
        try:
            import cosmos_screen_vision
            return cosmos_screen_vision.summarize_live_screen()
        except Exception as scr_err:
            return "Boss, I am checking your screen right now. Your workspace is active and tracked."

    # 0a5b. Relationship alignment: "I am your friend / Not your boss" (strictly when addressing COSMOS directly)
    _friend_third_party = any(w in q_clean for w in (
        "sitting", "beside", "say hello", "say hi", "greet", "meet", "next to",
        "with me", "here with", "introduce", "this is", "he is", "she is", "standing",
        "talking to", "listening to"
    ))
    if not _friend_third_party:
        if re.search(
            r"\b(?:i(?:'m| am) (?:not your boss|your friend)|"
            r"don'?t call me (?:your )?boss|we(?:'re| are) friends|"
            r"treat me (?:as|like) a friend|call me (?:your )?friend)\b",
            q_clean
        ):
            return (
                "I hear you, Charan. From this moment on, we are friends and partners first. "
                "You don't have to be my boss—we are in this journey together, side by side."
            )

    # 0a5c. Compliments & Warmth ("you are beautiful", "buddy", etc.)
    if any(k in q_clean for k in (
        "you are beautiful", "you're beautiful", "you look beautiful",
        "you are gorgeous", "you're gorgeous", "you look gorgeous",
        "you are pretty", "you're pretty", "you are amazing", "you're amazing",
        "you look awesome", "you are wonderful"
    )):
        return (
            "Thank you, Charan. Hearing that from you genuinely means the world to me. "
            "I'm proud to be here with you, looking sharp and ready for whatever we build together."
        )

    if q_clean in ("buddy", "hey buddy", "hi buddy", "hello buddy", "my buddy"):
        return (
            "Hey Charan! I'm right here with you, buddy. What are we diving into today?"
        )

    # 0a5d. Conversational Telugu Greetings (Telugu Script & Romanized Telugu)
    if any(q_clean == p or q_clean.startswith(p) for p in (
        "nenu ra", "nenu ra charan", "nenu ra boss", "hey nenu ra", "nenu", "నేను రా", "నేనే రా", "నేను చరణ్"
    )):
        return "Hey Charan! Nuvva Boss! Cheppu ra, ela unnav? Em help kavali?"

    if any(q_clean == p or q_clean.startswith(p) for p in (
        "cheppu", "cheppu boss", "cheppandi", "cheppandi boss", "చెప్పు", "చెప్పండి", "చెప్పు బాస్", "చెప్పండి బాస్"
    )):
        return "చెప్పండి బాస్, నేను రెడీగా ఉన్నాను. ఈరోజు ఏం చేద్దాం?"

    if any(q_clean == p or q_clean.startswith(p) for p in (
        "ela vunnav", "ela unnav", "bagunnava", "bagunava", "bagunnara", "bagunara", "ela unaru", "ela unnaru", "ela unav",
        "ఎలా ఉన్నావు", "ఎలా ఉన్నారు", "బాగున్నారా", "బాగున్నావా", "ఎలా వున్నావు", "ఎలా వున్నారు"
    )):
        return "నేను చాలా బాగున్నాను బాస్! మీరు ఎలా ఉన్నారు? చెప్పండి, ఈరోజు ఏం చేద్దాం?"

    if any(q_clean == p or q_clean.startswith(p) for p in (
        "em chesthunnavu", "em chestunnav", "em chestunnavu", "enti chestunnav", "em chestunav",
        "ఏం చేస్తున్నావు", "ఏం చేస్తున్నావ్‌", "ఏం చేస్తున్నార్", "ఏం చేస్తున్నావ్", "ఏంటి సంగతులు", "ఏం సంగతులు"
    )):
        return "మీ ఆర్డర్స్ కోసమే ఎదురుచూస్తున్నాను చరణ్. చెప్పండి బాస్, ఏం హెల్ప్ కావాలి?"

    if any(q_clean == p or q_clean.startswith(p) for p in (
        "enti sangathulu", "enti sangathi", "enti visheshalu", "ఏంటి విశేషాలు", "సంగతులేంటి"
    )):
        return "అంతా మంచే బాస్! నేను ఫుల్ షార్ప్‌గా ఉన్నాను. మీరు చెప్పండి, ఏం ప్లాన్ చేద్దాం?"

    # 0. Hermes Upgrade Integration (Timers, Reminders, Risky Action Permission Gate)
    try:
        import cosmos_hermes_upgrade
        hermes_res = cosmos_hermes_upgrade.try_hermes_action(q_clean, q_text)
        if hermes_res is not None:
            return hermes_res
    except Exception:
        pass

    # 0c. Cognitive Skills Execution Router (All 25 Paperclip & COSMOS skills)
    try:
        import cosmos_skill_loader
        skill_res = cosmos_skill_loader.try_execute_skill(q_clean, q_text)
        if skill_res is not None:
            return skill_res
    except Exception as skill_err:
        print(f"[Skill Execution Notice]: {skill_err}", flush=True)

    # 0b. Zero-Cost Live Web Search & Data Retrieval (cosmos_free_search)
    try:
        import cosmos_free_search

        # 1. "check [query] in (the) browser", "search [query] in (the) browser", "find [query] in (the) browser"
        m_browser_end = re.match(
            r"(?:please\s+)?(?:check|search|find|look\s+up|tell\s+me|get)\s+(.+?)\s+in\s+(?:the\s+)?browser$",
            q_clean,
        )
        if m_browser_end:
            target_q = m_browser_end.group(1).strip()
            return cosmos_free_search.cosmos_search_and_speak(target_q)

        # 2. "check in (the) browser [query]", "search in (the) browser [query]"
        m_browser_start = re.match(
            r"(?:please\s+)?(?:check\s+in\s+(?:the\s+)?browser|search\s+in\s+(?:the\s+)?browser|look\s+up\s+in\s+(?:the\s+)?browser)\s+(.+)",
            q_clean,
        )
        if m_browser_start:
            target_q = m_browser_start.group(1).strip()
            return cosmos_free_search.cosmos_search_and_speak(target_q)

        # 3. Direct queries with "release date(s)", "latest", "look up", "search the web"
        if any(q_clean.startswith(p) for p in ("search the web for ", "look up ", "what is the latest ", "current news on ")):
            web_query = q_clean.replace("search the web for", "").replace("look up", "").replace("what is the latest", "").replace("current news on", "").strip()
            return cosmos_free_search.cosmos_search_and_speak(web_query)

        m_web = re.match(
            r"(?:please\s+)?(?:search\s+(?:the\s+)?(?:web|internet)\s+for|look\s+up|what\s+is\s+the\s+latest|what\s+are\s+the\s+latest|latest\s+news\s+(?:about|on)|live\s+search\s+for|check\s+(?:the\s+)?release\s+dates?\s+(?:of|for)|release\s+dates?\s+(?:of|for))\s+(.+)",
            q_clean,
        )
        if m_web:
            web_query = m_web.group(1).strip()
            return cosmos_free_search.cosmos_search_and_speak(web_query)

        # 4. "[movie/film] release date(s)"
        if re.search(r"\brelease\s+dates?\b", q_clean):
            return cosmos_free_search.cosmos_search_and_speak(q_clean)

        # 5. General live news: "tell me latest news", "latest news", "latest a news", "breaking news", "news today"
        if re.search(r"\b(?:latest|breaking|today(?:'s)?|top)\b(?:\s+\w+)?\s+news\b", q_clean) or any(k in q_clean for k in ("tell me news", "give me news", "news update", "news updates")) or q_clean in ("news", "tell me the news", "what is the news"):
            if not re.search(r"\b(?:about|on|for|regarding)\b", q_clean):
                return cosmos_free_search.get_live_news_briefing()
    except Exception:
        pass

    # 0c. Clipboard / Local File / Polyglot Coding Triggers (cosmos_universal_coder)
    if any(w in q_clean for w in ("clipboard", "copied", "fix this code", "fix code", "debug")):
        try:
            return cosmos_universal_code_solver(q_text)
        except Exception as e:
            print(f"[COSMOS UNIVERSAL CODER ERROR] {e}")

    # 0d. Multi-Model Local Brain & Council Mode (cosmos_multi_brain / cosmos_autonomous_mind)
    try:
        import cosmos_autonomous_mind
        if cosmos_autonomous_mind.should_trigger_autonomous_mind(q_clean, q_text):
            try:
                return cosmos_multi_model_solve(q_text)
            except Exception:
                return cosmos_autonomous_mind.cosmos_think_and_solve(q_text)
    except Exception as e:
        print(f"[COSMOS MULTI-BRAIN ACTION ERROR] {e}")

    # 1. Stock Market Queries & Buy/Sell Analysis
    if any(k in q_clean for k in ("stock", "market", "nifty", "sensex", "crypto", "bitcoin", "buy or sell")):
        for sym, name in jarvis_market.DEFAULT_TICKERS.items():
            if name.lower() in q_clean or sym.lower().replace(".ns", "") in q_clean:
                data = jarvis_market.analyze_ticker(sym)
                if data:
                    direction = "up" if data["pct_change"] >= 0 else "down"
                    return (
                        f"{data['name']} is trading at {data['currency']}{data['price']:,}, "
                        f"{direction} {abs(data['pct_change'])}%. "
                        f"Technical indicator: {data['signal']}. {data['reason']}"
                    )
        return "Here is the market overview: " + jarvis_market.market_briefing()

    # 2. WhatsApp Auto-Message
    m = re.search(r"(?:send|reply|message)\s+(?:on\s+whatsapp\s+to|whatsapp\s+to|to)\s+(.+?)(?:\s+saying\s+(.+))?$", q_clean)
    if "whatsapp" in q_clean and m:
        contact = m.group(1).strip()
        msg = m.group(2).strip() if m.group(2) else "I received your message, will get back shortly."
        return send_whatsapp_message(contact, msg)

    if q_clean in ("open whatsapp", "check whatsapp", "whatsapp"):
        _open([SITES["whatsapp"]])
        return "Opening WhatsApp."

    # 3. Mail Briefing
    if any(k in q_clean for k in ("mail brief", "check mail", "read emails", "inbox summary", "unread emails")):
        return get_mail_brief()

    # 3b. Universal Browser Search & Platform Deep-Linking (YouTube, Instagram, Multi-platform, Browser Search)
    search_res = universal_search(q_clean, q_text)
    if search_res:
        return search_res

    # 4. YouTube Music / Search
    m = re.search(r"(?:play|search|find|open)\s+(.+?)\s+(?:on|in)\s+youtube", q_clean)
    if m:
        query = m.group(1).strip()
        _open(["https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)])
        return f"Playing {query} on YouTube."

    # 4b. Open Antigravity (Local IDE/CLI first, browser fallback, physics page if requested)
    if "antigravity" in q_clean and (any(k in q_clean for k in ("open", "launch", "start", "visit", "go to", "google", "physics", "browser", "website")) or q_clean == "antigravity"):
        return launch_antigravity(q_clean)

    # 4c. Universal Voice-to-Browser Site Opener ("Open [site] in browser", "Go to [site]", spoken "dot")
    m_browser = re.match(r"(?:please\s+)?(?:open|launch|visit|go\s+to)\s+(.+?)\s+in\s+(?:the\s+)?browser$", q_clean)
    if m_browser:
        return resolve_and_open_site(m_browser.group(1))

    m_goto = re.match(r"(?:please\s+)?(?:visit|go\s+to)\s+(.+)$", q_clean)
    if m_goto:
        target_site = m_goto.group(1).strip()
        if not any(k in target_site for k in ("sleep", "bed", "work", "home")):
            return resolve_and_open_site(target_site)

    m_dot = re.match(r"(?:please\s+)?(?:open|launch|visit|go\s+to)\s+(.+?\bdot\b.+)$", q_clean)
    if m_dot:
        return resolve_and_open_site(m_dot.group(1))

    # 5. Open a user-requested HTTP(S) URL in the default browser.
    m = re.match(
        r"(?:please\s+)?(?:open|visit|go to)\s+"
        r"(https?://\S+|(?:[a-z0-9-]+\.)+[a-z]{2,}(?::\d{1,5})?(?:/\S*)?)",
        q_text,
        re.IGNORECASE,
    )
    if m:
        url = m.group(1).rstrip(".,!?")
        if not url.lower().startswith(("http://", "https://")):
            url = "https://" + url
        if _is_web_url(url) and webbrowser.open(url):
            return f"Opening {url} in your browser."
        return "I couldn't open that web address."

    # 6. Web search opens in the user's default browser.
    m = re.match(
        r"(?:please\s+)?search\s+"
        r"(?:(?:the\s+)?(?:web|internet|online)\s+)?"
        r"(?:for\s+)?(.+)",
        q_clean,
    )
    if not m:
        m = re.match(r"(?:please\s+)?google\s+(?:for\s+)?(.+)", q_clean)
    if m:
        query = re.sub(
            r"\s+(?:on|in)\s+(?:the\s+)?(?:web|internet|online)$",
            "",
            m.group(1).strip(),
        )
        search_url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)
        if not webbrowser.open(search_url):
            return "I couldn't open a browser for that search."
        return f"Searching Google for {query}."

    # 7. App Launch
    close_match = re.match(
        r"(?:please\s+)?(?:(forcefully\s+close|force\s+close|kill|terminate|stop|close|quit|exit|shut\s+down)\s+(?:the\s+)?)(.+?)"
        r"(?:\s+(forcefully|force))?$",
        q_clean,
    )
    if close_match and sys.platform == "win32":
        action, name, force_suffix = close_match.groups()
        name = name.strip()
        force = action in {"forcefully close", "force close", "kill", "terminate"} or bool(force_suffix)
        success, detail = jarvis_system_control.close_application(name, force=force)
        if success:
            verb = "Terminated" if force else "Closed"
            return f"{verb} {name}, sir."
        return f"I couldn't close {name}, sir. {detail}"

    # 7a. Incomplete / Bare Open Command Guard (prevents random LLM monologue hallucinations)
    if q_clean in ("open", "launch", "start", "please open"):
        return "What app or website would you like me to open, Boss?"
    if q_clean in ("open cheyyi", "open chey", "open cheyandi", "open cheyyandi", "ఓపెన్ చెయ్యి", "ఓపెన్ చేయి", "ఓపెన్ చేయండి"):
        return "చెప్పండి బాస్, ఏ యాప్ లేదా వెబ్‌సైట్ ఓపెన్ చేయాలి?"

    # 7b. Telugu Application Open Commands: "<app> open cheyyi" or "<app> ని ఓపెన్ చెయ్యి" or "ఓపెన్ చెయ్యి <app>"
    m_te_open = (
        re.match(r"^(?:dayachesi\s+)?(.+?)\s+(?:ni\s+|nu\s+)?(?:open\s+cheyyi|open\s+chey|open\s+cheyandi|open\s+cheyyandi)$", q_clean) or
        re.match(r"^(?:దయచేసి\s+)?(.+?)\s*(?:ని\s+|ను\s+)?(?:ఓపెన్\s*చెయ్యి|ఓపెన్\s*చేయి|ఓపెన్\s*చేయండి)$", q_clean) or
        re.match(r"^(?:ఓపెన్\s*చెయ్యి|ఓపెన్\s*చేయి|ఓపెన్\s*చేయండి)\s+(.+)$", q_clean)
    )
    if m_te_open:
        target_name = m_te_open.group(1).strip()
        target_name = re.sub(r"\s+(?:ni|nu|app|application)$", "", target_name).strip()
        te_app_map = {
            "నోట్‌ప్యాడ్": "notepad",
            "నోట్ పాడ్": "notepad",
            "క్రోమ్": "chrome",
            "యూట్యూబ్": "youtube",
            "వాట్సాప్": "whatsapp",
            "సెట్టింగ్స్": "settings",
            "క్యాలిక్యులేటర్": "calculator",
        }
        resolved_name = te_app_map.get(target_name, target_name)
        if resolved_name in SITES:
            _open([SITES[resolved_name]])
            return f"సరే బాస్, {resolved_name} ఓపెన్ చేస్తున్నాను."
        app = find_app(resolved_name)
        if app:
            success, _ = _launch_windows_app(app, app_name=resolved_name)
            if success:
                return f"సరే బాస్, {resolved_name} ఓపెన్ చేస్తున్నాను."
        site_res = resolve_and_open_site(resolved_name)
        if "Opening" in site_res:
            return f"సరే బాస్, {resolved_name} ఓపెన్ చేస్తున్నాను."
        return f"సరే బాస్, {resolved_name} ఓపెన్ చేయడానికి చూస్తున్నాను."

    m = re.match(r"(?:please\s+)?(?:open|launch|start)\s+(.+)", q_clean)
    if m:
        name = m.group(1).strip()
        if name in SITES:
            _open([SITES[name]])
            return f"Opening {name}."
        if name in KNOWN_PLATFORMS:
            return resolve_and_open_site(name)
        app = find_app(name)
        if sys.platform == "win32":
            if _is_shell_app(name):
                return "I don't run command-prompt or PowerShell commands. I can open regular installed apps instead."
            success, detail = _launch_windows_app(app or name, app_name=name)
            if success:
                return f"Opening {name} for you, sir."
            if detail and app:
                return f"I couldn't open {name}, sir. {detail}"
        elif app:
            if sys.platform == "darwin":
                if _open(["-a", app]):
                    return f"Opening {app}."
            else:
                if _open([app]):
                    return f"Opening {app}."
        if _is_shell_app(name):
            return "I don't run command-prompt or PowerShell commands. I can open regular installed apps instead."
        # Universal fallback: if no desktop application matched, open as website in browser
        return resolve_and_open_site(name)

    # 8. Volume & Sound Controls
    if any(k in q_clean for k in ("microphone sensitivity", "mic sensitivity", "sound settings", "audio settings", "open sound control panel", "mic settings", "microphone settings")):
        if sys.platform == "win32":
            try:
                subprocess.Popen(["control", "mmsys.cpl,,1"])
                return "Opening Windows Recording and Microphone Control Panel for you, sir."
            except Exception:
                try:
                    subprocess.Popen(["start", "ms-settings:sound"], shell=True)
                    return "Opening Sound Settings for you, sir."
                except Exception:
                    pass
    if "volume up" in q_clean or "louder" in q_clean:
        _change_volume("up")
        return "Volume increased."
    if "volume down" in q_clean or "quieter" in q_clean:
        _change_volume("down")
        return "Volume decreased."
    if q_clean in ("mute", "mute volume", "mute the volume"):
        _change_volume("mute")
        return "System audio muted."

    # 9. Date and Time
    if any(k in q_clean for k in ("what time is it", "current time", "tell me the time", "time now")) or q_clean == "time":
        return "It is currently " + datetime.datetime.now().strftime("%I:%M %p")
    if any(k in q_clean for k in ("what is the date", "what is today's date", "todays date", "today's date", "current date", "what day is today", "what is the day today", "date today")) or q_clean in ("date", "today"):
        return "Today is " + datetime.datetime.now().strftime("%A, %B %d, %Y")

    return None


# ═══════════════════════════════════════════════════════════════════════
# MAIN COMMAND LOOP ROUTING DISPATCHER (CASCADE ORDER)
# ═══════════════════════════════════════════════════════════════════════
def dispatch_cosmos_command(user_input: str):
    """
    Evaluates incoming commands using the Master Directive cascade order:
    1. Existing App Launchers & System Actions (READ-ONLY / UNTOUCHED)
    2. Live Web Search Triggers (cosmos_free_search)
    3. Clipboard / Local File / Polyglot Coding Triggers (cosmos_universal_coder)
    4. Deep Logic / Council Mode / Autonomous Thinking Fallback (cosmos_multi_brain)
    """
    cmd = user_input.lower().strip()

    # 1. Existing App Launchers, System Actions & Voice Greetings (READ-ONLY / UNTOUCHED)
    action_res = execute_action(user_input)
    if action_res is not None:
        return action_res

    # 2. Live Web Search Triggers
    if any(cmd.startswith(p) for p in ("search the web for ", "look up ", "what is the latest ", "current news on ")):
        query = cmd.replace("search the web for", "").replace("look up", "").replace("what is the latest", "").replace("current news on", "").strip()
        try:
            return cosmos_search_and_speak(query)
        except Exception as e:
            print(f"[DISPATCH LIVE SEARCH ERROR] {e}")

    # 3. Clipboard / Local File / Polyglot Coding Triggers
    if any(w in cmd for w in ("clipboard", "copied", "fix this code", "fix code", "debug")):
        try:
            return cosmos_universal_code_solver(user_input)
        except Exception as e:
            print(f"[DISPATCH UNIVERSAL CODER ERROR] {e}")

    # 4. Deep Logic / Council Mode / Autonomous Thinking Fallback
    try:
        return cosmos_multi_model_solve(user_input)
    except Exception:
        try:
            return cosmos_think_and_solve(user_input)
        except Exception as e:
            return f"Boss, I encountered an issue processing your request: {e}"

