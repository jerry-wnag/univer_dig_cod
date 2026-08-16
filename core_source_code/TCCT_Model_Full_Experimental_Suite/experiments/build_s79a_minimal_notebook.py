import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "TCCT_S79A_MinimalBlindFailureMechanismAudit.wl"
OUTPUT = ROOT / "TCCT_S79A_MinimalBlindFailureMechanismAudit.ipynb"
MARKER = "(* S79A CELL *)"


source = SOURCE.read_text(encoding="utf-8")
parts = source.split(MARKER)
if parts[0].strip() or len(parts) != 5:
    raise RuntimeError("Expected exactly four S79A code-cell markers")

code_cells = [part.strip() + "\n" for part in parts[1:]]
notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "id": "s79a-intro",
            "metadata": {},
            "source": [
                "# TCCT S79A — Minimal Blind-Failure Mechanism Audit\n",
                "\n",
                "这是独立轻量审计：**不载入 S59–S78 Notebook，不重跑历史测试，不训练、不搜索、不改冻结模型。**\n",
                "\n",
                "只运行两组必要数据：16 个原始 S79 blind cases，以及 48 个小规模 motif 对照 cases。按顺序运行下面 4 个代码单元；最后一格给出 `RootCause`、完整性锁和下一阶段建议。\n",
            ],
        },
        *[
            {
                "cell_type": "code",
                "id": f"s79a-code-{index}",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": cell.splitlines(keepends=True),
            }
            for index, cell in enumerate(code_cells, start=1)
        ],
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "Wolfram Language 15",
            "language": "Wolfram Language",
            "name": "wolframlanguage15",
        },
        "language_info": {
            "file_extension": ".wl",
            "mimetype": "application/vnd.wolfram.mathematica",
            "name": "Wolfram Language",
            "version": "15.0",
        },
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

OUTPUT.write_text(
    json.dumps(notebook, ensure_ascii=False, indent=1) + "\n",
    encoding="utf-8",
)
print(OUTPUT)
