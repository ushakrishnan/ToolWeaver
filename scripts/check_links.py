import re
import sys
from collections.abc import Iterable
from pathlib import Path

import requests

MD_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def find_markdown_files(root: Path) -> Iterable[Path]:
    yield from root.rglob("*.md")


def extract_links(text: str) -> list[str]:
    links = []
    for m in MD_LINK_PATTERN.finditer(text):
        url = m.group(1).strip()
        # Skip anchors and relative links
        if url.startswith("#"):
            continue
        if url.startswith("http://") or url.startswith("https://"):
            links.append(url)
    return links


def check_link(url: str, timeout: float = 8.0) -> tuple[str, bool, int | None, str | None]:
    try:
        resp = requests.head(url, allow_redirects=True, timeout=timeout)
        status = resp.status_code
        if 200 <= status < 400:
            return url, True, status, None
        # Fallback to GET for servers that don't support HEAD
        resp = requests.get(url, allow_redirects=True, timeout=timeout, stream=True)
        status = resp.status_code
        if 200 <= status < 400:
            return url, True, status, None
        return url, False, status, None
    except requests.RequestException as e:
        return url, False, None, str(e)


def main() -> int:
    docs_dir = Path("docs")
    if not docs_dir.exists():
        print("docs/ directory not found")
        return 2

    all_links: list[str] = []
    for md in find_markdown_files(docs_dir):
        try:
            text = md.read_text(encoding="utf-8")
        except Exception:
            continue
        all_links.extend(extract_links(text))

    # De-duplicate
    uniq_links = sorted(set(all_links))

    broken: list[tuple[str, int | None, str | None]] = []
    for url in uniq_links:
        url, ok, status, err = check_link(url)
        if not ok:
            broken.append((url, status, err))

    if not broken:
        print(f"✓ All {len(uniq_links)} external links look good.")
        return 0

    print(f"❌ Found {len(broken)} broken/unstable links (of {len(uniq_links)} checked):")
    for url, status, err in broken:
        status_str = str(status) if status is not None else "N/A"
        err_str = f" — {err}" if err else ""
        print(f"- {url} (status: {status_str}){err_str}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
