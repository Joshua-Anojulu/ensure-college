"""Audit app/data/scholarships.json and app/data/summer_programs.json.

Run:  python scripts/validate_dataset.py

Exits non-zero if any structural errors are found (duplicate ids, unparseable
deadlines, out-of-range GPA). Warnings (such as VERIFY placeholders or tags
outside the canonical vocabulary) are reported but do not fail, because
unverified data is an expected state for this curated seed set.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

# Allow running as a plain script: python scripts/validate_dataset.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.data.loader import load_competitions, load_scholarships, load_summer_programs  # noqa: E402
from app.matching.matcher import _parse_iso_deadline  # noqa: E402
from app.models.competition import Competition  # noqa: E402
from app.models.program import SummerProgram  # noqa: E402
from app.models.scholarship import Scholarship  # noqa: E402
from app.vocabulary import (  # noqa: E402
    DEMOGRAPHIC_TAG_VALUES,
    FIELD_OF_STUDY_VALUES,
    GRADE_LEVEL_VALUES,
    STATE_CODE_VALUES,
)


def _deadline_ok(deadline: str) -> bool:
    if deadline == "rolling" or deadline.startswith("VERIFY"):
        return True
    return _parse_iso_deadline(deadline) is not None


STALE_AFTER_DAYS = 90

# The profile form deliberately does not ask about several niche eligibility
# conditions. Those can never be gated by the matcher, so the only honest
# surface is the special-check lane; a description that names a hard niche
# requirement without a matching special_requirements entry silently over-matches
# students. These guards are intentionally high-precision and warning-level.
_NICHE_REQUIREMENT_GUARDS = (
    {
        "label": "first-generation status",
        "description": re.compile(r"\bfirst[-\s]generation college students?\b", re.IGNORECASE),
        "encoded": re.compile(r"\bfirst[-\s]generation\b", re.IGNORECASE),
    },
    {
        "label": "identity/status",
        "description": re.compile(
            r"(?:\bopen only to\b|\blimited to\b|\brestricted to\b|\bapplicants must be\b|"
            r"\bstudents must be\b|\bmust identify as\b|\bwho identify as\b|\bliving with\b|"
            r"\bwith (?:a |an )?(?:documented |visible or invisible )?)"
            r".{0,120}\b(?:disabilit(?:y|ies)|disabled|learning disability|women|woman|"
            r"undocumented|immigrants?|new americans?|refugees?|asylees?|DACA|foster)\b|"
            r"\bfor\b.{0,80}\b(?:students|seniors|applicants)\b.{0,80}\b(?:with|living with)\b"
            r".{0,80}\b(?:disabilit(?:y|ies)|learning disability)\b|"
            r"\bopen only to women\b|\bfor women pursuing\b|\bfor New Americans\b",
            re.IGNORECASE,
        ),
        "encoded": re.compile(
            r"\b(?:disabilit(?:y|ies)|disabled|learning disability|women|woman|gender|"
            r"LGBTQ\+?|immigrants?|immigration|new americans?|undocumented|DACA|"
            r"refugees?|asylees?|foster|status)\b",
            re.IGNORECASE,
        ),
    },
    {
        "label": "nomination/endorsement",
        "description": re.compile(
            r"\b(?:requires institutional endorsement|must be nominated|nomination required)\b",
            re.IGNORECASE,
        ),
        "encoded": re.compile(
            r"\b(?:nomination|required nominee|nominated|endorsement|endorsed)\b",
            re.IGNORECASE,
        ),
    },
    {
        "label": "program-content",
        "description": re.compile(
            r"\b(?:ABET[-\s]accredited|substantially incorporates statistics|"
            r"eligible accredited programs|accredited or substantially equivalent programs)\b",
            re.IGNORECASE,
        ),
        "encoded": re.compile(
            r"\b(?:ABET|accredited|statistics|program(?:s)? substantially incorporates|"
            r"program-content|program content)\b",
            re.IGNORECASE,
        ),
    },
    {
        "label": "activity/lifestyle",
        "description": re.compile(
            r"\b(?:student[-\s]athletes?|varsity athletes?|240 hours of work before enrolling|"
            r"(?:volunteer|service) hours|unexpected financial hardship|"
            r"commitment to promoting a vegan diet|vegetarian or vegan)\b",
            re.IGNORECASE,
        ),
        "encoded": re.compile(
            r"\b(?:student[-\s]athletes?|athletic|athlete|varsity|240 hours|work before|"
            r"volunteer|service hours|hardship|vegan|vegetarian|lifestyle)\b",
            re.IGNORECASE,
        ),
    },
    {
        "label": "membership",
        "description": re.compile(
            r"\b(?:membership required|student membership is required|requires joining|"
            r"must (?:be|hold|join) (?:a |an |active |current )?.{0,80}members?|"
            r"must be active members?)\b",
            re.IGNORECASE,
        ),
        "encoded": re.compile(r"\b(?:member|membership|joining|network)\b", re.IGNORECASE),
    },
    {
        "label": "military affiliation",
        "description": re.compile(
            r"\bfor\b.{0,120}\b(?:veterans?|active-duty service members?|military spouses?|"
            r"disabled veterans?|service members who died)\b|"
            r"\b(?:veterans?|military spouses?)\b.{0,80}\b(?:only|required|eligible)\b",
            re.IGNORECASE,
        ),
        "encoded": re.compile(
            r"\b(?:veterans?|military|service members?|active-duty|spouses?|dependents?)\b",
            re.IGNORECASE,
        ),
    },
    {
        "label": "institution/channel",
        "description": re.compile(
            r"\b(?:partner colleges? through a national matching process|"
            r"district-by-district .{0,80} Member of Congress|"
            r"submit .{0,80} to their Member of Congress|"
            r"enrolled in local .{0,40} high schools?)\b",
            re.IGNORECASE,
        ),
        "encoded": re.compile(
            r"\b(?:partner[-\s]college|partner school|matching process|Member of Congress|"
            r"congressional district|local .{0,40} high school|institution|channel)\b",
            re.IGNORECASE,
        ),
    },
)

_NICHE_TRAP_PHRASES = (
    re.compile(r"\bregardless of immigration status\b", re.IGNORECASE),
    re.compile(r"\bDACA status alone does not qualify\b", re.IGNORECASE),
    re.compile(r"\bLGBTQ\+?.{0,80}\band allies\b", re.IGNORECASE),
    re.compile(r"\bwomen and/or\b", re.IGNORECASE),
    re.compile(r"\bmilitary bases?\b", re.IGNORECASE),
    re.compile(r"\bor dependents of active-duty U\.?S\.? military\b", re.IGNORECASE),
)


def _special_requirement_text(entry) -> str:
    elig = getattr(entry, "eligibility", None)
    if elig is None:
        return ""
    return " ".join(
        f"{req.label} {req.details}"
        for req in getattr(elig, "special_requirements", []) or []
    )


def _niche_requirement_warnings(entry, prefix: str) -> list[str]:
    description = getattr(entry, "description", "") or ""
    special_text = _special_requirement_text(entry)
    warnings: list[str] = []
    for guard in _NICHE_REQUIREMENT_GUARDS:
        if not guard["description"].search(description):
            continue
        if any(trap.search(description) for trap in _NICHE_TRAP_PHRASES):
            continue
        if guard["encoded"].search(special_text):
            continue
        warnings.append(
            f"{prefix}: description appears to contain a hard {guard['label']} "
            "requirement but no special_requirements entry encodes it "
            "(matcher will over-match)"
        )
    return warnings


def _normalized_special_label(label: str) -> str:
    return re.sub(r"\s+", " ", label.strip().lower())


def _duplicate_special_requirement_errors(entry, prefix: str) -> list[str]:
    elig = getattr(entry, "eligibility", None)
    if elig is None:
        return []
    seen: set[tuple[str, str]] = set()
    errors: list[str] = []
    for requirement in getattr(elig, "special_requirements", []) or []:
        key = (requirement.kind, _normalized_special_label(requirement.label))
        if key in seen:
            errors.append(
                f"{prefix}: duplicate special requirement {requirement.kind} "
                f"{key[1]!r}"
            )
            continue
        seen.add(key)
    return errors


def audit_dataset(scholarships: list[Scholarship], today: date | None = None) -> dict:
    """Return {errors, warnings, stats}. Errors are structural; warnings advisory.

    ``today`` defaults to the current date and is injectable so the staleness
    (needs-re-verification) checks can be tested deterministically.
    """
    today = today or date.today()
    errors: list[str] = []
    warnings: list[str] = []

    ids = [s.id for s in scholarships]
    for sid, count in Counter(ids).items():
        if count > 1:
            errors.append(f"Duplicate id: {sid} (appears {count} times)")

    verify_counts: Counter[str] = Counter()
    for s in scholarships:
        if not _deadline_ok(s.deadline):
            errors.append(f"{s.id}: unparseable deadline {s.deadline!r}")
        if s.estimated_deadline is not None and _parse_iso_deadline(s.estimated_deadline) is None:
            errors.append(f"{s.id}: invalid estimated_deadline {s.estimated_deadline!r} (must be an ISO date)")

        elig = s.eligibility
        if isinstance(elig.min_gpa, (int, float)) and not 0.0 <= float(elig.min_gpa) <= 4.0:
            errors.append(f"{s.id}: min_gpa out of range ({elig.min_gpa})")

        for field in elig.fields_of_study:
            if field not in FIELD_OF_STUDY_VALUES:
                warnings.append(f"{s.id}: field_of_study not in vocabulary: {field!r}")
        for tag in elig.demographics:
            if tag not in DEMOGRAPHIC_TAG_VALUES:
                warnings.append(f"{s.id}: demographic not in vocabulary: {tag!r}")
        for grade in elig.grade_levels:
            if grade not in GRADE_LEVEL_VALUES:
                warnings.append(f"{s.id}: grade_level not in vocabulary: {grade!r}")
        if isinstance(elig.states, list):
            for state in elig.states:
                if state.upper() not in STATE_CODE_VALUES:
                    warnings.append(f"{s.id}: state not a valid code: {state!r}")
        for school in elig.eligible_schools:
            aliases = [alias.strip().lower() for alias in school.aliases]
            if len(aliases) != len(set(aliases)):
                warnings.append(f"{s.id}: duplicate aliases for school {school.name!r}")
        errors.extend(_duplicate_special_requirement_errors(s, s.id))

        if s.verification is not None:
            if (
                s.verification.last_verified_at is not None
                and s.verification.last_verified_at > today
            ):
                errors.append(
                    f"{s.id}: last_verified_at is in the future "
                    f"({s.verification.last_verified_at})"
                )
            if (
                s.verification.provenance_recorded_at is not None
                and s.verification.provenance_recorded_at > today
            ):
                errors.append(
                    f"{s.id}: provenance_recorded_at is in the future "
                    f"({s.verification.provenance_recorded_at})"
                )
            if not s.verified:
                warnings.append(f"{s.id}: has verification metadata but verified is false")

        warnings.extend(_niche_requirement_warnings(s, s.id))

        if elig.min_gpa == "VERIFY":
            verify_counts["min_gpa"] += 1
        if s.deadline.startswith("VERIFY"):
            verify_counts["deadline"] += 1
        if elig.citizenship_requirement == "VERIFY":
            verify_counts["citizenship"] += 1
        if elig.states == "VERIFY":
            verify_counts["states"] += 1

    verified = sum(1 for s in scholarships if s.verified)
    estimated = sum(1 for s in scholarships if s.estimated_deadline)
    with_provenance = sum(1 for s in scholarships if s.verification is not None)
    verified_with_audit_date = sum(
        1
        for s in scholarships
        if s.verified and s.verification is not None and s.verification.last_verified_at is not None
    )
    source_recorded_without_audit = sum(
        1
        for s in scholarships
        if s.verified
        and s.verification is not None
        and s.verification.last_verified_at is None
    )
    stale_audit_ids = [
        s.id
        for s in scholarships
        if s.verified
        and s.verification is not None
        and s.verification.last_verified_at is not None
        and (today - s.verification.last_verified_at).days > STALE_AFTER_DAYS
    ]
    # Actionable re-verification queue: verified entries never independently
    # audited, plus those whose audit has aged past the staleness window.
    needs_reverification_ids = [
        s.id
        for s in scholarships
        if s.verified
        and s.verification is not None
        and (
            s.verification.last_verified_at is None
            or (today - s.verification.last_verified_at).days > STALE_AFTER_DAYS
        )
    ]
    stats = {
        "total": len(scholarships),
        "verified": verified,
        "unverified": len(scholarships) - verified,
        "special_requirements": sum(
            1 for s in scholarships if s.eligibility.special_requirements
        ),
        "estimated_deadlines": estimated,
        "with_provenance": with_provenance,
        "verified_with_audit_date": verified_with_audit_date,
        "source_recorded_without_audit": source_recorded_without_audit,
        "stale_audit": len(stale_audit_ids),
        "needs_reverification": len(needs_reverification_ids),
        "verified_without_provenance": verified - with_provenance,
        "verify_placeholders": dict(verify_counts),
    }
    return {
        "errors": errors,
        "warnings": warnings,
        "stats": stats,
        "stale_audit_ids": stale_audit_ids,
        "needs_reverification_ids": needs_reverification_ids,
    }


def audit_programs(programs: list[SummerProgram], today: date | None = None) -> dict:
    """Return structural errors/warnings for the elite summer-program catalog."""
    today = today or date.today()
    errors: list[str] = []
    warnings: list[str] = []
    verify_counts: Counter[str] = Counter()

    ids = [p.id for p in programs]
    for pid, count in Counter(ids).items():
        if count > 1:
            errors.append(f"program {pid}: duplicate id appears {count} times")

    for program in programs:
        if not _deadline_ok(program.deadline):
            errors.append(f"program {program.id}: unparseable deadline {program.deadline!r}")
        if (
            program.estimated_deadline is not None
            and _parse_iso_deadline(program.estimated_deadline) is None
        ):
            errors.append(
                f"program {program.id}: invalid estimated_deadline "
                f"{program.estimated_deadline!r} (must be an ISO date)"
            )

        elig = program.eligibility
        if isinstance(elig.min_gpa, (int, float)) and not 0.0 <= float(elig.min_gpa) <= 4.0:
            errors.append(f"program {program.id}: min_gpa out of range ({elig.min_gpa})")
        for field in elig.fields_of_study:
            if field not in FIELD_OF_STUDY_VALUES:
                warnings.append(f"program {program.id}: field_of_study not in vocabulary: {field!r}")
        for tag in elig.demographics:
            if tag not in DEMOGRAPHIC_TAG_VALUES:
                warnings.append(f"program {program.id}: demographic not in vocabulary: {tag!r}")
        for grade in elig.grade_levels:
            if grade not in GRADE_LEVEL_VALUES:
                warnings.append(f"program {program.id}: grade_level not in vocabulary: {grade!r}")
        if isinstance(elig.states, list):
            for state in elig.states:
                if state.upper() not in STATE_CODE_VALUES:
                    warnings.append(f"program {program.id}: state not a valid code: {state!r}")
        errors.extend(_duplicate_special_requirement_errors(program, f"program {program.id}"))

        requirement_ids = [requirement.id for requirement in program.application_requirements]
        for requirement_id, count in Counter(requirement_ids).items():
            if count > 1:
                errors.append(
                    f"program {program.id}: duplicate application requirement id "
                    f"{requirement_id!r}"
                )

        if program.verification is not None:
            if (
                program.verification.last_verified_at is not None
                and program.verification.last_verified_at > today
            ):
                errors.append(
                    f"program {program.id}: last_verified_at is in the future "
                    f"({program.verification.last_verified_at})"
                )
            if not program.verified:
                warnings.append(f"program {program.id}: has verification metadata but verified is false")

        warnings.extend(_niche_requirement_warnings(program, f"program {program.id}"))

        if program.deadline.startswith("VERIFY"):
            verify_counts["deadline"] += 1
        if elig.citizenship_requirement == "VERIFY":
            verify_counts["citizenship"] += 1
        if program.program_format == "VERIFY":
            verify_counts["program_format"] += 1
        if program.cost_category == "VERIFY":
            verify_counts["cost_category"] += 1

    stats = {
        "total": len(programs),
        "verified": sum(1 for p in programs if p.verified),
        "unverified": sum(1 for p in programs if not p.verified),
        "with_checklists": sum(1 for p in programs if p.application_requirements),
        "checklist_steps": sum(len(p.application_requirements) for p in programs),
        "estimated_deadlines": sum(1 for p in programs if p.estimated_deadline),
        "verify_placeholders": dict(verify_counts),
    }
    return {"errors": errors, "warnings": warnings, "stats": stats}


def audit_competitions(competitions: list[Competition], today: date | None = None) -> dict:
    """Return structural errors/warnings for the competitions catalog."""
    today = today or date.today()
    errors: list[str] = []
    warnings: list[str] = []
    verify_counts: Counter[str] = Counter()

    ids = [c.id for c in competitions]
    for cid, count in Counter(ids).items():
        if count > 1:
            errors.append(f"competition {cid}: duplicate id appears {count} times")

    for competition in competitions:
        if not _deadline_ok(competition.deadline):
            errors.append(
                f"competition {competition.id}: unparseable deadline {competition.deadline!r}"
            )
        if (
            competition.estimated_deadline is not None
            and _parse_iso_deadline(competition.estimated_deadline) is None
        ):
            errors.append(
                f"competition {competition.id}: invalid estimated_deadline "
                f"{competition.estimated_deadline!r} (must be an ISO date)"
            )

        elig = competition.eligibility
        if isinstance(elig.min_gpa, (int, float)) and not 0.0 <= float(elig.min_gpa) <= 4.0:
            errors.append(f"competition {competition.id}: min_gpa out of range ({elig.min_gpa})")
        for field in elig.fields_of_study:
            if field not in FIELD_OF_STUDY_VALUES:
                warnings.append(
                    f"competition {competition.id}: field_of_study not in vocabulary: {field!r}"
                )
        for tag in elig.demographics:
            if tag not in DEMOGRAPHIC_TAG_VALUES:
                warnings.append(
                    f"competition {competition.id}: demographic not in vocabulary: {tag!r}"
                )
        for grade in elig.grade_levels:
            if grade not in GRADE_LEVEL_VALUES:
                warnings.append(
                    f"competition {competition.id}: grade_level not in vocabulary: {grade!r}"
                )
        if isinstance(elig.states, list):
            for state in elig.states:
                if state.upper() not in STATE_CODE_VALUES:
                    warnings.append(
                        f"competition {competition.id}: state not a valid code: {state!r}"
                    )
        errors.extend(
            _duplicate_special_requirement_errors(
                competition,
                f"competition {competition.id}",
            )
        )

        requirement_ids = [requirement.id for requirement in competition.application_requirements]
        for requirement_id, count in Counter(requirement_ids).items():
            if count > 1:
                errors.append(
                    f"competition {competition.id}: duplicate application requirement id "
                    f"{requirement_id!r}"
                )

        if competition.verification is not None:
            if (
                competition.verification.last_verified_at is not None
                and competition.verification.last_verified_at > today
            ):
                errors.append(
                    f"competition {competition.id}: last_verified_at is in the future "
                    f"({competition.verification.last_verified_at})"
                )
            if not competition.verified:
                warnings.append(
                    f"competition {competition.id}: has verification metadata but verified is false"
                )

        warnings.extend(
            _niche_requirement_warnings(competition, f"competition {competition.id}")
        )

        if competition.deadline.startswith("VERIFY"):
            verify_counts["deadline"] += 1
        if elig.citizenship_requirement == "VERIFY":
            verify_counts["citizenship"] += 1
        if competition.participation_format == "VERIFY":
            verify_counts["participation_format"] += 1
        if competition.cost_category == "VERIFY":
            verify_counts["cost_category"] += 1

    stats = {
        "total": len(competitions),
        "verified": sum(1 for c in competitions if c.verified),
        "unverified": sum(1 for c in competitions if not c.verified),
        "with_checklists": sum(1 for c in competitions if c.application_requirements),
        "checklist_steps": sum(len(c.application_requirements) for c in competitions),
        "estimated_deadlines": sum(1 for c in competitions if c.estimated_deadline),
        "verify_placeholders": dict(verify_counts),
    }
    return {"errors": errors, "warnings": warnings, "stats": stats}


def main() -> int:
    scholarships = load_scholarships()
    programs = load_summer_programs()
    competitions = load_competitions()
    report = audit_dataset(scholarships)
    program_report = audit_programs(programs)
    competition_report = audit_competitions(competitions)
    stats = report["stats"]
    program_stats = program_report["stats"]

    print(f"Scholarships: {stats['total']}")
    print(f"  verified:   {stats['verified']}")
    print(f"  unverified: {stats['unverified']}")
    print(f"  special-check lane: {stats['special_requirements']}")
    print(f"  estimated deadlines: {stats['estimated_deadlines']}")
    print(f"  records with official source: {stats['with_provenance']}")
    print(f"  verified records with audit date: {stats['verified_with_audit_date']}")
    print(f"  source recorded without new audit: {stats['source_recorded_without_audit']}")
    print(f"  verified records awaiting source: {stats['verified_without_provenance']}")
    print(
        f"  needs re-verification (>{STALE_AFTER_DAYS}d old or never audited): "
        f"{stats['needs_reverification']} (audit gone stale: {stats['stale_audit']})"
    )
    print("VERIFY placeholders:")
    for field, count in sorted(stats["verify_placeholders"].items()):
        print(f"  {field:12} {count}")

    print("\nSummer programs:")
    print(f"  total:      {program_stats['total']}")
    print(f"  verified:   {program_stats['verified']}")
    print(f"  unverified: {program_stats['unverified']}")
    print(f"  with application checklists: {program_stats['with_checklists']}")
    print(f"  checklist steps: {program_stats['checklist_steps']}")
    print(f"  estimated deadlines: {program_stats['estimated_deadlines']}")
    print("  VERIFY placeholders:")
    for field, count in sorted(program_stats["verify_placeholders"].items()):
        print(f"    {field:14} {count}")

    competition_stats = competition_report["stats"]
    print("\nCompetitions:")
    print(f"  total:      {competition_stats['total']}")
    print(f"  verified:   {competition_stats['verified']}")
    print(f"  unverified: {competition_stats['unverified']}")
    print(f"  with application checklists: {competition_stats['with_checklists']}")
    print(f"  checklist steps: {competition_stats['checklist_steps']}")
    print(f"  estimated deadlines: {competition_stats['estimated_deadlines']}")
    print("  VERIFY placeholders:")
    for field, count in sorted(competition_stats["verify_placeholders"].items()):
        print(f"    {field:20} {count}")

    queue = report["needs_reverification_ids"]
    if queue:
        print(f"\nRe-verification queue ({len(queue)}):")
        for sid in queue[:50]:
            print(f"  - {sid}")
        if len(queue) > 50:
            print(f"  ... and {len(queue) - 50} more")

    warnings = [
        *report["warnings"],
        *program_report["warnings"],
        *competition_report["warnings"],
    ]
    errors = [*report["errors"], *program_report["errors"], *competition_report["errors"]]

    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for warning in warnings[:50]:
            print(f"  - {warning}")
        if len(warnings) > 50:
            print(f"  ... and {len(warnings) - 50} more")

    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("\nNo structural errors.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
