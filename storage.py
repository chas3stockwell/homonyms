import json
import os
from datetime import date

STORAGE_FILE = "data/game_results.json"


def _load():
    if not os.path.exists(STORAGE_FILE):
        return {}
    with open(STORAGE_FILE) as f:
        return json.load(f)


def _save(data):
    os.makedirs("data", exist_ok=True)
    with open(STORAGE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _key(ip, word_id):
    return f"{ip}_{date.today().isoformat()}_{word_id}"


def save_result(ip, word_id, guesses, matched_ids, score):
    data = _load()
    data[_key(ip, word_id)] = {
        "ip": ip,
        "date": date.today().isoformat(),
        "word_id": word_id,
        "guesses": guesses,
        "matched_ids": matched_ids,
        "score": score,
    }
    _save(data)


def get_result(ip, word_id):
    return _load().get(_key(ip, word_id))
