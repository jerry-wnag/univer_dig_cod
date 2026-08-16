(* S75D CELL *)
ClearAll["Global`*75D"];

expectedS75CProtocolHash75D=
"763931dc1199993023561d2a215f54797ea57cbef62923c242ad83f32df7d14b";

expectedParams75D={-1,0,-1,-1,-1,0,1,-1};
expectedK75D=5;
expectedTrainingPolicy75D={{3,1},{3,3},{4,3}};
expectedAddedContinueCodes75D={{1,3},{2,2},{3,2}};
expectedCompletedPolicy75D={
{1,3},{2,2},{3,1},{3,2},{3,3},{4,3}
};

selectedS75CResultLock75D=And[
AssociationQ[selectedSemanticRow75C],
SameQ[
Lookup[
selectedSemanticRow75C,
{
"Params","K","TrainingPolicy","ActualValidationScore",
"ActualAllSeenScore","GlobalSharedTokens",
"GlobalSafePolicyScore","GlobalSemanticClean",
"GlobalSafePolicy","AddedContinueCodes",
"CompletionEditCount","MissedContinueCases",
"TriggeredStopCases","SemanticClass"
}
],
{
expectedParams75D,expectedK75D,expectedTrainingPolicy75D,
160,192,0,224,True,expectedCompletedPolicy75D,
expectedAddedContinueCodes75D,3,32,0,
"SemanticCleanCoverageGap"
}
]
];

s75CResultLock75D=And[
TrueQ[preflightPass75C],
TrueQ[cert75C["PreflightPassed"]],
TrueQ[cert75C["S75BResultLockPassed"]],
SameQ[protocolHash75C,expectedS75CProtocolHash75D],
SameQ[
Lookup[
populationSummary75C,
{
"CandidatesAudited","AllScoreConsistencyChecksPassed",
"GloballySolvableCandidates","GlobalSemanticCleanCandidates",
"TrainingPolicyAllSeenPerfectCandidates",
"BestValidationScoreGloballySolvable",
"BestValidationScoreSemanticClean",
"MinimumCompletionEditsSemanticClean",
"FrozenSelectionRankAmongCleanByTotal",
"FrozenSelectionRankAmongCleanByProtocol"
}
],
{1795,True,2,2,0,160,160,3,1,1}
],
SameQ[
Lookup[frozen71,{"Params","K","Policy"}],
{{0,-1,1,-1,-1,0},5,{1,4}}
],
selectedS75CResultLock75D,
SameQ[cert75C["PolicyCompletionAppliedToFrozenModel"],False],
SameQ[cert75C["NewCandidateSelected"],False],
SameQ[cert75C["S76BlindTestRun"],False]
];

protocol75D=<|
"Stage"->"S75D",
"Name"->"ValidatedPolicyCompletionCheckpoint",
"CoreTCCTChanged"->False,
"OriginalFrozenModelChanged"->False,
"S75EncoderParamsChanged"->False,
"S75KChanged"->False,
"NewCandidateSelected"->False,
"PolicyChanged"->True,
"PolicyChangeType"->"AddValidationConfirmedContinueTokens",
"PolicyCompletionUsesValidationLabels"->True,
"PolicyCompletionIsTrainingOnly"->False,
"Current224CasesUsedAsValidation"->True,
"ExpectedAddedContinueCodes"->expectedAddedContinueCodes75D,
"ExpectedCompletedPolicy"->expectedCompletedPolicy75D,
"S75CResultLockPassed"->s75CResultLock75D,
"S76BlindTestRun"->False
|>;

protocolHash75D=Hash[
Normal[protocol75D],
"SHA256",
"HexString"
];

preflightPass75D=And[
TrueQ[s75CResultLock75D],
SameQ[selected75["Params"],expectedParams75D],
SameQ[selected75["K"],expectedK75D],
SameQ[selected75["Policy"],expectedTrainingPolicy75D]
];

preflight75D=Join[
protocol75D,
<|
"PreflightPassed"->preflightPass75D,
"S75CProtocolHash"->protocolHash75C,
"S75DProtocolHash"->protocolHash75D
|>
];

If[
!TrueQ[preflightPass75D],
Print[Dataset[{preflight75D}]];
Print["S75D aborted: S75C result lock or frozen model lock failed."];
Abort[]
];

Dataset[{preflight75D}]

(* S75D CELL *)
ClearAll[ScoreRowsWithPolicy75D];

trainingPolicy75D=selected75["Policy"];
addedContinueCodes75D=selectedSemanticRow75C[
"AddedContinueCodes"
];
completedPolicy75D=Sort@Union[
trainingPolicy75D,
addedContinueCodes75D
];

