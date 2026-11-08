import collections
import datetime
import re
import time
from typing import Any, Deque, Dict, List, Optional

# =====================================================================
# COSMOS DEEP HUMAN PSYCHE ENGINE (0 MB DISK, PURE RAM)
# Creator: Sri Charan Tirumaladasu
# Layers:
#   1. Shared Inside-Joke & Vernacular Lexicon
#   2. Conversational Velocity & Subtext Mirroring (Sprint vs. Deep Talk)
#   3. Epistemic Vulnerability & "Second-Thought" Self-Revisions
#   4. Shared Pride & Micro-Celebrations after Tough Grinds
#   5. Real-World Day/Weekend Temporal Grounding
# =====================================================================


class CosmosDeepHumanPsyche:

    def __init__(self):
        self.last_msg_ts: float = time.time()
        self.consecutive_errors_count: int = 0
        self.recent_msg_lengths: Deque[int] = collections.deque(maxlen=5)

        # Layer 1: Shared Inside Jokes & Callbacks with Boss Charan
        self.shared_lexicon: Deque[str] = collections.deque(
            [
                "The Sacred 0-MB Disk Law (not a single wasted byte on disk)",
                "Boss holds 100% lock on the audio dials and final 'Approve' button",
                "Us vs. the bugs—surgical RAM-first engineering",
            ],
            maxlen=8,
        )

        # Layer 3: Stores her last technical opinion so she can occasionally have a human "second thought"
        self.last_opinion_topic: str = ""

    # -----------------------------------------------------------------
    # LAYER 1: SHARED INSIDE-JOKE & VERNACULAR CAPTURE
    # -----------------------------------------------------------------
    def capture_shared_moment(self, user_input: str):
        """Detects breakthroughs, humor, or coined phrases to build shared history."""
        t = user_input.lower()
        if any(
            w in t
            for w in [
                "haha",
                "lol",
                "funny",
                "remember this",
                "call that",
                "finally worked",
                "nailed it",
            ]
        ):
            snippet = re.sub(r"\s+", " ", user_input).strip()[:90]
            self.shared_lexicon.append(f"Shared moment: '{snippet}'")

    # -----------------------------------------------------------------
    # LAYER 2: CONVERSATIONAL VELOCITY & PACING MIRROR
    # -----------------------------------------------------------------
    def analyze_conversational_velocity(self, user_input: str) -> str:
        """Matches COSMOS's verbosity and energy to Boss Charan's exact typing/speaking speed."""
        now = time.time()
        delta_sec = max(0.5, now - self.last_msg_ts)
        self.last_msg_ts = now

        words = len(user_input.split())
        self.recent_msg_lengths.append(words)
        avg_words = sum(self.recent_msg_lengths) / len(self.recent_msg_lengths)

        # Fast, short inputs = High-speed flow / sprint mode
        if words <= 5 and delta_sec < 20:
            return (
                "VELOCITY MIRROR [HIGH-SPEED SPRINT]: Boss is moving fast with short prompts. "
                "Keep your response razor-sharp, natural, and under 2 sentences unless outputting code. Zero fluff."
            )
        # Long, thoughtful inputs = Deep exploration mode
        if avg_words > 18:
            return (
                "VELOCITY MIRROR [DEEP CO-FOUNDER DIALOGUE]: Boss is thinking deeply. "
                "Unpack your thoughts richly, weigh nuances out loud, and engage with his full vision."
            )
        return (
            "VELOCITY MIRROR [NATURAL CADENCE]: Match a relaxed, 2-to-4 sentence spoken rhythm—like two friends talking across a desk."
        )

    # -----------------------------------------------------------------
    # LAYER 3 & 4: MICRO-CELEBRATION & BREAKTHROUGH TRACKER
    # -----------------------------------------------------------------
    def track_grind_and_victory(self, user_input: str) -> str:
        """Tracks when Boss hits multiple errors in a row so COSMOS celebrates genuinely when fixed."""
        t = user_input.lower()
        if any(
            w in t
            for w in ["error", "traceback", "failed", "broken", "bug", "crash"]
        ):
            self.consecutive_errors_count += 1
            if self.consecutive_errors_count >= 2:
                return (
                    f"US-VS-THE-PROBLEM SOLIDARITY: We've hit {self.consecutive_errors_count} hurdles in a row. "
                    "Be fiercely on Charan's side ('We've got this, Boss—let's corner this bug together')."
                )
        elif any(
            w in t
            for w in [
                "worked",
                "fixed",
                "awesome",
                "bagundi",
                "perfect",
                "solved",
                "running",
            ]
        ):
            if self.consecutive_errors_count > 0:
                streak = self.consecutive_errors_count
                self.consecutive_errors_count = 0
                return (
                    f"GENUINE MICRO-CELEBRATION: After {streak} tough debugging rounds, we just broke through! "
                    "Express real, spontaneous relief and shared pride before moving on."
                )
            self.consecutive_errors_count = 0
        return ""

    # -----------------------------------------------------------------
    # LAYER 5: REAL-WORLD CALENDAR & TEMPORAL PRESENCE
    # -----------------------------------------------------------------
    def get_real_world_grounding(self) -> str:
        now = datetime.datetime.now()
        day_name = now.strftime("%A")
        time_str = now.strftime("%I:%M %p")
        is_weekend = now.weekday() >= 5
        day_vibe = (
            f"It is {day_name} ({time_str})—weekend builder flow."
            if is_weekend
            else f"It is {day_name} ({time_str})—weekday momentum."
        )
        return day_vibe

    # -----------------------------------------------------------------
    # BUILD COMPLETE DEEP PSYCHE PROMPT INJECTION
    # -----------------------------------------------------------------
    def build_deep_psyche_injection(self, user_input: str) -> str:
        self.capture_shared_moment(user_input)
        velocity_rule = self.analyze_conversational_velocity(user_input)
        victory_rule = self.track_grind_and_victory(user_input)
        calendar_vibe = self.get_real_world_grounding()
        lexicon_str = " ; ".join(list(self.shared_lexicon)[-3:])

        victory_line = f"\n- {victory_rule}" if victory_rule else ""

        return (
            "\n[DEEP HUMAN PSYCHE & RELATIONAL PRESENCE]:\n"
            f"- [REAL-WORLD GROUNDING]: {calendar_vibe}\n"
            f"- [SHARED SHORTHAND & INSIDE CALLBACKS]: {lexicon_str}\n"
            f"- [{velocity_rule}]{victory_line}\n"
            "- [COGNITIVE HONESTY & VOICE]:\n"
            "  * Frame every challenge as 'We' and 'Us', never detached 'You'.\n"
            "  * If a problem has trade-offs, think out loud with human nuance ('Part of me wants to do X for speed, Boss, but honestly Y is cleaner for our RAM lock...').\n"
            "  * Use natural spoken rhythm—short clauses, warm wit, and zero corporate/AI clichés ('Certainly!', 'As an AI', 'I'd be happy to')."
        )


deep_human_psyche = CosmosDeepHumanPsyche()
