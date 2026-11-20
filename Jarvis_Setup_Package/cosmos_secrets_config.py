import os
from typing import Dict, Optional

# =====================================================================
# COSMOS CENTRALIZED SECRETS & CREDENTIAL CONFIG (0-MB Disk / RAM-First)
# Creator: Sri Charan Tirumaladasu
# Zero-leak credential loader for Dual-Engine COSMOS.
# Keys are NEVER logged, serialized, or returned in API responses.
# =====================================================================

# Optional local .env loading (skipped automatically in strict 0-MB RAM mode)
if os.environ.get("COSMOS_STRICT_RAM_ONLY", "0") != "1":
    try:
        from dotenv import load_dotenv
        _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        if os.path.exists(_env_path):
            load_dotenv(_env_path, override=False)
    except ImportError:
        pass


class CosmosSecretsConfig:
    """Centralized, zero-leak credential loader for Dual-Engine COSMOS."""

    # Nuance Labs (LiveKit audiovisual bridge)
    NUANCE_API_URL: str = os.environ.get(
        "NUANCE_API_URL", "https://api.nuancelabs.ai"
    ).rstrip("/")

    # Groq Cloud LLM (primary brain)
    GROQ_BASE_URL: str = os.environ.get(
        "GROQ_BASE_URL", "https://api.groq.com/openai/v1"
    ).rstrip("/")
    GROQ_MODEL: str = os.environ.get("COSMOS_GROQ_MODEL", "openai/gpt-oss-120b")

    # Local Ollama fallback (zero-key offline)
    OLLAMA_URL: str = os.environ.get(
        "OLLAMA_URL", "http://localhost:11434/api/chat"
    )
    OLLAMA_MODEL: str = os.environ.get("COSMOS_OLLAMA_MODEL", "llama3.1:8b")

    # -----------------------------------------------------------------
    # KEY ACCESSORS (read on every call, never cached as class attrs)
    # -----------------------------------------------------------------
    @staticmethod
    def get_nuance_key() -> Optional[str]:
        """Returns the Nuance API key from env, or None. Never caches."""
        key = os.environ.get("NUANCE_API_KEY", "").strip()
        return key or None

    @staticmethod
    def get_groq_key() -> Optional[str]:
        """Returns the Groq API key from env or local .groq_key file. Never caches."""
        # Priority 1: Environment variable
        key = os.environ.get("GROQ_API_KEY", "").strip()
        if key:
            return key
        # Priority 2: Local .groq_key file (legacy COSMOS compat)
        for candidate in [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), ".groq_key"),
            os.path.expanduser("~/.openjarvis/free.key"),
        ]:
            try:
                if os.path.exists(candidate):
                    val = open(candidate, encoding="utf-8").read().strip()
                    if val:
                        return val
            except Exception:
                pass
        # Priority 3: Local .env file (manual parse fallback)
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        try:
            if os.path.exists(env_path):
                with open(env_path, encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("GROQ_API_KEY="):
                            return line.split("=", 1)[1].strip()
        except Exception:
            pass
        return None

    # -----------------------------------------------------------------
    # SAFE STATUS (boolean/prefix only — NEVER exposes raw keys)
    # -----------------------------------------------------------------
    @classmethod
    def get_safe_status(cls) -> Dict[str, object]:
        """Returns safe boolean/prefix diagnostics without ever exposing secrets."""
        nk = cls.get_nuance_key()
        gk = cls.get_groq_key()
        return {
            "nuance_configured": bool(nk),
            "nuance_prefix_valid": bool(nk and nk.startswith("nk_")),
            "groq_configured": bool(gk),
            "groq_prefix_valid": bool(gk and gk.startswith("gsk_")),
            "groq_model": cls.GROQ_MODEL,
            "ollama_model": cls.OLLAMA_MODEL,
            "ram_only_mode": os.environ.get("COSMOS_STRICT_RAM_ONLY", "0") == "1",
        }


# Module-level singleton
secrets_cfg = CosmosSecretsConfig()
