from __future__ import annotations
from typing import Dict, Callable
from .mock import MockProvider

_registry: Dict[str, Callable[[], object]] = {
    "mock": lambda: MockProvider(),
}

def get(name: str):
    key = name.lower().strip()
    if key not in _registry:
        raise KeyError(f"Unknown provider '{name}'. Available: {', '.join(sorted(_registry))}")
    return _registry[key]()
