"""
COSMOS Key Verification Script — Smoke-tests both keys and server routes.
Creator: Sri Charan Tirumaladasu
NEVER prints raw API keys. Only prints boolean status and HTTP codes.
"""
import os
import sys
import json

try:
    import requests
except ImportError:
    print("ERROR: 'requests' not installed. Run: pip install requests")
    sys.exit(1)

BASE_URL = os.environ.get("COSMOS_SERVER_URL", "http://127.0.0.1:8000")


def main():
    print("=" * 60)
    print("  COSMOS DUAL-ENGINE KEY VERIFICATION")
    print("  Creator: Sri Charan Tirumaladasu")
    print("=" * 60)
    print()

    # --- 1. /api/state (safe credential status) ---
    print("1) Checking /api/state (safe credential status)...")
    try:
        state = requests.get(f"{BASE_URL}/api/state", timeout=10)
        state.raise_for_status()
        creds = state.json().get("credentials", {})
        print(f"   Nuance configured: {creds.get('nuance_configured', False)}")
        print(f"   Nuance prefix valid (nk_): {creds.get('nuance_prefix_valid', False)}")
        print(f"   Groq configured: {creds.get('groq_configured', False)}")
        print(f"   Groq prefix valid (gsk_): {creds.get('groq_prefix_valid', False)}")
        print(f"   RAM-only mode: {creds.get('ram_only_mode', False)}")
        print(f"   Groq model: {creds.get('groq_model', 'N/A')}")
    except requests.ConnectionError:
        print(f"   FAILED: Cannot connect to {BASE_URL}. Is the server running?")
        print(f"   Start with: .\\start_cosmos_ram.ps1")
        sys.exit(1)
    except Exception as e:
        print(f"   ERROR: {e}")

    print()

    # --- 2. Direct Groq key check (zero token spend) ---
    print("2) Checking Groq key directly via GET /openai/v1/models (zero token spend)...")
    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        try:
            r = requests.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {groq_key}"},
                timeout=15,
            )
            if r.ok:
                models = r.json().get("data", [])
                print(f"   Groq /models HTTP {r.status_code} | Models visible: {len(models)}")
                model_ids = [m.get("id", "") for m in models[:5]]
                print(f"   Sample models: {model_ids}")
            else:
                print(f"   Groq /models HTTP {r.status_code} | Detail: {r.text[:120]}")
        except Exception as e:
            print(f"   ERROR: {e}")
    else:
        print("   GROQ_API_KEY not set in this shell; skipping direct check.")

    print()

    # --- 3. /api/chat (Groq primary -> Ollama fallback) ---
    print("3) Testing /api/chat (Groq primary -> Ollama fallback)...")
    try:
        chat = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": "Ping check, COSMOS—reply in one short sentence.", "spoken_mode": False},
            timeout=30,
        )
        if chat.ok:
            data = chat.json()
            print(f"   /api/chat HTTP {chat.status_code} | Provider: {data.get('provider')} | Model: {data.get('model')}")
            reply = data.get("reply", "")
            print(f"   Reply preview: {reply[:120]}...")
        else:
            print(f"   /api/chat HTTP {chat.status_code} | Detail: {chat.text[:160]}")
    except Exception as e:
        print(f"   ERROR: {e}")

    print()

    # --- 4. /api/nuance-token (server-side nk_ -> st_ mint) ---
    print("4) Testing /api/nuance-token (server-side nk_ -> st_ mint)...")
    try:
        tok = requests.post(f"{BASE_URL}/api/nuance-token", timeout=25)
        if tok.ok:
            data = tok.json()
            token_val = data.get("token", "")
            print(f"   Mint SUCCESS | Token prefix valid (st_): {token_val.startswith('st_')}")
            print(f"   Warnings: {data.get('warnings', [])}")
        else:
            print(f"   Mint FAILED HTTP {tok.status_code} | Detail: {tok.text[:200]}")
    except Exception as e:
        print(f"   ERROR: {e}")

    print()
    print("=" * 60)
    print("  VERIFICATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
