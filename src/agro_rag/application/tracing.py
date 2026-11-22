"""Request-scoped instrumentation port for query stages."""

from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager, nullcontext
from contextvars import ContextVar
from typing import Literal

Stage = Literal["retrieval", "researcher", "verifier"]
StageTracer = Callable[[Stage], AbstractContextManager[None]]
_stage_tracer: ContextVar[StageTracer | None] = ContextVar("query_stage_tracer", default=None)


@contextmanager
def bind_stage_tracer(tracer: StageTracer) -> Iterator[None]:
    token = _stage_tracer.set(tracer)
    try:
        yield
    finally:
        _stage_tracer.reset(token)


def trace_stage(stage: Stage) -> AbstractContextManager[None]:
    tracer = _stage_tracer.get()
    return tracer(stage) if tracer is not None else nullcontext()
