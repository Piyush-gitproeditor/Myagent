import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("NEBIUS_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BASE_URL = "https://api.tokenfactory.nebius.com/v1/"
DB_PATH = BASE_DIR / "opps.db"

# Confirm exact IDs with find_model.py below (names are case-sensitive)
MODELS = [
    "nvidia/nemotron-3-super-120b-a12b",
    "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
    "nvidia/Nemotron-3-Ultra-550b-a55b",
    "nvidia/Nemotron-3_5-Lightning",
]
MODEL = MODELS[0]

if not API_KEY:
    raise SystemExit("NEBIUS_API_KEY not found. Check .env is in the project root "
                     "and named exactly '.env' (not '.env.txt').")