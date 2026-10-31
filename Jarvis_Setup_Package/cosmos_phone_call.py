"""
cosmos_phone_call.py - Direct Phone Link Native Automation for COSMOS
Architected & Exclusively Deployed for Sri Charan Tirumaladasu ("Boss")

Executes automated hands-free calls through Windows Phone Link using native Win32 API:
1. Minimizes COSMOS overlay so Phone Link has full screen focus
2. Launches / brings Phone Link to foreground
3. Types digits directly into the dialpad or types contact name into Search
4. Executes Enter keypress and clicks the Call button
"""

import ctypes
import ctypes.wintypes
import glob
import os
import re
import sqlite3
import sys
import time
import threading

user32 = ctypes.windll.user32

# Win32 Virtual Key Codes
VK_RETURN = 0x0D
VK_SPACE  = 0x20
VK_TAB    = 0x09
VK_BACK   = 0x08
VK_ESCAPE = 0x1B
VK_DOWN   = 0x28
VK_CONTROL = 0x11
KEYEVENTF_KEYUP = 0x0002

# Mouse flags
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP   = 0x0004

class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long)
    ]

def get_phone_link_contacts_db():
    """Finds the local SQLite contacts database synced by Windows Phone Link."""
    patterns = [
        os.path.expanduser('~/AppData/Local/Packages/Microsoft.YourPhone_*/LocalCache/Indexed/*/System/Database/contacts.db'),
        os.path.expanduser('~/AppData/Local/Packages/Microsoft.YourPhone_*/LocalCache/Indexed/*/System/Database/calling.db'),
    ]
    for p in patterns:
        matches = glob.glob(p)
        if matches:
            return matches[0]
    return None

def clean_contact_name_for_match(s: str) -> str:
    if not s:
        return ""
    # Strip emojis, punctuation, symbols
    s = re.sub(r'[^\w\s]', ' ', s, flags=re.UNICODE)
    return " ".join(s.lower().split())

def lookup_contact_in_phone_db(query: str):
    """
    Zero-latency local contact search directly from Phone Link's synced SQLite database.
    Matches names with exact, substring, or token overlap scoring.
    Returns (display_name, phone_number) or None.
    """
    db_path = get_phone_link_contacts_db()
    if not db_path or not os.path.isfile(db_path):
        return None

    q_clean = clean_contact_name_for_match(query)
    if not q_clean:
        return None

    q_words = [w for w in q_clean.split() if len(w) > 1]

    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur = con.cursor()
        cur.execute("""
            SELECT c.display_name, p.phone_number
            FROM contact c
            JOIN phonenumber p ON c.contact_id = p.contact_id
            WHERE p.phone_number IS NOT NULL AND p.phone_number != ''
        """)
        all_contacts = cur.fetchall()
        con.close()
    except Exception as e:
        print(f"[COSMOS PHONE DB ERROR] {e}")
        return None

    best_match = None
    best_score = 0

    for name, num in all_contacts:
        if not name or not num:
            continue
        c_clean = clean_contact_name_for_match(name)
        score = 0

        # Exact match
        if q_clean == c_clean:
            score = 100
        # Query is full substring of contact name
        elif q_clean in c_clean:
            score = 80
        # Contact name is substring of query
        elif c_clean in q_clean:
            score = 70
        else:
            c_words = set(c_clean.split())
            matched_words = [w for w in q_words if w in c_words]
            if matched_words:
                score = 30 * len(matched_words)

        if score > best_score:
            best_score = score
            best_match = (name, num)

    if best_score >= 30:
        return best_match
    return None

def send_key(vk):
    user32.keybd_event(vk, 0, 0, 0)
    time.sleep(0.04)
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.04)

def send_hotkey(mod_vk, key_vk):
    user32.keybd_event(mod_vk, 0, 0, 0)
    time.sleep(0.04)
    user32.keybd_event(key_vk, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(key_vk, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(mod_vk, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.04)

def mouse_click(x, y):
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.08)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.08)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.05)

def find_phone_link_hwnd():
    for name in ("Phone Link", "Your Phone"):
        h = user32.FindWindowW("ApplicationFrameWindow", name)
        if h and user32.IsWindowVisible(h):
            return h
        h = user32.FindWindowW(None, name)
        if h and user32.IsWindowVisible(h):
            return h
    return None

