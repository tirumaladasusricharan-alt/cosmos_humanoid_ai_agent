import ctypes
import time
from ctypes import wintypes

user32 = ctypes.windll.user32

def restore_mouse():
    print("[1] Unclipping cursor rectangle...")
    user32.ClipCursor(None)

    print("[2] Incrementing ShowCursor display counter...")
    for _ in range(50):
        if user32.ShowCursor(True) >= 0:
            break

    print("[3] Reloading Windows default system cursor scheme (SPI_SETCURSORS)...")
    SPI_SETCURSORS = 0x0057
    SPIF_UPDATEINIFILE = 0x01
    SPIF_SENDCHANGE = 0x02
    user32.SystemParametersInfoW(SPI_SETCURSORS, 0, None, SPIF_UPDATEINIFILE | SPIF_SENDCHANGE)

    print("[4] Loading standard IDC_ARROW cursor...")
    IDC_ARROW = 32512
    h_cursor = user32.LoadCursorW(0, IDC_ARROW)
    if h_cursor:
        user32.SetCursor(h_cursor)
        print(f"    Loaded & SetCursor IDC_ARROW handle: {h_cursor}")

    print("[5] Moving cursor to center of screen (640, 360) with wake jitter...")
    w = user32.GetSystemMetrics(0)
    h = user32.GetSystemMetrics(1)
    cx, cy = w // 2, h // 2
    user32.SetCursorPos(cx, cy)
    MOUSEEVENTF_MOVE = 0x0001
    for offset in [-20, 20, -20, 20, 0]:
        user32.SetCursorPos(cx + offset, cy)
        time.sleep(0.04)

    print("[6] Checking final cursor state...")
    class CURSORINFO(ctypes.Structure):
        _fields_ = [
            ('cbSize', wintypes.DWORD),
            ('flags', wintypes.DWORD),
            ('hCursor', wintypes.HANDLE),
            ('ptScreenPos', wintypes.POINT)
        ]
    ci = CURSORINFO()
    ci.cbSize = ctypes.sizeof(CURSORINFO)
    if user32.GetCursorInfo(ctypes.byref(ci)):
        state = "VISIBLE (SHOWING)" if ci.flags == 1 else f"FLAGS={ci.flags}"
        print(f"    Cursor Status: {state} at position ({ci.ptScreenPos.x}, {ci.ptScreenPos.y})")

    print("[SUCCESS] Windows system mouse cursor restored, centered, and refreshed!")

if __name__ == "__main__":
    restore_mouse()
