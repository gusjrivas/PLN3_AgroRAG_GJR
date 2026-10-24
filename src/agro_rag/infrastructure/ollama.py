"""Local Ollama adapter. Runtime model must be explicitly configured and installed."""

import json
from typing import Any

import httpx

from agro_rag.application.query import Generation, UpstreamError
from agro_rag.infrastructure.generation_contract import FORMATS, PROMPTS


class OllamaModel:
    def __init__(self, client: httpx.AsyncClient, base_url: str, model: str) -> None:
        self.client, self.base_url, self.model = client, base_url.rstrip("/"), model

    async def ready(self) -> bool:
        try:
            response = await self.client.get(self.base_url + "/api/tags", timeout=3)
            response.raise_for_status()
            body = response.json()
            models = body.get("models") if isinstance(body, dict) else None
            return isinstance(models, list) and any(
                isinstance(item, dict) and item.get("name") == self.model for item in models
            )
        except (httpx.HTTPError, ValueError):
            return False

    async def generate(self, role: str, payload: dict[str, Any], timeout: float) -> Generation:
        content = json.dumps(payload, ensure_ascii=False)
        try:
            response = await self.client.post(
                self.base_url + "/api/chat",
                timeout=timeout,
                json={
                    "model": self.model,
                    "stream": False,
                    "format": FORMATS[role],
                    "options": {"temperature": 0, "num_predict": 768},
                    "messages": [
                        {"role": "system", "content": PROMPTS[role]},
                        {"role": "user", "content": content},
                    ],
                },
            )
            response.raise_for_status()
            body = response.json()
            output = body["message"]["content"]
            data = json.loads(output)
            if not isinstance(data, dict):
                raise ValueError("Expected object")
            estimated = "prompt_eval_count" not in body or "eval_count" not in body
            input_tokens = body.get("prompt_eval_count", len((PROMPTS[role] + content).encode()))
            output_tokens = body.get("eval_count", len(output.encode()))
            if type(input_tokens) is not int or type(output_tokens) is not int:
                raise ValueError("Invalid usage")
            return Generation(data, input_tokens, output_tokens, estimated)
        except httpx.TimeoutException as exc:
            raise TimeoutError("Proveedor excedió el tiempo") from exc
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise UpstreamError("Salida o conexión del modelo inválida") from exc
