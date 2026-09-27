# EduGenie

An AI learning assistant powered by the Google Gemini API. Ask questions, paste
notes for a summary, or generate a 5-question MCQ quiz on any topic.

## Architecture

```
  Browser  (HTML + CSS + JavaScript)
        |  fetch() JSON over HTTP
        v
  Flask   (app.py)  -- validation, error handling
        |
        v
  gemini_client.py   -- prompts, input limits, friendly errors
        |
        v
  Google Gemini API  (gemini-3.5-flash, via google-genai)
```

The API key is read from `.env` on the server and is never sent to the browser.

## Project layout

| File                      | Purpose                                          |
|---------------------------|--------------------------------------------------|
| `app.py`                  | Flask routes: `/`, `/ask`, `/summarize`, `/quiz`, `/health` |
| `gemini_client.py`        | Gemini setup, per-feature system prompts, error mapping |
| `templates/index.html`    | Page markup with three feature tabs              |
| `static/style.css`        | Dark theme styling                               |
| `static/app.js`           | Fetch calls, loading/error states, tab switching |
| `requirements.txt`        | Dependencies                                     |
| `render.yaml`             | Render.com blueprint for the free plan           |
| `Procfile`                | Gunicorn start command (Heroku-style hosts)      |
| `.env.example`            | Template for your API key                        |

## Deploy for free (Render)

1. Push this folder to a GitHub repository (`.env` is gitignored, the key never
   leaves your machine).
2. In Render: **New + -> Blueprint**, pick the repo. `render.yaml` is detected
   automatically, so the plan, build and start commands are filled in for you.
3. When Render asks for the `GEMINI_API_KEY` env var, paste your AI Studio key.
4. When the deploy is green you get a free address like
   `https://edugenie-xxxx.onrender.com`.

The free plan sleeps after ~15 minutes of no traffic, so the first request after
a pause takes 30-60 seconds while the server wakes up.

## Setup

### 1. API key

1. Go to <https://aistudio.google.com/apikey>
2. Sign in with a Google account, click **Create API key**, copy it.
3. In this folder, copy `.env.example` to `.env` and paste the key:

```
GEMINI_API_KEY=REDACTED
```

### 2. Run

```bash
./run.sh          # Linux / macOS - creates .venv, installs deps, starts Flask
run.bat           # Windows
```

Or manually:

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000>.

Requires **Python 3.9+** (the `google-genai` package will not install on 3.8).

> Using the older `google-generativeai` SDK? It is deprecated and the `gemini-1.5-*`
> models have been shut down, so this project targets `google-genai` + Gemini 3.x Flash.

## Configuration

| Variable        | Default                    | Notes                                  |
|-----------------|----------------------------|----------------------------------------|
| `GEMINI_API_KEY`| *(required)*               | From AI Studio                         |
| `GEMINI_MODEL`  | `gemini-3.5-flash`        | Any model your key can reach, e.g. `gemini-3.5-flash-lite` or `gemini-flash-latest` |
| `FLASK_DEBUG`   | `0`                        | Set to `1` for auto-reload             |
| `PORT`          | `5000`                     |                                        |

## Features

- **Ask a Question** - a student-style answer to any doubt, with the model's
  assumptions stated when a question is ambiguous.
- **Summarize Notes** - pasted notes condensed to 3 bullet points plus the one
  key term to revise. Live character counter.
- **Generate Quiz** - 5 MCQs with options and answer keys on any topic.

Shared behaviour:

- Tabs instead of one long page, so each feature gets its own space.
- Buttons disable and show "Working..." while Gemini is generating, and inputs
  lock so a request can't be fired twice.
- Server-side validation: empty or over-8000-character input is rejected with a
  readable message instead of a stack trace.
- Gemini failures (bad key, exhausted quota, blocked prompt, timeout) are mapped
  to plain-language errors.
- AI output is inserted with `textContent`, not `innerHTML`, so model output can
  never inject markup into the page.

## Troubleshooting

| Symptom                          | Fix                                                        |
|----------------------------------|------------------------------------------------------------|
| "GEMINI_API_KEY is not set"      | `.env` is missing or the key name is misspelled.           |
| "Gemini rejected the API key"    | Key revoked or copied with extra spaces.                   |
| "Gemini's free quota is used up" | Free tier rate limit - wait a minute.                      |
| Blank page, nothing renders      | Static files not served - keep `static/` and `templates/` next to `app.py`. |

## Future scope

- Voice input for questions
- Multi-language answers (regional languages)
- Login plus saved history of questions and quizzes
- Flashcards and spaced-repetition revision from pasted notes
- PDF/Word export of generated quizzes
