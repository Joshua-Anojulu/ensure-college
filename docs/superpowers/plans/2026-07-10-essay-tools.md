# Essay Tools (Non-AI) + Auto-Match Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Verified essay prompts attached to requirement steps, start-by dates in the plan timeline, five public essay guide pages, and auto-match on session restore — no AI anywhere.

**Architecture:** Prompts are optional structured data on the existing `ApplicationRequirement` model (Option A from the spec), so the reuse map, checklists, and SEO detail pages render them from data they already iterate. Guides are server-rendered Jinja2 pages in a new focused module (`app/guide_pages.py`) following the `seo_pages.py` pattern. Start-by dates and auto-match are client-side only.

**Tech Stack:** FastAPI + Pydantic v2, Jinja2, vanilla JS (`app/static/js/app.js`), pytest.

**Spec:** `docs/superpowers/specs/2026-07-10-essay-tools-design.md` — read it first.

## Global Constraints

- No AI features; `app/essay/` stays dormant behind `AI_FEATURES_ENABLED`.
- No new Plan-tab sections; prompts collapsed by default (`<details>`); one guide link per reuse-map cluster; gated prompts = one muted line; homepage hero untouched.
- CSP is `script-src 'self'` — no inline `<script>`; interactive prompt display must be native `<details>`.
- Copy rules: at most one em dash per page of new copy; never the word "unlock"; light-only styling (no dark tokens).
- `length` strings mirror official sponsor wording verbatim; prompt text verbatim; no fabrication — absence of data stays meaningful.
- Asset cache-busting: bumping `style.css`/`app.js` requires updating the `?v=` query in BOTH `app/static/index.html` and `app/templates/base.html` (style only) AND the assertions in `tests/test_pages.py`. Current version: `20260710-2`.
- Run tests with `.venv\Scripts\python.exe -m pytest tests/ -q` from the repo root. Full suite green before every commit.
- Commit trailer `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>` is allowed in this repo.

## File Structure

- `app/models/scholarship.py` — add `EssayPromptItem`, `EssayPrompts` beside `ApplicationRequirement`; new optional field on `ApplicationRequirement` (shared by programs/competitions/match via existing imports).
- `app/templates/detail.html` — prompt rendering in the requirements section.
- `app/static/js/app.js` — prompt blocks in reuse map + checklists; start-by dates; match-flow extraction + auto-match.
- `app/static/css/style.css` — styles for prompt details, chips, start-by lines, guide pages.
- `app/guide_pages.py` (new) — guides router, theme registry, content loading.
- `app/data/essay_guides.json` (new) — guide content + curated external links.
- `app/templates/guide.html`, `app/templates/guides_index.html` (new).
- `app/main.py` — include guides router; add guide URLs to sitemap.
- `tests/test_essay_prompts.py`, `tests/test_guide_pages.py` (new); `tests/test_pages.py` (asset assertions).

---

### Task 1: Prompt data model + SEO detail rendering

**Files:**
- Modify: `app/models/scholarship.py` (after `ApplicationRequirement`, ~line 33-45)
- Modify: `app/templates/detail.html` (requirements block, lines 46-55)
- Create: `tests/test_essay_prompts.py`

**Interfaces:**
- Produces: `EssayPromptItem(prompt: str, length: str | None)`, `EssayPrompts(status: Literal["public","gated"], items: list[EssayPromptItem])`, and `ApplicationRequirement.essay_prompts: EssayPrompts | None` (default `None`). JSON key in catalog files: `"essay_prompts"`. Tasks 2 and 5 rely on these exact names.

- [ ] **Step 1: Write the failing model tests**

Create `tests/test_essay_prompts.py`:

```python
import pytest
from pydantic import ValidationError

from app.models.scholarship import ApplicationRequirement, EssayPromptItem, EssayPrompts


class TestEssayPromptsModel:
    def test_public_prompts_round_trip(self):
        req = ApplicationRequirement(
            id="essays",
            label="Complete the essays",
            essay_prompts={
                "status": "public",
                "items": [{"prompt": "Describe a community you belong to.", "length": "150-250 words"}],
            },
        )
        assert req.essay_prompts.status == "public"
        assert req.essay_prompts.items[0].prompt.startswith("Describe")
        assert req.essay_prompts.items[0].length == "150-250 words"

    def test_requirement_without_prompts_stays_none(self):
        req = ApplicationRequirement(id="apply", label="Apply online")
        assert req.essay_prompts is None

    def test_public_requires_at_least_one_item(self):
        with pytest.raises(ValidationError):
            EssayPrompts(status="public", items=[])

    def test_gated_requires_empty_items(self):
        with pytest.raises(ValidationError):
            EssayPrompts(status="gated", items=[EssayPromptItem(prompt="x")])

    def test_gated_with_empty_items_is_valid(self):
        prompts = EssayPrompts(status="gated", items=[])
        assert prompts.status == "gated"

    def test_unknown_status_rejected(self):
        with pytest.raises(ValidationError):
            EssayPrompts(status="varies", items=[])

    def test_blank_prompt_text_rejected(self):
        with pytest.raises(ValidationError):
            EssayPromptItem(prompt="   ")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_essay_prompts.py -q`
Expected: FAIL / ERROR with `ImportError: cannot import name 'EssayPromptItem'`.

