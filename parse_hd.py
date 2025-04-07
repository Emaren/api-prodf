import os
import sys
import logging
import json
from datetime import timedelta

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

def parse_hd_replay(filepath):
    logging.info("🎮 Parsing AoE2 HD replay: %s", filepath)
    
    # Dummy parser – AoE2HD support must be reverse-engineered
    # Here we fake some basic fields for MVP compatibility
    filename = os.path.basename(filepath)
    fake_duration = 600  # placeholder, 10 minutes
    fake_players = [
        {
            "name": "Unknown",
            "civilization": None,
            "winner": False,
            "team": "Unknown",
            "score": None,
            "apm": 0,
            "military_score": 0,
            "economy_score": 0,
            "technology_score": 0,
            "society_score": 0,
            "units_killed": 0,
            "buildings_destroyed": 0,
            "resources_gathered": 0,
            "fastest_castle_age": 0,
            "fastest_imperial_age": 0,
            "relics_collected": 0
        }
    ]

    parsed_data = {
        "replay_file": filepath,
        "game_version": "Version.HD",
        "duration": fake_duration,
        "game_duration": str(timedelta(seconds=fake_duration)),
        "map_name": "Unknown",
        "map_size": "Unknown",
        "game_type": "HD Replay",
        "players": fake_players,
        "winner": "Unknown",
        "unique_event_types": [],
        "key_events": []
    }

    # Output JSON next to the replay file
    outpath = filepath + ".json"
    with open(outpath, "w") as f:
        json.dump(parsed_data, f, indent=2)

    logging.info("✅ Dumped parsed HD replay to %s", outpath)
    return parsed_data

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python parse_hd.py <path_to_aoe2record>")
        sys.exit(1)

    replay_path = sys.argv[1]
    if not os.path.exists(replay_path):
        logging.error("File not found: %s", replay_path)
        sys.exit(1)

    parsed = parse_hd_replay(replay_path)

    # Optional: POST to API
    # import requests
    # response = requests.post("http://localhost:8000/api/replays", json=parsed)
    # logging.info("📤 API Response: %s - %s", response.status_code, response.text)
