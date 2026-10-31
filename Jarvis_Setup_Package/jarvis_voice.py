"""
jarvis_voice.py - Live Speech Recognition & Audio Response Loop
Listens continuously through your microphone, processes commands, and speaks back.
"""

import sys
import os

# Safeguard stdout/stderr for background pythonw.exe execution
if sys.stdout is None:
    try:
        sys.stdout = open(os.devnull, "w")
    except Exception:
        pass
if sys.stderr is None:
    try:
        sys.stderr = open(os.devnull, "w")
    except Exception:
        pass
import logging
import re
import subprocess
import time
import threading
import ctypes

# Debug log file for voice thread diagnostics (written even under pythonw.exe)
_voice_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cosmos_voice_debug.log")
_voice_logger = logging.getLogger("cosmos_voice")
_voice_logger.setLevel(logging.DEBUG)
_voice_fh = logging.FileHandler(_voice_log_path, mode="w", encoding="utf-8")
_voice_fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
_voice_logger.addHandler(_voice_fh)

if sys.platform == "win32":
    import pyaudiowpatch as pyaudio

    sys.modules.setdefault("pyaudio", pyaudio)
else:
    import pyaudio

import speech_recognition as sr
import jarvis_brain

_selected_voice = "female"
_voice_lock = threading.Lock()
_speech_lock = threading.Lock()


def _set_windows_output_volume(volume):
    """Set the Windows output volume."""
    winmm = ctypes.windll.winmm
    result = winmm.waveOutSetVolume(0, volume)
    if result != 0:
        raise OSError(result, "Could not set Windows output volume")


def _get_windows_output_volume():
    """Return the current Windows output volume."""
    winmm = ctypes.windll.winmm
    volume = ctypes.c_uint()
    result = winmm.waveOutGetVolume(0, ctypes.byref(volume))
    if result != 0:
        raise OSError(result, "Could not read Windows output volume")
    return volume.value


def get_voice():
    """Return the currently selected speech voice."""
    with _voice_lock:
        return _selected_voice


def set_voice(voice):
    """Keep local text-to-speech on the supported female voice."""
    normalized_voice = voice.casefold()
    if normalized_voice != "female":
        raise ValueError("Only the female voice is available")
    global _selected_voice
    with _voice_lock:
        _selected_voice = "female"


def parse_wake_command(query):
    """Return whether a wake word was spoken and the remaining command."""
    wake_phrase = (
        r"\b(?:(?:hey|ok(?:ay)?|hi|hello)\s+)?"
        r"(?:cosmo(?:s)?|kosmos|kozmos|cosmus|cosmas|cause\s+most|jarvis)\b"
    )
    has_wake_word = re.search(wake_phrase, query, re.IGNORECASE) is not None
    command = re.sub(wake_phrase, " ", query, flags=re.IGNORECASE)
    command = re.sub(r"[^\w\s]", " ", command)
    return has_wake_word, " ".join(command.split())


def is_close_command(query):
    """Return whether a query explicitly asks COSMOS to close."""
    normalized = re.sub(r"[^\w\s]", " ", query.casefold())
    words = " ".join(normalized.split())
    assistant_name = r"(?:cosmo(?:s)?|kosmos)"
    if re.search(
        rf"\bclose yourself\b(?:\s+(?:{assistant_name}|now|please|sir))*$",
        words,
    ):
        return True
    return re.search(
        rf"\b(?:close|quit|exit|shut down)\s+(?:the\s+)?{assistant_name}\b"
        rf"|\b{assistant_name}\s+(?:close|quit|exit|shut down)\b",
        words,
    ) is not None


