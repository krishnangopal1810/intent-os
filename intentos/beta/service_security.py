"""HTTP request security helpers for the local beta service."""

from __future__ import annotations

import hmac
import json
from http.client import HTTPMessage
from typing import Any


API_TOKEN_HEADER = "X-IntentOS-Token"
MAX_JSON_BODY_BYTES = 64 * 1024


def read_json(handler) -> dict[str, Any]:
    try:
        length = int(handler.headers.get("Content-Length") or "0")
    except ValueError as exc:
        raise ValueError("Content-Length must be an integer") from exc
    if length > MAX_JSON_BODY_BYTES:
        raise ValueError("request body is too large")
    raw = handler.rfile.read(length).decode("utf-8") if length else "{}"
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("request body must be a JSON object")
    return payload


def send_json(handler, payload: object, config, status: int = 200) -> None:
    data = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(data)))
    cors = cors_origin(handler.headers, config.allowed_origins)
    if cors:
        handler.send_header("Access-Control-Allow-Origin", cors)
        handler.send_header("Vary", "Origin")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", f"Content-Type, {API_TOKEN_HEADER}")
    handler.end_headers()
    handler.wfile.write(data)


def authorize_request(handler, config) -> bool:
    if not origin_allowed(handler.headers, config.allowed_origins):
        send_json(handler, {"error": "origin not allowed"}, config, status=403)
        return False
    if not config.api_token or not hmac.compare_digest(
        handler.headers.get(API_TOKEN_HEADER, ""),
        config.api_token,
    ):
        send_json(handler, {"error": "invalid IntentOS API token"}, config, status=403)
        return False
    return True


def origin_allowed(headers: HTTPMessage, allowed_origins: tuple[str, ...]) -> bool:
    origin = headers.get("Origin")
    if not origin:
        return True
    return origin in allowed_origins or origin.startswith("chrome-extension://")


def cors_origin(headers: HTTPMessage, allowed_origins: tuple[str, ...]) -> str | None:
    origin = headers.get("Origin")
    return origin if origin and origin_allowed(headers, allowed_origins) else None
