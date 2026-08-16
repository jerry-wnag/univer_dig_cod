import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
NOTEBOOK = ROOT / "TCCT_S87A_SevenBranchFailureAudit.ipynb"
WL_OUTPUT = ROOT / "TCCT_S87C_WorldMultisetDecoderResearch.wl"


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
CodeStats87C,
CodeHistogram87C,
PairwiseStats87C,
SelectRoleObservations87C,
WorldVector87C,
BuildFeatureRows87C,
SplitFeatureRows87C,
BalancedTrainingRules87C,
ScorePredictions87C,
EvaluateDecoderFold87C,
EvaluateDecoderFamily87C,
S87CDefinitionBundle
];

s87BStateAvailable87C=And[
ValueQ[allWorlds87A],
ValueQ[cert87A],
ValueQ[cert87B],
ListQ[allWorlds87A],
SameQ[Length[allWorlds87A],392],
TrueQ[cert87A["AuditValidityPassed"]],
TrueQ[cert87B["ResearchValidityPassed"]],
SameQ[cert87B["Outcome"],"S87B_NO_PERFECT_STRUCTURAL_DECODER_CANDIDATE"]
];

If[
!TrueQ[s87BStateAvailable87C],
Print["S87C aborted: the valid S87A/S87B runtime state is not available."];
Print["Run the existing S87A and S87B cells once, then run only S87C."];
Abort[]
];

modelHashBefore87C=Hash[Normal[frozen75D],"SHA256","HexString"];
candidateHashBefore87C=Hash[Normal[frozenCandidate86E],"SHA256","HexString"];
coreHashBefore87C=Hash[CoreDefinitionBundle87[],"SHA256","HexString"];
canonicalizerHashBefore87C=Hash[
{
DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],
DownValues[CanonicalCase79B]
},
"SHA256","HexString"
];
interventionHashBefore87C=Hash[
{
DownValues[LocalMediatorSources82],
DownValues[FullSemanticPatch82],
DownValues[LocalMediatorPatch82],
DownValues[ReferenceAction82]
},
"SHA256","HexString"
];
topologyHashBefore87C=Hash[
{DownValues[DoubleDiamondIn79],DownValues[HierarchicalDiamondIn80]},
"SHA256","HexString"
];
originalS87DefinitionHashBefore87C=Hash[
S87TestDefinitionBundle[],"SHA256","HexString"
];
k33CandidateFileHashBefore87C=FileHash[k33CandidatePath87,"SHA256"];

inputDataHashBefore87C=Hash[Normal[auditDataPayload87B],"SHA256","HexString"];

allRoles87C={
"QueriedDecision",
"QueriedMediatorSource",
"QueriedCorrectDestination",
"QueriedWrongDestination",
"QueriedDummyDestination",
"OtherDecision",
"OtherAnswerDestination",
"OtherReject"
};
queriedRoles87C=Take[allRoles87C,5];

featureFamilies87C={
"QueriedGlobalMoments",
"QueriedRoleMoments",
"AllRoleMoments",
"QueriedRoleHistograms",
"QueriedRoleMomentsHistograms",
"AllRoleMomentsQueriedHistograms",
"QueriedRoleMomentsPairwise"
};

protocol87C=<|
"Stage"->"S87C",
"Name"->"WorldMultisetDecoderResearch",
"ResearchOnly"->True,
"S87AlreadyRevealed"->True,
"UsesS87Labels"->True,
"BlindTest"->False,
"InputDataHash"->inputDataHashBefore87C,
"FrozenCandidateHash"->candidateHashBefore87C,
"K"->33,
"ObservationInputs"->{"Role","QueryBranchRelated","Code"},
"ForbiddenFeatureInputs"->{
"Topology","Depth","InterventionPair","Answer","GraphCondition","Target"
},
"ForbiddenInputsUsedForFoldSplittingOnly"->True,
"FeatureFamilies"->featureFamilies87C,
"Classifier"->"BalancedDeterministicDecisionTree",
"FoldAxes"->{"Topology","Depth","InterventionPair"},
"FoldCount"->Length[foldSpecs87B],
"CandidateCriterion"->"PerfectBothClassesOnAllElevenGroupedHoldouts",
"DecoderResearchTrainingRun"->True,
"FrozenModelTrainingRun"->False,
"DecoderFamilySearchRun"->True,
"FrozenCandidateSearchRun"->False,
"CoreEditApplied"->False,
"FrozenPolicyEditApplied"->False,
"NewDecoderFrozen"->False,
"CandidateExported"->False,
"S88BlindTestRun"->False
|>;

