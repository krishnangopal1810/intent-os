"""Token-aware HTTP client helpers for the local beta service."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from intentos.beta.service_security import API_TOKEN_HEADER


@dataclass(frozen=True)
class BetaHttpClient:
    base_url: str
    api_token: str
    origin: str | None = None
    timeout: float = 3

    def get_json(self, path: str) -> dict[str, Any]:
        with urlopen(self.request(path), timeout=self.timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"{path} returned non-object JSON")
        return payload

    def get_status(self, path: str, *, token: str | None = None, origin: str | None = None) -> int:
        try:
            with urlopen(
                self.request(path, token=token, origin=origin),
                timeout=self.timeout,
            ) as response:
                return response.status
        except HTTPError as exc:
            return exc.code

    def post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        with urlopen(self.post_request(path, payload), timeout=self.timeout) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(response_payload, dict):
            raise ValueError(f"{path} returned non-object JSON")
        return response_payload

    def post_status(
        self,
        path: str,
        payload: dict[str, Any],
        *,
        token: str | None = None,
        origin: str | None = None,
    ) -> int:
        try:
            with urlopen(
                self.post_request(path, payload, token=token, origin=origin),
                timeout=self.timeout,
            ) as response:
                return response.status
        except HTTPError as exc:
            return exc.code

    def request(
        self,
        path: str,
        *,
        token: str | None = None,
        origin: str | None = None,
    ) -> Request:
        return Request(self.url(path), headers=self.headers(token=token, origin=origin))

    def post_request(
        self,
        path: str,
        payload: dict[str, Any],
        *,
        token: str | None = None,
        origin: str | None = None,
    ) -> Request:
        return Request(
            self.url(path),
            data=json.dumps(payload).encode("utf-8"),
            headers=self.headers(
                {"Content-Type": "application/json"},
                token=token,
                origin=origin,
            ),
            method="POST",
        )

    def headers(
        self,
        extra: dict[str, str] | None = None,
        *,
        token: str | None = None,
        origin: str | None = None,
    ) -> dict[str, str]:
        headers = dict(extra or {})
        request_token = self.api_token if token is None else token
        if request_token:
            headers[API_TOKEN_HEADER] = request_token
        request_origin = self.origin if origin is None else origin
        if request_origin:
            headers["Origin"] = request_origin
        return headers

    def url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return self.base_url.rstrip("/") + "/" + path.lstrip("/")


def get_json(base_url: str, path: str, api_token: str, *, origin: str | None = None) -> dict[str, Any]:
    return BetaHttpClient(base_url, api_token, origin=origin).get_json(path)


def post_json(
    base_url: str,
    path: str,
    payload: dict[str, Any],
    api_token: str,
    *,
    origin: str | None = None,
) -> dict[str, Any]:
    return BetaHttpClient(base_url, api_token, origin=origin).post_json(path, payload)
