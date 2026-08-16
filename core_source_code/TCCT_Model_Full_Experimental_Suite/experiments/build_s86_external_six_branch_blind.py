import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
S84_SOURCE = ROOT / "TCCT_S84_BlindDoubleInterventionQueryGrid.wl"
WL_OUTPUT = ROOT / "TCCT_S86_ExternalSixBranchBlind.wl"
NB_OUTPUT = ROOT / "TCCT_S86_ExternalSixBranchBlind.ipynb"
AUTORUN_OUTPUT = ROOT / "TCCT_S86_ExternalSixBranchBlind_AutoRun.ipynb"
PREFLIGHT_OUTPUT = ROOT / "TCCT_S86_ExternalSixBranchBlind_Preflight_AutoRun.ipynb"


source84 = S84_SOURCE.read_text(encoding="utf-8")
if source84.count("(* S84 CELL *)") != 4:
    raise RuntimeError("S84 source no longer has exactly four code cells")

# Reuse the audited S84 harness structure only. This file contains definitions,
# not S84 runtime values. The frozen K=19 candidate remains unchanged.
source86 = source84.replace("(* S84 CELL *)", "(* S86 CELL *)")
source86 = source86.replace("84", "86")

# Restore the opaque stable-architecture hash that contains the digits "84".
source86 = source86.replace(
    "d7d16575e25bd1090e35486931dedae9f80254475ee49cd2d79d43f5d4d1355d",
    "d7d16575e25bd1090e35484931dedae9f80254475ee49cd2d79d43f5d4d1355d",
)

source86 = source86.replace(
    "BlindDoubleInterventionQueryGrid",
    "ExternalSixBranchBlind",
)
source86 = source86.replace(
    'frozenCandidate83B["FrozenBeforeS86"]',
    'frozenCandidate83B["FrozenBeforeS84"]',
)

clear_marker = r'''ClearAll[
NodeRole86,'''
if clear_marker not in source86:
    raise RuntimeError("S86 ClearAll insertion point not found")
source86 = source86.replace(
    clear_marker,
    r'''ClearAll[
T86,
Case86,
ReferenceAction86,
NodeRole86,''',
    1,
)

node_role_marker = "NodeRole86[originalNode_,case_List,answer_Integer]:=Module["
if node_role_marker not in source86:
    raise RuntimeError("S86 external grammar insertion point not found")

external_grammar = r'''
T86[
depth_Integer,
target_String,
answer_Integer,
seed_Integer,
branchCount_Integer
]:=Module[
{
bb,K,c,v,q,e,f={},ib,m,safe,u,dummy,r1,r2,wrong,
main,perm,anc,i
},
bb=1000000000 seed;
K=bb+1;
c=Table[bb+100+i,{i,branchCount}];
v=Table[bb+200+i,{i,branchCount}];
q=Table[bb+300+i,{i,branchCount}];
e=Flatten[
Table[
{
DirectedEdge[K,c[[i]]],
DirectedEdge[c[[i]],v[[i]]]
},
{i,branchCount}
],
1
];
Do[
ib=bb+20000000 i;
m=ib+1;
safe=ib+2;
u=ib+3;
dummy=ib+4;
r1=ib+10;
r2=ib+20;
wrong=c[[1+Mod[i,branchCount]]];
main=Join[
P59[q[[i]],r1,depth,ib+1000000],
P59[q[[i]],r2,depth,ib+2000000],
{
DirectedEdge[r1,m],
DirectedEdge[r2,m]
},
P59[q[[i]],safe,depth+1,ib+3000000]
];
perm=If[
target==="Continue",
{
DirectedEdge[m,c[[i]]],
DirectedEdge[safe,dummy],
DirectedEdge[u,wrong]
},
{
DirectedEdge[m,wrong],
DirectedEdge[safe,c[[i]]],
DirectedEdge[u,dummy]
}
];
anc=Join[
A59[m,i,bb+970000000+10000 i],
A59[c[[i]],i,bb+980000000+10000 i]
];
e=Join[e,main,perm,anc];
AppendTo[f,m],
{i,branchCount}
];
{{Union[e],q,K,v,c,f},answer}
];

Case86[depth_Integer,answer_Integer,target_String]:=
T86[depth,target,answer,86000000+100 depth,6];

ReferenceAction86[c_List]:=Module[
{
x=c[[1]],answer=c[[2]],branchCount,e,m,safe,u,dummy,
correct,wrong,continueEdges,stopEdges
},
branchCount=Length[x[[6]]];
e=x[[1]];
m=x[[6,answer]];
safe=m+1;
u=m+2;
dummy=m+3;
correct=x[[5,answer]];
wrong=x[[5,1+Mod[answer,branchCount]]];
continueEdges={
DirectedEdge[m,correct],
DirectedEdge[safe,dummy],
DirectedEdge[u,wrong]
};
stopEdges={
DirectedEdge[m,wrong],
DirectedEdge[safe,correct],
DirectedEdge[u,dummy]
};
Which[
And@@Map[MemberQ[e,#]&,continueEdges],"Continue",
And@@Map[MemberQ[e,#]&,stopEdges],"Stop",
True,"Undefined"
]
];

'''
source86 = source86.replace(node_role_marker, external_grammar + node_role_marker, 1)

