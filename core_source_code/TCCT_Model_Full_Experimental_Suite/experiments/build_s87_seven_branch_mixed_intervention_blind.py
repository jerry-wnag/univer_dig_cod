import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
S86_SOURCE = ROOT / "TCCT_S86_ExternalSixBranchBlind.wl"
S86E_NOTEBOOK = ROOT / "TCCT_S86E_FreezeK33Candidate.ipynb"
WL_OUTPUT = ROOT / "TCCT_S87_SevenBranchMixedInterventionBlind.wl"
NB_OUTPUT = ROOT / "TCCT_S87_SevenBranchMixedInterventionBlind.ipynb"
AUTORUN_OUTPUT = ROOT / "TCCT_S87_SevenBranchMixedInterventionBlind_AutoRun.ipynb"
PREFLIGHT_OUTPUT = ROOT / "TCCT_S87_SevenBranchMixedInterventionBlind_Preflight_AutoRun.ipynb"
PREFLIGHT_WL_OUTPUT = ROOT / "TCCT_S87_SevenBranchMixedInterventionBlind_Preflight.wl"
MARKER = "(* S87 CELL *)"


def load_code_cells(path: Path) -> list[str]:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    return [
        "".join(cell.get("source", []))
        for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code"
    ]


s86_parts = S86_SOURCE.read_text(encoding="utf-8").split("(* S86 CELL *)")
if len(s86_parts) != 5:
    raise RuntimeError("S86 source no longer has four code cells")

s86e_cells = load_code_cells(S86E_NOTEBOOK)
if len(s86e_cells) != 3:
    raise RuntimeError("S86E notebook no longer has three code cells")

# Preserve the frozen architecture/core preflight exactly as used in S86E.
architecture_cell = s86e_cells[0].strip() + "\n"

preflight_cell = r'''
expectedK33CandidateHash87=
"2eb674929cfe1710231a4f508d13b20fe0f98d84d2c594c6261f46f370066ae4";
expectedBaseK19CandidateHash87=
"a51e6a13bdeda37b041eee4b74cfb6e472c7e52107a60f1d5534bb5df44ce44f";
expectedSelectionCertificateHash87=
"974c588337fbd9c3f51e9ea6847ba360dfc9dcf6fced751104f028987900ac5a";
expectedSelectionProtocolHash87=
"3faafbe4eef88369c32637b2b6b0825e288f6c40d7286db47e8739f083c3d309";
expectedSelectedResultHash87=
"cf6809b1fee65997fe95bdb28e6e3886e2a09f00ed9815ef0f6edff1117fe5ce";

k33CandidatePath87="E:/engine_wolf/TCCT_S86E_K33FrozenCandidate.wl";
oldK19CandidatePath87="E:/engine_wolf/TCCT_S83B_FrozenCandidate.wl";

If[
!FileExistsQ[k33CandidatePath87],
Print["S87 aborted: frozen K33 candidate file is missing."];Abort[]
];

k33CandidateFileHashBefore87=FileHash[k33CandidatePath87,"SHA256"];
oldK19CandidateFileHashBefore87=If[
FileExistsQ[oldK19CandidatePath87],
FileHash[oldK19CandidatePath87,"SHA256"],
Missing["OldK19CandidateFileMissing"]
];

Clear[frozenCandidate86E];
Get[k33CandidatePath87];

candidateHashLoaded87=If[
AssociationQ[frozenCandidate86E],
Hash[Normal[frozenCandidate86E],"SHA256","HexString"],
Missing["K33CandidateNotLoaded"]
];
baseK19CandidateHashBefore87=Hash[
Normal[frozenCandidate83B],"SHA256","HexString"
];

ClearAll[CoreDefinitionBundle87];
CoreDefinitionBundle87[]:=CoreDefinitionBundle86[];

preflightPassed87=And[
TrueQ[preflightPassed86],
AssociationQ[frozenCandidate86E],
SameQ[candidateHashLoaded87,expectedK33CandidateHash87],
SameQ[baseK19CandidateHashBefore87,expectedBaseK19CandidateHash87],
SameQ[frozenCandidate86E["Stage"],"S86E"],
SameQ[frozenCandidate86E["Name"],"K33CrossArityCandidate"],
SameQ[frozenCandidate86E["BaseCandidateHash"],expectedBaseK19CandidateHash87],
SameQ[frozenCandidate86E["SelectionCertificateHash"],
expectedSelectionCertificateHash87],
SameQ[frozenCandidate86E["SelectionProtocolHash"],
expectedSelectionProtocolHash87],
SameQ[frozenCandidate86E["SelectedResultHash"],expectedSelectedResultHash87],
SameQ[frozenCandidate86E["EncoderParams"],frozen75D["Params"]],
SameQ[frozenCandidate86E["Representation"],"KExactRole"],
SameQ[frozenCandidate86E["K"],33],
SameQ[frozenCandidate86E["PolicyLength"],39],
SameQ[Length[frozenCandidate86E["Policy"]],39],
SameQ[frozenCandidate86E["CombinedDevelopmentScore"],552],
TrueQ[frozenCandidate86E["ExactNodeRoleUsed"]],
SameQ[frozenCandidate86E["TokenDeduplication"],"DeleteDuplicates"],
TrueQ[frozenCandidate86E["FrozenBeforeS87"]],
FileExistsQ[oldK19CandidatePath87]
];

expectedCandidateHash87=expectedK33CandidateHash87;
expectedCanonicalizerHash87=expectedCanonicalizerHash86;
expectedInterventionHash87=expectedInterventionHash86;

preflight87=<|
"Stage"->"S87",
"Name"->"SevenBranchMixedInterventionBlind",
"CandidateFrozenBeforeTest"->True,
"CandidateHash"->candidateHashLoaded87,
"ExpectedCandidateHash"->expectedK33CandidateHash87,
"K"->If[AssociationQ[frozenCandidate86E],frozenCandidate86E["K"],Missing[]],
"PolicyLength"->If[
AssociationQ[frozenCandidate86E],Length[frozenCandidate86E["Policy"]],Missing[]
],
"BranchCount"->7,
"Depths"->{47,83},
"SelectionRun"->False,
"PolicyEditApplied"->False,
"RetuningApplied"->False,
"S87LabelsUsedForSelection"->False,
"OriginalFrozenModelChanged"->False,
"BaseK19CandidateChanged"->False,
"CoreChanged"->False,
"DeduplicationMechanismChanged"->False,
"PreflightPassed"->preflightPassed87
|>;

If[
!TrueQ[preflightPassed87],
Print[Dataset[{preflight87}]];
Print["S87 aborted: frozen K33 candidate or architecture mismatch."];
Abort[]
];

Dataset[{preflight87}]
'''.strip() + "\n"

