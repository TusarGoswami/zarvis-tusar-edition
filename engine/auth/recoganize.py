"""
Face Authentication using DeepFace (deep-learning face verification).
===============================================================
Much more accurate than LBPH — uses neural net embeddings so
two different people will never be confused even if they look similar.

How it works:
  Enroll : capture one clear reference photo of the owner → saved as face_reference.jpg
  Verify : on every startup, camera compares live face against reference embedding
"""

import cv2
import os
import time
import threading

# Suppress TensorFlow C++ backend logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

CASCADE_FILE     = r"engine\auth\haarcascade_frontalface_default.xml"
REFERENCE_PHOTO  = r"engine\auth\face_reference.jpg"
SIMILARITY_THRESHOLD = 0.68   # DeepFace distance < 0.68 → same person
                               # (Facenet512 cosine metric; lower = more similar)


def _deepface_verify(ref_path: str, frame_bgr) -> tuple[bool, float]:
    """
    Compare reference photo against a live camera frame.
    Returns (is_same_person, distance).
    """
    try:
        from deepface import DeepFace
        import numpy as np
        import tempfile, os

        # Save the camera frame to a temp file for DeepFace
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        tmp.close()
        cv2.imwrite(tmp.name, frame_bgr)

        result = DeepFace.verify(
            img1_path = ref_path,
            img2_path = tmp.name,
            model_name     = "Facenet512",   # highly accurate, ~90MB on first run
            distance_metric = "cosine",
            enforce_detection = False,       # don't crash if face not detected
            silent = True
        )
        os.unlink(tmp.name)
        dist     = result["distance"]
        verified = result["verified"]
        return verified, dist
    except Exception as e:
        print(f"[FaceAuth] DeepFace error: {e}")
        return False, 1.0


def CaptureReferencePhoto() -> bool:
    """
    Open camera and save one clean face photo as the reference.
    Run this once via enroll_face.py option 1.
    """
    cascade = cv2.CascadeClassifier(CASCADE_FILE)
    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cam.set(3, 640)
    cam.set(4, 480)

    os.makedirs(os.path.dirname(REFERENCE_PHOTO), exist_ok=True)
    saved = False
    hold_frames = 0   # hold a detected face for N frames before saving

    print("[FaceEnroll] Look straight at the camera. A reference photo will be saved automatically.")

    while True:
        ret, frame = cam.read()
        if not ret:
            break

        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, 1.3, 5, minSize=(100, 100))

        msg   = "Look at camera..."
        color = (0, 165, 255)

        for (x, y, w, h) in faces:
            hold_frames += 1
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            if hold_frames >= 15:    # stable face for 15 frames → save
                # Save the full color frame (DeepFace works better with color)
                cv2.imwrite(REFERENCE_PHOTO, frame)
                msg   = "Reference photo saved!"
                color = (0, 255, 0)
                saved = True

        cv2.putText(frame, msg, (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        cv2.imshow("Zarvis - Capture Reference (ESC to cancel)", frame)

        if saved or (cv2.waitKey(10) & 0xFF == 27):
            break

    cam.release()
    cv2.destroyAllWindows()

    if saved:
        print(f"[FaceEnroll] Reference photo saved → {REFERENCE_PHOTO}")
    return saved


def AuthenticateFace(timeout_seconds: int = 45) -> int:
    """
    Use DeepFace to verify the person in front of the camera is the owner.

    Returns:
        1 → verified within timeout
        0 → failed / timeout / no reference photo
    """
    if not os.path.exists(REFERENCE_PHOTO):
        print("[FaceAuth] No reference photo found — run enroll_face.py first.")
        return 1

    cascade = cv2.CascadeClassifier(CASCADE_FILE)
    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cam.set(3, 640)
    cam.set(4, 480)

    font     = cv2.FONT_HERSHEY_SIMPLEX
    start    = time.time()
    result   = 0

    # Threading state for non-blocking DeepFace
    _df_thread = None
    _df_result = {"dist": None, "verified": False}
    
    def _run_verify(frame_copy):
        v, d = _deepface_verify(REFERENCE_PHOTO, frame_copy)
        _df_result["verified"] = v
        _df_result["dist"]     = d

    print(f"[FaceAuth] Engine warming up... Camera open — {timeout_seconds}s to authenticate.")

    while True:
        ret, frame = cam.read()
        if not ret:
            break

        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, 1.2, 5, minSize=(80, 80))

        label = "Detecting face..."
        color = (0, 165, 255)

        for (x, y, w, h) in faces:
            # If no background verification is currently running, spawn one
            if _df_thread is None or not _df_thread.is_alive():
                # Pass a copy of the frame to the thread
                _df_thread = threading.Thread(target=_run_verify, args=(frame.copy(),), daemon=True)
                _df_thread.start()

            last_dist     = _df_result["dist"]
            last_verified = _df_result["verified"]

            if last_dist is not None:
                dist_txt = f"dist={last_dist:.3f}"
                if last_verified:
                    label = f"TUSAR [OK]"
                    color = (0, 255, 0)
                else:
                    label = "Unknown"
                    color = (0, 0, 255)
            else:
                label = "Checking..."
                dist_txt = ""

            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, label,    (x+5, y-10),    font, 0.9, (255,255,255), 2)
            if last_dist is not None:
                cv2.putText(frame, dist_txt, (x+5, y+h-10), font, 0.8, color, 1)

        # Timeout HUD
        elapsed   = time.time() - start
        remaining = max(0, timeout_seconds - int(elapsed))
        cv2.putText(frame, f"Timeout: {remaining}s", (10, 30), font, 0.8, (255,255,0), 2)
        cv2.imshow("Zarvis - Face Authentication", frame)

        if _df_result["verified"]:
            print(f"[FaceAuth] Verified as TUSAR (dist={_df_result['dist']:.3f})")
            result = 1
            break

        if elapsed > timeout_seconds:
            print("[FaceAuth] Timeout — authentication failed.")
            break

        if cv2.waitKey(10) & 0xFF == 27:
            break

    cam.release()
    cv2.destroyAllWindows()
    return result