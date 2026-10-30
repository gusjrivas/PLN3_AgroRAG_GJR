import asyncio

from scripts.run_e3_cache import run_cache_trials


class FakeService:
    def __init__(self) -> None:
        self.calls = 0

    async def run(self, question, crop, context):
        self.calls += 1
        return {"usage": {"cache_hit": self.calls > 1}, "answer": question}


def test_eva_02_e3_records_three_cold_and_three_hot_trials() -> None:
    services = tuple(FakeService() for _ in range(3))

    rows = asyncio.run(run_cache_trials(services, question="riego", crop="lettuce"))

    assert [row["variant"] for row in rows] == ["cache_cold"] * 3 + ["cache_hot"] * 3
    assert [row["result"]["usage"]["cache_hit"] for row in rows] == [
        False,
        False,
        False,
        True,
        True,
        True,
    ]
