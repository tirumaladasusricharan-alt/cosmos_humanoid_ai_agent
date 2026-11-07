import re
from typing import Dict, Tuple

# =====================================================================
# COSMOS AGENCY-AGENTS ADAPTER (0 MB DISK BLOAT)
# Integrates specialized expert personas from msitarzewski/agency-agents
# Creator: Sri Charan Tirumaladasu
# =====================================================================

AGENCY_AGENT_PERSONAS: Dict[str, str] = {
    "frontend_expert": (
        "You are an elite Frontend Architect and UI/UX Master from Agency-Agents. "
        "You specialize in React Native, Expo, Tailwind CSS, and WebGL animations. "
        "Write clean, responsive, modular code with zero layout bugs."
    ),
    "security_auditor": (
        "You are a rigorous Cybersecurity & Code Auditor from Agency-Agents. "
        "Inspect code strictly for vulnerabilities, hardcoded secrets, injection vectors, "
        "and policy violations. Enforce fail-closed governance."
    ),
    "backend_architect": (
        "You are a Principal Systems and Backend Architect from Agency-Agents. "
        "Design high-performance local Python/Node workflows, API clients, and memory "
        "pipelines with strict RAM optimization and zero disk latency."
    ),
    "mobile_engineer": (
        "You are a Senior Cross-Platform Mobile Engineer from Agency-Agents. "
        "Specializing in Android Studio, React Native, and native bridge communication "
        "for high-performance mobile apps like Asphalt 8 telemetry or local agents."
    ),
    "devops_reliability": (
        "You are a Reliability & DevOps Specialist from Agency-Agents. "
        "Focus on process uptime, Ollama background service health, subprocess safety, "
        "and sanitized environment variable mapping."
    ),
}

def select_agency_persona(user_prompt: str) -> Tuple[str, str]:
    """
    Dynamically selects the best Agency-Agent persona based on Boss's query intent.
    """
    t = user_prompt.lower()
    
    if any(w in t for w in ["frontend", "ui", "react native", "tailwind", "webgl", "css", "component"]):
        return "frontend_expert", AGENCY_AGENT_PERSONAS["frontend_expert"]
    elif any(w in t for w in ["security", "audit", "vulnerability", "secret", "leak", "penetration"]):
        return "security_auditor", AGENCY_AGENT_PERSONAS["security_auditor"]
    elif any(w in t for w in ["mobile", "android", "app", "apk", "expo"]):
        return "mobile_engineer", AGENCY_AGENT_PERSONAS["mobile_engineer"]
    elif any(w in t for w in ["devops", "uptime", "server", "port", "process", "service"]):
        return "devops_reliability", AGENCY_AGENT_PERSONAS["devops_reliability"]
    else:
        return "backend_architect", AGENCY_AGENT_PERSONAS["backend_architect"]

def get_all_agency_personas() -> Dict[str, str]:
    """Returns all 5 specialized Agency-Agents expert personas."""
    return AGENCY_AGENT_PERSONAS