# Reuse the audited S86 external-grammar harness definitions, not its runtime
# cases or scores. Rename all stage-local symbols before introducing the new
# seven-branch mixed intervention.
harness = "\n\n".join(part.strip() for part in s86_parts[2:])
harness = harness.replace("86", "87")
harness = harness.replace("frozenCandidate83B", "frozenCandidate86E")
harness = harness.replace(
    'frozenCandidate86E["FrozenBeforeS84"]',
    'frozenCandidate86E["FrozenBeforeS87"]',
)
harness = harness.replace(
    "ExternalSixBranchBlind", "SevenBranchMixedInterventionBlind"
)
harness = harness.replace("S83B-K19ExactRole", "S86E-K33ExactRole")
harness = harness.replace("SixBranch", "SevenBranch")
harness = harness.replace("six-branch", "seven-branch")
harness = harness.replace("AllTwelveWorldsCorrect", "AllFourteenWorldsCorrect")

# The external grammar has seven independent branches. The core constructors
# remain untouched; only the test-only grammar wrapper changes arity and seed.
old_case = r'''Case87[depth_Integer,answer_Integer,target_String]:=
T87[depth,target,answer,87000000+100 depth,6];'''
new_case = r'''Case87[depth_Integer,answer_Integer,target_String]:=
T87[depth,target,answer,87000000+100 depth,7];'''
if old_case not in harness:
    raise RuntimeError("S87 seven-branch Case wrapper pattern not found")
harness = harness.replace(old_case, new_case)
harness = harness.replace(
    "branchCount=6,seedCase", "branchCount=7,seedCase", 1
)

# One intervention cuts a redundant incoming path while another branch gets a
# semantic Continue-to-Stop rewrite. Cutting one of two parents must preserve
# the queried relation; the stop rewrite must change exactly one query.
harness = harness.replace(
    "DoubleBranchPatch87", "MixedPathCutStopPatch87"
)
clear_anchor = "BranchStopPatch87,\nMixedPathCutStopPatch87,"
if clear_anchor not in harness:
    raise RuntimeError("S87 ClearAll mixed-intervention insertion point missing")
