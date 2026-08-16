import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
S86_SOURCE = ROOT / "TCCT_S86_ExternalSixBranchBlind.wl"
SELECTION_SOURCE = ROOT / "TCCT_S86D_SelectedK33Policy.wl"
WL_OUTPUT = ROOT / "TCCT_S86E_FreezeK33Candidate.wl"
NB_OUTPUT = ROOT / "TCCT_S86E_FreezeK33Candidate.ipynb"
AUTORUN_OUTPUT = ROOT / "TCCT_S86E_FreezeK33Candidate_AutoRun.ipynb"
PREFLIGHT_OUTPUT = ROOT / "TCCT_S86E_FreezeK33Candidate_Preflight_AutoRun.ipynb"
MARKER = "(* S86E CELL *)"


s86_parts = S86_SOURCE.read_text(encoding="utf-8").split("(* S86 CELL *)")
if len(s86_parts) != 5:
    raise RuntimeError("S86 source no longer has exactly four code cells")

selection_source = SELECTION_SOURCE.read_text(encoding="utf-8").strip()
cell1 = s86_parts[1].strip() + "\n"

cell2 = selection_source + r'''

expectedSelectionCertificateHash86E=
"974c588337fbd9c3f51e9ea6847ba360dfc9dcf6fced751104f028987900ac5a";
expectedSelectionProtocolHash86E=
"3faafbe4eef88369c32637b2b6b0825e288f6c40d7286db47e8739f083c3d309";
expectedSelectedResultHash86E=
"cf6809b1fee65997fe95bdb28e6e3886e2a09f00ed9815ef0f6edff1117fe5ce";
expectedBaseCandidateHash86E=
"a51e6a13bdeda37b041eee4b74cfb6e472c7e52107a60f1d5534bb5df44ce44f";

selectedArtifactHash86E=Hash[
Normal[selectedResultArtifact86D],"SHA256","HexString"
];

protocol86E=<|
"Stage"->"S86E",
"Name"->"FreezeK33Candidate",
"SelectionCertificateHash"->expectedSelectionCertificateHash86E,
"SelectionProtocolHash"->expectedSelectionProtocolHash86E,
"SelectedResultHash"->expectedSelectedResultHash86E,
"BaseCandidateHash"->expectedBaseCandidateHash86E,
"K"->33,
"PolicyLength"->39,
"HistoricalDevelopmentScore"->264,
"SixBranchDevelopmentScore"->288,
"CombinedDevelopmentScore"->552,
"SelectionRerun"->False,
"S86LabelsRead"->False,
"S87DataUsed"->False,
"CoreMayChange"->False,
"DeduplicationMayChange"->False,
"SingleModulusFutureCollisionRiskAcknowledged"->True,
"CollisionSafeEncoderImplemented"->False,
"ProvisionalUntilRevealedRegression"->True,
"FrozenBeforeS87"->True
|>;

protocolHash86E=Hash[Normal[protocol86E],"SHA256","HexString"];
modelHashBefore86E=Hash[Normal[frozen75D],"SHA256","HexString"];
baseCandidateHashBefore86E=Hash[
Normal[frozenCandidate83B],"SHA256","HexString"
];
coreHashBefore86E=Hash[CoreDefinitionBundle86[],"SHA256","HexString"];
oldCandidateFile86E="E:/engine_wolf/TCCT_S83B_FrozenCandidate.wl";
oldCandidateFileHashBefore86E=If[
FileExistsQ[oldCandidateFile86E],FileHash[oldCandidateFile86E,"SHA256"],
Missing["OldCandidateFileMissing"]
];

preflightPassed86E=And[
TrueQ[preflightPassed86],
SameQ[selectionProvenance86D["CertificateHash"],
expectedSelectionCertificateHash86E],
SameQ[selectionProvenance86D["ProtocolHash"],
expectedSelectionProtocolHash86E],
SameQ[selectionProvenance86D["SelectedResultHash"],
expectedSelectedResultHash86E],
SameQ[selectedArtifactHash86E,expectedSelectedResultHash86E],
SameQ[selectedResultArtifact86D["K"],33],
SameQ[selectedResultArtifact86D["PolicyLength"],39],
SameQ[Length[selectedResultArtifact86D["Policy"]],39],
TrueQ[selectedResultArtifact86D["CombinedPerfect"]],
SameQ[selectedResultArtifact86D["CombinedScore"],552],
SameQ[baseCandidateHashBefore86E,expectedBaseCandidateHash86E],
FileExistsQ[oldCandidateFile86E]
];

If[!TrueQ[preflightPassed86E],
Print["S86E aborted: S86D selection artifact or frozen base mismatch."];Abort[]
];

Dataset[{Join[protocol86E,<|
"ProtocolHash"->protocolHash86E,
"SelectionArtifactHash"->selectedArtifactHash86E,
"PreflightPassed"->preflightPassed86E
|>]}]
'''.strip() + "\n"

