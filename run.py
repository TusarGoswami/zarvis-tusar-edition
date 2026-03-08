import multiprocessing
import time


# ─────────────────────────────────────────────
# Process 1: Main Jarvis UI (eel server)
# q = shared Queue passed as argument (Windows-safe IPC)
# ─────────────────────────────────────────────
def startJarvis(q):
    print("Process 1 is running.")
    import threading
    from main import start

    # Background daemon thread watches for WAKE signals from Process 2
    def _watch_queue():
        while True:
            try:
                signal = q.get(timeout=1)
                if signal == "WAKE":
                    print("[Jarvis] Wake signal received — activating...")
                    try:
                        from engine.command import speak
                        speak("Yes, how can I help you?")
                        time.sleep(0.5)
                    except Exception as e:
                        print(f"[Jarvis] speak error: {e}")
                    try:
                        from engine.command import allCommands
                        allCommands(message=1)
                    except Exception as e:
                        print(f"[Jarvis] allCommands error: {e}")
            except Exception:
                pass  # queue timeout – keep looping

    watcher = threading.Thread(target=_watch_queue, daemon=True)
    watcher.start()

    start()  # blocks until eel exits


# ─────────────────────────────────────────────
# Process 2: Wake-Word background listener
# ─────────────────────────────────────────────
def listenHotword(q):
    print("Process 2 is running – Wake-Word listener active.")
    time.sleep(5)   # give Process 1 time to boot up

    from engine.hotword_listener import listen_for_wakeword

    def on_wake():
        print("[Wake-Word] Sending WAKE signal to main process...")
        q.put("WAKE")
        # Pause so command audio isn't re-detected as a wake phrase
        time.sleep(8)

    listen_for_wakeword(on_wake, device_index=1)


# ─────────────────────────────────────────────
# Entry Point
# wake_queue is created ONCE here and passed to both processes via args
# (On Windows, multiprocessing uses spawn – module-level globals are NOT shared)
# ─────────────────────────────────────────────
if __name__ == '__main__':
    wake_queue = multiprocessing.Queue()

    p1 = multiprocessing.Process(target=startJarvis,   args=(wake_queue,))
    p2 = multiprocessing.Process(target=listenHotword, args=(wake_queue,))

    p1.start()
    p2.start()

    p1.join()

    if p2.is_alive():
        p2.terminate()
        p2.join()

    print("system stop")