- [ ] **Step 3: Implement the models**

In `app/models/scholarship.py`, add directly after the `ApplicationRequirement` class (keep imports: `Literal` is already imported for `SpecialRequirement`; add `model_validator` to the existing pydantic import):

```python
class EssayPromptItem(BaseModel):
    """One official essay/short-answer prompt, recorded verbatim."""

    prompt: str = Field(min_length=1, max_length=1000)
    length: str | None = Field(
        default=None,
        max_length=80,
        description="Sponsor's own length wording, e.g. '650 words max'.",
    )

    @model_validator(mode="after")
    def _prompt_not_blank(self) -> "EssayPromptItem":
        if not self.prompt.strip():
            raise ValueError("prompt must not be blank")
        return self


class EssayPrompts(BaseModel):
    """Verified prompt data for one requirement step."""

    status: Literal["public", "gated"]
    items: list[EssayPromptItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def _status_shape(self) -> "EssayPrompts":
        if self.status == "public" and not self.items:
            raise ValueError("public prompts require at least one item")
        if self.status == "gated" and self.items:
            raise ValueError("gated prompts must have no items")
        return self
```

Then add the field to `ApplicationRequirement` (after `source_url`):

```python
    essay_prompts: "EssayPrompts | None" = None
```

Note: because `EssayPrompts` is defined after `ApplicationRequirement`, either move the two new classes ABOVE `ApplicationRequirement` (preferred — no forward ref needed, drop the quotes) or call `ApplicationRequirement.model_rebuild()` after the definitions. Prefer moving them above.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_essay_prompts.py -q`
Expected: 7 passed.

- [ ] **Step 5: Write the failing detail-page rendering test**

Append to `tests/test_essay_prompts.py`:

```python
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


class TestDetailPagePrompts:
    def _first_scholarship_with_requirements(self, client):
        state = client.app.state
        for entry in state.scholarships:
            if entry.application_requirements:
                return entry
        pytest.skip("no scholarship with requirements in catalog")

    def test_public_prompts_render_in_details_element(self, client):
        entry = self._first_scholarship_with_requirements(client)
        entry.application_requirements[0].essay_prompts = EssayPrompts(
            status="public",
            items=[EssayPromptItem(prompt="Why does this scholarship matter to you?", length="500 words max")],
        )
        try:
            response = client.get(f"/scholarships/{entry.id}")
            assert response.status_code == 200
            assert "<details" in response.text
            assert "Why does this scholarship matter to you?" in response.text
            assert "500 words max" in response.text
        finally:
            entry.application_requirements[0].essay_prompts = None

    def test_gated_prompts_render_muted_line(self, client):
        entry = self._first_scholarship_with_requirements(client)
        entry.application_requirements[0].essay_prompts = EssayPrompts(status="gated", items=[])
        try:
            response = client.get(f"/scholarships/{entry.id}")
            assert response.status_code == 200
            assert "Prompts revealed after registration" in response.text
        finally:
            entry.application_requirements[0].essay_prompts = None
```

- [ ] **Step 6: Run to verify the two new tests fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_essay_prompts.py -q`
Expected: 7 passed, 2 failed (missing markup).

- [ ] **Step 7: Render prompts in detail.html**

Replace the requirements `<li>` body in `app/templates/detail.html` (lines 50-52) with:

```html
        {% for req in requirements %}
        <li>
          <strong>{{ req.label }}</strong>{% if req.details %}: {{ req.details }}{% endif %}
          {% if req.essay_prompts and req.essay_prompts.status == "public" %}
          <details class="prompt-details">
            <summary>Essay prompt{{ "s" if req.essay_prompts.items | length > 1 else "" }}</summary>
            <ul class="prompt-list">
              {% for item in req.essay_prompts.items %}
              <li>{{ item.prompt }}{% if item.length %} <span class="prompt-length">{{ item.length }}</span>{% endif %}</li>
              {% endfor %}
            </ul>
          </details>
          {% elif req.essay_prompts and req.essay_prompts.status == "gated" %}
          <p class="prompt-gated">Prompts revealed after registration on the sponsor site.</p>
          {% endif %}
        </li>
        {% endfor %}
```

- [ ] **Step 8: Run the full suite**

Run: `.venv\Scripts\python.exe -m pytest tests/ -q`
Expected: all pass (316 existing + 9 new).

- [ ] **Step 9: Commit**

```bash
git add app/models/scholarship.py app/templates/detail.html tests/test_essay_prompts.py
git commit -m "Add verified essay prompt model and detail-page rendering"
```

---

### Task 2: Reuse map + checklist prompts, start-by dates

**Files:**
- Modify: `app/static/js/app.js` (`buildEssayReuseMap` ~line 2870, `buildApplicationChecklist` ~line 3219, `buildDeadlineTimeline` ~line 2749)
- Modify: `app/static/css/style.css` (new classes), `app/static/index.html` + `app/templates/base.html` (asset `?v=` → `20260710-3`)
- Modify: `tests/test_pages.py` (asset assertions), `tests/test_essay_prompts.py` (JS source smoke tests)

**Interfaces:**
- Consumes: `req.essay_prompts` JSON shape from Task 1 (arrives in match/saved payloads automatically via existing models).
- Produces: JS helpers `buildPromptBlock(requirement)` -> `HTMLElement | null` and `essayStartByLabel(item)` -> `string | null` (used only within app.js).

