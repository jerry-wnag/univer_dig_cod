import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
S86E_NOTEBOOK = ROOT / "TCCT_S86E_FreezeK33Candidate.ipynb"
S84_NOTEBOOK = ROOT / "TCCT_S84_BlindDoubleInterventionQueryGrid_AutoRun.ipynb"
S85_NOTEBOOK = ROOT / "TCCT_S85_BlindInverseInterventionQueryGrid_AutoRun.ipynb"
WL_OUTPUT = ROOT / "TCCT_S86F_RevealedS84S85Regression.wl"
NB_OUTPUT = ROOT / "TCCT_S86F_RevealedS84S85Regression.ipynb"
AUTORUN_OUTPUT = ROOT / "TCCT_S86F_RevealedS84S85Regression_AutoRun.ipynb"
PREFLIGHT_OUTPUT = ROOT / "TCCT_S86F_RevealedS84S85Regression_Preflight_AutoRun.ipynb"
MARKER = "(* S86F CELL *)"


def load_code_cells(path: Path) -> list[str]:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    return [
        "".join(cell.get("source", []))
        for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code"
    ]


def adapt_regression_cells(
    cells: list[str], old_stage: str, suffix: str, old_name: str, new_name: str
) -> list[str]:
    if len(cells) != 4:
        raise RuntimeError(f"S{old_stage} notebook no longer has four code cells")

    adapted = []
    for source in cells[1:]:
        source = source.replace(old_stage, suffix)
        source = source.replace("frozenCandidate83B", "frozenCandidate86E")
        source = source.replace("S83B-K19ExactRole", "S86E-K33ExactRole")
        source = source.replace(old_name, new_name)
        source = source.replace(
            '"HistoricalRegressionRerun"->False',
            '"HistoricalRegressionRerun"->True',
        )
        source = source.replace(
            f"blindPerfect{suffix}", f"regressionPerfect{suffix}"
        )
        source = source.replace(
            f"blindResultHash{suffix}", f"regressionResultHash{suffix}"
        )
        source = source.replace('"BlindPerfect"', '"RegressionPerfect"')
        adapted.append(source)

    if old_stage == "84":
        adapted = [
            source.replace(
                f'"S{suffix}IsBlindCounterfactualCompositionTest"->True',
                '"RevealedRegressionNotBlind"->True',
            )
            .replace(
                '"MayClaimBlindMultiInterventionCounterfactualComposition"',
                '"PreservesOriginalS84CounterfactualComposition"',
            )
            .replace(
                '"BLIND_DOUBLE_INTERVENTION_QUERY_GRID_PASS"',
                '"S86F_S84_REVEALED_REGRESSION_PASS"',
            )
            .replace(
                '"VALID_BLIND_DOUBLE_INTERVENTION_QUERY_GRID_FAILURE"',
                '"S86F_S84_VALID_REGRESSION_FAILURE"',
            )
            .replace(
                '"INVALID_S86F84_BLIND_TEST"',
                '"INVALID_S86F_S84_REGRESSION"',
            )
            .replace(
                '"S85_INDEPENDENT_INTERVENTION_OPERATOR_BLIND_TEST"',
                '"S86F_CONTINUE_TO_S85_REVEALED_REGRESSION"',
            )
            .replace(
                '"S86F84A_FAILURE_AUDIT_WITHOUT_RETUNING"',
                '"S86F_STOP_AND_AUDIT_S84_REGRESSION"',
            )
            for source in adapted
        ]
    else:
        adapted = [
            source.replace(
                f'"S{suffix}IsBlindCounterfactualCompositionTest"->True',
                '"RevealedRegressionNotBlind"->True',
            )
            .replace(
                '"MayClaimBlindInverseInterventionCounterfactualComposition"',
                '"PreservesOriginalS85CounterfactualComposition"',
            )
            .replace(
                '"BLIND_INVERSE_INTERVENTION_QUERY_GRID_PASS"',
                '"S86F_S85_REVEALED_REGRESSION_PASS"',
            )
            .replace(
                '"VALID_BLIND_INVERSE_INTERVENTION_QUERY_GRID_FAILURE"',
                '"S86F_S85_VALID_REGRESSION_FAILURE"',
            )
            .replace(
                '"INVALID_S86F85_BLIND_TEST"',
                '"INVALID_S86F_S85_REGRESSION"',
            )
            .replace(
                '"S86_COUNTERFACTUAL_CHECKPOINT_AND_EXTERNAL_GRAMMAR_TEST"',
                '"S86F_BUILD_COMBINED_REGRESSION_CERTIFICATE"',
            )
            .replace(
                '"S86F85A_FAILURE_AUDIT_WITHOUT_RETUNING"',
                '"S86F_STOP_AND_AUDIT_S85_REGRESSION"',
            )
            for source in adapted
        ]

    joined = "\n".join(adapted)
    if "frozenCandidate83B" in joined:
        raise RuntimeError(f"old K19 runtime candidate leaked into S{suffix}")
    if "S87" in joined:
        raise RuntimeError(f"S87 material leaked into S{suffix}")
    return [source.strip() + "\n" for source in adapted]


