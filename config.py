import json
import os

# ✅ Define the location of the config file
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_config():
    """
    Loads the configuration from config.json.
    If the file is missing or invalid, it raises an error.
    """
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

if __name__ == "__main__":
    try:
        config = load_config()
        print("✅ Successfully loaded configuration:")
        print(json.dumps(config, indent=2))
    except RuntimeError as e:
        print(str(e))
