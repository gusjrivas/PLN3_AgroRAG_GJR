"""Process liveness is deliberately independent of provider readiness."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok"}
