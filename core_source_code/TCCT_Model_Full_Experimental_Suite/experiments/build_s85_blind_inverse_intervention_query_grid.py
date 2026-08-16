import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
S84_SOURCE = ROOT / "TCCT_S84_BlindDoubleInterventionQueryGrid.wl"
WL_OUTPUT = ROOT / "TCCT_S85_BlindInverseInterventionQueryGrid.wl"
NB_OUTPUT = ROOT / "TCCT_S85_BlindInverseInterventionQueryGrid_AutoRun.ipynb"


source84 = S84_SOURCE.read_text(encoding="utf-8")
if source84.count("(* S84 CELL *)") != 4:
    raise RuntimeError("S84 source no longer has exactly four code cells")

# S85 deliberately reuses the already audited S84 harness structure, but
# reverses the intervention direction and changes depths/topology grid. It does
# not import any S84 runtime result, score, label, or certificate.
source85 = source84.replace("(* S84 CELL *)", "(* S85 CELL *)")
source85 = source85.replace("84", "85")
# The stage-number rename above must never rewrite opaque hash payloads. The
# locked S84 architecture hash happens to contain the digit pair "84".
source85 = source85.replace(
    "d7d16575e25bd1090e35485931dedae9f80254475ee49cd2d79d43f5d4d1355d",
    "d7d16575e25bd1090e35484931dedae9f80254475ee49cd2d79d43f5d4d1355d",
)
source85 = source85.replace(
    "BlindDoubleInterventionQueryGrid",
    "BlindInverseInterventionQueryGrid",
)
source85 = source85.replace("BranchStopPatch85", "BranchContinuePatch85")
source85 = source85.replace("DoubleBranchPatch85", "DoubleRestorePatch85")
source85 = source85.replace("patchedBranches", "restoredBranches")
source85 = source85.replace("PatchedBranches", "RestoredBranches")
source85 = source85.replace("PatchedBranchPairs", "RestoredBranchPairs")
source85 = source85.replace("PatchedQuery", "RestoredQuery")
source85 = source85.replace("UnpatchedQuery", "UnrestoredQuery")
source85 = source85.replace("PatchComponentValidity", "RestoreComponentValidity")
source85 = source85.replace("PatchNoConflict", "RestoreNoConflict")
source85 = source85.replace("PatchEditCountCorrect", "RestoreEditCountCorrect")
source85 = source85.replace("PatchChangesGraph", "RestorationChangesGraph")

# The candidate was physically frozen before S84 and remains bit-identical for
# S85. Keep the actual candidate metadata key instead of inventing a new one.
source85 = source85.replace(
    'frozenCandidate83B["FrozenBeforeS85"]',
    'frozenCandidate83B["FrozenBeforeS84"]',
)

old_topology_transform = r'''TopologyTransform85[topology_String,c_List]:=Switch[
topology,
"DoubleDiamondIn",DoubleDiamondIn79[c],
"HierarchicalDiamondIn",HierarchicalDiamondIn80[c],
_,$Failed
];'''
new_topology_transform = r'''TopologyTransform85[topology_String,c_List]:=Switch[
topology,
"DiamondIn",DiamondIn72[c],
"DoubleDiamondIn",DoubleDiamondIn79[c],
_,$Failed
];'''
if old_topology_transform not in source85:
    raise RuntimeError("S85 topology transform source pattern not found")
source85 = source85.replace(old_topology_transform, new_topology_transform)

old_expected_contractions = r'''ExpectedContractions85[topology_String,baseCase_List]:=Switch[
topology,
"DoubleDiamondIn",2 DecisionIncomingEdgeCount79B[baseCase],
"HierarchicalDiamondIn",3 DecisionIncomingEdgeCount79B[baseCase],
_,Missing["UnknownTopology"]
];'''
new_expected_contractions = r'''ExpectedContractions85[topology_String,baseCase_List]:=Switch[
topology,
"DiamondIn",DecisionIncomingEdgeCount79B[baseCase],
"DoubleDiamondIn",2 DecisionIncomingEdgeCount79B[baseCase],
_,Missing["UnknownTopology"]
];'''
if old_expected_contractions not in source85:
    raise RuntimeError("S85 contraction source pattern not found")
source85 = source85.replace(old_expected_contractions, new_expected_contractions)

old_edge_direction = r'''remove={
DirectedEdge[m,correct],
DirectedEdge[safe,dummy],
DirectedEdge[u,wrong]
};
add={
DirectedEdge[m,wrong],
DirectedEdge[safe,correct],
DirectedEdge[u,dummy]
};'''
new_edge_direction = r'''remove={
DirectedEdge[m,wrong],
DirectedEdge[safe,correct],
DirectedEdge[u,dummy]
};
add={
DirectedEdge[m,correct],
DirectedEdge[safe,dummy],
DirectedEdge[u,wrong]
};'''
if old_edge_direction not in source85:
    raise RuntimeError("S85 branch edge direction source pattern not found")
source85 = source85.replace(old_edge_direction, new_edge_direction)

source85 = source85.replace(
    'seedCase=Case59[depth,1,"Continue"];',
    'seedCase=Case59[depth,1,"Stop"];',
)
source85 = source85.replace(
    'topology,depth,restoredBranches,"Baseline",answer,"Continue",',
    'topology,depth,restoredBranches,"Baseline",answer,"Stop",',
)
source85 = source85.replace(
    'If[MemberQ[restoredBranches,answer],"Stop","Continue"],',
    'If[MemberQ[restoredBranches,answer],"Continue","Stop"],',
)

