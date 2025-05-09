import os
from dotenv import load_dotenv

load_dotenv()

# Rev AI Configuration
REV_AI_API_URL = ["https://api.rev.ai/speechtotext/v1"]
REV_AI_API_KEY = ["02JsFtX2pAFphcKAyTgDjMf06x9XjB-0PCZJvro1E2j2zatcZHU7lxJaJ9wIQwqN1r77GL6OQ5qDx-JQajdPPTSK6-acU"]

# Supported audio formats (based on FFmpeg support)
SUPPORTED_AUDIO_FORMATS = {
    'mp3', 'mp4', 'ogg', 'wav', 'pcm', 'flac', 'aac', 'm4a', 'wma', 'aiff'
}  # Changed to match variable name in rev_ai.py

# Google Sheets Configuration
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_NAME = os.getenv("SHEET_NAME")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Column Mapping
QUESTION_COLUMN_MAP = {
    "Staying Connected": {"link_col": 15, "transcript_col": 16}  # Cols O, P
}
EMAIL_COLUMN_INDEX = 5  # Column E
