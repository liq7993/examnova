from __future__ import annotations

import base64
import mimetypes
import os
import tempfile
from functools import lru_cache
from io import BytesIO

import httpx

from app.services.settings_store import load_settings


@lru_cache(maxsize=1)
def _get_paddle_ocr():
    try:
        from paddleocr import PaddleOCR
    except Exception:
        return None
    return PaddleOCR(use_angle_cls=True, lang="ch")


def parse_image_bytes(image_bytes: bytes, filename: str | None) -> tuple[str, str]:
    mathpix_text, mathpix_engine = _try_mathpix(image_bytes, filename)
    if mathpix_text:
        return (mathpix_text, mathpix_engine)

    ocr = _get_paddle_ocr()
    if ocr is None:
        if mathpix_engine.startswith("mathpix_error"):
            return (
                f"Mathpix 识别失败，且未安装 PaddleOCR。{mathpix_text}".strip(),
                mathpix_engine,
            )
        return ("OCR占位：尚未安装 PaddleOCR。", "stub")

    pipeline_lines, pipeline_engine = _try_pipeline(image_bytes, filename, ocr)
    if pipeline_lines:
        engine = pipeline_engine
        if mathpix_engine.startswith("mathpix_error"):
            engine = f"{mathpix_engine};{engine}"
        return ("\n".join(pipeline_lines), engine)

    lines = _run_paddle(image_bytes, filename, ocr)
    if not lines:
        return ("OCR未识别出有效文本。", "paddleocr")
    engine = "paddleocr"
    if mathpix_engine.startswith("mathpix_error"):
        engine = f"{mathpix_engine};{engine}"
    return ("\n".join(lines), engine)


def _guess_mime(filename: str | None) -> str:
    if filename:
        guess, _ = mimetypes.guess_type(filename)
        if guess:
            return guess
    return "image/png"


def _get_mathpix_settings() -> tuple[str, str, str] | None:
    settings = load_settings() or {}
    if not settings.get("mathpix_enabled"):
        return None
    app_id = settings.get("mathpix_app_id") or ""
    app_key = settings.get("mathpix_app_key") or ""
    endpoint = settings.get("mathpix_endpoint") or "https://api.mathpix.com/v3/text"
    if not app_id or not app_key:
        return None
    return (endpoint, app_id, app_key)


def _try_mathpix(image_bytes: bytes, filename: str | None) -> tuple[str, str]:
    config = _get_mathpix_settings()
    if not config:
        return ("", "")
    endpoint, app_id, app_key = config
    mime = _guess_mime(filename)
    payload = {
        "src": f"data:{mime};base64,{base64.b64encode(image_bytes).decode('utf-8')}",
        "formats": ["text"],
        "rm_spaces": True,
        "math_inline_delimiters": ["$", "$"],
    }
    headers = {
        "app_id": app_id,
        "app_key": app_key,
        "Content-Type": "application/json",
    }
    try:
        response = httpx.post(endpoint, json=payload, headers=headers, timeout=30)
    except Exception as exc:
        return (f"Mathpix 调用异常：{exc}", "mathpix_error")
    if response.status_code >= 400:
        return (f"Mathpix HTTP {response.status_code}", "mathpix_error")
    try:
        data = response.json()
    except Exception:
        return ("Mathpix 返回解析失败。", "mathpix_error")
    text = data.get("text")
    if not text:
        error = data.get("error") or "Mathpix 无文本输出。"
        return (str(error), "mathpix_error")
    return (text, "mathpix")


def _run_paddle(image_bytes: bytes, filename: str | None, ocr) -> list[str]:
    suffix = ".png"
    if filename and "." in filename:
        _, ext = os.path.splitext(filename)
        if ext:
            suffix = ext

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(image_bytes)
        temp_path = temp_file.name

    try:
        result = ocr.ocr(temp_path, cls=True)
    finally:
        try:
            os.remove(temp_path)
        except Exception:
            pass

    lines: list[str] = []
    try:
        for block in result:
            for line in block:
                if len(line) >= 2:
                    text = line[1][0]
                    if text:
                        lines.append(text)
    except Exception:
        pass
    return lines


def _preprocess_for_pipeline(image_bytes: bytes) -> bytes | None:
    try:
        from PIL import Image, ImageFilter, ImageOps
    except Exception:
        return None
    try:
        with Image.open(BytesIO(image_bytes)) as img:
            img = img.convert("L")
            img = ImageOps.autocontrast(img)
            img = img.filter(ImageFilter.MedianFilter(size=3))
            img = img.point(lambda x: 0 if x < 165 else 255, mode="1")
            output = BytesIO()
            img.save(output, format="PNG")
            return output.getvalue()
    except Exception:
        return None


def _try_pipeline(image_bytes: bytes, filename: str | None, ocr) -> tuple[list[str], str]:
    processed = _preprocess_for_pipeline(image_bytes)
    if processed is None:
        return ([], "pipeline_unavailable")
    lines = _run_paddle(processed, filename, ocr)
    if lines:
        return (lines, "pipeline+paddle")
    return ([], "pipeline_no_text")
