"""Append the S75 multiscale encoder search to the frozen S74 result."""

from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "wolfram" / "TCCT_S74_LayerAttributionAudit_Result.ipynb"
SOURCE = ROOT / "wolfram" / "TCCT_S75_MultiscaleSemanticEncoder.wl"
OUTPUT = ROOT / "wolfram" / "TCCT_S75_MultiscaleSemanticEncoder.ipynb"
MARKER = "(* S75 CELL *)"


def main() -> None:
    notebook = nbf.read(BASE, as_version=4)
    code_cells = [part.strip() for part in SOURCE.read_text(encoding="utf-8").split(MARKER)]
    code_cells = [source for source in code_cells if source]

    notebook.cells.extend(
        [
            nbf.v4.new_markdown_cell(
                "# S75 — Multiscale Semantic-Preserving Encoder\n\n"
                "S75 is a new representation branch. It does not alter the frozen S71–S74 "
                "checkpoints or the TCCT propagation mechanism. It pairs radius-2 and radius-3 "
                "codes and adds parent/child cardinality terms."
            ),
            nbf.v4.new_markdown_cell(
                "## Selection protocol\n\n"
                "The policy is derived only from S59 + ChainIn training cases at depths 2 and 5. "
                "Held depths, legacy topologies, and the already-observed S72 battery are used for "
                "validation and ranking. S75 is not a blind test. No S76 topology is evaluated here."
            ),
        ]
    )

    for index, source in enumerate(code_cells, start=1):
        cell = nbf.v4.new_code_cell(source)
        cell.metadata["tcct_stage"] = "S75"
        cell.metadata["tcct_s75_cell"] = index
        notebook.cells.append(cell)

    notebook.metadata["tcct_checkpoint_base"] = "S74_LayerAttributionAudit_Result"
    notebook.metadata["tcct_stage"] = "S75_MultiscaleSemanticEncoder"
    nbf.write(notebook, OUTPUT)
    print(f"Created {OUTPUT} with {len(code_cells)} unexecuted S75 cells")


if __name__ == "__main__":
    main()