harness = harness.replace(
    clear_anchor,
    "BranchStopPatch87,\nPathCutPatch87,\nMixedPathCutStopPatch87,",
    1,
)

old_patch_definition = r'''MixedPathCutStopPatch87[c_List,branches_List]:=Module[
{parts,remove,add},
parts=BranchStopPatch87[c,#]&/@branches;
remove=DeleteDuplicates@Flatten[Lookup[parts,"Remove"],1];
add=DeleteDuplicates@Flatten[Lookup[parts,"Add"],1];
<|
"Remove"->remove,
"Add"->add,
"Branches"->branches,
"ComponentPatchesValid"->And@@Lookup[parts,"ValidOnInput"],
"NoCrossBranchConflict"->Intersection[remove,add]==={},
"ExpectedEditCount"->And[Length[remove]===6,Length[add]===6]
|>
];'''
new_patch_definition = r'''PathCutPatch87[c_List,branch_Integer]:=Module[
{x,e,m,cutEdge,remainingEdge},
x=c[[1]];
e=x[[1]];
m=x[[6,branch]];
cutEdge=DirectedEdge[m+9,m];
remainingEdge=DirectedEdge[m+19,m];
<|
"Remove"->{cutEdge},
"Add"->{},
"ValidOnInput"->And[
MemberQ[e,cutEdge],MemberQ[e,remainingEdge]
]
|>
];

MixedPathCutStopPatch87[c_List,interventionPair_List]:=Module[
{cutPart,stopPart,remove,add},
cutPart=PathCutPatch87[c,First[interventionPair]];
stopPart=BranchStopPatch87[c,Last[interventionPair]];
remove=DeleteDuplicates@Join[cutPart["Remove"],stopPart["Remove"]];
add=DeleteDuplicates@Join[cutPart["Add"],stopPart["Add"]];
<|
"Remove"->remove,
"Add"->add,
"CutBranch"->First[interventionPair],
"StopBranch"->Last[interventionPair],
"ComponentPatchesValid"->And[
TrueQ[cutPart["ValidOnInput"]],TrueQ[stopPart["ValidOnInput"]]
],
"NoCrossBranchConflict"->Intersection[remove,add]==={},
"ExpectedEditCount"->And[Length[remove]===4,Length[add]===3]
|>
];'''
if old_patch_definition not in harness:
    raise RuntimeError("S87 mixed patch definition pattern not found")
harness = harness.replace(old_patch_definition, new_patch_definition)

bundle_anchor = (
    "DownValues[ExpectedContractions87],DownValues[BranchStopPatch87],\n"
    "DownValues[MixedPathCutStopPatch87],DownValues[PrepareWorld87],"
)
if bundle_anchor not in harness:
    raise RuntimeError("S87 test bundle insertion point missing")
harness = harness.replace(
    bundle_anchor,
    "DownValues[ExpectedContractions87],DownValues[BranchStopPatch87],\n"
    "DownValues[PathCutPatch87],DownValues[MixedPathCutStopPatch87],"
    "DownValues[PrepareWorld87],",
)

harness = harness.replace("patchedBranches", "interventionPair")
harness = harness.replace("PatchedBranches", "InterventionPair")
harness = harness.replace("PatchedQuery", "StopPatchedQuery")
harness = harness.replace("UnpatchedQuery", "NonStopQuery")
harness = harness.replace("PatchComponentValidity", "MixedInterventionValidity")
harness = harness.replace("PatchNoConflict", "MixedInterventionNoConflict")
harness = harness.replace("PatchEditCountCorrect", "MixedEditCountCorrect")
harness = harness.replace("PatchChangesGraph", "MixedInterventionChangesGraph")

# Only the semantic-stop branch changes target; the path-cut branch is an
# invariance intervention and remains Continue.
harness = harness.replace(
    'If[MemberQ[interventionPair,answer],"Stop","Continue"]',
    'If[SameQ[answer,Last[interventionPair]],"Stop","Continue"]',
)
harness = harness.replace(
    'MemberQ[interventionPair,base["Answer"]]',
    'SameQ[Last[interventionPair],base["Answer"]]',
)

harness = harness.replace(
    "blindDepths87={43,71};", "blindDepths87={47,83};"
)
old_intervention_pairs = (
    "blindPatchedBranchPairs87={{1,2},{2,3},{3,4},{4,5},{5,6},{1,6}};"
)
if harness.count(old_intervention_pairs) != 1:
    raise RuntimeError("S87 inherited intervention-pair grid mismatch")
