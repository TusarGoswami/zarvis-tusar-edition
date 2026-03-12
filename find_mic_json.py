import speech_recognition as sr
import struct
import json

def find_working_mic():
    mics = sr.Microphone.list_microphone_names()
    r = sr.Recognizer()
    results = []
    
    for i, name in enumerate(mics):
        if "Output" in name or "Speaker" in name or "Stereo Mix" in name:
            results.append({"index": i, "name": name, "status": "skipped"})
            continue
            
        try:
            with sr.Microphone(device_index=i) as source:
                # listen for 2 seconds
                audio = r.listen(source, timeout=3, phrase_time_limit=2)
                raw_data = audio.frame_data
                if not raw_data:
                    results.append({"index": i, "name": name, "status": "no_data"})
                    continue
                    
                vals = struct.unpack('<' + 'h' * (len(raw_data) // 2), raw_data)
                max_amp = max((abs(v) for v in vals), default=0)
                
                status = "SUCCESS_ACTIVE" if max_amp > 100 else "SILENT"
                results.append({"index": i, "name": name, "status": status, "max_amp": max_amp})
                
        except Exception as e:
            results.append({"index": i, "name": name, "status": "error", "error_msg": str(e)})
            
    with open('mic_test_report.json', 'w') as f:
        json.dump(results, f, indent=4)

if __name__ == '__main__':
    find_working_mic()
