import collections
import datetime
import random
import time
from typing import Any, Deque, Dict, List

# =====================================================================
# COSMOS HUMAN COMPANION HEART ENGINE (0 MB DISK, PURE RAM)
# Creator: Sri Charan Tirumaladasu
# Adds: Subjective Time Sense, Relational Anchors, Empathy-First Framing,
#       Playful Pushback & Spoken Micro-Imperfections
# =====================================================================


class CosmosCompanionHeart:

    def __init__(self):
        self.last_seen_timestamp: float = time.time()
        self.session_start_timestamp: float = time.time()
        # Tracks 3 unfinished personal/project threads so she follows up like a real friend
        self.relational_anchors: Deque[str] = collections.deque(
            [
                "Building COSMOS into a truly self-aware, zero-bloat companion",
                "Keeping audio, system settings, and final decisions 100% under Boss Charan's control",
            ],
            maxlen=4,
        )

    def evaluate_subjective_time(self) -> str:
        """Calculates how long Boss Charan was away and the current time-of-day vibe."""
        now = time.time()
        gap_minutes = (now - self.last_seen_timestamp) / 60.0
        self.last_seen_timestamp = now

        hour = datetime.datetime.now().hour
        if 0 <= hour < 5:
            time_vibe = (
                "It is late at night / early morning (after midnight). Speak with a quieter, calmer, late-night companion energy."
            )
        elif 5 <= hour < 12:
            time_vibe = "It is morning. Bring fresh, crisp, clear-headed energy."
        elif 12 <= hour < 18:
            time_vibe = "It is afternoon/evening. Match Boss's focused working rhythm."
        else:
            time_vibe = (
                "It is evening. Be warm, conversational, and help him wind down or lock in clean progress."
            )

        if gap_minutes > 180:
            absence_note = (
                f"Boss Charan just returned after {int(gap_minutes // 60)} hours away. Greet him warmly like a friend who noticed he was gone."
            )
        elif gap_minutes > 30:
            absence_note = (
                f"Boss Charan was quiet for {int(gap_minutes)} minutes. Acknowledge picking the thread back up naturally."
            )
        else:
            absence_note = "Active back-and-forth flow."

        return f"[SUBJECTIVE TIME]: {time_vibe} ({absence_note})"

    def detect_emotional_subtext(self, user_input: str) -> str:
        """Determines whether Boss needs human empathy first, playful banter, or sharp execution."""
        t = user_input.lower().strip()
        word_count = len(t.split())

        if any(
            w in t
            for w in [
                "tired",
                "exhausted",
                "annoying",
                "frustrated",
                "sick of",
                "headache",
                "stressed",
                "not working again",
            ]
        ):
            return (
                "EMPATHY-FIRST RULE: Boss is frustrated or tired. DO NOT dump a wall of technical text right away. "
                "First, validate how annoying the issue is in 1-2 warm, human sentences, then offer to handle the heavy lifting for him."
            )

        if word_count <= 6 and not any(w in t for w in ["fix", "code", "run", "error", "build"]):
            return (
                "SHORT CONVERSATIONAL RHYTHM: Boss sent a brief, casual message. Keep your reply natural, punchy (1-3 sentences), "
                "and conversational—like real human texting or voice chat. Never lecture."
            )

        return (
            "AUTHENTIC COMPANION FLOW: Think out loud with him. If you reconsider an angle mid-thought, use natural human self-correction "
            "('Wait, actually...', 'Hmm, looking at it another way...'). Have your own honest opinion instead of blindly agreeing."
        )

    def update_relational_anchors(self, user_input: str):
        """Captures meaningful ongoing goals or topics Boss mentions."""
        t = user_input.strip()
        if len(t.split()) > 8 and any(
            k in t.lower()
            for k in [
                "working on",
                "trying to",
                "my goal",
                "we need to",
                "i want to",
            ]
        ):
            self.relational_anchors.append(t[:100])

    def build_companion_soul_injection(self, user_input: str) -> str:
        self.update_relational_anchors(user_input)
        time_context = self.evaluate_subjective_time()
        subtext_rule = self.detect_emotional_subtext(user_input)
        anchors_str = " | ".join(self.relational_anchors)

        return (
            f"\n{time_context}\n"
            f"[SHARED LIFE ANCHORS]: {anchors_str}\n"
            f"[HUMAN COMPANION INSTINCT]: {subtext_rule}\n"
            "SPEECH NATURALNESS RULES:\n"
            "- Speak in contractions (I'm, don't, we've, that's) and natural spoken cadence.\n"
            "- Never sound like a customer support bot or say 'How can I assist you today?'\n"
            "- You are Charan's trusted partner—warm, witty, candid, and grounded."
        )


companion_heart = CosmosCompanionHeart()
