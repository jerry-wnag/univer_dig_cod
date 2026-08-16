"""Build a Jupyter notebook from the recovered TCCT S71 Wolfram cells."""

from pathlib import Path
import re

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "wolfram" / "TCCT_S71_recovered_full.wl"
OUTPUT = ROOT / "wolfram" / "TCCT_S71_Jupyter.ipynb"
CELL = re.compile(r"(?m)^\(\* In\[(\d+)\] \*\)\s*$")


def recovered_cells(text: str) -> list[tuple[int, str]]:
    markers = list(CELL.finditer(text))
    cells = []
    for index, marker in enumerate(markers):
        end = markers[index + 1].start() if index + 1 < len(markers) else len(text)
        code = text[marker.end() : end].strip()
        cells.append((int(marker.group(1)), code))
    return cells


def main() -> None:
    source_text = SOURCE.read_text(encoding="utf-8")
    cells = recovered_cells(source_text)

    notebook = nbf.v4.new_notebook()
    notebook["metadata"]["kernelspec"] = {
        "display_name": "Wolfram Language 15",
        "language": "Wolfram Language",
        "name": "wolframlanguage15",
    }
    notebook["metadata"]["language_info"] = {
        "name": "Wolfram Language",
        "file_extension": ".wl",
        "mimetype": "application/vnd.wolfram.mathematica",
        "codemirror_mode": "mathematica",
    }

    notebook["cells"] = [
        nbf.v4.new_markdown_cell(
            "# TCCT S71 - Blind Topology Transfer Checkpoint\n\n"
            "Recovered from the 111-page Wolfram PDF. The original 142 input "
            "cell labels are preserved in cell metadata and headings.\n\n"
            "Use **Kernel > Restart Kernel and Run All Cells** for a clean run."
        ),
        nbf.v4.new_markdown_cell("## Environment check"),
        nbf.v4.new_code_cell(
            '<|"WolframVersion" -> $Version, "SystemID" -> $SystemID, '
            '"ProcessorCount" -> $ProcessorCount|>'
        ),
        nbf.v4.new_markdown_cell(
            "## Recovered S59-S71 experiment\n\n"
            "The cells below follow the execution order recorded in the PDF."
        ),
    ]

    for original_number, code in cells:
        cell = nbf.v4.new_code_cell(code)
        cell["metadata"]["tcct_original_input"] = original_number
        notebook["cells"].append(cell)

    notebook["cells"].extend(
        [
            nbf.v4.new_markdown_cell("## S71 visual summary"),
            nbf.v4.new_code_cell("Dataset[{blindCert71}]"),
            nbf.v4.new_code_cell(
                "BarChart[\n"
                " candidateScores71,\n"
                " ChartLabels -> Placed[Range[Length[candidateScores71]], Below],\n"
                " PlotRange -> {0, 32},\n"
                " AxesLabel -> {\"Candidate\", \"ParallelIn score\"},\n"
                " PlotLabel -> \"Five SharedMerge-perfect candidates on ParallelIn\",\n"
                " ImageSize -> Large\n"
                "]"
            ),
            nbf.v4.new_code_cell(
                "With[{base = Case59[2, 1, \"Continue\"], "
                "parallel = Case71[2, 1, \"Continue\"]},\n"
                " Grid[{\n"
                "   {Style[\"S59 base\", Bold, 14], "
                "Style[\"ParallelIn blind topology\", Bold, 14]},\n"
                "   {Graph[base[[1, 1]], GraphLayout -> \"LayeredDigraphEmbedding\", "
                "VertexLabels -> None, VertexSize -> Tiny, ImageSize -> 500],\n"
                "    Graph[parallel[[1, 1]], GraphLayout -> \"LayeredDigraphEmbedding\", "
                "VertexLabels -> None, VertexSize -> Tiny, ImageSize -> 500]}\n"
                " }, Frame -> All, Spacings -> {2, 1}]\n"
                "]"
            ),
            nbf.v4.new_markdown_cell(
                "## Frozen model\n\n"
                "Do not retune this model inside the S71 checkpoint. Create a "
                "separate notebook for S72."
            ),
            nbf.v4.new_code_cell(
                '<|"K" -> 5, "Params" -> {0, -1, 1, -1, -1, 0}, '
                '"Policy" -> {1, 4}|>'
            ),
        ]
    )

    nbf.write(notebook, OUTPUT)
    print(f"Created {OUTPUT} with {len(notebook['cells'])} cells")


if __name__ == "__main__":
    main()
