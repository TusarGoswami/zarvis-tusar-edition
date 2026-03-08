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


def listen_for_wakeword(on_wake_callback, device_index=None):
    """
    Runs indefinitely, listening for any of the WAKE_WORDS.
    When detected, calls on_wake_callback() exactly once.
    """
    global _is_listening_for_command
    r = sr.Recognizer()

    # ── One-time calibration BEFORE the loop ──────────────────────────────────
    # adjust_for_ambient_noise inside the loop causes the threshold to spike
    # wildly if you speak during the 0.3 s calibration window.
    print("[Wake-Word] Calibrating microphone (stay quiet for 1 second)...")
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=1)

    # Lock the threshold in place – dynamic adjustment inside a short loop
    # causes enormous swings (threshold can jump to 900+ when noisy).
    r.dynamic_energy_threshold = False
    # Add a small margin on top of the ambient level so soft background sounds
    # don't trip the recognizer, but normal speech comfortably gets through.
    r.energy_threshold = max(r.energy_threshold * 1.2, 150)

    # Give more time for natural speech – 0.6 s pauses cut off words mid-sentence
    r.pause_threshold = 1.2        # wait 1.2 s of silence before ending phrase
    r.non_speaking_duration = 0.4  # exclude short silences inside a phrase

    print(f"[Wake-Word] Ready! Threshold locked at {r.energy_threshold:.0f}")
    print("[Wake-Word] Listening for 'Hey Friday'...")

    while True:
        with _lock:
            in_command_mode = _is_listening_for_command

        if in_command_mode:
            # Already processing a command – wait until it finishes
            time.sleep(0.5)
            continue

        try:
            with sr.Microphone() as source:
                # timeout   → how long to wait for speech to START (seconds)
                # phrase_time_limit → max length of the captured phrase (seconds)
                audio = r.listen(source, timeout=10, phrase_time_limit=12)

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
            pass        # Normal – nothing was said in the timeout window
        except sr.UnknownValueError:
            pass        # Audio captured but Google couldn't understand it
        except KeyboardInterrupt:
            print("[Wake-Word] Shutting down listener...")
            break       # Exit cleanly on Ctrl+C
        except Exception as e:
            print(f"[Wake-Word] Error: {e}")
            time.sleep(1)


def set_command_done():
    """Call this after a command finishes to return to idle mode."""
    global _is_listening_for_command
    with _lock:
        _is_listening_for_command = False
