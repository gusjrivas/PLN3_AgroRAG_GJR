"""Container readiness probe with no shell or external command dependency."""

import httpx

from agro_rag.bootstrap.settings import Settings


def check_readiness(
    settings: Settings,
    *,
    transport: httpx.BaseTransport | None = None,
) -> bool:
    if settings.healthcheck_expected_status == "ready" and not settings.reader_key:
        return False
    headers = (
        {"X-API-Key": settings.reader_key}
        if settings.healthcheck_expected_status == "ready"
        else {}
    )
    try:
        with httpx.Client(timeout=5.0, trust_env=False, transport=transport) as client:
            response = client.get(settings.healthcheck_url, headers=headers)
            return response.status_code == 200 and response.json() == {
                "status": settings.healthcheck_expected_status
            }
    except (httpx.HTTPError, ValueError):
        return False


def main() -> int:
    return 0 if check_readiness(Settings()) else 1
