"""Append the S75A tradeoff/mechanism audit to the locked S75 result."""

from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "wolfram" / "TCCT_S75_MultiscaleSemanticEncoder_Result.ipynb"
SOURCE = ROOT / "wolfram" / "TCCT_S75A_TradeoffMechanismAudit.wl"
OUTPUT = ROOT / "wolfram" / "TCCT_S75A_TradeoffMechanismAudit.ipynb"
MARKER = "(* S75A CELL *)"


def main() -> None:
    notebook = nbf.read(BASE, as_version=4)
    code_cells = [part.strip() for part in SOURCE.read_text(encoding="utf-8").split(MARKER)]
    code_cells = [source for source in code_cells if source]

    notebook.cells.extend(
        [
            nbf.v4.new_markdown_cell(
                "# S75A — Tradeoff and Mechanism Audit\n\n"
                "This is a read-only audit of the completed S75 candidate population. "
                "It does not change the TCCT core, the original frozen model, the S75 "
                "selection rule, or the selected S75 candidate."
            ),
            nbf.v4.new_markdown_cell(
                "## Diagnostic protocol\n\n"
                "The audit compares the frozen protocol selection, the most compatible "
                "S72-perfect candidate, and the highest-total-score candidate. It reports "
                "the Pareto frontier, per-topology failure layers, per-depth failures, and "
                "radius/degree-feature ablations. All oracle and ablation results are "
                "diagnostic only and are not used to retune or select a model."
            ),
        ]
    )

    for index, source in enumerate(code_cells, start=1):
        cell = nbf.v4.new_code_cell(source)
        cell.metadata["tcct_stage"] = "S75A"
        cell.metadata["tcct_s75a_cell"] = index
        notebook.cells.append(cell)

    notebook.metadata["tcct_checkpoint_base"] = "S75_MultiscaleSemanticEncoder_Result"
    notebook.metadata["tcct_stage"] = "S75A_TradeoffMechanismAudit"
    nbf.write(notebook, OUTPUT)
    print(f"Created {OUTPUT} with {len(code_cells)} unexecuted S75A audit cells")


if __name__ == "__main__":
    main()
