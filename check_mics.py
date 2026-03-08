"""
Quick diagnostic: lists all available microphones and tests the default one.
Run with: python check_mics.py
"""
import speech_recognition as sr

print("=" * 55)
print("  Available Microphone Devices")
print("=" * 55)
mics = sr.Microphone.list_microphone_names()
for i, name in enumerate(mics):
    print(f"  [{i}] {name}")

print()
print("=" * 55)
print("  Testing default microphone (5 seconds)...")
print("  SPEAK NOW to calibrate your energy threshold.")
print("=" * 55)

r = sr.Recognizer()
r.dynamic_energy_threshold = True

try:
    with sr.Microphone() as source:
        print(f"\n  Initial energy_threshold : {r.energy_threshold:.1f}")
        r.adjust_for_ambient_noise(source, duration=2)
        print(f"  After calibration        : {r.energy_threshold:.1f}")
        print("\n  Trying to listen for 5 seconds... (say something!)")
        audio = r.listen(source, timeout=5, phrase_time_limit=5)
        print("  ✅ Got audio! Recognizing...")
        text = r.recognize_google(audio, language="en-in")
        print(f"  You said: \"{text}\"")
except sr.WaitTimeoutError:
    print("  ❌ Timeout – no speech detected above threshold.")
    print(f"  Final energy_threshold   : {r.energy_threshold:.1f}")
    print("  → Your mic level is too low OR threshold is too high.")
except Exception as e:
    print(f"  ❌ Error: {e}")
