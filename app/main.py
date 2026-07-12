import hmac
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request as StarletteRequest

from app.api.account_routes import router as account_router
from app.api.auth_routes import router as auth_router
from app.data.loader import load_competitions, load_scholarships, load_summer_programs
from app.db.database import get_db, init_db
from app.db.models import User
from app.essay.advice import (
    EssayAdviceError,
    generate_essay_advice,
    generate_essay_review,
    generate_program_advice,
)
from app.llm import AIFeatureError
from app.matching.competition_matcher import match_competitions_response
from app.matching.matcher import match_scholarships, match_scholarships_response
from app.matching.program_matcher import match_programs_response
from app.models.competition import Competition, CompetitionMatchResponse
from app.models.essay import (
    EssayAdviceRequest,
    EssayAdviceResponse,
    EssayReviewRequest,
    EssayReviewResponse,
    ProgramAdviceRequest,
    ProgramAdviceResponse,
)
from app.models.match import MatchResponse, PreviewMatchResponse
from app.models.program import ProgramMatchResponse, SummerProgram
from app.models.resume import ResumeExtractionResponse
from app.models.scholarship import Scholarship
from app.models.student import PreviewMatchRequest, StudentProfile
from app.alerts import send_new_match_alerts
from app.rate_limit import rate_limiter
from app.reminders import send_reminder_digests
from app.resume.extractor import extract_profile_from_resume
from app.vocabulary import VocabularyOption, get_vocabulary

# Cap upload size so a huge file cannot be read fully into memory or sent upstream.
MAX_RESUME_BYTES = 5 * 1024 * 1024
# Cap pasted/decoded resume text so an oversized paste cannot inflate token cost.
MAX_RESUME_TEXT = 50_000

# AI endpoints call a paid API, so they are rate limited per client IP.
_essay_limit = rate_limiter(15, 60, "essay")
_resume_limit = rate_limiter(10, 60, "resume")

load_dotenv()

STATIC_DIR = Path(__file__).parent / "static"

# A stable default keeps logins working across local restarts. In production the
# app refuses to boot with a guessable key (see _resolve_session_secret).
DEV_SESSION_SECRET = "dev-only-insecure-session-secret-change-me"

_OG_IMAGE_PATH = "/static/og-image.png"
_SITEMAP_PATHS = ("/", "/privacy", "/terms")
_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    ),
}


def is_production_deploy() -> bool:
    """True when running on Render or against a Postgres DATABASE_URL."""
    return bool(os.getenv("RENDER")) or os.getenv("DATABASE_URL", "").startswith("postgres")


def _resolve_session_secret() -> str:
    secret = os.getenv("SESSION_SECRET", "").strip()
    # A Postgres database or Render's platform variable means this is a real
    # deployment, where signing session cookies with a guessable key would let
    # anyone forge a logged-in session.
    in_production = is_production_deploy()
    if not secret or secret == DEV_SESSION_SECRET:
        if in_production:
            raise RuntimeError(
                "SESSION_SECRET must be set to a strong, unique value in production. "
                "Set it in your host's environment variables and redeploy."
            )
        return DEV_SESSION_SECRET
    return secret


SESSION_SECRET = _resolve_session_secret()
# The Secure flag must never depend on remembering an env var in production:
# default it on for real deployments, allow the env var to force it on locally.
SESSION_COOKIE_SECURE = (
    os.getenv("SESSION_COOKIE_SECURE", "").lower() in {"1", "true", "yes"}
    or is_production_deploy()
)
_DOCS_ENABLED = not is_production_deploy()

# Old domain hosts that should be permanently redirected to the new domain.
_OLD_HOSTS = {"scholarships4u.dev", "www.scholarships4u.dev"}


def _ai_features_enabled() -> bool:
    """AI-backed endpoints (essay/program advice, resume parsing) are gated off
    by default; set AI_FEATURES_ENABLED=true to serve them."""
    return os.getenv("AI_FEATURES_ENABLED", "").lower() in {"1", "true", "yes"}


def require_ai_features() -> None:
    """FastAPI dependency: hide AI routes (404) unless the feature flag is on."""
    if not _ai_features_enabled():
        raise HTTPException(
            status_code=404,
            detail={"error": "This feature is not available."},
        )


def _public_base_url(request: Request) -> str:
    env = os.getenv("PUBLIC_APP_URL", "").strip().rstrip("/")
    return env or str(request.base_url).rstrip("/")


