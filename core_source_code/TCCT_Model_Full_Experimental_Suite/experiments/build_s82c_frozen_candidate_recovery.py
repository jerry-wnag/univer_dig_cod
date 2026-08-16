import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
S82C_SOURCE = ROOT / "TCCT_S82C_RepresentationCapacityDiagnosis.wl"
WL_OUTPUT = ROOT / "TCCT_S82C_FrozenCandidateRecovery.wl"
NB_OUTPUT = ROOT / "TCCT_S82C_FrozenCandidateRecovery.ipynb"
MARKER = "(* S82C RECOVERY CELL *)"


s82c = S82C_SOURCE.read_text(encoding="utf-8")
parts = s82c.split("(* S82C CELL *)")
if len(parts) != 5:
    raise RuntimeError("S82C source no longer has exactly four code cells")

base_definitions = parts[1].split(
    "expectedMinimalKernelDefinitionTextHash82C=", 1
)[0].rstrip()

capacity_functions = parts[3].split("legacyRows82C=", 1)[0].rstrip()
if "CaseByGrammar82C[" not in capacity_functions:
    raise RuntimeError("Could not recover the S82C capacity functions")

cell1 = base_definitions + r'''

expectedMinimalKernelDefinitionTextHash82CR=
"d56be85db649ba1ea4118050a019d35a07c28f394396858f1d40a1f90572b922";
expectedCanonicalizerHash82CR=
"5e95c90f528a68d1045048e54b5a08809bf54c01b934902faf47f3dc3e5e587d";
expectedStableFrozenArchitectureHash82CR=
"d7d16575e25bd1090e35484931dedae9f80254475ee49cd2d79d43f5d4d1355d";
expectedInterventionHash82CR=
"45a4f2364a569f5346c9d007c0da716dc1752193fc68abcb2b6acd88c5af54bf";
expectedCandidateHash82CR=
"1aeac2dc1aa0ec4f6e187e25ec054e3e8188c75ab1058b74f620500b826a587a";

ClearAll[CoreDefinitionBundle82CR];
CoreDefinitionBundle82CR[]:={
DownValues[P59],DownValues[A59],DownValues[T59],DownValues[Case59],
OwnValues[rw60],DownValues[Pack60],DownValues[SigLevels61],
DownValues[PropagationSafetyCap78],DownValues[RejectTrace78],
DownValues[DecisionStatePairsFromRejects78],DownValues[EncodeRows75],
DownValues[DiamondIn72],DownValues[DoubleDiamondIn79],DownValues[Case79]
};

minimalKernelDefinitionTextHash82CR=Hash[
ToString[InputForm[CoreDefinitionBundle82CR[]]],
"SHA256","HexString"
];

stableFrozenArchitectureHash82CR=Hash[
{
Normal[frozen75D],
minimalKernelDefinitionTextHash82CR,
canonicalizerImplementationHash79B
},
"SHA256","HexString"
];

preflightPassed82CR=And[
SameQ[modelHash79A,expectedFrozenModelHash79A],
SameQ[
minimalKernelDefinitionTextHash82CR,
expectedMinimalKernelDefinitionTextHash82CR
],
SameQ[canonicalizerImplementationHash79B,expectedCanonicalizerHash82CR],
SameQ[
stableFrozenArchitectureHash82CR,
expectedStableFrozenArchitectureHash82CR
],
SameQ[interventionImplementationHash82,expectedInterventionHash82CR]
];

preflight82CR=<|
"Stage"->"S82C-Recovery",
"Name"->"FrozenCandidateDeterministicRecovery",
"OriginalFrozenModelChanged"->False,
"CoreChanged"->False,
"CandidateSearchRun"->False,
"S83RowsLoaded"->False,
"S83LabelsLoaded"->False,
"PreflightPassed"->preflightPassed82CR
|>;

If[
!TrueQ[preflightPassed82CR],
Print[Dataset[{preflight82CR}]];
Print["Recovery aborted: frozen architecture mismatch."];
Abort[]
];

Dataset[{preflight82CR}]
'''.strip() + "\n"

