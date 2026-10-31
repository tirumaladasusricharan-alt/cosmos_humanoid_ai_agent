"""
add_to_startup.py - Adds COSMOS to Windows Startup
Runs once to create a shortcut in the Windows Startup folder
so COSMOS launches automatically when you log in.
"""

import os
import sys
import winreg

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHONW = os.path.join(SCRIPT_DIR, ".venv", "Scripts", "pythonw.exe")
COSMOS_SCRIPT = os.path.join(SCRIPT_DIR, "cosmos_server.py")

REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
REG_NAME = "COSMOSAI"
LEGACY_REG_NAME = "JarvisAI"


def add_startup():
    """Add COSMOS 3D Humanoid to Windows startup via registry."""
    cmd = f'"{PYTHONW}" "{COSMOS_SCRIPT}"'
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE)
        try:
            winreg.DeleteValue(key, LEGACY_REG_NAME)
        except FileNotFoundError:
            pass
        winreg.SetValueEx(key, REG_NAME, 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
        print("[+] COSMOS added to Windows Startup successfully!")
        print(f"    Registry: HKCU\\{REG_PATH}\\{REG_NAME}")
        print(f"    Command:  {cmd}")
        print()
        print("    COSMOS will now launch automatically when you log in.")
        print("    Tap Alt anywhere to summon the overlay.")
    except Exception as e:
        print(f"[X] Failed to add to startup: {e}")
        print("    Try running this script as Administrator.")


def remove_startup():
    """Remove COSMOS from Windows startup."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE)
        removed = False
        for name in (REG_NAME, LEGACY_REG_NAME):
            try:
                winreg.DeleteValue(key, name)
                removed = True
            except FileNotFoundError:
                continue
        winreg.CloseKey(key)
        if removed:
            print("[+] COSMOS removed from Windows Startup.")
        else:
            print("[i] COSMOS was not in Startup.")
    except FileNotFoundError:
        print("[i] COSMOS was not in Startup.")
    except Exception as e:
        print(f"[X] Failed to remove from startup: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--remove":
        remove_startup()
    else:
        add_startup()
