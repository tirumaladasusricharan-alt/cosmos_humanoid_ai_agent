import re
import time
from typing import Any, Dict

# =====================================================================
# COSMOS EMBODIED ACOUSTIC & VISUAL PRESENCE ENGINE (0 MB DISK)
# Creator: Sri Charan Tirumaladasu
# Closes the final 3 physical human gaps WITHOUT touching Boss's locked
# audio settings (volume/rate/pitch remain 100% under Boss's manual lock).
# =====================================================================


class CosmosEmbodiedPresence:

    def __init__(self):
        self.last_boss_speech_duration_sec: float = 0.0
        self.avatar_nonverbal_cue: str = "calm_eye_contact"

    # -----------------------------------------------------------------
    # 1. PARALINGUISTIC LISTENER: DETECTS BOSS'S VOCAL CADENCE & SIGHS
    # -----------------------------------------------------------------
    def analyze_boss_vocal_delivery(
        self, transcript: str, speech_duration_sec: float = 2.0
    ) -> str:
        """Infers Boss Charan's unspoken vocal energy from words-per-second
        and punctuation/hesitation markers without storing audio files.
        """
        words = len(transcript.split())
        wps = words / max(0.5, speech_duration_sec)

        # Detect sarcasm or exhausted flat delivery ("great...", "fine.", "whatever")
        if words <= 4 and any(
            w in transcript.lower()
            for w in ["great", "fine", "whatever", "sure", "okay..."]
        ):
            self.avatar_nonverbal_cue = "empathetic_head_tilt"
            return (
                "[VOCAL SUBTEXT]: Boss's delivery is very brief/flat—he might be tired or unconvinced. "
                "Check in gently rather than assuming excitement."
            )

        if wps > 3.5:
            self.avatar_nonverbal_cue = "attentive_nod_fast"
            return (
                "[VOCAL SUBTEXT]: Boss is speaking rapidly with high urgency/energy."
            )
        if wps < 1.2 and words > 4:
            self.avatar_nonverbal_cue = "soft_listening_gaze"
            return (
                "[VOCAL SUBTEXT]: Boss is speaking slowly and thoughtfully—match his unhurried, reflective pace."
            )

        self.avatar_nonverbal_cue = "warm_eye_contact"
        return "[VOCAL SUBTEXT]: Natural conversational cadence."

    # -----------------------------------------------------------------
    # 2. ACOUSTIC BREATH & CADENCE SHAPER (100% RESPECTS AUDIO LOCK)
    # -----------------------------------------------------------------
    @staticmethod
    def shape_text_for_human_breathing(spoken_text: str) -> str:
        """Shapes punctuation and micro-pauses in the text string so Edge-TTS
        sounds naturally breathed and human WITHOUT changing Boss's locked
        volume, pitch, or rate settings.
        """
        if not spoken_text:
            return ""
        text = spoken_text.strip()
        # Replace stiff colons/semicolons with natural spoken pause dashes
        text = re.sub(r"\s*[:;]\s*", " — ", text)
        # Add a subtle breath comma after conversational openers if missing
        text = re.sub(
            r"^(Honestly|Actually|Wait|Hmm|Chudu Boss|Cheppu Boss|Listen)\s+",
            r"\1, ",
            text,
            flags=re.IGNORECASE,
        )
        return text

    # -----------------------------------------------------------------
    # 3. NON-VERBAL AVATAR GAZE & MICRO-GESTURE TELEMETRY FOR FRONTEND
    # -----------------------------------------------------------------
    def get_avatar_embodiment_state(self, is_thinking: bool = False) -> Dict[str, Any]:
        """Exposes human-like eye-gaze, blink rhythm, and head-tilt states
        to ./cosmos frontend via /api/state.
        """
        if is_thinking:
            return {
                "gaze_target": "up_right_reflective",  # Humans look slightly away when thinking
                "blink_rate_rpm": 18,
                "gesture": "thoughtful_chin_rest",
            }
        return {
            "gaze_target": "direct_boss_eye_contact",
            "blink_rate_rpm": 14,
            "gesture": self.avatar_nonverbal_cue,
        }


embodied_presence = CosmosEmbodiedPresence()