frozen75D=<|
"Stage"->"S75D",
"Name"->"ValidatedPolicyCompletion",
"Representation"->
"PairedRadius2Radius3WithParentChildCardinality",
"Params"->selected75["Params"],
"K"->selected75["K"],
"TrainingPolicy"->trainingPolicy75D,
"Policy"->completedPolicy75D,
"AddedContinueCodes"->addedContinueCodes75D,
"PolicyCompletionUsesValidationLabels"->True,
"FrozenBeforeS76"->True
|>;

frozenModelHash75D=Hash[
Normal[frozen75D],
"SHA256",
"HexString"
];

ScoreRowsWithPolicy75D[
rows_List,
policy_List
]:=ScoreEncoded75[
EncodeRows75[
rows,
frozen75D["Params"],
frozen75D["K"]
],
policy
];

allSeenEncoded75D=EncodeRows75[
allSeenRows75B,
frozen75D["Params"],
frozen75D["K"]
];

trainingPolicyErrors75D=PolicyErrorCounts75B[
allSeenEncoded75D,
trainingPolicy75D
];

completedPolicyErrors75D=PolicyErrorCounts75B[
allSeenEncoded75D,
completedPolicy75D
];

completionSummary75D=<|
"Params"->frozen75D["Params"],
"K"->frozen75D["K"],
"TrainingPolicy"->trainingPolicy75D,
"CompletedPolicy"->completedPolicy75D,
"AddedContinueCodes"->Complement[
completedPolicy75D,
trainingPolicy75D
],
"RemovedTrainingCodes"->Complement[
trainingPolicy75D,
completedPolicy75D
],
"TrainingPolicyAllSeenScore"->ScoreEncoded75[
allSeenEncoded75D,
trainingPolicy75D
],
"CompletedPolicyAllSeenScore"->ScoreEncoded75[
allSeenEncoded75D,
completedPolicy75D
],
"AllSeenCases"->Length[allSeenEncoded75D],
"TrainingPolicyErrors"->trainingPolicyErrors75D,
"CompletedPolicyErrors"->completedPolicyErrors75D,
"FrozenModelHash"->frozenModelHash75D
|>;

Dataset[{completionSummary75D}]

(* S75D CELL *)
scopeRows75D=<|
"Training"->trainRows75,
"Heldout"->heldRows75,
"Legacy"->legacyValidationRows75,
"S72"->s72ValidationRows75,
"AllSeen"->allSeenRows75B
|>;

scopeScoreTable75D=Association@KeyValueMap[
Function[{scope,rows},
scope-><|
"Cases"->Length[rows],
"TrainingPolicyScore"->ScoreRowsWithPolicy75D[
rows,
trainingPolicy75D
],
"CompletedPolicyScore"->ScoreRowsWithPolicy75D[
rows,
completedPolicy75D
],
"RecoveredCases"->(
ScoreRowsWithPolicy75D[rows,completedPolicy75D]-
ScoreRowsWithPolicy75D[rows,trainingPolicy75D]
)
|>
],
scopeRows75D
];

grammarScoreTable75D=Map[
Function[grammar,
Module[{rows},
rows=Select[
allSeenRows75B,
# ["Grammar"]===grammar&
];
<|
"Grammar"->grammar,
"Cases"->Length[rows],
"TrainingPolicyScore"->ScoreRowsWithPolicy75D[
rows,
trainingPolicy75D
],
"CompletedPolicyScore"->ScoreRowsWithPolicy75D[
rows,
completedPolicy75D
]
|>
]
],
grammarList75
];