old_reference_relation = r'''If[
MemberQ[restoredBranches,base["Answer"]],
And[
SameQ[base["ReferenceAction"],"Continue"],
SameQ[hybrid["ReferenceAction"],"Stop"]
],
And[
SameQ[base["ReferenceAction"],"Continue"],
SameQ[hybrid["ReferenceAction"],"Continue"]
]
]'''
new_reference_relation = r'''If[
MemberQ[restoredBranches,base["Answer"]],
And[
SameQ[base["ReferenceAction"],"Stop"],
SameQ[hybrid["ReferenceAction"],"Continue"]
],
And[
SameQ[base["ReferenceAction"],"Stop"],
SameQ[hybrid["ReferenceAction"],"Stop"]
]
]'''
if source85.count(old_reference_relation) != 1:
    raise RuntimeError("S85 reference relation source pattern mismatch")
source85 = source85.replace(old_reference_relation, new_reference_relation)

old_prediction_relation = r'''If[
MemberQ[restoredBranches,base["Answer"]],
And[
SameQ[base["Prediction"],"Continue"],
SameQ[hybrid["Prediction"],"Stop"]
],
And[
SameQ[base["Prediction"],"Continue"],
SameQ[hybrid["Prediction"],"Continue"]
]
]'''
new_prediction_relation = r'''If[
MemberQ[restoredBranches,base["Answer"]],
And[
SameQ[base["Prediction"],"Stop"],
SameQ[hybrid["Prediction"],"Continue"]
],
And[
SameQ[base["Prediction"],"Stop"],
SameQ[hybrid["Prediction"],"Stop"]
]
]'''
if source85.count(old_prediction_relation) != 1:
    raise RuntimeError("S85 prediction relation source pattern mismatch")
source85 = source85.replace(old_prediction_relation, new_prediction_relation)

source85 = source85.replace('"DoubleIntervention"', '"InverseDoubleRestoration"')
source85 = source85.replace("blindDepths85={29,53};", "blindDepths85={31,59};")
source85 = source85.replace(
    'blindTopologies85={"DoubleDiamondIn","HierarchicalDiamondIn"};',
    'blindTopologies85={"DiamondIn","DoubleDiamondIn"};',
)
source85 = source85.replace(
    '"Intervention"->"TwoSimultaneousBranchStopPatches"',
    '"Intervention"->"TwoSimultaneousInverseBranchRestorations"',
)
source85 = source85.replace(
    '"QueryGrid"->"AllFourQueriesBeforeAndAfterIntervention"',
    '"QueryGrid"->"AllFourQueriesBeforeAndAfterInverseIntervention"',
)
source85 = source85.replace(
    '{DownValues[DoubleDiamondIn79],DownValues[HierarchicalDiamondIn80]}',
    '{DownValues[DiamondIn72],DownValues[DoubleDiamondIn79]}',
)
source85 = source85.replace(
    '"S83BlindRerun"->False,',
    '"S83BlindRerun"->False,\n"S84BlindRerun"->False,',
)
source85 = source85.replace(
    '"DoubleInterventionNovel"->True,',
    '"InverseInterventionDirectionNovel"->True,',
)
source85 = source85.replace(
    '"MayClaimBlindMultiInterventionCounterfactualComposition"',
    '"MayClaimBlindInverseInterventionCounterfactualComposition"',
)
source85 = source85.replace(
    '"BLIND_DOUBLE_INTERVENTION_QUERY_GRID_PASS"',
    '"BLIND_INVERSE_INTERVENTION_QUERY_GRID_PASS"',
)
source85 = source85.replace(
    '"VALID_BLIND_DOUBLE_INTERVENTION_QUERY_GRID_FAILURE"',
    '"VALID_BLIND_INVERSE_INTERVENTION_QUERY_GRID_FAILURE"',
)
source85 = source85.replace(
    '"S86_INDEPENDENT_INTERVENTION_OPERATOR_BLIND_TEST"',
    '"S86_COUNTERFACTUAL_CHECKPOINT_AND_EXTERNAL_GRAMMAR_TEST"',
)

# S85 reverses direction. Therefore baseline Stop count is 96, while restored
# Continue and unrestored Stop counts remain 48 each. Existing summary field
# names still state the target action and need no numeric change.

for forbidden in (
    "blindScenarios84=",
    "summary84=",
    "cert84=",
    "blindResultHash84=",
    "b4f5665ae614ed45ead125da26c55d16ffa579f88eafb155b9b9d115bd959740",
):
    if forbidden in source85:
        raise RuntimeError(f"S84 runtime material leaked into S85: {forbidden}")

if source85.index("protocolHash85=") > source85.index("blindScenarios85="):
    raise RuntimeError("S85 cases would be evaluated before protocol hashing")

WL_OUTPUT.write_text(source85, encoding="utf-8")

parts = source85.split("(* S85 CELL *)")
if len(parts) != 5:
    raise RuntimeError("Generated S85 source does not have four cells")
cells = [part.strip() + "\n" for part in parts[1:]]

notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# TCCT S85 — Blind Inverse-Intervention Query Grid\n",
                "\n",
                "The same frozen K=19 candidate is tested in the unseen reverse "
                "direction: an all-Stop graph is partially restored to Continue on "
                "two branches, with every query checked before and after restoration.\n",
                "\n",
                "No policy search or edit is permitted. Core propagation, canonicalization, "
                "intervention primitives, topology functions, and token deduplication remain "
                "hash-locked.\n",
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
