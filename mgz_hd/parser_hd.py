import logging
from header.hd import Header
from resign import detect_resign


def parse_hd_replay(file_path):
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        header = Header.parse(data)

        return {
            "players": header.get_players(),
            "civs": header.get_civilizations(),
            "duration": header.get_duration(),
            "version": header.get_version(),
            "map": header.get_map(),
            "winner": detect_resign(header.get_events()),
        }

    except Exception as e:
        logging.error(f"Failed to parse HD replay: {file_path} — {e}")
        return None
