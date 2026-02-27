import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

_client = None


def get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def check_guess(guess, word, unmatched_definitions):
    definitions_text = "\n".join(
        f"{i + 1}. [ID:{d['id']}] {d['definition']}"
        for i, d in enumerate(unmatched_definitions)
    )

    prompt = f"""You are judging a word game about the word "{word}".

The player's guess: "{guess}"

Unmatched definitions:
{definitions_text}

Does the player's guess correctly describe any of these definitions? Be generous — if they demonstrate understanding of the meaning, count it.

Reply with only the definition ID (e.g. "bolt_1") if it matches, or "none" if it doesn't."""

    response = get_client().messages.create(
        model=CLAUDE_MODEL,
        max_tokens=20,
        messages=[{"role": "user", "content": prompt}],
    )

    usage = response.usage
    input_cost  = usage.input_tokens  * 0.80  / 1_000_000
    output_cost = usage.output_tokens * 4.00  / 1_000_000
    print(f"[API] guess='{guess}' | in={usage.input_tokens} out={usage.output_tokens} | cost=${input_cost + output_cost:.6f}")

    answer = response.content[0].text.strip().lower()

    if answer == "none":
        return {"matched": False, "matched_definition_id": None}

    for d in unmatched_definitions:
        if d["id"].lower() in answer:
            return {"matched": True, "matched_definition_id": d["id"]}

    return {"matched": False, "matched_definition_id": None}
