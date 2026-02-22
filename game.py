import json
import hashlib
from datetime import date

_words_cache = None


def load_words():
    global _words_cache
    if _words_cache is None:
        with open("words.json", "r") as f:
            data = json.load(f)
        _words_cache = data["words"]
    return _words_cache


def get_daily_word(offset=0):
    """Select today's word deterministically. Same word for all players.
    offset > 0 gives bonus words beyond the daily one."""
    words = load_words()
    today = date.today().isoformat()
    hash_val = int(hashlib.sha256(today.encode()).hexdigest(), 16)
    index = (hash_val % len(words) + offset) % len(words)
    return words[index]


def get_word_number():
    """Get a display number for today's puzzle (days since launch)."""
    launch = date(2026, 2, 20)
    return (date.today() - launch).days + 1


def calculate_score(matched_count, total_count):
    if total_count == 0:
        return 0
    return round((matched_count / total_count) * 100)
