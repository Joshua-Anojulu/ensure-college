# Scholarships4U

Scholarships4U is a personal portfolio project that helps U.S. students explore a small curated set of real national scholarships. Students submit a profile, receive ranked matches with transparent scoring, and can request essay guidance generated server-side by an LLM.

## How it works

**Matching.** The app scores each scholarship with a transparent additive algorithm over field-of-study overlap and demographic tag overlap. GPA, grade level, state, citizenship, and passed deadlines act as hard filters only when the dataset holds a real value (not a `VERIFY` placeholder). Open-to-all scholarships receive a lower field score than specific field matches. Results are grouped into **Strong** and **Possible** tiers, with tie-breaking by confirmed upcoming deadlines and then scholarship name. Every match includes human-readable reasons and a numeric score breakdown.

**Essay advice.** When a student clicks **Get essay advice** on a result card, the backend sends the student's actual profile inputs and the scholarship description to the Anthropic API. The response suggests essay angles tied to the student's stated activities and background, notes what the sponsor likely values, and flags one common mistake. The API key never leaves the server.

## Tech stack

- **Backend:** Python, FastAPI
- **Frontend:** Vanilla HTML, CSS, and JavaScript (served by FastAPI)
- **Data:** Pydantic models, local JSON file loaded at startup
- **LLM:** Anthropic API (Claude Sonnet) for essay advice, server-side only

## Run locally

### 1. Create a virtual environment

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS or Linux:

```bash
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

For development and tests:

```bash
pip install -r requirements-dev.txt
```

### 3. Set the API key

Copy the example env file and add your key:

```bash
copy .env.example .env
```

On macOS or Linux, use `cp .env.example .env`.

Edit `.env` and set:

```
ANTHROPIC_API_KEY=your_key_here
```

The real key belongs only in `.env`, which is gitignored. Do not put a real key in `.env.example`.

Essay advice requires a valid key. Each request incurs Anthropic API usage cost.

### 4. Start the server

```bash
uvicorn app.main:app --reload
```

Open the app at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Deploy (Render)

This repo includes a [`render.yaml`](render.yaml) for [Render](https://render.com/) free-tier web services.

1. Push the repository to GitHub (without `.env`).
2. In Render, create a **Blueprint** or **Web Service** from the repo.
3. Render reads `render.yaml` and uses:
   - **Build:** `pip install -r requirements.txt`
   - **Start:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. In the Render dashboard, set **Environment Variables**:
   - `ANTHROPIC_API_KEY` = your Anthropic API key

Do not commit the API key. Set it only in the host's environment variable UI.

### Railway (alternative)

1. Create a new project from the GitHub repo.
2. Set the start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

3. Add `ANTHROPIC_API_KEY` in Railway's **Variables** tab.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Web app |
| `GET` | `/health` | Health check |
| `GET` | `/vocabulary` | Form option lists |
| `GET` | `/scholarships` | Full dataset |
| `POST` | `/match` | Rank scholarships for a profile |
| `POST` | `/essay-advice` | Generate essay guidance |

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

Tests mock Anthropic calls. No paid API usage during the test run.

## Project structure

```
ScholarMatch/
├── render.yaml
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── tests/
└── app/
    ├── main.py
    ├── vocabulary.py
    ├── essay/
    ├── matching/
    ├── models/
    ├── static/
    └── data/
        └── scholarships.json
```

## Limitations

- The scholarship dataset is a **small curated seed set** (18 entries), not a comprehensive directory.
- Some fields are marked `VERIFY` and must be confirmed on each sponsor's official page before you rely on them.
- Essay advice is generated guidance, not a guarantee of admission or funding.
- This is a **personal portfolio project**, not an official scholarship search or application service.

## Future work

- Resume parsing as a profile intake method
- Expand and fully verify the scholarship dataset
- School-specific scholarship matching
- Live data integration with sponsor feeds or APIs

---

*Scholarships4U is a personal project built for learning and demonstration.*
