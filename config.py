import json
import os
from dotenv import load_dotenv

# ✅ Resolve project base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Track whether an env file was loaded
env_loaded = False

# ✅ 1. Prefer .env.override
override_path = os.path.join(BASE_DIR, ".env.override")
if os.path.exists(override_path):
    load_dotenv(dotenv_path=override_path)
    env_loaded = True
    print("✅ Loaded override from .env.override")

# ✅ 2. Fallback to .env.production or .env (based on ENV)
if not env_loaded:
    ENV = os.getenv("ENV", "development")
    env_file = ".env.production" if ENV == "production" else ".env"
    env_path = os.path.join(BASE_DIR, env_file)
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path)
        env_loaded = True
        print(f"✅ Loaded environment: {ENV} from {env_file}")
    else:
        print(f"⚠️ No env file found for {ENV}. Proceeding with defaults.")

# ✅ 3. Finally, load .env.local if it exists (optional overrides)
local_path = os.path.join(BASE_DIR, ".env.local")
if os.path.exists(local_path):
    load_dotenv(dotenv_path=local_path, override=True)
    print("✅ Loaded .env.local (final override layer)")

# --- Exports ---
def get_flask_api_url():
    return os.getenv("FLASK_API_URL", "http://localhost:8002/api/parse_replay")

def load_config():
    config_path = os.path.join(BASE_DIR, "config.json")
    if not os.path.exists(config_path):
        raise RuntimeError(f"❌ Configuration file not found at {config_path}")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"❌ JSON error in config.json: {e}")
    except Exception as e:
        raise RuntimeError(f"❌ Failed to load config.json: {e}")

# ✅ Debug print
print(f"🚀 ENV is: {os.getenv('ENV', 'development')}")
print(f"🌐 FLASK_API_URL is: {os.getenv('FLASK_API_URL')}")
