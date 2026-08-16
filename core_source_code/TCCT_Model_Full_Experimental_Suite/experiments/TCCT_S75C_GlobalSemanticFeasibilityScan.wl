(* S75C CELL *)
ClearAll["Global`*75C"];

expectedS75BProtocolHash75C=
"eb3bc37f8c9ee9fb2932f2fc2c9f66301866c9f367cbb49fb4397c1dbf42e9bd";

frozenGlobalSummary75C=First@Select[
cert75B["GlobalCrossTopologySummary"],
# ["CandidateRole"]==="FrozenProtocolSelection"&
];

s75BResultLock75C=And[
TrueQ[preflightPass75B],
TrueQ[cert75B["PreflightPassed"]],
TrueQ[cert75B["S75AResultLockPassed"]],
SameQ[protocolHash75B,expectedS75BProtocolHash75C],
SameQ[cert75B["DataCertificate"]["AllSeenCases"],224],
SameQ[cert75B["DataCertificate"]["ValidationCases"],192],
SameQ[
Lookup[
frozenGlobalSummary75C,
{
"RawPerfectPolicyFeasible",
"LatentPerfectPolicyFeasible",
"RawSafePolicyScoreCombined",
"LatentSafePolicyScoreCombined",
"TrainingPolicyScoreCombined",
"UnseenEvaluationContinueTokens",
"MissedContinueCases",
"TriggeredStopCases",
"RootCause"
}
],
{
True,True,224,224,192,3,32,0,
"TrainingCoverageGap"
}
]
];

protocol75C=<|
"Stage"->"S75C",
"Name"->"GlobalSemanticFeasibilityScan",
"AuditOnly"->True,
"CoreTCCTChanged"->False,
"OriginalFrozenModelChanged"->False,
"S75SelectionChanged"->False,
"S75BResultChanged"->False,
"NewParameterSearchIntroduced"->False,
"ExistingTrainingPerfectCandidatesAudited"->1795,
"AllSeenCasesPerCandidate"->224,
"ValidationCasesPerCandidate"->192,
"GlobalSemanticCleanDefinition"->
"PerfectPurePolicyFeasibleAndZeroSharedTokens",
"PolicyCompletionUsesValidationLabels"->True,
"PolicyCompletionIsDiagnosticOnly"->True,
"S75BResultLockPassed"->s75BResultLock75C
|>;

protocolHash75C=Hash[
Normal[protocol75C],
"SHA256",
"HexString"
];

preflightPass75C=And[
TrueQ[preflightPass75B],
TrueQ[s75BResultLock75C]
];

Dataset[{
Join[
protocol75C,
<|
"PreflightPassed"->preflightPass75C,
"S75BProtocolHash"->protocolHash75B,
"S75CProtocolHash"->protocolHash75C
|>
]
}]

(* S75C CELL *)
ClearAll[
EvaluateSemanticCandidate75C,
SemanticChunkSummary75C
];

rawAllSeenFeasibility75C=SemanticFeasibility75B[
RawEncodedRows75B[allSeenRows75B]
];

