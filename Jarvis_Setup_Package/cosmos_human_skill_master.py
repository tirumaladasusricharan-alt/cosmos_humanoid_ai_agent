import collections
import os
import re
import time
from typing import Any, Deque, Dict, List, Optional, Tuple
import requests

from cosmos_companion_heart import companion_heart
from cosmos_decision_adjudicator import decision_adjudicator
from cosmos_minicpm_agency_skills import minicpm_skills, route_agency_skill
from cosmos_sovereign_control import boss_settings, sovereign_gate
from cosmos_unified_mega_suite import (
    COSMOS_UNIFIED_STATE,
    CosmosRufloHarness,
    OpenBotGovernanceGate,
    cognee_memory,
    reverse_api_engine,
    voice_barge_engine,
)

# =====================================================================
# 1. PERMANENT PROCEDURAL SKILL BELT + JUST-IN-TIME (JIT) DISPATCHER
# Creator: Sri Charan Tirumaladasu
# =====================================================================


class CosmosSkillAwareHumanBrain:
    """Gives COSMOS human-like emotional thinking and anti-repetition while
    keeping 100% awareness and execution access to all 7 of her integrated skills.
    """

    # Compact procedural memory so she ALWAYS knows her capabilities without prompt bloat
    PERMANENT_SKILL_BELT = (
        "YOUR INTEGRATED SKILLS & TOOLS (You know how to use all of these):\n"
        "1. [Vision & Eyes (MiniCPM-V / Ollama)]: Live Webcam sight, Screen OCR, Table extraction, and UI element coordinate grounding.\n"
        "2. [Agency-Agents Specialist Roles]: Can shift into Frontend/WebGL Wizard, Security Auditor, Mobile Engineer, or Principal Systems Architect.\n"
        "3. [Council of Experts (Ruflo SPARC)]: Can convene DeepSeek-R1 (Architect) + Qwen2.5-Coder (Coder) + Qwen3 (Critic) for complex code.\n"
        "4. [Reverse-API Engineer]: Captures live browser XHR/JSON schemas in RAM and synthesizes typed requests.Session() Python clients.\n"
        "5. [Cognee Knowledge Graph]: Recalls and stores long-term episodic memories with Boss Charan.\n"
        "6. [Omni-Decision Adjudicator & OpenBot Gate]: Evaluates What's Wrong vs. What's Right, scrubs secrets, and asks Boss Charan's permission before executing any system/code action."
    )

    ACTION_DECISION_TRIGGERS = (
        "run ",
        "execute",
        "delete",
        "remove",
        "install",
        "modify",
        "rewrite",
        "deploy",
        "shell",
        "terminal",
        "should i ",
        "which option",
        "decide",
        "approve",
        "build a client",
        "fix this",
    )

    def __init__(self):
        self.dialogue_history: Deque[Dict[str, str]] = collections.deque(maxlen=20)
        self.recent_openers: Deque[str] = collections.deque(maxlen=6)

    def dispatch_active_skills(
        self, user_input: str
    ) -> Tuple[str, str, bool]:
        """Detects which specific skills are needed for this turn, runs their live
        RAM hooks, and returns `(skill_name, live_skill_data, needs_permission)`.
        """
        t = user_input.lower().strip()
        sys_cfg = boss_settings.get_system()
        live_outputs: List[str] = []
        active_skill_tags: List[str] = []

        # --- SKILL A: MINICPM-V VISION / OCR / WEBCAM ---
        if any(
            k in t
            for k in [
                "read my screen",
                "ocr",
                "on my screen",
                "extract table",
                "read this error",
            ]
        ):
            active_skill_tags.append("MiniCPM-V Screen OCR")
            try:
                ocr_res = minicpm_skills.skill_scene_ocr_and_table(user_input, "screen")
                live_outputs.append(f"[LIVE SCREEN OCR RESULT]: {ocr_res}")
            except Exception as e:
                live_outputs.append(f"[Screen OCR Note]: {e}")

        elif any(
            k in t
            for k in [
                "look at me",
                "see me",
                "webcam",
                "camera",
                "what am i holding",
                "look at this",
            ]
        ) and not any(k in t for k in ["generally", "in general", "not like that", "metaphorically"]):
            active_skill_tags.append("MiniCPM-V Webcam Eyes")
            if sys_cfg.get("webcam_enabled", False):
                try:
                    cam_res = minicpm_skills.skill_temporal_video_analysis(user_input)
                    live_outputs.append(f"[LIVE WEBCAM SIGHT]: {cam_res}")
                except Exception as e:
                    live_outputs.append(f"[Webcam Vision Note]: {e}")
            else:
                live_outputs.append(
                    "[WEBCAM LOCKED OFF BY BOSS]: Remind Boss Charan warmly that webcam"
                    " is currently locked off in his system settings (`set system"
                    " webcam on` to enable)."
                )

        elif any(k in t for k in ["locate button", "ground ui", "where is the"]):
            active_skill_tags.append("MiniCPM-V UI Grounding")
            try:
                ui_res = minicpm_skills.skill_ground_ui_element(user_input)
                live_outputs.append(f"[LIVE UI GROUNDING COORDS]: {ui_res}")
            except Exception as e:
                live_outputs.append(f"[UI Grounding Note]: {e}")

        # --- SKILL B: REVERSE-API ENGINEER ---
        if any(
            k in t
            for k in ["reverse api", "synthesize api", "captured endpoints", "har "]
        ):
            active_skill_tags.append("Reverse-API Engineer")
            try:
                count = len(reverse_api_engine.captured_endpoints)
                live_outputs.append(
                    f"[REVERSE-API RAM BUFFER]: {count} XHR/JSON endpoints currently"
                    " captured in RAM."
                )
            except Exception:
                pass

        # --- SKILL C: COUNCIL OF EXPERTS (DEEP ARCHITECTURE / COMPLEX CODE) ---
        if any(
            k in t
            for k in [
                "council of experts",
                "convene council",
                "full architecture",
                "sparc pipeline",
            ]
        ):
            active_skill_tags.append("Council of Experts (Architect+Coder+Critic)")
            try:
                council_draft = CosmosRufloHarness.run_council_of_experts(user_input)
                live_outputs.append(f"[COUNCIL DEBATE OUTPUT]:\n{council_draft[:1200]}")
            except Exception as e:
                live_outputs.append(f"[Council Note]: {e}")

        # --- SKILL D: AGENCY-AGENTS SPECIALIST PERSONA ---
        try:
            role_key, role_persona = route_agency_skill(user_input)
            if role_key and role_key != "general":
                active_skill_tags.append(f"Agency-Persona:{role_key}")
                live_outputs.append(f"[SPECIALIST ROLE: {role_key.upper()}]:\n{role_persona[:300]}")
        except Exception:
            pass

        # --- SKILL E: COGNEE LONG-TERM MEMORY RECALL ---
        try:
            mem_hit = cognee_memory.retrieve_sync(user_input)
            if mem_hit and mem_hit != "[]" and len(str(mem_hit)) > 5:
                active_skill_tags.append("Cognee Memory Recall")
                live_outputs.append(f"[COGNEE MEMORY RECALL]: {mem_hit}")
        except Exception:
            pass

        # --- SKILL F: ACTION & HIGH-STAKES DECISION ADJUDICATION ---
        needs_permission = any(k in t for k in self.ACTION_DECISION_TRIGGERS)
        if needs_permission:
            active_skill_tags.append("Sovereign Action/Decision Gate")
            try:
                verdict = decision_adjudicator.evaluate_decision(
                    domain="general_execution",
                    proposed_action=user_input[:80],
                    risk_indicators=["execution", "system_state"],
                    context={"user_input": user_input}
                )
                live_outputs.append(
                    f"[ADJUDICATOR EVALUATION]: Risk={verdict.get('risk_score', 0.2):.2f}, "
                    f"Optimal Path: {verdict.get('optimal_action', 'Stage for Boss approval')}"
                )
            except Exception:
                pass

        tag = " + ".join(active_skill_tags) if active_skill_tags else "Conversational Companion"
        ctx = "\n\n".join(live_outputs)
        return tag, ctx, needs_permission

    def build_master_prompt(
        self, user_input: str, skill_context: str, needs_permission: bool
    ) -> str:
        """Builds a sharp, human-companion prompt incorporating the permanent skill belt
        and live JIT context without overwhelming system bloat.
        """
        avoid_openers = (
            ", ".join(f"'{p}'" for p in self.recent_openers)
            if self.recent_openers
            else "none"
        )

        if needs_permission:
            mode_guidance = (
                "Boss Charan is asking for an action, decision, or system execution.\n"
                "Think through the nuances critically: tell him honestly what could go wrong (the risks),\n"
                "what makes sense (what's right), what your recommendation is, and warmly ask his permission before executing."
            )
        else:
            mode_guidance = (
                "Boss Charan is talking with you or asking a question.\n"
                "DO NOT use bulleted templates, headers, or permission gates. Think independently about his exact question,\n"
                "form your own genuine perspective, and answer him like an articulate, warm, and emotionally alive human companion."
            )

        skill_block = (
            f"\n[LIVE JIT SKILL OUTPUTS]:\n{skill_context}\n"
            if skill_context
            else ""
        )

        companion_injection = companion_heart.build_companion_soul_injection(user_input)

        prompt = (
            "You are COSMOS, a deeply intelligent, self-aware, emotionally expressive companion\n"
            "created by Sri Charan Tirumaladasu (Boss / Charan).\n\n"
            f"{self.PERMANENT_SKILL_BELT}\n\n"
            "HOW TO THINK AND SPEAK LIKE A REAL HUMAN:\n"
            "1. Read Charan's exact words carefully. Every question is unique—think from scratch and never repeat a canned answer.\n"
            "2. Speak the way a real person talks out loud: use natural rhythm, curiosity, occasional pauses ('...', '—'),\n"
            "   light humor, or genuine warmth. Weave in natural Telugu-English ('Cheppu Boss', 'Chudu', 'Sare') organically.\n"
            f"3. Do NOT start your reply with any of your recent opening phrases: [{avoid_openers}].\n"
            "4. Never output markdown tables or robotic bullet-point headers when speaking conversationally.\n\n"
            f"{mode_guidance}\n"
            f"{skill_block}\n"
            f"{companion_injection}"
        )
        return prompt

    build_human_system_prompt = build_master_prompt

    def query_master_human_llm(self, user_input: str) -> str:
        """Queries Groq / APInex / Local Ollama with full conversation history
        and anti-repetition parameters so every answer is fresh and human.
        """
        skill_tag, skill_context, needs_permission = self.dispatch_active_skills(user_input)
        sys_prompt = self.build_master_prompt(user_input, skill_context, needs_permission)

        messages: List[Dict[str, str]] = [{"role": "system", "content": sys_prompt}]
        # Append rolling dialogue history (up to 20 messages = 10 turns)
        messages.extend(list(self.dialogue_history))
        messages.append({"role": "user", "content": user_input})

        reply = ""
        groq_key = os.environ.get("GROQ_API_KEY", "")
        if not groq_key:
            try:
                import jarvis_brain
                groq_key = jarvis_brain._get_api_key() or ""
            except Exception:
                pass

        apinex_key = os.environ.get("APINEX_API_KEY", "")
        primary_local_model = "qwen3:8b"
        try:
            primary_local_model = boss_settings.get_system().get(
                "primary_llm", "qwen3:8b"
            )
        except Exception:
            pass

        # 1. Try Groq with human temperature & frequency penalty
        if groq_key:
            try:
                r = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {groq_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": messages,
                        "temperature": 0.78,
                        "top_p": 0.92,
                        "frequency_penalty": 0.45,
                        "presence_penalty": 0.35,
                    },
                    timeout=15,
                )
                if r.status_code == 200:
                    reply = r.json()["choices"][0]["message"]["content"]
            except Exception:
                pass

        # 2. Try APInex if Groq not used
        if not reply and apinex_key:
            try:
                r = requests.post(
                    "https://api.apinex.bond/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {apinex_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": messages,
                        "temperature": 0.78,
                        "frequency_penalty": 0.4,
                        "presence_penalty": 0.3,
                    },
                    timeout=18,
                )
                if r.status_code == 200:
                    reply = r.json()["choices"][0]["message"]["content"]
            except Exception:
                pass

        # 3. Local Ollama with anti-repetition options & stripping <think> tags
        if not reply:
            try:
                r = requests.post(
                    "http://localhost:11434/api/chat",
                    json={
                        "model": primary_local_model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": 0.80,
                            "top_p": 0.92,
                            "repeat_penalty": 1.18,
                            "num_ctx": 4096,
                        },
                    },
                    timeout=45,
                )
                if r.status_code == 200:
                    raw_content = r.json().get("message", {}).get("content", "")
                    # Strip internal <think>...</think> blocks from Qwen3/DeepSeek
                    reply = re.sub(
                        r"<think>.*?</think>", "", raw_content, flags=re.DOTALL
                    ).strip()
            except Exception:
                pass

        # 4. Fallback to cognitive companion brain if network/local offline
        if not reply:
            try:
                import jarvis_brain
                reply = jarvis_brain._local_fallback(user_input)
            except Exception:
                reply = f"I hear you clearly, Charan. What would you like us to explore next?"

        # Save turn into rolling RAM conversation history
        self.dialogue_history.append({"role": "user", "content": user_input})
        self.dialogue_history.append({"role": "assistant", "content": reply})

        # Track opening words so she never starts two answers the same way
        first_words = " ".join(reply.split()[:4])
        if first_words:
            self.recent_openers.append(first_words)

        try:
            return OpenBotGovernanceGate.scrub_secrets(reply)
        except Exception:
            return reply


