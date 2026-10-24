"""HTTP-only frontend boundary; never imports backend internals."""

from typing import Any

import httpx


class ApiError(Exception):
    pass


SAFE_API_ERRORS = {
    "NOT_READY": ("Respuesta verificada no disponible: el corpus o modelo no está configurado."),
    "DEADLINE": "El modelo tardó demasiado. Volvé a intentar la consulta.",
    "MODEL_INVALID": "El modelo no produjo una respuesta válida. Reformulá la consulta.",
    "MODEL_UNAVAILABLE": (
        "El proveedor del modelo no tiene disponibilidad, cuota o acceso. "
        "Revisá la configuración de la API."
    ),
    "RETRIEVAL_UNAVAILABLE": "La recuperación de fuentes no está disponible temporalmente.",
    "BUSY": "Hay dos consultas en curso. Esperá un momento y volvé a intentar.",
    "BUDGET": "La consulta superó el presupuesto permitido. Probá con una pregunta más breve.",
}


def safe_api_error(response: httpx.Response) -> str:
    try:
        body = response.json()
        error_body = body.get("error", body.get("detail", {}).get("error"))
        code = error_body.get("code")
    except (AttributeError, ValueError, TypeError):
        code = None
    if isinstance(code, str) and code in SAFE_API_ERRORS:
        return SAFE_API_ERRORS[code]
    return f"Servicio no disponible o solicitud rechazada ({response.status_code})."


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
            raise ApiError(safe_api_error(exc.response)) from exc
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
