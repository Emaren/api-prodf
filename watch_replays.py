import os
import platform
import time
import logging
import json
import threading
import io
from watchdog.observers.polling import PollingObserver
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from mgz import header, summary
from config import load_config

# ✅ Load configuration from config.json
config = load_config()
config_dirs = config.get("replay_directories", None)
use_polling = config.get("use_polling", True)
polling_interval = config.get("polling_interval", 1)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ✅ File to store processed replays
PROCESSED_REPLAYS_FILE = "processed_replays.json"
processed_replays = {}

# ✅ Define AoE2HD and AoE2DE Replay Directories
AOE2HD_REPLAY_DIR = "/Users/tonyblum/Library/Application Support/CrossOver/Bottles/Steam/drive_c/Program Files (x86)/Steam/steamapps/common/Age2HD/SaveGame/multi"
AOE2DE_REPLAY_DIR = os.path.expanduser("~/Documents/My Games/Age of Empires 2 DE/SaveGame")

# ✅ Load previously processed replays
def load_processed_replays():
    global processed_replays
    try:
        with open(PROCESSED_REPLAYS_FILE, "r") as f:
            processed_replays = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        processed_replays = {}

# ✅ Save processed replays
def save_processed_replays():
    with open(PROCESSED_REPLAYS_FILE, "w") as f:
        json.dump(processed_replays, f, indent=4)

def format_duration(seconds):
    """Convert game duration from raw value to 'Xh Ym Zs' format."""
    try:
        seconds = int(float(seconds))
        if seconds > 86400:  # If more than 24 hours, it's likely in milliseconds
            seconds = seconds // 1000

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours}h {minutes}m {seconds}s"
    except Exception as e:
        logging.error(f"❌ Error formatting duration: {e}")
        return "Unknown"

# ✅ Parse AoE2 replay files
def parse_replay(file_path):
    try:
        logging.info(f"✅ Detected New Replay: {file_path}")
        logging.info(f"📂 Attempting to parse replay: {file_path}")
        processed_replays[file_path] = {"status": "processed"}
        save_processed_replays()
    except Exception as e:
        logging.error(f"❌ Error parsing {file_path}: {e}")

# ✅ Stream replay updates (for live parsing)
def stream_replay_updates(replay_file):
    last_size = 0
    while True:
        try:
            current_size = os.path.getsize(replay_file)
            if current_size > last_size:
                logging.info(f"🔄 Processing replay update: {replay_file}")
                parse_replay(replay_file)
            last_size = current_size
        except Exception as e:
            logging.error(f"❌ Error streaming {replay_file}: {e}")
        time.sleep(3)  # Adjust polling interval as needed

# ✅ Watchdog Event Handler for AoE2HD & AoE2DE files
class ReplayEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and (event.src_path.endswith(".aoe2record") or event.src_path.endswith(".aoe2mpgame")):
            if "Out of Sync Save" in event.src_path:
                logging.warning(f"⚠️ Ignoring out-of-sync replay: {event.src_path}")
                return  # Skip processing

            logging.info(f"🆕 New replay detected: {event.src_path}")
            threading.Thread(target=stream_replay_updates, args=(event.src_path,), daemon=True).start()


    def on_modified(self, event):
        if not event.is_directory and (event.src_path.endswith(".aoe2record") or event.src_path.endswith(".aoe2mpgame")):
            logging.info(f"✍️ Replay Modified: {event.src_path}")
            threading.Thread(target=stream_replay_updates, args=(event.src_path,), daemon=True).start()

def get_possible_directories():
    """Auto-detect likely AoE2 replay directories based on OS."""
    dirs = []
    system = platform.system()
    home = os.path.expanduser("~")

    if system == "Windows":
        userprofile = os.environ.get("USERPROFILE", "")
        dirs += [
            os.path.join(userprofile, "Documents", "My Games", "Age of Empires 2 HD", "SaveGame"),
            os.path.join(userprofile, "Documents", "My Games", "Age of Empires 2 DE", "SaveGame"),
            r"C:\GOG Games\Age of Empires II HD\SaveGame",
            r"C:\Age of Empires 2 HD\SaveGame",
            r"D:\Games\Age of Empires II HD\SaveGame"
        ]
    elif system == "Darwin":  # macOS
        dirs.append(AOE2HD_REPLAY_DIR)
        dirs.append(AOE2DE_REPLAY_DIR)
    elif system == "Linux":
        dirs += [
            os.path.join(home, ".wine", "drive_c", "Program Files (x86)", "Microsoft Games",
                         "Age of Empires II HD", "SaveGame"),
            os.path.join(home, ".wine", "drive_c", "Program Files", "Age of Empires II HD", "SaveGame"),
            os.path.join(home, "Documents", "My Games", "Age of Empires 2 HD", "SaveGame"),
            os.path.join(home, "Documents", "My Games", "Age of Empires 2 DE", "SaveGame")
        ]
    return [d for d in dirs if os.path.isdir(d)]

# ✅ Determine directories to watch
if config_dirs:
    possible_dirs = config_dirs
else:
    possible_dirs = get_possible_directories()

def watch_replay_directories(directories, use_polling=True, interval=1):
    """Watches AoE2 HD & DE replay directories for new game files."""
    load_processed_replays()
    observer = PollingObserver() if use_polling else Observer()

    for directory in directories:
        if os.path.exists(directory):
            logging.info(f"👀 Watching directory: {directory}")
            observer.schedule(ReplayEventHandler(), directory, recursive=False)
        else:
            logging.warning(f"⚠️ Directory not found: {directory}")

    observer.start()
    try:
        while True:
            time.sleep(interval)
    except KeyboardInterrupt:
        logging.info("🛑 Stopping watcher.")
        observer.stop()
    observer.join()

# ✅ Run the watcher
if __name__ == '__main__':
    logging.info("📌 Watching AoE2 HD & DE Replay Directories...")
    watch_replay_directories(possible_dirs, use_polling=True, interval=polling_interval)
