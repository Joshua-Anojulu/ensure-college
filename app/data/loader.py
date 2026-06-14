import json
from pathlib import Path

from app.models.scholarship import Scholarship

DEFAULT_DATA_PATH = Path(__file__).parent / "scholarships.json"


def load_scholarships(path: Path | None = None) -> list[Scholarship]:
    """Load scholarships from the seed JSON file.

    The file is a top-level object with a ``scholarships`` array, not a bare list.
    """
    data_path = path or DEFAULT_DATA_PATH
    raw = json.loads(data_path.read_text(encoding="utf-8"))
    return [Scholarship.model_validate(entry) for entry in raw["scholarships"]]
