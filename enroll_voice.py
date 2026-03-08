"""
Voice Enrollment Script for Zarvis
====================================
Run this ONCE to record your voice fingerprint.
After this, Zarvis will verify your voice on every startup.

Usage:
    python enroll_voice.py
"""

import sys
import os

# Make sure project root is on path
sys.path.insert(0, os.path.dirname(__file__).replace("\\engine\\auth", "").replace("/engine/auth", ""))

from engine.auth.voice_auth import enroll

if __name__ == "__main__":
    print("=" * 55)
    print("  Zarvis Voice Enrollment")
    print("=" * 55)
    print("You will be asked to say 5 short phrases.")
    print("Speak clearly and at a normal volume.")
    print("=" * 55 + "\n")

    success = enroll(n_samples=5)

    if success:
        print("\n✅ Enrollment complete!")
        print("   Zarvis will now verify your voice on every startup.")
    else:
        print("\n❌ Enrollment failed. Please try again.")