EvaluateSemanticCandidate75C[
candidate_Association
]:=Module[
{
allEncoded,trainEncoded,validationEncoded,trainSets,
validationSets,globalSets,globalFeasibility,policy,
actualValidationScore,actualAllSeenScore,policyErrors,
globalSafePolicy,globalSafeValidationScore,addedCodes,
invalidatedCodes,continueToStop,stopToContinue,
unseenContinue,unseenStop,semanticClean,semanticClass,
scoreConsistency
},
allEncoded=EncodeRows75[
allSeenRows75B,
candidate["Params"],
candidate["K"]
];
trainEncoded=Take[
allEncoded,
Length[trainRows75]
];
validationEncoded=Drop[
allEncoded,
Length[trainRows75]
];
trainSets=TokenSets75B[trainEncoded];
validationSets=TokenSets75B[validationEncoded];
globalSets=TokenSets75B[allEncoded];
globalFeasibility=SemanticFeasibility75B[allEncoded];
policy=candidate["Policy"];
actualValidationScore=ScoreEncoded75[
validationEncoded,
policy
];
actualAllSeenScore=ScoreEncoded75[
allEncoded,
policy
];
policyErrors=PolicyErrorCounts75B[
validationEncoded,
policy
];
globalSafePolicy=globalFeasibility["SafePolicy"];
globalSafeValidationScore=ScoreEncoded75[
validationEncoded,
globalSafePolicy
];
addedCodes=Complement[
globalSafePolicy,
policy
];
invalidatedCodes=Intersection[
policy,
globalSets["Stop"]
];
continueToStop=Intersection[
trainSets["ContinueOnly"],
validationSets["Stop"]
];
stopToContinue=Intersection[
trainSets["Stop"],
validationSets["Continue"]
];
unseenContinue=Complement[
validationSets["Continue"],
trainSets["All"]
];
unseenStop=Complement[
validationSets["Stop"],
trainSets["All"]
];
semanticClean=And[
TrueQ[globalFeasibility["PerfectPurePolicyFeasible"]],
SameQ[globalFeasibility["SharedTokens"],0]
];
scoreConsistency=And[
SameQ[actualValidationScore,candidate["SeenTotal"]],
SameQ[
actualAllSeenScore,
candidate["TrainScore"]+candidate["SeenTotal"]
]
];
semanticClass=Which[
Not@TrueQ[rawAllSeenFeasibility75C[
"PerfectPurePolicyFeasible"
]],
"RawCrossTopologyObservationConflict",
semanticClean&&actualAllSeenScore==Length[allSeenRows75B],
"SemanticCleanAndTrainingIdentified",
semanticClean,
"SemanticCleanCoverageGap",
TrueQ[globalFeasibility["PerfectPurePolicyFeasible"]],
"GloballySolvableWithRedundantMixedTokens",
True,
"LatentCrossTopologySemanticConflict"
];
<|
"Params"->candidate["Params"],
"K"->candidate["K"],
"TrainingPolicy"->policy,
"PolicyLength"->candidate["PolicyLength"],
"L1"->candidate["L1"],
"TrainScore"->candidate["TrainScore"],
"HeldScore"->candidate["HeldScore"],
"LegacyScore"->candidate["LegacyScore"],
"S72Score"->candidate["S72Score"],
"ActualValidationScore"->actualValidationScore,
"ActualAllSeenScore"->actualAllSeenScore,
"ScoreConsistencyPassed"->scoreConsistency,
"GlobalDistinctTokens"->globalFeasibility["DistinctTokens"],
"GlobalSharedTokens"->globalFeasibility["SharedTokens"],
"GlobalSafePolicyScore"->globalFeasibility[
"SafeSemanticPolicyScore"
],
"GlobalPerfectPolicyFeasible"->globalFeasibility[
"PerfectPurePolicyFeasible"
],
"GlobalSemanticClean"->semanticClean,
"GlobalSafePolicy"->globalSafePolicy,
"GlobalSafePolicyLength"->Length[globalSafePolicy],
"GlobalSafeValidationScore"->globalSafeValidationScore,
"AddedContinueCodes"->addedCodes,
"AddedContinueCodeCount"->Length[addedCodes],
"InvalidatedTrainingPolicyCodes"->invalidatedCodes,
"InvalidatedTrainingPolicyCodeCount"->Length[invalidatedCodes],
"CompletionEditCount"->Length[addedCodes]+Length[invalidatedCodes],
"TrainContinueToValidationStopTokens"->Length[continueToStop],
"TrainStopToValidationContinueTokens"->Length[stopToContinue],
"UnseenValidationContinueTokens"->Length[unseenContinue],
"UnseenValidationStopTokens"->Length[unseenStop],
"MissedContinueCases"->policyErrors["MissedContinueCases"],
"TriggeredStopCases"->policyErrors["TriggeredStopCases"],
"SemanticClass"->semanticClass
|>
];

SemanticChunkSummary75C[
rows_List,
chunkID_Integer
]:=<|
"Chunk"->chunkID,
"CandidatesAudited"->Length[rows],
"ScoreConsistencyPassed"->And@@Lookup[
rows,
"ScoreConsistencyPassed"
],
"GloballySolvable"->Count[
rows,
x_/;TrueQ[x["GlobalPerfectPolicyFeasible"]]
],
"GlobalSemanticClean"->Count[
rows,
x_/;TrueQ[x["GlobalSemanticClean"]]
],
"BestActualValidationScore"->If[
Length[rows]>0,
Max[Lookup[rows,"ActualValidationScore"]],
Missing["EmptyChunk"]
]
|>;

