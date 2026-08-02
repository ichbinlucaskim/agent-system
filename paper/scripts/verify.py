#!/usr/bin/env python3
"""Verify downloaded arXiv PDFs against the records in papers.yaml.

Four checks are run per paper:

1. magic bytes   the file begins with %PDF
2. size floor    at least 50 KB; anything smaller is flagged as suspect
3. metadata      the title returned by the arXiv API matches the title in
                 papers.yaml after normalization
4. content       a normalized substring of the title appears in the text of
                 page 1, extracted with pypdf

SHA256 and byte size are computed for every file. Any failed check marks the
paper FAIL, including the size floor: a file below the floor is reported as
FAIL with a reason naming it as suspect rather than being silently accepted.

Normalization lowercases, strips punctuation, collapses whitespace, and
transliterates a small set of Greek letters to their ASCII names, because at
least one title in this library is written with a Greek letter on arXiv and
with the ASCII spelling in papers.yaml. That transliteration is a documented
normalization step, not a way of forcing a match: every other difference still
fails the check.

Results are cached in .verify-cache.json at the library root so that
build_index.py can render MANIFEST.md without repeating the network calls.
Local facts such as SHA256 and byte size are always recomputed by
build_index.py rather than trusted from the cache.

Usage:
    python scripts/verify.py <arxiv_id> <pdf_path>
    python scripts/verify.py --all
    python scripts/verify.py --all --offline
    python scripts/verify.py --all --json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

try:
    import requests
    import yaml
    from pypdf import PdfReader
except ImportError as exc:  # pragma: no cover - environment dependent
    missing = {"requests": "requests", "yaml": "pyyaml", "pypdf": "pypdf"}
    name = getattr(exc, "name", "") or ""
    package = missing.get(name.split(".")[0], name)
    print(f"Missing dependency: {package}", file=sys.stderr)
    print(f"Install it with: pip install {package}", file=sys.stderr)
    raise SystemExit(2) from exc

ROOT = Path(__file__).resolve().parent.parent
PAPERS_YAML = ROOT / "papers.yaml"
CACHE_PATH = ROOT / ".verify-cache.json"

ARXIV_API = "http://export.arxiv.org/api/query"
ATOM = "{http://www.w3.org/2005/Atom}"
MIN_BYTES = 50 * 1024
REQUEST_INTERVAL_S = 3.0
USER_AGENT = "agent-system-paper-library/1.0 (personal study library)"

# Titles on arXiv occasionally use a Greek letter where an ASCII spelling is
# more practical for a filename or a YAML record. Transliterate the few that
# turn up rather than special-casing one paper.
GREEK_TRANSLITERATION = {
    "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta",
    "ε": "epsilon", "ζ": "zeta", "η": "eta", "θ": "theta",
    "ι": "iota", "κ": "kappa", "λ": "lambda", "μ": "mu",
    "ν": "nu", "ξ": "xi", "π": "pi", "ρ": "rho",
    "σ": "sigma", "τ": "tau", "υ": "upsilon", "φ": "phi",
    "χ": "chi", "ψ": "psi", "ω": "omega",
}

_last_request_at: float | None = None


def throttle() -> None:
    """Ensure at least REQUEST_INTERVAL_S between two arXiv requests."""
    global _last_request_at
    if _last_request_at is not None:
        elapsed = time.monotonic() - _last_request_at
        if elapsed < REQUEST_INTERVAL_S:
            time.sleep(REQUEST_INTERVAL_S - elapsed)
    _last_request_at = time.monotonic()


def normalize(text: str) -> str:
    """Lowercase, transliterate Greek, drop punctuation, collapse whitespace."""
    text = unicodedata.normalize("NFKC", text or "")
    text = "".join(GREEK_TRANSLITERATION.get(ch, ch) for ch in text.lower())
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def title_probe(title: str, words: int = 6) -> str:
    """A normalized leading substring of a title, used for the content check.

    Page 1 text extraction breaks lines unpredictably, so matching the whole
    title is brittle. A leading run of words is specific enough to identify the
    paper and robust enough to survive extraction.
    """
    return " ".join(normalize(title).split()[:words])


def compact(text: str) -> str:
    """Normalize and then remove spaces entirely.

    Titles set in small caps extract with a space after the leading glyph of a
    word: ReAct comes back as 'reac t s ynergizing', SWE-bench as 'swe bench
    c an'. Word boundaries in extracted PDF text are not trustworthy, so the
    page 1 content check compares with spacing removed on both sides. The probe
    is still a long specific run of title characters, so this tolerates a
    rendering artifact without weakening what is being checked.
    """
    return normalize(text).replace(" ", "")


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class ArxivError(RuntimeError):
    """Raised when the arXiv API cannot be queried or returns no usable entry."""


def fetch_arxiv_metadata(arxiv_id: str, *, timeout: int = 30) -> dict:
    """Query the arXiv API for one id and return title, authors, and year."""
    throttle()
    response = requests.get(
        ARXIV_API,
        params={"id_list": arxiv_id, "max_results": 1},
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    root = ElementTree.fromstring(response.text)
    entry = root.find(f"{ATOM}entry")
    if entry is None:
        raise ArxivError(f"no entry returned for {arxiv_id}")
    entry_id = (entry.findtext(f"{ATOM}id") or "").strip()
    if "api/errors" in entry_id:
        reason = (entry.findtext(f"{ATOM}summary") or "unknown error").strip()
        raise ArxivError(f"arXiv reported an error for {arxiv_id}: {reason}")
    title = " ".join((entry.findtext(f"{ATOM}title") or "").split())
    authors = [
        " ".join((node.findtext(f"{ATOM}name") or "").split())
        for node in entry.findall(f"{ATOM}author")
    ]
    published = (entry.findtext(f"{ATOM}published") or "").strip()
    year = int(published[:4]) if published[:4].isdigit() else 0
    if not title:
        raise ArxivError(f"empty title returned for {arxiv_id}")
    return {
        "arxiv_id": arxiv_id,
        "title": title,
        "authors": [name for name in authors if name],
        "year": year,
        "published": published,
    }


def page_one_text(path: Path) -> str:
    """Extract the text of page 1, returning an empty string on failure."""
    try:
        reader = PdfReader(str(path))
        if not reader.pages:
            return ""
        return reader.pages[0].extract_text() or ""
    except Exception:
        # A PDF that cannot be parsed fails the content check; the reason is
        # recorded by the caller rather than raised here.
        return ""


@dataclass
class VerifyResult:
    """The outcome of verifying one paper."""

    arxiv_id: str
    slug: str = ""
    path: str = ""
    exists: bool = False
    magic_ok: bool = False
    size_ok: bool = False
    size_bytes: int = 0
    sha256: str = ""
    metadata_ok: bool | None = None
    api_title: str = ""
    content_ok: bool = False
    status: str = "FAIL"
    reasons: list[str] = field(default_factory=list)
    verified_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def verify_paper(
    arxiv_id: str,
    pdf_path: Path,
    expected_title: str,
    *,
    slug: str = "",
    offline: bool = False,
) -> VerifyResult:
    """Run all four checks against one file and return a structured result."""
    result = VerifyResult(
        arxiv_id=arxiv_id,
        slug=slug,
        path=str(pdf_path.relative_to(ROOT)) if pdf_path.is_relative_to(ROOT)
        else str(pdf_path),
        verified_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )

    if not pdf_path.is_file():
        result.reasons.append("file is missing")
        result.status = "FAIL"
        return result
    result.exists = True

    # Check 1: magic bytes.
    with pdf_path.open("rb") as handle:
        header = handle.read(4)
    result.magic_ok = header == b"%PDF"
    if not result.magic_ok:
        result.reasons.append(f"does not begin with %PDF (saw {header!r})")

    # Check 2: size floor.
    result.size_bytes = pdf_path.stat().st_size
    result.size_ok = result.size_bytes >= MIN_BYTES
    if not result.size_ok:
        result.reasons.append(
            f"suspect: {result.size_bytes} bytes is below the "
            f"{MIN_BYTES} byte floor"
        )

    result.sha256 = sha256_of(pdf_path)

    # Check 3: metadata match against the arXiv API.
    if offline:
        result.metadata_ok = None
        result.reasons.append("metadata check skipped (offline)")
    else:
        try:
            metadata = fetch_arxiv_metadata(arxiv_id)
        except (ArxivError, requests.RequestException) as exc:
            result.metadata_ok = False
            result.reasons.append(f"metadata lookup failed: {exc}")
        else:
            result.api_title = metadata["title"]
            result.metadata_ok = normalize(metadata["title"]) == normalize(
                expected_title
            )
            if not result.metadata_ok:
                result.reasons.append(
                    f"title mismatch: arXiv says {metadata['title']!r}, "
                    f"papers.yaml says {expected_title!r}"
                )

    # Check 4: content match on page 1, compared with spacing removed because
    # small-caps titles extract with spurious spaces inside words.
    probe = title_probe(expected_title)
    extracted = compact(page_one_text(pdf_path))
    result.content_ok = bool(probe) and compact(probe) in extracted
    if not result.content_ok:
        result.reasons.append(
            f"page 1 text does not contain the title probe {probe!r}"
        )

    failed = (
        not result.magic_ok
        or not result.size_ok
        or not result.content_ok
        or result.metadata_ok is False
    )
    if failed:
        result.status = "FAIL"
    elif result.metadata_ok is None:
        result.status = "PARTIAL"
    else:
        result.status = "PASS"
    return result


def load_papers() -> list[dict]:
    if not PAPERS_YAML.is_file():
        raise SystemExit(f"papers.yaml not found at {PAPERS_YAML}")
    data = yaml.safe_load(PAPERS_YAML.read_text(encoding="utf-8")) or {}
    return data.get("papers") or []


def pdf_path_for(entry: dict) -> Path:
    return (
        ROOT
        / "topics"
        / entry["primary_topic"]
        / "pdf"
        / f"{entry['arxiv_id']}-{entry['slug']}.pdf"
    )


def load_cache() -> dict:
    if not CACHE_PATH.is_file():
        return {}
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_cache(cache: dict) -> None:
    CACHE_PATH.write_text(
        json.dumps(cache, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def record_result(result: VerifyResult) -> None:
    """Merge one result into the on-disk cache."""
    cache = load_cache()
    cache[result.arxiv_id] = result.to_dict()
    save_cache(cache)


def format_row(result: VerifyResult) -> str:
    marks = "".join(
        [
            "M" if result.magic_ok else "-",
            "S" if result.size_ok else "-",
            "A" if result.metadata_ok else ("?" if result.metadata_ok is None else "-"),
            "C" if result.content_ok else "-",
        ]
    )
    return (
        f"{result.status:<8}{result.arxiv_id:<12}{marks:<6}"
        f"{result.size_bytes:>10}  {result.slug}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify downloaded arXiv PDFs against papers.yaml."
    )
    parser.add_argument("arxiv_id", nargs="?", help="bare arXiv id, for example 2210.03629")
    parser.add_argument("pdf_path", nargs="?", help="path to the PDF to check")
    parser.add_argument("--all", action="store_true", help="verify every paper on disk")
    parser.add_argument(
        "--offline", action="store_true", help="skip the arXiv metadata check"
    )
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    args = parser.parse_args(argv)

    papers = load_papers()
    by_id = {entry["arxiv_id"]: entry for entry in papers}

    if args.all:
        targets = [(entry, pdf_path_for(entry)) for entry in papers]
    else:
        if not args.arxiv_id or not args.pdf_path:
            parser.error("give an arxiv_id and a pdf path, or use --all")
        entry = by_id.get(args.arxiv_id)
        if entry is None:
            print(f"{args.arxiv_id} is not listed in papers.yaml", file=sys.stderr)
            return 2
        targets = [(entry, Path(args.pdf_path).resolve())]

    results = []
    cache = load_cache()
    for entry, path in targets:
        result = verify_paper(
            entry["arxiv_id"],
            path,
            entry["title"],
            slug=entry.get("slug", ""),
            offline=args.offline,
        )
        results.append(result)
        cache[result.arxiv_id] = result.to_dict()
    save_cache(cache)

    if args.json:
        print(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        print(f"{'status':<8}{'arxiv id':<12}{'checks':<6}{'bytes':>10}  slug")
        print("-" * 60)
        for result in results:
            print(format_row(result))
        failures = [r for r in results if r.status == "FAIL"]
        print("-" * 60)
        print(
            f"{len(results)} checked, {len(results) - len(failures)} passing, "
            f"{len(failures)} failing"
        )
        for result in failures:
            print(f"\nFAIL {result.arxiv_id} {result.slug}")
            for reason in result.reasons:
                print(f"  - {reason}")

    return 1 if any(r.status == "FAIL" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
