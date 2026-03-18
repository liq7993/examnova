import json
import re
from typing import Any


def extract_json_object(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    text = text.strip()
    # Fast path: direct JSON object.
    if text.startswith("{") and text.endswith("}"):
        try:
            return json.loads(text)
        except Exception:
            pass
    # Fallback: find the first JSON object block.
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except Exception:
        return None