semanticCandidateChunks75C=Partition[
candidates75,
UpTo[600]
];

gridCert75C=<|
"CandidatesToAudit"->Length[candidates75],
"Chunks"->Length[semanticCandidateChunks75C],
"ChunkSizes"->Length/@semanticCandidateChunks75C,
"AllSeenCasesPerCandidate"->Length[allSeenRows75B],
"RawAllSeenPerfectPolicyFeasible"->rawAllSeenFeasibility75C[
"PerfectPurePolicyFeasible"
],
"RawAllSeenSafePolicyScore"->rawAllSeenFeasibility75C[
"SafeSemanticPolicyScore"
]
|>;

Dataset[{gridCert75C}]

(* S75C CELL *)
r75CA=EvaluateSemanticCandidate75C/@
semanticCandidateChunks75C[[1]];

Dataset[{SemanticChunkSummary75C[r75CA,1]}]

(* S75C CELL *)
r75CB=EvaluateSemanticCandidate75C/@
semanticCandidateChunks75C[[2]];

Dataset[{SemanticChunkSummary75C[r75CB,2]}]

(* S75C CELL *)
r75CC=EvaluateSemanticCandidate75C/@
semanticCandidateChunks75C[[3]];

Dataset[{SemanticChunkSummary75C[r75CC,3]}]

(* S75C CELL *)
ClearAll[
TotalRankKey75C,
ProtocolRankKey75C,
RankPosition75C
];

semanticRows75C=Join[
r75CA,r75CB,r75CC
];