- [ ] **Step 1: Write failing JS-source smoke tests**

Append to `tests/test_essay_prompts.py`:

```python
from pathlib import Path

APP_JS = Path(__file__).resolve().parent.parent / "app" / "static" / "js" / "app.js"


class TestFrontendPromptWiring:
    def test_app_js_defines_prompt_block_and_start_by(self):
        source = APP_JS.read_text(encoding="utf-8")
        assert "function buildPromptBlock" in source
        assert "function essayStartByLabel" in source
        assert "Prompts revealed after registration" in source
        assert "Start drafting by" in source
```

Run: `.venv\Scripts\python.exe -m pytest tests/test_essay_prompts.py -q` — expected: 1 new failure.

- [ ] **Step 2: Add the JS helpers**

In `app/static/js/app.js`, directly above `function buildEssayReuseMap(items)` (~line 2870), add:

```javascript
function buildPromptBlock(requirement) {
  const prompts = requirement.essay_prompts;
  if (!prompts) return null;
  if (prompts.status === "gated") {
    const note = document.createElement("p");
    note.className = "prompt-gated";
    note.textContent = "Prompts revealed after registration on the sponsor site.";
    return note;
  }
  if (prompts.status !== "public" || !prompts.items?.length) return null;
  const details = document.createElement("details");
  details.className = "prompt-details";
  const summary = document.createElement("summary");
  summary.textContent = prompts.items.length > 1 ? "Essay prompts" : "Essay prompt";
  details.appendChild(summary);
  const list = document.createElement("ul");
  list.className = "prompt-list";
  for (const item of prompts.items) {
    const li = document.createElement("li");
    li.textContent = item.prompt;
    if (item.length) {
      const chip = document.createElement("span");
      chip.className = "prompt-length";
      chip.textContent = item.length;
      li.appendChild(document.createTextNode(" "));
      li.appendChild(chip);
    }
    list.appendChild(li);
  }
  details.appendChild(list);
  return details;
}

const ESSAY_START_LEAD_DAYS = 21;

function essayStartByDate(item) {
  const hasWriting = incompleteRequirements(item).some((requirement) =>
    isWritingRequirement(requirement)
  );
  if (!hasWriting) return null;
  const deadline =
    savedOpportunityDeadline(item) ||
    item.scholarship?.estimated_deadline ||
    item.program?.estimated_deadline ||
    item.competition?.estimated_deadline ||
    null;
  if (!deadline) return null;
  const parsed = new Date(`${deadline}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return null;
  parsed.setDate(parsed.getDate() - ESSAY_START_LEAD_DAYS);
  return parsed;
}

function essayStartByLabel(item) {
  const start = essayStartByDate(item);
  if (!start) return null;
  if (start <= new Date()) return "Essays: start now";
  const text = start.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  return `Start drafting by ${text}`;
}
```

Note: `savedOpportunityDeadline`, `incompleteRequirements`, and `isWritingRequirement` already exist in app.js — verify the exact deadline accessor returns an ISO string (it feeds `daysUntil` today) and adjust the fallback chain to whatever estimated-deadline accessor already exists before inventing the property chain above.

- [ ] **Step 3: Wire prompts + start-by into the three surfaces**

(a) In `buildEssayReuseMap`, inside the `for (const need of cluster.needs.slice(0, 4))` loop, after `li.textContent = ...`, append the prompt block:

```javascript
      const promptBlock = buildPromptBlock(need.requirement);
      if (promptBlock) li.appendChild(promptBlock);
```

(b) In the same function, after `meta.textContent = ...`, add the cluster's earliest start line:

```javascript
    const startDates = cluster.needs
      .map((need) => essayStartByDate(need.item))
      .filter(Boolean);
    if (startDates.length) {
      const earliest = new Date(Math.min(...startDates.map((d) => d.getTime())));
      const startLine = document.createElement("p");
      startLine.className = "essay-cluster-start";
      startLine.textContent =
        earliest <= new Date()
          ? "Earliest start: now"
          : `Earliest start: ${earliest.toLocaleDateString("en-US", { month: "short", day: "numeric" })}`;
      card.appendChild(startLine);
    }
```

(place after the existing `meta` append, before the `list` append).

(c) In `buildApplicationChecklist`, locate the loop that renders each requirement row (below the `updateProgress` definition; each requirement renders a label + checkbox). After the row's label element is appended, add:

```javascript
    const promptBlock = buildPromptBlock(requirement);
    if (promptBlock) row.appendChild(promptBlock);
```

(match the actual local variable names in that loop — the requirement iteration variable and the row container.)

(d) In `buildDeadlineTimeline`, after `copy.appendChild(detail);` (~line 2791), add:

```javascript
    const startBy = essayStartByLabel(item);
    if (startBy) {
      const startLine = document.createElement("p");
      startLine.className = "timeline-start-by";
      startLine.textContent = startBy;
      copy.appendChild(startLine);
    }