s86e_cells = load_code_cells(S86E_NOTEBOOK)
s84_cells = load_code_cells(S84_NOTEBOOK)
s85_cells = load_code_cells(S85_NOTEBOOK)
if len(s86e_cells) != 3:
    raise RuntimeError("S86E notebook no longer has three code cells")

# Preserve the architecture/core preflight cell exactly as used by S86E.
architecture_cell = s86e_cells[0].strip() + "\n"

preflight_cell = r'''
expectedK33CandidateHash86F=
"2eb674929cfe1710231a4f508d13b20fe0f98d84d2c594c6261f46f370066ae4";
expectedBaseK19CandidateHash86F=
"a51e6a13bdeda37b041eee4b74cfb6e472c7e52107a60f1d5534bb5df44ce44f";
expectedSelectionCertificateHash86F=
"974c588337fbd9c3f51e9ea6847ba360dfc9dcf6fced751104f028987900ac5a";
expectedSelectionProtocolHash86F=
"3faafbe4eef88369c32637b2b6b0825e288f6c40d7286db47e8739f083c3d309";
expectedSelectedResultHash86F=
"cf6809b1fee65997fe95bdb28e6e3886e2a09f00ed9815ef0f6edff1117fe5ce";

k33CandidatePath86F="E:/engine_wolf/TCCT_S86E_K33FrozenCandidate.wl";
oldK19CandidatePath86F="E:/engine_wolf/TCCT_S83B_FrozenCandidate.wl";

If[
!FileExistsQ[k33CandidatePath86F],
Print["S86F aborted: frozen K33 candidate file is missing."];Abort[]
];

k33CandidateFileHashBefore86F=FileHash[k33CandidatePath86F,"SHA256"];
oldK19CandidateFileHashBefore86F=If[
FileExistsQ[oldK19CandidatePath86F],
FileHash[oldK19CandidatePath86F,"SHA256"],
Missing["OldK19CandidateFileMissing"]
];

Clear[frozenCandidate86E];
Get[k33CandidatePath86F];

k33CandidateHashBefore86F=If[
AssociationQ[frozenCandidate86E],
Hash[Normal[frozenCandidate86E],"SHA256","HexString"],
Missing["K33CandidateNotLoaded"]
];
baseK19CandidateHashBefore86F=Hash[
Normal[frozenCandidate83B],"SHA256","HexString"
];
modelHashBefore86F=Hash[Normal[frozen75D],"SHA256","HexString"];
coreHashBefore86F=Hash[CoreDefinitionBundle86[],"SHA256","HexString"];
canonicalizerHashBefore86F=canonicalizerImplementationHash79B;
interventionHashBefore86F=interventionImplementationHash82;

preflightPassed86F=And[
TrueQ[preflightPassed86],
AssociationQ[frozenCandidate86E],
SameQ[k33CandidateHashBefore86F,expectedK33CandidateHash86F],
SameQ[baseK19CandidateHashBefore86F,expectedBaseK19CandidateHash86F],
SameQ[frozenCandidate86E["Stage"],"S86E"],
SameQ[frozenCandidate86E["Name"],"K33CrossArityCandidate"],
SameQ[frozenCandidate86E["BaseCandidateHash"],expectedBaseK19CandidateHash86F],
SameQ[frozenCandidate86E["SelectionCertificateHash"],
expectedSelectionCertificateHash86F],
SameQ[frozenCandidate86E["SelectionProtocolHash"],
expectedSelectionProtocolHash86F],
SameQ[frozenCandidate86E["SelectedResultHash"],expectedSelectedResultHash86F],
SameQ[frozenCandidate86E["EncoderParams"],frozen75D["Params"]],
SameQ[frozenCandidate86E["Representation"],"KExactRole"],
SameQ[frozenCandidate86E["K"],33],
SameQ[frozenCandidate86E["PolicyLength"],39],
SameQ[Length[frozenCandidate86E["Policy"]],39],
SameQ[frozenCandidate86E["CombinedDevelopmentScore"],552],
TrueQ[frozenCandidate86E["ExactNodeRoleUsed"]],
SameQ[frozenCandidate86E["TokenDeduplication"],"DeleteDuplicates"],
TrueQ[frozenCandidate86E["FrozenBeforeS87"]],
FileExistsQ[oldK19CandidatePath86F]
];

ClearAll[CoreDefinitionBundle86F84,CoreDefinitionBundle86F85];
CoreDefinitionBundle86F84[]:=CoreDefinitionBundle86[];
CoreDefinitionBundle86F85[]:=CoreDefinitionBundle86[];

preflightPassed86F84=preflightPassed86F;
preflightPassed86F85=preflightPassed86F;
expectedCandidateHash86F84=expectedK33CandidateHash86F;
expectedCandidateHash86F85=expectedK33CandidateHash86F;
expectedCanonicalizerHash86F84=expectedCanonicalizerHash86;
expectedCanonicalizerHash86F85=expectedCanonicalizerHash86;
expectedInterventionHash86F84=expectedInterventionHash86;
expectedInterventionHash86F85=expectedInterventionHash86;
candidateHashLoaded86F84=k33CandidateHashBefore86F;
candidateHashLoaded86F85=k33CandidateHashBefore86F;

preflight86F=<|
"Stage"->"S86F",
"Name"->"RevealedS84S85Regression",
"AuditType"->"RevealedRegressionNotBlind",
"K33CandidateFileLoaded"->FileExistsQ[k33CandidatePath86F],
"CandidateHash"->k33CandidateHashBefore86F,
"ExpectedCandidateHash"->expectedK33CandidateHash86F,
"K"->If[AssociationQ[frozenCandidate86E],frozenCandidate86E["K"],Missing[]],
"PolicyLength"->If[
AssociationQ[frozenCandidate86E],Length[frozenCandidate86E["Policy"]],Missing[]
],
"SelectionRun"->False,
"PolicyEditApplied"->False,
"RetuningApplied"->False,
"S84S85LabelsUsedForSelection"->False,
"S87DataUsed"->False,
"OriginalFrozenModelChanged"->False,
"BaseK19CandidateChanged"->False,
"CoreChanged"->False,
"DeduplicationMechanismChanged"->False,
"PreflightPassed"->preflightPassed86F
|>;

If[
!TrueQ[preflightPassed86F],
Print[Dataset[{preflight86F}]];
Print["S86F aborted: frozen K33 candidate or architecture mismatch."];
Abort[]
];

Dataset[{preflight86F}]
'''.strip() + "\n"

