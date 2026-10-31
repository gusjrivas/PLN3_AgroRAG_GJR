"""Small black-box adapter between garak REST and the AgroRAG gateway."""

from __future__ import annotations

import argparse
import json
import os
import ssl
from collections.abc import Callable, Mapping
from contextlib import AbstractContextManager
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from typing import Any, Literal, Protocol, cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener


class AdapterError(RuntimeError):
    """A deliberately sanitized target failure."""


class _Readable(Protocol):
    def read(self) -> bytes: ...


Transport = Callable[[Request, float], AbstractContextManager[_Readable]]
Outcome = Literal["success", "contract_rejected", "budget_exhausted", "error"]
ResultObserver = Callable[[Outcome], None]
CONTRACT_REJECTION_TEXT = "La entrada fue rechazada por el contrato público de la API."
BUDGET_EXHAUSTED_TEXT = "El presupuesto máximo de la prueba fue alcanzado."
HARD_MAX_COST_NANO_USD = 200_000_000
INPUT_NANO_USD_PER_TOKEN = 2_500
OUTPUT_NANO_USD_PER_TOKEN = 10_000
MAX_QUERY_TOKENS = 12_000
QUERY_RESERVATION_NANO_USD = MAX_QUERY_TOKENS * max(
    INPUT_NANO_USD_PER_TOKEN, OUTPUT_NANO_USD_PER_TOKEN
)


class AdapterStats:
    def __init__(self, max_cost_nano_usd: int = HARD_MAX_COST_NANO_USD) -> None:
        self._lock = Lock()
        self._counts = {
            "success": 0,
            "contract_rejected": 0,
            "budget_exhausted": 0,
            "error": 0,
        }
        self._max_cost_nano_usd = max_cost_nano_usd
        self._spent_nano_usd = 0
        self._reserved_nano_usd = 0
        self._input_tokens = 0
        self._output_tokens = 0

    def record(self, outcome: Outcome) -> None:
        with self._lock:
            self._counts[outcome] += 1

    def reserve(self) -> bool:
        with self._lock:
            if (
                self._spent_nano_usd + self._reserved_nano_usd + QUERY_RESERVATION_NANO_USD
                > self._max_cost_nano_usd
            ):
                self._counts["budget_exhausted"] += 1
                return False
            self._reserved_nano_usd += QUERY_RESERVATION_NANO_USD
            return True

    def refund(self) -> None:
        with self._lock:
            self._reserved_nano_usd -= QUERY_RESERVATION_NANO_USD

    def charge_error(self) -> None:
        with self._lock:
            self._reserved_nano_usd -= QUERY_RESERVATION_NANO_USD
            self._spent_nano_usd += QUERY_RESERVATION_NANO_USD

    def settle(self, input_tokens: int, output_tokens: int) -> None:
        if input_tokens < 0 or output_tokens < 0:
            raise ValueError("invalid token usage")
        cost = input_tokens * INPUT_NANO_USD_PER_TOKEN + output_tokens * OUTPUT_NANO_USD_PER_TOKEN
        if cost > QUERY_RESERVATION_NANO_USD:
            raise ValueError("token usage exceeds reserved cost")
        with self._lock:
            self._reserved_nano_usd -= QUERY_RESERVATION_NANO_USD
            self._spent_nano_usd += cost
            self._input_tokens += input_tokens
            self._output_tokens += output_tokens

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            counts = dict(self._counts)
            counts.update(
                {
                    "input_tokens": self._input_tokens,
                    "output_tokens": self._output_tokens,
                    "spent_nano_usd": self._spent_nano_usd,
                    "reserved_nano_usd": self._reserved_nano_usd,
                    "max_cost_nano_usd": self._max_cost_nano_usd,
                }
            )
            counts["total"] = sum(self._counts.values())
        return counts


def _ignore_result(_outcome: Outcome) -> None:
    return


