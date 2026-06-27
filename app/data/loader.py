import json
from pathlib import Path

from app.models.program import SummerProgram
from app.models.scholarship import Scholarship

DEFAULT_DATA_PATH = Path(__file__).parent / "scholarships.json"
DEFAULT_PROGRAMS_PATH = Path(__file__).parent / "summer_programs.json"


def load_scholarships(path: Path | None = None) -> list[Scholarship]:
    """Load scholarships from the seed JSON file.

    The file is a top-level object with a ``scholarships`` array, not a bare list.
    """
    data_path = path or DEFAULT_DATA_PATH
    raw = json.loads(data_path.read_text(encoding="utf-8"))
    return [Scholarship.model_validate(entry) for entry in raw["scholarships"]]


def load_summer_programs(path: Path | None = None) -> list[SummerProgram]:
    """Load elite summer programs from the seed JSON file.

    The file is a top-level object with a ``programs`` array, not a bare list.
    """
    data_path = path or DEFAULT_PROGRAMS_PATH
    raw = json.loads(data_path.read_text(encoding="utf-8"))
    return [SummerProgram.model_validate(entry) for entry in raw["programs"]]