```

- [ ] **Step 4: Add CSS**

Append to `app/static/css/style.css` (use existing custom properties; no new colors beyond tokens):

```css
/* Essay prompts + start-by */
.prompt-details { margin-top: 0.4rem; font-size: 0.78rem; }
.prompt-details summary { cursor: pointer; color: var(--ink-soft); font-weight: 600; }
.prompt-list { margin: 0.4rem 0 0 1rem; display: grid; gap: 0.35rem; color: var(--ink-soft); }
.prompt-length { font-family: "Space Mono", monospace; font-size: 0.68rem; color: var(--muted); border: 1px solid var(--line); border-radius: var(--radius-sm); padding: 0 0.35rem; white-space: nowrap; }
.prompt-gated { margin-top: 0.35rem; font-size: 0.74rem; color: var(--muted); }
.timeline-start-by { margin-top: 0.2rem; font-size: 0.74rem; font-weight: 600; color: var(--amber-strong); }
.essay-cluster-start { font-size: 0.74rem; font-weight: 600; color: var(--amber-strong); }
```

Check `var(--amber-strong)`, `var(--line)`, `var(--radius-sm)`, `var(--ink-soft)`, `var(--muted)` all exist in style.css (they are used elsewhere, e.g. `.plan-table td.has-work`); substitute the file's actual token names if any differ.

- [ ] **Step 5: Bump asset versions**

- `app/static/index.html`: `style.css?v=20260710-3` and `app.js?v=20260710-3`
- `app/templates/base.html` line 20: `style.css?v=20260710-3`
- `tests/test_pages.py` lines 87-88: update both assertions to `20260710-3`.

- [ ] **Step 6: Run full suite**

Run: `.venv\Scripts\python.exe -m pytest tests/ -q`
Expected: all pass.

- [ ] **Step 7: Browser-verify (required)**

Start the app (`.venv\Scripts\python.exe -m uvicorn app.main:app --port 8099`), log in with a dev account with saved essay-bearing items, and confirm: reuse map items show collapsed prompt expanders only for steps with data (none yet — temporarily hand-edit one entry in `app/data/scholarships.json` to carry an `essay_prompts` block, restart, verify, then revert); timeline rows show "Start drafting by ..." for essay-bearing saved items; nothing renders for items without deadlines. Kill the server after.

- [ ] **Step 8: Commit**

```bash
git add app/static/js/app.js app/static/css/style.css app/static/index.html app/templates/base.html tests/
git commit -m "Render essay prompts and start-by dates in plan surfaces"
```

---

### Task 3: Essay guide pages

**Files:**
- Create: `app/guide_pages.py`, `app/data/essay_guides.json`, `app/templates/guide.html`, `app/templates/guides_index.html`
- Modify: `app/main.py` (router include + sitemap), `app/static/js/app.js` (cluster guide link), `app/templates/base.html` (footer link), `app/static/index.html` (footer link + asset bump `20260710-4`), `app/static/css/style.css` (guide styles)
- Create: `tests/test_guide_pages.py`; Modify: `tests/test_pages.py` (asset assertions)

**Interfaces:**
- Consumes: `render_page` and `public_base_url` from `app/seo_pages.py`.
- Produces: `guides_router` (APIRouter) and `GUIDE_THEME_KEYS: list[str]` exported from `app/guide_pages.py`; routes `/guides/essays` and `/guides/essays/{theme}`. `app/main.py` imports both. Theme keys MUST equal the reuse map's `WRITING_REUSE_GROUPS` keys: `identity`, `why-fit`, `leadership-service`, `academic-research`, `general-writing`.

- [ ] **Step 1: Write failing route tests**

Create `tests/test_guide_pages.py`:

```python
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

THEME_KEYS = ["identity", "why-fit", "leadership-service", "academic-research", "general-writing"]


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


class TestGuidePages:
    def test_index_lists_all_themes(self, client):
        response = client.get("/guides/essays")
        assert response.status_code == 200
        for key in THEME_KEYS:
            assert f"/guides/essays/{key}" in response.text

    @pytest.mark.parametrize("key", THEME_KEYS)
    def test_each_theme_page_renders(self, client, key):
        response = client.get(f"/guides/essays/{key}")
        assert response.status_code == 200
        assert "Example essays" in response.text
        assert 'rel="noopener noreferrer"' in response.text
        assert response.headers["Cache-Control"].startswith("public, s-maxage=86400")

    def test_unknown_theme_404s(self, client):
        assert client.get("/guides/essays/nonexistent").status_code == 404

    def test_sitemap_includes_guides(self, client):
        text = client.get("/sitemap.xml").text
        assert "<loc>http://testserver/guides/essays</loc>" in text
        for key in THEME_KEYS:
            assert f"<loc>http://testserver/guides/essays/{key}</loc>" in text

    def test_guide_content_structure(self):
        data = json.loads(
            (Path(__file__).resolve().parent.parent / "app" / "data" / "essay_guides.json").read_text(encoding="utf-8")
        )
        assert [theme["key"] for theme in data["themes"]] == THEME_KEYS
        for theme in data["themes"]:
            assert theme["title"] and theme["intro"]
            assert len(theme["steps"]) >= 3
            assert len(theme["links"]) >= 2
            for link in theme["links"]:
                assert link["url"].startswith("https://")
                assert link["title"] and link["source"]
