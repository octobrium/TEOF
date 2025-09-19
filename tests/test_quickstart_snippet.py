import pathlib

from tools.snippets.render_quickstart import load_commands, render_markdown

ROOT = pathlib.Path(__file__).resolve().parents[1]
SNIPPET_PATH = ROOT / "docs" / "_generated" / "quickstart_snippet.md"
DOCS = [
    ROOT / "README.md",
    ROOT / ".github" / "AGENT_ONBOARDING.md",
    ROOT / "docs" / "AGENTS.md",
    ROOT / "docs" / "quickstart.md",
]


def test_generated_snippet_matches_render() -> None:
    payload = load_commands()
    expected = render_markdown(payload["commands"], payload["notes"]).strip()
    actual = SNIPPET_PATH.read_text(encoding="utf-8").strip()
    assert actual == expected


def test_docs_embed_snippet() -> None:
    snippet = SNIPPET_PATH.read_text(encoding="utf-8").strip()
    for doc in DOCS:
        content = doc.read_text(encoding="utf-8")
        assert snippet in content, f"Snippet not found in {doc}"