cell3 = r'''
frozenCandidate86E=<|
"Stage"->"S86E",
"Name"->"K33CrossArityCandidate",
"BaseFrozenModelHash"->frozenCandidate83B["BaseFrozenModelHash"],
"BaseCandidateHash"->expectedBaseCandidateHash86E,
"SelectionCertificateHash"->expectedSelectionCertificateHash86E,
"SelectionProtocolHash"->expectedSelectionProtocolHash86E,
"SelectedResultHash"->expectedSelectedResultHash86E,
"EncoderParams"->frozenCandidate83B["EncoderParams"],
"Representation"->"KExactRole",
"K"->selectedResultArtifact86D["K"],
"Policy"->selectedResultArtifact86D["Policy"],
"PolicyLength"->selectedResultArtifact86D["PolicyLength"],
"ExactNodeRoleUsed"->True,
"TokenDeduplication"->"DeleteDuplicates",
"HistoricalDevelopmentRows"->264,
"HistoricalDevelopmentScore"->selectedResultArtifact86D["HistoricalScore"],
"SixBranchDevelopmentWorlds"->288,
"SixBranchDevelopmentScore"->selectedResultArtifact86D["SixBranchScore"],
"CombinedDevelopmentRows"->552,
"CombinedDevelopmentScore"->selectedResultArtifact86D["CombinedScore"],
"S86LabelsUsedForDevelopment"->True,
"SingleModulusFutureCollisionRiskAcknowledged"->True,
"CollisionSafeEncoderImplemented"->False,
"ProvisionalUntilRevealedRegression"->True,
"FrozenBeforeS87"->True
|>;

candidateHash86E=Hash[Normal[frozenCandidate86E],"SHA256","HexString"];
candidatePath86E="E:/engine_wolf/TCCT_S86E_K33FrozenCandidate.wl";
candidateExportResult86E=Export[
candidatePath86E,
"frozenCandidate86E="<>ToString[InputForm[frozenCandidate86E]]<>";\n",
"Text"
];
candidateExported86E=And[
StringQ[candidateExportResult86E],FileExistsQ[candidatePath86E]
];

If[TrueQ[candidateExported86E],Get[candidatePath86E]];
candidateHashAfterReload86E=If[
AssociationQ[frozenCandidate86E],
Hash[Normal[frozenCandidate86E],"SHA256","HexString"],
Missing["ReloadFailed"]
];

modelHashAfter86E=Hash[Normal[frozen75D],"SHA256","HexString"];
baseCandidateHashAfter86E=Hash[
Normal[frozenCandidate83B],"SHA256","HexString"
];
coreHashAfter86E=Hash[CoreDefinitionBundle86[],"SHA256","HexString"];
oldCandidateFileHashAfter86E=If[
FileExistsQ[oldCandidateFile86E],FileHash[oldCandidateFile86E,"SHA256"],
Missing["OldCandidateFileMissing"]
];
protocolHashAfter86E=Hash[Normal[protocol86E],"SHA256","HexString"];

freezeValidityPassed86E=And[
TrueQ[preflightPassed86E],
SameQ[protocolHash86E,protocolHashAfter86E],
SameQ[modelHashBefore86E,modelHashAfter86E],
SameQ[baseCandidateHashBefore86E,baseCandidateHashAfter86E],
SameQ[baseCandidateHashAfter86E,expectedBaseCandidateHash86E],
SameQ[coreHashBefore86E,coreHashAfter86E],
SameQ[oldCandidateFileHashBefore86E,oldCandidateFileHashAfter86E],
TrueQ[candidateExported86E],
AssociationQ[frozenCandidate86E],
SameQ[candidateHash86E,candidateHashAfterReload86E],
SameQ[frozenCandidate86E["K"],33],
SameQ[frozenCandidate86E["PolicyLength"],39],
SameQ[Length[frozenCandidate86E["Policy"]],39],
SameQ[frozenCandidate86E["CombinedDevelopmentScore"],552],
TrueQ[frozenCandidate86E["FrozenBeforeS87"]]
];

cert86E=<|
"Stage"->"S86E",
"Name"->"FreezeK33Candidate",
"K"->frozenCandidate86E["K"],
"PolicyLength"->frozenCandidate86E["PolicyLength"],
"HistoricalDevelopmentScore"->
frozenCandidate86E["HistoricalDevelopmentScore"],
"SixBranchDevelopmentScore"->
frozenCandidate86E["SixBranchDevelopmentScore"],
"CombinedDevelopmentScore"->frozenCandidate86E["CombinedDevelopmentScore"],
"CandidateHash"->candidateHash86E,
"CandidateFile"->candidatePath86E,
"CandidateFileExported"->candidateExported86E,
"CandidateReloadHashMatched"->SameQ[
candidateHash86E,candidateHashAfterReload86E
],
"OldK19CandidateFileChanged"->!SameQ[
oldCandidateFileHashBefore86E,oldCandidateFileHashAfter86E
],
"OriginalFrozenModelChanged"->!SameQ[modelHashBefore86E,modelHashAfter86E],
"BaseFrozenCandidateChanged"->!SameQ[
baseCandidateHashBefore86E,baseCandidateHashAfter86E
],
"CoreChanged"->!SameQ[coreHashBefore86E,coreHashAfter86E],
"DeduplicationMechanismChanged"->False,
"SelectionRerun"->False,
"S86LabelsReadDuringFreeze"->False,
"S87DataUsed"->False,
"SingleModulusFutureCollisionRiskAcknowledged"->True,
"CollisionSafeEncoderImplemented"->False,
"ProvisionalUntilRevealedRegression"->True,
"FrozenBeforeS87"->True,
"FreezeValidityPassed"->freezeValidityPassed86E,
"Outcome"->If[
TrueQ[freezeValidityPassed86E],
"S86E_K33_CANDIDATE_FROZEN",
"S86E_FREEZE_FAILED_DO_NOT_RUN_REGRESSION"
],
"SuggestedNextStage"->If[
TrueQ[freezeValidityPassed86E],
"S86F_REVEALED_S84_S85_REGRESSION",
"FIX_FREEZE_ONLY"
]
|>;

Dataset[{cert86E}]
'''.strip() + "\n"

cells = [cell1, cell2, cell3]
wl_source = "\n\n".join(f"{MARKER}\n{cell}" for cell in cells)
WL_OUTPUT.write_text(wl_source, encoding="utf-8")

markdown = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "# TCCT S86E - Freeze K33 Candidate\n",
        "\n",
        "Freeze-only stage using the exact S86D selection artifact. No selection, "
        "development scoring, or S87 data is evaluated. The old K19 file and all "
        "core definitions are hash-locked. The candidate remains provisional until "
        "revealed S84/S85 regression passes.\n",
    ],
}

notebook = {
    "cells": [
        markdown,
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

payload = json.dumps(notebook, ensure_ascii=False, indent=1)
NB_OUTPUT.write_text(payload, encoding="utf-8")
AUTORUN_OUTPUT.write_text(payload, encoding="utf-8")

preflight_notebook = dict(notebook)
preflight_notebook["cells"] = [markdown, *notebook["cells"][1:3]]
PREFLIGHT_OUTPUT.write_text(
    json.dumps(preflight_notebook, ensure_ascii=False, indent=1),
    encoding="utf-8",
)

print(WL_OUTPUT)
print(NB_OUTPUT)
print(AUTORUN_OUTPUT)
print(PREFLIGHT_OUTPUT)
