"""Append the frozen S72 topology battery to the reproduced S71 notebook."""

from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "wolfram" / "TCCT_S71R_WL15_Reproduced_Checkpoint.ipynb"
SOURCE = ROOT / "wolfram" / "TCCT_S72_FrozenTopologyBattery.wl"
OUTPUT = ROOT / "wolfram" / "TCCT_S72_FrozenTopologyBattery.ipynb"
MARKER = "(* S72 CELL *)"


def main() -> None:
    notebook = nbf.read(BASE, as_version=4)
    code_cells = [part.strip() for part in SOURCE.read_text(encoding="utf-8").split(MARKER)]
    code_cells = [source for source in code_cells if source]

    notebook.cells.extend(
        [
            nbf.v4.new_markdown_cell(
                "# S72 — Frozen Topology Battery\n\n"
                "This protocol was written and frozen before any S72 score was evaluated. "
                "The S71 model remains fixed. Run all S71 cells first, then execute the "
                "S72 cells in order. Do not edit the topology definitions after viewing scores."
            ),
            nbf.v4.new_markdown_cell(
                "## Pre-registered blind families\n\n"
                "- `ParallelOut`: parallel expansion on decision-node outputs.\n"
                "- `DiamondIn`: each incoming edge splits and reconverges before the decision node.\n"
                "- `SharedParallelIn`: all parents feed two shared gates before the decision node.\n\n"
                "The battery contains 32 cases per family and 96 cases total."
            ),
        ]
    )

    for index, source in enumerate(code_cells, start=1):
        cell = nbf.v4.new_code_cell(source)
        cell.metadata["tcct_stage"] = "S72"
        cell.metadata["tcct_s72_cell"] = index
        notebook.cells.append(cell)

    notebook.metadata["tcct_checkpoint_base"] = "S71R_WL15_Reproduced"
    notebook.metadata["tcct_stage"] = "S72_FrozenTopologyBattery"
    nbf.write(notebook, OUTPUT)
    print(f"Created {OUTPUT} with {len(code_cells)} frozen S72 code cells")


if __name__ == "__main__":
    main()