harness = harness.replace(
    old_intervention_pairs,
    "blindInterventionPairs87={{1,3},{2,4},{3,5},{4,6},{5,7},{6,1},{7,2}};",
)
harness = harness.replace(
    "blindPatchedBranchPairs87", "blindInterventionPairs87"
)
harness = harness.replace("StopPatchedBranchPairs", "InterventionPairs")
harness = harness.replace('"PatchedBranchPairs"', '"InterventionPairs"')
harness = harness.replace('"DoubleIntervention"', '"MixedPathCutStopIntervention"')

protocol_replacements = {
    '"BranchCount"->6,': '"BranchCount"->7,',
    '"ExpectedScenarios"->24,': '"ExpectedScenarios"->28,',
    '"ExpectedWorldPairs"->144,': '"ExpectedWorldPairs"->196,',
    '"ExpectedWorlds"->288,': '"ExpectedWorlds"->392,',
    '"ExternalGrammar"->"IndependentSevenBranchT87",': (
        '"ExternalGrammar"->"IndependentSevenBranchT87",'
    ),
    '"Intervention"->"TwoSimultaneousBranchStopPatches",': (
        '"Intervention"->"OneRedundantPathCutPlusOneBranchStopPatch",'
    ),
    '"QueryGrid"->"AllSixQueriesBeforeAndAfterIntervention",': (
        '"QueryGrid"->"AllSevenQueriesBeforeAndAfterMixedIntervention",'
    ),
    '"ExpectedStopPatchedQueryPairs"->48,': (
        '"ExpectedStopPatchedQueryPairs"->28,'
    ),
    '"ExpectedNonStopQueryPairs"->96,': '"ExpectedNonStopQueryPairs"->168,',
}
for old, new in protocol_replacements.items():
    if old not in harness:
        raise RuntimeError(f"S87 protocol pattern missing: {old}")
    harness = harness.replace(old, new)

seven_branch_count_anchor = 'SameQ[w["BranchCount"],6]'
if harness.count(seven_branch_count_anchor) != 1:
    raise RuntimeError("S87 seven-branch world-count condition mismatch")
harness = harness.replace(
    seven_branch_count_anchor,
    'SameQ[w["BranchCount"],7]',
)

validity_replacements = {
    'SameQ[summary87["Scenarios"],24]': 'SameQ[summary87["Scenarios"],28]',
    'SameQ[summary87["WorldPairs"],144]': 'SameQ[summary87["WorldPairs"],196]',
    'SameQ[summary87["Worlds"],288]': 'SameQ[summary87["Worlds"],392]',
    'SameQ[summary87["StopPatchedQueryPairs"],48]': (
        'SameQ[summary87["StopPatchedQueryPairs"],28]'
    ),
    'SameQ[summary87["NonStopQueryPairs"],96]': (
        'SameQ[summary87["NonStopQueryPairs"],168]'
    ),
    'SameQ[summary87["MixedInterventionValidity"],24]': (
        'SameQ[summary87["MixedInterventionValidity"],28]'
    ),
    'SameQ[summary87["MixedInterventionNoConflict"],24]': (
        'SameQ[summary87["MixedInterventionNoConflict"],28]'
    ),
    'SameQ[summary87["MixedEditCountCorrect"],24]': (
        'SameQ[summary87["MixedEditCountCorrect"],28]'
    ),
    'SameQ[summary87["BaselineSameGraphAcrossQueries"],24]': (
        'SameQ[summary87["BaselineSameGraphAcrossQueries"],28]'
    ),
    'SameQ[summary87["InterventionSameGraphAcrossQueries"],24]': (
        'SameQ[summary87["InterventionSameGraphAcrossQueries"],28]'
    ),
    'SameQ[summary87["MixedInterventionChangesGraph"],24]': (
        'SameQ[summary87["MixedInterventionChangesGraph"],28]'
    ),
    'SameQ[summary87["ReferenceRelationsCorrect"],144]': (
        'SameQ[summary87["ReferenceRelationsCorrect"],196]'
    ),
    'SameQ[summary87["CanonicalCaseExactlyBase"],288]': (
        'SameQ[summary87["CanonicalCaseExactlyBase"],392]'
    ),
    'SameQ[summary87["ContractionCountCorrect"],288]': (
        'SameQ[summary87["ContractionCountCorrect"],392]'
    ),
    'SameQ[summary87["ProtectedNodesPreserved"],288]': (
        'SameQ[summary87["ProtectedNodesPreserved"],392]'
    ),
    'SameQ[summary87["ReferenceActionsCorrect"],288]': (
        'SameQ[summary87["ReferenceActionsCorrect"],392]'
    ),
    'SameQ[summary87["NonEmptyTokens"],288]': (
        'SameQ[summary87["NonEmptyTokens"],392]'
    ),
    'SameQ[summary87["TerminatedNaturally"],288]': (
        'SameQ[summary87["TerminatedNaturally"],392]'
    ),
    'SameQ[summary87["SevenBranchWorlds"],288]': (
        'SameQ[summary87["SevenBranchWorlds"],392]'
    ),
    'SameQ[summary87["BaselineCorrect"],144]': (
        'SameQ[summary87["BaselineCorrect"],196]'
    ),
    'SameQ[summary87["InterventionContinueCorrect"],96]': (
        'SameQ[summary87["InterventionContinueCorrect"],168]'
    ),
    'SameQ[summary87["InterventionStopCorrect"],48]': (
        'SameQ[summary87["InterventionStopCorrect"],28]'
    ),
    'SameQ[summary87["WorldCorrect"],288]': (
        'SameQ[summary87["WorldCorrect"],392]'
    ),
    'SameQ[summary87["PairCorrect"],144]': (
        'SameQ[summary87["PairCorrect"],196]'
    ),
    'SameQ[summary87["PredictionRelationsCorrect"],144]': (
        'SameQ[summary87["PredictionRelationsCorrect"],196]'
    ),
    'SameQ[summary87["ScenarioPerfect"],24]': (
        'SameQ[summary87["ScenarioPerfect"],28]'
    ),
}
for old, new in validity_replacements.items():
    if harness.count(old) != 1:
        raise RuntimeError(f"S87 validity pattern mismatch: {old}")
    harness = harness.replace(old, new)

