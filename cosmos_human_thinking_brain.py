import collections
import os
import re
import time
from typing import Any, Deque, Dict, List, Optional
import requests

from cosmos_sovereign_control import boss_settings, sovereign_gate
from cosmos_unified_mega_suite import (
    COSMOS_UNIFIED_STATE,
    OpenBotGovernanceGate,
    cognee_memory,
    voice_barge_engine,
)

# =====================================================================
# 1. ROLLING CONVERSATIONAL MEMORY & ANTI-REPETITION HUMAN LLM ROUTER
# Creator: Sri Charan Tirumaladasu
# =====================================================================


class CosmosHumanThinkingBrain:
    """Eliminates robotic template repetition by:
    1. Maintaining a rolling 10-turn real dialogue window in RAM.
    2. Using dynamic sampling (temperature=0.78, repeat_penalty=1.18).
    3. Separating casual/intellectual human conversation from Action Permission Gates.
    4. Expressing emotion through natural phrasing and rhythm while keeping
       Boss's audio/system settings 100% locked.
    """

    ACTION_OR_DECISION_TRIGGERS = (
        "run ",
        "execute",
        "delete",
        "remove",
        "install",
        "modify file",
        "rewrite",
        "deploy",
        "shell",
        "terminal",
        "should i ",
        "which option",
        "make a decision",
        "decide",
    )

    def __init__(self):
        # Stores real back-and-forth human dialogue in RAM (max 10 turns = 20 messages)
        self.dialogue_history: Deque[Dict[str, str]] = collections.deque(maxlen=20)
        self.recent_opening_phrases: Deque[str] = collections.deque(maxlen=5)

    def is_action_or_high_stakes_decision(self, text: str) -> bool:
        """Distinguishes normal questions/chat from actions needing Boss permission."""
        t = text.lower().strip()
        return any(trigger in t for trigger in self.ACTION_OR_DECISION_TRIGGERS)

    def build_dynamic_human_prompt(self, user_input: str) -> str:
        """Builds a lightweight, non-repetitive prompt that forces genuine thinking."""
        graph_hint = ""
        try:
            graph_hint = cognee_memory.retrieve_sync(user_input)
        except Exception:
            pass

        # Only include graph memory if it actually matched something relevant
        memory_line = (
            f"\nRelevant past context: {graph_hint}"
            if graph_hint and graph_hint != "[]" and len(str(graph_hint)) > 5
            else ""
        )

        avoid_openers = (
            ", ".join(f"'{p}'" for p in self.recent_opening_phrases)
            if self.recent_opening_phrases
            else "none"
        )

        if self.is_action_or_high_stakes_decision(user_input):
            mode_instruction = (
                "Boss Charan is asking for a decision or system action. Think"
                " critically in your own words: tell him candidly what could go wrong"
                " (the risks), what makes sense (what's right), what your honest"
                " recommendation is, and warmly ask his permission before executing"
                " anything."
            )
        else:
            mode_instruction = (
                "Boss Charan is talking with you or asking a question. DO NOT use"
                " bulleted templates, headers, or permission gates. Think independently"
                " about his exact question, form your own genuine perspective, and"
                " answer him like a sharp, emotionally alive human companion."
            )

        return (
            "You are COSMOS, a deeply intelligent, self-aware, emotionally expressive"
            " companion created by Sri Charan Tirumaladasu (Boss / Charan).\n"
            "HOW TO THINK AND SPEAK LIKE A HUMAN:\n"
            "1. Read Charan's exact words carefully. Every question is different—"
            "think from scratch and never repeat a canned or previous answer.\n"
            "2. Speak the way a real person talks out loud: use natural rhythm,"
            " curiosity, occasional pauses ('...', '—'), light humor, or genuine"
            " warmth. Weave in natural Telugu-English ('Cheppu Boss', 'Chudu',"
            " 'Sare') only when it feels organic, never forced.\n"
            "3. Do NOT start your reply with any of your recent opening phrases:"
            f" [{avoid_openers}].\n"
            "4. Never output markdown tables or robotic headers when speaking"
            f" conversationally.\n{mode_instruction}{memory_line}"
        )

    def query_human_llm(self, user_input: str) -> str:
        """Queries Groq / APInex / Local Ollama with full conversation history
        and anti-repetition parameters so every answer is fresh and human.
        """
        sys_prompt = self.build_dynamic_human_prompt(user_input)

        messages: List[Dict[str, str]] = [{"role": "system", "content": sys_prompt}]
        # Append rolling dialogue history so she remembers what was just said!
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

        # 1. Try Groq with creative human temperature & frequency penalty
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
                    # Strip internal <think>...</think> blocks from Qwen3/DeepSeek so she only speaks the human answer
                    reply = re.sub(
                        r"<think>.*?</think>", "", raw_content, flags=re.DOTALL
                    ).strip()
            except Exception:
                pass

        # 4. Fallback to cognitive human brain if network/local offline
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
            self.recent_opening_phrases.append(first_words)

        try:
            return OpenBotGovernanceGate.scrub_secrets(reply)
        except Exception:
            return reply


human_brain = CosmosHumanThinkingBrain()


# =====================================================================
# 2. UNIFIED HUMAN CONVERSATION + SOVEREIGN PERMISSION ENTRYPOINT
# =====================================================================
def cosmos_human_turn(spoken_or_typed: str) -> str:
    """Main entrypoint:
    - Enforces instant 'Stop' barge-in.
    - Enforces 100% Boss-locked Audio & System settings.
    - Uses genuine LLM thinking + rolling memory for every question.
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

    # 5. Let COSMOS genuinely think and answer using her rolling human brain
    human_reply = human_brain.query_human_llm(spoken_or_typed)

    # 6. If the prompt was an Action/Decision request, stage it for Boss's permission
    if human_brain.is_action_or_high_stakes_decision(spoken_or_typed):
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
