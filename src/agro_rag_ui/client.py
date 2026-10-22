"""HTTP-only frontend boundary; never imports backend internals."""

from typing import Any

import httpx


class ApiError(Exception):
    pass


class ApiClient:
    def __init__(self, base_url: str, key: str, http: httpx.Client | None = None) -> None:
        self.base_url, self.key, self.http = base_url.rstrip("/"), key, http

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            if self.http is None:
                with httpx.Client(timeout=65, trust_env=False) as client:
                    response = client.request(
                        method, self.base_url + path, headers={"X-API-Key": self.key}, **kwargs
                    )
            else:
                response = self.http.request(
                    method, self.base_url + path, headers={"X-API-Key": self.key}, **kwargs
                )
            response.raise_for_status()
            body = response.json()
            if not isinstance(body, dict):
                raise ValueError("Expected object")
            return body
        except httpx.HTTPStatusError as exc:
            raise ApiError(
                f"Servicio no disponible o solicitud rechazada ({exc.response.status_code})."
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise ApiError("No se pudo obtener una respuesta válida del servicio.") from exc

    def search(self, question: str, crop: str | None) -> dict[str, Any]:
        params = {"question": question}
        if crop:
            params["crop"] = crop
        return self._request("GET", "/v1/preview/search", params=params)

    def query(
        self,
        question: str,
        crop: str | None,
        context: dict[str, Any],
        clarification: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/query",
            json={
                "question": question,
                "crop": crop,
                "context": context,
                "clarification_context": clarification,
            },
        )
