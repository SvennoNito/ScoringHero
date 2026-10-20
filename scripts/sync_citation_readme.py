"""Regenerate the APA citation line in README.md from CITATION.cff.

Run after CITATION.cff changes (CI does this on push); exits 1 if README was
out of date so CI can fail/fix in the same step.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CFF_PATH = ROOT / "CITATION.cff"
README_PATH = ROOT / "README.md"

START = "<!-- CITATION:START -->"
END = "<!-- CITATION:END -->"


def apa_citation(cff: dict) -> str:
    authors = []
    for a in cff["authors"]:
        family = a["family-names"]
        initials = "".join(f"{p[0]}." for p in a["given-names"].split())
        authors.append(f"{family}, {initials}")
    if len(authors) == 1:
        author_str = authors[0]
    elif len(authors) == 2:
        author_str = " & ".join(authors)
    else:
        author_str = ", ".join(authors[:-1]) + ", & " + authors[-1]

    year = cff["date-released"].split("-")[0]
    title = cff["title"]
    version = cff["version"]
    doi = cff.get("doi")
    # APA software: publisher + DOI link when archived (Zenodo), else repository URL
    source = f"Zenodo. https://doi.org/{doi}" if doi else cff["repository-code"]

    return (
        f"> {author_str} ({year}). *{title}* (Version {version}) "
        f"[Computer software]. {source}"
    )


def main() -> int:
    cff = yaml.safe_load(CFF_PATH.read_text(encoding="utf-8"))
    citation = apa_citation(cff)

    readme = README_PATH.read_text(encoding="utf-8")
    pattern = re.compile(
        re.escape(START) + r"\n.*?\n" + re.escape(END), re.DOTALL
    )
    new_block = f"{START}\n{citation}\n{END}"
    if not pattern.search(readme):
        print("CITATION markers not found in README.md", file=sys.stderr)
        return 1

    new_readme = pattern.sub(new_block, readme)
    if new_readme == readme:
        print("README citation already up to date.")
        return 0

    README_PATH.write_text(new_readme, encoding="utf-8")
    print("README citation updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
