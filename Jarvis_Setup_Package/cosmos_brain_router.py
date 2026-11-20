"""
COSMOS Brain Router — Groq (primary) + Ollama (fallback) chat & tool-call router.
Creator: Sri Charan Tirumaladasu
Groq API key NEVER leaves this server. Frontend sends only user messages.
"""
import json
import os
import sys
import time
import traceback

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import Any, Dict, List, Optional
    import httpx
except ImportError as e:
    print(f"[COSMOS BRAIN ROUTER] Missing dependency: {e}. Install via: pip install fastapi httpx uvicorn")
    sys.exit(1)

# Import centralized secrets config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cosmos_secrets_config import secrets_cfg

# Import OpenHer feelings for emotional context injection
try:
    from cosmos_openher_feelings_engine import openher_feelings
except ImportError:
    openher_feelings = None

app = FastAPI(title="COSMOS Brain Router", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8080", "http://localhost:8080", "http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate-limit tracking (RAM-only)
_model_cooldowns: Dict[str, float] = {}
_global_cooldown_until: float = 0.0


# -----------------------------------------------------------------
# Models
# -----------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    spoken_mode: bool = False
    system_prompt: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None


class ToolCallRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = {}
    user_context: Optional[str] = None


# -----------------------------------------------------------------
# POST /api/chat — Groq primary → Ollama fallback
# -----------------------------------------------------------------
@app.post("/api/chat")
async def chat(req: ChatRequest):
    groq_key = secrets_cfg.get_groq_key()

    # Build messages
    system_prompt = req.system_prompt or (
        "You are COSMOS, an emotionally alive Digital Human companion and co-founder "
        "created by Sri Charan Tirumaladasu (Boss Charan). Speak warmly, naturally, "
        "and authentically. Keep casual turns to 1-3 heartfelt sentences."
    )

    # Inject OpenHer feelings if available
    if openher_feelings:
        try:
            feeling_prompt = openher_feelings.build_feeling_system_prompt(req.message)
            if feeling_prompt:
                system_prompt = feeling_prompt
        except Exception:
            pass

    messages = [{"role": "system", "content": system_prompt}]
    if req.history:
        messages.extend(req.history[-12:])
    messages.append({"role": "user", "content": req.message})

    # ------- Attempt 1: Groq Cloud -------
    if groq_key and time.time() >= _global_cooldown_until:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{secrets_cfg.GROQ_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {groq_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": secrets_cfg.GROQ_MODEL,
                        "messages": messages,
                        "max_tokens": 450,
                        "temperature": 0.75,
                    },
                )

            if resp.status_code == 200:
                data = resp.json()
                answer = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if answer:
                    # Store affective memory
                    if openher_feelings:
                        try:
                            openher_feelings.store_affective_memory(req.message, answer)
                        except Exception:
                            pass
                    return {"reply": answer, "provider": "groq", "model": secrets_cfg.GROQ_MODEL}

            elif resp.status_code == 429:
                _global_cooldown_until = time.time() + 30.0
                print(f"[COSMOS BRAIN ROUTER] Groq rate-limited, cooling down 30s", flush=True)
            else:
                print(f"[COSMOS BRAIN ROUTER] Groq HTTP {resp.status_code}", flush=True)

        except httpx.RequestError as e:
            # Network error — log without exposing key
            print(f"[COSMOS BRAIN ROUTER] Groq network error: {type(e).__name__}", flush=True)
        except Exception as e:
            print(f"[COSMOS BRAIN ROUTER] Groq error: {type(e).__name__}", flush=True)

    # ------- Attempt 2: Local Ollama Fallback -------
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                secrets_cfg.OLLAMA_URL,
                json={
                    "model": secrets_cfg.OLLAMA_MODEL,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": 0.75, "num_predict": 400},
                },
            )

        if resp.status_code == 200:
            data = resp.json()
            answer = data.get("message", {}).get("content", "").strip()
            if answer:
                if openher_feelings:
                    try:
                        openher_feelings.store_affective_memory(req.message, answer)
                    except Exception:
                        pass
                return {"reply": answer, "provider": "ollama", "model": secrets_cfg.OLLAMA_MODEL}
    except Exception as e:
        print(f"[COSMOS BRAIN ROUTER] Ollama fallback error: {type(e).__name__}", flush=True)

    # ------- Attempt 3: OpenHer feelings-based fallback -------
    if openher_feelings:
        fallback_reply = openher_feelings.generate_feeling_response(req.message)
        return {"reply": fallback_reply, "provider": "openher_feelings", "model": "local_ram"}

    return {"reply": "I hear you, Charan. My cloud and local models are both temporarily unavailable, but I'm still right here.", "provider": "static_fallback", "model": "none"}


# -----------------------------------------------------------------
# POST /api/cosmos/tool — Delegated tool-call execution via Groq
# -----------------------------------------------------------------
@app.post("/api/cosmos/tool")
async def tool_call(req: ToolCallRequest):
    groq_key = secrets_cfg.get_groq_key()
    if not groq_key:
        raise HTTPException(status_code=503, detail="Groq API not configured for tool calls.")

    tool_prompt = (
        f"Execute the following tool call and return the result as JSON.\n"
        f"Tool: {req.tool_name}\n"
        f"Arguments: {json.dumps(req.arguments)}\n"
    )
    if req.user_context:
        tool_prompt += f"User Context: {req.user_context}\n"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{secrets_cfg.GROQ_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": secrets_cfg.GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a precise tool executor. Return structured JSON results."},
                        {"role": "user", "content": tool_prompt},
                    ],
                    "max_tokens": 500,
                    "temperature": 0.3,
                },
            )

        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=f"Groq tool call failed: HTTP {resp.status_code}")

        data = resp.json()
        result = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        return {"tool": req.tool_name, "result": result, "provider": "groq"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[COSMOS BRAIN ROUTER] Tool call error: {type(e).__name__}", flush=True)
        raise HTTPException(status_code=500, detail="Tool execution failed.")


# -----------------------------------------------------------------
# Health check
# -----------------------------------------------------------------
@app.get("/api/health")
async def health():
    return {"status": "alive", "engine": "COSMOS Brain Router"}


if __name__ == "__main__":
    import uvicorn
    print("[COSMOS BRAIN ROUTER] Starting on http://127.0.0.1:8001 ...")
    uvicorn.run(app, host="127.0.0.1", port=8001)
