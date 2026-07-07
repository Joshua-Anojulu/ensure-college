import json
from pathlib import Path

from app.models.competition import Competition
from app.models.program import SummerProgram
from app.models.scholarship import Scholarship

DEFAULT_DATA_PATH = Path(__file__).parent / "scholarships.json"
DEFAULT_SPECIAL_REQUIREMENTS_PATH = Path(__file__).parent / "special_requirements.json"
DEFAULT_PROGRAMS_PATH = Path(__file__).parent / "summer_programs.json"
DEFAULT_COMPETITIONS_PATH = Path(__file__).parent / "competitions.json"


def _load_special_requirements(path: Path = DEFAULT_SPECIAL_REQUIREMENTS_PATH) -> dict[str, list[dict]]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw.get("requirements", {})


def load_scholarships(path: Path | None = None) -> list[Scholarship]:
    """Load scholarships from the seed JSON file.

    The file is a top-level object with a ``scholarships`` array, not a bare list.
    """
    data_path = path or DEFAULT_DATA_PATH
    raw = json.loads(data_path.read_text(encoding="utf-8"))
    if path is None:
        special_requirements = _load_special_requirements()
        for entry in raw["scholarships"]:
            requirements = special_requirements.get(entry["id"])
            if requirements:
                eligibility = entry.setdefault("eligibility", {})
                existing = eligibility.get("special_requirements", [])
                eligibility["special_requirements"] = [*existing, *requirements]
    return [Scholarship.model_validate(entry) for entry in raw["scholarships"]]


def load_summer_programs(path: Path | None = None) -> list[SummerProgram]:
    """Load elite summer programs from the seed JSON file.

    The file is a top-level object with a ``programs`` array, not a bare list.
    """
    data_path = path or DEFAULT_PROGRAMS_PATH
    raw = json.loads(data_path.read_text(encoding="utf-8"))
    return [SummerProgram.model_validate(entry) for entry in raw["programs"]]


def load_competitions(path: Path | None = None) -> list[Competition]:
    """Load curated competitions from the seed JSON file.

    The file is a top-level object with a ``competitions`` array, not a bare list.
    """
    data_path = path or DEFAULT_COMPETITIONS_PATH
    raw = json.loads(data_path.read_text(encoding="utf-8"))
    return [Competition.model_validate(entry) for entry in raw["competitions"]]
