import os
import platform
import time
import logging
import threading
import hashlib
from watchdog.observers.polling import PollingObserver
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from config import load_config

# Override API endpoint for production
os.environ["API_ENDPOINT"] = "https://aoe2hd-parser-api.onrender.com/api/parse_replay"


# ✅ Import full parsing logic and API submission
from parse_replay import parse_replay as full_parse_replay, send_to_api

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

config = load_config()
REPLAY_DIRS = config.get("replay_directories") or []
USE_POLLING = config.get("use_polling", True)
POLL_INTERVAL = config.get("polling_interval", 1)
PARSE_INTERVAL = config.get("parse_interval", 10)

ACTIVE_REPLAYS = {}
LOCK = threading.Lock()


def sha1_of_file(path):
    try:
        with open(path, 'rb') as f:
            return hashlib.sha1(f.read()).hexdigest()
    except Exception:
        return None


def parse_replay(file_path, iteration, is_final=False):
    try:
        parsed_data = full_parse_replay(file_path, parse_iteration=iteration, is_final=is_final)
        if parsed_data:
            send_to_api(parsed_data)
    except Exception as e:
        logging.error(f"❌ Parse failed: {e}")


def wait_for_stability(file_path, stable_delay=5, poll_interval=2):
    last_size = -1
    stable_time = 0

    while True:
        try:
            size = os.path.getsize(file_path)
        except FileNotFoundError:
            logging.warning(f"🛑 File disappeared: {file_path}")
            return False

        if size == last_size:
            stable_time += poll_interval
        else:
            stable_time = 0
            last_size = size

        if stable_time >= stable_delay:
            logging.info(f"🔒 File stable: {file_path}")
            return True

        time.sleep(poll_interval)


def watch_live_replay(file_path):
    if not wait_for_stability(file_path):
        return

    last_hash = None
    iteration = 0
    stable_iterations = 0
    max_stable_iterations = 3

    while True:
        if not os.path.exists(file_path):
            logging.info(f"🛑 File removed: {file_path}")
            return

        h = sha1_of_file(file_path)
        if h and h != last_hash:
            last_hash = h
            iteration += 1
            stable_iterations = 0
            parse_replay(file_path, iteration, is_final=False)
        else:
            stable_iterations += 1

        if stable_iterations >= max_stable_iterations:
            logging.info(f"✅ Final parse triggered for: {file_path}")
            parse_replay(file_path, iteration + 1, is_final=True)
            break

        time.sleep(PARSE_INTERVAL)


class ReplayEventHandler(FileSystemEventHandler):
    def handle_event(self, path):
        if not path.endswith((".aoe2record", ".aoe2mpgame", ".mgz")) or "Out of Sync" in path:
            return

        with LOCK:
            if path not in ACTIVE_REPLAYS:
                logging.info(f"🆕 Detected replay: {path}")
                t = threading.Thread(target=watch_live_replay, args=(path,), daemon=True)
                ACTIVE_REPLAYS[path] = t
                t.start()

    def on_created(self, event):
        if not event.is_directory:
            self.handle_event(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.handle_event(event.src_path)


def get_default_replay_dirs():
    system = platform.system()
    home = os.path.expanduser("~")
    dirs = ["/replays"]

    if system == "Windows":
        userprofile = os.environ.get("USERPROFILE", "")
        dirs += [
            os.path.join(userprofile, "Documents", "My Games", "Age of Empires 2 HD", "SaveGame"),
            os.path.join(userprofile, "Documents", "My Games", "Age of Empires 2 DE", "SaveGame"),
        ]
    elif system == "Darwin":
        dirs += [
            "/Users/tonyblum/Library/Application Support/CrossOver/Bottles/Steam/drive_c/Program Files (x86)/Steam/steamapps/common/Age2HD/SaveGame",
            "/Users/tonyblum/Documents/My Games/Age of Empires 2 DE/SaveGame",
        ]
    else:
        dirs += [
            os.path.join(home, ".wine/drive_c/Program Files (x86)/Microsoft Games/Age of Empires II HD/SaveGame"),
            os.path.join(home, "Documents/My Games/Age of Empires 2 HD/SaveGame"),
        ]

    return [d for d in dirs if os.path.isdir(d)]


if __name__ == '__main__':
    directories = REPLAY_DIRS or get_default_replay_dirs()
    observer = PollingObserver() if USE_POLLING else Observer()

    for directory in directories:
        if os.path.exists(directory):
            logging.info(f"👀 Watching directory: {directory}")
            observer.schedule(ReplayEventHandler(), directory, recursive=False)
        else:
            logging.warning(f"⚠️ Missing directory: {directory}")

    observer.start()
    try:
        while True:
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        logging.info("🛑 Stopping watcher...")
        observer.stop()

    observer.join()