```

Run: `.venv\Scripts\python.exe -m pytest tests/test_guide_pages.py -q` — expected: all FAIL (404s / missing file).

- [ ] **Step 2: Write the guide content**

Create `app/data/essay_guides.json`. Full content (implementer: verify every URL returns 200 in a browser before committing; replace any dead link with another reputable published collection):

```json
{
  "themes": [
    {
      "key": "identity",
      "title": "Identity, community, and lived experience essays",
      "intro": "These prompts ask who you are and what shaped you. The strongest answers zoom in on one specific story instead of summarizing a whole life.",
      "steps": [
        "Pick one moment or place, not a montage: a shift at your job, one conversation, one room in your house.",
        "Show the before and after: what did you believe or do differently because of it?",
        "Connect it forward: one sentence on how this shapes what you want to do next is enough.",
        "Read it aloud. If a sentence could appear in anyone else's essay, cut or sharpen it."
      ],
      "dos": ["Use concrete detail (names, sounds, objects)", "Keep the timeline tight", "Let discomfort stay in the story"],
      "donts": ["Open with a dictionary definition", "List every activity you do", "Claim a lesson the story does not show"],
      "links": [
        {"title": "Essays That Worked", "url": "https://apply.jhu.edu/application-process/essays-that-worked/", "source": "Johns Hopkins Admissions"},
        {"title": "College essay examples with analysis", "url": "https://www.collegeessayguy.com/blog/college-essay-examples", "source": "College Essay Guy"}
      ]
    },
    {
      "key": "why-fit",
      "title": "\"Why this program or scholarship\" essays",
      "intro": "Sponsors ask this to filter out copy-paste applicants. Specificity is the entire game: name the parts of the program only a real reader of their site would know.",
      "steps": [
        "Spend 15 minutes on the sponsor's site and write down three specifics: a course, a value in their mission statement, a past winner's project.",
        "Tie each specific to something you have already done, not just something you want.",
        "Answer the mirror question too: what do you bring them?",
        "Swap test: if you could replace the program name with a rival's and the essay still works, it is not specific enough."
      ],
      "dos": ["Name specific courses, mentors, or program features", "Show you know what the sponsor values", "Keep one paragraph about them, one about you, one about the fit"],
      "donts": ["Praise prestige or rankings", "Reuse this essay without re-tailoring the specifics", "Write more about your general goals than about the fit"],
      "links": [
        {"title": "Why us essay guide with examples", "url": "https://www.collegeessayguy.com/blog/why-us-college-essay", "source": "College Essay Guy"},
        {"title": "Applying to college: essays", "url": "https://www.khanacademy.org/college-careers-more/college-admissions/applying-to-college", "source": "Khan Academy"}
      ]
    },
    {
      "key": "leadership-service",
      "title": "Leadership, service, and impact essays",
      "intro": "The prompt says leadership; the reader wants evidence of initiative and effect on other people. Titles are optional, outcomes are not.",
      "steps": [
        "Choose the story where something changed because you acted, even if you held no title.",
        "Quantify what you honestly can (people, hours, dollars) and describe what you cannot.",
        "Give the setback one sentence: what went wrong and what you adjusted reads as maturity.",
        "End on the people affected, not on yourself."
      ],
      "dos": ["Show initiative you took without being asked", "Credit the team while owning your part", "Use one number that makes scale real"],
      "donts": ["Equate a position with impact", "Inflate numbers", "Make the conclusion about your own growth only"],
      "links": [
        {"title": "Essays That Worked", "url": "https://apply.jhu.edu/application-process/essays-that-worked/", "source": "Johns Hopkins Admissions"},
        {"title": "Extracurricular activity essay examples", "url": "https://www.collegeessayguy.com/blog/extracurricular-activity-examples", "source": "College Essay Guy"}
      ]
    },
    {
      "key": "academic-research",
      "title": "Academic interest, research, and problem-solving essays",
      "intro": "These prompts test whether your interest survives contact with detail. Write about the question that hooked you, not the field's importance in general.",
      "steps": [
        "Start from a specific question or problem you could not let go of, stated plainly.",
        "Trace what you actually did about it: a project, a course you sought out, something you built or measured.",
        "Include one moment of being wrong or stuck; real inquiry has friction.",
        "Point at the edge: what do you not know yet that this program or award would let you pursue?"
      ],
      "dos": ["Define one technical idea simply enough for any reader", "Show self-directed work", "Name what you want to learn next"],
      "donts": ["Recite the syllabus of your interest", "Hide behind jargon", "Claim certainty about a career at 17"],
      "links": [
        {"title": "Applying to college: essays", "url": "https://www.khanacademy.org/college-careers-more/college-admissions/applying-to-college", "source": "Khan Academy"},
        {"title": "College essay examples with analysis", "url": "https://www.collegeessayguy.com/blog/college-essay-examples", "source": "College Essay Guy"}
      ]
    },
    {
      "key": "general-writing",
      "title": "General essays and short answers",
      "intro": "Catch-all prompts and short answers reward the same base draft, carefully tailored. Draft once at full length, then cut to each word limit without losing the one idea that is yours.",
      "steps": [
        "Write the 650-word version of your core story first, even if every target is shorter.",
        "Cut by removing whole ideas, not adjectives: a 250-word answer holds one idea well.",
        "Answer the literal prompt in the first two sentences; readers skim.",
        "Track versions per sponsor so you never send the wrong tailoring."
      ],
      "dos": ["Keep one master draft per theme", "Re-read the exact prompt before every submission", "Respect word limits exactly"],
      "donts": ["Pad short answers to hit the limit", "Send an essay that answers a different sponsor's prompt", "Recycle without re-reading"],
      "links": [
        {"title": "Common App essay prompts", "url": "https://www.commonapp.org/apply/essay-prompts", "source": "Common App"},
        {"title": "College essay examples with analysis", "url": "https://www.collegeessayguy.com/blog/college-essay-examples", "source": "College Essay Guy"}
      ]
    }
  ]
}
```

- [ ] **Step 3: Implement `app/guide_pages.py`**

```python
"""Server-rendered essay guide pages: /guides/essays and per-theme guides.

Static editorial content from app/data/essay_guides.json; same caching and
rendering pattern as the SEO pages. No AI involved anywhere.
"""

