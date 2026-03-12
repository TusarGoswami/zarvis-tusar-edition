import speech_recognition as sr
import struct

def find_working_mic():
    print("Searching for a working microphone...")
    mics = sr.Microphone.list_microphone_names()
    r = sr.Recognizer()
    
    working_mics = []
    
    for i, name in enumerate(mics):
        # Skip output devices to save time
        if "Output" in name or "Speaker" in name:
            continue
            
        print(f"\n[{i}] Testing: {name}")
        try:
            with sr.Microphone(device_index=i) as source:
                # We don't adjust for ambient noise here, we just want to see if it picks up ANY raw amplitude
                print("  Listening for 1.5 seconds... MAKE SOME NOISE!")
                audio = r.listen(source, timeout=3, phrase_time_limit=1.5)
                
                # Get raw PCM data
                raw_data = audio.frame_data
                if not raw_data:
                    print("  -> No data captured.")
                    continue
                    
                # Unpack 16-bit PCM
                vals = struct.unpack('<' + 'h' * (len(raw_data) // 2), raw_data)
                max_amp = max((abs(v) for v in vals), default=0)
                
                print(f"  -> Max volume detected: {max_amp} (out of 32768)")
                
                if max_amp > 100:
                    print("  *** SUCCESS! This microphone picks up sound! ***")
                    working_mics.append(i)
                else:
                    print("  -> This microphone is completely silent.")
                    
        except sr.WaitTimeoutError:
            print("  -> Timed out waiting for speech.")
        except Exception as e:
            print(f"  -> Error: {e}")
            
    print("\n=======================================================")
    if working_mics:
        print(f"Found working microphones at indexes: {working_mics}")
        print("We can try hardcoding one of these indexes into the code!")
    else:
        print("COULD NOT FIND ANY BREATHE OF LIFE FROM ANY MICROPHONE.")
        print("This means Windows/Hardware is physically muting the input before Python sees it.")

if __name__ == '__main__':
    find_working_mic()
