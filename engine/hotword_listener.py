"""
Zarvis – Flexible Wake Detector
================================
Instead of fixed phrases, Zarvis wakes up whenever you say ANY natural
greeting or address — in English, Hindi, or mixed (Hinglish).

Wake triggers (any one is enough):
  • Starts with a greeting word  : hey, hello, hi, oye, are, aye, yo, bolo, sun
  • Contains an assistant name   : zarvis, jarvis, friday, siri, alexa, cortana
  • Contains a Hindi address word : bhai, yaar, dost, mitra
  • Short isolated phrase (≤ 3 words) that begins with a trigger starter

Examples that WILL wake Zarvis:
  "hey zarvis"            "hello bhai kya haal hai"
  "oye sun mere bhai"     "hey siri tell me"
  "hi friday"             "are yaar"          "yo jarvis"
"""

import speech_recognition as sr
import time
import threading

# ── Words / patterns that signal "the user is addressing me" ─────────────────

# If the text STARTS WITH any of these → wake
_GREETING_STARTERS = {
    # English
    "hey", "hello", "hi", "okay", "ok", "yo", "wake",
    # Hindi / Hinglish
    "oye", "aye", "are", "bolo", "sun", "bol",
}

# If the text CONTAINS any of these ANYWHERE → wake (strong signals)
_NAME_TRIGGERS = {
    "zarvis", "jarvis", "friday", "siri", "alexa", "cortana",
}

# If the text CONTAINS any of these Hindi address words → wake
_HINDI_ADDRESS = {
    "bhai", "yaar", "dost", "mitra",
}


def _is_wake_intent(text: str) -> bool:
    """Return True if the recognised text looks like the user addressing Zarvis."""
    words = text.strip().lower().split()
    if not words:
        return False

    # 1. Starts with a greeting starter word
    if words[0] in _GREETING_STARTERS:
        return True

    # 2. Contains the assistant's name (anywhere in the phrase)
    if any(name in text for name in _NAME_TRIGGERS):
        return True

    # 3. Contains a Hindi affectionate address (anywhere)
    if any(addr in words for addr in _HINDI_ADDRESS):
        return True

    return False


# ─────────────────────────────────────────────────────────────────────────────

_is_listening_for_command = False
_lock = threading.Lock()


def listen_for_wakeword(on_wake_callback, device_index=None):
    """
    Listens indefinitely. Calls on_wake_callback() when the user
    appears to be addressing Zarvis (flexible, language-agnostic detection).
    """
    global _is_listening_for_command
    r = sr.Recognizer()

    # ── One-time calibration (stay quiet for ~1 s) ────────────────────────────
    print("[Wake-Word] Calibrating microphone (stay quiet for 1 second)...")
    with sr.Microphone(device_index=5) as source:
        r.adjust_for_ambient_noise(source, duration=1)

    r.dynamic_energy_threshold = False
    r.energy_threshold = max(r.energy_threshold * 1.2, 150)
    r.pause_threshold = 1.2        # 1.2 s silence → phrase ends
    r.non_speaking_duration = 0.4

    print(f"[Wake-Word] Ready! Threshold: {r.energy_threshold:.0f}")
    print("[Wake-Word] Say anything to address me — 'Hey Zarvis', 'Hello bhai', 'Oye sun', etc.")

    while True:
        with _lock:
            in_command_mode = _is_listening_for_command

        if in_command_mode:
            time.sleep(0.5)
            continue

        try:
            with sr.Microphone(device_index=5) as source:
                audio = r.listen(source, timeout=10, phrase_time_limit=8)

            text = r.recognize_google(audio, language="en-in").lower()
            print(f"[Wake-Word] Heard: \"{text}\"")

            if _is_wake_intent(text):
                print(f"[Wake-Word] ✅ Wake intent detected!")
                with _lock:
                    _is_listening_for_command = True
                on_wake_callback()
                with _lock:
                    _is_listening_for_command = False
                print("[Wake-Word] ↩ Returning to idle...")

        except sr.WaitTimeoutError:
            pass
        except sr.UnknownValueError:
            pass
        except KeyboardInterrupt:
            print("[Wake-Word] Shutting down listener...")
            break
        except Exception as e:
            print(f"[Wake-Word] Error: {e}")
            time.sleep(1)


def set_command_done():
    """Call this after a command finishes to return to idle mode."""
    global _is_listening_for_command
    with _lock:
        _is_listening_for_command = False
