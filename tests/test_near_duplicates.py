"""scripts/near-duplicates.py flags pages that restate each other and stays quiet otherwise."""
from conftest import load

nd = load("near_duplicates", "scripts/near-duplicates.py")

SENT = ("The classifier reviews each action before it runs and blocks actions that escalate beyond "
        "your request or target infrastructure it does not recognize. ")


def write(tmp, folder, slug, title, body, aliases=""):
    d = tmp / "wiki" / folder
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{slug}.md").write_text(f"---\ntitle: {title}\naliases: [{aliases}]\n---\n{body}\n")


def test_shared_sentences_are_flagged(tmp_path):
    write(tmp_path, "using", "auto-mode", "Auto Mode", SENT * 3 + "Extra unique words about modes here.")
    write(tmp_path, "using", "classifier-notes", "Classifier Notes", SENT * 3 + "Different closing remarks entirely.")
    pairs = nd.find(str(tmp_path), 0.25)
    assert [(a, b) for _, a, b, _ in pairs] == [("auto-mode", "classifier-notes")]


def test_unrelated_pages_are_quiet(tmp_path):
    write(tmp_path, "using", "a", "Alpha", "Streaming responses arrive as server sent events over one connection per request made.")
    write(tmp_path, "using", "b", "Beta", "Worktrees give every background session a separate checkout so edits never collide with others.")
    assert nd.find(str(tmp_path), 0.25) == []


def test_alias_equal_to_other_slug_is_flagged(tmp_path):
    write(tmp_path, "using", "plugins", "Plugins", "One body about plugins and their manifests.")
    write(tmp_path, "extending", "plugin-guide", "Plugin Guide", "Totally different text about authoring.", aliases="plugins")
    assert nd.find(str(tmp_path), 0.9)
