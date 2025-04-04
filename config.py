import json
import os
from dotenv import load_dotenv

# ✅ Load .env file from root or aoe2-betting subdir
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "aoe2-betting", ".env"))

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    if not os.path.exists(CONFIG_FILE):
        raise RuntimeError(f"❌ Configuration file not found at {CONFIG_FILE}. Please ensure config.json is present.")

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config
    except json.JSONDecodeError as e:
        raise RuntimeError(f"❌ Failed to load configuration due to JSON format error: {e}")
    except Exception as e:
        raise RuntimeError(f"❌ Unexpected error while loading configuration: {e}")