import json
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.seo_pages import render_page

guides_router = APIRouter()

_GUIDES_PATH = Path(__file__).parent / "data" / "essay_guides.json"
_GUIDES = json.loads(_GUIDES_PATH.read_text(encoding="utf-8"))["themes"]
_GUIDES_BY_KEY = {theme["key"]: theme for theme in _GUIDES}
GUIDE_THEME_KEYS = [theme["key"] for theme in _GUIDES]


@guides_router.get("/guides/essays", response_class=HTMLResponse)
def guides_index(request: Request) -> HTMLResponse:
    return render_page(
        request,
        "guides_index.html",
        page_title="Scholarship and program essay guides | EnsureCollege",
        meta_description="Practical guides for the five kinds of essays scholarships, summer programs, and competitions actually ask for, with linked example essays.",
        themes=_GUIDES,
    )


@guides_router.get("/guides/essays/{theme_key}", response_class=HTMLResponse)
def guide_detail(theme_key: str, request: Request) -> HTMLResponse:
    theme = _GUIDES_BY_KEY.get(theme_key)
    if theme is None:
        return render_page(request, "404.html", status_code=404, page_title="Not found | EnsureCollege")
    return render_page(
        request,
        "guide.html",
        page_title=f"{theme['title']} | EnsureCollege",
        meta_description=theme["intro"][:155],
        theme=theme,
    )
```

- [ ] **Step 4: Create the templates**

`app/templates/guides_index.html`:

```html
{% extends "base.html" %}
{% block content %}
  <section class="results-header">
    <p class="eyebrow">Essay guides</p>
    <h2>Write once, tailor carefully</h2>
    <p class="results-summary">Five short guides for the kinds of writing scholarships, summer programs, and competitions actually ask for.</p>
  </section>
  <ul class="browse-list panel">
    {% for theme in themes %}
    <li class="browse-row">
      <a href="/guides/essays/{{ theme.key }}">{{ theme.title }}</a>
      <span class="browse-row-meta">{{ theme.intro }}</span>
    </li>
    {% endfor %}
  </ul>
{% endblock %}
```

`app/templates/guide.html`:

```html
{% extends "base.html" %}
{% block content %}
  <nav class="detail-breadcrumb" aria-label="Breadcrumb">
    <a href="/guides/essays">Essay guides</a> <span aria-hidden="true">›</span> <span>{{ theme.title }}</span>
  </nav>
  <section class="results-header">
    <p class="eyebrow">Essay guide</p>
    <h2>{{ theme.title }}</h2>
    <p class="results-summary">{{ theme.intro }}</p>
  </section>
  <section class="detail-section panel guide-body">
    <h3>How to approach it</h3>
    <ol class="guide-steps">
      {% for step in theme.steps %}<li>{{ step }}</li>{% endfor %}
    </ol>
    <div class="guide-dos-donts">
      <div><h4>Do</h4><ul>{% for item in theme.dos %}<li>{{ item }}</li>{% endfor %}</ul></div>
      <div><h4>Avoid</h4><ul>{% for item in theme.donts %}<li>{{ item }}</li>{% endfor %}</ul></div>
    </div>
    <h3>Example essays</h3>
    <p class="guide-links-note">Real published collections, not our own writing. Read a few before drafting; notice how specific they get.</p>
    <ul class="guide-links">
      {% for link in theme.links %}
      <li><a href="{{ link.url }}" target="_blank" rel="noopener noreferrer">{{ link.title }}</a> <span class="browse-row-meta">{{ link.source }}</span></li>
      {% endfor %}
    </ul>
    <p class="guide-back"><a href="/browse">Browse opportunities</a> · <a href="/#profile-form">Find your matches</a></p>
  </section>
{% endblock %}
```

- [ ] **Step 5: Wire into main.py**

In `app/main.py`, next to the existing `seo_router` include, add:

```python
from app.guide_pages import GUIDE_THEME_KEYS, guides_router
app.include_router(guides_router)
```

In `sitemap_xml` (line ~258), after `paths: list[str] = list(_SITEMAP_PATHS) + ["/browse"]`, add:

```python
    paths.append("/guides/essays")
    paths.extend(f"/guides/essays/{key}" for key in GUIDE_THEME_KEYS)
