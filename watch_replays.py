import os
import platform
import time
import logging
import json
import threading
import requests
from watchdog.observers.polling import PollingObserver
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from config import load_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

config = load_config()
config_dirs = config.get("replay_directories", None)
use_polling = config.get("use_polling", True)
polling_interval = config.get("polling_interval", 1)

PROCESSED_REPLAYS_FILE = "processed_replays.json"
processed_replays = {}

# Hardcoded AoE2 replay paths
AOE2HD_REPLAY_DIR = "/Users/tonyblum/Library/Application Support/CrossOver/Bottles/Steam/drive_c/Program Files (x86)/Steam/steamapps/common/Age2HD/SaveGame"
AOE2DE_REPLAY_DIR = os.path.expanduser("~/Documents/My Games/Age of Empires 2 DE/SaveGame")

def load_processed_replays():
    global processed_replays
    try:
        with open(PROCESSED_REPLAYS_FILE, "r") as f:
            processed_replays = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        processed_replays = {}

def save_processed_replays():
    with open(PROCESSED_REPLAYS_FILE, "w") as f:
        json.dump(processed_replays, f, indent=4)

def parse_replay_api(file_path):
    """Tell the Flask API to parse this replay."""
    try:
        # Rewrite path for Docker
        if file_path.startswith(AOE2HD_REPLAY_DIR):
            file_path = file_path.replace(AOE2HD_REPLAY_DIR, "/replays")

        logging.info(f"📂 Sending to parser: {file_path}")
        url = "http://localhost:8002/api/parse_replay"
        resp = requests.post(url, json={"replay_file": file_path})
        if resp.ok:
            logging.info(f"✅ Replay parsed/stored: {file_path}")
        else:
            logging.error(f"❌ Backend error: {resp.text}")
    except Exception as e:
        logging.error(f"❌ API call failed: {e}")

def wait_for_final_state(replay_file):
    """Wait for the replay file to stop growing before triggering parse."""
    stable_delay = 5
    poll_interval = 2
    last_size = -1
    stable_time = 0
    start_time = time.time()

    while True:
        try:
            size = os.path.getsize(replay_file)
        except FileNotFoundError:
            logging.warning(f"File disappeared: {replay_file}")
            return

        if size == last_size:
            stable_time += poll_interval
        else:
            stable_time = 0
            last_size = size

        if stable_time >= stable_delay:
            logging.info(f"🔒 Stable file => parsing: {replay_file}")
            parse_replay_api(replay_file)
            return

        if (time.time() - start_time) > 300:
            logging.warning(f"⚠️ Timeout on: {replay_file}")
            return

        time.sleep(poll_interval)

def on_new_or_modified_replay(replay_file):
    """Skip out-of-sync games, otherwise parse in a thread."""
    if "Out of Sync Save" in replay_file:
        logging.warning(f"⚠️ Skipping out-of-sync replay: {replay_file}")
        return

    t = threading.Thread(target=wait_for_final_state, args=(replay_file,), daemon=True)
    t.start()

class ReplayEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith((".aoe2record", ".aoe2mpgame")):
            logging.info(f"🆕 New replay: {event.src_path}")
            on_new_or_modified_replay(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith((".aoe2record", ".aoe2mpgame")):
            logging.info(f"✍️ Modified replay: {event.src_path}")
            on_new_or_modified_replay(event.src_path)

def get_possible_directories():
    dirs = []
    system = platform.system()
    home = os.path.expanduser("~")

    if system == "Windows":
        userprofile = os.environ.get("USERPROFILE", "")
        dirs += [
            os.path.join(userprofile, "Documents", "My Games", "Age of Empires 2 HD", "SaveGame"),
            os.path.join(userprofile, "Documents", "My Games", "Age of Empires 2 DE", "SaveGame"),
        ]
    elif system == "Darwin":
        dirs.append(AOE2HD_REPLAY_DIR)
        dirs.append(AOE2DE_REPLAY_DIR)
    else:  # Linux
        dirs += [
            os.path.join(home, ".wine/drive_c/Program Files (x86)/Microsoft Games/Age of Empires II HD/SaveGame"),
            os.path.join(home, "Documents/My Games/Age of Empires 2 HD/SaveGame"),
        ]
    return [d for d in dirs if os.path.isdir(d)]

def watch_replay_directories(directories, use_polling=True, interval=1):
    load_processed_replays()
    observer = PollingObserver() if use_polling else Observer()

    for directory in directories:
        if os.path.exists(directory):
            logging.info(f"👀 Watching: {directory}")
            observer.schedule(ReplayEventHandler(), directory, recursive=False)
        else:
            logging.warning(f"⚠️ Missing directory: {directory}")

    observer.start()
    try:
        while True:
            time.sleep(interval)
    except KeyboardInterrupt:
        logging.info("🛑 Stopping watcher.")
        observer.stop()
    observer.join()

if __name__ == '__main__':
    logging.info("📌 Starting Replay Watcher...")
    if config_dirs:
        watch_dirs = config_dirs
    else:
        watch_dirs = get_possible_directories()

    watch_replay_directories(watch_dirs, use_polling=use_polling, interval=polling_interval)