old_node_locals = "{x,m,correct,wrong,dummy,querySources,queryBranch,role},"
new_node_locals = (
    "{x,branchCount,m,correct,wrong,dummy,querySources,queryBranch,role},"
)
if source86.count(old_node_locals) != 1:
    raise RuntimeError("S86 NodeRole local variables pattern mismatch")
source86 = source86.replace(old_node_locals, new_node_locals)
source86 = source86.replace(
    "x=case[[1]];\nm=x[[6,answer]];",
    "x=case[[1]];\nbranchCount=Length[x[[6]]];\nm=x[[6,answer]];",
    1,
)

# Generalize only the new S86 query-role helper. The earlier ReferenceAction82
# is part of the locked intervention primitive and must remain byte-for-byte
# behaviorally identical, including its original four-branch modulo.
external_layer_start = source86.index("T86[")
locked_prefix = source86[:external_layer_start]
external_layer = source86[external_layer_start:]
if locked_prefix.count("1+Mod[answer,4]") != 1:
    raise RuntimeError("Locked ReferenceAction82 modulo pattern mismatch")
if external_layer.count("1+Mod[answer,4]") != 1:
    raise RuntimeError("S86 NodeRole modulo pattern mismatch")
external_layer = external_layer.replace(
    "1+Mod[answer,4]", "1+Mod[answer,branchCount]", 1
)
source86 = locked_prefix + external_layer
if source86.count("1+Mod[branch,4]") != 1:
    raise RuntimeError("S86 expected one branch-patch modulo-4 helper")
source86 = source86.replace("1+Mod[branch,4]", "1+Mod[branch,branchCount]")

old_patch_locals = "{x,e,m,safe,u,dummy,correct,wrong,remove,add},"
new_patch_locals = (
    "{x,branchCount,e,m,safe,u,dummy,correct,wrong,remove,add},"
)
if source86.count(old_patch_locals) != 1:
    raise RuntimeError("S86 patch local variables pattern mismatch")
source86 = source86.replace(old_patch_locals, new_patch_locals)
source86 = source86.replace(
    "x=c[[1]];\ne=x[[1]];",
    "x=c[[1]];\nbranchCount=Length[x[[6]]];\ne=x[[1]];",
    1,
)

source86 = source86.replace(
    '"ReferenceAction"->ReferenceAction82[canonicalCase],',
    '"ReferenceAction"->ReferenceAction86[canonicalCase],\n'
    '"BranchCount"->Length[canonicalCase[[1,6]]],',
)
source86 = source86.replace(
    'seedCase=Case59[depth,1,"Continue"];',
    'seedCase=Case86[depth,1,"Continue"];',
)

old_scenario_locals = r'''{
seedCase,patch,hybridSeed,baseWorlds,hybridWorlds,
worldPairs,baseGraphHashes,hybridGraphHashes
},'''
new_scenario_locals = r'''{
branchCount=6,seedCase,patch,hybridSeed,baseWorlds,hybridWorlds,
worldPairs,baseGraphHashes,hybridGraphHashes
},'''
if source86.count(old_scenario_locals) != 1:
    raise RuntimeError("S86 scenario local variables pattern mismatch")
source86 = source86.replace(old_scenario_locals, new_scenario_locals)

# Only the two per-scenario query grids should change from four to six.
if source86.count("{answer,Range[4]}") != 2:
    raise RuntimeError("S86 expected two four-query grids")
source86 = source86.replace("{answer,Range[4]}", "{answer,Range[branchCount]}")

old_bundle = r'''S86TestDefinitionBundle[]:={
DownValues[NodeRole86],DownValues[EncodePair86],DownValues[PredictTokens86],'''
new_bundle = r'''S86TestDefinitionBundle[]:={
DownValues[T86],DownValues[Case86],DownValues[ReferenceAction86],
DownValues[NodeRole86],DownValues[EncodePair86],DownValues[PredictTokens86],'''
if old_bundle not in source86:
    raise RuntimeError("S86 test bundle pattern not found")
