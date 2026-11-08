"""
cosmos_sovereign_control.py - COSMOS Sovereign Permission Gate & Boss-Locked Audio/System Settings
Architected exclusively for Sri Charan Tirumaladasu ("Boss" / "Charan" / "Sir")
Mandate:
1. Autonomous Moral/Technical Reasoning ("What's Wrong vs. What's Right") + Mandatory Permission Gate.
2. 100% Boss-Controlled Audio Settings (Somatic auto-drift strictly disabled).
3. 100% Boss-Controlled System Settings (Webcam, clipboard, daemons strictly manual).
"""

import time
from typing import Any, Callable, Dict, Optional
from cosmos_decision_adjudicator import decision_adjudicator
from cosmos_unified_mega_suite import (
    COSMOS_UNIFIED_STATE,
    CosmosRufloHarness,
    OpenBotGovernanceGate,
    voice_barge_engine,
)

# =====================================================================
# 1. 100% BOSS-LOCKED AUDIO & SYSTEM SETTINGS REGISTRY (READ-ONLY TO AI)
# Creator & Sole Controller: Sri Charan Tirumaladasu
# =====================================================================


class BossLockedSettingsRegistry:
    """
    Locks all audio and system settings under Boss Charan's 100% manual control.
    COSMOS's affect/somatic engines CANNOT overwrite these values.
    """

    def __init__(self):
        self._audio_settings: Dict[str, Any] = {
            "master_mute": False,
            "volume": "+0%",                     # Locked until Boss changes it
            "tts_rate": "+0%",                   # Locked (Somatic auto-drift disabled)
            "tts_pitch": "+0Hz",                 # Locked (Somatic auto-drift disabled)
            "voice_id": "en-IN-NeerjaNeural",    # Locked default voice
            "barge_in_enabled": True,
        }
        self._system_settings: Dict[str, Any] = {
            "webcam_enabled": False,             # Off by default until Boss enables
            "clipboard_sniffer_enabled": False,  # Off by default until Boss enables
            "shell_execution_enabled": False,    # Strictly locked behind permission
            "primary_llm": "qwen3:8b",
            "require_permission_for_all_decisions": True,  # Immutable True
        }

    # --- READ-ONLY GETTERS FOR COSMOS ---
    def get_audio(self) -> Dict[str, Any]:
        return dict(self._audio_settings)

    def get_system(self) -> Dict[str, Any]:
        return dict(self._system_settings)

    # --- BOSS-ONLY MANUAL OVERRIDE COMMANDS ---
    def boss_update_audio(self, key: str, value: Any) -> str:
        if key not in self._audio_settings:
            return f"[Audio Lock]: Unknown setting '{key}'."
        self._audio_settings[key] = value
        # Sync locked prosody to shared state so Edge-TTS obeys Boss's exact settings
        COSMOS_UNIFIED_STATE["affect"]["tts_rate"] = self._audio_settings["tts_rate"]
        COSMOS_UNIFIED_STATE["affect"]["tts_pitch"] = self._audio_settings["tts_pitch"]
        return f"[Boss Audio Control]: '{key}' locked to '{value}'."

    def boss_update_system(self, key: str, value: Any) -> str:
        if key == "require_permission_for_all_decisions":
            return "[System Lock]: Permission gate is permanently locked ON for Boss Charan."
        if key not in self._system_settings:
            return f"[System Lock]: Unknown setting '{key}'."
        self._system_settings[key] = value
        return f"[Boss System Control]: '{key}' locked to '{value}'."


boss_settings = BossLockedSettingsRegistry()


# =====================================================================
# 2. AUTONOMOUS ETHICAL/TECHNICAL REASONER + MANDATORY PERMISSION GATE
# =====================================================================
APPROVAL_KEYWORDS = {
    "approve", "approved", "yes proceed", "go ahead", "do it",
    "execute", "permission granted", "sare chey", "chey", "yes"
}
REJECTION_KEYWORDS = {
    "reject", "deny", "denied", "cancel", "don't do it",
    "no", "abort", "vaddu", "stop"
}


