import os
import threading
import eel

from engine.features import *
from engine.command import *


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
        # Direct transition to Start
        _speak_async("Hello Tusar, Welcome back! How can I help you?")
        eel.hideStart()
        playAssistantSound()

    os.system('start chrome.exe --app="http://localhost:8000/index.html"')
    eel.start('index.html', mode=None, host='localhost', block=True)