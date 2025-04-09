import os
import io
import json
import logging
import re
import platform
import hashlib
from datetime import datetime
import requests
import sys
import tempfile
import argparse

# Add current directory to sys.path so that imports work correctly.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import mgz_hd.parser_hd
from mgz import header, summary
from mgz_hd.parser_hd import parse_hd_replay as hd_parse_replay
from mgz_hd.fast.actions import parse_action_71094
from config import load_config, get_flask_api_url

print("MGZ Path:", mgz_hd.__file__)
print("Working dir:", os.getcwd())
print("Using mgz_hd from:", mgz_hd.__file__)

# Load configuration
config = load_config()
LOG_LEVEL = os.environ.get("LOGGING_LEVEL", config.get("logging_level", "DEBUG")).upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.DEBUG),
    format="%(asctime)s [%(levelname)s] %(message)s"
)

FLASK_API_URL = get_flask_api_url()

def format_duration(seconds: int) -> str:
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m {secs}s" if hours else f"{minutes}m {secs}s"

def extract_datetime_from_filename(filename: str):
    match = re.search(r"@(\d{4})\.(\d{2})\.(\d{2}) (\d{6})", filename)
    if match:
        year, month, day, time_part = match.groups()
        return datetime.strptime(f"{year}-{month}-{day} {time_part}", "%Y-%m-%d %H%M%S")
    return None

def infer_resign_winner(file_bytes, players):
    if len(players) != 2:
        logging.warning("⚠️ Skipped resign logic: not a 2-player match.")
        return None

    resigns = []
    with io.BytesIO(file_bytes) as f:
        while True:
            try:
                action = parse_action_71094(f)
                if not action:
                    break
                if getattr(action, "operation", "") == "Resign":
                    resigns.append(action)
                    logging.info(f"📌 Resign detected: player_id={action.player_id}")
            except Exception:
                break

    if len(resigns) == 1:
        loser_index = resigns[0].player_id - 1
        if loser_index in [0, 1]:
            logging.info(f"🏁 Resign winner inferred: {players[1 - loser_index]['name']}")
            return 1 - loser_index
    return None

def hash_replay_file(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def parse_de_replay(file_bytes):
    logging.debug("📥 Starting parse_de_replay()")
    stats = {}
    with io.BytesIO(file_bytes) as buf:
        h = header.parse_stream(buf)
        stats["game_version"] = str(h.version)

    with io.BytesIO(file_bytes) as buf:
        s = summary.Summary(buf)
        raw_duration = s.get_duration()
        if raw_duration > 48 * 3600:
            raw_duration //= 1000

        stats.update({
            "duration": raw_duration,
            "game_duration": format_duration(raw_duration),
            "map_name": s.get_map().get("name", "Unknown"),
            "map_size": s.get_map().get("size", "Unknown"),
            "game_type": str(s.get_version()),
        })

        raw_players = s.get_players()
        players = []
        winner = None
        for p in raw_players:
            player = {
                "name": p.get("name", "Unknown").strip(),
                "civilization": p.get("civilization", "Unknown"),
                "winner": p.get("winner", False),
                "score": p.get("score", 0),
            }
            players.append(player)
            if player["winner"]:
                winner = player["name"]

        if not winner and len(players) == 2:
            resign_winner = infer_resign_winner(file_bytes, players)
            if resign_winner is not None:
                players[resign_winner]["winner"] = True
                players[1 - resign_winner]["winner"] = False
                winner = players[resign_winner]["name"]

        stats["players"] = players
        stats["winner"] = winner or "Unknown"
    return stats

def parse_hd_replay_bytes(file_bytes):
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(file_bytes)
            tmp_file.flush()
            tmp_path = tmp_file.name
        result = hd_parse_replay(tmp_path)
        if result is None:
            raise ValueError("HD parser returned None.")
        return result
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

def parse_replay(replay_path: str, parse_iteration=0, is_final=False) -> dict:
    logging.debug(f"🛠 Starting parse (iteration={parse_iteration}, final={is_final}) for: {replay_path}")
    if not os.path.exists(replay_path):
        logging.error(f"❌ Replay not found: {replay_path}")
        return {}

    try:
        with open(replay_path, "rb") as f:
            file_bytes = f.read()
    except Exception as e:
        logging.error(f"❌ Error reading replay: {e}")
        return {}

    basename = os.path.basename(replay_path)
    try:
        if "v5.8" in basename:
            stats = parse_hd_replay_bytes(file_bytes)
        else:
            stats = parse_de_replay(file_bytes)
    except Exception as hd_error:
        logging.error(f"❌ HD parser failed: {hd_error}. Falling back to DE parser.")
        try:
            stats = parse_de_replay(file_bytes)
        except Exception as de_error:
            logging.error(f"❌ DE parser also failed: {de_error}.")
            return {}

    dt = extract_datetime_from_filename(basename)
    stats["played_on"] = dt.isoformat() if dt else None
    stats["replay_file"] = replay_path
    stats["parse_iteration"] = parse_iteration
    stats["is_final"] = is_final
    stats["replay_hash"] = hash_replay_file(replay_path)

    try:
        with open(replay_path + ".json", "w") as f:
            json.dump(stats, f, indent=4)
    except Exception as e:
        logging.warning(f"❌ Debug JSON write failed: {e}")

    return stats

def send_to_api(parsed_data: dict, force: bool = False):
    targets = config.get("api_targets", ["local"])
    endpoints = {
        "local": "http://localhost:8002/api/parse_replay",
        "render": "https://aoe2hd-parser-api.onrender.com/api/parse_replay"
    }

    for target in targets:
        base_url = endpoints.get(target)
        if not base_url:
            logging.warning(f"⚠️ Unknown API target: {target}")
            continue

        api_url = base_url + ("?force=true" if force else "")
        try:
            logging.info(f"📤 Sending to [{target}] => {parsed_data['replay_file']}")
            resp = requests.post(api_url, json=parsed_data)
            if resp.ok:
                logging.info(f"✅ [{target}] Response: {resp.status_code} - {resp.text}")
            else:
                logging.error(f"❌ [{target}] Error: {resp.status_code} - {resp.text}")
        except Exception as exc:
            logging.error(f"❌ [{target}] API failed: {exc}")
            logging.debug(f"📦 Payload: {json.dumps(parsed_data, indent=2)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse and upload AoE2HD replay file.")
    parser.add_argument("replay_path", nargs="?", help="Path to the replay file")
    parser.add_argument("--force", action="store_true", help="Force reparse even if marked as final")
    args = parser.parse_args()

    if args.replay_path:
        if os.path.exists(args.replay_path):
            logging.info(f"📄 Parsing single replay: {args.replay_path}")
            result = parse_replay(args.replay_path, parse_iteration=1, is_final=True)
            if result:
                send_to_api(result, force=args.force)
        else:
            logging.error(f"❌ File not found: {args.replay_path}")
    else:
        # Fall back to scanning all configured replay directories
        SAVEGAME_DIRS = config.get("replay_directories") or []
        for path in SAVEGAME_DIRS:
            logging.info(f"📁 Scanning replay dir: {path}")
            if not os.path.exists(path):
                logging.warning(f"⚠️ Missing: {path}")
                continue

            replays = [f for f in os.listdir(path) if f.endswith(".aoe2record") or f.endswith(".mgz")]
            replays.sort(key=lambda fname: extract_datetime_from_filename(fname) or datetime.min, reverse=True)

            for fname in replays:
                replay_path = os.path.join(path, fname)
                parsed_result = parse_replay(replay_path, parse_iteration=1, is_final=True)
                if parsed_result:
                    send_to_api(parsed_result, force=args.force)