cell2 = capacity_functions + r'''

recoveryGrammars82CR={
"S59","ChainIn","SharedMerge","ParallelIn",
"ParallelOut","DiamondIn","SharedParallelIn"
};
recoveryDepths82CR={2,5,9,15};
recoveryStressDepths82CR={2,5};
fixedCandidateSpec82CR=<|
"Name"->"K10ExactRole",
"Type"->"KExactRole",
"K"->10
|>;

protocol82CR=<|
"Stage"->"S82C-Recovery",
"Name"->"FrozenCandidateDeterministicRecovery",
"Purpose"->"RecoverLostInMemoryCandidateFromLockedDevelopmentProtocol",
"ExpectedCandidateHash"->expectedCandidateHash82CR,
"FixedRepresentation"->"KExactRole",
"FixedK"->10,
"GrammarOrder"->recoveryGrammars82CR,
"Depths"->recoveryDepths82CR,
"StressDepths"->recoveryStressDepths82CR,
"StopAsSoonAsExpectedCandidateHashMatches"->True,
"CandidateSearchRun"->False,
"HyperparameterSearchRun"->False,
"PolicyEditApplied"->False,
"S82BlindRowsLoaded"->False,
"S82BlindLabelsLoaded"->False,
"S83RowsLoaded"->False,
"S83LabelsLoaded"->False
|>;

protocolHash82CR=Hash[Normal[protocol82CR],"SHA256","HexString"];
modelHashBefore82CR=Hash[Normal[frozen75D],"SHA256","HexString"];
coreHashBefore82CR=Hash[CoreDefinitionBundle82CR[],"SHA256","HexString"];
canonicalizerHashBefore82CR=canonicalizerImplementationHash79B;
interventionHashBefore82CR=interventionImplementationHash82;

Dataset[{Join[protocol82CR,<|
"ProtocolHash"->protocolHash82CR,
"NoRecoveryRowEvaluatedBeforeProtocolHash"->True
|>]}]
'''.strip() + "\n"

