import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
NOTEBOOK = ROOT / "TCCT_S87A_SevenBranchFailureAudit.ipynb"
WL_OUTPUT = ROOT / "TCCT_S87B_StructuralPolicyDecoderResearch.wl"


def check_wl_delimiters(source: str) -> None:
    pairs = {")": "(", "]": "[", "}": "{"}
    stack: list[tuple[str, int]] = []
    in_string = False
    escaped = False
    comment_depth = 0
    index = 0
    while index < len(source):
        char = source[index]
        next_char = source[index + 1] if index + 1 < len(source) else ""
        if comment_depth:
            if char == "(" and next_char == "*":
                comment_depth += 1
                index += 2
                continue
            if char == "*" and next_char == ")":
                comment_depth -= 1
                index += 2
                continue
            index += 1
            continue
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == "(" and next_char == "*":
            comment_depth = 1
            index += 2
            continue
        if char == '"':
            in_string = True
        elif char in "([{":
            stack.append((char, index))
        elif char in ")]}":
            if not stack or stack[-1][0] != pairs[char]:
                raise RuntimeError(f"unbalanced Wolfram delimiter {char} at {index}")
            stack.pop()
        index += 1
    if in_string or comment_depth or stack:
        raise RuntimeError(
            f"unterminated Wolfram source: string={in_string}, "
            f"comment_depth={comment_depth}, stack_tail={stack[-3:]}"
        )


preflight_cell = r'''
ClearAll[
FeatureToken87B,
WorldFeatureTokens87B,
ContinueFeatures87B,
StopFeatures87B,
SafeFeaturePolicy87B,
ScoreFeaturePolicy87B,
SplitFold87B,
EvaluateFold87B,
EvaluateFamily87B,
S87BDefinitionBundle
];

s87AStateAvailable87B=And[
ValueQ[allWorlds87A],
ValueQ[cert87A],
ValueQ[auditValidityPassed87A],
ListQ[allWorlds87A],
SameQ[Length[allWorlds87A],392],
TrueQ[auditValidityPassed87A],
SameQ[cert87A["Diagnosis"],"FROZEN_POLICY_COVERAGE_GAP"]
];

If[
!TrueQ[s87AStateAvailable87B],
Print["S87B aborted: the valid S87A runtime state is not available."];
Print["Return to this notebook's S87A cells and run them once, then run only the S87B cells."];
Abort[]
];

modelHashBefore87B=Hash[Normal[frozen75D],"SHA256","HexString"];
candidateHashBefore87B=Hash[Normal[frozenCandidate86E],"SHA256","HexString"];
coreHashBefore87B=Hash[CoreDefinitionBundle87[],"SHA256","HexString"];
canonicalizerHashBefore87B=Hash[
{
DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],
DownValues[CanonicalCase79B]
},
"SHA256","HexString"
];
interventionHashBefore87B=Hash[
{
DownValues[LocalMediatorSources82],
DownValues[FullSemanticPatch82],
DownValues[LocalMediatorPatch82],
DownValues[ReferenceAction82]
},
"SHA256","HexString"
];
topologyHashBefore87B=Hash[
{DownValues[DoubleDiamondIn79],DownValues[HierarchicalDiamondIn80]},
"SHA256","HexString"
];
originalS87DefinitionHashBefore87B=Hash[
S87TestDefinitionBundle[],"SHA256","HexString"
];
k33CandidateFileHashBefore87B=FileHash[k33CandidatePath87,"SHA256"];

auditDataPayload87B=Map[
Function[world,
<|
"Topology"->world["Topology"],
"Depth"->world["Depth"],
"InterventionPair"->world["InterventionPair"],
"GraphCondition"->world["GraphCondition"],
"Answer"->world["Answer"],
"Target"->world["Target"],
"K33Tokens"->world["K33Tokens"]
|>
],
allWorlds87A
];
auditDataHashBefore87B=Hash[
Normal[auditDataPayload87B],"SHA256","HexString"
];

featureFamilies87B={
"ExactRoleCode",
"RoleOnly",
"RoleCode1",
"RoleCode2",
"RoleDeltaMod33",
"RoleSumMod33",
"RoleProductMod33",
"RoleEquality",
"RoleOrder",
"RoleParityPair",
"RoleMinMaxMod11"
};

foldSpecs87B=Join[
Map[<|"Axis"->"Topology","Heldout"->#|>&,DeleteDuplicates@Lookup[allWorlds87A,"Topology"]],
Map[<|"Axis"->"Depth","Heldout"->#|>&,DeleteDuplicates@Lookup[allWorlds87A,"Depth"]],
Map[<|"Axis"->"InterventionPair","Heldout"->#|>&,
DeleteDuplicates@Lookup[allWorlds87A,"InterventionPair"]]
];

protocol87B=<|
"Stage"->"S87B",
"Name"->"StructuralPolicyDecoderResearch",
"ResearchOnly"->True,
"S87AlreadyRevealed"->True,
"UsesS87Labels"->True,
"BlindTest"->False,
"InputAuditDataHash"->auditDataHashBefore87B,
"FrozenCandidateHash"->candidateHashBefore87B,
"K"->33,
"FeatureFamilies"->featureFamilies87B,
"FoldAxes"->{"Topology","Depth","InterventionPair"},
"FoldCount"->Length[foldSpecs87B],
"SelectionObjective"->"WorstClassAccuracyThenMeanBalancedAccuracyThenSimplicity",
"TrainingRun"->False,
"CoreEditApplied"->False,
"CandidateSearchRun"->False,
"FrozenPolicyEditApplied"->False,
"NewDecoderFrozen"->False,
"CandidateExported"->False,
"S88BlindTestRun"->False
|>;

protocolHash87B=Hash[Normal[protocol87B],"SHA256","HexString"];
Dataset[{Join[protocol87B,<|"ProtocolHash"->protocolHash87B|>]}]
'''.strip() + "\n"

