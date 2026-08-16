"""Append the corrected cross-topology semantic audit to the locked S75A result."""

from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "wolfram" / "TCCT_S75A_TradeoffMechanismAudit_Result.ipynb"
SOURCE = ROOT / "wolfram" / "TCCT_S75B_CrossTopologySemanticAudit.wl"
OUTPUT = ROOT / "wolfram" / "TCCT_S75B_CrossTopologySemanticAudit.ipynb"
MARKER = "(* S75B CELL *)"


def main() -> None:
    notebook = nbf.read(BASE, as_version=4)
    code_cells = [part.strip() for part in SOURCE.read_text(encoding="utf-8").split(MARKER)]
    code_cells = [source for source in code_cells if source]

    notebook.cells.extend(
        [
            nbf.v4.new_markdown_cell(
                "# S75B — Cross-Topology Semantic Audit\n\n"
                "S75B corrects the per-topology attribution limitation found in S75A. "
                "It jointly audits training, heldout, legacy, and S72 token meanings without "
                "changing the TCCT core, frozen models, candidate ranking, or S75 selection."
            ),
            nbf.v4.new_markdown_cell(
                "## Corrected interpretation protocol\n\n"
                "The audit distinguishes unseen validation codes from semantic flips between "
                "training and new topologies. It also tests whether one pure code-membership "
                "policy can be perfect on each combined scope. Ablation totals are considered "
                "protocol-eligible only when the ablated representation remains training-perfect."
            ),
        ]
    )

    for index, source in enumerate(code_cells, start=1):
        cell = nbf.v4.new_code_cell(source)
        cell.metadata["tcct_stage"] = "S75B"
        cell.metadata["tcct_s75b_cell"] = index
        notebook.cells.append(cell)

    notebook.metadata["tcct_checkpoint_base"] = "S75A_TradeoffMechanismAudit_Result"
    notebook.metadata["tcct_stage"] = "S75B_CrossTopologySemanticAudit"
    nbf.write(notebook, OUTPUT)
    print(f"Created {OUTPUT} with {len(code_cells)} unexecuted S75B audit cells")


if __name__ == "__main__":
    main()