globallySolvableRows75C=Select[
semanticRows75C,
TrueQ[# ["GlobalPerfectPolicyFeasible"]]&
];

semanticCleanRows75C=Select[
semanticRows75C,
TrueQ[# ["GlobalSemanticClean"]]&
];

TotalRankKey75C[row_Association]:={
-row["ActualValidationScore"],
row["CompletionEditCount"],
row["AddedContinueCodeCount"],
-row["HeldScore"],
-row["LegacyScore"],
-row["S72Score"],
row["L1"],
row["PolicyLength"],
row["Params"],
row["TrainingPolicy"]
};

ProtocolRankKey75C[row_Association]:={
-row["HeldScore"],
-row["LegacyScore"],
-row["S72Score"],
row["CompletionEditCount"],
row["L1"],
row["PolicyLength"],
row["Params"],
row["TrainingPolicy"]
};

rankedSolvableByTotal75C=SortBy[
globallySolvableRows75C,
TotalRankKey75C
];

rankedCleanByTotal75C=SortBy[
semanticCleanRows75C,
TotalRankKey75C
];

rankedCleanByProtocol75C=SortBy[
semanticCleanRows75C,
ProtocolRankKey75C
];

selectedSemanticRow75C=First@Select[
semanticRows75C,
SameQ[# ["Params"],selected75["Params"]]&
];

bestSolvableByTotal75C=If[
Length[rankedSolvableByTotal75C]>0,
First[rankedSolvableByTotal75C],
$Failed
];

bestCleanByTotal75C=If[
Length[rankedCleanByTotal75C]>0,
First[rankedCleanByTotal75C],
$Failed
];

bestCleanByProtocol75C=If[
Length[rankedCleanByProtocol75C]>0,
First[rankedCleanByProtocol75C],
$Failed
];

RankPosition75C[
rankedRows_List,
params_List
]:=Module[{position},
position=FirstPosition[
Lookup[rankedRows,"Params"],
params
];
If[
MissingQ[position],
Missing["NotInRanking"],
First[position]
]
];

semanticClassCounts75C=Counts[
Lookup[semanticRows75C,"SemanticClass"]
];

cleanScoreDistribution75C=Counts[
Lookup[
semanticCleanRows75C,
"ActualValidationScore"
]
];

populationSummary75C=<|
"CandidatesAudited"->Length[semanticRows75C],
"AllScoreConsistencyChecksPassed"->And@@Lookup[
semanticRows75C,
"ScoreConsistencyPassed"
],
"GloballySolvableCandidates"->Length[
globallySolvableRows75C
],
"GlobalSemanticCleanCandidates"->Length[
semanticCleanRows75C
],
"TrainingPolicyAllSeenPerfectCandidates"->Count[
semanticRows75C,
x_/;SameQ[x["ActualAllSeenScore"],224]
],
"BestValidationScoreGloballySolvable"->If[
Length[globallySolvableRows75C]>0,
Max[Lookup[
globallySolvableRows75C,
"ActualValidationScore"
]],
Missing["None"]
],
"BestValidationScoreSemanticClean"->If[
Length[semanticCleanRows75C]>0,
Max[Lookup[
semanticCleanRows75C,
"ActualValidationScore"
]],
Missing["None"]
],
"MinimumCompletionEditsSemanticClean"->If[
Length[semanticCleanRows75C]>0,
Min[Lookup[
semanticCleanRows75C,
"CompletionEditCount"
]],
Missing["None"]
],
"FrozenSelectionRankAmongCleanByTotal"->RankPosition75C[
rankedCleanByTotal75C,
selected75["Params"]
],
"FrozenSelectionRankAmongCleanByProtocol"->RankPosition75C[
rankedCleanByProtocol75C,
selected75["Params"]
],
"SemanticClassCounts"->semanticClassCounts75C,
"CleanValidationScoreDistribution"->cleanScoreDistribution75C
|>;

Dataset[{populationSummary75C}]

(* S75C CELL *)
representativeSemanticRows75C={
<|
"CandidateRole"->"FrozenProtocolSelection",
"Candidate"->selectedSemanticRow75C
|>,
<|
"CandidateRole"->"BestGloballySolvableByValidationTotal",
"Candidate"->bestSolvableByTotal75C
|>,
<|
"CandidateRole"->"BestSemanticCleanByValidationTotal",
"Candidate"->bestCleanByTotal75C
|>,
<|
"CandidateRole"->"BestSemanticCleanByFrozenProtocol",
"Candidate"->bestCleanByProtocol75C
|>
};

representativeSemanticTable75C=Map[
Function[spec,
Join[
<|"CandidateRole"->spec["CandidateRole"]|>,
KeyTake[
spec["Candidate"],
{
"Params","K","TrainingPolicy","HeldScore","LegacyScore",
"S72Score","ActualValidationScore","ActualAllSeenScore",
"GlobalSharedTokens","GlobalSafePolicyScore",
"GlobalPerfectPolicyFeasible","GlobalSemanticClean",
"GlobalSafePolicy","AddedContinueCodes",
"InvalidatedTrainingPolicyCodes","CompletionEditCount",
"UnseenValidationContinueTokens","MissedContinueCases",
"TriggeredStopCases","SemanticClass"
}
]
]
],
representativeSemanticRows75C
];

Dataset[representativeSemanticTable75C]

topCleanCandidates75C=Map[
KeyTake[
#,
{
"Params","K","TrainingPolicy","HeldScore","LegacyScore",
"S72Score","ActualValidationScore","GlobalSafePolicy",
"AddedContinueCodes","CompletionEditCount","L1",
"PolicyLength","SemanticClass"
}
]&,
Take[rankedCleanByTotal75C,UpTo[20]]
];

Dataset[topCleanCandidates75C]

(* S75C CELL *)
cert75C=<|
"Stage"->"S75C",
"Name"->"GlobalSemanticFeasibilityScan",
"AuditOnly"->True,
"CoreTCCTChanged"->False,
"OriginalFrozenModelChanged"->False,
"S75SelectionChanged"->False,
"S75BResultChanged"->False,
"S75BResultLockPassed"->s75BResultLock75C,
"PreflightPassed"->preflightPass75C,
"S75BProtocolHash"->protocolHash75B,
"S75CProtocolHash"->protocolHash75C,
"RawAllSeenFeasibility"->rawAllSeenFeasibility75C,
"PopulationSummary"->populationSummary75C,
"RepresentativeCandidates"->representativeSemanticTable75C,
"PolicyCompletionUsesValidationLabels"->True,
"PolicyCompletionAppliedToFrozenModel"->False,
"NewCandidateSelected"->False,
"S76BlindTestRun"->False
|>;

Dataset[{cert75C}]
