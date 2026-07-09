"""Server-rendered SEO pages: opportunity details, browse directories.

These pages are the crawlable surface of the catalog. They render from the
in-memory app.state lists (loaded at startup), carry the same verification
labeling the app uses, and are edge-cached (data changes only at deploy).
"""

import json
import os
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

seo_router = APIRouter()

SEO_CACHE_CONTROL = "public, s-maxage=86400, stale-while-revalidate=604800"

_env = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=select_autoescape(("html",)),
)

KINDS = {
    "scholarships": {
        "plural": "scholarships",
        "label_singular": "Scholarship",
        "label_plural": "Scholarships",
        "award_label": "Award",
        "state_dict": "scholarships_by_id",
        "state_list": "scholarships",
        "org_attr": "sponsor",
    },
    "programs": {
        "plural": "programs",
        "label_singular": "Summer program",
        "label_plural": "Summer programs",
        "award_label": "Cost",
        "state_dict": "programs_by_id",
        "state_list": "programs",
        "org_attr": "host",
    },
    "competitions": {
        "plural": "competitions",
        "label_singular": "Competition",
        "label_plural": "Competitions",
        "award_label": "Recognition",
        "state_dict": "competitions_by_id",
        "state_list": "competitions",
        "org_attr": "host",
    },
}


def public_base_url(request: Request) -> str:
    env = os.getenv("PUBLIC_APP_URL", "").strip().rstrip("/")
    return env or str(request.base_url).rstrip("/")


def render_page(request: Request, template: str, status_code: int = 200, **context) -> HTMLResponse:
    context.setdefault("base_url", public_base_url(request))
    context.setdefault("page_title", "EnsureCollege")
    context.setdefault("meta_description", "Scholarships, summer programs, and competitions with source-linked details.")
    context.setdefault("canonical", context["base_url"] + request.url.path)
    html = _env.get_template(template).render(**context)
    return HTMLResponse(html, status_code=status_code, headers={"Cache-Control": SEO_CACHE_CONTROL})


def _format_date(iso: str) -> str:
    try:
        return date.fromisoformat(iso).strftime("%b %-d, %Y") if os.name != "nt" else date.fromisoformat(iso).strftime("%b %d, %Y").replace(" 0", " ")
    except ValueError:
        return iso


def _award_text(kind_key: str, entry) -> str:
    if kind_key == "scholarships":
        amount = entry.award_amount
        if isinstance(amount, (int, float)):
            return f"${amount:,.0f}"
        return str(amount)
    if kind_key == "programs":
        return str(entry.cost) if entry.cost else ""
    return str(entry.recognition) if getattr(entry, "recognition", None) else ""


def _deadline_parts(entry) -> tuple[str, str]:
    """Return (value, note). Estimated/unverified deadlines carry the site's labeling."""
    deadline = getattr(entry, "deadline", None)
    estimated = getattr(entry, "estimated_deadline", None)
    if deadline and deadline not in ("VERIFY", "rolling"):
        return _format_date(deadline), ""
    if deadline == "rolling":
        return "Rolling", ""
    if estimated:
        return f"~{_format_date(estimated)}", "Estimated; confirm on sponsor site"
    return "See sponsor site", "Not yet published; confirm on sponsor site"


_HUMANIZE_WORD_MAP = {
    "us": "U.S.",
    "daca": "DACA",
    "esa": "ESA",
}


def _humanize(token: str) -> str:
    """Turn a snake_case token into human-readable text.

    Freeform prose values (containing a space or a period) are already
    human-written and are returned unchanged. Snake_case tokens are split on
    "_"; recognized acronym/abbreviation words are mapped case-insensitively
    (e.g. "us" -> "U.S."), and only the first word that isn't specially
    mapped gets capitalized so results like "us_citizen" -> "U.S. citizen"
    read naturally instead of "U.S. Citizen".
    """
    if " " in token or "." in token:
        return token
    words = token.split("_")
    result = []
    for i, word in enumerate(words):
        lower = word.lower()
        if lower in _HUMANIZE_WORD_MAP:
            result.append(_HUMANIZE_WORD_MAP[lower])
        elif i == 0:
            result.append(word.capitalize())
        else:
            result.append(lower)
    return " ".join(result)


def _eligibility_rows(entry) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    elig = getattr(entry, "eligibility", None)
    if elig is None:
        return rows
    if getattr(elig, "grade_levels", None):
        rows.append(("Grade levels", ", ".join(_humanize(g) for g in elig.grade_levels)))
    citizenship = getattr(elig, "citizenship_requirement", None)
    if citizenship and citizenship != "VERIFY":
        rows.append(("Citizenship", _humanize(citizenship)))
    min_gpa = getattr(elig, "min_gpa", None)
    if isinstance(min_gpa, (int, float)):
        rows.append(("Minimum GPA", f"{min_gpa:g}"))
    if getattr(elig, "fields_of_study", None):
        rows.append(("Fields of study", ", ".join(_humanize(f) for f in elig.fields_of_study)))
    states = getattr(elig, "states", "any")
    if isinstance(states, list) and states:
        rows.append(("States", ", ".join(states)))
    if getattr(elig, "essay_required", False):
        rows.append(("Essay", "Required"))
    return rows