def _absolute_og_image_urls(html: str, base_url: str) -> str:
    absolute = f"{base_url}{_OG_IMAGE_PATH}"
    return html.replace(f'content="{_OG_IMAGE_PATH}"', f'content="{absolute}"')


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        response = await call_next(request)
        for header, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        # HSTS only makes sense over HTTPS. Emit it in production so browsers
        # pin the site to HTTPS; skip it locally where the app runs over HTTP.
        if is_production_deploy():
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("RUN_MIGRATIONS_ON_STARTUP", "true").lower() not in {"0", "false", "no"}:
        init_db()
    app.state.scholarships = load_scholarships()
    app.state.programs = load_summer_programs()
    app.state.competitions = load_competitions()
    app.state.scholarships_by_id = {s.id: s for s in app.state.scholarships}
    app.state.programs_by_id = {p.id: p for p in app.state.programs}
    app.state.competitions_by_id = {c.id: c for c in app.state.competitions}
    yield


app = FastAPI(
    title="EnsureCollege",
    description="Match students to scholarships with transparent, explainable scoring.",
    lifespan=lifespan,
    docs_url="/docs" if _DOCS_ENABLED else None,
    redoc_url="/redoc" if _DOCS_ENABLED else None,
    openapi_url="/openapi.json" if _DOCS_ENABLED else None,
)


@app.middleware("http")
async def _redirect_old_domain(request: StarletteRequest, call_next):
    host = request.headers.get("host", "").split(":")[0].lower()
    if host in _OLD_HOSTS:
        target = f"https://ensurecollege.com{request.url.path}"
        if request.url.query:
            target += f"?{request.url.query}"
        return Response(status_code=301, headers={"Location": target})
    return await call_next(request)


app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=SESSION_COOKIE_SECURE,
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(account_router)

from app.seo_pages import seo_router  # noqa: E402  (import near use, matches file's route grouping)
from app.guide_pages import GUIDE_THEME_KEYS, guides_router  # noqa: E402

app.include_router(seo_router)
app.include_router(guides_router)


def _find_scholarship(scholarships: list[Scholarship], scholarship_id: str) -> Scholarship | None:
    for scholarship in scholarships:
        if scholarship.id == scholarship_id:
            return scholarship
    return None


def _find_program(programs: list[SummerProgram], program_id: str) -> SummerProgram | None:
    for program in programs:
        if program.id == program_id:
            return program
    return None


@app.get("/")
def serve_index(request: Request) -> HTMLResponse:
    # Always revalidate the HTML so the ?v cache-busting on CSS/JS stays reliable;
    # a stale cached page would keep requesting old asset versions.
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    html = _absolute_og_image_urls(html, _public_base_url(request))
    html = html.replace(
        "__AI_FEATURES_ENABLED__", "true" if _ai_features_enabled() else "false"
    )
    # Hero stats state the live catalog size so the copy never drifts from the data.
    html = html.replace("__COUNT_SCHOLARSHIPS__", str(len(request.app.state.scholarships)))
    html = html.replace("__COUNT_PROGRAMS__", str(len(request.app.state.programs)))
    html = html.replace("__COUNT_COMPETITIONS__", str(len(request.app.state.competitions)))
    return HTMLResponse(html, headers={"Cache-Control": "no-cache"})


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt(request: Request) -> PlainTextResponse:
    base = _public_base_url(request)
    return PlainTextResponse(
        f"User-agent: *\nAllow: /\nDisallow: /docs\nDisallow: /redoc\nSitemap: {base}/sitemap.xml\n",
        media_type="text/plain",
    )


@app.get("/sitemap.xml", response_class=Response)
def sitemap_xml(request: Request) -> Response:
    base = _public_base_url(request)
    paths: list[str] = list(_SITEMAP_PATHS) + ["/browse"]
    paths.append("/guides/essays")
    paths.extend(f"/guides/essays/{key}" for key in GUIDE_THEME_KEYS)
    for kind_key, attr in (
        ("scholarships", "scholarships"),
        ("programs", "programs"),
        ("competitions", "competitions"),
    ):
        paths.append(f"/browse/{kind_key}")
        for entry in getattr(request.app.state, attr):
            paths.append(f"/{kind_key}/{entry.id}")
    urls = "\n".join(
        f"  <url><loc>{base}/</loc></url>" if path == "/" else f"  <url><loc>{base}{path}</loc></url>"
        for path in paths
    )
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}\n"
        "</urlset>\n"
    )
    return Response(
        content=body,
        media_type="application/xml",
        headers={"Cache-Control": "public, s-maxage=86400, stale-while-revalidate=604800"},
    )


