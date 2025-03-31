###############################################################################
# parse_replay.py
###############################################################################
import os
import io
import json
import logging
import re
from datetime import datetime
import requests

from mgz import header, summary
from mgz.fast.actions import parse_action_71094

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

FLASK_API_URL = "http://192.168.250.28:8002/api/parse_replay"


def format_duration(seconds: int) -> str:
    minutes = seconds // 60
    hours = minutes // 60
    minutes %= 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    return f"{minutes}m {secs}s"


def extract_datetime_from_filename(filename: str):
    match = re.search(r"@(\d{4})\.(\d{2})\.(\d{2}) (\d{6})", filename)
    if match:
        date_str = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
        time_str = match.group(4)
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H%M%S")
    return None


def infer_resign_winner(file_bytes, players):
    if len(players) != 2:
        logging.warning("⚠️ Skipping resign logic: not a 2-player match.")
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
            except Exception as e:
                logging.warning(f"⚠️ Action parsing failed: {e}")
                break

    logging.info(f"🔎 Total resigns detected: {len(resigns)}")

    if len(resigns) == 1:
        loser_pid = resigns[0].player_id
        loser_index = loser_pid - 1
        if loser_index in (0, 1):
            return 1 - loser_index
        else:
            logging.warning(f"⚠️ Unexpected player_id in resign: {loser_pid}")
    return None


def parse_replay(replay_path: str) -> dict:
    if not os.path.exists(replay_path):
        logging.error(f"❌ Replay not found: {replay_path}")
        return {}

    try:
        with open(replay_path, "rb") as f:
            file_bytes = f.read()
    except Exception as e:
        logging.error(f"❌ Error reading replay: {e}")
        return {}

    stats = {}
    try:
        with io.BytesIO(file_bytes) as buf:
            h = header.parse_stream(buf)
            stats["game_version"] = str(h.version)
            logging.info(f"✅ Game Version: {stats['game_version']}")
    except Exception as exc:
        logging.error(f"❌ parse header error: {exc}")
        return {}

    try:
        with io.BytesIO(file_bytes) as buf:
            s = summary.Summary(buf)
            raw_duration = s.get_duration()
            if raw_duration > 48 * 3600:
                raw_duration //= 1000
            stats["duration"] = raw_duration
            stats["game_duration"] = format_duration(raw_duration)
            stats["map_name"] = s.get_map().get("name", "Unknown")
            stats["map_size"] = s.get_map().get("size", "Unknown")
            stats["game_type"] = str(s.get_version())

            raw_players = s.get_players()
            players = []
            winner = None
            for p in raw_players:
                p_data = {
                    "name": p.get("name", "Unknown").strip(),
                    "civilization": p.get("civilization", "Unknown"),
                    "winner": p.get("winner", False),
                    "score": p.get("score", 0),
                }
                players.append(p_data)
                if p_data["winner"]:
                    winner = p_data["name"]

            # Try inferring winner from resign if not marked
            if not winner and len(players) == 2:
                r_index = infer_resign_winner(file_bytes, players)
                if r_index is not None:
                    players[r_index]["winner"] = True
                    players[1 - r_index]["winner"] = False
                    winner = players[r_index]["name"]
                    logging.info(f"🏆 Winner determined by single Resign: {winner}")

            stats["players"] = players
            stats["winner"] = winner if winner else "Unknown"

    except Exception as exc:
        logging.error(f"❌ parse summary error: {exc}")
        return {}

    base_name = os.path.basename(replay_path)
    dt = extract_datetime_from_filename(base_name)
    stats["played_on"] = dt.isoformat() if dt else None

    debug_path = replay_path + ".json"
    try:
        with open(debug_path, "w") as f:
            json.dump(stats, f, indent=4)
        logging.info(f"🔍 Debug JSON => {debug_path}")
    except Exception as e:
        logging.warning(f"Could not write debug JSON: {e}")

    return stats


def send_to_api(parsed_data: dict):
    if not parsed_data or "replay_file" not in parsed_data:
        logging.error("❌ Missing replay_file in parsed_data.")
        return

    try:
        logging.info(f"📤 Sending to API => {parsed_data['replay_file']}")
        resp = requests.post(FLASK_API_URL, json=parsed_data)
        logging.info(f"Response: {resp.status_code} - {resp.text}")
    except Exception as exc:
        logging.error(f"❌ Could not send to API: {exc}")


if __name__ == "__main__":
    SAVEGAME_DIR = "/Users/tonyblum/Library/Application Support/CrossOver/Bottles/Steam/drive_c/Program Files (x86)/Steam/steamapps/common/Age2HD/SaveGame"

    all_replays = [f for f in os.listdir(SAVEGAME_DIR) if f.endswith(".aoe2record")]

    def dt_key(fname):
        dt_ = extract_datetime_from_filename(fname)
        return dt_ if dt_ else datetime.min

    all_replays.sort(key=dt_key, reverse=True)

    for fname in all_replays:
        path = os.path.join(SAVEGAME_DIR, fname)
        results = parse_replay(path)
        if results:
            results["replay_file"] = os.path.abspath(path)
            send_to_api(results)
