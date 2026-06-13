from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class DigiChefSettings:
    json_path: str = "data/digichef_store.json"
    uploads_dir: str = "data/digichef_uploads"


def load_settings() -> DigiChefSettings:
    return DigiChefSettings(
        json_path=os.getenv("DIGICHEF_JSON_PATH", "data/digichef_store.json").strip(),
        uploads_dir=os.getenv("DIGICHEF_UPLOADS_DIR", "data/digichef_uploads").strip(),
    )
