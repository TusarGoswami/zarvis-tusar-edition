"""
Face Enrollment Script for Zarvis (DeepFace version)
=====================================================
Run this ONCE to capture your reference photo.
Zarvis will use it to verify your identity at every startup.

Usage:
    python enroll_face.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.auth.recoganize import CaptureReferencePhoto, REFERENCE_PHOTO


if __name__ == "__main__":
    print("=" * 55)
    print("  Zarvis Face Enrollment (DeepFace)")
    print("=" * 55)
    print()

    if os.path.exists(REFERENCE_PHOTO):
        choice = input("A reference photo already exists. Replace it? (y/n): ").strip().lower()
        if choice != "y":
            print("Keeping existing reference photo. Nothing changed.")
            sys.exit(0)

    print()
    print("Instructions:")
    print("  1. Make sure your face is well-lit (light source in FRONT of you)")
    print("  2. Look straight at the camera")
    print("  3. The photo will be taken automatically when your face is stable")
    print()
    input("Press Enter when ready...")

    import time
    success = CaptureReferencePhoto()

    if success:
        print()
        print("=" * 55)
        print("  Downloading neural network models (first time only) ...")
        from engine.auth.recoganize import _deepface_verify, REFERENCE_PHOTO
        import cv2
        frame = cv2.imread(REFERENCE_PHOTO)
        _deepface_verify(REFERENCE_PHOTO, frame)

        print("=" * 55)
        print("  Enrollment complete!")
        print("  Only YOUR face will now unlock Zarvis.")
        print("=" * 55)
    else:
        print()
        print("Enrollment failed — no face detected. Try again in better lighting.")
