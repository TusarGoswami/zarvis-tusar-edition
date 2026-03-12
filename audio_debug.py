import pyaudio

def report_audio_devices():
    p = pyaudio.PyAudio()
    out = []
    try:
        default_in = p.get_default_input_device_info()
        out.append(f"--- DEFAULT INPUT DEVICE ---")
        out.append(f"Name: {default_in['name']}")
        out.append(f"Index: {default_in['index']}")
        out.append(f"Channels: {default_in['maxInputChannels']}")
        out.append(f"Sample Rate: {default_in['defaultSampleRate']}")
    except Exception as e:
        out.append(f"Could not get default input device: {e}")

    out.append("\n--- ALL AVAILABLE AUDIO INPUTS ---")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            out.append(f"[{info['index']}] {info['name']} (Channels: {info['maxInputChannels']}, API: {info['hostApi']})")

    p.terminate()

    with open('audio_info.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))

if __name__ == '__main__':
    report_audio_devices()
