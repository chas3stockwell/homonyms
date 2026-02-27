document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("guess-form");
    const input = document.getElementById("guess-input");
    const submitBtn = document.getElementById("submit-btn");
    const timerEl = document.getElementById("timer");
    const matchedList = document.getElementById("matched-list");
    const guessList = document.getElementById("guess-list");
    const progressEl = document.getElementById("progress");
    const activeTabProgress = document.getElementById("active-tab-progress");
    const placeholders = document.getElementById("placeholders");

    const endTimestamp = parseFloat(document.body.dataset.endTimestamp);
    let gameOver = false;

    // --- Timer ---
    function updateTimer() {
        const now = Date.now() / 1000;
        const remaining = Math.max(0, endTimestamp - now);
        const minutes = Math.floor(remaining / 60);
        const seconds = Math.floor(remaining % 60);
        timerEl.textContent = minutes + ":" + seconds.toString().padStart(2, "0");

        if (remaining <= 30) {
            timerEl.classList.add("timer-warning");
        }

        if (remaining <= 0) {
            clearInterval(timerInterval);
            handleTimeUp();
        }
    }

    const timerInterval = setInterval(updateTimer, 250);
    updateTimer();

    function handleTimeUp() {
        if (gameOver) return;
        gameOver = true;
        input.disabled = true;
        submitBtn.disabled = true;

        fetch("/time-up", { method: "POST" })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.redirect) window.location.href = data.redirect;
            });
    }

    // --- Guess Submission ---
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
            body: JSON.stringify({ guess: guess }),
        })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.error === "Time is up" || data.redirect) {
                    if (data.redirect) window.location.href = data.redirect;
                    return;
                }

                if (data.matched) {
                    addMatchedDefinition(data.matched_definition);
                    progressEl.textContent =
                        data.matched_count + "/" + data.total_definitions + " found";
                    if (activeTabProgress) {
                        activeTabProgress.textContent =
                            data.matched_count + "/" + data.total_definitions;
                    }
                    input.classList.add("flash-success");
                    setTimeout(function () {
                        input.classList.remove("flash-success");
                    }, 600);
                } else {
                    addGuessToHistory(guess);
                    input.classList.add("flash-fail");
                    setTimeout(function () {
                        input.classList.remove("flash-fail");
                    }, 600);
                }

                if (data.all_found && data.redirect) {
                    setTimeout(function () {
                        window.location.href = data.redirect;
                    }, 800);
                    return;
                }
            })
            .catch(function (err) {
                console.error("Guess error:", err);
            })
            .finally(function () {
                input.value = "";
                input.disabled = false;
                submitBtn.disabled = false;
                submitBtn.textContent = "Go";
                input.focus();
            });
    });

    function addGuessToHistory(text) {
        var li = document.createElement("li");
        li.className = "guess-miss";
        li.innerHTML =
            '<span class="guess-icon">&#10007;</span> ' +
            '<span class="guess-text">"' + escapeHtml(text) + '"</span>';
        guessList.prepend(li);
    }

    function addMatchedDefinition(defText) {
        var div = document.createElement("div");
        div.className = "matched-def animate-in";
        div.innerHTML =
            '<span class="check">&#10003;</span> ' +
            '<span class="def-text">' + escapeHtml(defText) + "</span>";
        matchedList.appendChild(div);

        // Remove one placeholder
        var placeholder = placeholders.querySelector(".def-placeholder");
        if (placeholder) placeholder.remove();
    }

    function escapeHtml(str) {
        var div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }
});
