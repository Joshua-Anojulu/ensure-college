"""Server-rendered essay guide pages: /guides/essays and per-theme guides.

Static editorial content from app/data/essay_guides.json; same caching and
rendering pattern as the SEO pages. No AI involved anywhere.
"""

import json
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.seo_pages import public_base_url, render_page

guides_router = APIRouter()

_GUIDES_PATH = Path(__file__).parent / "data" / "essay_guides.json"
_GUIDES = json.loads(_GUIDES_PATH.read_text(encoding="utf-8"))["themes"]
_GUIDES_BY_KEY = {theme["key"]: theme for theme in _GUIDES}
GUIDE_THEME_KEYS = [theme["key"] for theme in _GUIDES]


def _jsonld(name: str, description: str, canonical: str) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": name,
        "description": description,
        "url": canonical,
    }
    # json.dumps does not escape "</"; embedding the raw result inside a
    # <script> tag (see guide.html / guides_index.html) would let a
    # "</script>" in name/description close the JSON-LD block early. See
    # app/seo_pages.py:_jsonld for the same escape and full rationale.
    return json.dumps(data).replace("</", "<\\/")


@guides_router.get("/guides/essays", response_class=HTMLResponse)
def guides_index(request: Request) -> HTMLResponse:
    page_title = "Scholarship and program essay guides | EnsureCollege"
    meta_description = "Practical guides for the five kinds of essays scholarships, summer programs, and competitions actually ask for, with linked example essays."
    canonical = f"{public_base_url(request)}/guides/essays"
    return render_page(
        request,
        "guides_index.html",
        page_title=page_title,
        meta_description=meta_description,
        themes=_GUIDES,
        jsonld=_jsonld(page_title, meta_description, canonical),
    )


@guides_router.get("/guides/essays/{theme_key}", response_class=HTMLResponse)
def guide_detail(theme_key: str, request: Request) -> HTMLResponse:
    theme = _GUIDES_BY_KEY.get(theme_key)
    if theme is None:
        return render_page(request, "404.html", status_code=404, page_title="Not found | EnsureCollege")
    page_title = f"{theme['title']} | EnsureCollege"
    intro = theme["intro"]
    meta_description = (intro[:152] + "...") if len(intro) > 155 else intro
    canonical = f"{public_base_url(request)}/guides/essays/{theme_key}"
    return render_page(
        request,
        "guide.html",
        page_title=page_title,
        meta_description=meta_description,
        theme=theme,
        jsonld=_jsonld(page_title, meta_description, canonical),
    )
