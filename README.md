# Daily 3

A daily word game where you're given **3 words** and challenged to name as many of their meanings as you can in 3 minutes.

300+ players and counting.

## How It Works

Every day, a new **Daily 3** — three homonyms (words with multiple meanings) — is revealed. Switch between the three words using the tabs at the top. Type descriptions of each meaning you can think of — for example, if the word is **"bank"**, you might type:

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

Your score is the percentage of total definitions found across all three words. At the end, all meanings are revealed — including the ones you missed.

## Features

- **Daily 3** — three new words every day for everyone, resets at midnight
- **3-minute shared timer** — one clock across all three words
- **Word tabs** — switch between words mid-game, progress is saved
- **AI-powered matching** — describe meanings in your own words, Claude judges
- **Shareable results** — copy a spoiler-free scorecard after the game
- **30+ curated words** with definitions sourced from a hand-built word list
- **IP-based persistence** — game results saved server-side by player

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

## Deployment

Deployed on [Railway](https://railway.app). Set `ANTHROPIC_API_KEY` and `SECRET_KEY` as environment variables in the Railway dashboard — never commit the `.env` file.

## Tech Stack

- **Flask** — routes, sessions, templates
- **Anthropic Claude Haiku** — AI-powered definition matching per guess
- **Vanilla JS** — timer, AJAX guesses, real-time tab updates
- **No database** — game state in signed session cookie, results in flat JSON file
