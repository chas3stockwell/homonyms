# Homonyms

A daily word game where you're given a single word and challenged to name as many of its meanings as you can in 3 minutes.

## How It Works

Every day, a new **homonym** (a word with multiple meanings) is revealed. You type descriptions of each meaning you can think of — for example, if the word is **"bank"**, you might type:

- "where you keep your money"
- "the side of a river"
- "to tilt an airplane in a turn"

Your guesses are evaluated by AI (Claude), so you don't need exact wording — just demonstrate you understand the meaning.

## Scoring

Each word has 5–6 definitions across difficulty tiers:

| Tier | Description |
|------|-------------|
| **Common** | Meanings most people know |
| **Niche** | Requires some domain knowledge |
| **Rare** | Obscure but real usages |
| **Unicorn** | Meanings almost nobody thinks of |

Your score is the percentage of definitions found. At the end, all meanings are revealed — including the ones you missed.

## Features

- **Daily puzzle** — same word for everyone, resets at midnight
- **3-minute timer** — think fast
- **AI-powered matching** — describe meanings in your own words
- **Shareable results** — copy a spoiler-free scorecard (e.g. `Homonyms #1 — CELL 4/6 ++++-​-`)
- **30 curated words** with definitions sourced from a hand-built word list

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file:

```
ANTHROPIC_API_KEY=sk-ant-...
SECRET_KEY=any-random-string
```

Run the app:

```bash
python app.py
```

Visit [http://localhost:5001](http://localhost:5001).

## Tech Stack

- **Flask** — routes, sessions, templates
- **Anthropic Claude API** — fuzzy definition matching
- **Vanilla JS** — timer, AJAX guesses, UI updates
- **No database** — game state lives in a signed session cookie
