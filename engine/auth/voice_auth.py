"""
Voice Authentication – Speaker Verification
=============================================
Uses MFCC (Mel-frequency cepstral coefficients) fingerprinting to verify
that the person speaking is the enrolled owner (Tusar).

Workflow
--------
1. ENROLL  : run `python engine/auth/enroll_voice.py` once to record your
             voice and save a reference fingerprint.
2. VERIFY  : call verify_voice() at startup – it records a short clip and
             compares its MFCC with the saved fingerprint.
"""

import os
import sys
import numpy as np
import speech_recognition as sr

# ── Paths ─────────────────────────────────────────────────────────────────────
_AUTH_DIR        = os.path.join("engine", "auth")
VOICE_MODEL_PATH = os.path.join(_AUTH_DIR, "voice_model.npy")

# ── Tuning ────────────────────────────────────────────────────────────────────
SIMILARITY_THRESHOLD = 0.88   # cosine similarity; raise to be stricter
N_MFCC               = 40     # number of MFCC coefficients
SAMPLE_RATE          = 16000  # Hz — speech_recognition default


# ── MFCC helpers ──────────────────────────────────────────────────────────────

def _audio_to_array(audio: sr.AudioData) -> np.ndarray:
    """Convert speech_recognition AudioData → float32 numpy array."""
    raw = audio.get_raw_data(convert_rate=SAMPLE_RATE, convert_width=2)
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
    # Normalise to [-1, 1]
    if samples.max() != 0:
        samples /= 32768.0
    return samples


def _mfcc(samples: np.ndarray, n_mfcc: int = N_MFCC) -> np.ndarray:
    """Compute mean MFCC vector from a mono float32 array using librosa."""
    import librosa
    mfcc_matrix = librosa.feature.mfcc(y=samples, sr=SAMPLE_RATE, n_mfcc=n_mfcc)
    return np.mean(mfcc_matrix, axis=1)   # shape: (n_mfcc,)


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two 1-D vectors (range –1 … 1)."""
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


# ── Capture a voice sample ────────────────────────────────────────────────────

def _record_sample(prompt: str = "Say a phrase...",
                   timeout: int = 10,
                   phrase_limit: int = 6) -> np.ndarray | None:
    """
    Open the microphone, prompt the user, record one phrase, return numpy array.
    Returns None on error.
    """
    r = sr.Recognizer()
    r.dynamic_energy_threshold = False
    r.energy_threshold = 300
    r.pause_threshold  = 1.0

    print(f"[VoiceAuth] {prompt}")
    try:
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
        return _audio_to_array(audio)
    except sr.WaitTimeoutError:
        print("[VoiceAuth] No speech detected (timeout).")
        return None
    except Exception as e:
        print(f"[VoiceAuth] Recording error: {e}")
        return None


# ── Public API ────────────────────────────────────────────────────────────────

def enroll(n_samples: int = 5) -> bool:
    """
    Record n_samples voice clips, average their MFCCs, save to VOICE_MODEL_PATH.
    Returns True on success.
    """
    phrases = [
        "Hey Zarvis, ready for authentication",
        "My name is Tusar and I am the owner",
        "Open Chrome and search Google",
        "Hello Zarvis, how are you today",
        "Voice recognition authentication complete",
    ]

    vectors = []
    print(f"\n[VoiceAuth] Starting enrollment – {n_samples} samples needed.")
    print("[VoiceAuth] Speak naturally and clearly after each prompt.\n")

    for i in range(n_samples):
        phrase = phrases[i % len(phrases)]
        print(f"[VoiceAuth] Sample {i+1}/{n_samples} — please say:")
        print(f'  ➜  "{phrase}"')

        samples = _record_sample(
            prompt="Recording... (speak now)",
            timeout=8,
            phrase_limit=6
        )
        if samples is None:
            print("[VoiceAuth] ⚠  No audio captured, skipping this sample.")
            continue

        vec = _mfcc(samples)
        vectors.append(vec)
        print(f"[VoiceAuth] ✅ Sample {i+1} captured.\n")

    if len(vectors) < 2:
        print("[VoiceAuth] ❌ Not enough valid samples to enroll.")
        return False

    reference = np.mean(vectors, axis=0)
    os.makedirs(_AUTH_DIR, exist_ok=True)
    np.save(VOICE_MODEL_PATH, reference)
    print(f"[VoiceAuth] 🎤 Voice model saved to: {VOICE_MODEL_PATH}")
    return True


def verify_voice(timeout: int = 10) -> bool:
    """
    Record a short clip and compare against the enrolled voice fingerprint.

    Returns True if the speaker matches the enrolled owner.
    Returns True (bypass) if no model file found — so Zarvis still starts
    even before first enrollment.
    """
    if not os.path.exists(VOICE_MODEL_PATH):
        print("[VoiceAuth] No voice model found — skipping voice auth (run enroll_voice.py first).")
        return True   # graceful bypass until user runs enrollment

    try:
        reference = np.load(VOICE_MODEL_PATH)
    except Exception as e:
        print(f"[VoiceAuth] Could not load voice model: {e}")
        return True

    print("[VoiceAuth] 🎤 Please say a phrase to verify your voice...")
    samples = _record_sample(
        prompt="Recording voice — speak now (up to 6 seconds)",
        timeout=timeout,
        phrase_limit=6
    )
    if samples is None:
        print("[VoiceAuth] ❌ Voice verification failed — no audio.")
        return False

    try:
        candidate = _mfcc(samples)
    except Exception as e:
        print(f"[VoiceAuth] MFCC error: {e}")
        return False

    sim = _cosine_similarity(reference, candidate)
    print(f"[VoiceAuth] Similarity score: {sim:.4f}  (threshold: {SIMILARITY_THRESHOLD})")

    if sim >= SIMILARITY_THRESHOLD:
        print("[VoiceAuth] ✅ Voice verified!")
        return True
    else:
        print("[VoiceAuth] ❌ Voice not recognised.")
        return False
