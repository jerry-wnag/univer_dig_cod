"""Append the read-only S73 failure-mechanism audit to the frozen S72 result."""

from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "wolfram" / "TCCT_S72_FrozenTopologyBattery_Result.ipynb"
SOURCE = ROOT / "wolfram" / "TCCT_S73_TopologyFailureMechanismAudit.wl"
OUTPUT = ROOT / "wolfram" / "TCCT_S73_TopologyFailureMechanismAudit.ipynb"
MARKER = "(* S73 CELL *)"


def main() -> None:
    notebook = nbf.read(BASE, as_version=4)
    code_cells = [part.strip() for part in SOURCE.read_text(encoding="utf-8").split(MARKER)]
    code_cells = [source for source in code_cells if source]

    notebook.cells.extend(
        [
            nbf.v4.new_markdown_cell(
                "# S73 — Topology Failure Mechanism Audit\n\n"
                "This stage is diagnostic only. It does not change TCCT, the encoder, "
                "the frozen parameters, K, or the policy. It reads the frozen S72 result "
                "and traces latent-code selection and semantic collisions."
            ),
            nbf.v4.new_markdown_cell(
                "## Audit questions\n\n"
                "1. Which Continue cases lose every selected latent code?\n"
                "2. Which Stop cases acquire a selected latent code?\n"
                "3. Are failures invariant across depth?\n"
                "4. Do new raw relation states appear, or do known states collide after encoding?\n\n"
                "No search or retuning is permitted in this notebook."
            ),
        ]
    )

    for index, source in enumerate(code_cells, start=1):
        cell = nbf.v4.new_code_cell(source)
        cell.metadata["tcct_stage"] = "S73"
        cell.metadata["tcct_s73_cell"] = index
        notebook.cells.append(cell)

    notebook.metadata["tcct_checkpoint_base"] = "S72_FrozenTopologyBattery_Result"
    notebook.metadata["tcct_stage"] = "S73_TopologyFailureMechanismAudit"
    nbf.write(notebook, OUTPUT)
    print(f"Created {OUTPUT} with {len(code_cells)} unexecuted S73 audit cells")


if __name__ == "__main__":
    main()
