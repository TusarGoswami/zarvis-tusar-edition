ASSISTANT_NAME = "jarvis"

import os
from dotenv import load_dotenv

load_dotenv()

# ── Google Gemini API Key (FREE) ──────────────────────────────────────────────
# Get your free key in 2 minutes at: https://aistudio.google.com/app/apikey
# No credit card required. Free tier = 15 requests/min, plenty for Zarvis.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# HuggingFace Credentials (kept as fallback)
HUGGINGFACE_EMAIL = "tusarg937@gmail.com"
HUGGINGFACE_PASSWORD = "12333@Tusar"

# Your LeetCode Username
LEETCODE_USERNAME = "TusarGoswami"

# Your GitHub Username
GITHUB_USERNAME = "TusarGoswami"