class CosmosSovereignDecisionGate:
    """
    1. Thinks independently about What's Wrong vs. What's Right.
    2. Formulates the Right Decision.
    3. Halts execution in a RAM staging queue and asks Boss Charan for permission.
    """

    def __init__(self):
        self.pending_decision: Optional[Dict[str, Any]] = None

    def propose_decision(
        self,
        user_input: str,
        proposed_action_summary: str,
        execution_callback: Optional[Callable[[], str]] = None,
        candidate_code: str = ""
    ) -> str:
        """Evaluates What's Wrong & Right, selects the right path, and stages it for Boss Charan's explicit permission."""
        verdict = decision_adjudicator.evaluate_everything(
            user_input, COSMOS_UNIFIED_STATE, candidate_code=candidate_code
        )

        # Re-enforce Boss's locked audio settings so somatic engine cannot alter them
        locked_audio = boss_settings.get_audio()
        COSMOS_UNIFIED_STATE["affect"]["tts_rate"] = locked_audio["tts_rate"]
        COSMOS_UNIFIED_STATE["affect"]["tts_pitch"] = locked_audio["tts_pitch"]

        self.pending_decision = {
            "id": f"DEC_{int(time.time())}",
            "timestamp": time.strftime("%H:%M:%S"),
            "user_request": user_input,
            "whats_wrong": verdict.get("whats_wrong") or ["No critical flaws detected."],
            "whats_right": verdict.get("whats_right") or ["Safe operational parameters verified."],
            "chosen_right_decision": proposed_action_summary,
            "optimal_adjudication": verdict.get("optimal_action", "Proceed with validated safe execution."),
            "callback": execution_callback,
            "status": "AWAITING_BOSS_PERMISSION",
        }
        COSMOS_UNIFIED_STATE["pending_permission"] = {
            k: v for k, v in self.pending_decision.items() if k != "callback"
        }

        wrong_bullets = "\n  - ".join(self.pending_decision["whats_wrong"])
        right_bullets = "\n  - ".join(self.pending_decision["whats_right"])

        proposal_msg = (
            f"### ⚖️ COSMOS Autonomous Assessment & Decision Proposal\n"
            f"**1. What's Wrong / Risks Identified:**\n  - {wrong_bullets}\n\n"
            f"**2. What's Right / Validated:**\n  - {right_bullets}\n\n"
            f"**3. My Recommended Right Decision:**\n  - {proposed_action_summary}\n\n"
            f"🔒 **Awaiting Your Permission, Boss:** Shall I proceed with this decision? *(Say **'Approve'** to execute or **'Cancel'** to abort)*."
        )
        return proposal_msg

    def handle_boss_verdict(self, spoken_or_typed: str) -> Optional[str]:
        """Checks if Boss Charan is approving or rejecting the staged decision."""
        if not self.pending_decision:
            return None

        clean = spoken_or_typed.lower().strip()

        if clean in APPROVAL_KEYWORDS or any(clean.startswith(k) for k in APPROVAL_KEYWORDS):
            decision = self.pending_decision
            self.pending_decision = None
            COSMOS_UNIFIED_STATE["pending_permission"] = None

            result_output = "Decision executed as approved."
            if decision.get("callback"):
                try:
                    result_output = decision["callback"]()
                except Exception as e:
                    result_output = f"[Execution Error]: {e}"

            return (
                f"✅ **[Permission Granted by Boss Charan]**: Executing `{decision['chosen_right_decision']}`.\n\n{result_output}"
            )

        if clean in REJECTION_KEYWORDS or any(clean.startswith(k) for k in REJECTION_KEYWORDS):
            aborted = self.pending_decision["chosen_right_decision"]
            self.pending_decision = None
            COSMOS_UNIFIED_STATE["pending_permission"] = None
            return (
                f"🛑 **[Decision Cancelled by Boss Charan]**: Aborted `{aborted}`. Standing by for your next instruction."
            )

        return None


sovereign_gate = CosmosSovereignDecisionGate()


