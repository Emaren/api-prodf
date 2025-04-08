import os
from parser_hd import parse_hd_replay

replay_dir = os.path.expanduser("~/Library/Application Support/CrossOver/Bottles/Steam/drive_c/Program Files (x86)/Steam/steamapps/common/Age2HD/SaveGame/")
files = [f for f in os.listdir(replay_dir) if f.endswith('.mgz')]

if not files:
    print("No .mgz files found.")
else:
    replay_path = os.path.join(replay_dir, files[0])
    stats = parse_hd_replay(replay_path)
    print(stats)
