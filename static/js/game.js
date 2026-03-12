document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("guess-form");
    const input = document.getElementById("guess-input");
    const submitBtn = document.getElementById("submit-btn");
    const timerEl = document.getElementById("timer");
    const progressEl = document.getElementById("progress");
    const matchedList = document.getElementById("matched-list");
    const placeholders = document.getElementById("placeholders");
    const guessList = document.getElementById("guess-list");
    const wordDisplay = document.getElementById("word-display");

    const endTimestamp = parseFloat(document.body.dataset.endTimestamp);
    let gameOver = false;

    // Local mirror of server state so tab switches are instant
    const wordsState = ALL_WORDS.map(function (w) {
        return {
            word: w.word,
            matched_definitions: w.matched_definitions.slice(),
            matched_count: w.matched_count,
            total_definitions: w.total_definitions,
            guesses: w.guesses.slice(),
        };
    });

    // --- Timer ---
    function updateTimer() {
        const now = Date.now() / 1000;
        const remaining = Math.max(0, endTimestamp - now);
        const minutes = Math.floor(remaining / 60);
        const seconds = Math.floor(remaining % 60);
        timerEl.textContent = minutes + ":" + seconds.toString().padStart(2, "0");
        if (remaining <= 30) timerEl.classList.add("timer-warning");
        if (remaining <= 0) { clearInterval(timerInterval); handleTimeUp(); }
    }
    const timerInterval = setInterval(updateTimer, 250);
    updateTimer();

    function handleTimeUp() {
        if (gameOver) return;
        gameOver = true;
        input.disabled = true;
        submitBtn.disabled = true;
        fetch("/time-up", { method: "POST" }).finally(function () { showSurvey(); });
    }

    // --- Tab switching ---
    function renderActiveWord() {
        const w = wordsState[activeIdx];

        // Word tiles
        wordDisplay.innerHTML = w.word.split("").map(function (ch) {
            return '<span class="tile">' + escapeHtml(ch) + "</span>";
        }).join("");

        // Progress
        progressEl.textContent = w.matched_count + "/" + w.total_definitions + " found";

        // Tab highlights + progress badges
        document.querySelectorAll(".word-tab").forEach(function (tab, i) {
            tab.classList.toggle("active", i === activeIdx);
            tab.querySelector(".tab-progress").textContent =
                wordsState[i].matched_count + "/" + wordsState[i].total_definitions;
        });

        // Matched definitions
        matchedList.innerHTML = w.matched_definitions.map(function (d) {
            return '<div class="matched-def">' +
                '<span class="check">&#10003;</span>' +
                '<span class="def-text">' + escapeHtml(d.definition) + "</span>" +
                '<span class="tier-badge tier-' + escapeHtml((d.tier || "").toLowerCase()) + '">' + escapeHtml(d.tier || "") + "</span>" +
                "</div>";
        }).join("");

        // Placeholders
        const remaining = w.total_definitions - w.matched_count;
        placeholders.innerHTML = Array(remaining).fill(
            '<div class="def-placeholder"><span class="qmark">?</span><span class="placeholder-text">Unknown meaning</span></div>'
        ).join("");

        // Guess history (misses only, newest first)
        guessList.innerHTML = w.guesses.slice().reverse().filter(function (g) {
            return !g.matched;
        }).map(function (g) {
            return '<li class="guess-miss"><span class="guess-icon">&#10007;</span> <span class="guess-text">"' + escapeHtml(g.text) + '"</span></li>';
        }).join("");

        input.focus();
    }

    document.querySelectorAll(".word-tab").forEach(function (tab) {
        tab.addEventListener("click", function () {
            const idx = parseInt(tab.dataset.idx, 10);
            if (idx === activeIdx) return;
            activeIdx = idx;
            renderActiveWord();
            // Keep server session in sync (fire and forget)
            fetch("/switch-word", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ idx: idx }),
            });
        });
    });

    // --- Guess submission ---
    form.addEventListener("submit", function (e) {
        e.preventDefault();
        if (gameOver) return;

        const guess = input.value.trim();
        if (!guess) return;

        input.disabled = true;
        submitBtn.disabled = true;
        submitBtn.textContent = "...";

        fetch("/guess", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ guess: guess, word_idx: activeIdx }),
        })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.error === "Time is up" || (data.redirect && data.all_found == null)) {
                    if (data.redirect) window.location.href = data.redirect;
                    return;
                }

                const w = wordsState[activeIdx];

                if (data.matched) {
                    w.matched_count = data.matched_count;
                    w.matched_definitions.push({
                        definition: data.matched_definition,
                        tier: data.matched_definition_tier || "",
                    });
                    w.guesses.push({ text: guess, matched: true });

                    // Add matched def to DOM
                    var div = document.createElement("div");
                    div.className = "matched-def animate-in";
                    div.innerHTML =
                        '<span class="check">&#10003;</span> ' +
                        '<span class="def-text">' + escapeHtml(data.matched_definition) + "</span>" +
                        '<span class="tier-badge tier-' + escapeHtml((data.matched_definition_tier || "").toLowerCase()) + '">' + escapeHtml(data.matched_definition_tier || "") + "</span>";
                    matchedList.appendChild(div);

                    var placeholder = placeholders.querySelector(".def-placeholder");
                    if (placeholder) placeholder.remove();

                    progressEl.textContent = data.matched_count + "/" + data.total_definitions + " found";
                    document.querySelectorAll(".word-tab")[activeIdx].querySelector(".tab-progress").textContent =
                        data.matched_count + "/" + data.total_definitions;

                    input.classList.add("flash-success");
                    setTimeout(function () { input.classList.remove("flash-success"); }, 600);
                } else {
                    w.guesses.push({ text: guess, matched: false });

                    var li = document.createElement("li");
                    li.className = "guess-miss";
                    li.innerHTML = '<span class="guess-icon">&#10007;</span> <span class="guess-text">"' + escapeHtml(guess) + '"</span>';
                    guessList.prepend(li);

                    input.classList.add("flash-fail");
                    setTimeout(function () { input.classList.remove("flash-fail"); }, 600);
                }

                if (data.all_found) {
                    gameOver = true;
                    input.disabled = true;
                    submitBtn.disabled = true;
                    setTimeout(showSurvey, 800);
                }
            })
            .catch(function (err) { console.error("Guess error:", err); })
            .finally(function () {
                input.value = "";
                if (!gameOver) {
                    input.disabled = false;
                    submitBtn.disabled = false;
                    submitBtn.textContent = "Go";
                    input.focus();
                }
            });
    });

    function escapeHtml(str) {
        var div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    // --- Survey ---
    var surveyData = { rejected_guess: "", answer_feeling: "", time_feeling: "", change_feedback: "" };

    function showSurvey() {
        document.getElementById("survey-overlay").classList.remove("hidden");
        document.getElementById("survey-rejected").focus();
    }

    function goToStep(n) {
        document.querySelectorAll(".survey-step").forEach(function (el) { el.classList.add("hidden"); });
        document.getElementById("survey-step-" + n).classList.remove("hidden");
    }

    function submitSurveyAndRedirect() {
        surveyData.change_feedback = document.getElementById("survey-feedback").value.trim();
        fetch("/survey", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(surveyData),
        }).finally(function () { window.location.href = RESULTS_URL; });
    }

    // Step 1: rejected guess → next
    document.getElementById("survey-next-1").addEventListener("click", function () {
        surveyData.rejected_guess = document.getElementById("survey-rejected").value.trim();
        goToStep(2);
    });
    document.getElementById("survey-rejected").addEventListener("keydown", function (e) {
        if (e.key === "Enter") { document.getElementById("survey-next-1").click(); }
    });

    // Step 2: aha vs obscure
    document.getElementById("survey-feeling-aha").addEventListener("click", function () {
        surveyData.answer_feeling = "aha"; goToStep(3);
    });
    document.getElementById("survey-feeling-obscure").addEventListener("click", function () {
        surveyData.answer_feeling = "obscure"; goToStep(3);
    });

    // Step 3: time feeling
    document.getElementById("survey-time-less").addEventListener("click", function () {
        surveyData.time_feeling = "not_enough"; goToStep(4);
        document.getElementById("survey-feedback").focus();
    });
    document.getElementById("survey-time-right").addEventListener("click", function () {
        surveyData.time_feeling = "just_right"; goToStep(4);
        document.getElementById("survey-feedback").focus();
    });
    document.getElementById("survey-time-more").addEventListener("click", function () {
        surveyData.time_feeling = "too_much"; goToStep(4);
        document.getElementById("survey-feedback").focus();
    });

    // Step 4: submit / skip
    document.getElementById("survey-submit").addEventListener("click", submitSurveyAndRedirect);
    document.getElementById("survey-skip").addEventListener("click", submitSurveyAndRedirect);
});
