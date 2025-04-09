import os
import io
import json
import logging
import hashlib
from mgz import header
from mgz import summary  

from utils.extract_datetime import extract_datetime_from_filename

def parse_replay_full(replay_path):
    if not os.path.exists(replay_path):
        logging.error(f"❌ Replay not found: {replay_path}")
        return None

    try:
        with open(replay_path, "rb") as f:
            file_bytes = f.read()

        h = header.parse(file_bytes)
        s = summary.Summary(io.BytesIO(file_bytes))

        stats = {
            "game_version": str(h.version),
            "map": {
                "name": s.get_map().get("name", "Unknown"),
                "size": s.get_map().get("size", "Unknown"),
            },
            "game_type": str(s.get_version()),
            "duration": int(s.get_duration() // 1000 if s.get_duration() > 48 * 3600 else s.get_duration()),
        }

        players = []
        winner = None
        for p in s.get_players():
            p_data = {
                "name": p.get("name", "Unknown"),
                "civilization": p.get("civilization", "Unknown"),
                "winner": p.get("winner", False),
                "score": p.get("score", 0),
            }
            players.append(p_data)
            if p_data["winner"]:
                winner = p_data["name"]

        stats["players"] = players
        stats["winner"] = winner or "Unknown"
        dt = extract_datetime_from_filename(os.path.basename(replay_path))
        stats["played_on"] = dt.isoformat() if dt else None

        logging.info(f"✅ parse_replay_full => {replay_path}")
        return stats

    except Exception as e:
        logging.error(f"❌ parse error: {e}")
        return None

def hash_replay_file(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

