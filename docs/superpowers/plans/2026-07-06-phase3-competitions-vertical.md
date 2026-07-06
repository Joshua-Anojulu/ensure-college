# Phase 3: Competitions Vertical Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Add a third catalog vertical — **Competitions** (science fairs, olympiads, hackathons, business/debate, essay contests) — matched to a student's profile exactly like Scholarships and Summer Programs, reusing the shared matching engine and UI patterns.

**Architecture:** Mirror the existing **Summer Programs** vertical (spec Option A). New `Competition` model reuses the scholarship building blocks (`Eligibility`, `ApplicationRequirement`, `VerificationMetadata`) and the shared `app.matching.common` helpers, so scoring stays consistent. Data is a curated JSON catalog loaded into `app.state` on startup (in-memory, same as programs — fine at this dataset size; see Scale note). Frontend adds a Competitions tab that reuses the program-card renderer.

**Tech Stack:** FastAPI, Pydantic, vanilla-JS frontend, pytest. Run Python via `.venv\Scripts\python.exe`.

## Global Constraints

- **Mirror the programs vertical** — follow `app/models/program.py`, `app/matching/program_matcher.py`, `load_summer_programs`, the `/programs` + `/programs/match` routes, and the program card UI. Consistency over novelty.
- **Reuse** `Eligibility`, `ApplicationRequirement`, `SpecialRequirement`, `VerificationMetadata` from `app/models/scholarship.py`, and the helpers in `app/matching/common.py` (`grade_level_matches`, `citizenship_satisfies`, `matching_fields`, `matching_demographics`, `parse_iso_deadline`). Do NOT duplicate scoring logic.
- **VERIFY discipline (non-negotiable):** every dataset field whose current-cycle value isn't confirmed from an **official source** stays the literal `"VERIFY"`. Never fabricate deadlines, prizes, eligibility, or URLs. Cite sources in each record's `verification`.
- **Scale:** keep the catalog in-memory + linear scoring (matches programs; competition counts are in the hundreds at most). Do NOT add a DB-backed search here — that decision is reserved for the future College-search vertical.
- Keep the full suite green (currently 208). Commit as the repo owner (Claude co-author trailer is fine on this repo).
- No AI features are involved; `AI_FEATURES_ENABLED` stays off.

---

### Task 1: `Competition` model

**Files:**
- Create: `app/models/competition.py`
- Test: `tests/test_competitions.py` (created here, expanded in Task 4)

**Interfaces:**
- Consumes: `Eligibility`, `ApplicationRequirement`, `SpecialRequirement`, `VerificationMetadata` from `app.models.scholarship`.
- Produces: `Competition`, `CompetitionScoreBreakdown`, `CompetitionMatchResult`, and the literals `CompetitionCostCategory`, `ParticipationFormat`.

- [ ] **Step 1: Write the failing test** in `tests/test_competitions.py`:

```python
from app.models.competition import Competition
from app.models.scholarship import Eligibility


def test_competition_defaults_unconfirmed_fields_to_verify():
    c = Competition(
        id="isef",
        name="Regeneron ISEF",
        host="Society for Science",
        category="STEM research",
        url="https://www.societyforscience.org/isef/",
        eligibility=Eligibility(),
        description="International science and engineering fair.",
    )
    assert c.cost_category == "VERIFY"
    assert c.participation_format == "VERIFY"
    assert c.deadline == "VERIFY"
    assert c.verified is False
```

- [ ] **Step 2: Run to verify it fails**
  Run: `.venv\Scripts\python.exe -m pytest tests/test_competitions.py -q` → FAIL (module missing).

- [ ] **Step 3: Implement `app/models/competition.py`** mirroring `app/models/program.py`. Field mapping vs. SummerProgram: `host` (sponsor/organizer), `category` (subject label, replaces `subject`), `recognition` (award/prize/recognition, replaces `selectivity`), `participation_format` (individual/team, replaces `program_format`), `competition_dates` (replaces `program_dates`), plus `cost`/`cost_category`, `deadline`, `estimated_deadline`, `eligibility`, `description`, `application_requirements`, `verified`, `verification`.

