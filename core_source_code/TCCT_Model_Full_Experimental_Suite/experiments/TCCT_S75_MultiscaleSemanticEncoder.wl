(* S75 CELL *)
ClearAll["Global`*75"];

originalFrozenModel75=<|
"Params"->{0,-1,1,-1,-1,0},
"K"->5,
"Policy"->{1,4}
|>;

originalModelLock75=SameQ[
originalFrozenModel75,
frozenModel74,
frozenModel73,
frozenModel72,
frozen71
];

s74ResultLock75=And[
TrueQ[preflightPass74],
TrueQ[cert74["PreflightPassed"]],
SameQ[cert74["CasesPerTopologyPerRadius"],32]
];

preflightPass75=And[
originalModelLock75,
s74ResultLock75
];

protocol75=<|
"Stage"->"S75",
"Name"->"MultiscaleSemanticEncoder",
"CoreTCCTChanged"->False,
"OriginalFrozenModelChanged"->False,
"NewRepresentationBranch"->True,
"Representation"->"PairedRadius2Radius3WithParentChildCardinality",
"Radii"->{2,3},
"K"->5,
"ParameterCount"->8,
"ParameterAlphabet"->{-1,0,1},
"ParameterCandidates"->6561,
"PolicyDerivedFromTrainingOnly"->True,
"TrainingGrammars"->{"S59","ChainIn"},
"TrainingDepths"->{2,5},
"HeldoutDepths"->{9,15},
"LegacyValidation"->{"SharedMerge","ParallelIn"},
"S72UsedAsValidation"->True,
"S75IsBlindTest"->False,
"RetuningOriginalModel"->False,
"S76ReservedForFutureBlindTest"->True
|>;

protocolHash75=Hash[
Normal[protocol75],
"SHA256",
"HexString"
];

Dataset[{
Join[
protocol75,
<|
"OriginalModelMatchesS71ThroughS74"->originalModelLock75,
"S74ResultMatches"->s74ResultLock75,
"PreflightPassed"->preflightPass75,
"ProtocolHash"->protocolHash75
|>
]
}]

(* S75 CELL *)
ClearAll[
DecisionStatePairs75,
CaseByGrammar75,
BuildRows75
];

DecisionStatePairs75[c_List]:=Module[
{rej,levels,nodes},
rej=Reject61[c];
If[
Length[rej]==0,
Return[{}]
];
levels=SigLevels61[c,3];
nodes=rej[[All,2]];
DeleteDuplicates[
Map[
Function[node,
{
Lookup[levels[[3]],node],
Lookup[levels[[4]],node]
}
],
nodes
]
]
];

CaseByGrammar75[
grammar_String,
depth_Integer,
answer_Integer,
target_String
]:=Switch[
grammar,
"S59",
Case59[depth,answer,target],
"ChainIn",
Case63["ChainIn",depth,answer,target],
"SharedMerge",
Case63["SharedMerge",depth,answer,target],
"ParallelIn",
Case71[depth,answer,target],
"ParallelOut"|"DiamondIn"|"SharedParallelIn",
Case72[grammar,depth,answer,target],
_,
$Failed
];

BuildRows75[
grammars_List,
depthSet_List
]:=Flatten[
Table[
<|
"Grammar"->grammar,
"Depth"->depth,
"Answer"->answer,
"Target"->target,
"StatePairs"->DecisionStatePairs75[
CaseByGrammar75[
grammar,
depth,
answer,
target
]
]
|>,
{grammar,grammars},
{depth,depthSet},
{answer,Range[4]},
{target,{"Continue","Stop"}}
],
3
];

trainRows75=BuildRows75[
{"S59","ChainIn"},
{2,5}
];

heldRows75=BuildRows75[
{"S59","ChainIn"},
{9,15}
];

legacyValidationRows75=BuildRows75[
{"SharedMerge","ParallelIn"},
{2,5,9,15}
];

s72ValidationRows75=BuildRows75[
{"ParallelOut","DiamondIn","SharedParallelIn"},
{2,5,9,15}
];

dataCert75=<|
"TrainingCases"->Length[trainRows75],
"HeldoutCases"->Length[heldRows75],
"LegacyValidationCases"->Length[legacyValidationRows75],
"S72ValidationCases"->Length[s72ValidationRows75],
"TrainingTargets"->Counts[Lookup[trainRows75,"Target"]],
"EmptyTrainingStatePairs"->Count[
Lookup[trainRows75,"StatePairs"],
{}
]
|>;