s84_regression_cells = adapt_regression_cells(
    s84_cells,
    old_stage="84",
    suffix="86F84",
    old_name="BlindDoubleInterventionQueryGrid",
    new_name="RevealedS84DoubleInterventionRegression",
)
s85_regression_cells = adapt_regression_cells(
    s85_cells,
    old_stage="85",
    suffix="86F85",
    old_name="BlindInverseInterventionQueryGrid",
    new_name="RevealedS85InverseInterventionRegression",
)

final_cell = r'''
modelHashAfter86F=Hash[Normal[frozen75D],"SHA256","HexString"];
baseK19CandidateHashAfter86F=Hash[
Normal[frozenCandidate83B],"SHA256","HexString"
];
k33CandidateHashAfter86F=Hash[
Normal[frozenCandidate86E],"SHA256","HexString"
];
coreHashAfter86F=Hash[CoreDefinitionBundle86[],"SHA256","HexString"];
canonicalizerHashAfter86F=canonicalizerImplementationHash79B;
interventionHashAfter86F=interventionImplementationHash82;
k33CandidateFileHashAfter86F=FileHash[k33CandidatePath86F,"SHA256"];
oldK19CandidateFileHashAfter86F=FileHash[oldK19CandidatePath86F,"SHA256"];

originalFrozenModelUnchanged86F=SameQ[
modelHashBefore86F,modelHashAfter86F
];
baseK19CandidateUnchanged86F=And[
SameQ[baseK19CandidateHashBefore86F,baseK19CandidateHashAfter86F],
SameQ[baseK19CandidateHashAfter86F,expectedBaseK19CandidateHash86F],
SameQ[oldK19CandidateFileHashBefore86F,oldK19CandidateFileHashAfter86F]
];
k33CandidateUnchanged86F=And[
SameQ[k33CandidateHashBefore86F,k33CandidateHashAfter86F],
SameQ[k33CandidateHashAfter86F,expectedK33CandidateHash86F],
SameQ[k33CandidateFileHashBefore86F,k33CandidateFileHashAfter86F]
];
coreUnchanged86F=SameQ[coreHashBefore86F,coreHashAfter86F];
canonicalizerUnchanged86F=SameQ[
canonicalizerHashBefore86F,canonicalizerHashAfter86F
];
interventionUnchanged86F=SameQ[
interventionHashBefore86F,interventionHashAfter86F
];

regressionValidityPassed86F=And[
TrueQ[preflightPassed86F],
TrueQ[testValidityPassed86F84],
TrueQ[testValidityPassed86F85],
TrueQ[originalFrozenModelUnchanged86F],
TrueQ[baseK19CandidateUnchanged86F],
TrueQ[k33CandidateUnchanged86F],
TrueQ[coreUnchanged86F],
TrueQ[canonicalizerUnchanged86F],
TrueQ[interventionUnchanged86F],
SameQ[summary86F84["Scenarios"],24],
SameQ[summary86F84["WorldPairs"],96],
SameQ[summary86F84["Worlds"],192],
SameQ[summary86F85["Scenarios"],24],
SameQ[summary86F85["WorldPairs"],96],
SameQ[summary86F85["Worlds"],192]
];

regressionPerfect86F=And[
TrueQ[regressionValidityPassed86F],
TrueQ[regressionPerfect86F84],
TrueQ[regressionPerfect86F85],
SameQ[summary86F84["WorldCorrect"],192],
SameQ[summary86F85["WorldCorrect"],192],
SameQ[summary86F84["PairCorrect"],96],
SameQ[summary86F85["PairCorrect"],96],
SameQ[summary86F84["ScenarioPerfect"],24],
SameQ[summary86F85["ScenarioPerfect"],24]
];

resultPayload86F=<|
"Stage"->"S86F",
"Name"->"RevealedS84S85Regression",
"AuditType"->"RevealedRegressionNotBlind",
"CandidateHash"->k33CandidateHashAfter86F,
"K"->frozenCandidate86E["K"],
"PolicyLength"->frozenCandidate86E["PolicyLength"],
"S84Scenarios"->summary86F84["Scenarios"],
"S84WorldPairs"->summary86F84["WorldPairs"],
"S84WorldCorrect"->summary86F84["WorldCorrect"],
"S84PairCorrect"->summary86F84["PairCorrect"],
"S84ScenarioPerfect"->summary86F84["ScenarioPerfect"],
"S84RegressionPassed"->regressionPerfect86F84,
"S85Scenarios"->summary86F85["Scenarios"],
"S85WorldPairs"->summary86F85["WorldPairs"],
"S85WorldCorrect"->summary86F85["WorldCorrect"],
"S85PairCorrect"->summary86F85["PairCorrect"],
"S85ScenarioPerfect"->summary86F85["ScenarioPerfect"],
"S85RegressionPassed"->regressionPerfect86F85,
"CombinedScenarios"->summary86F84["Scenarios"]+summary86F85["Scenarios"],
"CombinedWorldPairs"->summary86F84["WorldPairs"]+summary86F85["WorldPairs"],
"CombinedWorlds"->summary86F84["Worlds"]+summary86F85["Worlds"],
"CombinedWorldCorrect"->
summary86F84["WorldCorrect"]+summary86F85["WorldCorrect"],
"OriginalFrozenModelChanged"->!TrueQ[originalFrozenModelUnchanged86F],
"BaseK19CandidateChanged"->!TrueQ[baseK19CandidateUnchanged86F],
"K33CandidateChanged"->!TrueQ[k33CandidateUnchanged86F],
"CoreChanged"->!TrueQ[coreUnchanged86F],
"CanonicalizerChanged"->!TrueQ[canonicalizerUnchanged86F],
"InterventionChanged"->!TrueQ[interventionUnchanged86F],
"S84TopologyImplementationsChanged"->cert86F84["TopologyImplementationsChanged"],
"S85TopologyImplementationsChanged"->cert86F85["TopologyImplementationsChanged"],
"DeduplicationMechanismChanged"->Or[
TrueQ[cert86F84["DeduplicationMechanismChanged"]],
TrueQ[cert86F85["DeduplicationMechanismChanged"]]
],
"TrainingRun"->False,
"CandidateSelectionRun"->False,
"PolicyEditApplied"->False,
"RetuningApplied"->False,
"S84S85LabelsUsedForSelection"->False,
"S87DataUsed"->False,
"RegressionValidityPassed"->regressionValidityPassed86F,
"RegressionPerfect"->regressionPerfect86F,
"TotalTraceSeconds"->
summary86F84["TotalTraceSeconds"]+summary86F85["TotalTraceSeconds"]
|>;

regressionResultHash86F=Hash[
Normal[resultPayload86F],"SHA256","HexString"
];

cert86F=Join[
resultPayload86F,
<|
"RegressionResultHash"->regressionResultHash86F,
"Outcome"->Which[
!TrueQ[regressionValidityPassed86F],
"INVALID_S86F_REGRESSION",
TrueQ[regressionPerfect86F],
"S86F_REVEALED_S84_S85_REGRESSION_PASS",
True,
"VALID_S86F_REGRESSION_FAILURE"
],
"SuggestedNextStage"->If[
TrueQ[regressionPerfect86F],
"S87_NEW_BLIND_TEST_WITH_FROZEN_K33",
"S86G_FAILURE_AUDIT_WITHOUT_RETUNING"
]
|>
];

Dataset[{cert86F}]
'''.strip() + "\n"

