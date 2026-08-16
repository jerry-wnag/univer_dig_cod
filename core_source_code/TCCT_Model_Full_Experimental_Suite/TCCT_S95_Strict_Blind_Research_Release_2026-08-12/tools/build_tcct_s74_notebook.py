"""Append the S74 layer-attribution audit to the frozen S73 result."""

from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "wolfram" / "TCCT_S73_TopologyFailureMechanismAudit_Result.ipynb"
SOURCE = ROOT / "wolfram" / "TCCT_S74_LayerAttributionAudit.wl"
OUTPUT = ROOT / "wolfram" / "TCCT_S74_LayerAttributionAudit.ipynb"
MARKER = "(* S74 CELL *)"


def main() -> None:
    notebook = nbf.read(BASE, as_version=4)
    code_cells = [part.strip() for part in SOURCE.read_text(encoding="utf-8").split(MARKER)]
    code_cells = [source for source in code_cells if source]

    notebook.cells.extend(
        [
            nbf.v4.new_markdown_cell(
                "# S74 — Layer Attribution Audit\n\n"
                "This audit keeps the frozen model unchanged and separates three possible "
                "failure layers: raw radius-limited representation, latent compression, "
                "and frozen-policy semantic alignment."
            ),
            nbf.v4.new_markdown_cell(
                "## Interpretation\n\n"
                "For each topology and radius 2–4, the notebook computes: \n\n"
                "- a label-informed raw-state oracle ceiling;\n"
                "- a label-informed latent-code oracle ceiling;\n"
                "- the actual score of the unchanged frozen policy.\n\n"
                "The oracle scores are diagnostic ceilings only and are never used for "
                "selection or retuning."
            ),
        ]
    )

    for index, source in enumerate(code_cells, start=1):
        cell = nbf.v4.new_code_cell(source)
        cell.metadata["tcct_stage"] = "S74"
        cell.metadata["tcct_s74_cell"] = index
        notebook.cells.append(cell)

    notebook.metadata["tcct_checkpoint_base"] = "S73_TopologyFailureMechanismAudit_Result"
    notebook.metadata["tcct_stage"] = "S74_LayerAttributionAudit"
    nbf.write(notebook, OUTPUT)
    print(f"Created {OUTPUT} with {len(code_cells)} unexecuted S74 audit cells")


if __name__ == "__main__":
    main()