```

- [ ] **Step 6: Cross-links + styles + asset bump**

(a) `app/static/js/app.js`, in `buildEssayReuseMap`, after the cluster `list` is appended to `card`, add one guide link per cluster (`cluster.group.key` matches the route slugs):

```javascript
    const guideLink = document.createElement("a");
    guideLink.className = "essay-guide-link";
    guideLink.href = `/guides/essays/${cluster.group.key}`;
    guideLink.textContent = "How to write this kind of essay";
    card.appendChild(guideLink);
```

(b) Footer links: in `app/templates/base.html` and the footer of `app/static/index.html`, add `<a href="/guides/essays">Essay guides</a>` alongside the existing Browse/Privacy/Terms links (match surrounding markup and separators).

(c) Append to `app/static/css/style.css`:

```css
/* Essay guide pages */
.guide-body { display: grid; gap: 1rem; }
.guide-steps { margin-left: 1.1rem; display: grid; gap: 0.5rem; color: var(--ink-soft); }
.guide-dos-donts { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; }
.guide-dos-donts ul { margin-left: 1.1rem; display: grid; gap: 0.3rem; color: var(--ink-soft); }
.guide-links { display: grid; gap: 0.45rem; }
.guide-links-note { color: var(--muted); font-size: 0.85rem; }
.essay-guide-link { display: inline-block; margin-top: 0.5rem; font-size: 0.78rem; font-weight: 600; }
```

(d) Bump assets to `20260710-4` in `app/static/index.html` (both) and `app/templates/base.html` (style), update `tests/test_pages.py` assertions.

- [ ] **Step 7: Verify links live, run suite, browser-check**

- Open each of the 5 distinct URLs in `essay_guides.json` and confirm they load (replace dead ones and rerun).
- Run: `.venv\Scripts\python.exe -m pytest tests/ -q` — expected: all pass.
- Browser: `/guides/essays` renders, one theme page renders correctly at mobile width, reuse map clusters show the guide link.

- [ ] **Step 8: Commit**

```bash
git add app/guide_pages.py app/data/essay_guides.json app/templates/ app/main.py app/static/ tests/
git commit -m "Add public essay guide pages with curated example links"
```

---

### Task 4: Auto-match on session restore

**Files:**
- Modify: `app/static/js/app.js` (`handleSubmit` ~line 4020, `loadSession` ~line 1752, auth submit handler ~line 1718-1724)
- Modify: `app/static/index.html` + `app/templates/base.html` (asset bump `20260710-5`), `tests/test_pages.py`, `tests/test_essay_prompts.py` (source smoke)

**Interfaces:**
- Consumes: `buildProfile()` (returns `{profile}` or `{error}`), `loadProfileIntoForm()`, `setLoading`, `renderResults`, `loadPrograms`, `loadCompetitions`, `activateOpportunityView`, `updateOpportunityTabCounts` — all existing.
- Produces: `async function runMatchFlow(profile)` (shared core) and `async function autoMatchFromSavedProfile()` (silent path).

- [ ] **Step 1: Write failing source smoke test**

Append to `tests/test_essay_prompts.py` `TestFrontendPromptWiring`:

```python
    def test_app_js_wires_auto_match(self):
        source = APP_JS.read_text(encoding="utf-8")
        assert "function runMatchFlow" in source
        assert "function autoMatchFromSavedProfile" in source
        assert source.count("autoMatchFromSavedProfile()") >= 2  # loadSession + login
```

Run: `.venv\Scripts\python.exe -m pytest tests/test_essay_prompts.py -q` — expected: 1 failure.

- [ ] **Step 2: Extract the shared match core**

In `app/static/js/app.js`, refactor `handleSubmit` so the fetch/render body lives in a shared function. Replace the current `handleSubmit` (lines 4020-4073) with:

```javascript
async function runMatchFlow(profile) {
  const response = await fetch("/match", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });
  if (response.status === 422) {
    const data = await response.json();
    const err = new Error("validation");
    err.validationDetail = data.detail;
    throw err;
  }
  if (!response.ok) {
    throw new Error(`Match request failed (${response.status})`);
  }
  const payload = await response.json();
  lastSubmittedProfile = profile;
  lastResults = payload.matches;
  lastNearMisses.scholarships = payload.near_misses || [];
  renderResults(lastResults);
  updateOpportunityTabCounts();
  await activateOpportunityView("scholarships");
  loadPrograms(profile);
  loadCompetitions(profile);
}

async function handleSubmit(event) {
  event.preventDefault();
  hideFormError();

  const built = buildProfile();
  if (built.error) {
    showFormError(built.error);
    return;
  }

  resultsSection.hidden = false;
  programsSection.hidden = true;
  competitionsSection.hidden = true;
  savedSection.hidden = true;
  setOpportunityTabsVisible(false);
  setLoading(true);

  try {
    await runMatchFlow(built.profile);
    saveProfileSilently(built.profile);
  } catch (err) {
    if (err.validationDetail) {
      showFormError(formatValidationErrors(err.validationDetail));
    } else {
      showFormError(
        "The match request did not go through. Check your connection and try again."
      );
      console.error(err);
    }
  } finally {
    setLoading(false);
  }
}

