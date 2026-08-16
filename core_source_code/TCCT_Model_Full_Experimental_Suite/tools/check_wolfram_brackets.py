"""Lightweight structural check for recovered Wolfram Language source."""

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "wolfram" / "TCCT_S71_recovered_full.wl"
CELL = re.compile(r"(?m)^\(\* In\[(\d+)\] \*\)\s*$")
PAIRS = {"]": "[", "}": "{", ")": "("}


def bracket_error(code: str) -> str | None:
    stack: list[tuple[str, int]] = []
    index = 0
    string = False
    escape = False
    comment_depth = 0

    while index < len(code):
        current = code[index]
        following = code[index + 1] if index + 1 < len(code) else ""

        if comment_depth:
            if current == "(" and following == "*":
                comment_depth += 1
                index += 2
                continue
            if current == "*" and following == ")":
                comment_depth -= 1
                index += 2
                continue
            index += 1
            continue

        if string:
            if escape:
                escape = False
            elif current == "\\":
                escape = True
            elif current == '"':
                string = False
            index += 1
            continue

        if current == "(" and following == "*":
            comment_depth = 1
            index += 2
            continue
        if current == '"':
            string = True
            index += 1
            continue

        if current in "[{(":
            stack.append((current, index))
        elif current in "]})":
            if not stack or stack[-1][0] != PAIRS[current]:
                return f"unexpected {current!r} at offset {index}"
            stack.pop()
        index += 1

    if string:
        return "unterminated string"
    if comment_depth:
        return "unterminated comment"
    if stack:
        opener, offset = stack[-1]
        return f"unclosed {opener!r} at offset {offset}"
    return None


def main() -> None:
    sources = [Path(value) for value in sys.argv[1:]] or [SOURCE]
    failed = False

    for source in sources:
        text = source.read_text(encoding="utf-8")
        markers = list(CELL.finditer(text))
        errors = []

        if markers:
            for index, marker in enumerate(markers):
                end = markers[index + 1].start() if index + 1 < len(markers) else len(text)
                error = bracket_error(text[marker.end() : end])
                if error:
                    errors.append((f"In[{marker.group(1)}]", error))
            print(f"Checked {len(markers)} recovered cells in {source.name}")
        else:
            error = bracket_error(text)
            if error:
                errors.append((source.name, error))
            print(f"Checked {source.name}")

        if errors:
            failed = True
            for label, error in errors:
                print(f"{label}: {error}")
        else:
            print("Balanced brackets, strings, and comments")

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