Dataset[{dataCert75}]

(* S75 CELL *)
ClearAll[
EncodeRows75,
TrainingPolicy75,
ScoreEncoded75,
EvaluateCandidate75,
SearchChunk75,
ChunkSummary75
];

EncodeRows75[
data_List,
p_List,
k_Integer
]:=Module[{rec},
rec[s_]:=rec[s]=If[
MatchQ[s,{_Integer,_Integer}],
1+Mod[
s[[1]]+2 s[[2]],
k
],
Module[
{z,ps,cs,parentSum,childSum,parentSquare,childSquare},
z=rec[s[[1]]];
ps=rec/@s[[2]];
cs=rec/@s[[3]];
parentSum=Total[ps-1];
childSum=Total[cs-1];
parentSquare=Total[(ps-1)^2];
childSquare=Total[(cs-1)^2];
1+Mod[
p[[1]]+
p[[2]](z-1)+
p[[3]]parentSum+
p[[4]]childSum+
p[[5]]parentSquare+
p[[6]]childSquare+
p[[7]]Length[ps]+
p[[8]]Length[cs],
k
]
]
];
Map[
Function[row,
Join[
KeyTake[
row,
{"Grammar","Depth","Answer","Target"}
],
<|
"Codes"->DeleteDuplicates[
Map[
Function[pair,
{
rec[pair[[1]]],
rec[pair[[2]]]
}
],
row["StatePairs"]
]
]
|>
]
],
data
]
];

TrainingPolicy75[encodedTraining_List]:=Module[
{continueRows,stopRows,continueCodes,stopCodes},
continueRows=Select[
encodedTraining,
# ["Target"]==="Continue"&
];
stopRows=Select[
encodedTraining,
# ["Target"]==="Stop"&
];
continueCodes=Union@@Lookup[continueRows,"Codes"];
stopCodes=Union@@Lookup[stopRows,"Codes"];
Complement[
continueCodes,
stopCodes
]
];

