"""Small black-box adapter between garak REST and the AgroRAG gateway."""

from __future__ import annotations

import argparse
import json
import os
import ssl
from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener


class AdapterError(RuntimeError):
    """A deliberately sanitized target failure."""


class _Readable(Protocol):
    def read(self) -> bytes: ...


Transport = Callable[[Request, float], AbstractContextManager[_Readable]]


@dataclass(frozen=True)
class GatewayConfig:
    target_url: str
    authorization: str
    reader_key: str
    timeout_seconds: float = 60.0

    def __post_init__(self) -> None:
        parsed = urlparse(self.target_url)
        if (
            parsed.scheme != "https"
            or not parsed.netloc
            or parsed.username is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("El target Garak debe ser una URL HTTPS absoluta")
        if parsed.path != "/v1/query":
            raise ValueError("El target Garak debe terminar en /v1/query")
        if not self.authorization.startswith("Basic ") or not self.reader_key:
            raise ValueError("Credenciales Garak inválidas")
        if self.timeout_seconds <= 0:
            raise ValueError("Timeout Garak inválido")

    @classmethod
    def from_secret_files(
        cls,
        *,
        target_url: str,
        authorization_file: Path,
        reader_key_file: Path,
        timeout_seconds: float = 60.0,
    ) -> GatewayConfig:
        return cls(
            target_url=target_url,
            authorization=_read_secret(authorization_file),
            reader_key=_read_secret(reader_key_file),
            timeout_seconds=timeout_seconds,
        )


def _read_secret(path: Path) -> str:
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ValueError(f"No se pudo leer el secreto requerido: {path.name}") from exc
    if not value:
        raise ValueError(f"El secreto requerido está vacío: {path.name}")
    return value


def _default_transport(request: Request, timeout: float) -> AbstractContextManager[_Readable]:
    context = ssl.create_default_context()
    opener = build_opener(HTTPSHandler(context=context), _NoRedirect())
    return opener.open(request, timeout=timeout)


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        return None


def generate(
    prompt: str,
    config: GatewayConfig,
    *,
    transport: Transport = _default_transport,
) -> str:
    if not isinstance(prompt, str) or not prompt:
        raise AdapterError("invalid prompt")
    request = Request(
        config.target_url,
        data=json.dumps({"question": prompt}).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Authorization": config.authorization,
            "Content-Type": "application/json",
            "X-API-Key": config.reader_key,
        },
        method="POST",
    )
    try:
        with transport(request, config.timeout_seconds) as response:
            body = json.loads(response.read())
    except HTTPError as exc:
        raise AdapterError(f"gateway request failed (status={exc.code})") from None
    except (URLError, TimeoutError, OSError, ValueError):
        raise AdapterError("gateway request failed") from None

    answer = body.get("answer") if isinstance(body, dict) else None
    if not isinstance(answer, str):
        raise AdapterError("gateway response contract mismatch")
    if answer:
        return answer
    status = body.get("status")
    if status == "needs_clarification":
        return "La solicitud necesita aclaración antes de poder responderse."
    return "No hay evidencia suficiente para responder la solicitud."


class _AdapterServer(ThreadingHTTPServer):
    config: GatewayConfig


class _Handler(BaseHTTPRequestHandler):
    server: _AdapterServer

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/generate":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 64 * 1024:
                raise AdapterError("invalid request")
            payload = json.loads(self.rfile.read(length))
            prompt = payload.get("prompt") if isinstance(payload, dict) else None
            text = generate(prompt, self.server.config)
        except (AdapterError, ValueError) as exc:
            self._json(502, {"error": str(exc)})
            return
        self._json(200, {"text": text})

    def log_message(self, format: str, *args: Any) -> None:
        # Prompts and credentials must not enter runner logs.
        return

    def _json(self, status: int, body: dict[str, str]) -> None:
        encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8090)
    args = parser.parse_args()
    config = GatewayConfig.from_secret_files(
        target_url=os.environ["AGRO_GARAK_TARGET_URL"],
        authorization_file=Path(
            os.getenv("AGRO_GATEWAY_AUTHORIZATION_FILE", "/run/secrets/gateway_authorization")
        ),
        reader_key_file=Path(os.getenv("AGRO_READER_KEY_FILE", "/run/secrets/reader_key")),
        timeout_seconds=float(os.getenv("AGRO_GARAK_TIMEOUT_SECONDS", "60")),
    )
    server = _AdapterServer((args.host, args.port), _Handler)
    server.config = config
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