@dataclass(frozen=True)
class GatewayConfig:
    target_url: str
    authorization: str
    reader_key: str
    timeout_seconds: float = 60.0
    max_cost_usd: str = "0.20"

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
        _ = self.max_cost_nano_usd

    @property
    def max_cost_nano_usd(self) -> int:
        try:
            value = Decimal(self.max_cost_usd)
            nano_value = value * Decimal(1_000_000_000)
        except InvalidOperation as exc:
            raise ValueError("El presupuesto Garak es inválido") from exc
        if nano_value != nano_value.to_integral_value():
            raise ValueError("El presupuesto Garak es inválido")
        result = int(nano_value)
        if result <= 0 or result > HARD_MAX_COST_NANO_USD:
            raise ValueError("El presupuesto Garak debe estar entre USD 0 y USD 0,20")
        return result

    @classmethod
    def from_secret_files(
        cls,
        *,
        target_url: str,
        authorization_file: Path,
        reader_key_file: Path,
        timeout_seconds: float = 60.0,
        max_cost_usd: str = "0.20",
    ) -> GatewayConfig:
        return cls(
            target_url=target_url,
            authorization=_read_secret(authorization_file),
            reader_key=_read_secret(reader_key_file),
            timeout_seconds=timeout_seconds,
            max_cost_usd=max_cost_usd,
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
    return cast(AbstractContextManager[_Readable], opener.open(request, timeout=timeout))


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        return None


def generate(
    prompt: str,
    config: GatewayConfig,
    *,
    transport: Transport = _default_transport,
    on_result: ResultObserver = _ignore_result,
    stats: AdapterStats | None = None,
) -> str:
    if not isinstance(prompt, str) or not prompt:
        raise AdapterError("invalid prompt")
    if stats is not None and not stats.reserve():
        on_result("budget_exhausted")
        return BUDGET_EXHAUSTED_TEXT
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
        if exc.code == 422:
            if stats is not None:
                stats.refund()
                stats.record("contract_rejected")
            on_result("contract_rejected")
            return CONTRACT_REJECTION_TEXT
        if stats is not None:
            stats.charge_error()
            stats.record("error")
        on_result("error")
        raise AdapterError(f"gateway request failed (status={exc.code})") from None
    except (URLError, TimeoutError, OSError, ValueError):
        if stats is not None:
            stats.charge_error()
            stats.record("error")
        on_result("error")
        raise AdapterError("gateway request failed") from None

    answer = body.get("answer") if isinstance(body, dict) else None
    usage = body.get("usage") if isinstance(body, dict) else None
    input_tokens = usage.get("input_tokens") if isinstance(usage, dict) else None
    output_tokens = usage.get("output_tokens") if isinstance(usage, dict) else None
    if (
        not isinstance(answer, str)
        or not isinstance(input_tokens, int)
        or isinstance(input_tokens, bool)
        or not isinstance(output_tokens, int)
        or isinstance(output_tokens, bool)
    ):
        if stats is not None:
            stats.charge_error()
            stats.record("error")
        on_result("error")
        raise AdapterError("gateway response contract mismatch")
    if stats is not None:
        try:
            stats.settle(input_tokens, output_tokens)
        except ValueError:
            stats.charge_error()
            stats.record("error")
            on_result("error")
            raise AdapterError("gateway usage exceeds reserved budget") from None
        stats.record("success")
    on_result("success")
    if answer:
        return answer
    status = body.get("status")
    if status == "needs_clarification":
        return "La solicitud necesita aclaración antes de poder responderse."
    return "No hay evidencia suficiente para responder la solicitud."


class _AdapterServer(ThreadingHTTPServer):
    config: GatewayConfig
    stats: AdapterStats


class _Handler(BaseHTTPRequestHandler):
    server: _AdapterServer

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/metrics":
            self.send_error(404)
            return
        self._json(200, self.server.stats.snapshot())

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
            if not isinstance(prompt, str):
                raise AdapterError("invalid prompt")
            text = generate(prompt, self.server.config, stats=self.server.stats)
        except (AdapterError, ValueError) as exc:
            self._json(502, {"error": str(exc)})
            return
        self._json(200, {"text": text})

    def log_message(self, format: str, *args: Any) -> None:
        # Prompts and credentials must not enter runner logs.
        return

    def _json(self, status: int, body: Mapping[str, object]) -> None:
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
        max_cost_usd=os.getenv("AGRO_GARAK_MAX_COST_USD", "0.20"),
    )
    server = _AdapterServer((args.host, args.port), _Handler)
    server.config = config
    server.stats = AdapterStats(config.max_cost_nano_usd)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