cell3 = r'''
ClearAll[BuildFrozenCandidate82CR];

BuildFrozenCandidate82CR[policy_List]:=<|
"Stage"->"S82C",
"Name"->"CapacityRepairedQueryRoleCandidate",
"BaseFrozenModelHash"->expectedFrozenModelHash79A,
"EncoderParams"->frozen75D["Params"],
"Representation"->"KExactRole",
"K"->10,
"Policy"->policy,
"ExactNodeRoleUsed"->True,
"S82BlindLabelsUsedForSelection"->False,
"FrozenBeforeS83"->True
|>;

stressRows82CR=Flatten[
Table[
PrepareCapacityRow82C[
"LocalMediatorDevelopment",depth,answer,"Stop",
ApplyEdgePatch81[
Case59[depth,answer,"Continue"],
LocalMediatorPatch82[depth,answer]
]
],
{depth,recoveryStressDepths82CR},
{answer,Range[4]}
],
1
];

recoveryRows82CR={};
recoveryProgress82CR={};
recoveredCandidate82CR=Missing["NotRecovered"];
recoveredCandidateHash82CR=Missing["NotRecovered"];
recoveryMatched82CR=False;
grammarsNeeded82CR={};

Do[
rowsForGrammar82CR=Flatten[
Table[
PrepareCapacityRow82C[
grammar,depth,answer,target,
CaseByGrammar82C[grammar,depth,answer,target]
],
{depth,recoveryDepths82CR},
{answer,Range[4]},
{target,{"Continue","Stop"}}
],
2
];
recoveryRows82CR=Join[recoveryRows82CR,rowsForGrammar82CR];
grammarsNeeded82CR=Append[grammarsNeeded82CR,grammar];
currentTokenRows82CR=TokenizedRows82C[
Join[recoveryRows82CR,stressRows82CR],
fixedCandidateSpec82CR
];
currentPolicy82CR=SafePolicy82C[currentTokenRows82CR];
recoveredCandidate82CR=BuildFrozenCandidate82CR[currentPolicy82CR];
recoveredCandidateHash82CR=Hash[
Normal[recoveredCandidate82CR],"SHA256","HexString"
];
recoveryMatched82CR=SameQ[
recoveredCandidateHash82CR,expectedCandidateHash82CR
];
recoveryProgress82CR=Append[
recoveryProgress82CR,
<|
"GrammarAdded"->grammar,
"GrammarsUsed"->Length[grammarsNeeded82CR],
"LegacyRowsUsed"->Length[recoveryRows82CR],
"StressRowsUsed"->Length[stressRows82CR],
"PolicyLength"->Length[currentPolicy82CR],
"CandidateHashMatched"->recoveryMatched82CR
|>
];
If[TrueQ[recoveryMatched82CR],Break[]],
{grammar,recoveryGrammars82CR}
];

recoveryTokenRows82CR=If[
TrueQ[recoveryMatched82CR],
TokenizedRows82C[
Join[recoveryRows82CR,stressRows82CR],fixedCandidateSpec82CR
],
{}
];
recoveryScore82CR=If[
TrueQ[recoveryMatched82CR],
ScoreRows82C[recoveryTokenRows82CR,recoveredCandidate82CR["Policy"]],
0
];

candidateSnapshotPath82CR=
"E:/engine_wolf/TCCT_S82C_FrozenCandidate.wl";

If[
TrueQ[recoveryMatched82CR],
Export[
candidateSnapshotPath82CR,
"frozenCandidate82C="<>
ToString[InputForm[recoveredCandidate82CR]]<>";\n",
"Text"
]
];

modelHashAfter82CR=Hash[Normal[frozen75D],"SHA256","HexString"];
coreHashAfter82CR=Hash[CoreDefinitionBundle82CR[],"SHA256","HexString"];
canonicalizerHashAfter82CR=Hash[
{
DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],
DownValues[CanonicalCase79B]
},
"SHA256","HexString"
];
interventionHashAfter82CR=Hash[
{
DownValues[LocalMediatorSources82],
DownValues[FullSemanticPatch82],
DownValues[LocalMediatorPatch82],
DownValues[ReferenceAction82]
},
"SHA256","HexString"
];
protocolHashAfter82CR=Hash[Normal[protocol82CR],"SHA256","HexString"];

integrityPassed82CR=And[
SameQ[modelHashBefore82CR,modelHashAfter82CR],
SameQ[modelHashAfter82CR,expectedFrozenModelHash79A],
SameQ[coreHashBefore82CR,coreHashAfter82CR],
SameQ[canonicalizerHashBefore82CR,canonicalizerHashAfter82CR],
SameQ[canonicalizerHashAfter82CR,expectedCanonicalizerHash82CR],
SameQ[interventionHashBefore82CR,interventionHashAfter82CR],
SameQ[interventionHashAfter82CR,expectedInterventionHash82CR],
SameQ[protocolHash82CR,protocolHashAfter82CR]
];

recoverySucceeded82CR=And[
TrueQ[preflightPassed82CR],
TrueQ[integrityPassed82CR],
TrueQ[recoveryMatched82CR],
SameQ[
recoveryScore82CR,
Length[recoveryTokenRows82CR]
],
FileExistsQ[candidateSnapshotPath82CR]
];

cert82CR=<|
"Stage"->"S82C-Recovery",
"Name"->"FrozenCandidateDeterministicRecovery",
"GrammarsNeeded"->grammarsNeeded82CR,
"LegacyRowsRecomputed"->Length[recoveryRows82CR],
"StressRowsRecomputed"->Length[stressRows82CR],
"RowsCorrect"->recoveryScore82CR,
"RowsChecked"->Length[recoveryTokenRows82CR],
"RecoveredPolicyLength"->If[
AssociationQ[recoveredCandidate82CR],
Length[recoveredCandidate82CR["Policy"]],
Missing["NoPolicy"]
],
"ExpectedCandidateHash"->expectedCandidateHash82CR,
"RecoveredCandidateHash"->recoveredCandidateHash82CR,
"CandidateHashMatched"->recoveryMatched82CR,
"CandidateFileExported"->FileExistsQ[candidateSnapshotPath82CR],
"CandidateFile"->candidateSnapshotPath82CR,
"OriginalFrozenModelChanged"->!SameQ[
modelHashBefore82CR,modelHashAfter82CR
],
"CoreChanged"->!SameQ[coreHashBefore82CR,coreHashAfter82CR],
"CanonicalizerChanged"->!SameQ[
canonicalizerHashBefore82CR,canonicalizerHashAfter82CR
],
"InterventionChanged"->!SameQ[
interventionHashBefore82CR,interventionHashAfter82CR
],
"CandidateSearchRun"->False,
"HyperparameterSearchRun"->False,
"PolicyEditApplied"->False,
"S82BlindRowsLoaded"->False,
"S83RowsLoaded"->False,
"IntegrityPassed"->integrityPassed82CR,
"RecoverySucceeded"->recoverySucceeded82CR,
"Outcome"->If[
TrueQ[recoverySucceeded82CR],
"FROZEN_CANDIDATE_RECOVERED",
"RECOVERY_FAILED_DO_NOT_RUN_S83"
]
|>;

Column[{
Dataset[recoveryProgress82CR],
Dataset[{cert82CR}]
}]
'''.strip() + "\n"

cells = [cell1, cell2, cell3]
wl_source = "\n\n".join(f"{MARKER}\n{cell}" for cell in cells)

for forbidden in (
    "stressValidationRows82C=",
    "capacityResults82C=",
    "selectedCapacityCandidate82C=",
    "blindCounterfactualPairs82=",
    "blindDepths82=",
    "blindPairs83=",
    "blindDepths83=",
):
    if forbidden in wl_source:
        raise RuntimeError(f"Blind or selection material leaked into recovery: {forbidden}")

if wl_source.index("protocolHash82CR=") > wl_source.index("stressRows82CR="):
    raise RuntimeError("Recovery rows would be evaluated before protocol hashing")

WL_OUTPUT.write_text(wl_source, encoding="utf-8")

notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# TCCT S82C — Frozen Candidate Recovery\n",
                "\n",
                "该 Notebook 只恢复因内核重启而丢失的 S82C 冻结候选文件。它固定 K=10 和 KExactRole，不搜索新模型；按原开发语法逐批恢复，并在候选哈希完全等于既定哈希时立即停止。\n",
                "\n",
                "不读取 S82 盲测或 S83 数据。恢复成功后再运行 S83。\n",
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