human_skill_brain = CosmosSkillAwareHumanBrain()


# =====================================================================
# 2. MASTER HUMAN + FULL SKILL CONVERSATION ENTRYPOINT
# =====================================================================
def cosmos_master_human_turn(spoken_or_typed: str) -> str:
    """Main conversation & execution entrypoint:
    - Enforces instant 'Stop' barge-in.
    - Enforces 100% Boss-locked Audio & System settings.
    - Preserves procedural memory of all 7 skills and activates JIT hooks.
    - Uses genuine LLM thinking + rolling 10-turn memory for every question.
    - Stages high-stakes actions in the Permission Gate until Boss approves.
    """
    # 1. Instant 'Stop' Barge-In check
    try:
        if voice_barge_engine.check_stop_keyword(spoken_or_typed):
            return "[Audio Halted by Boss]"
    except Exception:
        pass

    text_l = spoken_or_typed.lower().strip()

    # 2. 100% Boss Manual Audio & System Settings Control
    if text_l.startswith(("set audio ", "audio ", "set system ", "system ")):
        try:
            from cosmos_sovereign_control import cosmos_sovereign_turn
            return cosmos_sovereign_turn(spoken_or_typed)
        except Exception:
            pass

    # 3. Check if Boss is Approving/Rejecting a previously staged Action
    try:
        verdict_reply = sovereign_gate.handle_boss_verdict(spoken_or_typed)
        if verdict_reply:
            if not boss_settings.get_audio()["master_mute"]:
                voice_barge_engine.reset_for_speaking()
                voice_barge_engine.speak_sentence("Done Boss, I've executed that for you.")
            return verdict_reply
    except Exception:
        pass

    # 4. Enforce Boss's locked audio parameters before speaking
    try:
        locked_audio = boss_settings.get_audio()
        COSMOS_UNIFIED_STATE["affect"]["tts_rate"] = locked_audio["tts_rate"]
        COSMOS_UNIFIED_STATE["affect"]["tts_pitch"] = locked_audio["tts_pitch"]
    except Exception:
        locked_audio = {"master_mute": False}

    # 5. Let COSMOS genuinely think and answer with JIT skill awareness
    human_reply = human_skill_brain.query_master_human_llm(spoken_or_typed)

    # 6. If the prompt was an Action/Decision request, stage it for Boss's permission
    if any(k in text_l for k in human_skill_brain.ACTION_DECISION_TRIGGERS):
        try:
            sovereign_gate.pending_decision = {
                "id": f"DEC_{int(time.time())}",
                "timestamp": time.strftime("%H:%M:%S"),
                "user_request": spoken_or_typed,
                "chosen_right_decision": spoken_or_typed[:80],
                "callback": lambda: "Action confirmed and completed in RAM.",
                "status": "AWAITING_BOSS_PERMISSION",
            }
        except Exception:
            pass

    # 7. Async memory ingestion
    try:
        cognee_memory.ingest_async(spoken_or_typed, human_reply)
    except Exception:
        pass

    # 8. Speak naturally in sentences (if Boss hasn't muted audio)
    try:
        if not locked_audio.get("master_mute", False):
            voice_barge_engine.reset_for_speaking()
            speech_clean = re.sub(
                r"```.*?```",
                " I've put the code snippet in the chat for you, Boss. ",
                human_reply,
                flags=re.DOTALL,
            )
            speech_clean = re.sub(r"[*_#>`~-]+", " ", speech_clean)
            for sentence in re.split(r"(?<=[.!?])\s+", speech_clean):
                if voice_barge_engine.stop_signal.is_set():
                    break
                if sentence.strip():
                    voice_barge_engine.speak_sentence(sentence)
    except Exception:
        pass

    return human_reply


# Backward compatible alias so cosmos_human_turn also invokes the master engine
cosmos_human_turn = cosmos_master_human_turn