protocolHash87C=Hash[Normal[protocol87C],"SHA256","HexString"];
Dataset[{Join[protocol87C,<|"ProtocolHash"->protocolHash87C|>]}]
'''.strip() + "\n"

research_cell = r'''
CodeStats87C[observations_List]:=Module[
{codes,a,b,delta,sum,product},
codes=Lookup[observations,"Code",{}];
If[Length[codes]===0,Return[ConstantArray[0,17]]];
a=codes[[All,1]];
b=codes[[All,2]];
delta=Mod[a-b,33];
sum=Mod[a+b-2,33];
product=Mod[(a-1)(b-1),33];
{
Length[codes],
Length[DeleteDuplicates[codes]],
Total[a],Total[b],
Total[a^2],Total[b^2],
Min[a],Max[a],Min[b],Max[b],
Total[delta],Total[sum],Total[product],
Count[MapThread[SameQ,{a,b}],True],
Count[MapThread[Less,{a,b}],True],
Count[MapThread[Greater,{a,b}],True],
Total[Abs[a-b]]
}
];

CodeHistogram87C[observations_List]:=Module[{codes,a,b},
codes=Lookup[observations,"Code",{}];
If[Length[codes]===0,Return[ConstantArray[0,66]]];
a=codes[[All,1]];
b=codes[[All,2]];
Join[Count[a,#]&/@Range[33],Count[b,#]&/@Range[33]]
];

PairwiseStats87C[observations_List]:=Module[
{codes,pairs,firstDistance,secondDistance,crossDistance},
codes=Lookup[observations,"Code",{}];
pairs=Subsets[codes,{2}];
If[Length[pairs]===0,Return[ConstantArray[0,10]]];
firstDistance=Abs[pairs[[All,1,1]]-pairs[[All,2,1]]];
secondDistance=Abs[pairs[[All,1,2]]-pairs[[All,2,2]]];
crossDistance=Abs[
(pairs[[All,1,1]]-pairs[[All,1,2]])-
(pairs[[All,2,1]]-pairs[[All,2,2]])
];
{
Length[pairs],
Total[firstDistance],Total[secondDistance],Total[crossDistance],
Min[firstDistance],Max[firstDistance],
Min[secondDistance],Max[secondDistance],
Count[firstDistance,0],Count[secondDistance,0]
}
];

SelectRoleObservations87C[
world_Association,role_String,queryRelatedOnly_
]:=Select[
world["Observations"],
And[
SameQ[#1["Role"],role],
If[TrueQ[queryRelatedOnly],TrueQ[#1["QueryBranchRelated"]],True]
]&
];

WorldVector87C[world_Association,family_String]:=Module[
{queriedObservations,queriedRoleObservations,allRoleObservations},
queriedObservations=Select[
world["Observations"],TrueQ[#1["QueryBranchRelated"]]&
];
queriedRoleObservations=Map[
SelectRoleObservations87C[world,#,True]&,
queriedRoles87C
];
allRoleObservations=Map[
SelectRoleObservations87C[world,#,False]&,
allRoles87C
];
Switch[
family,
"QueriedGlobalMoments",
Join[CodeStats87C[queriedObservations],PairwiseStats87C[queriedObservations]],
"QueriedRoleMoments",
Flatten[CodeStats87C/@queriedRoleObservations],
"AllRoleMoments",
Flatten[CodeStats87C/@allRoleObservations],
"QueriedRoleHistograms",
Flatten[CodeHistogram87C/@queriedRoleObservations],
"QueriedRoleMomentsHistograms",
Flatten@Join[
CodeStats87C/@queriedRoleObservations,
CodeHistogram87C/@queriedRoleObservations
],
"AllRoleMomentsQueriedHistograms",
Flatten@Join[
CodeStats87C/@allRoleObservations,
CodeHistogram87C/@queriedRoleObservations
],
"QueriedRoleMomentsPairwise",
Join[
Flatten[CodeStats87C/@queriedRoleObservations],
PairwiseStats87C[queriedObservations]
],
_,$Failed
]
];

BuildFeatureRows87C[worlds_List,family_String]:=Map[
Function[world,
<|
"Topology"->world["Topology"],
"Depth"->world["Depth"],
"InterventionPair"->world["InterventionPair"],
"Target"->world["Target"],
"Vector"->WorldVector87C[world,family]
|>
],
worlds
];

SplitFeatureRows87C[rows_List,fold_Association]:=Module[
{axis,value,test,train},
axis=fold["Axis"];
value=fold["Heldout"];
test=Select[rows,SameQ[#1[axis],value]&];
train=Select[rows,!SameQ[#1[axis],value]&];
<|"Train"->train,"Test"->test|>
];

BalancedTrainingRules87C[rows_List]:=Module[
{continueRows,stopRows,repeatCount,balancedStopRows},
continueRows=Select[rows,SameQ[#1["Target"],"Continue"]&];
stopRows=Select[rows,SameQ[#1["Target"],"Stop"]&];
If[
Length[continueRows]===0||Length[stopRows]===0,
Return[$Failed]
];
repeatCount=Ceiling[Length[continueRows]/Length[stopRows]];
balancedStopRows=Take[
Flatten[ConstantArray[stopRows,repeatCount],1],
Length[continueRows]
];
(#1["Vector"]->#1["Target"])&/@Join[continueRows,balancedStopRows]
];

ScorePredictions87C[rows_List,predictions_List]:=Module[
{targets,continuePositions,stopPositions,continueCorrect,stopCorrect},
targets=Lookup[rows,"Target"];
continuePositions=Flatten@Position[targets,"Continue"];
stopPositions=Flatten@Position[targets,"Stop"];
continueCorrect=Count[predictions[[continuePositions]],"Continue"];
stopCorrect=Count[predictions[[stopPositions]],"Stop"];
<|
"Score"->Count[MapThread[SameQ,{predictions,targets}],True],
"Cases"->Length[rows],
"ContinueCorrect"->continueCorrect,
"ContinueCases"->Length[continuePositions],
"StopCorrect"->stopCorrect,
"StopCases"->Length[stopPositions],
"ContinueAccuracy"->N[continueCorrect/Length[continuePositions]],
"StopAccuracy"->N[stopCorrect/Length[stopPositions]],
"BalancedAccuracy"->N@Mean[{
continueCorrect/Length[continuePositions],
stopCorrect/Length[stopPositions]
}]
|>
];

EvaluateDecoderFold87C[
rows_List,family_String,fold_Association
]:=Module[
{split,train,test,trainingRules,classifier,predictions,score},
split=SplitFeatureRows87C[rows,fold];
train=split["Train"];
test=split["Test"];
trainingRules=BalancedTrainingRules87C[train];
SeedRandom[870300+Length[train]+Length[test],Method->"MersenneTwister"];
classifier=Quiet@Check[
Classify[trainingRules,Method->"DecisionTree"],
$Failed
];
If[
SameQ[classifier,$Failed]||Head[classifier]=!=ClassifierFunction,
Return[<|
"Family"->family,"Axis"->fold["Axis"],"Heldout"->fold["Heldout"],
"TrainWorlds"->Length[train],"TestWorlds"->Length[test],
"ClassifierValid"->False,"Score"->0,"Cases"->Length[test],
"ContinueCorrect"->0,
"ContinueCases"->Count[test,row_/;SameQ[row["Target"],"Continue"]],
"StopCorrect"->0,
"StopCases"->Count[test,row_/;SameQ[row["Target"],"Stop"]],
"ContinueAccuracy"->0.,"StopAccuracy"->0.,"BalancedAccuracy"->0.,
"Perfect"->False
|>]
];
predictions=Quiet@Check[classifier/@Lookup[test,"Vector"],$Failed];
If[SameQ[predictions,$Failed],predictions=ConstantArray["Invalid",Length[test]]];
score=ScorePredictions87C[test,predictions];
Join[
<|
"Family"->family,
"Axis"->fold["Axis"],
"Heldout"->fold["Heldout"],
"TrainWorlds"->Length[train],
"TestWorlds"->Length[test],
"FeatureDimension"->Length[First[Lookup[train,"Vector"]]],
"ClassifierValid"->True
|>,
score,
<|"Perfect"->SameQ[score["Score"],score["Cases"]]|>
]
];

EvaluateDecoderFamily87C[worlds_List,family_String]:=Module[
{rows,foldRows,fullRules,fullClassifier,fullPredictions,fullScore,validFolds},
rows=BuildFeatureRows87C[worlds,family];
foldRows=EvaluateDecoderFold87C[rows,family,#]&/@foldSpecs87B;
fullRules=BalancedTrainingRules87C[rows];
SeedRandom[870399,Method->"MersenneTwister"];
fullClassifier=Quiet@Check[
Classify[fullRules,Method->"DecisionTree"],
$Failed
];
If[
SameQ[fullClassifier,$Failed]||Head[fullClassifier]=!=ClassifierFunction,
fullPredictions=ConstantArray["Invalid",Length[rows]],
fullPredictions=Quiet@Check[
fullClassifier/@Lookup[rows,"Vector"],
ConstantArray["Invalid",Length[rows]]
]
];
fullScore=ScorePredictions87C[rows,fullPredictions];
validFolds=Count[foldRows,row_/;TrueQ[row["ClassifierValid"]]];
<|
"Family"->family,
"FeatureDimension"->Length[First[Lookup[rows,"Vector"]]],
"Folds"->Length[foldRows],
"ValidFolds"->validFolds,
"PerfectFolds"->Count[foldRows,row_/;TrueQ[row["Perfect"]]],
"WorstContinueAccuracy"->Min[Lookup[foldRows,"ContinueAccuracy"]],
"WorstStopAccuracy"->Min[Lookup[foldRows,"StopAccuracy"]],
"WorstClassAccuracy"->Min@Join[
Lookup[foldRows,"ContinueAccuracy"],Lookup[foldRows,"StopAccuracy"]
],
"MeanBalancedAccuracy"->Mean[Lookup[foldRows,"BalancedAccuracy"]],
"FullScore"->fullScore["Score"],
"FullCases"->fullScore["Cases"],
"FullContinueCorrect"->fullScore["ContinueCorrect"],
"FullContinueCases"->fullScore["ContinueCases"],
"FullStopCorrect"->fullScore["StopCorrect"],
"FullStopCases"->fullScore["StopCases"],
"FoldRows"->foldRows,
"FullClassifier"->fullClassifier
|>
];

S87CDefinitionBundle[]:={
DownValues[CodeStats87C],DownValues[CodeHistogram87C],
DownValues[PairwiseStats87C],DownValues[SelectRoleObservations87C],
DownValues[WorldVector87C],DownValues[BuildFeatureRows87C],
DownValues[SplitFeatureRows87C],DownValues[BalancedTrainingRules87C],
DownValues[ScorePredictions87C],DownValues[EvaluateDecoderFold87C],
DownValues[EvaluateDecoderFamily87C]
};

definitionHashBeforeEvaluation87C=Hash[
S87CDefinitionBundle[],"SHA256","HexString"
];

familyResults87C=EvaluateDecoderFamily87C[
allWorlds87A,#
]&/@featureFamilies87C;

rankedResults87C=SortBy[
familyResults87C,
{
-#1["PerfectFolds"],
-#1["WorstClassAccuracy"],
-#1["MeanBalancedAccuracy"],
-#1["FullScore"],
#1["FeatureDimension"],
#1["Family"]
}&
];
bestResult87C=First[rankedResults87C];
bestFamily87C=bestResult87C["Family"];
bestFoldRows87C=bestResult87C["FoldRows"];

worldMultisetDecoderCandidateFound87C=And[
SameQ[bestResult87C["ValidFolds"],Length[foldSpecs87B]],
SameQ[bestResult87C["PerfectFolds"],Length[foldSpecs87B]],
SameQ[bestResult87C["WorstContinueAccuracy"],1.],
SameQ[bestResult87C["WorstStopAccuracy"],1.],
SameQ[bestResult87C["FullScore"],Length[allWorlds87A]]
];

modelHashAfter87C=Hash[Normal[frozen75D],"SHA256","HexString"];
candidateHashAfter87C=Hash[Normal[frozenCandidate86E],"SHA256","HexString"];
coreHashAfter87C=Hash[CoreDefinitionBundle87[],"SHA256","HexString"];
canonicalizerHashAfter87C=Hash[
{
DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],
DownValues[CanonicalCase79B]
},
"SHA256","HexString"
];
interventionHashAfter87C=Hash[
{
DownValues[LocalMediatorSources82],
DownValues[FullSemanticPatch82],
DownValues[LocalMediatorPatch82],
DownValues[ReferenceAction82]
},
"SHA256","HexString"
];
topologyHashAfter87C=Hash[
{DownValues[DoubleDiamondIn79],DownValues[HierarchicalDiamondIn80]},
"SHA256","HexString"
];
originalS87DefinitionHashAfter87C=Hash[
S87TestDefinitionBundle[],"SHA256","HexString"
];
definitionHashAfterEvaluation87C=Hash[
S87CDefinitionBundle[],"SHA256","HexString"
];
protocolHashAfter87C=Hash[Normal[protocol87C],"SHA256","HexString"];
inputDataHashAfter87C=Hash[Normal[auditDataPayload87B],"SHA256","HexString"];
k33CandidateFileHashAfter87C=FileHash[k33CandidatePath87,"SHA256"];

coreUnchanged87C=SameQ[coreHashBefore87C,coreHashAfter87C];
deduplicationMechanismUnchanged87C=And[
TrueQ[coreUnchanged87C],
SameQ[
protocol87["TokenDeduplication"],
"DeleteDuplicatesAfterExactRoleCodePairing"
]
];

researchValidityPassed87C=And[
SameQ[Length[foldSpecs87B],11],
SameQ[Length[familyResults87C],Length[featureFamilies87C]],
And@@Map[
SameQ[#1["ValidFolds"],Length[foldSpecs87B]]&,
familyResults87C
],
SameQ[modelHashBefore87C,modelHashAfter87C],
SameQ[candidateHashBefore87C,candidateHashAfter87C],
TrueQ[coreUnchanged87C],
SameQ[canonicalizerHashBefore87C,canonicalizerHashAfter87C],
SameQ[interventionHashBefore87C,interventionHashAfter87C],
SameQ[topologyHashBefore87C,topologyHashAfter87C],
SameQ[
originalS87DefinitionHashBefore87C,originalS87DefinitionHashAfter87C
],
SameQ[definitionHashBeforeEvaluation87C,definitionHashAfterEvaluation87C],
SameQ[protocolHash87C,protocolHashAfter87C],
SameQ[inputDataHashBefore87C,inputDataHashAfter87C],
SameQ[k33CandidateFileHashBefore87C,k33CandidateFileHashAfter87C],
TrueQ[deduplicationMechanismUnchanged87C]
];

cert87C=<|
"Stage"->"S87C",
"Name"->"WorldMultisetDecoderResearch",
"ResearchValidityPassed"->researchValidityPassed87C,
"ResearchOnly"->True,
"BlindTest"->False,
"Worlds"->Length[allWorlds87A],
"FeatureFamiliesTested"->Length[featureFamilies87C],
"GroupedHoldoutFolds"->Length[foldSpecs87B],
"BestFeatureFamily"->bestFamily87C,
"BestFeatureDimension"->bestResult87C["FeatureDimension"],
"BestPerfectFolds"->bestResult87C["PerfectFolds"],
"BestWorstContinueAccuracy"->bestResult87C["WorstContinueAccuracy"],
"BestWorstStopAccuracy"->bestResult87C["WorstStopAccuracy"],
"BestMeanBalancedAccuracy"->bestResult87C["MeanBalancedAccuracy"],
"BestFullScore"->bestResult87C["FullScore"],
"BestFullCases"->bestResult87C["FullCases"],
"WorldMultisetDecoderCandidateFound"->worldMultisetDecoderCandidateFound87C,
"ForbiddenFeatureInputsUsed"->False,
"OriginalFrozenModelChanged"->!SameQ[modelHashBefore87C,modelHashAfter87C],
"FrozenCandidateChanged"->!SameQ[candidateHashBefore87C,candidateHashAfter87C],
"CoreChanged"->!TrueQ[coreUnchanged87C],
"CanonicalizerChanged"->!SameQ[
canonicalizerHashBefore87C,canonicalizerHashAfter87C
],
"InterventionChanged"->!SameQ[
interventionHashBefore87C,interventionHashAfter87C
],
"TopologyImplementationsChanged"->!SameQ[
topologyHashBefore87C,topologyHashAfter87C
],
"DeduplicationMechanismChanged"->!TrueQ[
deduplicationMechanismUnchanged87C
],
"CandidateFileChanged"->!SameQ[
k33CandidateFileHashBefore87C,k33CandidateFileHashAfter87C
],
"UsesRevealedS87Labels"->True,
"S87LabelsAppliedToFrozenModel"->False,
"DecoderResearchTrainingRun"->True,
"FrozenModelTrainingRun"->False,
"DecoderFamilySearchRun"->True,
"FrozenCandidateSearchRun"->False,
"FrozenPolicyEditApplied"->False,
"NewDecoderFrozen"->False,
"CandidateExported"->False,
"MayClaimNewBlindGeneralization"->False,
"Outcome"->Which[
!TrueQ[researchValidityPassed87C],
"S87C_INVALID_RESEARCH_AUDIT",
TrueQ[worldMultisetDecoderCandidateFound87C],
"S87C_WORLD_MULTISET_DECODER_CANDIDATE_FOUND_NOT_FROZEN",
True,
"S87C_NO_PERFECT_WORLD_MULTISET_DECODER_CANDIDATE"
],
"SuggestedNextStage"->If[
TrueQ[worldMultisetDecoderCandidateFound87C],
"S87D_FREEZE_DECODER_THEN_DESIGN_S88_BLIND",
"S87D_AUDIT_QUERY_LOCAL_SEMANTIC_SUFFICIENCY"
]
|>;

Column[{
Dataset[Map[KeyDrop[#,{"FoldRows","FullClassifier"}]&,familyResults87C]],
Dataset[bestFoldRows87C],
Dataset[{cert87C}]
}]
'''.strip() + "\n"


for cell_number, source in enumerate((preflight_cell, research_cell), start=1):
    try:
        check_wl_delimiters(source)
    except RuntimeError as exc:
        raise RuntimeError(f"S87C code cell {cell_number}: {exc}") from exc

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
        "metadata": {"tcct_stage": "S87C"},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
notebook["cells"] = [
    cell
    for cell in notebook.get("cells", [])
    if cell.get("metadata", {}).get("tcct_stage") != "S87C"
]
notebook["cells"].extend(
    [
        {
            "cell_type": "markdown",
            "metadata": {"tcct_stage": "S87C"},
            "source": [
                "## S87C - World multiset decoder research\n",
                "\n",
                "Run only the next two cells in the current kernel. This stage "
                "uses local observation multisets and a balanced deterministic "
                "decision tree under the same 11 grouped holdouts. Topology, depth, "
                "intervention identifiers, answer, graph condition, and target are "
                "never decoder features. No model component is edited or frozen.\n",
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
    "(* S87C PREFLIGHT CELL *)\n"
    + preflight_cell
    + "\n(* S87C RESEARCH CELL *)\n"
    + research_cell,
    encoding="utf-8",
)

print(NOTEBOOK)
print(WL_OUTPUT)