def place_call(target: str = "+917780538869"):
    target_str = str(target).strip()

    # 1. Minimize COSMOS overlay so Phone Link has full screen & focus
    try:
        cosmos_hwnd = user32.FindWindowW(None, "COSMOS_OVERLAY_ROOT")
        if cosmos_hwnd:
            user32.SetWindowPos(cosmos_hwnd, -2, 0, 0, 0, 0, 0x0001 | 0x0002)
            user32.ShowWindow(cosmos_hwnd, 6) # SW_MINIMIZE
    except Exception:
        pass

    # 2. Parse target & resolve from local contacts database
    clean_digits = re.sub(r"[^\d]", "", target_str)
    is_phone_number = len(clean_digits) >= 7 and len(re.sub(r"[\d\s\-+]", "", target_str)) == 0
    resolved_contact_name = None

    # If target is Boss's name or personal phone, use Boss's number 7780538869
    if any(k in target_str.lower() for k in ("charan", "boss", "my phone", "me")):
        clean_digits = "7780538869"
        is_phone_number = True
        resolved_contact_name = "Sri Charan"
    elif not is_phone_number:
        # Match against Sri Charan's Phone Link contacts database
        db_match = lookup_contact_in_phone_db(target_str)
        if db_match:
            resolved_contact_name, matched_num = db_match
            matched_digits = re.sub(r"[^\d]", "", matched_num)
            if len(matched_digits) >= 7:
                clean_digits = matched_digits
                is_phone_number = True
                print(f"[COSMOS PHONE] Resolved '{target_str}' to contact '{resolved_contact_name}' with number: {clean_digits}")

    os.system("start ms-phone:")
    time.sleep(1.2)

    # 3. Find and bring Phone Link to front
    phone_hwnd = None
    for _ in range(30):
        phone_hwnd = find_phone_link_hwnd()
        if phone_hwnd:
            break
        time.sleep(0.1)

    if phone_hwnd:
        user32.ShowWindow(phone_hwnd, 9) # SW_RESTORE
        time.sleep(0.2)
        fg = user32.GetForegroundWindow()
        fg_t = user32.GetWindowThreadProcessId(fg, None)
        target_t = user32.GetWindowThreadProcessId(phone_hwnd, None)
        if fg_t != target_t:
            user32.AttachThreadInput(fg_t, target_t, True)
        user32.SetForegroundWindow(phone_hwnd)
        user32.BringWindowToTop(phone_hwnd)
        if fg_t != target_t:
            user32.AttachThreadInput(fg_t, target_t, False)
        time.sleep(0.3)

    # 4. Dialing execution
    if is_phone_number and clean_digits:
        # PATH A: Type digits directly into the dialpad (100% Proven Call on PC)
        print(f"[COSMOS PHONE] Actively typing digits {clean_digits} into Phone Link dialpad...")
        for ch in clean_digits:
            vk = ord(ch) # '0'-'9' virtual key code
            send_key(vk)
            time.sleep(0.04)

        time.sleep(0.3)
        # Press Enter to initiate call
        send_key(VK_RETURN)
        time.sleep(0.3)

        # Also click the round green Call button at bottom of keypad if window rect known
        if phone_hwnd:
            rect = RECT()
            if user32.GetWindowRect(phone_hwnd, ctypes.byref(rect)):
                w = rect.right - rect.left
                h = rect.bottom - rect.top
                btn_x = rect.right - int(w * 0.22)
                btn_y = rect.bottom - 95
                mouse_click(btn_x, btn_y)
    else:
        # PATH B: Search contact name in UI & click the Blue Call button on the contact row
        print(f"[COSMOS PHONE] Searching contact '{target_str}' in Phone Link UI...")
        send_hotkey(VK_CONTROL, ord('E'))
        time.sleep(0.2)
        send_hotkey(VK_CONTROL, ord('A'))
        time.sleep(0.1)
        for ch in target_str:
            vk = user32.VkKeyScanW(ord(ch)) & 0xFF
            if vk != 0xFF:
                send_key(vk)
                time.sleep(0.03)
        time.sleep(0.5)

        # Click the Blue Call button on the 1st search result item
        if phone_hwnd:
            rect = RECT()
            if user32.GetWindowRect(phone_hwnd, ctypes.byref(rect)):
                w = rect.right - rect.left
                h = rect.bottom - rect.top
                # Position of Blue Call button on contact row (approx X=47% width, Y=28% height)
                call_icon_x = rect.left + int(w * 0.47)
                call_icon_y = rect.top + int(h * 0.28)
                # Hover to show buttons, then click
                user32.SetCursorPos(rect.left + int(w * 0.25), call_icon_y)
                time.sleep(0.15)
                mouse_click(call_icon_x, call_icon_y)

    # Also launch phone_link_call.ps1 as a parallel helper for UIAutomation
    try:
        ps_script = os.path.join(os.path.dirname(__file__), "phone_link_call.ps1")
        if os.path.exists(ps_script):
            import subprocess
            subprocess.Popen(["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", ps_script, str(target_str)])
    except Exception:
        pass

    return True

def place_call_threaded(target: str = "+917780538869"):
    threading.Thread(target=lambda: place_call(target), daemon=True).start()

if __name__ == "__main__":
    t = sys.argv[1] if len(sys.argv) > 1 else "+917780538869"
    place_call(t)
