from __future__ import annotations

import httpx

from app.services.settings_store import load_settings


def _extract_message_content(data: dict) -> str | None:
    try:
        choice = data.get("choices", [])[0]
    except Exception:
        return None
    if isinstance(choice, dict):
        message = choice.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str):
                return content.strip()
        messages = choice.get("messages")
        if isinstance(messages, list) and messages:
            content = messages[0].get("content")
            if isinstance(content, str):
                return content.strip()
    return None


def _request_completion(
    *,
    api_key: str,
    base_url: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    timeout: float,
    reasoning_split: bool,
    max_tokens: int | None = None,
) -> tuple[str | None, str | None]:
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: dict = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
    }
    if reasoning_split:
        payload["reasoning_split"] = True
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    try:
        with httpx.Client(timeout=timeout, trust_env=False, http2=False) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        return None, f"http_{exc.response.status_code}"
    except httpx.RemoteProtocolError:
        return None, "remote_protocol_error"
    except httpx.TimeoutException:
        return None, "timeout"
    except Exception:
        return None, "request_error"

    content = _extract_message_content(data)
    if not content:
        return None, "empty_response"
    return content, None


def generate_text_from_settings(
    settings: dict | None,
    system_prompt: str,
    user_prompt: str,
) -> tuple[str | None, str | None]:
    if not settings:
        return None, "missing_settings"
    api_key = settings.get("api_key")
    base_url = settings.get("base_url")
    model = settings.get("model")
    demo_mode = settings.get("demo_mode", True)

    if demo_mode:
        return None, "demo_mode"

    if not api_key or not base_url or not model:
        return None, "missing_config"

    return _request_completion(
        api_key=api_key,
        base_url=base_url,
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.4,
        timeout=90,
        reasoning_split=True,
    )


def generate_text(system_prompt: str, user_prompt: str) -> tuple[str | None, str | None]:
    return generate_text_from_settings(load_settings(), system_prompt, user_prompt)


def test_connection(settings: dict) -> tuple[bool, str]:
    demo_mode = settings.get("demo_mode", True)
    if demo_mode:
        return True, "演示模式已开启：不会请求外部模型。"

    api_key = settings.get("api_key")
    base_url = settings.get("base_url")
    model = settings.get("model")
    if not api_key or not base_url or not model:
        return False, "缺少 live 模式所需配置。"

    content, error = _request_completion(
        api_key=api_key,
        base_url=base_url,
        model=model,
        system_prompt="你是连接测试助手。请只回复 OK。",
        user_prompt="请回复 OK。",
        temperature=0,
        timeout=20,
        reasoning_split=False,
        max_tokens=8,
    )
    if error:
        return False, f"外部模型连接失败：{error}"
    return True, f"外部模型连接成功，返回：{content}"
