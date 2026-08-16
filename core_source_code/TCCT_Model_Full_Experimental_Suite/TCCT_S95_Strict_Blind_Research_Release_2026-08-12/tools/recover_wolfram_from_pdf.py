"""Recover Wolfram Language input cells from the S71 checkpoint PDF.

The PDF was exported by Wolfram and stores notebook brackets as font-specific
Unicode glyphs. This utility extracts In[n] cells, normalizes those glyphs, and
writes an auditable Wolfram Language source archive.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_PDF = ROOT / "docs" / "Blind Topology Transfer Checkpoint.pdf"
DEFAULT_OUTPUT = ROOT / "experiments" / "TCCT_S71_recovered_full.wl"

CELL_MARKER = re.compile(r"(?m)^(In\[(\d+)\]:=|Out\[(\d+)\]=)\s*")

GLYPH_MAP = str.maketrans(
    {
        "\uf00f": "[",
        "\uf015": "]",
        "\uf01c": "{",
        "\uf027": "}",
        "\uf113": "<|",
        "\uf114": "|>",
        "\uf0a7": "[[",
        "\uf0ad": "]]",
        "\u301a": "[[",
        "\u301b": "]]",
        "\uf000": "(",
        "\uf006": ")",
        "\uf00c": "/",
        "\u2192": "->",
        "\u29f4": ":>",
        "\u2a75": "==",
        "\u2264": "<=",
        "\u2265": ">=",
        "\u00d7": "*",
    }
)


def extract_pdf_text(source_pdf: Path) -> str:
    reader = PdfReader(source_pdf)
    pages: list[str] = []
    for page_number, page in enumerate(reader.pages, start=1):
        lines = (page.extract_text() or "").splitlines()
        lines = [line for line in lines if line.strip() != str(page_number)]
        pages.append("\n".join(lines))
    return "\n".join(pages)


def normalize(code: str) -> str:
    code = re.split(
        r"\n(?:KeyDrop: The argument|Correlation: The standard deviation)",
        code,
        maxsplit=1,
    )[0]
    code = code.translate(GLYPH_MAP)
    code = re.sub(r"(?<=\d)\s+(?=\d)", "", code)
    code = re.sub(
        r'"([^"\r\n]*)"',
        lambda match: f'"{match.group(1).strip()}"',
        code,
    )
    code = code.replace("\ufb00", "ff")
    code = code.replace("\u2013", "-").replace("\u2014", "-")
    return code.strip()


def input_cells(text: str) -> list[tuple[int, str]]:
    markers = list(CELL_MARKER.finditer(text))
    cells: list[tuple[int, str]] = []
    for index, marker in enumerate(markers):
        input_number = marker.group(2)
        if input_number is None:
            continue
        end = markers[index + 1].start() if index + 1 < len(markers) else len(text)
        cells.append((int(input_number), normalize(text[marker.end() : end])))
    return cells


def write_archive(cells: list[tuple[int, str]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    chunks = [
        "(* TCCT S71 - recovered input cells *)\n",
        "(* Source: Blind Topology Transfer Checkpoint.pdf *)\n",
        "(* Generated mechanically; original In[n] labels are preserved. *)\n\n",
    ]
    for number, code in cells:
        chunks.append(f"(* In[{number}] *)\n{code}\n\n")
    output.write_text("".join(chunks), encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_pdf", nargs="?", type=Path, default=DEFAULT_SOURCE_PDF)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    cells = input_cells(extract_pdf_text(args.source_pdf))
    write_archive(cells, args.output)
    print(f"Recovered {len(cells)} input cells")
    print(args.output)


if __name__ == "__main__":
    main()
