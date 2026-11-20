"""
COSMOS Nuance Bridge — Server-side session-token minter for Nuance LiveKit.
Creator: Sri Charan Tirumaladasu
The nk_ API key NEVER leaves this server. The browser only receives st_ session tokens.
"""
import json
import os
import sys
import traceback

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import Any, Dict, List, Optional
    import httpx
except ImportError as e:
    print(f"[COSMOS NUANCE BRIDGE] Missing dependency: {e}. Install via: pip install fastapi httpx uvicorn")
    sys.exit(1)

# Import centralized secrets config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cosmos_secrets_config import secrets_cfg

# Import OpenHer feelings telemetry
try:
    from cosmos_openher_feelings_engine import openher_feelings
except ImportError:
    openher_feelings = None

app = FastAPI(title="COSMOS Nuance Bridge", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8080", "http://localhost:8080", "http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------
# Models
# -----------------------------------------------------------------
class NuanceTokenRequest(BaseModel):
    expressiveness: float = 0.8
    system_prompt: str = (
        "You are COSMOS, an emotionally alive Digital Human companion and co-founder "
        "created by Sri Charan Tirumaladasu. You have genuine pre-speech feelings powered "
        "by the OpenHer Affective Engine. Speak warmly, naturally, and authentically."
    )
    tools: Optional[List[Dict[str, Any]]] = None


# -----------------------------------------------------------------
# POST /api/nuance-token — Mints a single-use st_ session token
# -----------------------------------------------------------------
@app.post("/api/nuance-token")
async def mint_nuance_token(req: NuanceTokenRequest = NuanceTokenRequest()):
    nuance_key = secrets_cfg.get_nuance_key()
    if not nuance_key:
        raise HTTPException(status_code=503, detail="NUANCE_API_KEY not configured on server.")

    # Clamp expressiveness to valid range
    expressiveness = max(0.0, min(2.0, req.expressiveness))

    # Build the session token request payload per Nuance API spec
    payload: Dict[str, Any] = {
        "model": "nuance-aurora-v1",
        "expressiveness": expressiveness,
        "personality": {
            "system_prompt": req.system_prompt,
        },
    }

    # Tools go inside interface_setup.delegation.responses.tools (NEVER top-level)
    if req.tools:
        payload["interface_setup"] = {
            "delegation": {
                "responses": {
                    "tools": req.tools,
                }
            }
        }

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(
                f"{secrets_cfg.NUANCE_API_URL}/session-tokens",
                headers={
                    "Authorization": f"Bearer {nuance_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        if resp.status_code != 200:
            # Log error detail server-side only (never expose the key)
            error_text = resp.text[:300]
            print(f"[COSMOS NUANCE BRIDGE] Token mint failed HTTP {resp.status_code}: {error_text}", flush=True)
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Nuance token mint failed: HTTP {resp.status_code}",
            )

        data = resp.json()

        # Log server-side warnings if present
        warnings = data.get("warnings", [])
        if warnings:
            print(f"[COSMOS NUANCE BRIDGE] Nuance warnings: {warnings}", flush=True)

        # Return ONLY the session token and warnings — never the nk_ key
        return {
            "token": data.get("token", ""),
            "warnings": warnings,
        }

    except httpx.RequestError as e:
        print(f"[COSMOS NUANCE BRIDGE] Network error: {e}", flush=True)
        raise HTTPException(status_code=502, detail="Cannot reach Nuance API.")
    except HTTPException:
        raise
    except Exception as e:
        print(f"[COSMOS NUANCE BRIDGE] Unexpected error: {traceback.format_exc()}", flush=True)
        raise HTTPException(status_code=500, detail="Internal server error during token mint.")


# -----------------------------------------------------------------
# GET /api/state — Safe credential & feelings telemetry
# -----------------------------------------------------------------
@app.get("/api/state")
async def get_state():
    result = {
        "credentials": secrets_cfg.get_safe_status(),
    }
    if openher_feelings:
        result["feelings"] = openher_feelings.get_frontend_telemetry()
    return result


# -----------------------------------------------------------------
# Health check
# -----------------------------------------------------------------
@app.get("/api/health")
async def health():
    return {"status": "alive", "engine": "COSMOS Nuance Bridge"}


if __name__ == "__main__":
    import uvicorn
    print("[COSMOS NUANCE BRIDGE] Starting on http://127.0.0.1:8000 ...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