source86 = source86.replace(old_bundle, new_bundle)

source86 = source86.replace("blindDepths86={29,53};", "blindDepths86={43,71};")
source86 = source86.replace(
    "blindPatchedBranchPairs86=Subsets[Range[4],{2}];",
    "blindPatchedBranchPairs86={{1,2},{2,3},{3,4},{4,5},{5,6},{1,6}};",
)

protocol_replacements = {
    '"ExpectedScenarios"->24,\n"ExpectedWorldPairs"->96,\n"ExpectedWorlds"->192,': (
        '"BranchCount"->6,\n"ExpectedScenarios"->24,\n'
        '"ExpectedWorldPairs"->144,\n"ExpectedWorlds"->288,'
    ),
    '"ExpectedPatchedQueryPairs"->48,\n"ExpectedUnpatchedQueryPairs"->48,': (
        '"ExpectedPatchedQueryPairs"->48,\n'
        '"ExpectedUnpatchedQueryPairs"->96,'
    ),
    '"Intervention"->"TwoSimultaneousBranchStopPatches",': (
        '"ExternalGrammar"->"IndependentSixBranchT86",\n'
        '"Intervention"->"TwoSimultaneousBranchStopPatches",'
    ),
    '"QueryGrid"->"AllFourQueriesBeforeAndAfterIntervention",': (
        '"QueryGrid"->"AllSixQueriesBeforeAndAfterIntervention",'
    ),
    '"S83BlindRerun"->False,': (
        '"S83BlindRerun"->False,\n"S84BlindRerun"->False,\n'
        '"S85BlindRerun"->False,'
    ),
}
for old, new in protocol_replacements.items():
    if old not in source86:
        raise RuntimeError(f"S86 protocol pattern not found: {old}")
    source86 = source86.replace(old, new)

# Add an explicit six-branch validity count immediately before total trace time.
summary_insert = r'''"HitSafetyCap"->Count[
blindWorlds86,w_/;TrueQ[w["HitSafetyCap"]]
],
"TotalTraceSeconds"->Total@Lookup[blindWorlds86,"TraceSeconds"]'''
summary_replacement = r'''"HitSafetyCap"->Count[
blindWorlds86,w_/;TrueQ[w["HitSafetyCap"]]
],
"SixBranchWorlds"->Count[
blindWorlds86,w_/;SameQ[w["BranchCount"],6]
],
"TotalTraceSeconds"->Total@Lookup[blindWorlds86,"TraceSeconds"]'''
if summary_insert not in source86:
    raise RuntimeError("S86 summary insertion point not found")
source86 = source86.replace(summary_insert, summary_replacement)

validity_replacements = {
    'SameQ[summary86["WorldPairs"],96]': 'SameQ[summary86["WorldPairs"],144]',
    'SameQ[summary86["Worlds"],192]': 'SameQ[summary86["Worlds"],288]',
    'SameQ[summary86["UnpatchedQueryPairs"],48]': (
        'SameQ[summary86["UnpatchedQueryPairs"],96]'
    ),
    'SameQ[summary86["ReferenceRelationsCorrect"],96]': (
        'SameQ[summary86["ReferenceRelationsCorrect"],144]'
    ),
    'SameQ[summary86["CanonicalCaseExactlyBase"],192]': (
        'SameQ[summary86["CanonicalCaseExactlyBase"],288]'
    ),
    'SameQ[summary86["ContractionCountCorrect"],192]': (
        'SameQ[summary86["ContractionCountCorrect"],288]'
    ),
    'SameQ[summary86["ProtectedNodesPreserved"],192]': (
        'SameQ[summary86["ProtectedNodesPreserved"],288]'
    ),
    'SameQ[summary86["ReferenceActionsCorrect"],192]': (
        'SameQ[summary86["ReferenceActionsCorrect"],288]'
    ),
    'SameQ[summary86["NonEmptyTokens"],192]': (
        'SameQ[summary86["NonEmptyTokens"],288]'
    ),
    'SameQ[summary86["TerminatedNaturally"],192]': (
        'SameQ[summary86["TerminatedNaturally"],288]'
    ),
    'SameQ[summary86["BaselineCorrect"],96]': (
        'SameQ[summary86["BaselineCorrect"],144]'
    ),
    'SameQ[summary86["InterventionContinueCorrect"],48]': (
        'SameQ[summary86["InterventionContinueCorrect"],96]'
    ),
    'SameQ[summary86["WorldCorrect"],192]': (
        'SameQ[summary86["WorldCorrect"],288]'
    ),
    'SameQ[summary86["PairCorrect"],96]': (
        'SameQ[summary86["PairCorrect"],144]'
    ),
    'SameQ[summary86["PredictionRelationsCorrect"],96]': (
        'SameQ[summary86["PredictionRelationsCorrect"],144]'
    ),
}
for old, new in validity_replacements.items():
    if source86.count(old) != 1:
        raise RuntimeError(f"S86 validity pattern mismatch: {old}")
    source86 = source86.replace(old, new)