```python
"""Models for the competitions feature.

A Competition reuses the scholarship building blocks (Eligibility,
ApplicationRequirement, VerificationMetadata) and adds the facts that matter for
a competition: category, recognition/prize, participation format, cost, and run
dates. The same VERIFY discipline applies: an unconfirmed field stays "VERIFY".
"""
from __future__ import annotations

from datetime import date
from typing import Literal, Union

from pydantic import BaseModel, Field, HttpUrl

from app.models.scholarship import (
    ApplicationRequirement,
    Eligibility,
    SpecialRequirement,
    VerificationMetadata,
)

CompetitionCostCategory = Literal["free", "stipend", "paid", "VERIFY"]
ParticipationFormat = Literal["individual", "team", "either", "VERIFY"]


class Competition(BaseModel):
    """A curated, verified competition (a college-application enhancer)."""

    id: str
    name: str
    host: str = Field(description="Sponsoring/organizing body.")
    category: str = Field(description="Short category label, e.g. 'STEM research'.")
    url: HttpUrl
    cost: str = Field(default="VERIFY", description='Human-readable cost, e.g. "Free to enter".')
    cost_category: CompetitionCostCategory = "VERIFY"
    recognition: str = Field(
        default="VERIFY",
        description='Human-readable prize/recognition, e.g. "Cash prizes; national medal".',
    )
    participation_format: ParticipationFormat = "VERIFY"
    location: str = "VERIFY"
    competition_dates: str = Field(
        default="VERIFY",
        description="When the competition runs, distinct from the registration deadline.",
    )
    deadline: Union[str, Literal["rolling"]] = Field(
        default="VERIFY",
        description='Registration deadline: ISO date (YYYY-MM-DD), "rolling", or "VERIFY".',
    )
    estimated_deadline: str | None = Field(
        default=None,
        description="Approximate ISO deadline from a prior cycle; informational only.",
    )
    eligibility: Eligibility
    description: str
    application_requirements: list[ApplicationRequirement] = Field(default_factory=list)
    verified: bool = False
    verification: VerificationMetadata | None = None


class CompetitionScoreBreakdown(BaseModel):
    """Per-component contributions to a competition's fit score (all additive)."""

    category: float = 0.0
    demographics: float = 0.0
    financial_access: float = 0.0
    total: float = 0.0


class CompetitionMatchResult(BaseModel):
    """A competition scored for one student, with transparent reasons."""

    competition_id: str
    name: str
    host: str
    category: str
    cost: str
    cost_category: CompetitionCostCategory
    recognition: str
    participation_format: ParticipationFormat
    location: str
    competition_dates: str
    deadline: str
    estimated_deadline: str | None
    url: str
    verified: bool
    verification_source_url: str | None
    last_verified_at: date | None
    essay_required: bool
    score: float
    match_tier: str
    match_reasons: list[str]
    score_breakdown: CompetitionScoreBreakdown
    application_requirements: list[ApplicationRequirement] = Field(default_factory=list)
    requires_special_check: bool = False
    special_requirements: list[SpecialRequirement] = Field(default_factory=list)
```

- [ ] **Step 4: Run to verify it passes** → `pytest tests/test_competitions.py -q` PASS.
- [ ] **Step 5: Commit** `git add app/models/competition.py tests/test_competitions.py && git commit -m "Add Competition model"`

---

### Task 2: Competition matcher

**Files:**
- Create: `app/matching/competition_matcher.py`
- Test: `tests/test_competitions.py` (add matcher cases)

**Interfaces:**
- Consumes: `app.matching.common` helpers; `Competition`, `CompetitionMatchResult`, `CompetitionScoreBreakdown`; `StudentProfile`.
- Produces: `match_competitions(student, competitions, *, today=None) -> list[CompetitionMatchResult]`.