def speak(text):
    """Speak using the selected voice at full playback volume."""
    if not text:
        return
    print(f"\n[COSMOS]: {text}\n")
    selected_voice = get_voice()
    with _speech_lock:
        if sys.platform == "darwin":
            subprocess.run(["say", "-v", "Samantha", text])
        else:
            try:
                import pyttsx3
                engine = pyttsx3.init()
                voices = engine.getProperty("voices")
                preferred_voice_names = ("zira", "aria", "jenny", "sonia", "samantha")
                matching_voice = next(
                    (
                        voice
                        for preferred_name in preferred_voice_names
                        for voice in voices
                        if preferred_name in f"{voice.id} {voice.name}".casefold()
                    ),
                    None,
                )
                if matching_voice is not None:
                    engine.setProperty("voice", matching_voice.id)
                engine.setProperty("rate", 175)
                previous_output_volume = None
                if sys.platform == "win32":
                    previous_output_volume = _get_windows_output_volume()
                    _set_windows_output_volume(0xFFFFFFFF)
                try:
                    engine.setProperty("volume", 1.0)
                    engine.say(text)
                    engine.runAndWait()
                finally:
                    if previous_output_volume is not None:
                        _set_windows_output_volume(previous_output_volume)
            except Exception as error:
                print(f"[TTS ERROR] Could not speak with the {selected_voice} voice: {error}")


def get_best_microphone_index():
    """Detects and returns the active clean microphone device index, avoiding noisy DirectSound driver bugs."""
    try:
        import audioop

        # 1. Test Windows Default Recording Device (device_index=None) first
        try:
            with sr.Microphone(device_index=None) as source:
                energy = 0
                for _ in range(3):
                    buf = source.stream.read(source.CHUNK)
                    energy += audioop.rms(buf, 2)
                avg_energy = energy / 3
                if 5 < avg_energy < 800:
                    _voice_logger.info(f"Selected default system microphone (device_index=None, energy={avg_energy:.1f})")
                    return None
        except Exception:
            pass

        p = pyaudio.PyAudio()
        candidates = []
        for i in range(p.get_device_count()):
            d = p.get_device_info_by_index(i)
            name = d.get('name', '')
            if d.get('maxInputChannels', 0) > 0 and 'loopback' not in name.lower():
                api = p.get_host_api_info_by_index(d['hostApi']).get('name', '')
                candidates.append((i, name, api))
        p.terminate()

        scored = []
        for idx, name, api in candidates:
            score = 0
            if "mme" in api.lower():
                score += 10
            elif "wasapi" in api.lower():
                score += 5
            elif "directsound" in api.lower():
                score -= 20
            if "microphone array" in name.lower():
                score += 5
            scored.append((score, idx, name, api))
        scored.sort(key=lambda x: x[0], reverse=True)

        for score, idx, name, api in scored:
            try:
                with sr.Microphone(device_index=idx) as source:
                    energy = 0
                    for _ in range(3):
                        buf = source.stream.read(source.CHUNK)
                        energy += audioop.rms(buf, 2)
                    avg_energy = energy / 3
                    if 5 < avg_energy < 800:
                        _voice_logger.info(f"Selected best microphone device: [{idx}] {name} (energy={avg_energy:.1f})")
                        return idx
            except Exception:
                continue
    except Exception as e:
        _voice_logger.warning(f"Error detecting best mic: {e}")
    return None