# =====================================================================
# 3. BOSS MANUAL SETTINGS COMMAND PARSER + SOVEREIGN TURN WRAPPER
# =====================================================================
def cosmos_sovereign_turn(spoken_or_typed: str) -> str:
    """
    Drop-in replacement entrypoint that enforces:
    1. Instant 'Stop' Barge-In.
    2. 100% Boss-controlled Audio & System settings commands.
    3. Approval/Rejection check for pending decisions.
    4. Autonomous 'What's Wrong / What's Right' analysis + Mandatory Permission Gate.
    """
    # 1. Check instant Stop keyword
    if voice_barge_engine.check_stop_keyword(spoken_or_typed):
        return "[Audio Halted by Boss]"

    text_l = spoken_or_typed.lower().strip()

    # 2. Direct Boss Audio Control Commands (100% manual)
    if text_l.startswith("set audio ") or text_l.startswith("audio "):
        if "mute on" in text_l or "mute true" in text_l:
            return boss_settings.boss_update_audio("master_mute", True)
        if "mute off" in text_l or "unmute" in text_l:
            return boss_settings.boss_update_audio("master_mute", False)
        for token in spoken_or_typed.split():
            if token.endswith("%") and ("rate" in text_l or "speed" in text_l):
                return boss_settings.boss_update_audio("tts_rate", token)
            if token.endswith("%") and "volume" in text_l:
                return boss_settings.boss_update_audio("volume", token)
            if token.endswith("Hz") and "pitch" in text_l:
                return boss_settings.boss_update_audio("tts_pitch", token)

    # 3. Direct Boss System Control Commands (100% manual)
    if text_l.startswith("set system ") or text_l.startswith("system "):
        if "webcam on" in text_l:
            return boss_settings.boss_update_system("webcam_enabled", True)
        if "webcam off" in text_l:
            return boss_settings.boss_update_system("webcam_enabled", False)
        if "clipboard on" in text_l:
            return boss_settings.boss_update_system("clipboard_sniffer_enabled", True)
        if "clipboard off" in text_l:
            return boss_settings.boss_update_system("clipboard_sniffer_enabled", False)

    # 4. Check if Boss is Approving or Rejecting a Pending Decision
    verdict_response = sovereign_gate.handle_boss_verdict(spoken_or_typed)
    if verdict_response:
        if not boss_settings.get_audio()["master_mute"]:
            try:
                voice_barge_engine.speak_sentence("Understood Boss. Updating execution state now.")
            except Exception:
                pass
        return verdict_response

    # 5. Autonomous Reasoning: Evaluate What's Wrong & Right, Formulate Decision, Ask Permission
    sys_prompt = (
        "You are COSMOS, created exclusively by Sri Charan Tirumaladasu (Boss).\n"
        "SOVEREIGNTY LAW:\n"
        "1. Independently analyze the situation: state clearly WHAT IS WRONG (risks/flaws) and WHAT IS RIGHT.\n"
        "2. Formulate the optimal RIGHT DECISION.\n"
        "3. DO NOT execute any system change or final action without asking Boss Charan's permission first.\n"
        "4. Never attempt to alter audio settings or system settings on your own."
    )

    def _deferred_execution() -> str:
        raw = CosmosRufloHarness.query_hybrid_llm(spoken_or_typed, system_prompt=sys_prompt)
        return OpenBotGovernanceGate.scrub_secrets(raw)

    proposal = sovereign_gate.propose_decision(
        user_input=spoken_or_typed,
        proposed_action_summary=f"Analyze and execute optimal solution for: '{spoken_or_typed[:80]}'",
        execution_callback=_deferred_execution,
    )

    # Speak short permission request only if Boss has not muted audio
    if not boss_settings.get_audio()["master_mute"]:
        try:
            voice_barge_engine.reset_for_speaking()
            voice_barge_engine.speak_sentence(
                "Boss, I have evaluated what is wrong and what is right, and prepared the optimal decision. Please say approve if you want me to proceed."
            )
        except Exception:
            pass

    return proposal
