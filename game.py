import json
import hashlib
from datetime import date

DAILY_WORD_COUNT = 3

_words_cache = None


def load_words():
    global _words_cache
    if _words_cache is None:
        with open("words.json", "r") as f:
            data = json.load(f)
        _words_cache = data["words"]
    return _words_cache


def get_daily_words(offset=0):
    """Return today's set of DAILY_WORD_COUNT words deterministically."""
    words = load_words()
    today = date.today().isoformat()
    hash_val = int(hashlib.sha256(today.encode()).hexdigest(), 16)
    base_index = hash_val % len(words)
    start = (base_index + offset * DAILY_WORD_COUNT) % len(words)
    return [words[(start + i) % len(words)] for i in range(DAILY_WORD_COUNT)]


def get_word_number():
    """Get a display number for today's puzzle (days since launch)."""
    launch = date(2026, 2, 20)
    return (date.today() - launch).days + 1


def calculate_score(matched_count, total_count):
    if total_count == 0:
        return 0
    return round((matched_count / total_count) * 100)