@app.get("/privacy")
def serve_privacy() -> FileResponse:
    return FileResponse(STATIC_DIR / "privacy.html", headers={"Cache-Control": "no-cache"})


@app.get("/terms")
def serve_terms() -> FileResponse:
    return FileResponse(STATIC_DIR / "terms.html", headers={"Cache-Control": "no-cache"})


@app.get("/health")
def health() -> dict[str, str]:
    info = {"status": "ok"}
    commit = os.getenv("VERCEL_GIT_COMMIT_SHA") or os.getenv("RENDER_GIT_COMMIT")
    if commit:
        # The host injects the deployed commit SHA; exposing it confirms which
        # build is live (handy for verifying a redeploy actually rolled out).
        info["commit"] = commit[:7]
    return info


@app.get("/vocabulary")
def vocabulary() -> dict[str, list[VocabularyOption]]:
    return get_vocabulary()


@app.get("/scholarships")
def get_scholarships(request: Request) -> list[Scholarship]:
    return request.app.state.scholarships


@app.post("/match")
def match_student(request: Request, student: StudentProfile) -> MatchResponse:
    scholarships: list[Scholarship] = request.app.state.scholarships
    return match_scholarships_response(student, scholarships)


@app.post("/match/preview")
def match_preview(request: Request, body: PreviewMatchRequest) -> PreviewMatchResponse:
    """Three-question teaser: real matcher, residency gates flagged instead of applied.

    The placeholder citizenship/state below are never consulted — the matcher
    skips those gates in preview mode — they only satisfy StudentProfile's
    required-field validation.
    """
    student = StudentProfile(
        gpa=body.gpa,
        grade_level=body.grade_level,
        intended_majors=body.intended_majors,
        citizenship="us_citizen",
        state="TX",
    )
    scholarships: list[Scholarship] = request.app.state.scholarships
    results = match_scholarships(student, scholarships, skip_residency_gates=True)
    return PreviewMatchResponse(total_matches=len(results), results=results[:3])


@app.get("/programs")
def get_programs(request: Request) -> list[SummerProgram]:
    return request.app.state.programs


@app.post("/programs/match")
def match_summer_programs(request: Request, student: StudentProfile) -> ProgramMatchResponse:
    programs: list[SummerProgram] = request.app.state.programs
    return match_programs_response(student, programs)


@app.get("/competitions")
def get_competitions(request: Request) -> list[Competition]:
    return request.app.state.competitions


@app.post("/competitions/match")
def match_competition_list(
    request: Request, student: StudentProfile
) -> CompetitionMatchResponse:
    competitions: list[Competition] = request.app.state.competitions
    return match_competitions_response(student, competitions)


@app.post(
    "/essay-advice",
    response_model=EssayAdviceResponse,
    dependencies=[Depends(require_ai_features), Depends(_essay_limit)],
)
def essay_advice(request: Request, body: EssayAdviceRequest) -> EssayAdviceResponse:
    scholarships: list[Scholarship] = request.app.state.scholarships
    scholarship = _find_scholarship(scholarships, body.scholarship_id)
    if scholarship is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "That scholarship was not found in the current dataset."},
        )

    try:
        advice_text = generate_essay_advice(body.student, scholarship)
    except EssayAdviceError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.user_message},
        ) from None

    return EssayAdviceResponse(
        scholarship_id=scholarship.id,
        scholarship_name=scholarship.name,
        advice=advice_text,
    )


@app.post(
    "/essay-review",
    response_model=EssayReviewResponse,
    dependencies=[Depends(require_ai_features), Depends(_essay_limit)],
)
def essay_review(request: Request, body: EssayReviewRequest) -> EssayReviewResponse:
    scholarships: list[Scholarship] = request.app.state.scholarships
    scholarship = _find_scholarship(scholarships, body.scholarship_id)
    if scholarship is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "That scholarship was not found in the current dataset."},
        )

    try:
        feedback_text = generate_essay_review(body.student, scholarship, body.draft)
    except EssayAdviceError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.user_message},
        ) from None

    return EssayReviewResponse(
        scholarship_id=scholarship.id,
        scholarship_name=scholarship.name,
        feedback=feedback_text,
    )


