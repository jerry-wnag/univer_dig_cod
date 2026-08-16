import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WL_OUTPUT = ROOT / "TCCT_S83B_FreezeK19OuterCandidate.wl"
NB_OUTPUT = ROOT / "TCCT_S83B_FreezeK19OuterCandidate_AutoRun.ipynb"
MARKER = "(* S83B FREEZE CELL *)"


cell1 = r'''
If[
!ValueQ[cert83BScan]||
!TrueQ[cert83BScan["ScanValidityPassed"]]||
!AssociationQ[selectedRepresentation83B]||
!SameQ[selectedRepresentation83B["Name"],"K19ExactRole"]||
!TrueQ[selectedRepresentation83B["Perfect"]],
Print["S83B freeze aborted: valid selected K19 state is required."];
Abort[]
];

protocol83BFreeze=<|
"Stage"->"S83B",
"Name"->"FreezeK19OuterCandidate",
"BaseCandidateHash"->expectedCandidateHash83,
"Representation"->"KExactRole",
"K"->19,
"DevelopmentRows"->264,
"DevelopmentScore"->264,
"PolicyLength"->selectedRepresentation83B["PolicyLength"],
"SelectionUsesS83Labels"->True,
"S83BIsBlindTest"->False,
"CoreMayChange"->False,
"Deduplication"->"DeleteDuplicatesUnchanged",
"FrozenBeforeS84"->True
|>;

protocolHash83BFreeze=Hash[
Normal[protocol83BFreeze],"SHA256","HexString"
];
modelHashBefore83BFreeze=Hash[
Normal[frozen75D],"SHA256","HexString"
];
oldCandidateHashBefore83BFreeze=Hash[
Normal[frozenCandidate82C],"SHA256","HexString"
];
coreHashBefore83BFreeze=Hash[
CoreDefinitionBundle83[],"SHA256","HexString"
];

Dataset[{Join[
protocol83BFreeze,
<|"ProtocolHash"->protocolHash83BFreeze|>
]}]
'''.strip() + "\n"

cell2 = r'''
frozenCandidate83B=<|
"Stage"->"S83B",
"Name"->"CapacityExpandedQueryRoleCandidate",
"BaseFrozenModelHash"->expectedFrozenModelHash79A,
"BaseCandidateHash"->expectedCandidateHash83,
"EncoderParams"->frozen75D["Params"],
"Representation"->"KExactRole",
"K"->19,
"Policy"->selectedRepresentation83B["Policy"],
"PolicyLength"->selectedRepresentation83B["PolicyLength"],
"ExactNodeRoleUsed"->True,
"TokenDeduplication"->"DeleteDuplicates",
"DevelopmentRows"->264,
"DevelopmentScore"->selectedRepresentation83B["AllDevelopmentScore"],
"S83LabelsUsedForDevelopment"->True,
"FrozenBeforeS84"->True
|>;

candidateHash83B=Hash[
Normal[frozenCandidate83B],"SHA256","HexString"
];
candidatePath83B=
"E:/engine_wolf/TCCT_S83B_FrozenCandidate.wl";

Export[
candidatePath83B,
"frozenCandidate83B="<>
ToString[InputForm[frozenCandidate83B]]<>";\n",
"Text"
];

modelHashAfter83BFreeze=Hash[
Normal[frozen75D],"SHA256","HexString"
];
oldCandidateHashAfter83BFreeze=Hash[
Normal[frozenCandidate82C],"SHA256","HexString"
];
coreHashAfter83BFreeze=Hash[
CoreDefinitionBundle83[],"SHA256","HexString"
];
protocolHashAfter83BFreeze=Hash[
Normal[protocol83BFreeze],"SHA256","HexString"
];

freezeValidityPassed83B=And[
SameQ[modelHashBefore83BFreeze,modelHashAfter83BFreeze],
SameQ[oldCandidateHashBefore83BFreeze,oldCandidateHashAfter83BFreeze],
SameQ[oldCandidateHashAfter83BFreeze,expectedCandidateHash83],
SameQ[coreHashBefore83BFreeze,coreHashAfter83BFreeze],
SameQ[protocolHash83BFreeze,protocolHashAfter83BFreeze],
SameQ[frozenCandidate83B["K"],19],
SameQ[frozenCandidate83B["PolicyLength"],26],
SameQ[frozenCandidate83B["DevelopmentScore"],264],
FileExistsQ[candidatePath83B]
];

cert83B=<|
"Stage"->"S83B",
"Name"->"FreezeK19OuterCandidate",
"Representation"->frozenCandidate83B["Representation"],
"K"->frozenCandidate83B["K"],
"PolicyLength"->frozenCandidate83B["PolicyLength"],
"DevelopmentScore"->frozenCandidate83B["DevelopmentScore"],
"DevelopmentCases"->frozenCandidate83B["DevelopmentRows"],
"CandidateHash"->candidateHash83B,
"CandidateFile"->candidatePath83B,
"CandidateFileExported"->FileExistsQ[candidatePath83B],
"OriginalFrozenModelChanged"->!SameQ[
modelHashBefore83BFreeze,modelHashAfter83BFreeze
],
"S82CFrozenCandidateChanged"->!SameQ[
oldCandidateHashBefore83BFreeze,oldCandidateHashAfter83BFreeze
],
"CoreChanged"->!SameQ[coreHashBefore83BFreeze,coreHashAfter83BFreeze],
"DeduplicationMechanismChanged"->False,
"S83BIsBlindTest"->False,
"FrozenBeforeS84"->True,
"FreezeValidityPassed"->freezeValidityPassed83B,
"Outcome"->If[
TrueQ[freezeValidityPassed83B],
"K19_OUTER_CANDIDATE_FROZEN",
"FREEZE_FAILED_DO_NOT_RUN_S84"
]
|>;

Dataset[{cert83B}]
'''.strip() + "\n"

cells = [cell1, cell2]
wl_source = "\n\n".join(f"{MARKER}\n{cell}" for cell in cells)
WL_OUTPUT.write_text(wl_source, encoding="utf-8")

notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# TCCT S83B — Freeze K19 Outer Candidate\n",
                "\n",
                "冻结 S83B 开发阶段选出的 K19 ExactRole 外层候选。核心、规则、规范化器和去重均不变；S84 才是新盲测。\n",
            ],
        },
        *[
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": cell.splitlines(keepends=True),
            }
            for cell in cells
        ],
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "Wolfram Language 15",
            "language": "Wolfram Language",
            "name": "wolframlanguage15",
        },
        "language_info": {
            "codemirror_mode": "mathematica",
            "file_extension": ".m",
            "mimetype": "application/vnd.wolfram.m",
            "name": "Wolfram Language",
            "pygments_lexer": "mathematica",
            "version": "15.0",
        },
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

NB_OUTPUT.write_text(
    json.dumps(notebook, ensure_ascii=False, indent=1),
    encoding="utf-8",
)

print(WL_OUTPUT)
print(NB_OUTPUT)
