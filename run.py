import multiprocessing
import time


# ─────────────────────────────────────────────
# Process 1: Main Jarvis UI (eel server)
# wake_q  → P2 sends "WAKE" here when hotword fires
# done_q  → P1 sends "DONE" here when speaking + command finish
# ─────────────────────────────────────────────
def startJarvis(wake_q, done_q):
    print("Process 1 is running.")
    import threading
    from main import start

    # Background daemon thread watches for WAKE signals from Process 2
    def _watch_queue():
        while True:
            try:
                signal = wake_q.get(timeout=1)
                if signal == "WAKE":
                    print("[Jarvis] Wake signal received — activating...")
                    try:
                        from engine.command import speak
                        speak("Yes, how can I help you?")
                        time.sleep(0.3)
                    except Exception as e:
                        print(f"[Jarvis] speak error: {e}")
                    try:
                        from engine.command import allCommands
                        allCommands(message=1)
                    except Exception as e:
                        print(f"[Jarvis] allCommands error: {e}")
                    finally:
                        # Signal Process 2 that we are fully done speaking
                        # so it can safely resume listening for the wake word
                        done_q.put("DONE")
            except Exception:
                pass  # queue timeout – keep looping

    watcher = threading.Thread(target=_watch_queue, daemon=True)
    watcher.start()

    start()  # blocks until eel exits


# ─────────────────────────────────────────────
# Process 2: Wake-Word background listener
# ─────────────────────────────────────────────
def listenHotword(wake_q, done_q):
    print("Process 2 is running – Wake-Word listener active.")
    time.sleep(5)   # give Process 1 time to boot up

    from engine.hotword_listener import listen_for_wakeword

    def on_wake():
        print("[Wake-Word] Sending WAKE signal to main process...")
        wake_q.put("WAKE")
        # Wait for Process 1 to signal it has finished speaking & processing.
        # This prevents the mic from picking up Zarvis's own TTS output.
        print("[Wake-Word] Waiting for Zarvis to finish speaking...")
        try:
            done_q.get(timeout=90)   # up to 90 s for long responses
        except Exception:
            pass  # timeout safety valve
        # Small extra buffer so the last TTS word doesn't bleed into mic
        time.sleep(2)
        print("[Wake-Word] ↩ Ready for next wake word...")

    listen_for_wakeword(on_wake)


# ─────────────────────────────────────────────
# Entry Point
# Queues are created ONCE and passed to both processes via args.
# (On Windows, multiprocessing uses spawn – module-level globals NOT shared)
# ─────────────────────────────────────────────
if __name__ == '__main__':
    wake_queue = multiprocessing.Queue()   # P2 → P1 : "WAKE"
    done_queue = multiprocessing.Queue()   # P1 → P2 : "DONE"

    p1 = multiprocessing.Process(target=startJarvis,   args=(wake_queue, done_queue))
    p2 = multiprocessing.Process(target=listenHotword, args=(wake_queue, done_queue))

    p1.start()
    p2.start()

    p1.join()

    if p2.is_alive():
        p2.terminate()
        p2.join()

    print("system stop")