def _jsonld(kind_key: str, entry, canonical: str) -> str:
    data: dict = {
        "@context": "https://schema.org",
        "name": entry.name,
        "description": entry.description,
        "url": canonical,
    }
    if kind_key == "scholarships":
        data["@type"] = "MonetaryGrant"
        data["funder"] = {"@type": "Organization", "name": entry.sponsor}
        if isinstance(entry.award_amount, (int, float)):
            data["amount"] = {"@type": "MonetaryAmount", "currency": "USD", "value": entry.award_amount}
    elif kind_key == "programs":
        data["@type"] = "EducationalOccupationalProgram"
        data["provider"] = {"@type": "Organization", "name": entry.host}
    else:
        # Competition dates are freeform strings in the dataset, so no honest
        # Event markup is possible; plain WebPage claims nothing false.
        data["@type"] = "WebPage"
    # json.dumps does not escape "</"; embedding the raw result inside a
    # <script> tag (see detail.html) would let a "</script>" in entry.name or
    # entry.description close the JSON-LD block early and let an attacker-
    # controlled "<script>...</script>" that follows execute for real. This
    # is a valid JSON escape (JSON permits "\/") so it changes no semantics.
    return json.dumps(data).replace("</", "<\\/")


def detail_context(kind_key: str, entry, request: Request) -> dict:
    kind = KINDS[kind_key]
    base = public_base_url(request)
    canonical = f"{base}/{kind_key}/{entry.id}"
    award = _award_text(kind_key, entry)
    deadline_text, deadline_note = _deadline_parts(entry)
    verification = getattr(entry, "verification", None)
    verified_line = ""
    source_url = ""
    if entry.verified and verification and verification.last_verified_at:
        verified_line = f"Verified {_format_date(verification.last_verified_at.isoformat())}"
    if verification:
        source_url = str(verification.source_url)
    # Award belongs in the title only for scholarships ("$20,000 scholarship");
    # a program's cost or a competition's prize in that slot would misread as a grant.
    if kind_key == "scholarships" and award:
        title_award = f": {award} scholarship"
    else:
        title_award = f": {kind['label_singular'].lower()}"
    return {
        "page_title": f"{entry.name}{title_award} | EnsureCollege",
        "meta_description": (entry.description[:152] + "...") if len(entry.description) > 155 else entry.description,
        "canonical": canonical,
        "kind": kind,
        "entry": entry,
        "org": getattr(entry, kind["org_attr"]),
        "award_text": award,
        "deadline_text": deadline_text,
        "deadline_note": deadline_note,
        "eligibility_rows": _eligibility_rows(entry),
        "requirements": list(getattr(entry, "application_requirements", []) or []),
        "verified_line": verified_line,
        "source_url": source_url,
        "jsonld": _jsonld(kind_key, entry, canonical),
    }


def _detail_response(kind_key: str, slug: str, request: Request) -> HTMLResponse:
    entries = getattr(request.app.state, KINDS[kind_key]["state_dict"])
    entry = entries.get(slug)
    if entry is None:
        return render_page(request, "404.html", status_code=404, page_title="Not found | EnsureCollege")
    return render_page(request, "detail.html", **detail_context(kind_key, entry, request))


@seo_router.get("/scholarships/{slug}", response_class=HTMLResponse)
def scholarship_detail(slug: str, request: Request) -> HTMLResponse:
    return _detail_response("scholarships", slug, request)


@seo_router.get("/programs/{slug}", response_class=HTMLResponse)
def program_detail(slug: str, request: Request) -> HTMLResponse:
    return _detail_response("programs", slug, request)


@seo_router.get("/competitions/{slug}", response_class=HTMLResponse)
def competition_detail(slug: str, request: Request) -> HTMLResponse:
    return _detail_response("competitions", slug, request)


@seo_router.get("/browse", response_class=HTMLResponse)
def browse_index(request: Request) -> HTMLResponse:
    kinds = []
    total = 0
    for key, kind in KINDS.items():
        count = len(getattr(request.app.state, kind["state_list"]))
        total += count
        kinds.append({**kind, "count": count})
    return render_page(
        request,
        "browse_index.html",
        page_title="Browse all opportunities | EnsureCollege",
        meta_description="Every scholarship, summer program, and competition in the EnsureCollege catalog, with deadlines and official sources.",
        kinds=kinds,
        total=total,
    )


@seo_router.get("/browse/{kind_key}", response_class=HTMLResponse)
def browse_directory(kind_key: str, request: Request) -> HTMLResponse:
    kind = KINDS.get(kind_key)
    if kind is None:
        return render_page(request, "404.html", status_code=404, page_title="Not found | EnsureCollege")
    entries = getattr(request.app.state, kind["state_list"])
    rows = []
    for entry in entries:
        deadline_text, _note = _deadline_parts(entry)
        award = _award_text(kind_key, entry)
        meta = " · ".join(part for part in (award, f"deadline {deadline_text}") if part)
        rows.append({"href": f"/{kind_key}/{entry.id}", "name": entry.name, "meta": meta})
    rows.sort(key=lambda r: r["name"].lower())
    return render_page(
        request,
        "browse.html",
        page_title=f"All {kind['label_plural'].lower()} | EnsureCollege",
        meta_description=f"All {len(rows)} {kind['label_plural'].lower()} in the EnsureCollege catalog, with awards, deadlines, and official sources.",
        kind=kind,
        rows=rows,
    )
