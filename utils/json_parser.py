from __future__ import annotations

import json
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


class StructuredOutputError(ValueError):
    pass


def extract_json_candidate(raw_text: str) -> str:
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            text = "\n".join(lines[1:-1]).strip()
    start_positions = [i for i in (text.find("{"), text.find("[")) if i != -1]
    if not start_positions:
        return text
    start = min(start_positions)
    end_object = text.rfind("}")
    end_array = text.rfind("]")
    end = max(end_object, end_array)
    if end != -1 and end >= start:
        return text[start : end + 1]
    return text[start:]


def parse_model(raw: str, model_type: type[T]) -> T:
    candidate = extract_json_candidate(raw)
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise StructuredOutputError(f"無法解析 JSON: {exc}") from exc

    try:
        return model_type.model_validate(data)
    except ValidationError as exc:
        raise StructuredOutputError(f"資料結構不符合預期: {exc}") from exc


def parse_model_list(raw: str, model_type: type[T]) -> list[T]:
    candidate = extract_json_candidate(raw)
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise StructuredOutputError(f"無法解析 JSON: {exc}") from exc

    if not isinstance(data, list):
        raise StructuredOutputError("預期為 JSON 陣列。")

    items: list[T] = []
    for entry in data:
        try:
            items.append(model_type.model_validate(entry))
        except ValidationError as exc:
            raise StructuredOutputError(f"陣列項目結構錯誤: {exc}") from exc
    return items


def dump_model_list(items: list[BaseModel]) -> list[dict[str, Any]]:
    return [item.model_dump(mode="json") for item in items]
