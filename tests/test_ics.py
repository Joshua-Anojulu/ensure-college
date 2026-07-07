from app.data.loader import load_scholarships, load_summer_programs
from app.ics import build_calendar


def test_calendar_exports_scholarship_and_program_verified_deadlines():
    scholarship = next(
        item
        for item in load_scholarships()
        if item.deadline and not item.deadline.startswith("VERIFY") and item.deadline != "rolling"
    )
    program = load_summer_programs()[0].model_copy(update={"deadline": "2026-02-01"})

    calendar = build_calendar([scholarship], [program])

    assert "BEGIN:VCALENDAR" in calendar
    assert f"UID:scholarship-{scholarship.id}@ensurecollege" in calendar
    assert f"UID:program-{program.id}@ensurecollege" in calendar
    assert f"SUMMARY:Apply: {program.name}" in calendar
    assert "X-WR-CALNAME:EnsureCollege verified deadlines" in calendar


def test_calendar_skips_unverified_program_deadlines():
    program = load_summer_programs()[0].model_copy(update={"deadline": "VERIFY"})

    calendar = build_calendar([], [program])

    assert f"UID:program-{program.id}@ensurecollege" not in calendar
    assert "BEGIN:VCALENDAR" in calendar


def test_calendar_folds_lines_at_75_octets():
    program = load_summer_programs()[0].model_copy(
        update={
            "deadline": "2026-02-01",
            "name": "An Extremely Long Program Name That Overflows The Line " * 3,
        }
    )

    calendar = build_calendar([], [program])

    for line in calendar.split("\r\n"):
        assert len(line.encode("utf-8")) <= 75
    # Unfolding (joining continuation lines) restores the full summary text.
    unfolded = calendar.replace("\r\n ", "")
    assert f"SUMMARY:Apply: {program.name}" in unfolded
