from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Dict, Any

@dataclass(frozen=True)
class Generation:
    text: str
    usage: Dict[str, int] | None = None
    model: str | None = None
    provider: str | None = None

class Provider(Protocol):
    name: str
    def generate(self, prompt: str, *, temperature: float = 0.0,
                 max_tokens: int = 512, model: str | None = None,
                 **kwargs: Any) -> Generation: ...
