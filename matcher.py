import textdistance

def check_guess(guess, word, unmatched_definitions):
    """
    Check if a user's guess matches any unmatched definition using keyword matching.
    Keywords are comma-separated strings stored on each definition.
    """
    guess_lower = guess.lower()
    JARO_SIMILARITY_SCORE = 0.8

    for definition in unmatched_definitions:
        keywords = [k.strip().lower() for k in definition.get("keywords", "").split(",")]
        for keyword in keywords:
            if keyword and textdistance.jaro_winkler(guess_lower, keyword) > JARO_SIMILARITY_SCORE:
                return {"matched": True, "matched_definition_id": definition["id"]}


