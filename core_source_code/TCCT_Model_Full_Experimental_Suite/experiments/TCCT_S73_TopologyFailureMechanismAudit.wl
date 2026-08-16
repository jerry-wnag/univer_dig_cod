(* S73 CELL *)
ClearAll["Global`*73"];

frozenModel73=<|
"Params"->{0,-1,1,-1,-1,0},
"K"->5,
"Policy"->{1,4}
|>;

expectedS72ProtocolHash73=
"9655a29d19e0069fd40b340f33cdf72bc729a712aa2e485423f640a3d6335feb";

expectedS72Scores73=<|
"ParallelOut"->8,
"DiamondIn"->16,
"SharedParallelIn"->28
|>;

modelLock73=SameQ[
frozenModel73,
frozenModel72,
frozen71
];

protocolLock73=SameQ[
protocolHash72,
expectedS72ProtocolHash73
];

resultLock73=And[
SameQ[scoresByTopology72,expectedS72Scores73],
SameQ[Total[Lookup[caseResults72,"Passed"]],52],
SameQ[Length[caseResults72],96]
];

preflightPass73=And[
modelLock73,
protocolLock73,
resultLock73
];

preflight73=<|
"Stage"->"S73",
"Name"->"TopologyFailureMechanismAudit",
"AuditOnly"->True,
"CoreTCCTChanged"->False,
"ModelChanged"->False,
"RetuningAllowed"->False,
"NewModelSearch"->False,
"ModelMatchesS71AndS72"->modelLock73,
"S72ProtocolHashMatches"->protocolLock73,
"S72ResultMatches"->resultLock73,
"PreflightPassed"->preflightPass73
|>;

Dataset[{preflight73}]

(* S73 CELL *)
ClearAll[SelectedCodes73,CaseAudit73];