validity_anchor = 'SameQ[summary86["HitSafetyCap"],0]\n];'
if validity_anchor not in source86:
    raise RuntimeError("S86 six-branch validity anchor not found")
source86 = source86.replace(
    validity_anchor,
    'SameQ[summary86["HitSafetyCap"],0],\n'
    'SameQ[summary86["SixBranchWorlds"],288]\n];',
)

source86 = source86.replace(
    '"DoubleInterventionNovel"->True,',
    '"ExternalSixBranchGrammarNovel"->True,',
)
source86 = source86.replace(
    '"AllQueryRolesTestedPerGraph"->True,',
    '"AllSixQueryRolesTestedPerGraph"->True,',
)
source86 = source86.replace(
    '"AllEightWorldsCorrect"',
    '"AllTwelveWorldsCorrect"',
)
source86 = source86.replace(
    '"MayClaimBlindMultiInterventionCounterfactualComposition"',
    '"MayClaimBlindSixBranchCounterfactualTransfer"',
)
source86 = source86.replace(
    '"BLIND_DOUBLE_INTERVENTION_QUERY_GRID_PASS"',
    '"BLIND_EXTERNAL_SIX_BRANCH_PASS"',
)
source86 = source86.replace(
    '"VALID_BLIND_DOUBLE_INTERVENTION_QUERY_GRID_FAILURE"',
    '"VALID_BLIND_EXTERNAL_SIX_BRANCH_FAILURE"',
)
source86 = source86.replace(
    '"S85_INDEPENDENT_INTERVENTION_OPERATOR_BLIND_TEST"',
    '"S87_PATH_CUT_INTERVENTION_BLIND_TEST"',
)

# This is an external grammar test, not a new candidate or a core revision.
for forbidden in (
    "blindScenarios84=",
    "summary84=",
    "cert84=",
    "blindResultHash84=",
    "selectedRepresentation83B=",
    "semanticDevelopmentRows83B=",
    "capacityResults83B=",
):
    if forbidden in source86:
        raise RuntimeError(f"Prior blind/development runtime leaked into S86: {forbidden}")

test_harness_source = source86[source86.index("T86["):]
if any(
    forbidden in test_harness_source
    for forbidden in ("Mod[answer,4]", "Mod[branch,4]", "Range[4]")
):
    raise RuntimeError("A hard-coded four-branch query helper remains in S86")

if source86.index("protocolHash86=") > source86.index("blindScenarios86="):
    raise RuntimeError("S86 cases would be evaluated before protocol hashing")

WL_OUTPUT.write_text(source86, encoding="utf-8")

parts = source86.split("(* S86 CELL *)")
if len(parts) != 5:
    raise RuntimeError("Generated S86 source does not have four cells")
cells = [part.strip() + "\n" for part in parts[1:]]

markdown = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "# TCCT S86 — External Six-Branch Blind Test\n",
        "\n",
        "The frozen S83B K=19 exact-role candidate is evaluated on an independently "
        "defined six-branch grammar. Every graph is queried on all six branches before "
        "and after a balanced two-branch Continue-to-Stop intervention.\n",
        "\n",
        "No candidate search, K change, policy edit, retraining, or historical rerun is "
        "permitted. Core propagation, canonicalization, topology implementations, the "
        "frozen candidate, and DeleteDuplicates behavior are hash-locked.\n",
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
preflight_notebook["cells"] = [markdown, notebook["cells"][1], notebook["cells"][2]]
PREFLIGHT_OUTPUT.write_text(
    json.dumps(preflight_notebook, ensure_ascii=False, indent=1),
    encoding="utf-8",
)

print(WL_OUTPUT)
print(NB_OUTPUT)
print(AUTORUN_OUTPUT)
print(PREFLIGHT_OUTPUT)
