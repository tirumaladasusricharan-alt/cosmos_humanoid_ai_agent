"""Microphone diagnostic for COSMOS — speak into mic when prompted."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pyaudiowpatch as pyaudio
sys.modules.setdefault("pyaudio", pyaudio)
import speech_recognition as sr
import time

r = sr.Recognizer()
r.dynamic_energy_threshold = True
r.energy_threshold = 300
r.pause_threshold = 1.5
r.non_speaking_duration = 0.5

print("=" * 60)
print("  COSMOS MICROPHONE DIAGNOSTIC")
print("=" * 60)
print()

# List mics
mics = sr.Microphone.list_microphone_names()
for i, name in enumerate(mics):
    print(f"  [{i}] {name}")
print()

with sr.Microphone() as source:
    print(f"Default mic index: {source.device_index}")
    print(f"Sample rate: {source.SAMPLE_RATE}")
    print(f"Sample width: {source.SAMPLE_WIDTH}")
    print()
    
    print("Calibrating ambient noise (2 seconds, stay quiet)...")
    r.adjust_for_ambient_noise(source, duration=2)
    print(f"Energy threshold after calibration: {r.energy_threshold:.1f}")
    print()
    
    for attempt in range(3):
        print(f"--- Attempt {attempt+1}/3 ---")
        print("SPEAK NOW (say 'Hey Cosmos' or anything)... ", flush=True)
        try:
            audio = r.listen(source, timeout=6, phrase_time_limit=8)
            raw = audio.get_raw_data()
            print(f"  Captured {len(raw)} bytes of audio")
            
            # Check audio levels
            import struct
            samples = struct.unpack(f"<{len(raw)//2}h", raw)
            peak = max(abs(s) for s in samples)
            rms = (sum(s*s for s in samples) / len(samples)) ** 0.5
            print(f"  Peak amplitude: {peak} (max 32767)")
            print(f"  RMS amplitude:  {rms:.1f}")
            
            if peak < 500:
                print("  WARNING: Audio is VERY quiet — mic may be muted or gain too low")
            elif peak < 2000:
                print("  WARNING: Audio is quiet — consider increasing mic volume")
            else:
                print("  Audio levels look OK")
            
            try:
                text = r.recognize_google(audio)
                print(f"  RECOGNIZED: '{text}'")
                print("  SUCCESS! Microphone is working.")
            except sr.UnknownValueError:
                print("  Google could NOT understand the audio (UnknownValueError)")
                print("  This means audio was captured but speech wasn't clear enough")
            except sr.RequestError as e:
                print(f"  Google API ERROR: {e}")
                print("  Check internet connection!")
        except sr.WaitTimeoutError:
            print("  TIMEOUT — no speech detected within 6 seconds")
            print(f"  Current energy_threshold: {r.energy_threshold:.1f}")
            print("  This means the mic isn't picking up sound above the noise floor")
        print()
    
    print("Diagnostic complete.")