SelectedCodes73[codes_List]:=Select[
Sort@DeleteDuplicates[codes],
MemberQ[frozenModel73["Policy"],#]&
];

CaseAudit73[row_Association]:=Module[
{selected,failureType},
selected=SelectedCodes73[row["Codes"]];
failureType=Which[
row["Passed"]==1,
"Correct",
row["Target"]==="Continue",
"ContinueFalseNegative",
True,
"StopFalsePositive"
];
Join[
row,
<|
"SelectedCodes"->selected,
"SelectedCount"->Length[selected],
"CodeSignature"->Sort[row["Codes"]],
"FailureType"->failureType
|>
]
];

caseAudit73=If[
TrueQ[preflightPass73],
CaseAudit73/@caseResults72,
{}
];

answerSummary73=Flatten[
Table[
Module[{sub,continueRows,stopRows},
sub=Select[
caseAudit73,
# ["Grammar"]===topology&&# ["Answer"]===answer&
];
continueRows=Select[sub,# ["Target"]==="Continue"&];
stopRows=Select[sub,# ["Target"]==="Stop"&];
<|
"Topology"->topology,
"Answer"->answer,
"Cases"->Length[sub],
"Passed"->Total[Lookup[sub,"Passed"]],
"Accuracy"->N[Mean[Lookup[sub,"Passed"]]],
"ContinuePassed"->Total[Lookup[continueRows,"Passed"]],
"StopPassed"->Total[Lookup[stopRows,"Passed"]],
"FailureTypes"->Counts[Lookup[sub,"FailureType"]],
"ContinueSelectedPatterns"->Counts[
Lookup[continueRows,"SelectedCodes"]
],
"StopSelectedPatterns"->Counts[
Lookup[stopRows,"SelectedCodes"]
],
"DepthInvariantPrediction"->And[
Length[DeleteDuplicates[Lookup[continueRows,"Prediction"]]]==1,
Length[DeleteDuplicates[Lookup[stopRows,"Prediction"]]]==1
]
|>
],
{topology,topologies72},
{answer,answers72}
],
1
];

Dataset[answerSummary73]

(* S73 CELL *)
pairRows73=Flatten[
Table[
Module[{continueRow,stopRow,continueSelected,stopSelected},
continueRow=SelectFirst[
caseAudit73,
# ["Grammar"]===topology&&
# ["Depth"]===depth&&
# ["Answer"]===answer&&
# ["Target"]==="Continue"&
];
stopRow=SelectFirst[
caseAudit73,
# ["Grammar"]===topology&&
# ["Depth"]===depth&&
# ["Answer"]===answer&&
# ["Target"]==="Stop"&
];
continueSelected=continueRow["SelectedCodes"];
stopSelected=stopRow["SelectedCodes"];
<|
"Topology"->topology,
"Depth"->depth,
"Answer"->answer,
"ContinueCodes"->continueRow["CodeSignature"],
"StopCodes"->stopRow["CodeSignature"],
"ContinueSelected"->continueSelected,
"StopSelected"->stopSelected,
"SharedCodes"->Intersection[
continueRow["CodeSignature"],
stopRow["CodeSignature"]
],
"SharedSelectedCodes"->Intersection[
continueSelected,
stopSelected
],
"PolicySeparable"->And[
Length[continueSelected]>0,
Length[stopSelected]==0
],
"PairPassed"->Boole[
continueRow["Passed"]==1&&stopRow["Passed"]==1
],
"PairSignature"->{
continueRow["CodeSignature"],
stopRow["CodeSignature"]
}
|>
],
{topology,topologies72},
{depth,depths72},
{answer,answers72}
],
2
];

pairSummary73=Flatten[
Table[
Module[{sub},
sub=Select[
pairRows73,
# ["Topology"]===topology&&# ["Answer"]===answer&
];
<|
"Topology"->topology,
"Answer"->answer,
"DepthPairs"->Length[sub],
"PerfectDepthPairs"->Total[Lookup[sub,"PairPassed"]],
"PolicySeparableDepths"->Count[
Lookup[sub,"PolicySeparable"],
True
],
"DepthInvariantCodePair"->Apply[
SameQ,
Lookup[sub,"PairSignature"]
],
"ContinueSelectedPatterns"->Counts[
Lookup[sub,"ContinueSelected"]
],
"StopSelectedPatterns"->Counts[
Lookup[sub,"StopSelected"]
],
"SharedSelectedPatterns"->Counts[
Lookup[sub,"SharedSelectedCodes"]
]
|>
],
{topology,topologies72},
{answer,answers72}
],
1
];

Dataset[pairSummary73]

(* S73 CELL *)
rawStateRows73=If[
TrueQ[preflightPass73],
Flatten[
Map[
Function[row,
Map[
Function[state,
Module[{knownPosition,knownID,knownTarget,code},
knownPosition=FirstPosition[
states64,
state,
Missing["Novel"]
];
knownID=If[
MissingQ[knownPosition],
Missing["Novel"],
First[knownPosition]
];
knownTarget=If[
IntegerQ[knownID],
stateRows70D[[knownID]]["Target"],
Missing["Novel"]
];
code=CodeState70D[
state,
frozenModel73["Params"],
frozenModel73["K"]
];
<|
"Topology"->row["Grammar"],
"Depth"->row["Depth"],
"Answer"->row["Answer"],
"Target"->row["Target"],
"StateHash"->Hash[state,"SHA256","HexString"],
"KnownStateID"->knownID,
"KnownTarget"->knownTarget,
"Code"->code,
"SelectedCode"->MemberQ[
frozenModel73["Policy"],
code
]
|>
]
],
row["States"]
]
],
testRows72
],
1
],
{}
];

codeAudit73=Flatten[
Table[
Module[{topologyRows,codes},
topologyRows=Select[
rawStateRows73,
# ["Topology"]===topology&
];
codes=Sort@DeleteDuplicates[Lookup[topologyRows,"Code"]];
Map[
Function[code,
Module[{sub,targets,continueCount,stopCount},
sub=Select[topologyRows,# ["Code"]===code&];
targets=DeleteDuplicates[Lookup[sub,"Target"]];
continueCount=Count[Lookup[sub,"Target"],"Continue"];
stopCount=Count[Lookup[sub,"Target"],"Stop"];
<|
"Topology"->topology,
"Code"->code,
"SelectedCode"->MemberQ[frozenModel73["Policy"],code],
"ContinueOccurrences"->continueCount,
"StopOccurrences"->stopCount,
"SemanticCollision"->And[
MemberQ[targets,"Continue"],
MemberQ[targets,"Stop"]
],
"StopRisk"->And[
MemberQ[frozenModel73["Policy"],code],
stopCount>0
],
"ContinueSupport"->And[
MemberQ[frozenModel73["Policy"],code],
continueCount>0
]
|>
]
],
codes
]
],
{topology,topologies72}
],
1
];

Dataset[codeAudit73]

(* S73 CELL *)
stateSummary73=Map[
Function[topology,
Module[{stateSub,codeSub,knownCount,novelCount},
stateSub=Select[
rawStateRows73,
# ["Topology"]===topology&
];
codeSub=Select[
codeAudit73,
# ["Topology"]===topology&
];
knownCount=Count[Lookup[stateSub,"KnownStateID"],_Integer];
novelCount=Length[stateSub]-knownCount;
<|
"Topology"->topology,
"StateOccurrences"->Length[stateSub],
"DistinctRawStates"->Length@DeleteDuplicates[
Lookup[stateSub,"StateHash"]
],
"KnownStateOccurrences"->knownCount,
"NovelStateOccurrences"->novelCount,
"NovelStateFraction"->If[
Length[stateSub]>0,
N[novelCount/Length[stateSub]],
0.
],
"DistinctCodes"->Length[codeSub],
"SemanticCollisionCodes"->Count[
Lookup[codeSub,"SemanticCollision"],
True
],
"SelectedCollisionCodes"->Count[
codeSub,
x_/;TrueQ[x["SemanticCollision"]]&&TrueQ[x["SelectedCode"]]
],
"SelectedCodesAppearingInStop"->Count[
Lookup[codeSub,"StopRisk"],
True
],
"SelectedCodesSupportingContinue"->Count[
Lookup[codeSub,"ContinueSupport"],
True
]
|>
]
],
topologies72
];

Dataset[stateSummary73]

(* S73 CELL *)
failureExamples73=Map[
Function[row,
KeyTake[
row,
{
"Grammar",
"Depth",
"Answer",
"Target",
"Prediction",
"Codes",
"SelectedCodes",
"FailureType"
}
]
],
DeleteDuplicatesBy[
Select[caseAudit73,# ["Passed"]==0&],
{
# ["Grammar"],
# ["Answer"],
# ["Target"],
# ["FailureType"]
}&
]
];

Dataset[failureExamples73]

(* S73 CELL *)
failureCounts73=AssociationMap[
Function[topology,
Counts[
Lookup[
Select[caseAudit73,# ["Grammar"]===topology&],
"FailureType"
]
]
],
topologies72
];

accuracyByTopology73=AssociationMap[
Function[topology,
N@Mean[
Lookup[
Select[caseAudit73,# ["Grammar"]===topology&],
"Passed"
]
]
],
topologies72
];

auditCert73=<|
"Stage"->"S73",
"Name"->"TopologyFailureMechanismAudit",
"AuditOnly"->True,
"CoreTCCTChanged"->False,
"ModelChanged"->False,
"RetuningAllowed"->False,
"PreflightPassed"->preflightPass73,
"FrozenModel"->frozenModel73,
"S72ProtocolHash"->protocolHash72,
"CasesAudited"->Length[caseAudit73],
"AccuracyByTopology"->accuracyByTopology73,
"FailureCountsByTopology"->failureCounts73,
"StateMechanismSummary"->AssociationThread[
topologies72,
KeyDrop[stateSummary73,"Topology"]
]
|>;

Dataset[{auditCert73}]

(* S73 CELL *)
scoreMatrix73=Table[
Total[
Lookup[
Select[
caseAudit73,
# ["Grammar"]===topology&&# ["Answer"]===answer&
],
"Passed"
]
],
{topology,topologies72},
{answer,answers72}
];

MatrixPlot[
scoreMatrix73,
PlotLegends->Automatic,
PlotLabel->"S73 passed cases by topology and answer (out of 8)",
FrameTicks->{
Thread[Range[Length[topologies72]]->topologies72],
Thread[Range[Length[answers72]]->answers72]
},
ImageSize->Large
]
