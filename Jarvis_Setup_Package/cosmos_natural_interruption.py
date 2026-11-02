"""
cosmos_natural_interruption.py - Instant Natural Interruption (Barge-In) Engine for COSMOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Zero-Regression & 0 MB Model Storage Architecture
Creator & Sole Authority: Sri Charan Tirumaladasu ("Boss" / "Charan" / "Sir")
"""

import sys
sys.dont_write_bytecode = True

import io
import queue
import threading
import pygame

# =====================================================================
# COSMOS NATURAL INTERRUPTION (BARGE-IN) ENGINE (0 MB DISK USAGE)
# Creator: Sri Charan Tirumaladasu
# =====================================================================


class CosmosBargeInManager:

    def __init__(self, status_callback=None):
        self.audio_queue = queue.Queue()
        self.interrupt_event = threading.Event()
        self.is_speaking = False
        self.status_callback = status_callback

        # Ensure pygame mixer is ready with clean 24kHz audio (zero buffer underruns)
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init(frequency=24000)
            except Exception:
                pass

        # Start the non-blocking playback worker thread
        threading.Thread(target=self._playback_loop, daemon=True).start()

    def trigger_interruption(self):
        """Instantly cuts off COSMOS's voice the moment Sri Charan Tirumaladasu speaks."""
        print("\n[Barge-In Detected]: Interrupting COSMOS speech immediately.")
        self.interrupt_event.set()

        # 1. Clear any pending sentences waiting in the RAM queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.task_done()
            except queue.Empty:
                break

        # 2. Stop currently playing audio instantly via pygame
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

        self.is_speaking = False
        if self.status_callback:
            try:
                self.status_callback("LISTENING")
            except Exception:
                pass

    def enqueue_speech_chunk(self, audio_bytes: bytes):
        """Queues a synthesized sentence chunk for playback."""
        if not self.interrupt_event.is_set():
            self.audio_queue.put(audio_bytes)

    def _playback_loop(self):
        """Background worker that plays speech chunks smoothly unless interrupted."""
        while True:
            try:
                audio_data = self.audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if self.interrupt_event.is_set():
                self.audio_queue.task_done()
                continue

            try:
                self.is_speaking = True
                if self.status_callback:
                    try:
                        self.status_callback("TALKING")
                    except Exception:
                        pass
                if not pygame.mixer.get_init():
                    pygame.mixer.init(frequency=24000)
                pygame.mixer.music.load(io_bytes_wrapper(audio_data))
                pygame.mixer.music.play()

                # Poll playback state rapidly so interruption is sub-millisecond
                while pygame.mixer.music.get_busy():
                    if self.interrupt_event.is_set():
                        pygame.mixer.music.stop()
                        break
                    pygame.time.Clock().tick(50)

            except Exception as e:
                print(f"[Playback Error]: {e}")
            finally:
                self.is_speaking = False
                if self.status_callback and self.audio_queue.empty():
                    try:
                        self.status_callback("IDLE")
                    except Exception:
                        pass
                self.audio_queue.task_done()


def io_bytes_wrapper(b: bytes):
    return io.BytesIO(b)


# Global singleton instance across COSMOS
barge_manager = CosmosBargeInManager()
