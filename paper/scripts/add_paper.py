#!/usr/bin/env python3
"""Add one arXiv paper to the library.

    python scripts/add_paper.py <arxiv_id> --topic <topic-folder> [--tier X]
           [--slug X] [--builds-on a,b] [--lab-refs a,b]

The sequence is: refuse an id already present in papers.yaml, query the arXiv
API for title, authors, and year, derive a slug from the title when one is not
given, download the PDF into the topic folder, verify it, and only then append
the entry to papers.yaml, create the note stubs if they are absent, and rerun
the index build. A download that fails verification is deleted rather than
left on disk in a half-checked state.

Every request to arXiv, whether to the API or to the PDF endpoint, goes
through the shared throttle in verify.py, which keeps at least three seconds
between requests.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import requests
    import yaml
except ImportError as exc:  # pragma: no cover - environment dependent
    missing = {"requests": "requests", "yaml": "pyyaml"}
    name = getattr(exc, "name", "") or ""
    package = missing.get(name.split(".")[0], name)
    print(f"Missing dependency: {package}", file=sys.stderr)
    print(f"Install it with: pip install {package}", file=sys.stderr)
    raise SystemExit(2) from exc

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify import (  # noqa: E402
    ArxivError,
    PAPERS_YAML,
    ROOT,
    USER_AGENT,
    fetch_arxiv_metadata,
    load_papers,
    normalize,
    pdf_path_for,
    record_result,
    throttle,
    verify_paper,
)

PDF_URL = "https://arxiv.org/pdf/{arxiv_id}"

# The order keys are written in every entry of papers.yaml.
KEY_ORDER = [
    "arxiv_id",
    "slug",
    "title",
    "authors",
    "year",
    "primary_topic",
    "also_relevant_to",
    "tier",
    "builds_on",
    "extended_by",
    "related",
    "lab_refs",
    "status",
]

VALID_TOPICS = [
    "01-reasoning",
    "02-acting-and-tools",
    "03-self-correction",
    "04-memory-and-retrieval",
    "05-multi-agent",
    "06-environment-and-interface",
    "07-evaluation",
]
VALID_TIERS = ["core", "deep", "reference"]

STOPWORDS = {"a", "an", "the", "of", "for", "with", "in", "on", "and", "to", "via"}


def slug_from_title(title: str) -> str:
    """Derive a short kebab-case slug from a title.

    Prefers the part before a colon, which for this kind of paper is almost
    always the system name, and otherwise falls back to the leading content
    words of the title.
    """
    head = title.split(":")[0] if ":" in title else title
    words = [w for w in normalize(head).split() if w not in STOPWORDS]
    if not words:
        words = normalize(title).split()[:4]
    return "-".join(words[:4]) or "paper"


def split_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def read_yaml_document() -> tuple[str, list[dict]]:
    """Return the leading comment header of papers.yaml and its paper list."""
    text = PAPERS_YAML.read_text(encoding="utf-8")
    header_lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("#") or not line.strip():
            header_lines.append(line)
            continue
        break
    header = "\n".join(header_lines).rstrip() + "\n\n"
    data = yaml.safe_load(text) or {}
    return header, data.get("papers") or []


def ordered_entry(entry: dict) -> dict:
    """Rebuild one entry with the canonical key order."""
    return {key: entry.get(key, _default_for(key)) for key in KEY_ORDER}


def _default_for(key: str):
    if key in {"authors", "also_relevant_to", "builds_on", "extended_by", "related", "lab_refs"}:
        return []
    if key == "year":
        return None
    if key == "status":
        return "unread"
    return ""


def write_yaml_document(header: str, papers: list[dict]) -> None:
    """Write papers.yaml, preserving the header comment and the key order."""
    body = yaml.dump(
        {"papers": [ordered_entry(entry) for entry in papers]},
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=100,
    )
    PAPERS_YAML.write_text(header + body, encoding="utf-8")


NOTE_HEADINGS_EN = [
    "Core ideas",
    "What problem it solves",
    "Limitations",
    "What it leads to next",
    "Connection to the lab",
]
NOTE_HEADINGS_KO = [
    "핵심 아이디어",
    "무엇을 해결하는가",
    "한계",
    "다음으로 이어지는 것",
    "lab과의 연결",
]


def note_stub(entry: dict, lang: str) -> str:
    """Build an empty note stub. Nothing is filled in but the title and link."""
    headings = NOTE_HEADINGS_EN if lang == "en" else NOTE_HEADINGS_KO
    lines = [
        f"# {entry['title']}",
        "",
        f"<https://arxiv.org/abs/{entry['arxiv_id']}>",
        "",
    ]
    for heading in headings:
        lines += [f"## {heading}", "", ""]
    return "\n".join(lines).rstrip() + "\n"


def create_note_stubs(entry: dict) -> tuple[list[str], list[str]]:
    """Create the two note stubs when absent. Returns (created, skipped)."""
    base = ROOT / "topics" / entry["primary_topic"] / "notes"
    base.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    skipped: list[str] = []
    for lang, suffix in (("en", ".md"), ("ko", ".ko.md")):
        path = base / f"{entry['arxiv_id']}-{entry['slug']}{suffix}"
        relative = str(path.relative_to(ROOT))
        if path.exists():
            skipped.append(relative)
            continue
        path.write_text(note_stub(entry, lang), encoding="utf-8")
        created.append(relative)
    return created, skipped


def download_pdf(arxiv_id: str, destination: Path, *, timeout: int = 60) -> None:
    """Download one PDF from arXiv, honouring the shared request throttle."""
    throttle()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(
        PDF_URL.format(arxiv_id=arxiv_id),
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
        stream=True,
        allow_redirects=True,
    ) as response:
        response.raise_for_status()
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 256):
                if chunk:
                    handle.write(chunk)


def rerun_build_index() -> int:
    import build_index

    return build_index.main([])


def add_paper(
    arxiv_id: str,
    topic: str,
    *,
    tier: str = "deep",
    slug: str | None = None,
    builds_on: list[str] | None = None,
    lab_refs: list[str] | None = None,
    also_relevant_to: list[str] | None = None,
    extended_by: list[str] | None = None,
    related: list[str] | None = None,
) -> int:
    header, papers = read_yaml_document()
    if any(entry["arxiv_id"] == arxiv_id for entry in papers):
        print(f"Refusing: {arxiv_id} is already listed in papers.yaml", file=sys.stderr)
        return 1
    if topic not in VALID_TOPICS:
        print(f"Refusing: {topic} is not one of {', '.join(VALID_TOPICS)}", file=sys.stderr)
        return 1
    if tier not in VALID_TIERS:
        print(f"Refusing: tier must be one of {', '.join(VALID_TIERS)}", file=sys.stderr)
        return 1

    try:
        metadata = fetch_arxiv_metadata(arxiv_id)
    except (ArxivError, requests.RequestException) as exc:
        print(f"Failed: could not fetch metadata for {arxiv_id}: {exc}", file=sys.stderr)
        return 1

    entry = {
        "arxiv_id": arxiv_id,
        "slug": slug or slug_from_title(metadata["title"]),
        "title": metadata["title"],
        "authors": metadata["authors"],
        "year": metadata["year"],
        "primary_topic": topic,
        "also_relevant_to": also_relevant_to or [],
        "tier": tier,
        "builds_on": builds_on or [],
        "extended_by": extended_by or [],
        "related": related or [],
        "lab_refs": lab_refs or [],
        "status": "unread",
    }

    destination = pdf_path_for(entry)
    if destination.exists():
        print(f"Refusing: {destination.relative_to(ROOT)} already exists", file=sys.stderr)
        return 1

    print(f"Downloading {arxiv_id} to {destination.relative_to(ROOT)}")
    try:
        download_pdf(arxiv_id, destination)
    except requests.RequestException as exc:
        if destination.exists():
            destination.unlink()
        print(f"Failed: download error for {arxiv_id}: {exc}", file=sys.stderr)
        return 1

    result = verify_paper(arxiv_id, destination, entry["title"], slug=entry["slug"])
    if result.status == "FAIL":
        destination.unlink(missing_ok=True)
        print(f"Failed: {arxiv_id} did not verify, the partial file was deleted", file=sys.stderr)
        for reason in result.reasons:
            print(f"  - {reason}", file=sys.stderr)
        return 1
    record_result(result)
    print(f"Verified {arxiv_id}: {result.status} ({result.size_bytes} bytes)")

    papers.append(entry)
    write_yaml_document(header, papers)
    created, skipped = create_note_stubs(entry)
    for path in created:
        print(f"created note stub {path}")
    for path in skipped:
        print(f"left existing note stub alone {path}")

    print("Rebuilding the index")
    rerun_build_index()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Add one arXiv paper to the library.")
    parser.add_argument("arxiv_id", help="bare arXiv id, for example 2210.03629")
    parser.add_argument("--topic", required=True, choices=VALID_TOPICS)
    parser.add_argument("--tier", default="deep", choices=VALID_TIERS)
    parser.add_argument("--slug", default=None)
    parser.add_argument("--builds-on", default="", help="comma separated arXiv ids")
    parser.add_argument("--lab-refs", default="", help="comma separated lab folder names")
    parser.add_argument("--also-relevant-to", default="", help="comma separated topic folders")
    parser.add_argument("--extended-by", default="", help="comma separated arXiv ids")
    parser.add_argument("--related", default="", help="comma separated arXiv ids")
    args = parser.parse_args(argv)

    return add_paper(
        args.arxiv_id,
        args.topic,
        tier=args.tier,
        slug=args.slug,
        builds_on=split_list(args.builds_on),
        lab_refs=split_list(args.lab_refs),
        also_relevant_to=split_list(args.also_relevant_to),
        extended_by=split_list(args.extended_by),
        related=split_list(args.related),
    )


if __name__ == "__main__":
    raise SystemExit(main())
