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
from parse_replay import parse_replay as full_parse_replay, send_to_api

# Load config
config = load_config()
REPLAY_DIRS = config.get("replay_directories") or []
USE_POLLING = config.get("use_polling", True)
POLL_INTERVAL = config.get("polling_interval", 1)
PARSE_INTERVAL = config.get("parse_interval", 15)  # 🔄 Increased from 10 to 15
LOGGING_LEVEL = os.environ.get("LOGGING_LEVEL", config.get("logging_level", "DEBUG")).upper()

# Logging
logging.basicConfig(
    level=getattr(logging, LOGGING_LEVEL, logging.DEBUG),
    format="%(asctime)s [%(levelname)s] %(message)s"
)

ACTIVE_REPLAYS = {}
LOCK = threading.Lock()

def sha1_of_file(path):
    try:
        with open(path, 'rb') as f:
            sha1 = hashlib.sha1(f.read()).hexdigest()
            logging.debug(f"🔐 SHA1 of {path}: {sha1}")
            return sha1
    except Exception as e:
        logging.error(f"❌ Failed to compute SHA1 of file: {path} | Error: {e}")
        return None

def parse_replay(file_path, iteration, is_final=False):
    logging.debug(f"🧪 Parsing replay (iteration={iteration}, final={is_final}): {file_path}")
    try:
        parsed_data = full_parse_replay(file_path, parse_iteration=iteration, is_final=is_final)
        if parsed_data:
            logging.debug(f"📦 Parsed data keys: {list(parsed_data.keys())}")
            send_to_api(parsed_data)
        else:
            logging.warning(f"⚠️ Empty parse result for: {file_path}")
    except Exception as e:
        logging.error(f"❌ Parse failed: {e}", exc_info=True)

def wait_for_stability(file_path, stable_delay=15, poll_interval=3):  # ⏳ Increased delay and slower polling
    last_size = -1
    stable_time = 0
    logging.debug(f"🔍 Waiting for file to stabilize: {file_path}")
    while True:
        try:
            size = os.path.getsize(file_path)
        except FileNotFoundError:
            logging.warning(f"🛑 File disappeared: {file_path}")
            return False

        if size == last_size:
            stable_time += poll_interval
            logging.debug(f"⏱️ Stable for {stable_time}/{stable_delay} seconds")
        else:
            stable_time = 0
            last_size = size
            logging.debug(f"📏 File size changed to: {size}")

        if stable_time >= stable_delay:
            logging.info(f"🔒 File considered stable: {file_path}")
            return True

        time.sleep(poll_interval)

def watch_live_replay(file_path):
    logging.info(f"🎬 Started live watch: {file_path}")
    if not wait_for_stability(file_path):
        logging.warning(f"⚠️ File never stabilized: {file_path}")
        return

    last_hash = None
    iteration = 0
    stable_iterations = 0
    max_stable_iterations = 6  # ⏲️ Increased from 3 to 6
    min_seconds_between_parses = 120  # 🧘 Increased from 60s to 120s

    last_parse_time = 0

    while True:
        if not os.path.exists(file_path):
            logging.info(f"🗑️ File removed during watch: {file_path}")
            return

        now = time.time()
        h = sha1_of_file(file_path)

        if h and h != last_hash and (now - last_parse_time >= min_seconds_between_parses):
            logging.debug(f"🌀 New file hash detected: {h}")
            last_hash = h
            last_parse_time = now
            iteration += 1
            stable_iterations = 0
            logging.debug(f"🚀 Triggering intermediate parse #{iteration} for {file_path}")
            parse_replay(file_path, iteration, is_final=False)
        else:
            stable_iterations += 1
            logging.debug(f"⏸ No new hash or throttle active. Stable iterations: {stable_iterations}/{max_stable_iterations}")

        if stable_iterations >= max_stable_iterations:
            logging.info(f"🏁 Final parse triggered for: {file_path}")
            parse_replay(file_path, iteration + 1, is_final=True)
            break

        time.sleep(PARSE_INTERVAL)

class ReplayEventHandler(FileSystemEventHandler):
    def handle_event(self, path):
        if not path.endswith((".aoe2record", ".aoe2mpgame", ".mgz")) or "Out of Sync" in path:
            logging.debug(f"🚫 Ignored file: {path}")
            return

        with LOCK:
            if path not in ACTIVE_REPLAYS:
                logging.info(f"🆕 New replay detected: {path}")
                t = threading.Thread(target=watch_live_replay, args=(path,), daemon=True)
                ACTIVE_REPLAYS[path] = t
                t.start()
            else:
                logging.debug(f"🔁 Already watching: {path}")

    def on_created(self, event):
        if not event.is_directory:
            logging.debug(f"📁 File created: {event.src_path}")
            self.handle_event(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            logging.debug(f"✏️ File modified: {event.src_path}")
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
            logging.warning(f"⚠️ Replay directory missing: {directory}")

    observer.start()
    try:
        while True:
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        logging.info("🛑 Watcher shutdown requested")
        observer.stop()

    observer.join()