harness = harness.replace(
    '"ExternalSevenBranchGrammarNovel"->True,',
    '"ExternalSevenBranchMixedInterventionNovel"->True,',
)
harness = harness.replace(
    '"AllSixQueryRolesTestedPerGraph"->True,',
    '"AllSevenQueryRolesTestedPerGraph"->True,',
)
harness = harness.replace(
    '"MayClaimBlindSevenBranchCounterfactualTransfer"',
    '"MayClaimBlindSevenBranchMixedInterventionTransfer"',
)
harness = harness.replace(
    '"BLIND_EXTERNAL_SIX_BRANCH_PASS"',
    '"S87_BLIND_SEVEN_BRANCH_MIXED_INTERVENTION_PASS"',
)
harness = harness.replace(
    '"VALID_BLIND_EXTERNAL_SIX_BRANCH_FAILURE"',
    '"S87_VALID_BLIND_FAILURE_DO_NOT_RETUNE"',
)
harness = harness.replace(
    '"S87_PATH_CUT_INTERVENTION_BLIND_TEST"',
    '"S88_COLLISION_SAFE_ENCODER_RESEARCH_BRANCH"',
)

# Add physical-file locks and explicit no-selection claims to the final audit.
after_hash_anchor = 'protocolHashAfter87=Hash[Normal[protocol87],"SHA256","HexString"];'
if after_hash_anchor not in harness:
    raise RuntimeError("S87 final hash insertion point missing")
harness = harness.replace(
    after_hash_anchor,
    after_hash_anchor
    + r'''
k33CandidateFileHashAfter87=FileHash[k33CandidatePath87,"SHA256"];
oldK19CandidateFileHashAfter87=FileHash[oldK19CandidatePath87,"SHA256"];
k33CandidateFileUnchanged87=SameQ[
k33CandidateFileHashBefore87,k33CandidateFileHashAfter87
];
oldK19CandidateFileUnchanged87=SameQ[
oldK19CandidateFileHashBefore87,oldK19CandidateFileHashAfter87
];''',
)

validity_anchor = (
    'TrueQ[protocolUnchanged87],\n'
    'TrueQ[deduplicationMechanismUnchanged87],'
)
if harness.count(validity_anchor) != 1:
    raise RuntimeError("S87 file-lock validity insertion point mismatch")
harness = harness.replace(
    validity_anchor,
    validity_anchor
    + "\nTrueQ[k33CandidateFileUnchanged87],"
    + "\nTrueQ[oldK19CandidateFileUnchanged87],",
)

