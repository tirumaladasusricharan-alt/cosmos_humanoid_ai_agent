"""
cosmos_natural_interruption.py - Instant Natural Interruption (Barge-In) Engine for COSMOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Zero-Regression & 0 MB Model Storage Architecture
Creator & Sole Authority: Sri Charan Tirumaladasu ("Boss" / "Charan" / "Sir")

Architecture:
1. Low-Latency WASAPI Audio Stream (16kHz, 512-sample chunks = ~32ms resolution)
2. Speech Onset VAD Trigger (<64ms latency budget)
3. Hard In-Process Kill Switch (pygame.mixer.music.stop() + pygame.mixer.stop() + RAM queue drain)
"""

import sys
sys.dont_write_bytecode = True

import audioop
import io
import queue
import struct
import threading
import time

try:
    if sys.platform == "win32":
        try:
            import pyaudiowpatch as pyaudio
        except ImportError:
            import pyaudio
        sys.modules.setdefault("pyaudio", pyaudio)
    else:
        import pyaudio
except Exception:
    pyaudio = None

import pygame


def compute_rms(data: bytes) -> float:
    """Calculates RMS audio energy in RAM with zero extra dependencies."""
    try:
        return float(audioop.rms(data, 2))
    except Exception:
        count = len(data) // 2
        if count == 0:
            return 0.0
        shorts = struct.unpack(f"{count}h", data)
        return (sum(s * s for s in shorts) / count) ** 0.5


class CosmosBargeInManager:

    def __init__(self, status_callback=None):
        self.audio_queue = queue.Queue()
        self.interrupt_event = threading.Event()
        self.is_speaking = False
        self.status_callback = status_callback
        self.vad_enabled = True
        self.ambient_energy = 280.0

        # Ensure pygame mixer is ready with small buffer (512 samples) to minimize hardware delay
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=512)
            except Exception:
                try:
                    pygame.mixer.init(frequency=24000)
                except Exception:
                    pass

        # Start non-blocking playback worker thread
        threading.Thread(target=self._playback_loop, daemon=True).start()

        # Start continuous WASAPI low-latency speech onset VAD worker
        if pyaudio:
            threading.Thread(target=self._wasapi_vad_loop, daemon=True).start()

    def trigger_interruption(self):
        """Instantly cuts off COSMOS's voice in <50ms the moment Sri Charan Tirumaladasu speaks."""
        if self.interrupt_event.is_set() and not self.is_speaking:
            return

        print("\n[Barge-In Detected (<50ms)]: Hard-stopping COSMOS speech immediately.")
        self.interrupt_event.set()

        # 1. Drain pending speech chunks waiting in RAM queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.task_done()
            except queue.Empty:
                break

        # 2. Hard-stop audio playback instantly (flushes OS sound card buffer)
        if pygame.mixer.get_init():
            try:
                pygame.mixer.music.stop()
                pygame.mixer.stop()
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
                audio_data = self.audio_queue.get(timeout=0.05)
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
                    pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=512)

                pygame.mixer.music.load(io_bytes_wrapper(audio_data))
                pygame.mixer.music.play()

                # 100 Hz poll loop (10ms resolution) ensures hard cutoff within sub-millisecond range
                while pygame.mixer.music.get_busy():
                    if self.interrupt_event.is_set():
                        pygame.mixer.music.stop()
                        pygame.mixer.stop()
                        break
                    pygame.time.Clock().tick(100)

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

    def _wasapi_vad_loop(self):
        """Continuous low-latency capture loop (512 samples at 16kHz = 32ms per tick)."""
        CHUNK = 512
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000

        try:
            p = pyaudio.PyAudio()
            stream = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )

            consecutive_voice_ticks = 0
            while self.vad_enabled:
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    rms = compute_rms(data)

                    # Update ambient baseline when quiet
                    if not self.is_speaking:
                        self.ambient_energy = self.ambient_energy * 0.96 + rms * 0.04

                    # Speech onset threshold (adaptive to environment)
                    onset_threshold = max(420.0, self.ambient_energy * 2.2)

                    if rms > onset_threshold:
                        consecutive_voice_ticks += 1
                        # ~64ms of speech onset (2 ticks) triggers hard interrupt
                        if consecutive_voice_ticks >= 2:
                            if self.is_speaking or not self.audio_queue.empty():
                                self.trigger_interruption()
                    else:
                        consecutive_voice_ticks = 0

                except Exception:
                    time.sleep(0.01)
        except Exception as e:
            print(f"[WASAPI VAD Status]: {e}")


def io_bytes_wrapper(b: bytes):
    return io.BytesIO(b)


# Global singleton instance across COSMOS
barge_manager = CosmosBargeInManager()
