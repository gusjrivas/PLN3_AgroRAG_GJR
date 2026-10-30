"""OpenAI Responses API adapter with strict structured outputs."""

import json
from typing import Any
from urllib.parse import quote

import httpx

from agro_rag.application.query import Generation, ProviderUnavailable, UpstreamError
from agro_rag.infrastructure.generation_contract import FORMATS, PROMPTS


class OpenAIModel:
    def __init__(
        self,
        client: httpx.AsyncClient,
        base_url: str,
        api_key: str,
        model: str,
        *,
        max_output_tokens: int = 768,
    ) -> None:
        if not 1 <= max_output_tokens <= 768:
            raise ValueError("Límite de salida inválido")
        self.client = client
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.max_output_tokens = max_output_tokens

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    async def ready(self) -> bool:
        try:
            response = await self.client.get(
                f"{self.base_url}/models/{quote(self.model, safe='')}",
                headers=self.headers,
                timeout=5,
            )
            response.raise_for_status()
            body = response.json()
            return isinstance(body, dict) and body.get("id") == self.model
        except (httpx.HTTPError, ValueError):
            return False

    async def generate(self, role: str, payload: dict[str, Any], timeout: float) -> Generation:
        try:
            response = await self.client.post(
                self.base_url + "/responses",
                headers=self.headers,
                timeout=timeout,
                json={
                    "model": self.model,
                    "instructions": PROMPTS[role],
                    "input": json.dumps(payload, ensure_ascii=False),
                    "text": {
                        "format": {
                            "type": "json_schema",
                            "name": f"agrorag_{role}",
                            "strict": True,
                            "schema": FORMATS[role],
                        }
                    },
                    "max_output_tokens": self.max_output_tokens,
                    "temperature": 0,
                    "store": False,
                },
            )
            response.raise_for_status()
            body = response.json()
            output = self._output_text(body)
            data = json.loads(output)
            usage = body.get("usage")
            if not isinstance(data, dict) or not isinstance(usage, dict):
                raise ValueError("Invalid response")
            input_tokens = usage.get("input_tokens")
            output_tokens = usage.get("output_tokens")
            if type(input_tokens) is not int or type(output_tokens) is not int:
                raise ValueError("Invalid usage")
            return Generation(data, input_tokens, output_tokens)
        except httpx.TimeoutException as exc:
            raise TimeoutError("Proveedor excedió el tiempo") from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in {401, 403, 404, 429}:
                raise ProviderUnavailable("Proveedor de modelo no disponible") from exc
            raise UpstreamError("Salida o conexión del modelo inválida") from exc
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise UpstreamError("Salida o conexión del modelo inválida") from exc

    @staticmethod
    def _output_text(body: object) -> str:
        if not isinstance(body, dict) or body.get("status") != "completed":
            raise ValueError("Incomplete response")
        output = body.get("output")
        if not isinstance(output, list):
            raise ValueError("Missing output")
        for item in output:
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if isinstance(part, dict) and part.get("type") == "output_text":
                    text = part.get("text")
                    if isinstance(text, str):
                        return text
        raise ValueError("Missing structured output")
