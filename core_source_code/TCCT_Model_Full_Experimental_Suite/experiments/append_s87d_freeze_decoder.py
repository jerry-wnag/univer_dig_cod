import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
NOTEBOOK = ROOT / "TCCT_S87A_SevenBranchFailureAudit.ipynb"
WL_SOURCE = ROOT / "TCCT_S87D_FreezeWorldMultisetDecoder.wl"
RUNTIME_SOURCE = ROOT / "TCCT_S87D_FrozenDecoderRuntime.wl"
STAGE_MARKER = "TCCT S87D CELL"


def check_wl_delimiters(source: str) -> None:
    pairs = {")": "(", "]": "[", "}": "{"}
    stack: list[tuple[str, int]] = []
    in_string = False
    escaped = False
    comment_depth = 0
    index = 0
    while index < len(source):
        char = source[index]
        next_char = source[index + 1] if index + 1 < len(source) else ""
        if comment_depth:
            if char == "(" and next_char == "*":
                comment_depth += 1
                index += 2
                continue
            if char == "*" and next_char == ")":
                comment_depth -= 1
                index += 2
                continue
            index += 1
            continue
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == "(" and next_char == "*":
            comment_depth = 1
            index += 2
            continue
        if char == '"':
            in_string = True
        elif char in "([{":
            stack.append((char, index))
        elif char in ")]}" :
            if not stack or stack[-1][0] != pairs[char]:
                raise RuntimeError(
                    f"unbalanced Wolfram delimiter {char} at {index}"
                )
            stack.pop()
        index += 1
    if in_string or comment_depth or stack:
        raise RuntimeError(
            "unterminated Wolfram source: "
            f"string={in_string}, comment_depth={comment_depth}, "
            f"stack_tail={stack[-3:]}"
        )


def source_lines(text: str) -> list[str]:
    return text.splitlines(keepends=True)


notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
source = WL_SOURCE.read_text(encoding="utf-8").strip() + "\n"
check_wl_delimiters(source)
check_wl_delimiters(RUNTIME_SOURCE.read_text(encoding="utf-8"))

cells = notebook.setdefault("cells", [])
matching_indices = [
    index
    for index, cell in enumerate(cells)
    if cell.get("cell_type") == "code"
    and STAGE_MARKER in "".join(cell.get("source", []))
]

if len(matching_indices) > 1:
    raise RuntimeError("notebook contains more than one S87D code cell")

if matching_indices:
    cell = cells[matching_indices[0]]
    cell["source"] = source_lines(source)
    cell["execution_count"] = None
    cell["outputs"] = []
else:
    while (
        cells
        and cells[-1].get("cell_type") == "code"
        and not "".join(cells[-1].get("source", [])).strip()
    ):
        cells.pop()
    cells.extend(
        [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": source_lines(
                    "## S87D - Freeze and lock the S87C decoder\n\n"
                    "Run **only the next cell** in the current completed S87C "
                    "kernel. Do not restart the kernel and do not run all cells. "
                    "This stage freezes the already-selected decoder, verifies a "
                    "binary export/import round trip, and does not generate or read "
                    "any S88 blind-test data.\n"
                ),
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": source_lines(source),
            },
        ]
    )

temporary = NOTEBOOK.with_suffix(".ipynb.s87d.tmp")
temporary.write_text(
    json.dumps(notebook, ensure_ascii=False, indent=1) + "\n",
    encoding="utf-8",
)
temporary.replace(NOTEBOOK)

print(f"updated: {NOTEBOOK}")
print(f"cells: {len(cells)}")
print(f"S87D code chars: {len(source)}")