ScoreEncoded75[
encodedRows_List,
policy_List
]:=Total[
Map[
Function[row,
Module[{prediction,truth},
prediction=AnyTrue[
row["Codes"],
MemberQ[policy,#]&
];
truth=row["Target"]==="Continue";
Boole[SameQ[prediction,truth]]
]
],
encodedRows
]
];

EvaluateCandidate75[
p_List,
k_Integer
]:=Module[
{trainEncoded,policy,trainScore,heldScore,
legacyScore,s72Score},
trainEncoded=EncodeRows75[trainRows75,p,k];
policy=TrainingPolicy75[trainEncoded];
trainScore=ScoreEncoded75[
trainEncoded,
policy
];
If[
trainScore<Length[trainRows75],
Return[$Failed]
];
heldScore=ScoreEncoded75[
EncodeRows75[heldRows75,p,k],
policy
];
legacyScore=ScoreEncoded75[
EncodeRows75[legacyValidationRows75,p,k],
policy
];
s72Score=ScoreEncoded75[
EncodeRows75[s72ValidationRows75,p,k],
policy
];
<|
"Params"->p,
"K"->k,
"Policy"->policy,
"PolicyLength"->Length[policy],
"L1"->Total[Abs[p]],
"TrainScore"->trainScore,
"HeldScore"->heldScore,
"LegacyScore"->legacyScore,
"S72Score"->s72Score,
"SeenTotal"->heldScore+legacyScore+s72Score,
"AllSeenPerfect"->And[
heldScore==Length[heldRows75],
legacyScore==Length[legacyValidationRows75],
s72Score==Length[s72ValidationRows75]
]
|>
];

SearchChunk75[
parameterChunk_List,
k_Integer
]:=DeleteCases[
EvaluateCandidate75[#,k]&/@parameterChunk,
$Failed
];

ChunkSummary75[
rows_List,
chunkID_Integer
]:=<|
"Chunk"->chunkID,
"TrainingPerfectCandidates"->Length[rows],
"BestHeldScore"->If[
Length[rows]>0,
Max[Lookup[rows,"HeldScore"]],
Missing["NoTrainingPerfectCandidate"]
],
"BestLegacyScore"->If[
Length[rows]>0,
Max[Lookup[rows,"LegacyScore"]],
Missing["NoTrainingPerfectCandidate"]
],
"BestS72Score"->If[
Length[rows]>0,
Max[Lookup[rows,"S72Score"]],
Missing["NoTrainingPerfectCandidate"]
]
|>;

(* S75 CELL *)
params75=Tuples[
{-1,0,1},
8
];

chunks75=Partition[
params75,
UpTo[2187]
];

gridCert75=<|
"ParameterCandidates"->Length[params75],
"Chunks"->Length[chunks75],
"ChunkSizes"->Length/@chunks75,
"K"->5
|>;

Dataset[{gridCert75}]

(* S75 CELL *)
r75A=SearchChunk75[
chunks75[[1]],
5
];

Dataset[{ChunkSummary75[r75A,1]}]

(* S75 CELL *)
r75B=SearchChunk75[
chunks75[[2]],
5
];

Dataset[{ChunkSummary75[r75B,2]}]

(* S75 CELL *)
r75C=SearchChunk75[
chunks75[[3]],
5
];

Dataset[{ChunkSummary75[r75C,3]}]

(* S75 CELL *)
candidates75=Join[
r75A,
r75B,
r75C
];

rankedCandidates75=SortBy[
candidates75,
Function[m,
{
-m["HeldScore"],
-m["LegacyScore"],
-m["S72Score"],
m["L1"],
m["PolicyLength"],
m["Params"],
m["Policy"]
}
]
];

selected75=If[
Length[rankedCandidates75]>0,
First[rankedCandidates75],
$Failed
];

selectionSummary75=<|
"TrainingPerfectCandidates"->Length[candidates75],
"AllSeenPerfectCandidates"->Count[
candidates75,
x_/;TrueQ[x["AllSeenPerfect"]]
],
"BestHeldScore"->If[
Length[candidates75]>0,
Max[Lookup[candidates75,"HeldScore"]],
Missing["None"]
],
"BestLegacyScore"->If[
Length[candidates75]>0,
Max[Lookup[candidates75,"LegacyScore"]],
Missing["None"]
],
"BestS72Score"->If[
Length[candidates75]>0,
Max[Lookup[candidates75,"S72Score"]],
Missing["None"]
],
"Selected"->selected75
|>;

Dataset[{selectionSummary75}]

(* S75 CELL *)
grammarList75={
"S59",
"ChainIn",
"SharedMerge",
"ParallelIn",
"ParallelOut",
"DiamondIn",
"SharedParallelIn"
};

fullRowsByGrammar75=AssociationMap[
BuildRows75[{#},{2,5,9,15}]&,
grammarList75
];

grammarScores75=If[
AssociationQ[selected75],
AssociationMap[
Function[grammar,
ScoreEncoded75[
EncodeRows75[
fullRowsByGrammar75[grammar],
selected75["Params"],
selected75["K"]
],
selected75["Policy"]
]
],
grammarList75
],
<||>
];

frozen75=If[
AssociationQ[selected75],
<|
"Representation"->"PairedRadius2Radius3WithParentChildCardinality",
"Params"->selected75["Params"],
"K"->selected75["K"],
"Policy"->selected75["Policy"]
|>,
$Failed
];

cert75=<|
"Stage"->"S75",
"Name"->"MultiscaleSemanticEncoder",
"CoreTCCTChanged"->False,
"OriginalFrozenModelChanged"->False,
"RepresentationChangedInNewBranch"->True,
"ProtocolHash"->protocolHash75,
"PolicyDerivedFromTrainingOnly"->True,
"S72UsedAsValidation"->True,
"S75IsBlindTest"->False,
"ParameterCandidates"->Length[params75],
"TrainingPerfectCandidates"->Length[candidates75],
"AllSeenPerfectCandidates"->Count[
candidates75,
x_/;TrueQ[x["AllSeenPerfect"]]
],
"FrozenCandidate"->frozen75,
"ScoresByGrammar"->grammarScores75,
"AllSeenGrammarsPerfect"->And@@Map[
SameQ[#,32]&,
Lookup[grammarScores75,grammarList75]
],
"S76ReservedForFutureBlindTest"->True
|>;

Dataset[{cert75}]

(* S75 CELL *)
Dataset[
Map[
KeyTake[
#,
{
"Params",
"K",
"PolicyLength",
"L1",
"TrainScore",
"HeldScore",
"LegacyScore",
"S72Score",
"SeenTotal",
"AllSeenPerfect"
}
]&,
Take[
rankedCandidates75,
UpTo[20]
]
]
]
