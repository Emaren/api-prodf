def detect_resign(events):
    for event in events:
        if event.get("type") == "resign":
            return event.get("player_id")
    return None
