from datetime import datetime, timezone

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from config import ALLOW_UNLIMITED_PLAYS, GAME_DURATION_SECONDS, SECRET_KEY
from game import calculate_score, get_daily_words, get_word_number
from matcher import check_guess
from storage import save_result

app = Flask(__name__)
app.secret_key = SECRET_KEY


def get_current_words():
    return get_daily_words(session.get("word_offset", 0))


@app.route("/")
def index():
    words_data = get_current_words()
    word_ids = [w["id"] for w in words_data]
    already_played = (
        not ALLOW_UNLIMITED_PLAYS
        and session.get("session_word_ids") == word_ids
        and session.get("game_finished")
    )
    return render_template(
        "index.html",
        words_data=words_data,
        already_played=already_played,
        puzzle_number=get_word_number(),
        word_offset=session.get("word_offset", 0),
    )


@app.route("/play")
def play():
    words_data = get_current_words()
    word_ids = [w["id"] for w in words_data]

    # Already finished today - redirect to results (unless unlimited plays is on)
    if (
        not ALLOW_UNLIMITED_PLAYS
        and session.get("session_word_ids") == word_ids
        and session.get("game_finished")
    ):
        return redirect(url_for("results"))

    # Switch active word if requested via query param
    switch_to = request.args.get("word")
    if switch_to is not None:
        try:
            idx = int(switch_to)
            if 0 <= idx < len(words_data):
                session["active_word_index"] = idx
        except ValueError:
            pass

    # Initialize new game session
    new_game = session.get("session_word_ids") != word_ids
    replay = ALLOW_UNLIMITED_PLAYS and session.get("game_finished")
    if new_game or replay:
        session["session_word_ids"] = word_ids
        session["game_start"] = datetime.now(timezone.utc).timestamp()
        session["game_finished"] = False
        session["active_word_index"] = 0
        session["words_state"] = [
            {"word_id": w["id"], "matched_ids": [], "guesses": []}
            for w in words_data
        ]

    end_time = session["game_start"] + GAME_DURATION_SECONDS
    remaining = max(0, end_time - datetime.now(timezone.utc).timestamp())

    if remaining <= 0:
        session["game_finished"] = True
        return redirect(url_for("results"))

    active_idx = session.get("active_word_index", 0)
    words_state = session.get("words_state", [])

    words_display = []
    for i, w in enumerate(words_data):
        state = words_state[i] if i < len(words_state) else {"matched_ids": [], "guesses": []}
        matched_ids = set(state.get("matched_ids", []))
        matched_defs = [d for d in w["definitions"] if d["id"] in matched_ids]
        words_display.append({
            "word": w["word"],
            "definitions": w["definitions"],
            "matched_definitions": matched_defs,
            "matched_count": len(matched_defs),
            "total_definitions": len(w["definitions"]),
            "guesses": state.get("guesses", []),
            "is_active": i == active_idx,
        })

    return render_template(
        "play.html",
        words_display=words_display,
        active_word=words_display[active_idx],
        active_idx=active_idx,
        end_timestamp=end_time,
        puzzle_number=get_word_number(),
        word_offset=session.get("word_offset", 0),
    )


