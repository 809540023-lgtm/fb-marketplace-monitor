from __future__ import annotations

from datetime import datetime
import mimetypes
from pathlib import Path
import re
import shutil
from uuid import uuid4

from fastapi import UploadFile

from digichef.config import load_settings

_settings = load_settings()


def uploads_root() -> Path:
    root = Path(_settings.uploads_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _safe_segment(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip())
    return cleaned.strip("-").lower()


def _guess_extension(upload: UploadFile) -> str:
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix:
        return suffix
    guessed = mimetypes.guess_extension(upload.content_type or "")
    return guessed or ".jpg"


def save_upload(upload: UploadFile, bucket: str, preferred_name: str | None = None) -> str:
    bucket_name = _safe_segment(bucket) or "misc"
    stem = _safe_segment(preferred_name or Path(upload.filename or "").stem or bucket_name) or bucket_name
    now = datetime.now().astimezone()
    relative_dir = Path(bucket_name) / now.strftime("%Y") / now.strftime("%m") / now.strftime("%d")
    target_dir = uploads_root() / relative_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{stem}-{uuid4().hex[:12]}{_guess_extension(upload)}"
    target_path = target_dir / filename
    upload.file.seek(0)
    with target_path.open("wb") as handle:
        shutil.copyfileobj(upload.file, handle)
    return f"/digichef/uploads/{relative_dir.as_posix()}/{filename}"


def resolve_upload(file_path: str) -> Path:
    root = uploads_root().resolve()
    candidate = (root / file_path).resolve()
    if candidate != root and root not in candidate.parents:
        raise FileNotFoundError(file_path)
    if not candidate.exists() or not candidate.is_file():
        raise FileNotFoundError(file_path)
    return candidate
