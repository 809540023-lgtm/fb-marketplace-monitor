from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any


class DigiChefJsonRepository:
    backend_name = "json"
    repository_mode = "snapshot_file"

    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        raw = self.path.read_text(encoding="utf-8")
        if not raw.strip():
            return None
        try:
            return json.loads(raw)
        except JSONDecodeError:
            return None

    def save(self, payload: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def readiness(self) -> dict[str, Any]:
        return {
            "backend": self.backend_name,
            "repository_mode": self.repository_mode,
            "json_path": str(self.path),
            "ready": True,
            "initialized": self.path.exists(),
        }
