from __future__ import annotations
import hashlib, textwrap
from .base import Generation

class MockProvider:
    name = "mock"
    def generate(self, prompt: str, *, temperature: float = 0.0,
                 max_tokens: int = 256, model: str | None = None, **kwargs):
        h = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        verdict = ["affirm", "deny", "unclear"][int(h[:2], 16) % 3]
        body = textwrap.shorten(prompt.replace("\n", " "), width=max_tokens, placeholder="…")
        return Generation(text=f"[{verdict}] {body}",
                          usage={"mock": len(prompt)}, model="mock-1", provider=self.name)