payload_anchor = (
    '"DeduplicationMechanismChanged"->!TrueQ[deduplicationMechanismUnchanged87],'
)
if harness.count(payload_anchor) != 1:
    raise RuntimeError("S87 result payload insertion point mismatch")
harness = harness.replace(
    payload_anchor,
    payload_anchor
    + '\n"K33CandidateFileChanged"->!TrueQ[k33CandidateFileUnchanged87],'
    + '\n"OldK19CandidateFileChanged"->!TrueQ[oldK19CandidateFileUnchanged87],',
)

cert_start = harness.index("cert87=Join[")
cert_anchor = '"S87LabelsUsedForSelection"->False,'
cert_anchor_index = harness.index(cert_anchor, cert_start)
cert_insert_index = cert_anchor_index + len(cert_anchor)
harness = (
    harness[:cert_insert_index]
    + '\n"S84S85RegressionUsedForSelection"->False,'
    + harness[cert_insert_index:]
)

# Ensure the protocol is frozen before cases and forbid any prior runtime data.
if harness.index("protocolHash87=") > harness.index("blindScenarios87="):
    raise RuntimeError("S87 cases would be evaluated before protocol hashing")
for forbidden in (
    "selectedResult86D",
    "combinedTokenRows86B",
    "summary86F84",
    "summary86F85",
    "cert86F",
    "frozenCandidate86B",
    "S83B-K19ExactRole",
    "BLIND_EXTERNAL_SIX_BRANCH_PASS",
    "VALID_BLIND_EXTERNAL_SIX_BRANCH_FAILURE",
):
    if forbidden in harness:
        raise RuntimeError(f"development or revealed runtime leaked into S87: {forbidden}")

harness_parts = harness.split("(* S87 CELL *)")
if len(harness_parts) != 1:
    raise RuntimeError("unexpected inherited S87 marker")

# Original source parts are concatenated without markers above. Recover the
# three cells using stable boundaries that already existed in S86.
run_boundary = "blindScenarios87=Flatten["
audit_boundary = 'modelHashAfter87=Hash[Normal[frozen75D],"SHA256","HexString"];'
if harness.count(run_boundary) != 1 or harness.count(audit_boundary) != 1:
    raise RuntimeError("S87 cell boundaries are ambiguous")
definition_source, remainder = harness.split(run_boundary, 1)
run_prefix, audit_source = remainder.split(audit_boundary, 1)
definition_cell = definition_source.strip() + "\n"
run_cell = (run_boundary + run_prefix).strip() + "\n"
audit_cell = (audit_boundary + audit_source).strip() + "\n"

cells = [architecture_cell, preflight_cell, definition_cell, run_cell, audit_cell]
wl_source = "\n\n".join(f"{MARKER}\n{cell}" for cell in cells)
WL_OUTPUT.write_text(wl_source, encoding="utf-8")

markdown = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "# TCCT S87 - Seven-Branch Mixed-Intervention Blind Test\n",
        "\n",
        "The S86E K=33 candidate and its 39-token policy are frozen before this test. "
        "S87 introduces an unseen seven-branch grammar, depths 47 and 83, and a "
        "mixed intervention: one redundant parent path is cut while another branch "
        "is changed from Continue to Stop. Every branch is queried before and after "
        "the intervention.\n",
        "\n",
        "No K search, policy edit, retraining, retuning, S84/S85 regression score, "
        "or S87 label may influence the candidate. Run once and preserve failures.\n",
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
        for cell in [architecture_cell, preflight_cell, definition_cell]
    ],
]
PREFLIGHT_OUTPUT.write_text(
    json.dumps(preflight_notebook, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
PREFLIGHT_WL_OUTPUT.write_text(
    "\n\n".join(
        f"{MARKER}\n{cell}"
        for cell in [architecture_cell, preflight_cell, definition_cell]
    )
    + "\n\n"
    + 'Print[InputForm[<|"PreflightPassed"->preflightPassed87,'
    + '"ProtocolHash"->protocolHash87,'
    + '"TestDefinitionHash"->testDefinitionHashBefore87,'
    + '"K"->frozenCandidate86E["K"],'
    + '"PolicyLength"->frozenCandidate86E["PolicyLength"],'
    + '"CasesGeneratedBeforeProtocolHash"->False|>]];\n',
    encoding="utf-8",
)

for path in (
    WL_OUTPUT,
    NB_OUTPUT,
    AUTORUN_OUTPUT,
    PREFLIGHT_OUTPUT,
    PREFLIGHT_WL_OUTPUT,
):
    print(path)
