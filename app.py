from datetime import datetime

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from config import GAME_DURATION_SECONDS, SECRET_KEY
from game import calculate_score, get_daily_word, get_word_number
from matcher import check_guess

app = Flask(__name__)
app.secret_key = SECRET_KEY


@app.route("/")
def index():
    word_data = get_daily_word()
    definition_count = len(word_data["definitions"])
    already_played = (
        session.get("last_played_word_id") == word_data["id"]
        and session.get("game_finished")
    )
    return render_template(
        "index.html",
        word=word_data["word"],
        definition_count=definition_count,
        already_played=already_played,
        puzzle_number=get_word_number(),
    )


@app.route("/play")
def play():
    word_data = get_daily_word()

    # Already finished today - go to results
    if (
        session.get("last_played_word_id") == word_data["id"]
        and session.get("game_finished")
    ):
        return redirect(url_for("results"))

    # Initialize new game session for today's word
    if session.get("current_word_id") != word_data["id"]:
        session["current_word_id"] = word_data["id"]
        session["matched_ids"] = []
        session["guesses"] = []
        session["game_start"] = datetime.utcnow().timestamp()
        session["game_finished"] = False

    end_time = session["game_start"] + GAME_DURATION_SECONDS
    remaining = max(0, end_time - datetime.utcnow().timestamp())

    if remaining <= 0:
        session["game_finished"] = True
        session["last_played_word_id"] = word_data["id"]
        return redirect(url_for("results"))

    matched_defs = [
        d for d in word_data["definitions"] if d["id"] in session.get("matched_ids", [])
    ]

    return render_template(
        "play.html",
        word=word_data["word"],
        total_definitions=len(word_data["definitions"]),
        matched_definitions=matched_defs,
        matched_count=len(matched_defs),
        end_timestamp=end_time,
        puzzle_number=get_word_number(),
    )


@app.route("/guess", methods=["POST"])
def guess():
    word_data = get_daily_word()

    if session.get("game_finished") or session.get("current_word_id") != word_data["id"]:
        return jsonify({"error": "No active game"}), 400

    end_time = session["game_start"] + GAME_DURATION_SECONDS
    if datetime.utcnow().timestamp() > end_time:
        session["game_finished"] = True
        session["last_played_word_id"] = word_data["id"]
        return jsonify({"error": "Time is up", "redirect": url_for("results")})

    guess_text = request.json.get("guess", "").strip()
    if not guess_text:
        return jsonify({"error": "Empty guess"}), 400
    if len(guess_text) > 200:
        return jsonify({"error": "Guess too long"}), 400

    matched_ids = set(session.get("matched_ids", []))
    unmatched = [d for d in word_data["definitions"] if d["id"] not in matched_ids]

    if not unmatched:
        session["game_finished"] = True
        session["last_played_word_id"] = word_data["id"]
        return jsonify({"all_found": True, "redirect": url_for("results")})

    result = check_guess(guess_text, word_data["word"], unmatched)

    guess_record = {"text": guess_text, "matched": result["matched"]}

    matched_definition = None
    if result["matched"]:
        matched_def_id = result["matched_definition_id"]
        session["matched_ids"] = session.get("matched_ids", []) + [matched_def_id]
        matched_def = next(
            (d for d in word_data["definitions"] if d["id"] == matched_def_id), None
        )
        if matched_def:
            matched_definition = matched_def["definition"]
            guess_record["matched_definition_id"] = matched_def_id

    guesses = session.get("guesses", [])
    guesses.append(guess_record)
    session["guesses"] = guesses

    all_found = len(session["matched_ids"]) == len(word_data["definitions"])
    if all_found:
        session["game_finished"] = True
        session["last_played_word_id"] = word_data["id"]

    return jsonify(
        {
            "matched": result["matched"],
            "matched_definition": matched_definition,
            "matched_count": len(session["matched_ids"]),
            "total_definitions": len(word_data["definitions"]),
            "all_found": all_found,
            "redirect": url_for("results") if all_found else None,
        }
    )


@app.route("/time-up", methods=["POST"])
def time_up():
    word_data = get_daily_word()
    session["game_finished"] = True
    session["last_played_word_id"] = word_data["id"]
    return jsonify({"redirect": url_for("results")})


@app.route("/results")
def results():
    word_data = get_daily_word()

    if session.get("current_word_id") != word_data["id"]:
        return redirect(url_for("index"))

    session["game_finished"] = True
    session["last_played_word_id"] = word_data["id"]

    matched_ids = set(session.get("matched_ids", []))
    all_defs = word_data["definitions"]

    matched_defs = [d for d in all_defs if d["id"] in matched_ids]
    missed_defs = [d for d in all_defs if d["id"] not in matched_ids]

    score = calculate_score(len(matched_defs), len(all_defs))

    return render_template(
        "results.html",
        word=word_data["word"],
        matched_definitions=matched_defs,
        missed_definitions=missed_defs,
        score=score,
        matched_count=len(matched_defs),
        total_count=len(all_defs),
        guesses=session.get("guesses", []),
        puzzle_number=get_word_number(),
    )


if __name__ == "__main__":
    app.run(debug=True, port=5001)