- [ ] **Step 1: Write failing matcher tests** (add to `tests/test_competitions.py`) — mirror `tests/test_matcher.py`/`test_programs.py`: a strong category match scores high; a passed real deadline excludes; a grade-gate excludes when not met; an open-category competition still appears as "possible". (Use the existing test helpers' pattern for building a `StudentProfile`.)

- [ ] **Step 2: Run → FAIL** (`match_competitions` missing).

- [ ] **Step 3: Implement `app/matching/competition_matcher.py`** by copying `app/matching/program_matcher.py` and renaming program→competition, `subject`→`category`, `program_format`→`participation_format`, `selectivity`→`recognition`, `program_dates`→`competition_dates`. Keep the identical gates (grade/gpa/citizenship/deadline), the identical additive weights (`WEIGHT_SUBJECT=40`, `_OPEN=10`, `DEMOGRAPHICS=25`, `FINANCIAL_ACCESS=10`, `STRONG_MATCH_THRESHOLD=35`), the field-mismatch and special-requirement tier downgrades, and the same sort (`-score`, then name). The category overlap uses `matching_fields(student.intended_majors, elig.fields_of_study)` exactly as programs do.

- [ ] **Step 4: Run → PASS**; then full suite `pytest tests/ -q`.
- [ ] **Step 5: Commit** `git add app/matching/competition_matcher.py tests/test_competitions.py && git commit -m "Add transparent competition matcher"`

---

### Task 3: Loader + seed dataset + validator

**Files:**
- Modify: `app/data/loader.py` (add `load_competitions()`)
- Create: `app/data/competitions.json`
- Modify: `scripts/validate_dataset.py`, `tests/test_dataset.py` (cover competitions)

**Interfaces:**
- Produces: `load_competitions() -> list[Competition]`.

- [ ] **Step 1:** Add `load_competitions()` to `app/data/loader.py`, mirroring `load_summer_programs()` (same `_dataset_notice`/list-key handling, same Pydantic validation, same error behavior).
- [ ] **Step 2: Create `app/data/competitions.json`** with a `_dataset_notice` and a **seed of ~12–15 real, currently-relevant competitions**, each sourced from its **official page**, with unconfirmed fields left as `"VERIFY"` and `verification` populated. Seed candidates (verify each against the official site — do NOT trust memory for dates/prizes): Regeneron ISEF, Regeneron STS, AMC→AIME→USAMO, Congressional App Challenge, Congressional Art Competition, DECA ICDC, FBLA NLC, NSDA Nationals (debate), Scholastic Art & Writing Awards, National History Day, Conrad Challenge, Diamond Challenge (entrepreneurship), a national essay contest (e.g. Profile in Courage / John Locke). Categories should map to `intended_majors` vocabulary so matching works.
- [ ] **Step 3:** Extend `scripts/validate_dataset.py` and `tests/test_dataset.py` to validate `competitions.json` structurally and count its `VERIFY` placeholders, mirroring the summer-programs coverage.
- [ ] **Step 4:** Run `.venv\Scripts\python.exe scripts\validate_dataset.py` and `pytest tests/test_dataset.py -q` → pass.
- [ ] **Step 5: Commit** `git add app/data/loader.py app/data/competitions.json scripts/validate_dataset.py tests/test_dataset.py && git commit -m "Add competitions dataset, loader, and validator coverage"`

---

### Task 4: Routes + startup load

**Files:**
- Modify: `app/main.py`

**Interfaces:**
- Consumes: `load_competitions`, `match_competitions`, `Competition`, `CompetitionMatchResult`.
- Produces: `GET /competitions`, `POST /competitions/match`; `app.state.competitions`.

- [ ] **Step 1: Write failing route tests** (add to `tests/test_competitions.py` or `tests/test_api.py`): `GET /competitions` returns 200 + a non-empty list; `POST /competitions/match` with a valid `StudentProfile` returns 200 + a ranked list. Mirror the existing `/programs` route tests.
- [ ] **Step 2: Run → FAIL.**
- [ ] **Step 3: Implement**, mirroring the programs routes (`app/main.py` ~lines 258-266) and the lifespan dataset load:
  - In `lifespan`, add `app.state.competitions = load_competitions()`.
  - Add imports for `load_competitions`, `match_competitions`, `Competition`, `CompetitionMatchResult`.
  - Add:
    ```python
    @app.get("/competitions")
    def get_competitions(request: Request) -> list[Competition]:
        return request.app.state.competitions

    @app.post("/competitions/match")
    def match_competition_list(request: Request, student: StudentProfile) -> list[CompetitionMatchResult]:
        competitions: list[Competition] = request.app.state.competitions
        return match_competitions(student, competitions)
    ```
- [ ] **Step 4: Run → PASS**; full suite green.
- [ ] **Step 5: Commit** `git add app/main.py tests/ && git commit -m "Add /competitions and /competitions/match routes"`

---

### Task 5: Frontend — Competitions tab

**Files:**
- Modify: `app/static/index.html` (nav/tab + a competitions results lane)
- Modify: `app/static/js/app.js` (fetch `/competitions/match`, render cards, wire the tab, saved items)
- Modify: `app/static/css/style.css` only if a competition-specific token/label is needed

**Interfaces:**
- Consumes: `/competitions`, `/competitions/match`.

- [ ] **Step 1:** Locate the Summer Programs frontend wiring in `app.js` — the vertical/tab switch (`activateOpportunityView`, `ensureCatalogData`, `loadPrograms`, `renderPrograms`, `buildProgramCard`, `buildCatalogProgramSection`) — and the programs tab markup in `index.html`. These are your templates.
- [ ] **Step 2:** Add a **Competitions** tab/vertical mirroring programs: a `loadCompetitions(profile)` that POSTs to `/competitions/match`, a `renderCompetitions()`, and a `buildCompetitionCard()` cloned from `buildProgramCard()` (swap program fields → competition fields: `recognition`, `participation_format`, `competition_dates`). Reuse the existing requirement-matrix, deadline/ICS, and saved-items code paths.
- [ ] **Step 3: Verify** by running the app locally (`.venv\Scripts\python.exe -m uvicorn app.main:app --port 8099`): the Competitions tab loads, a profile match shows ranked competition cards with reasons, deadlines/saved-items work, no console errors. (No JS unit runner — verify in-browser + keep the Python route tests green.)
- [ ] **Step 4: Full suite** `pytest tests/ -q` → green.
- [ ] **Step 5: Commit** `git add app/static && git commit -m "Add Competitions tab to the frontend"`

---

## Self-review notes
- Spec §5 coverage: model (T1), matcher (T2), dataset+loader+validator (T3), routes+state (T4), UI (T5) — all mapped.
- Reuses shared `Eligibility`/`common.py` — no duplicated scoring, per Global Constraints.
- Kept in-memory + linear (Scale note) — DB-backed search deferred to the future College-search vertical.
- Dataset authored under VERIFY discipline; unconfirmed fields stay `VERIFY`, sources cited.
