import os
import threading
import eel

from engine.features import *
from engine.command import *
from engine.auth import recoganize
from engine.auth.voice_auth import verify_voice


def _speak_async(text: str):
    """Run speak() in a background thread so it never blocks eel's event loop."""
    t = threading.Thread(target=speak, args=(text,), daemon=True)
    t.start()
    t.join()   # still wait for it to finish before continuing the auth flow


def start():

    eel.init("www")

    playAssistantSound()

    @eel.expose
    def init():
        eel.hideLoader()

        # ── Step 1: Face Authentication ───────────────────────────────────────
        _speak_async("Ready for Face Authentication. Please look at the camera.")
        face_flag = recoganize.AuthenticateFace(timeout_seconds=20)

        if face_flag != 1:
            _speak_async("Face Authentication Failed. Access Denied.")
            return

        eel.hideFaceAuth()
        _speak_async("Face Authentication Successful.")
        eel.hideFaceAuthSuccess()
        playAssistantSound()

        # ── Step 2: Voice Authentication ──────────────────────────────────────
        _speak_async("Now please verify your voice. Say any phrase when ready.")
        voice_ok = verify_voice(timeout=12)

        if not voice_ok:
            _speak_async("Voice Authentication Failed. Access Denied.")
            return

        _speak_async("Voice Authentication Successful. Hello Tusar, Welcome back! How can I help you?")
        eel.hideStart()
        playAssistantSound()

    os.system('start chrome.exe --app="http://localhost:8000/index.html"')
    eel.start('index.html', mode=None, host='localhost', block=True)