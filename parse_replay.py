import os
import io
import json
import logging
import re
import platform
import hashlib
from datetime import datetime
import requests

import mgz_hd
from mgz_hd import header, summary
from mgz_hd.fast.actions import parse_action_71094

from config import load_config, get_flask_api_url

print("Using mgz_hd from:", mgz_hd.__file__)

# Load config
config = load_config()
LOG_LEVEL = os.environ.get("LOGGING_LEVEL", config.get("logging_level", "DEBUG")).upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.DEBUG),
                    format="%(asctime)s [%(levelname)s] %(message)s")

FLASK_API_URL = get_flask_api_url()


def format_duration(seconds: int) -> str:
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m {secs}s" if hours else f"{minutes}m {secs}s"


def extract_datetime_from_filename(filename: str):
    match = re.search(r"@(\d{4})\.(\d{2})\.(\d{2}) (\d{6})", filename)
    if match:
        date_part, time_part = match.group(1, 2, 3), match.group(4)
        date_str = "-".join(date_part)
        return datetime.strptime(f"{date_str} {time_part}", "%Y-%m-%d %H%M%S")
    return None


def infer_resign_winner(file_bytes, players):
    if len(players) != 2:
        logging.debug(f"🧠 Running resign inference — Players: {[p['name'] for p in players]}")
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
        logging.info(f"🏁 Resign winner inferred: {players[1 - loser_index]['name']}")
        logging.info(f"🧠 Only one resign action detected. Assuming player_id={loser_pid} resigned.")
        loser_pid = resigns[0].player_id
        loser_index = loser_pid - 1
        if loser_index in [0, 1]:
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
        logging.debug(f"🧩 Header version: {stats['game_version']}")

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

        logging.debug(f"🗺️ Map: {stats['map_name']} | Size: {stats['map_size']} | Duration: {stats['game_duration']}")

        raw_players = s.get_players()
        players, winner = [], None
        for p in raw_players:
            player = {
                "name": p.get("name", "Unknown").strip(),
                "civilization": p.get("civilization", "Unknown"),
                "winner": p.get("winner", False),
                "score": p.get("score", 0),
            }
            players.append(player)
            logging.debug(f"👤 Player: {player['name']} | Civ: {player['civilization']} | Winner: {player['winner']}")

            if player["winner"]:
                winner = player["name"]

        if not winner and len(players) == 2:
            logging.debug("🤔 No explicit winner found. Attempting resign inference.")
            resign_winner = infer_resign_winner(file_bytes, players)
            if resign_winner is not None:
                players[resign_winner]["winner"] = True
                players[1 - resign_winner]["winner"] = False
                winner = players[resign_winner]["name"]

        stats["players"] = players
        stats["winner"] = winner or "Unknown"
        logging.debug(f"🏆 Final winner: {stats['winner']}")

    return stats


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

    try:
        stats = parse_de_replay(file_bytes)
    except RuntimeError as e:
        logging.warning(f"⏳ Likely in-progress or incomplete replay (safe to retry later): {e}")
        return {}
    except Exception as e:
        logging.error(f"❌ Unexpected parse failure: {e}")
        return {}

    dt = extract_datetime_from_filename(os.path.basename(replay_path))
    stats["played_on"] = dt.isoformat() if dt else None
    stats["replay_file"] = replay_path
    stats["parse_iteration"] = parse_iteration
    stats["is_final"] = is_final
    stats["replay_hash"] = hash_replay_file(replay_path)

    logging.debug(f"🧾 Parsed stats keys: {list(stats.keys())}")
    logging.debug(f"🕒 Played on: {stats['played_on']} | Replay hash: {stats['replay_hash']}")

    try:
        with open(replay_path + ".json", "w") as f:
            json.dump(stats, f, indent=4)
        logging.debug(f"💾 Debug JSON written: {replay_path}.json")
    except Exception as e:
        logging.warning(f"❌ Debug JSON write failed: {e}")

    return stats


def send_to_api(parsed_data: dict):
    targets = config.get("api_targets", ["local"])
    endpoints = {
        "local": "http://localhost:8002/api/parse_replay",
        "render": "https://aoe2hd-parser-api.onrender.com/api/parse_replay"
    }

    for target in targets:
        api_url = endpoints.get(target)
        if not api_url:
            logging.warning(f"⚠️ Unknown API target: {target}")
            continue

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
    SAVEGAME_DIRS = config.get("replay_directories") or []
    if not SAVEGAME_DIRS:
        SAVEGAME_DIRS = get_default_replay_dirs()

    for path in SAVEGAME_DIRS:
        logging.info(f"📁 Scanning replay dir: {path}")
        if not os.path.exists(path):
            logging.warning(f"⚠️ Missing: {path}")
            continue

        replays = [f for f in os.listdir(path) if f.endswith(".aoe2record") or f.endswith(".mgz")]

        def dt_key(fname):
            dt = extract_datetime_from_filename(fname)
            return dt or datetime.min

        replays.sort(key=dt_key, reverse=True)

        for fname in replays:
            replay_path = os.path.join(path, fname)
            parsed_result = parse_replay(replay_path, parse_iteration=1, is_final=True)
            if parsed_result:
                send_to_api(parsed_result)
