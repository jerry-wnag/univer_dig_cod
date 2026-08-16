"""Append the all-candidate semantic feasibility scan to the locked S75B result."""

from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "wolfram" / "TCCT_S75B_CrossTopologySemanticAudit_Result.ipynb"
SOURCE = ROOT / "wolfram" / "TCCT_S75C_GlobalSemanticFeasibilityScan.wl"
OUTPUT = ROOT / "wolfram" / "TCCT_S75C_GlobalSemanticFeasibilityScan.ipynb"
MARKER = "(* S75C CELL *)"


def main() -> None:
    notebook = nbf.read(BASE, as_version=4)
    code_cells = [part.strip() for part in SOURCE.read_text(encoding="utf-8").split(MARKER)]
    code_cells = [source for source in code_cells if source]

    notebook.cells.extend(
        [
            nbf.v4.new_markdown_cell(
                "# S75C — Global Semantic Feasibility Scan\n\n"
                "S75C audits all 1,795 training-perfect S75 candidates. It does not add a "
                "parameter search, alter the TCCT core, change the frozen model, or apply a "
                "validation-informed policy completion."
            ),
            nbf.v4.new_markdown_cell(
                "## Population-level question\n\n"
                "For every candidate, the audit asks whether one pure code-membership policy "
                "can solve all 224 seen cases, whether every observed code has a single global "
                "meaning, and how many validation-informed policy edits would be required. "
                "Completion policies are diagnostic only; S76 remains untouched."
            ),
        ]
    )

    for index, source in enumerate(code_cells, start=1):
        cell = nbf.v4.new_code_cell(source)
        cell.metadata["tcct_stage"] = "S75C"
        cell.metadata["tcct_s75c_cell"] = index
        notebook.cells.append(cell)

    notebook.metadata["tcct_checkpoint_base"] = "S75B_CrossTopologySemanticAudit_Result"
    notebook.metadata["tcct_stage"] = "S75C_GlobalSemanticFeasibilityScan"
    nbf.write(notebook, OUTPUT)
    print(f"Created {OUTPUT} with {len(code_cells)} unexecuted S75C audit cells")


if __name__ == "__main__":
    main()
