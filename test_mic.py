import speech_recognition as sr
import time

def test():
    print("Testing Microphone. Please SPEAK NOW for 5 seconds.")
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=1)
            print(f"Energy threshold set to: {r.energy_threshold}")
            print("Listening...")
            audio = r.listen(source, timeout=10, phrase_time_limit=5)
            print("Audio captured. Saving to test_audio.wav in your folder...")
            with open("test_audio.wav", "wb") as f:
                f.write(audio.get_wav_data())
            print("Calling Google Speech API...")
            try:
                text = r.recognize_google(audio)
                print(f"Google understood: [{text}]")
            except sr.UnknownValueError:
                print("Google didn't hear any English words. Did you speak?")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test()