def listen_for_input(stop_event, enabled_event, ready_event, on_transcript, on_error):
    """Keep listening while enabled and retry recoverable microphone failures."""
    _voice_logger.info("listen_for_input STARTED")
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.energy_threshold = 400
    recognizer.pause_threshold = 1.5
    recognizer.non_speaking_duration = 0.5
    best_mic_idx = get_best_microphone_index()

    while not stop_event.is_set():
        if not enabled_event.wait(timeout=0.1):
            continue
        _voice_logger.info("enabled_event is SET, opening microphone...")
        try:
            with sr.Microphone(device_index=best_mic_idx) as source:
                _voice_logger.info(f"Microphone opened (index={source.device_index}, rate={source.SAMPLE_RATE})")
                recognizer.adjust_for_ambient_noise(source, duration=1.0)
                _voice_logger.info(f"Ambient noise calibrated, energy_threshold={recognizer.energy_threshold:.1f}")
                if recognizer.energy_threshold > 800:
                    recognizer.energy_threshold = 500
                elif recognizer.energy_threshold < 200:
                    recognizer.energy_threshold = 300
                _voice_logger.info(f"Clamped energy_threshold={recognizer.energy_threshold:.1f}")

                listen_cycle = 0
                while enabled_event.is_set() and not stop_event.is_set():
                    listen_cycle += 1
                    ready_is_set = ready_event.is_set()
                    if not ready_is_set:
                        _voice_logger.debug(f"Cycle {listen_cycle}: ready_event NOT set, waiting...")
                    if not ready_event.wait(timeout=0.2):
                        continue
                    if listen_cycle % 20 == 1:
                        _voice_logger.debug(f"Cycle {listen_cycle}: Listening for speech (timeout=5s)...")
                    try:
                        audio = recognizer.listen(source, timeout=5, phrase_time_limit=12)
                    except sr.WaitTimeoutError:
                        if listen_cycle % 20 == 0:
                            _voice_logger.debug(f"Cycle {listen_cycle}: WaitTimeoutError (no speech detected)")
                        continue
                    audio_len = len(audio.get_raw_data())
                    _voice_logger.info(f"Cycle {listen_cycle}: Captured {audio_len} bytes of audio")
                    if stop_event.is_set() or not enabled_event.is_set():
                        _voice_logger.info("Stop/disabled after capture, breaking")
                        break
                    if not ready_event.is_set():
                        _voice_logger.warning("ready_event cleared after capture, skipping recognition")
                        continue
                    ready_event.clear()
                    _voice_logger.info("Sending audio to Google Speech API...")
                    query = ""
                    for lang in ("en-IN", "en-US"):
                        try:
                            candidate = recognizer.recognize_google(audio, language=lang).strip()
                            if candidate:
                                query = candidate
                                break
                        except sr.UnknownValueError:
                            continue
                        except sr.RequestError as e:
                            _voice_logger.error(f"Google API RequestError ({lang}): {e}")
                            continue
                    if not query:
                        _voice_logger.info("Speech not understood across languages, resetting ready_event")
                        ready_event.set()
                        continue
                    if query:
                        _voice_logger.info(f"RECOGNIZED: '{query}' — calling on_transcript")
                        on_transcript(query)
                    else:
                        _voice_logger.info("Empty query after recognition, resetting ready_event")
                        ready_event.set()
        except Exception as e:
            if stop_event.is_set():
                _voice_logger.info(f"Exception after stop: {e}")
                break
            _voice_logger.error(f"Microphone exception: {e}", exc_info=True)
            on_error(e)
            stop_event.wait(0.5)
    _voice_logger.info("listen_for_input EXITED")


def listen_loop():
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8

    while True:
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=1.0)
                print("\n" + "=" * 50)
                print("  COSMOS AI ASSISTANT IS ACTIVE AND LISTENING")
                print("  Say commands like:")
                print("    - 'Cosmos, open VS Code'")
                print("    - 'Play lofi on YouTube'")
                print("    - 'Stock market update' / 'Analyze Nifty'")
                print("    - 'Send WhatsApp message'")
                print("    - 'Read unread emails'")
                print("=" * 50 + "\n")

                while True:
                    try:
                        print("Listening... ", end="", flush=True)
                        audio = recognizer.listen(
                            source, timeout=10, phrase_time_limit=8
                        )
                    except sr.WaitTimeoutError:
                        continue

                    print("Processing... ", end="", flush=True)
                    try:
                        query = recognizer.recognize_google(audio).strip()
                    except sr.UnknownValueError:
                        continue
                    except sr.RequestError as e:
                        print(f"\n[MICROPHONE ERROR] Recognition failed: {e}")
                        continue
                    print(f"\nYou said: \"{query}\"")

                    # Wake word is optional here; direct commands remain supported.
                    _, q_clean = parse_wake_command(query)

                    if not q_clean:
                        speak("Namaste boss, welcome to your world again.")
                        continue

                    response = jarvis_brain.think(q_clean)
                    speak(response)

        except KeyboardInterrupt:
            print("\nShutting down COSMOS. Goodbye!")
            break
        except Exception as e:
            print(f"\n[Notice]: {e}")
            time.sleep(0.5)


if __name__ == "__main__":
    listen_loop()
