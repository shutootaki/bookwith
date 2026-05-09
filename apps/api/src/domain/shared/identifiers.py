from __future__ import annotations

import re
import uuid

_STRICT_UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def is_strict_uuid(value: object) -> bool:
    if not isinstance(value, str) or not _STRICT_UUID.match(value):
        return False
    try:
        uuid.UUID(value)
    except ValueError:
        return False
    return True


def normalize_strict_uuid(
    value: object,
    *,
    name: str,
    generate_if_empty: bool = False,
) -> str:
    if not value and generate_if_empty:
        return str(uuid.uuid4())
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} is required")
    if not is_strict_uuid(value):
        raise ValueError(f"{name} must be a valid UUID")
    return value.lower()
