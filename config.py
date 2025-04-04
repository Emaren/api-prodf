import json
import os
from dotenv import load_dotenv

# Detect environment (default: development)
ENV = os.getenv("ENV", "development")

# Select .env or .env.production based on ENV
env_file = ".env.production" if ENV == "production" else ".env"
env_path = os.path.join(os.path.dirname(__file__), "aoe2-betting", env_file)

# ✅ Load the correct .env file
load_dotenv(dotenv_path=env_path)
print(f"✅ Loaded environment: {ENV} from {env_file}")

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

# Optional: expose API URLs based on environment
def get_flask_api_url():
    return os.getenv("FLASK_API_URL", "http://localhost:8002/api/parse_replay")