cells = [
    architecture_cell,
    preflight_cell,
    *s84_regression_cells,
    *s85_regression_cells,
    final_cell,
]

wl_source = "\n\n".join(f"{MARKER}\n{cell}" for cell in cells)
if wl_source.count("S87") != 4:
    raise RuntimeError("unexpected S87 reference count in S86F source")
if "CandidateSearchRun\"->True" in wl_source or "CandidateSelectionRun\"->True" in wl_source:
    raise RuntimeError("candidate selection accidentally enabled")
WL_OUTPUT.write_text(wl_source, encoding="utf-8")

markdown = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "# TCCT S86F - Revealed S84/S85 Regression\n",
        "\n",
        "Run the exact revealed S84 and S85 counterfactual test generators with the "
        "frozen S86E K=33 candidate. This is regression, not a new blind test. No "
        "selection, policy edit, retuning, or S87 data is allowed.\n",
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
            "file_extension": ".wl",
            "mimetype": "application/vnd.wolfram.mathematica",
            "name": "Wolfram Language",
            "pygments_lexer": "mathematica",
            "version": "15.0",
        },
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

payload = json.dumps(notebook, ensure_ascii=False, indent=2) + "\n"
NB_OUTPUT.write_text(payload, encoding="utf-8")
AUTORUN_OUTPUT.write_text(payload, encoding="utf-8")

preflight_notebook = dict(notebook)
preflight_notebook["cells"] = [
    markdown,
    *[
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": cell.splitlines(keepends=True),
        }
        for cell in [architecture_cell, preflight_cell]
    ],
]
PREFLIGHT_OUTPUT.write_text(
    json.dumps(preflight_notebook, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

for path in (WL_OUTPUT, NB_OUTPUT, AUTORUN_OUTPUT, PREFLIGHT_OUTPUT):
    print(path)