research_cell = r'''
FeatureToken87B[token_List,family_String]:=Module[
{role,code,a,b},
role=token[[1]];
code=token[[2]];
a=code[[1]];
b=code[[2]];
Switch[
family,
"ExactRoleCode",token,
"RoleOnly",role,
"RoleCode1",{role,a},
"RoleCode2",{role,b},
"RoleDeltaMod33",{role,1+Mod[a-b,33]},
"RoleSumMod33",{role,1+Mod[a+b-2,33]},
"RoleProductMod33",{role,1+Mod[(a-1)(b-1),33]},
"RoleEquality",{role,SameQ[a,b]},
"RoleOrder",{role,Sign[a-b]},
"RoleParityPair",{role,Mod[a,2],Mod[b,2]},
"RoleMinMaxMod11",{role,Mod[Min[a,b],11],Mod[Max[a,b],11]},
_,$Failed
]
];

WorldFeatureTokens87B[world_Association,family_String]:=DeleteDuplicates[
FeatureToken87B[#,family]&/@world["K33Tokens"]
];

ContinueFeatures87B[worlds_List,family_String]:=Union@@Map[
WorldFeatureTokens87B[#,family]&,
Select[worlds,SameQ[#1["Target"],"Continue"]&]
];

StopFeatures87B[worlds_List,family_String]:=Union@@Map[
WorldFeatureTokens87B[#,family]&,
Select[worlds,SameQ[#1["Target"],"Stop"]&]
];

SafeFeaturePolicy87B[worlds_List,family_String]:=Complement[
ContinueFeatures87B[worlds,family],
StopFeatures87B[worlds,family]
];

ScoreFeaturePolicy87B[
worlds_List,family_String,policy_List
]:=Module[{predictionRows,continueRows,stopRows},
predictionRows=Map[
Function[world,
<|
"Target"->world["Target"],
"Prediction"->If[
AnyTrue[WorldFeatureTokens87B[world,family],MemberQ[policy,#]&],
"Continue","Stop"
]
|>
],
worlds
];
continueRows=Select[predictionRows,SameQ[#1["Target"],"Continue"]&];
stopRows=Select[predictionRows,SameQ[#1["Target"],"Stop"]&];
<|
"Score"->Count[predictionRows,row_/;SameQ[row["Prediction"],row["Target"]]],
"Cases"->Length[predictionRows],
"ContinueCorrect"->Count[
continueRows,row_/;SameQ[row["Prediction"],"Continue"]
],
"ContinueCases"->Length[continueRows],
"StopCorrect"->Count[stopRows,row_/;SameQ[row["Prediction"],"Stop"]],
"StopCases"->Length[stopRows]
|>
];

SplitFold87B[worlds_List,fold_Association]:=Module[{axis,value,test,train},
axis=fold["Axis"];
value=fold["Heldout"];
test=Select[worlds,SameQ[#1[axis],value]&];
train=Select[worlds,!SameQ[#1[axis],value]&];
<|"Train"->train,"Test"->test|>
];

EvaluateFold87B[
worlds_List,family_String,fold_Association
]:=Module[
{split,train,test,policy,score,exactTrainPolicy,novelContinue,novelCorrect},
split=SplitFold87B[worlds,fold];
train=split["Train"];
test=split["Test"];
policy=SafeFeaturePolicy87B[train,family];
score=ScoreFeaturePolicy87B[test,family,policy];
exactTrainPolicy=SafeFeaturePolicy87B[train,"ExactRoleCode"];
novelContinue=Select[
test,
SameQ[#1["Target"],"Continue"]&&
Intersection[#1["K33Tokens"],exactTrainPolicy]==={}&
];
novelCorrect=Count[
novelContinue,
world_/;AnyTrue[
WorldFeatureTokens87B[world,family],MemberQ[policy,#]&
]
];
Join[
<|
"Family"->family,
"Axis"->fold["Axis"],
"Heldout"->fold["Heldout"],
"TrainWorlds"->Length[train],
"TestWorlds"->Length[test],
"PolicyLength"->Length[policy]
|>,
score,
<|
"ContinueAccuracy"->N[score["ContinueCorrect"]/score["ContinueCases"]],
"StopAccuracy"->N[score["StopCorrect"]/score["StopCases"]],
"BalancedAccuracy"->N[Mean[{
score["ContinueCorrect"]/score["ContinueCases"],
score["StopCorrect"]/score["StopCases"]
}]],
"Perfect"->SameQ[score["Score"],score["Cases"]],
"NovelExactTokenContinueWorlds"->Length[novelContinue],
"NovelExactTokenContinueCorrect"->novelCorrect
|>
]
];

EvaluateFamily87B[worlds_List,family_String]:=Module[
{foldRows,fullPolicy,fullScore,perfectFolds,worstContinue,worstStop,meanBalanced},
foldRows=EvaluateFold87B[worlds,family,#]&/@foldSpecs87B;
fullPolicy=SafeFeaturePolicy87B[worlds,family];
fullScore=ScoreFeaturePolicy87B[worlds,family,fullPolicy];
perfectFolds=Count[foldRows,row_/;TrueQ[row["Perfect"]]];
worstContinue=Min[Lookup[foldRows,"ContinueAccuracy"]];
worstStop=Min[Lookup[foldRows,"StopAccuracy"]];
meanBalanced=Mean[Lookup[foldRows,"BalancedAccuracy"]];
<|
"Family"->family,
"Folds"->Length[foldRows],
"PerfectFolds"->perfectFolds,
"WorstContinueAccuracy"->worstContinue,
"WorstStopAccuracy"->worstStop,
"WorstClassAccuracy"->Min[worstContinue,worstStop],
"MeanBalancedAccuracy"->meanBalanced,
"FullScore"->fullScore["Score"],
"FullCases"->fullScore["Cases"],
"FullContinueCorrect"->fullScore["ContinueCorrect"],
"FullContinueCases"->fullScore["ContinueCases"],
"FullStopCorrect"->fullScore["StopCorrect"],
"FullStopCases"->fullScore["StopCases"],
"FullPolicyLength"->Length[fullPolicy],
"SharedFeatureCount"->Length@Intersection[
ContinueFeatures87B[worlds,family],StopFeatures87B[worlds,family]
],
"NovelExactTokenContinueWorlds"->Total@Lookup[
foldRows,"NovelExactTokenContinueWorlds"
],
"NovelExactTokenContinueCorrect"->Total@Lookup[
foldRows,"NovelExactTokenContinueCorrect"
],
"FoldRows"->foldRows,
"FullPolicy"->fullPolicy
|>
];

S87BDefinitionBundle[]:={
DownValues[FeatureToken87B],DownValues[WorldFeatureTokens87B],
DownValues[ContinueFeatures87B],DownValues[StopFeatures87B],
DownValues[SafeFeaturePolicy87B],DownValues[ScoreFeaturePolicy87B],
DownValues[SplitFold87B],DownValues[EvaluateFold87B],
DownValues[EvaluateFamily87B]
};

definitionHashBeforeEvaluation87B=Hash[
S87BDefinitionBundle[],"SHA256","HexString"
];

familyResults87B=EvaluateFamily87B[allWorlds87A,#]&/@featureFamilies87B;
structuralResults87B=Select[
familyResults87B,!SameQ[#1["Family"],"ExactRoleCode"]&
];
rankedStructuralResults87B=SortBy[
structuralResults87B,
{
-#1["PerfectFolds"],
-#1["WorstClassAccuracy"],
-#1["MeanBalancedAccuracy"],
-#1["FullScore"],
#1["FullPolicyLength"],
#1["Family"]
}&
];
bestStructuralResult87B=First[rankedStructuralResults87B];
bestStructuralFamily87B=bestStructuralResult87B["Family"];
bestStructuralFoldRows87B=bestStructuralResult87B["FoldRows"];

structuralCandidateFound87B=And[
SameQ[bestStructuralResult87B["PerfectFolds"],Length[foldSpecs87B]],
SameQ[bestStructuralResult87B["FullScore"],Length[allWorlds87A]],
SameQ[bestStructuralResult87B["WorstContinueAccuracy"],1.],
SameQ[bestStructuralResult87B["WorstStopAccuracy"],1.]
];

modelHashAfter87B=Hash[Normal[frozen75D],"SHA256","HexString"];
candidateHashAfter87B=Hash[Normal[frozenCandidate86E],"SHA256","HexString"];
coreHashAfter87B=Hash[CoreDefinitionBundle87[],"SHA256","HexString"];
canonicalizerHashAfter87B=Hash[
{
DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],
DownValues[CanonicalCase79B]
},
"SHA256","HexString"
];
interventionHashAfter87B=Hash[
{
DownValues[LocalMediatorSources82],
DownValues[FullSemanticPatch82],
DownValues[LocalMediatorPatch82],
DownValues[ReferenceAction82]
},
"SHA256","HexString"
];
topologyHashAfter87B=Hash[
{DownValues[DoubleDiamondIn79],DownValues[HierarchicalDiamondIn80]},
"SHA256","HexString"
];
originalS87DefinitionHashAfter87B=Hash[
S87TestDefinitionBundle[],"SHA256","HexString"
];
definitionHashAfterEvaluation87B=Hash[
S87BDefinitionBundle[],"SHA256","HexString"
];
protocolHashAfter87B=Hash[Normal[protocol87B],"SHA256","HexString"];
auditDataHashAfter87B=Hash[Normal[auditDataPayload87B],"SHA256","HexString"];
k33CandidateFileHashAfter87B=FileHash[k33CandidatePath87,"SHA256"];

coreUnchanged87B=SameQ[coreHashBefore87B,coreHashAfter87B];
deduplicationMechanismUnchanged87B=And[
TrueQ[coreUnchanged87B],
SameQ[
protocol87["TokenDeduplication"],
"DeleteDuplicatesAfterExactRoleCodePairing"
]
];

researchValidityPassed87B=And[
SameQ[Length[foldSpecs87B],11],
SameQ[Length[familyResults87B],Length[featureFamilies87B]],
SameQ[modelHashBefore87B,modelHashAfter87B],
SameQ[candidateHashBefore87B,candidateHashAfter87B],
TrueQ[coreUnchanged87B],
SameQ[canonicalizerHashBefore87B,canonicalizerHashAfter87B],
SameQ[interventionHashBefore87B,interventionHashAfter87B],
SameQ[topologyHashBefore87B,topologyHashAfter87B],
SameQ[
originalS87DefinitionHashBefore87B,originalS87DefinitionHashAfter87B
],
SameQ[definitionHashBeforeEvaluation87B,definitionHashAfterEvaluation87B],
SameQ[protocolHash87B,protocolHashAfter87B],
SameQ[auditDataHashBefore87B,auditDataHashAfter87B],
SameQ[k33CandidateFileHashBefore87B,k33CandidateFileHashAfter87B],
TrueQ[deduplicationMechanismUnchanged87B]
];

cert87B=<|
"Stage"->"S87B",
"Name"->"StructuralPolicyDecoderResearch",
"ResearchValidityPassed"->researchValidityPassed87B,
"ResearchOnly"->True,
"BlindTest"->False,
"Worlds"->Length[allWorlds87A],
"FeatureFamiliesTested"->Length[featureFamilies87B],
"GroupedHoldoutFolds"->Length[foldSpecs87B],
"BestStructuralFamily"->bestStructuralFamily87B,
"BestPerfectFolds"->bestStructuralResult87B["PerfectFolds"],
"BestWorstContinueAccuracy"->bestStructuralResult87B["WorstContinueAccuracy"],
"BestWorstStopAccuracy"->bestStructuralResult87B["WorstStopAccuracy"],
"BestMeanBalancedAccuracy"->bestStructuralResult87B["MeanBalancedAccuracy"],
"BestFullScore"->bestStructuralResult87B["FullScore"],
"BestFullCases"->bestStructuralResult87B["FullCases"],
"BestFullPolicyLength"->bestStructuralResult87B["FullPolicyLength"],
"BestSharedFeatureCount"->bestStructuralResult87B["SharedFeatureCount"],
"NovelExactTokenContinueWorlds"->
bestStructuralResult87B["NovelExactTokenContinueWorlds"],
"NovelExactTokenContinueCorrect"->
bestStructuralResult87B["NovelExactTokenContinueCorrect"],
"StructuralDecoderCandidateFound"->structuralCandidateFound87B,
"OriginalFrozenModelChanged"->!SameQ[modelHashBefore87B,modelHashAfter87B],
"FrozenCandidateChanged"->!SameQ[candidateHashBefore87B,candidateHashAfter87B],
"CoreChanged"->!TrueQ[coreUnchanged87B],
"CanonicalizerChanged"->!SameQ[
canonicalizerHashBefore87B,canonicalizerHashAfter87B
],
"InterventionChanged"->!SameQ[
interventionHashBefore87B,interventionHashAfter87B
],
"TopologyImplementationsChanged"->!SameQ[
topologyHashBefore87B,topologyHashAfter87B
],
"DeduplicationMechanismChanged"->!TrueQ[
deduplicationMechanismUnchanged87B
],
"CandidateFileChanged"->!SameQ[
k33CandidateFileHashBefore87B,k33CandidateFileHashAfter87B
],
"UsesRevealedS87Labels"->True,
"S87LabelsAppliedToFrozenModel"->False,
"TrainingRun"->False,
"CandidateSearchRun"->False,
"FrozenPolicyEditApplied"->False,
"NewDecoderFrozen"->False,
"CandidateExported"->False,
"MayClaimNewBlindGeneralization"->False,
"Outcome"->Which[
!TrueQ[researchValidityPassed87B],
"S87B_INVALID_RESEARCH_AUDIT",
TrueQ[structuralCandidateFound87B],
"S87B_STRUCTURAL_DECODER_CANDIDATE_FOUND_NOT_FROZEN",
True,
"S87B_NO_PERFECT_STRUCTURAL_DECODER_CANDIDATE"
],
"SuggestedNextStage"->If[
TrueQ[structuralCandidateFound87B],
"S87C_FREEZE_DECODER_THEN_DESIGN_S88_BLIND",
"S87C_EXPAND_TRANSPARENT_DECODER_FAMILY_WITHOUT_BLIND_DATA"
]
|>;

Column[{
Dataset[Map[KeyDrop[#,{"FoldRows","FullPolicy"}]&,familyResults87B]],
Dataset[bestStructuralFoldRows87B],
Dataset[{cert87B}]
}]
'''.strip() + "\n"

