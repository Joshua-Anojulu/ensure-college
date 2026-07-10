"""Matching helpers shared by the scholarship and summer-program matchers.

Both matchers score the same student profile against the same building blocks
(citizenship, field of study, demographics, grade level, deadlines), so the
logic for those gates lives here and is imported by each matcher. Keeping it in
one place is what guarantees a student's eligibility is judged identically for a
scholarship and a program.
"""

from __future__ import annotations

from datetime import date

# Citizenship requirement value -> the set of student citizenship tags it admits.
CITIZENSHIP_ALLOWED: dict[str, set[str]] = {
    "us_citizen": {"us_citizen"},
    "permanent_resident": {"permanent_resident"},
    "us_citizen_or_permanent_resident": {"us_citizen", "permanent_resident"},
    "us_citizen_national_or_permanent_resident": {
        "us_citizen",
        "permanent_resident",
        "us_national",
    },
    "us_citizen_permanent_resident_or_daca": {
        "us_citizen",
        "permanent_resident",
        "daca",
    },
    "us_citizen_permanent_resident_or_national": {
        "us_citizen",
        "permanent_resident",
        "us_national",
    },
    "us_citizen_permanent_resident_or_us_national": {
        "us_citizen",
        "permanent_resident",
        "us_national",
    },
}

# Field matching is intentionally asymmetric. A requirement for a broad area like
# "science" may reasonably fit a student who chose a more specific science field.
# The reverse is not true: a student choosing a broad field like "science" should
# not be told they overlap with a requirement that specifically wants
# "computer_science".
FIELD_REQUIREMENT_CHILDREN: dict[str, set[str]] = {
    "arts": {"music"},
    "health_medicine": {"nursing"},
    "natural_sciences": {"environmental_science"},
    "science": {
        "computer_science",
        "environmental_science",
        "mathematics",
        "natural_sciences",
        "research",
    },
    "technology": {"computer_science", "engineering"},
}

# Grade matching is also asymmetric. A broad level accepts a student's specific
# class year, but a vague legacy student value should not satisfy a narrow
# senior-only or junior-only requirement.
GRADE_REQUIREMENT_CHILDREN: dict[str, set[str]] = {
    "high_school": {
        "high_school_freshman",
        "high_school_sophomore",
        "high_school_junior",
        "high_school_senior",
    },
    "college_undergraduate": {
        "college_freshman",
        "college_sophomore",
        "college_junior",
        "college_senior",
    },
}

# Related-field adjacency: partial fit credit only, never eligibility.
# Symmetric by construction; a test enforces it. Values are fields_of_study
# vocabulary entries.
FIELD_ADJACENCY: dict[str, set[str]] = {
    "computer_science": {"technology", "engineering", "mathematics", "science"},
    "technology": {"computer_science", "engineering"},
    "engineering": {"computer_science", "technology", "mathematics", "science", "architecture"},
    "mathematics": {"computer_science", "engineering", "science", "research", "business"},
    "science": {
        "natural_sciences",
        "environmental_science",
        "health_medicine",
        "research",
        "mathematics",
        "engineering",
        "computer_science",
    },
    "natural_sciences": {"science", "environmental_science", "agriculture", "research"},
    "environmental_science": {"science", "natural_sciences", "agriculture"},
    "agriculture": {"environmental_science", "natural_sciences"},
    "health_medicine": {"nursing", "science"},
    "nursing": {"health_medicine"},
    "arts": {"music", "literature", "architecture", "communications"},
    "music": {"arts"},
    "literature": {"humanities", "arts", "communications"},
    "humanities": {"literature", "philosophy", "social_sciences", "law"},
    "philosophy": {"humanities"},
    "social_sciences": {"humanities", "law", "education", "communications"},
    "law": {"social_sciences", "humanities", "business"},
    "business": {"communications", "law", "mathematics"},
    "communications": {"arts", "literature", "social_sciences", "business"},
    "education": {"social_sciences"},
    "research": {"science", "mathematics", "natural_sciences"},
    "architecture": {"engineering", "arts"},
}

GRADE_PROGRESSION: list[str] = [
    "middle_school",
    "high_school_freshman",
    "high_school_sophomore",
    "high_school_junior",
    "high_school_senior",
    "college_freshman",
    "college_sophomore",
    "college_junior",
    "college_senior",
]

GRADE_LABELS: dict[str, str] = {
    "middle_school": "in middle school",
    "high_school_freshman": "a high school freshman",
    "high_school_sophomore": "a high school sophomore",
    "high_school_junior": "a high school junior",
    "high_school_senior": "a high school senior",
    "college_freshman": "a college freshman",
    "college_sophomore": "a college sophomore",
    "college_junior": "a college junior",
    "college_senior": "a college senior",
}


def normalize_tag(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def parse_iso_deadline(deadline: str) -> date | None:
    if deadline == "rolling":
        return None
    if deadline == "VERIFY" or deadline.startswith("VERIFY"):
        return None
    try:
        return date.fromisoformat(deadline)
    except ValueError:
        return None


def citizenship_satisfies(student_citizenship: str, requirement: str) -> bool | None:
    """Return True/False when requirement is known, None when unverified."""
    if requirement == "VERIFY":
        return None
    if requirement == "any":
        return True
    allowed = CITIZENSHIP_ALLOWED.get(requirement)
    if allowed is None:
        allowed = {normalize_tag(requirement)}
    return normalize_tag(student_citizenship) in allowed


def matching_fields(student_majors: list[str], required_fields: list[str]) -> list[str]:
    if not required_fields:
        return []
    norm_majors = {normalize_tag(major) for major in student_majors}
    matches: list[str] = []
    for field in required_fields:
        norm_field = normalize_tag(field)
        accepted_student_fields = {norm_field, *FIELD_REQUIREMENT_CHILDREN.get(norm_field, set())}
        if norm_majors.intersection(accepted_student_fields):
            matches.append(field)
    return matches


def grade_level_matches(student_grade: str, required_grades: list[str]) -> bool:
    for grade in required_grades:
        norm_grade = normalize_tag(grade)
        if normalize_tag(student_grade) == norm_grade:
            return True
        accepted_student_grades = GRADE_REQUIREMENT_CHILDREN.get(norm_grade, set())
        if normalize_tag(student_grade) in accepted_student_grades:
            return True
    return False


def matching_demographics(student_tags: list[str], required_tags: list[str]) -> list[str]:
    if not required_tags:
        return []
    student_set = {normalize_tag(tag) for tag in student_tags}
    return [tag for tag in required_tags if normalize_tag(tag) in student_set]


def related_fields(student_majors: list[str], required_fields: list[str]) -> list[str]:
    """Required fields with no exact/child overlap but an adjacent student major.

    Exact and child matches are handled by matching_fields; this only reports
    requirements that would otherwise score zero.
    """
    if not required_fields:
        return []
    exact = set(matching_fields(student_majors, required_fields))
    norm_majors = {normalize_tag(major) for major in student_majors}
    related: list[str] = []
    for field in required_fields:
        if field in exact:
            continue
        adjacent = FIELD_ADJACENCY.get(normalize_tag(field), set())
        if norm_majors.intersection(adjacent):
            related.append(field)
    return related


def earliest_future_qualifying_grade(
    student_grade: str, required_grades: list[str]
) -> str | None:
    """Earliest grade strictly after the student's current one that qualifies."""
    norm = normalize_tag(student_grade)
    if norm not in GRADE_PROGRESSION:
        return None
    start = GRADE_PROGRESSION.index(norm) + 1
    for grade in GRADE_PROGRESSION[start:]:
        if grade_level_matches(grade, required_grades):
            return grade
    return None
