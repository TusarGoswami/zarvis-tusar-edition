"""
Zarvis Wake-Word Listener
Continuously listens in background for the phrase "hey friday"
and triggers the full speech recognition pipeline.
"""

import speech_recognition as sr
import time
import threading

WAKE_WORDS = ["hey friday", "hey jarvis", "ok friday", "okay friday"]

_is_listening_for_command = False
_lock = threading.Lock()


def listen_for_wakeword(on_wake_callback, device_index=1):
    """
    Runs indefinitely, listening for any of the WAKE_WORDS.
    When detected, calls on_wake_callback() exactly once.
    """
    global _is_listening_for_command
    r = sr.Recognizer()
    r.energy_threshold = 2500       # Sensitivity – raise if false activations
    r.dynamic_energy_threshold = True
    r.pause_threshold = 0.6

    print("[Wake-Word] Listening for 'Hey Friday'...")

    while True:
        with _lock:
            in_command_mode = _is_listening_for_command

        if in_command_mode:
            # Already processing a command – wait until it finishes
            time.sleep(0.5)
            continue

        try:
            with sr.Microphone(device_index=device_index) as source:
                r.adjust_for_ambient_noise(source, duration=0.3)
                # Short timeout so we loop quickly and stay responsive
                audio = r.listen(source, timeout=4, phrase_time_limit=4)

            text = r.recognize_google(audio, language="en-in").lower()
            print(f"[Wake-Word] Heard: {text}")

            if any(wake in text for wake in WAKE_WORDS):
                print("[Wake-Word] ✅ Wake word detected!")
                with _lock:
                    _is_listening_for_command = True
                on_wake_callback()
                with _lock:
                    _is_listening_for_command = False
                print("[Wake-Word] ↩ Returning to idle mode...")

        except sr.WaitTimeoutError:
            pass        # Normal – nothing was said
        except sr.UnknownValueError:
            pass        # Could not understand audio
        except Exception as e:
            # E.g. device errors – wait briefly then retry
            print(f"[Wake-Word] Error: {e}")
            time.sleep(1)


def set_command_done():
    """Call this after a command finishes to return to idle mode."""
    global _is_listening_for_command
    with _lock:
        _is_listening_for_command = False
