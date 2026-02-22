import json
import re

import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def check_guess(guess, word, unmatched_definitions):
    """
    Send a user's guess to Claude and determine which definition (if any) it matches.

    Returns:
        {"matched": True/False, "matched_definition_id": "..." or None}
    """
    defs_text = "\n".join(
        f'- ID: "{d["id"]}" | Definition: "{d["definition"]}"'
        for d in unmatched_definitions
    )

    prompt = f"""You are a judge in a word game about homonyms. The word is "{word}".

The player submitted this guess: "{guess}"

Here are the remaining unmatched definitions for this word:
{defs_text}

Does the player's guess match ANY ONE of these definitions? The guess does not need to be
word-for-word. It should demonstrate that the player understands that particular meaning of
the word. Be generous but not absurd -- the player should clearly be referring to the
specific meaning described in the definition.

Respond in JSON only, no markdown fences:
{{"matched": true, "matched_definition_id": "the_id"}}
or
{{"matched": false, "matched_definition_id": null}}"""

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=150,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            return {"matched": False, "matched_definition_id": None}

    # Validate the matched ID actually exists
    if result.get("matched"):
        valid_ids = {d["id"] for d in unmatched_definitions}
        if result.get("matched_definition_id") not in valid_ids:
            return {"matched": False, "matched_definition_id": None}

    return result
