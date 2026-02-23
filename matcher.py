def check_guess(guess, word, unmatched_definitions):
    """
    Check if a user's guess matches any unmatched definition using keyword matching.
    Keywords are comma-separated strings stored on each definition.
    """
    guess_lower = guess.lower()

    for definition in unmatched_definitions:
        keywords = [k.strip().lower() for k in definition.get("keywords", "").split(",")]
        for keyword in keywords:
            if keyword and keyword in guess_lower:
                return {"matched": True, "matched_definition_id": definition["id"]}

    return {"matched": False, "matched_definition_id": None}