Dataset[KeyValueMap[Join[<|"Scope"->#1|>,#2]&,scopeScoreTable75D]]

Dataset[grammarScoreTable75D]

(* S75D CELL *)
allSeenTokenSets75D=TokenSets75B[allSeenEncoded75D];
semanticFeasibility75D=SemanticFeasibility75B[
allSeenEncoded75D
];

policyTokenAudit75D=Map[
Function[token,
<|
"Token"->token,
"AllSeenMeaning"->TokenMeaning75B[
token,
allSeenTokenSets75D
],
"InTrainingPolicy"->MemberQ[trainingPolicy75D,token],
"InCompletedPolicy"->MemberQ[completedPolicy75D,token],
"AddedAtS75D"->MemberQ[addedContinueCodes75D,token]
|>
],
allSeenTokenSets75D["All"]
];

completionSafety75D=<|
"GlobalSharedTokens"->semanticFeasibility75D[
"SharedTokens"
],
"GlobalPerfectPolicyFeasible"->semanticFeasibility75D[
"PerfectPurePolicyFeasible"
],
"GlobalSafePolicy"->semanticFeasibility75D[
"SafePolicy"
],
"CompletedPolicyEqualsGlobalSafePolicy"->SameQ[
completedPolicy75D,
semanticFeasibility75D["SafePolicy"]
],
"UncoveredContinueTokens"->Complement[
allSeenTokenSets75D["Continue"],
completedPolicy75D
],
"SelectedStopTokens"->Intersection[
completedPolicy75D,
allSeenTokenSets75D["Stop"]
],
"UnobservedPolicyTokens"->Complement[
completedPolicy75D,
allSeenTokenSets75D["All"]
]
|>;

Dataset[{completionSafety75D}]

Dataset[Select[policyTokenAudit75D,TrueQ[# ["InCompletedPolicy"]]&]]

(* S75D CELL *)
allGrammarScoresPerfect75D=And@@Map[
SameQ[# ["CompletedPolicyScore"],# ["Cases"]]&,
grammarScoreTable75D
];

resultLock75D=And[
TrueQ[preflightPass75D],
SameQ[frozen75D["Params"],expectedParams75D],
SameQ[frozen75D["K"],expectedK75D],
SameQ[trainingPolicy75D,expectedTrainingPolicy75D],
SameQ[addedContinueCodes75D,expectedAddedContinueCodes75D],
SameQ[completedPolicy75D,expectedCompletedPolicy75D],
SameQ[
completionSummary75D["TrainingPolicyAllSeenScore"],
192
],
SameQ[
completionSummary75D["CompletedPolicyAllSeenScore"],
224
],
SameQ[completionSummary75D["AllSeenCases"],224],
SameQ[
Lookup[
completedPolicyErrors75D,
{"MissedContinueCases","TriggeredStopCases"}
],
{0,0}
],
SameQ[
completionSummary75D["RemovedTrainingCodes"],
{}
],
SameQ[semanticFeasibility75D["SharedTokens"],0],
TrueQ[semanticFeasibility75D["PerfectPurePolicyFeasible"]],
TrueQ[
completionSafety75D[
"CompletedPolicyEqualsGlobalSafePolicy"
]
],
SameQ[completionSafety75D["UncoveredContinueTokens"],{}],
SameQ[completionSafety75D["SelectedStopTokens"],{}],
SameQ[completionSafety75D["UnobservedPolicyTokens"],{}],
TrueQ[allGrammarScoresPerfect75D]
];

checkpoint75D=<|
"Stage"->"S75D",
"Name"->"ValidatedPolicyCompletionCheckpoint",
"Status"->If[resultLock75D,"FROZEN","FAILED"],
"CoreTCCTChanged"->False,
"OriginalFrozenModelChanged"->False,
"EncoderParamsChanged"->False,
"KChanged"->False,
"NewCandidateSelected"->False,
"Params"->frozen75D["Params"],
"K"->frozen75D["K"],
"TrainingPolicy"->trainingPolicy75D,
"CompletedPolicy"->completedPolicy75D,
"AddedContinueCodes"->addedContinueCodes75D,
"PolicyCompletionUsesValidationLabels"->True,
"PolicyCompletionIsTrainingOnly"->False,
"PolicyCompletionAppliedToS75Model"->True,
"TrainingPolicyAllSeenScore"->192,
"CompletedPolicyAllSeenScore"->ScoreEncoded75[
allSeenEncoded75D,
completedPolicy75D
],
"AllSeenCases"->Length[allSeenEncoded75D],
"AllSeenAccuracy"->N[
ScoreEncoded75[allSeenEncoded75D,completedPolicy75D]/
Length[allSeenEncoded75D]
],
"GlobalSharedTokens"->semanticFeasibility75D[
"SharedTokens"
],
"MissedContinueCases"->completedPolicyErrors75D[
"MissedContinueCases"
],
"TriggeredStopCases"->completedPolicyErrors75D[
"TriggeredStopCases"
],
"AllSevenGrammarsPerfect"->allGrammarScoresPerfect75D,
"FrozenBeforeS76"->resultLock75D,
"S76BlindTestRun"->False,
"S75CProtocolHash"->protocolHash75C,
"S75DProtocolHash"->protocolHash75D,
"FrozenModelHash"->frozenModelHash75D,
"ResultLockPassed"->resultLock75D
|>;

checkpointHash75D=Hash[
Normal[checkpoint75D],
"SHA256",
"HexString"
];

cert75D=Join[
checkpoint75D,
<|
"CheckpointHash"->checkpointHash75D,
"ScopeScores"->scopeScoreTable75D,
"GrammarScores"->grammarScoreTable75D,
"CompletionSafety"->completionSafety75D
|>
];

If[
!TrueQ[resultLock75D],
Print[Dataset[{cert75D}]];
Print["S75D failed: do not proceed to S76."];
Abort[]
];

Dataset[{checkpoint75D}]

Dataset[{cert75D}]