@app.route("/guess", methods=["POST"])
def guess():
    words_data = get_current_words()
    word_ids = [w["id"] for w in words_data]

    if session.get("game_finished") or session.get("session_word_ids") != word_ids:
        return jsonify({"error": "No active game"}), 400

    end_time = session["game_start"] + GAME_DURATION_SECONDS
    if datetime.now(timezone.utc).timestamp() > end_time:
        session["game_finished"] = True
        return jsonify({"error": "Time is up", "redirect": url_for("results")})

    guess_text = request.json.get("guess", "").strip()
    if not guess_text:
        return jsonify({"error": "Empty guess"}), 400
    if len(guess_text) > 200:
        return jsonify({"error": "Guess too long"}), 400

    active_idx = session.get("active_word_index", 0)
    words_state = session.get("words_state", [])
    active_state = dict(words_state[active_idx])
    active_word = words_data[active_idx]

    matched_ids = set(active_state.get("matched_ids", []))
    unmatched = [d for d in active_word["definitions"] if d["id"] not in matched_ids]

    if not unmatched:
        return jsonify({
            "matched": False,
            "word_complete": True,
            "matched_count": len(matched_ids),
            "total_definitions": len(active_word["definitions"]),
        })

    result = check_guess(guess_text, active_word["word"], unmatched)

    guess_record = {"text": guess_text, "matched": result["matched"]}
    matched_definition = None
    matched_definition_tier = None

    if result["matched"]:
        matched_def_id = result["matched_definition_id"]
        active_state["matched_ids"] = active_state.get("matched_ids", []) + [matched_def_id]
        matched_def = next(
            (d for d in active_word["definitions"] if d["id"] == matched_def_id), None
        )
        if matched_def:
            matched_definition = matched_def["definition"]
            matched_definition_tier = matched_def.get("tier", "")
            guess_record["matched_definition_id"] = matched_def_id

    active_state["guesses"] = active_state.get("guesses", []) + [guess_record]
    words_state[active_idx] = active_state
    session["words_state"] = words_state

    new_matched_count = len(active_state["matched_ids"])
    word_complete = new_matched_count == len(active_word["definitions"])

    all_complete = all(
        len(s.get("matched_ids", [])) == len(words_data[i]["definitions"])
        for i, s in enumerate(words_state)
    )
    if all_complete:
        session["game_finished"] = True

    return jsonify({
        "matched": result["matched"],
        "matched_definition": matched_definition,
        "matched_definition_tier": matched_definition_tier,
        "matched_count": new_matched_count,
        "total_definitions": len(active_word["definitions"]),
        "word_complete": word_complete,
        "all_found": all_complete,
        "redirect": url_for("results") if all_complete else None,
    })


@app.route("/time-up", methods=["POST"])
def time_up():
    session["game_finished"] = True
    return jsonify({"redirect": url_for("results")})


@app.route("/results")
def results():
    words_data = get_current_words()
    word_ids = [w["id"] for w in words_data]

    if session.get("session_word_ids") != word_ids:
        return redirect(url_for("index"))

    session["game_finished"] = True

    words_state = session.get("words_state", [])
    words_results = []
    total_matched = 0
    total_defs = 0
    all_guesses = []

    for i, w in enumerate(words_data):
        state = words_state[i] if i < len(words_state) else {"matched_ids": [], "guesses": []}
        matched_ids = set(state.get("matched_ids", []))
        matched_defs = [d for d in w["definitions"] if d["id"] in matched_ids]
        missed_defs = [d for d in w["definitions"] if d["id"] not in matched_ids]
        score = calculate_score(len(matched_defs), len(w["definitions"]))
        guesses = state.get("guesses", [])
        all_guesses.extend(guesses)
        total_matched += len(matched_defs)
        total_defs += len(w["definitions"])
        words_results.append({
            "word": w["word"],
            "matched_definitions": matched_defs,
            "missed_definitions": missed_defs,
            "score": score,
            "matched_count": len(matched_defs),
            "total_count": len(w["definitions"]),
            "guesses": guesses,
        })

    overall_score = calculate_score(total_matched, total_defs)

    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
    ip = ip.split(",")[0].strip()
    save_result(ip, str(word_ids), all_guesses, [], overall_score)

    return render_template(
        "results.html",
        words_results=words_results,
        overall_score=overall_score,
        total_matched=total_matched,
        total_defs=total_defs,
        guess_count=len(all_guesses),
        puzzle_number=get_word_number(),
        word_offset=session.get("word_offset", 0),
    )


@app.route("/next-word", methods=["POST"])
def next_word():
    session["word_offset"] = session.get("word_offset", 0) + 1
    session["session_word_ids"] = None
    session["words_state"] = []
    session["game_start"] = None
    session["game_finished"] = False
    session["active_word_index"] = 0
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, port=5001)