async function autoMatchFromSavedProfile() {
  if (!currentUser || lastResults) {
    return;
  }
  const built = buildProfile();
  if (built.error) {
    return; // incomplete saved profile: keep today's behavior silently
  }
  resultsSection.hidden = false;
  programsSection.hidden = true;
  competitionsSection.hidden = true;
  savedSection.hidden = true;
  setOpportunityTabsVisible(false);
  setLoading(true);
  try {
    await runMatchFlow(built.profile);
  } catch (err) {
    console.error(err);
    resultsSection.hidden = true; // degrade to pre-match state, no toast
  } finally {
    setLoading(false);
  }
}
```

Behavior notes preserved from the original: `saveProfileSilently` runs ONLY on manual submit (auto path matches an already-saved profile); auto path never calls `showFormError`.

- [ ] **Step 3: Call it from both session paths**

(a) In `loadSession` (~line 1758), after `await Promise.all([loadProfileIntoForm(), loadSaved()]);` add:

```javascript
      await autoMatchFromSavedProfile();
```

(b) In the auth submit handler (~line 1721), after its `await Promise.all([loadProfileIntoForm(), loadSaved()]);` and before the existing `if (lastResults)` re-render, add:

```javascript
    await autoMatchFromSavedProfile();
```

- [ ] **Step 4: Bump assets + run suite**

Assets to `20260710-5` in `app/static/index.html` (both refs) and `app/templates/base.html`; update `tests/test_pages.py`. Run: `.venv\Scripts\python.exe -m pytest tests/ -q` — all pass.

- [ ] **Step 5: Browser-verify (required)**

Start the dev server. With a dev account that has a complete saved profile: reload the page → lanes populate through skeletons without pressing match, no scroll jump, no error toast. With a fresh account (no profile): reload → form behavior unchanged. Manual re-match with edited values still works. Log out → no auto-match. Kill the server.

- [ ] **Step 6: Commit**

```bash
git add app/static/js/app.js app/static/index.html app/templates/base.html tests/
git commit -m "Auto-run match for returning users with a complete saved profile"
```

---

### Task 5: Prompt verification data pass (run LAST)

**Files:**
- Modify: `app/data/scholarships.json`, `app/data/summer_programs.json`, `app/data/competitions.json` (add `essay_prompts` blocks only)

This is a data task, not a code task. The UI from Tasks 1-2 renders absent data gracefully, so results can land incrementally.

- [ ] **Step 1: Build the target list**

Run from repo root:

```python
.venv\Scripts\python.exe -c "
import json, re
pat = re.compile(r'essay|short answer|short-answer|response|statement|writing|problem set|solutions', re.I)
for fname, key in [('scholarships.json','scholarships'),('summer_programs.json','programs'),('competitions.json','competitions')]:
    data = json.load(open(f'app/data/{fname}', encoding='utf-8'))
    entries = data if isinstance(data, list) else data.get(key, data)
    for e in entries:
        hits = [r['id'] for r in (e.get('application_requirements') or []) if pat.search((r.get('label','') + ' ' + str(r.get('details','') or '')))]
        if hits:
            print(f\"{fname[:-5]}\t{e['id']}\t{','.join(hits)}\")
"
```

Expected: roughly 40-60 lines (entry id + requirement ids to enrich).

- [ ] **Step 2: Dispatch verification subagents (Sonnet, not Opus/Fable)**

Batch the target list into groups of ~10 entries. Each subagent gets these rules verbatim:

> For each entry, open the requirement's `source_url` (or the entry's official application page). If the official page shows the essay/short-answer prompts publicly, add to that requirement:
> `"essay_prompts": {"status": "public", "items": [{"prompt": "<exact official wording>", "length": "<sponsor's exact length wording, omit if none>"}]}`
> If the page makes clear prompts exist but only appear inside the application portal, add `"essay_prompts": {"status": "gated", "items": []}`.
> If the page is dead, ambiguous, or you cannot verify: change NOTHING for that requirement. Never paraphrase, never summarize, never invent lengths. Do not modify any other fields.

- [ ] **Step 3: Validate + test after each batch**

```bash
.venv\Scripts\python.exe scripts/validate_dataset.py
.venv\Scripts\python.exe -m pytest tests/ -q
```

Expected: validator clean (Pydantic enforces the shape at load), all tests pass.

- [ ] **Step 4: Spot-check and commit per batch**

Manually diff-review each batch (prompt text reads like official wording, no invented lengths, gated entries have empty items), then:

```bash
git add app/data/
git commit -m "Add verified essay prompts: batch N (X public, Y gated)"
```

- [ ] **Step 5: Deploy check**

After the final batch merges and deploys, open one enriched entry's public detail page on ensurecollege.com and its reuse-map rendering with a saved item, confirming prompts render in production.

---

## Self-Review Notes

- Spec coverage: data model + pass (Tasks 1, 5), three display surfaces (Tasks 1, 2), start-by dates (Task 2), guide pages + cross-links + sitemap + footer (Task 3), auto-match incl. completeness rule and silent failure (Task 4), anti-overwhelm rules embedded in Global Constraints. Error handling: model validation (T1), silent auto-match degrade (T4), 404 on unknown theme (T3).
- Known judgment points for implementers: exact local variable names inside `buildApplicationChecklist`'s render loop (step marked accordingly), the estimated-deadline accessor in app.js (Task 2 step 2 note), and CSS token names (verify before use). Everything else is verbatim.