for cell_number, source in enumerate((preflight_cell, research_cell), start=1):
    try:
        check_wl_delimiters(source)
    except RuntimeError as exc:
        raise RuntimeError(f"S87B code cell {cell_number}: {exc}") from exc

combined_source = preflight_cell + "\n" + research_cell
for forbidden in (
    'AssociateTo[frozenCandidate86E',
    'frozenCandidate86E["K"]=',
    'frozenCandidate86E["Policy"]=',
    'Export[k33CandidatePath87',
):
    if forbidden in combined_source:
        raise RuntimeError(f"forbidden frozen-candidate mutation found: {forbidden}")


def make_code_cell(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {"tcct_stage": "S87B"},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
notebook["cells"] = [
    cell
    for cell in notebook.get("cells", [])
    if cell.get("metadata", {}).get("tcct_stage") != "S87B"
]
notebook["cells"].extend(
    [
        {
            "cell_type": "markdown",
            "metadata": {"tcct_stage": "S87B"},
            "source": [
                "## S87B - Structural policy decoder research\n",
                "\n",
                "Run only the next two cells in the current S87A kernel. Do not "
                "restart the kernel. This revealed-data research compares exact "
                "token lookup with transparent lower-dimensional feature decoders "
                "under 11 grouped holdout folds. It does not edit or freeze the model.\n",
            ],
        },
        make_code_cell(preflight_cell),
        make_code_cell(research_cell),
    ]
)

NOTEBOOK.write_text(
    json.dumps(notebook, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
WL_OUTPUT.write_text(
    "(* S87B PREFLIGHT CELL *)\n"
    + preflight_cell
    + "\n(* S87B RESEARCH CELL *)\n"
    + research_cell,
    encoding="utf-8",
)

print(NOTEBOOK)
print(WL_OUTPUT)