@app.post(
    "/program-advice",
    response_model=ProgramAdviceResponse,
    dependencies=[Depends(require_ai_features), Depends(_essay_limit)],
)
def program_advice(request: Request, body: ProgramAdviceRequest) -> ProgramAdviceResponse:
    programs: list[SummerProgram] = request.app.state.programs
    program = _find_program(programs, body.program_id)
    if program is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "That summer program was not found in the current dataset."},
        )

    try:
        advice_text = generate_program_advice(body.student, program)
    except EssayAdviceError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.user_message},
        ) from None

    return ProgramAdviceResponse(
        program_id=program.id,
        program_name=program.name,
        advice=advice_text,
    )


async def _read_upload_capped(upload: UploadFile, max_bytes: int) -> bytes | None:
    """Read an upload in chunks, returning None if it exceeds max_bytes.

    Reading in chunks (rather than upload.read() all at once) means a huge file
    is rejected after ~max_bytes instead of being loaded fully into memory.
    """
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await upload.read(64 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            return None
        chunks.append(chunk)
    return b"".join(chunks)


@app.post(
    "/resume/extract",
    response_model=ResumeExtractionResponse,
    dependencies=[Depends(require_ai_features), Depends(_resume_limit)],
)
async def resume_extract(
    file: UploadFile | None = File(default=None),
    text: str | None = Form(default=None),
) -> ResumeExtractionResponse:
    resume_text = (text or "").strip()[:MAX_RESUME_TEXT] or None
    pdf_bytes: bytes | None = None

    if file is not None:
        raw = await _read_upload_capped(file, MAX_RESUME_BYTES)
        if raw is None:
            raise HTTPException(
                status_code=413,
                detail={"error": "That file is too large. Use a resume under 5 MB."},
            )
        filename = (file.filename or "").lower()
        if file.content_type == "application/pdf" or filename.endswith(".pdf"):
            pdf_bytes = raw or None
        else:
            decoded = raw.decode("utf-8", errors="ignore").strip()
            resume_text = "\n".join(part for part in (resume_text, decoded) if part) or None

    if resume_text:
        resume_text = resume_text[:MAX_RESUME_TEXT]

    if pdf_bytes is None and not resume_text:
        raise HTTPException(
            status_code=400,
            detail={"error": "Upload a PDF or paste your resume text."},
        )

    try:
        return extract_profile_from_resume(resume_text=resume_text, pdf_bytes=pdf_bytes)
    except AIFeatureError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.user_message},
        ) from None


@app.get("/reminders/unsubscribe", response_class=HTMLResponse)
def reminders_unsubscribe(token: str, db: Session = Depends(get_db)) -> HTMLResponse:
    """One-click unsubscribe from deadline reminder emails (no login needed)."""
    user = None
    if token:
        user = db.query(User).filter(User.reminder_unsubscribe_token == token).first()
    if user is not None and user.reminders_enabled:
        user.reminders_enabled = False
        db.commit()
    # Always show the same confirmation, so the token is not a membership oracle.
    page = (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>Reminders off</title>"
        "<style>body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;background:#eae8e1;"
        "color:#17181c;display:grid;place-items:center;min-height:100vh;margin:0}"
        ".c{max-width:30rem;padding:2rem;background:#fbfaf7;border:1px solid #ddd9cd;border-radius:14px;text-align:center}"
        "a{color:#1b2430}</style></head><body><div class='c'>"
        "<h1>Reminders turned off</h1>"
        "<p>You won't get deadline reminder emails anymore. You can turn them back on "
        "anytime under Account settings.</p>"
        "<p><a href='/'>Back to EnsureCollege</a></p></div></body></html>"
    )
    return HTMLResponse(page)


@app.get("/reminders/run")
def reminders_run(
    request: Request,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    """Send due deadline digests. Guarded by CRON_SECRET (Vercel cron sends it as
    an Authorization: Bearer header). Disabled if CRON_SECRET is unset. GET
    because Vercel Cron issues GET requests; the per-user re-send guard makes
    repeated invocations safe."""
    secret = os.getenv("CRON_SECRET", "").strip()
    presented = (authorization or "").removeprefix("Bearer ").strip()
    if not secret or not hmac.compare_digest(presented, secret):
        raise HTTPException(status_code=404, detail={"error": "Not found."})
    scholarships = request.app.state.scholarships
    programs = request.app.state.programs
    competitions = request.app.state.competitions
    scholarship_index = {s.id: s for s in scholarships}
    program_index = {p.id: p for p in programs}
    competition_index = {c.id: c for c in competitions}
    return {
        "deadline_reminders": send_reminder_digests(
            db, scholarship_index, program_index, competition_index
        ),
        "new_match_alerts": send_new_match_alerts(db, scholarships, programs, competitions),
    }


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

