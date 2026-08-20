BeginPackage["S125CRunner`"];
Begin["`Private`"];
ClearAll["Global`*"];
$HistoryLength=0;
Print["============================================================"];
Print["TCCT S125-C PILOT MULTI-RESTART MATCHED-TRANSFORMER COMPARISON"];
Print["LOCKED TCCT + 3-SEED MATCHED REASONER + 4X STRONG REASONER -> 5 FRESH WORLDS"];
Print["============================================================"];
S125BStop[msg_]:=(Print["FATAL: ",msg];Throw[$Failed,"S125BFatal"]);
Catch[
s125RunnerDirectory=If[
StringQ[$InputFileName]&&StringLength[$InputFileName]>0,
DirectoryName[ExpandFileName[$InputFileName]],
Directory[]
];
s125BaseWLName="TCCT_S124_T5R1_StrictFreshWorldGeneralizationAttribution.wl";
s125BaseNotebookName="TCCT_S124_T5R1_StrictFreshWorldGeneralizationAttribution.ipynb";
s125ConfiguredSource=Quiet@Check[Environment["S125_T5R1_SOURCE"],Missing[]];
s125BaseCandidates=DeleteDuplicates@Select[
{
s125ConfiguredSource,
FileNameJoin[{s125RunnerDirectory,s125BaseWLName}],
FileNameJoin[{s125RunnerDirectory,s125BaseNotebookName}],
FileNameJoin[{Directory[],s125BaseWLName}],
FileNameJoin[{Directory[],s125BaseNotebookName}]
},
StringQ[#]&&FileExistsQ[#]&
];
If[
s125BaseCandidates==={},
S125BStop["canonical T5R1 .wl/.ipynb not found; set S125_T5R1_SOURCE or place the runner beside it"]
];
s125BaseFile=First[s125BaseCandidates];
s125RequestedExecutionMode=Quiet@Check[Environment["S125_EXECUTION_MODE"],Missing[]];
s125ExecutionMode=If[s125RequestedExecutionMode==="JupyterKernel","JupyterKernel","ExternalKernel"];
s125PreflightOnly=Quiet@Check[Environment["S125C_PREFLIGHT_ONLY"],""]==="True";
s125OutputFolderName=If[
s125ExecutionMode==="JupyterKernel",
"S125C_Jupyter_Pilot5_MultiRestartMatched_Output",
"S125C_Pilot5_MultiRestartMatched_Output"
];
s125OutputRoot=FileNameJoin[{DirectoryName[s125BaseFile],s125OutputFolderName}];
s125WorldSeeds=Range[1258501,1258505];
s125RequiredPassRate=1.00;
s125CanonicalSeedPattern=RegularExpression["hiddenBenchmarkSeedS119B\\s*=\\s*1245501\\s*;"];
s125CanonicalOutputPattern=RegularExpression["t5sOutputDirectory\\s*=\\s*FileNameJoin\\[\\{Directory\\[\\],\\s*\"S124_T5R1_Output\"\\}\\]\\s*;"];
s125FixedCellGatePattern=RegularExpression["If\\[\\s*Length\\[conditionalTransitionsS119B\\]\\s*=!=\\s*42,\\s*T5SStop\\[\"expected 42 sparse conditional transition cells\"\\]\\s*\\];"];
s125FixedCellFinalPassPattern=RegularExpression["Length\\[conditionalTransitionsS119B\\]\\s*===\\s*42"];
s125JupyterStopLiteral="T5SStop[msg_]:=(Print[\"FATAL: \",msg];Abort[]);";
s125StrongConfigMarker="t5sReasonFinalSeed=1245703;";
s125MatchedTrainingStartMarker="SeedRandom[t5sReasonSelectSeed];";
s125MatchedTrainingEndMarker=StringRiffle[{"T5SStop[\"final reasoner failed training competence gate\"]","];"},"\n"];
s125StrongSpecMarker="t5sPerceptionSpec=<|";
s125ProtocolHashLiteral="{discoveryPolicySpecS119B,t5sReasonSpec,t5sPerceptionSpec,t5sWinnerMargin}";
s125StrongTrainingMarker="t5sHighOrderMaxSequenceLength=";
s125GlobalFreezeHashMarker=StringRiffle[{"t5sReasonMaxSeqLen","},","\"SHA256\""},"\n"];
s125FreezePrintMarker="Print[\"NeuralReasonerFrozen=True\"];";
s125Phase6Marker="Print[\"PHASE 6: FIRST OPENING OF FRESH HIGH-ORDER HOLDOUT\"];";
s125CompleteMarker=StringRiffle[{"Print[\"S124-T5R1 COMPLETE\"];","Print[\"============================================================\"];"},"\n"];
s125RequiredMarkers={
"S124-T5R1 STRICT FRESH-WORLD",
"MaximumTrainingInteractionOrder\"->2",
"t5sReasonValidationBalancedGate=0.60",
"t5sReasonTrainingBalancedGate=0.70",
"t5sWinnerMargin=0.02"
};
s125BaseKind=ToLowerCase[FileExtension[s125BaseFile]];
S125NotebookCode[file_String]:=
Module[{json,cells,codeCells,parts},
json=Quiet@Check[Import[file,"RawJSON"],$Failed];
If[!AssociationQ[json],Return[$Failed]];
cells=Lookup[json,"cells",{}];
If[!ListQ[cells],Return[$Failed]];
codeCells=Select[
cells,
AssociationQ[#]&&Lookup[#,"cell_type",""]==="code"&
];
parts=Table[
With[{source=Lookup[cell,"source",{}]},
Which[
StringQ[source],source,
ListQ[source]&&AllTrue[source,StringQ],StringJoin[source],
True,""
]
],
{cell,codeCells}
];
parts=Select[parts,StringLength[StringTrim[#]]>0&];
If[parts==={},$Failed,StringRiffle[parts,"\n\n"]]
];
s125BaseContainerHash=FileHash[s125BaseFile,"SHA256","HexString"];
s125BaseText=Switch[
s125BaseKind,
"wl"|"wls",Import[s125BaseFile,"Text",CharacterEncoding->"UTF-8"],
"ipynb",S125NotebookCode[s125BaseFile],
_,S125BStop["canonical T5R1 source must be .wl, .wls, or .ipynb"]
];
If[!StringQ[s125BaseText],S125BStop["could not read canonical T5R1 source"]];
If[!And@@(StringContainsQ[s125BaseText,#]&/@s125RequiredMarkers),S125BStop["canonical T5R1 source markers do not match"]];
If[Length[StringCases[s125BaseText,s125CanonicalSeedPattern]]=!=1,S125BStop["expected exactly one canonical fresh-world seed assignment"]];
If[Length[StringCases[s125BaseText,s125CanonicalOutputPattern]]=!=1,S125BStop["expected exactly one canonical T5R1 output-directory assignment"]];
If[Length[StringCases[s125BaseText,s125FixedCellGatePattern]]=!=1,S125BStop["expected exactly one fixed 42-cell audit gate"]];
If[Length[StringCases[s125BaseText,s125FixedCellFinalPassPattern]]=!=1,S125BStop["expected exactly one fixed 42-cell final-pass gate"]];
If[s125ExecutionMode==="JupyterKernel"&&StringCount[s125BaseText,s125JupyterStopLiteral]=!=1,S125BStop["expected exactly one Jupyter stop definition"]];
If[StringCount[s125BaseText,#]=!=1,S125BStop["expected exactly one strong-baseline injection marker: "<>#]]&/@
{s125StrongConfigMarker,s125StrongSpecMarker,s125ProtocolHashLiteral,s125StrongTrainingMarker,s125GlobalFreezeHashMarker,s125FreezePrintMarker,s125Phase6Marker,s125CompleteMarker};
If[StringCount[s125BaseText,s125MatchedTrainingStartMarker]=!=1,S125BStop["expected exactly one matched-training start marker"]];
If[StringCount[s125BaseText,s125MatchedTrainingEndMarker]=!=1,S125BStop["expected exactly one matched-training end marker"]];
If[Length[DeleteDuplicates[s125WorldSeeds]]=!=Length[s125WorldSeeds],S125BStop["world seed list contains duplicates"]];
If[Length[s125WorldSeeds]=!=5,S125BStop["S125-C pilot requires exactly 5 preregistered worlds"]];
If[!DirectoryQ[s125OutputRoot],CreateDirectory[s125OutputRoot]];
s125BaseSourceHash=Hash[s125BaseText,"SHA256","HexString"];
S125CReplaceMatchedTraining[text_String]:=Module[{startPosition,endPosition},
startPosition=First@StringPosition[text,s125MatchedTrainingStartMarker];
endPosition=First@StringPosition[text,s125MatchedTrainingEndMarker];
If[startPosition[[1]]>=endPosition[[1]],S125BStop["matched-training marker order is invalid"]];
StringTake[text,startPosition[[1]]-1]<>s125MatchedTrainingInjection<>StringDrop[text,endPosition[[2]]]
];
s125ManifestCore=<|
"Stage"->"S125-C-Pilot5",
"Protocol"->"MultiRestartMatchedAndStrongTransformerComparison",
"ProtocolRevision"->"C1-ThreeSeedMatchedSelectionBeforeHighOrder",
"BaseSourceFile"->FileNameTake[s125BaseFile],
"BaseSourceKind"->s125BaseKind,
"BaseContainerSHA256"->s125BaseContainerHash,
"BaseSourceSHA256"->s125BaseSourceHash,
"CanonicalT5R1WorldSeed"->1245501,
"PreregisteredWorldSeeds"->s125WorldSeeds,
"WorldCount"->Length[s125WorldSeeds],
"RequiredPassRate"->s125RequiredPassRate,
"OnlyPermittedSourceChanges"->{"hiddenBenchmarkSeedS119B","t5sOutputDirectory","S125-C provenance prints","both fixed 42-cell gates -> structure-derived completeness audit","Abort -> tagged Throw in Jupyter mode","pre-world three-seed matched-reasoner and strong-reasoner specifications in protocol hash","canonical single-seed matched training -> preregistered three-seed low-order-only selection","strong-reasoner training and freeze before high-order","strong-reasoner prospective evaluation and pilot summary after opening"},
"LockedTrainingOrder"->2,
"LockedHighOrderDefinition"->">=3 nonzero factors",
"LockedPerceptionGate"->0.98,
"LockedReasonValidationBalancedGate"->0.60,
"LockedReasonTrainingBalancedGate"->0.70,
"LockedWinnerMargin"->0.02,
"MatchedRestartSpec"-><|"SelectionSeeds"->{1258611,1258612,1258613},"FinalSeeds"->{1258621,1258622,1258623},"SelectionMetric"->"LowOrderValidationBalancedAccuracy","FinalMetric"->"LowOrderTrainingBalancedAccuracy","HighOrderUsedForSelection"->False,"ArchitectureChanged"->False|>,
"StrongReasonerSpec"-><|"DModel"->96,"Heads"->4,"Layers"->3,"FF"->384,"Dropout"->0.10,"LearningRate"->0.0003,"BatchSize"->64,"Rounds"->35,"Patience"->6,"ValidationBalancedGate"->0.60,"TrainingBalancedGate"->0.70,"SelectSeed"->1258102,"FinalSeed"->1258103|>,
"PilotOutcomeDoesNotControlProtocolPass"->True,
"ExecutionMode"->If[
s125ExecutionMode==="JupyterKernel",
"Activated Jupyter kernel with Global context reset before every world",
"One fresh external Wolfram kernel per world"
]
|>;
s125ManifestHash=Hash[s125ManifestCore,"SHA256","HexString"];
s125Manifest=Join[s125ManifestCore,<|
"ManifestSHA256"->s125ManifestHash,
"FrozenBeforeFirstWorld"->True,
"CreatedAt"->DateString[{"ISODate"," ","Time"," ","TimeZone"}]
|>];
s125ManifestFile=FileNameJoin[{s125OutputRoot,"S125C_pilot_preregistered_manifest.wl"}];
s125ManifestJSONFile=FileNameJoin[{s125OutputRoot,"S125C_pilot_preregistered_manifest.json"}];
If[
FileExistsQ[s125ManifestFile],
s125ExistingManifest=Quiet@Check[Get[s125ManifestFile],$Failed];
If[
!AssociationQ[s125ExistingManifest]||
Lookup[s125ExistingManifest,"ManifestSHA256",Missing[]]=!=s125ManifestHash,
S125BStop["existing output root belongs to a different manifest; use a new output directory"]
],
Put[s125Manifest,s125ManifestFile];
Export[s125ManifestJSONFile,s125Manifest,"RawJSON"]
];
Print["BaseSource=",s125BaseFile];
Print["BaseSourceKind=",s125BaseKind];
Print["BaseContainerSHA256=",s125BaseContainerHash];
Print["BaseSourceSHA256=",s125BaseSourceHash];
Print["ManifestSHA256=",s125ManifestHash];
Print["PreregisteredWorldSeeds=",s125WorldSeeds];
Print["WorldCount=",Length[s125WorldSeeds]];
Print["RequiredPassRate=",s125RequiredPassRate];
Print["MANIFEST FROZEN BEFORE FIRST WORLD=True"];
s125DirectKernelCandidates=DeleteDuplicates@Select[
{
Quiet@Check[FindExecutable["WolframKernel"],Missing[]],
Quiet@Check[FindExecutable["MathKernel"],Missing[]],
Quiet@Check[FileNameJoin[{$InstallationDirectory,"WolframKernel.exe"}],Missing[]],
Quiet@Check[FileNameJoin[{$InstallationDirectory,"MathKernel.exe"}],Missing[]],
Quiet@Check[FileNameJoin[{$InstallationDirectory,"Executables","WolframKernel.exe"}],Missing[]],
Quiet@Check[FileNameJoin[{$InstallationDirectory,"Executables","MathKernel.exe"}],Missing[]]
},
StringQ[#]&&FileExistsQ[#]&
];
s125WolframScript=Quiet@Check[FindExecutable["wolframscript"],Missing[]];
If[
s125ExecutionMode==="ExternalKernel",
Which[
Length[s125DirectKernelCandidates]>0,
s125KernelExecutable=First[s125DirectKernelCandidates];
s125KernelMode="DirectKernel";
S125KernelCommand[file_String]:={s125KernelExecutable,"-script",file,"-noicon"},
StringQ[s125WolframScript]&&FileExistsQ[s125WolframScript],
s125KernelExecutable=s125WolframScript;
s125KernelMode="WolframScript";
S125KernelCommand[file_String]:={s125KernelExecutable,"-file",file},
True,
S125BStop["no external Wolfram kernel executable was found"]
],
s125KernelExecutable="CURRENT_JUPYTER_KERNEL";
s125KernelMode="CurrentActivatedJupyterKernel"
];
Print["ExternalKernelMode=",s125KernelMode];
Print["ExternalKernelExecutable=",s125KernelExecutable];
s125StrongConfigInjection=StringRiffle[
{
"t5cMatchedSelectionSeeds={1258611,1258612,1258613};",
"t5cMatchedFinalSeeds={1258621,1258622,1258623};",
"If[Length[t5cMatchedSelectionSeeds]=!=3||Length[DeleteDuplicates[t5cMatchedSelectionSeeds]]=!=3,T5SStop[\"matched selection seed preregistration audit failed\"]];",
"If[Length[t5cMatchedFinalSeeds]=!=3||Length[DeleteDuplicates[t5cMatchedFinalSeeds]]=!=3,T5SStop[\"matched final seed preregistration audit failed\"]];",
"t5bStrongReasonDModel=96;",
"t5bStrongReasonHeads=4;",
"t5bStrongReasonLayers=3;",
"t5bStrongReasonFF=384;",
"t5bStrongReasonDropout=0.10;",
"t5bStrongReasonLR=0.0003;",
"t5bStrongReasonBatch=64;",
"t5bStrongReasonRounds=35;",
"t5bStrongReasonPatience=6;",
"t5bStrongReasonSelectSeed=1258102;",
"t5bStrongReasonFinalSeed=1258103;",
"t5bStrongReasonValidationBalancedGate=0.60;",
"t5bStrongReasonTrainingBalancedGate=0.70;",
"If[Mod[t5bStrongReasonDModel,t5bStrongReasonHeads]=!=0,T5SStop[\"strong reason dModel/head mismatch\"]];"
},
"\n"
];
s125StrongSpecInjection=StringRiffle[
{
"t5cMatchedRestartSpec=<|",
"\"SelectionSeeds\"->t5cMatchedSelectionSeeds,",
"\"FinalSeeds\"->t5cMatchedFinalSeeds,",
"\"SelectionMetric\"->\"LowOrderValidationBalancedAccuracy\",",
"\"FinalMetric\"->\"LowOrderTrainingBalancedAccuracy\",",
"\"ValidationBalancedGate\"->t5sReasonValidationBalancedGate,",
"\"TrainingBalancedGate\"->t5sReasonTrainingBalancedGate,",
"\"HighOrderUsedForSelection\"->False,",
"\"ArchitectureChanged\"->False",
"|>;",
"t5bStrongReasonSpec=<|",
"\"DModel\"->t5bStrongReasonDModel,",
"\"Heads\"->t5bStrongReasonHeads,",
"\"Layers\"->t5bStrongReasonLayers,",
"\"FF\"->t5bStrongReasonFF,",
"\"Dropout\"->t5bStrongReasonDropout,",
"\"LearningRate\"->t5bStrongReasonLR,",
"\"BatchSize\"->t5bStrongReasonBatch,",
"\"Rounds\"->t5bStrongReasonRounds,",
"\"Patience\"->t5bStrongReasonPatience,",
"\"ValidationBalancedGate\"->t5bStrongReasonValidationBalancedGate,",
"\"TrainingBalancedGate\"->t5bStrongReasonTrainingBalancedGate,",
"\"SelectSeed\"->t5bStrongReasonSelectSeed,",
"\"FinalSeed\"->t5bStrongReasonFinalSeed,",
"\"ComparisonRole\"->\"Approximately4xMatchedTransformerReasoner\"",
"|>;"
},
"\n"
];
s125MatchedTrainingInjection=StringRiffle[
{
"Print[\"============================================================\"];",
"Print[\"PHASE 5C: PREREGISTERED 3-SEED MATCHED REASONER SELECTION\"];",
"Print[\"SELECTION AND FINAL CHOICE USE LOW-ORDER DATA ONLY\"];",
"Print[\"HIGH-ORDER OUTPUTS REMAIN SEALED\"];",
"Print[\"============================================================\"];",
"t5cMatchedSelectionRecords=Table[Module[{net0,training,net,pred,acc,bal},",
"SeedRandom[seed];",
"net0=NetInitialize[T5SReasonNet[]];",
"training=NetTrain[net0,t5sReasonTrainRules,All,ValidationSet->t5sReasonValRules,MaxTrainingRounds->t5sReasonRounds,BatchSize->t5sReasonBatch,LearningRate->t5sReasonLR,Method->\"ADAM\",TrainingProgressMeasurements->{\"Accuracy\",\"ErrorRate\"},TrainingStoppingCriterion-><|\"Criterion\"->\"Loss\",\"Patience\"->t5sReasonPatience|>,TrainingProgressReporting->\"Print\",TargetDevice->t5sTargetDevice,RandomSeeding->seed];",
"net=training[\"TrainedNet\"];",
"pred=T5SPredictBatched[net,t5sReasonValInputs,128];",
"If[Length[pred]=!=Length[t5sReasonValLabels]||!And@@(MemberQ[{0,1},#]&/@pred),T5SStop[\"multi-restart reason validation prediction audit failed\"]];",
"acc=N[Mean[MapThread[Boole[SameQ[#1,#2]]&,{pred,t5sReasonValLabels}]]];",
"bal=T5SBalancedAccuracy[t5sReasonValLabels,pred];",
"<|\"Seed\"->seed,\"Net\"->net,\"ValidationAccuracy\"->acc,\"ValidationBalancedAccuracy\"->bal|>],{seed,t5cMatchedSelectionSeeds}];",
"t5cMatchedSelectionCandidateMetrics=KeyDrop[#,\"Net\"]&/@t5cMatchedSelectionRecords;",
"Print[\"MatchedSelectionCandidateMetrics=\",t5cMatchedSelectionCandidateMetrics];",
"t5cMatchedValidSelectionRecords=Select[t5cMatchedSelectionRecords,Function[record,NumericQ[Lookup[record,\"ValidationBalancedAccuracy\"]]&&Lookup[record,\"ValidationBalancedAccuracy\"]>=t5sReasonValidationBalancedGate]];",
"If[t5cMatchedValidSelectionRecords==={},T5SStop[\"all preregistered matched reasoners failed validation competence gate\"]];",
"t5cMatchedSelectedSelectionRecord=First@SortBy[t5cMatchedValidSelectionRecords,Function[record,{-Lookup[record,\"ValidationBalancedAccuracy\"],Lookup[record,\"Seed\"]}]];",
"t5cMatchedSelectedSelectionSeed=Lookup[t5cMatchedSelectedSelectionRecord,\"Seed\"];",
"t5sReasonSelectionNet=Lookup[t5cMatchedSelectedSelectionRecord,\"Net\"];",
"t5sReasonValPred=T5SPredictBatched[t5sReasonSelectionNet,t5sReasonValInputs,128];",
"t5sReasonValidationAccuracy=N[Mean[MapThread[Boole[SameQ[#1,#2]]&,{t5sReasonValPred,t5sReasonValLabels}]]];",
"t5sReasonValidationZeroAccuracy=T5SClassAccuracy[t5sReasonValLabels,t5sReasonValPred,0];",
"t5sReasonValidationOneAccuracy=T5SClassAccuracy[t5sReasonValLabels,t5sReasonValPred,1];",
"t5sReasonValidationBalancedAccuracy=T5SBalancedAccuracy[t5sReasonValLabels,t5sReasonValPred];",
"Print[\"MatchedSelectedSelectionSeed=\",t5cMatchedSelectedSelectionSeed];",
"Print[\"ReasonValidationAccuracy=\",t5sReasonValidationAccuracy];",
"Print[\"ReasonValidationZeroAccuracy=\",t5sReasonValidationZeroAccuracy];",
"Print[\"ReasonValidationOneAccuracy=\",t5sReasonValidationOneAccuracy];",
"Print[\"ReasonValidationBalancedAccuracy=\",t5sReasonValidationBalancedAccuracy];",
"t5sReasonAllInputs=T5SReasonInputs[t5sMembershipRows];",
"t5sReasonAllLabels=T5SReasonLabels[t5sMembershipRows];",
"t5sReasonAllRules=MapThread[Rule,{t5sReasonAllInputs,t5sReasonAllLabels}];",
"t5cMatchedFinalRecords=Table[Module[{net0,training,net,pred,acc,bal},",
"SeedRandom[seed];",
"net0=NetInitialize[T5SReasonNet[]];",
"training=NetTrain[net0,t5sReasonAllRules,All,MaxTrainingRounds->t5sReasonRounds,BatchSize->t5sReasonBatch,LearningRate->t5sReasonLR,Method->\"ADAM\",TrainingProgressMeasurements->{\"Accuracy\",\"ErrorRate\"},TrainingProgressReporting->\"Print\",TargetDevice->t5sTargetDevice,RandomSeeding->seed];",
"net=training[\"TrainedNet\"];",
"pred=T5SPredictBatched[net,t5sReasonAllInputs,128];",
"If[Length[pred]=!=Length[t5sReasonAllLabels]||!And@@(MemberQ[{0,1},#]&/@pred),T5SStop[\"multi-restart final reason prediction audit failed\"]];",
"acc=N[Mean[MapThread[Boole[SameQ[#1,#2]]&,{pred,t5sReasonAllLabels}]]];",
"bal=T5SBalancedAccuracy[t5sReasonAllLabels,pred];",
"<|\"Seed\"->seed,\"Net\"->net,\"TrainingAccuracy\"->acc,\"TrainingBalancedAccuracy\"->bal|>],{seed,t5cMatchedFinalSeeds}];",
"t5cMatchedFinalCandidateMetrics=KeyDrop[#,\"Net\"]&/@t5cMatchedFinalRecords;",
"Print[\"MatchedFinalCandidateMetrics=\",t5cMatchedFinalCandidateMetrics];",
"t5cMatchedValidFinalRecords=Select[t5cMatchedFinalRecords,Function[record,NumericQ[Lookup[record,\"TrainingBalancedAccuracy\"]]&&Lookup[record,\"TrainingBalancedAccuracy\"]>=t5sReasonTrainingBalancedGate]];",
"If[t5cMatchedValidFinalRecords==={},T5SStop[\"all preregistered matched final reasoners failed training competence gate\"]];",
"t5cMatchedSelectedFinalRecord=First@SortBy[t5cMatchedValidFinalRecords,Function[record,{-Lookup[record,\"TrainingBalancedAccuracy\"],Lookup[record,\"Seed\"]}]];",
"t5cMatchedSelectedFinalSeed=Lookup[t5cMatchedSelectedFinalRecord,\"Seed\"];",
"t5sFrozenReasoner=Lookup[t5cMatchedSelectedFinalRecord,\"Net\"];",
"t5sReasonTrainPred=T5SPredictBatched[t5sFrozenReasoner,t5sReasonAllInputs,128];",
"t5sReasonTrainingAccuracy=N[Mean[MapThread[Boole[SameQ[#1,#2]]&,{t5sReasonTrainPred,t5sReasonAllLabels}]]];",
"t5sReasonTrainingBalancedAccuracy=T5SBalancedAccuracy[t5sReasonAllLabels,t5sReasonTrainPred];",
"Print[\"MatchedSelectedFinalSeed=\",t5cMatchedSelectedFinalSeed];",
"Print[\"FinalReasonTrainingAccuracy=\",t5sReasonTrainingAccuracy];",
"Print[\"FinalReasonTrainingBalancedAccuracy=\",t5sReasonTrainingBalancedAccuracy];",
"If[!NumericQ[t5sReasonTrainingBalancedAccuracy]||t5sReasonTrainingBalancedAccuracy<t5sReasonTrainingBalancedGate,T5SStop[\"selected matched final reasoner failed training competence gate\"]];",
"Clear[t5cMatchedSelectionRecords,t5cMatchedValidSelectionRecords,t5cMatchedSelectedSelectionRecord,t5cMatchedFinalRecords,t5cMatchedValidFinalRecords,t5cMatchedSelectedFinalRecord];"
},
"\n"
];
s125StrongTrainingInjection=StringRiffle[
{
"Print[\"============================================================\"];",
"Print[\"PHASE 5B: STRONG TRANSFORMER REASONER TRAINING\"];",
"Print[\"HIGH-ORDER OUTPUTS REMAIN SEALED\"];",
"Print[\"============================================================\"];",
"T5BStrongReasonNet[]:=Module[{blocks},",
"blocks=Table[T5SReasonBlock[t5bStrongReasonDModel,t5bStrongReasonHeads,t5bStrongReasonFF,t5bStrongReasonDropout],{t5bStrongReasonLayers}];",
"NetChain[Join[{NetMapOperator[LinearLayer[t5bStrongReasonDModel]]},blocks,{NormalizationLayer[2,\"Same\"],SequenceLastLayer[],LinearLayer[2],SoftmaxLayer[]}],\"Input\"->{\"Varying\",t5sReasonInputDim},\"Output\"->NetDecoder[{\"Class\",{0,1}}]]",
"];",
"SeedRandom[t5bStrongReasonSelectSeed];",
"t5bStrongReasonSelectNet0=NetInitialize[T5BStrongReasonNet[]];",
"t5bStrongReasonSelection=NetTrain[t5bStrongReasonSelectNet0,t5sReasonTrainRules,All,ValidationSet->t5sReasonValRules,MaxTrainingRounds->t5bStrongReasonRounds,BatchSize->t5bStrongReasonBatch,LearningRate->t5bStrongReasonLR,Method->\"ADAM\",TrainingProgressMeasurements->{\"Accuracy\",\"ErrorRate\"},TrainingStoppingCriterion-><|\"Criterion\"->\"Loss\",\"Patience\"->t5bStrongReasonPatience|>,TrainingProgressReporting->\"Print\",TargetDevice->t5sTargetDevice,RandomSeeding->t5bStrongReasonSelectSeed];",
"t5bStrongReasonSelectionNet=t5bStrongReasonSelection[\"TrainedNet\"];",
"t5bStrongReasonValPred=T5SPredictBatched[t5bStrongReasonSelectionNet,t5sReasonValInputs,128];",
"If[Length[t5bStrongReasonValPred]=!=Length[t5sReasonValLabels]||!And@@(MemberQ[{0,1},#]&/@t5bStrongReasonValPred),T5SStop[\"strong reason validation prediction audit failed\"]];",
"t5bStrongReasonValidationAccuracy=N[Mean[MapThread[Boole[SameQ[#1,#2]]&,{t5bStrongReasonValPred,t5sReasonValLabels}]]];",
"t5bStrongReasonValidationBalancedAccuracy=T5SBalancedAccuracy[t5sReasonValLabels,t5bStrongReasonValPred];",
"Print[\"StrongReasonValidationAccuracy=\",t5bStrongReasonValidationAccuracy];",
"Print[\"StrongReasonValidationBalancedAccuracy=\",t5bStrongReasonValidationBalancedAccuracy];",
"If[!NumericQ[t5bStrongReasonValidationBalancedAccuracy]||t5bStrongReasonValidationBalancedAccuracy<t5bStrongReasonValidationBalancedGate,T5SStop[\"strong reasoner failed validation competence gate\"]];",
"SeedRandom[t5bStrongReasonFinalSeed];",
"t5bStrongReasonFinalNet0=NetInitialize[T5BStrongReasonNet[]];",
"t5bStrongReasonFinalTraining=NetTrain[t5bStrongReasonFinalNet0,t5sReasonAllRules,All,MaxTrainingRounds->t5bStrongReasonRounds,BatchSize->t5bStrongReasonBatch,LearningRate->t5bStrongReasonLR,Method->\"ADAM\",TrainingProgressMeasurements->{\"Accuracy\",\"ErrorRate\"},TrainingProgressReporting->\"Print\",TargetDevice->t5sTargetDevice,RandomSeeding->t5bStrongReasonFinalSeed];",
"t5bFrozenStrongReasoner=t5bStrongReasonFinalTraining[\"TrainedNet\"];",
"t5bStrongReasonTrainPred=T5SPredictBatched[t5bFrozenStrongReasoner,t5sReasonAllInputs,128];",
"If[!And@@(MemberQ[{0,1},#]&/@t5bStrongReasonTrainPred),T5SStop[\"strong final reasoner produced invalid training prediction\"]];",
"t5bStrongReasonTrainingAccuracy=N[Mean[MapThread[Boole[SameQ[#1,#2]]&,{t5bStrongReasonTrainPred,t5sReasonAllLabels}]]];",
"t5bStrongReasonTrainingBalancedAccuracy=T5SBalancedAccuracy[t5sReasonAllLabels,t5bStrongReasonTrainPred];",
"Print[\"StrongFinalReasonTrainingAccuracy=\",t5bStrongReasonTrainingAccuracy];",
"Print[\"StrongFinalReasonTrainingBalancedAccuracy=\",t5bStrongReasonTrainingBalancedAccuracy];",
"If[!NumericQ[t5bStrongReasonTrainingBalancedAccuracy]||t5bStrongReasonTrainingBalancedAccuracy<t5bStrongReasonTrainingBalancedGate,T5SStop[\"strong final reasoner failed training competence gate\"]];",
"t5bMatchedReasonParameterCount=Total[Times@@#&/@Values[Map[Dimensions,Quiet@NetInformation[t5sFrozenReasoner,\"Arrays\"]]]];",
"t5bStrongReasonParameterCount=Total[Times@@#&/@Values[Map[Dimensions,Quiet@NetInformation[t5bFrozenStrongReasoner,\"Arrays\"]]]];",
"If[!IntegerQ[t5bStrongReasonParameterCount]||t5bStrongReasonParameterCount<=3*t5bMatchedReasonParameterCount,T5SStop[\"strong reasoner parameter-scale audit failed\"]];",
"Print[\"MatchedReasonParameterCount=\",t5bMatchedReasonParameterCount];",
"Print[\"StrongReasonParameterCount=\",t5bStrongReasonParameterCount];",
"t5bStrongReasonFreezeFile=FileNameJoin[{t5sOutputDirectory,\"S125C_STRONG_NEURAL_REASONER_FROZEN_BEFORE_HIGHORDER.wlnet\"}];",
"Export[t5bStrongReasonFreezeFile,t5bFrozenStrongReasoner];",
"t5bStrongReasonFreezeFileHash=FileHash[t5bStrongReasonFreezeFile,\"SHA256\",\"HexString\"];",
"Print[\"StrongReasonFreezeFileHash=\",t5bStrongReasonFreezeFileHash];",
"Clear[t5bStrongReasonSelection,t5bStrongReasonSelectNet0,t5bStrongReasonSelectionNet,t5bStrongReasonFinalTraining,t5bStrongReasonFinalNet0,t5bStrongReasonValPred,t5bStrongReasonTrainPred];"
},
"\n"
];
s125StrongSignatureInjection=StringRiffle[
{
"T5BStrongNeuralSignature[seq_List]:=Module[{inputs,pred},",
"inputs=Table[T5SReasonInput[seq,probe],{probe,publicProbesS119B}];",
"pred=T5SPredictBatched[t5bFrozenStrongReasoner,inputs,14];",
"If[Length[pred]=!=14||!And@@(MemberQ[{0,1},#]&/@pred),T5SStop[\"invalid strong-neural prospective signature\"]];",
"pred",
"];"
},
"\n"
];
s125StrongEvaluationInjection=StringRiffle[
{
"Print[\"============================================================\"];",
"Print[\"S125-C PILOT: MULTI-RESTART MATCHED + STRONG REASONER EVALUATION\"];",
"Print[\"NO MODEL CHANGES; ALL MODELS WERE FROZEN BEFORE HIGH-ORDER OPENING\"];",
"Print[\"============================================================\"];",
"t5bStrongHighOrderSignatures=T5BStrongNeuralSignature/@Lookup[prospectiveHighOrderHoldoutS119B,\"Sequence\"];",
"t5bStrongTrueHighOrderSignatures=Lookup[t5sHighOrderRows,\"TrueSignature\"];",
"If[Length[t5bStrongHighOrderSignatures]=!=Length[t5sHighOrderRows],T5SStop[\"strong state signature count mismatch\"]];",
"t5bStrongExactCount=Total[MapThread[Boole[SameQ[#1,#2]]&,{t5bStrongHighOrderSignatures,t5bStrongTrueHighOrderSignatures}]];",
"t5bStrongExactAccuracy=N[t5bStrongExactCount/Length[t5sHighOrderRows]];",
"t5bStrongProbeFlat=Flatten[t5bStrongHighOrderSignatures];",
"t5bStrongProbeAccuracy=N[Mean[MapThread[Boole[SameQ[#1,#2]]&,{t5bStrongProbeFlat,t5sTrueProbeFlat}]]];",
"t5bStrongProbeZeroAccuracy=T5SClassAccuracy[t5sTrueProbeFlat,t5bStrongProbeFlat,0];",
"t5bStrongProbeOneAccuracy=T5SClassAccuracy[t5sTrueProbeFlat,t5bStrongProbeFlat,1];",
"t5bStrongProbeBalancedAccuracy=T5SBalancedAccuracy[t5sTrueProbeFlat,t5bStrongProbeFlat];",
"t5bStrongTransitionSignatures=Flatten[Table[T5BStrongNeuralSignature[Append[row[\"Sequence\"],action]],{row,prospectiveHighOrderHoldoutS119B},{action,publicActionsS119B}],1];",
"t5bStrongTrueTransitionSignatures=Lookup[t5sHighOrderTransitionRows,\"TrueSignature\"];",
"If[Length[t5bStrongTransitionSignatures]=!=Length[t5sHighOrderTransitionRows],T5SStop[\"strong transition signature count mismatch\"]];",
"t5bStrongTransitionExactCount=Total[MapThread[Boole[SameQ[#1,#2]]&,{t5bStrongTransitionSignatures,t5bStrongTrueTransitionSignatures}]];",
"t5bStrongTransitionExactAccuracy=N[t5bStrongTransitionExactCount/Length[t5sHighOrderTransitionRows]];",
"t5bStrongTransitionFlat=Flatten[t5bStrongTransitionSignatures];",
"t5bStrongTransitionProbeAccuracy=N[Mean[MapThread[Boole[SameQ[#1,#2]]&,{t5bStrongTransitionFlat,t5sTransitionTrueFlat}]]];",
"t5bStrongTransitionZeroAccuracy=T5SClassAccuracy[t5sTransitionTrueFlat,t5bStrongTransitionFlat,0];",
"t5bStrongTransitionOneAccuracy=T5SClassAccuracy[t5sTransitionTrueFlat,t5bStrongTransitionFlat,1];",
"t5bStrongTransitionBalancedAccuracy=T5SBalancedAccuracy[t5sTransitionTrueFlat,t5bStrongTransitionFlat];",
"t5bBestNeuralStateExactAccuracy=Max[t5sNeuralExactAccuracy,t5bStrongExactAccuracy];",
"t5bBestNeuralTransitionExactAccuracy=Max[t5sNeuralTransitionExactAccuracy,t5bStrongTransitionExactAccuracy];",
"t5bTCCTMinusBestNeuralStateExact=N[t5sTCCTExactAccuracy-t5bBestNeuralStateExactAccuracy];",
"t5bTCCTMinusBestNeuralTransitionExact=N[t5sTCCTTransitionExactAccuracy-t5bBestNeuralTransitionExactAccuracy];",
"t5bPilotProtocolPass=And[TrueQ[t5sStrictProtocolPass],Length[t5cMatchedSelectionCandidateMetrics]===3,Length[t5cMatchedFinalCandidateMetrics]===3,MemberQ[t5cMatchedSelectionSeeds,t5cMatchedSelectedSelectionSeed],MemberQ[t5cMatchedFinalSeeds,t5cMatchedSelectedFinalSeed],NumericQ[t5bStrongReasonValidationBalancedAccuracy],t5bStrongReasonValidationBalancedAccuracy>=t5bStrongReasonValidationBalancedGate,NumericQ[t5bStrongReasonTrainingBalancedAccuracy],t5bStrongReasonTrainingBalancedAccuracy>=t5bStrongReasonTrainingBalancedGate,IntegerQ[t5bStrongReasonParameterCount],t5bStrongReasonParameterCount>3*t5bMatchedReasonParameterCount,StringQ[t5bStrongReasonFreezeFileHash],StringLength[t5bStrongReasonFreezeFileHash]>=32,Length[t5bStrongHighOrderSignatures]===74,Length[t5bStrongTransitionSignatures]===592];",
"t5bPilotOutcome=Which[!TrueQ[t5bPilotProtocolPass],\"PILOT_PROTOCOL_GATE_FAILED\",t5bTCCTMinusBestNeuralStateExact>=t5sWinnerMargin&&t5bTCCTMinusBestNeuralTransitionExact>=t5sWinnerMargin,\"TCCT_ADVANTAGE_OVER_BEST_NEURAL_BASELINE\",t5bTCCTMinusBestNeuralStateExact<=-t5sWinnerMargin&&t5bTCCTMinusBestNeuralTransitionExact<=-t5sWinnerMargin,\"BEST_NEURAL_BASELINE_ADVANTAGE\",True,\"PARITY_OR_MIXED_RESULT\"];",
"Print[\"StrongHighOrderExact=\",t5bStrongExactCount,\"/\",Length[t5sHighOrderRows]];",
"Print[\"StrongHighOrderExactAccuracy=\",t5bStrongExactAccuracy];",
"Print[\"StrongProbeAccuracy=\",t5bStrongProbeAccuracy];",
"Print[\"StrongProbeBalancedAccuracy=\",t5bStrongProbeBalancedAccuracy];",
"Print[\"StrongTransitionExact=\",t5bStrongTransitionExactCount,\"/\",Length[t5sHighOrderTransitionRows]];",
"Print[\"StrongTransitionExactAccuracy=\",t5bStrongTransitionExactAccuracy];",
"Print[\"StrongTransitionProbeAccuracy=\",t5bStrongTransitionProbeAccuracy];",
"Print[\"StrongTransitionBalancedAccuracy=\",t5bStrongTransitionBalancedAccuracy];",
"Print[\"TCCTMinusBestNeuralStateExact=\",t5bTCCTMinusBestNeuralStateExact];",
"Print[\"TCCTMinusBestNeuralTransitionExact=\",t5bTCCTMinusBestNeuralTransitionExact];",
"Print[\"PILOT PROTOCOL PASS=\",t5bPilotProtocolPass];",
"Print[\"PILOT OUTCOME=\",t5bPilotOutcome];",
"t5bSummary=Association[t5sSummary];",
"AssociateTo[t5bSummary,{\"Stage\"->\"S125-C-Pilot5\",\"Protocol\"->\"MultiRestartMatchedAndStrongTransformerComparison\",\"MatchedRestartSpec\"->t5cMatchedRestartSpec,\"MatchedSelectionCandidateMetrics\"->t5cMatchedSelectionCandidateMetrics,\"MatchedFinalCandidateMetrics\"->t5cMatchedFinalCandidateMetrics,\"MatchedSelectedSelectionSeed\"->t5cMatchedSelectedSelectionSeed,\"MatchedSelectedFinalSeed\"->t5cMatchedSelectedFinalSeed,\"ExpectedConditionalTransitionCells\"->expectedConditionalTransitionCellsS119B,\"MatchedReasonParameterCount\"->t5bMatchedReasonParameterCount,\"StrongReasonParameterCount\"->t5bStrongReasonParameterCount,\"StrongReasonSpec\"->t5bStrongReasonSpec,\"StrongReasonValidationAccuracy\"->t5bStrongReasonValidationAccuracy,\"StrongReasonValidationBalancedAccuracy\"->t5bStrongReasonValidationBalancedAccuracy,\"StrongFinalReasonTrainingAccuracy\"->t5bStrongReasonTrainingAccuracy,\"StrongFinalReasonTrainingBalancedAccuracy\"->t5bStrongReasonTrainingBalancedAccuracy,\"StrongReasonFreezeFileHash\"->t5bStrongReasonFreezeFileHash,\"StrongHighOrderExact\"->t5bStrongExactCount,\"StrongHighOrderExactAccuracy\"->t5bStrongExactAccuracy,\"StrongProbeAccuracy\"->t5bStrongProbeAccuracy,\"StrongProbeZeroAccuracy\"->t5bStrongProbeZeroAccuracy,\"StrongProbeOneAccuracy\"->t5bStrongProbeOneAccuracy,\"StrongProbeBalancedAccuracy\"->t5bStrongProbeBalancedAccuracy,\"StrongTransitionExact\"->t5bStrongTransitionExactCount,\"StrongTransitionExactAccuracy\"->t5bStrongTransitionExactAccuracy,\"StrongTransitionProbeAccuracy\"->t5bStrongTransitionProbeAccuracy,\"StrongTransitionZeroAccuracy\"->t5bStrongTransitionZeroAccuracy,\"StrongTransitionOneAccuracy\"->t5bStrongTransitionOneAccuracy,\"StrongTransitionBalancedAccuracy\"->t5bStrongTransitionBalancedAccuracy,\"BestNeuralStateExactAccuracy\"->t5bBestNeuralStateExactAccuracy,\"BestNeuralTransitionExactAccuracy\"->t5bBestNeuralTransitionExactAccuracy,\"TCCTMinusBestNeuralStateExact\"->t5bTCCTMinusBestNeuralStateExact,\"TCCTMinusBestNeuralTransitionExact\"->t5bTCCTMinusBestNeuralTransitionExact,\"PilotProtocolPass\"->t5bPilotProtocolPass,\"PilotOutcome\"->t5bPilotOutcome,\"AllModelsFrozenBeforeHighOrder\"->True}];",
"t5bSummaryFile=FileNameJoin[{t5sOutputDirectory,\"S125C_pilot_summary.wl\"}];",
"Put[t5bSummary,t5bSummaryFile];",
"Print[\"S125C_SummaryFile=\",t5bSummaryFile];",
"Print[\"============================================================\"];",
"Print[\"S125-C PILOT WORLD COMPLETE\"];",
"Print[\"============================================================\"];"
},
"\n"
];
S125LineRule[line_String]:=
Module[{positions,left,right},
positions=StringPosition[line,"=",1];
If[positions==={},Return[Nothing]];
left=StringTrim[StringTake[line,positions[[1,1]]-1]];
right=StringTrim[StringDrop[line,positions[[1,2]]]];
If[
StringMatchQ[left,RegularExpression["[A-Za-z][A-Za-z0-9_ \\-]*"]],
left->right,
Nothing
]
];
S125Metrics[text_String]:=
Association[S125LineRule/@StringSplit[text,{"\r\n","\n","\r"}]];
S125Metric[metrics_Association,keys_List]:=
Module[{found},
found=SelectFirst[keys,KeyExistsQ[metrics,#]&,Missing["NotFound",keys]];
If[MissingQ[found],found,Lookup[metrics,found]]
];
S125TrueStringQ[value_]:=StringQ[value]&&StringTrim[value]==="True";
S125ZeroStringQ[value_]:=StringQ[value]&&MemberQ[{"0","0.","0.0"},StringTrim[value]];
S125TwoStringQ[value_]:=StringQ[value]&&MemberQ[{"2","2.","2.0"},StringTrim[value]];
S125RunWorld[seed_Integer,index_Integer,total_Integer]:=
Module[
{
runDirectory,generatedFile,logFile,errorFile,resultFile,existingResult,
seedReplacement,outputReplacement,preparedBaseText,generatedText,generatedHash,started,
processResult,exitCode,stdout,stderr,metrics,strictValue,prospectiveValue,
sharedPerceptionValue,orderValue,touchedValue,protocolHashValue,checks,
runCompleted,runPassed,result,stdoutStream,stderrStream,evaluationStatus,
replacementRules,dynamicCellGateReplacement,jupyterStopReplacement,
summaryFile,summaryAssociation,fatalFile,fatalText
},
runDirectory=FileNameJoin[{s125OutputRoot,"world_"<>IntegerString[index,10,2]<>"_seed_"<>ToString[seed]}];
If[!DirectoryQ[runDirectory],CreateDirectory[runDirectory]];
generatedFile=FileNameJoin[{runDirectory,"S125C_generated_multirestart_comparison_seed_"<>ToString[seed]<>".wl"}];
logFile=FileNameJoin[{runDirectory,"S125C_stdout.log"}];
errorFile=FileNameJoin[{runDirectory,"S125C_stderr.log"}];
resultFile=FileNameJoin[{runDirectory,"S125C_result.wl"}];
If[
FileExistsQ[resultFile],
existingResult=Quiet@Check[Get[resultFile],$Failed];
If[
AssociationQ[existingResult]&&
Lookup[existingResult,"WorldSeed",Missing[]]===seed&&
Lookup[existingResult,"BaseSourceSHA256",Missing[]]===s125BaseSourceHash&&
Lookup[existingResult,"ManifestSHA256",Missing[]]===s125ManifestHash,
If[
TrueQ[Lookup[existingResult,"Completed",False]],
Print["RESUME SKIP ",index,"/",total," seed=",seed," passed=",Lookup[existingResult,"RunPassed",False]];
Return[existingResult],
Print["RESUME RETRY ",index,"/",total," seed=",seed," previous run was incomplete"]
],
S125BStop["existing per-world result does not match the frozen manifest"]
]
];
seedReplacement="hiddenBenchmarkSeedS119B="<>ToString[seed]<>";";
outputReplacement="t5sOutputDirectory="<>ToString[runDirectory,InputForm]<>";\n"<>
"Print[\"S125ManifestHash=\",\""<>s125ManifestHash<>"\"];\n"<>
"Print[\"S125BaseSourceSHA256=\",\""<>s125BaseSourceHash<>"\"];";
dynamicCellGateReplacement=StringRiffle[
{
"expectedConditionalTransitionCellsS119B=Total[Table[Module[{targetFactor,parentFactors,targetCount,parentProduct},",
"targetFactor=Lookup[actionToLearnedFactorS119B,action];",
"parentFactors=Lookup[learnedParentsByActionS119B,action,{}];",
"targetCount=learnedFactorsS119B[[targetFactor]][\"StateCount\"];",
"parentProduct=If[parentFactors==={},1,Times@@(learnedFactorsS119B[[#]][\"StateCount\"]&/@parentFactors)];",
"targetCount*parentProduct],{action,publicActionsS119B}]];",
"Print[\"ExpectedConditionalTransitionCells=\",expectedConditionalTransitionCellsS119B];",
"If[Length[conditionalTransitionsS119B]=!=expectedConditionalTransitionCellsS119B,T5SStop[\"sparse conditional transition table is incomplete\"]];"
},
"\n"
];
jupyterStopReplacement="T5SStop[msg_]:=(Print[\"FATAL: \",msg];Export[FileNameJoin[{t5sOutputDirectory,\"S125C_fatal.txt\"}],ToString[msg],\"Text\"];Throw[$Failed,\"T5SFatal\"]);";
replacementRules={
s125CanonicalSeedPattern->seedReplacement,
s125CanonicalOutputPattern->outputReplacement,
s125FixedCellGatePattern->dynamicCellGateReplacement,
s125FixedCellFinalPassPattern->"Length[conditionalTransitionsS119B]===expectedConditionalTransitionCellsS119B",
s125StrongConfigMarker->(s125StrongConfigMarker<>"\n"<>s125StrongConfigInjection),
s125StrongSpecMarker->(s125StrongSpecInjection<>"\n"<>s125StrongSpecMarker),
s125ProtocolHashLiteral->"{discoveryPolicySpecS119B,t5sReasonSpec,t5cMatchedRestartSpec,t5bStrongReasonSpec,t5sPerceptionSpec,t5sWinnerMargin}",
s125StrongTrainingMarker->(s125StrongTrainingInjection<>"\n"<>s125StrongTrainingMarker),
s125GlobalFreezeHashMarker->StringRiffle[{"t5sReasonMaxSeqLen,","t5cMatchedRestartSpec,","t5cMatchedSelectionCandidateMetrics,","t5cMatchedFinalCandidateMetrics,","t5cMatchedSelectedSelectionSeed,","t5cMatchedSelectedFinalSeed,","t5bStrongReasonSpec,","t5bStrongReasonValidationBalancedAccuracy,","t5bStrongReasonTrainingBalancedAccuracy,","t5bStrongReasonParameterCount,","t5bStrongReasonFreezeFileHash","},","\"SHA256\""},"\n"],
s125FreezePrintMarker->(s125FreezePrintMarker<>"\nPrint[\"StrongNeuralReasonerFrozen=True\"];") ,
s125Phase6Marker->(s125StrongSignatureInjection<>"\n"<>s125Phase6Marker),
s125CompleteMarker->(s125CompleteMarker<>"\n"<>s125StrongEvaluationInjection)
};
If[s125ExecutionMode==="JupyterKernel",AppendTo[replacementRules,s125JupyterStopLiteral->jupyterStopReplacement]];
preparedBaseText=S125CReplaceMatchedTraining[s125BaseText];
generatedText=StringReplace[
preparedBaseText,
replacementRules
];
If[StringContainsQ[generatedText,"hiddenBenchmarkSeedS119B=1245501;"],S125BStop["canonical world seed survived source generation"]];
If[!StringContainsQ[generatedText,seedReplacement],S125BStop["generated world seed is missing"]];
If[!StringContainsQ[generatedText,"S125ManifestHash"],S125BStop["generated provenance marker is missing"]];
If[!StringContainsQ[generatedText,"ExpectedConditionalTransitionCells"],S125BStop["dynamic conditional-cell audit is missing"]];
If[Length[StringCases[generatedText,s125FixedCellGatePattern]]=!=0,S125BStop["fixed 42-cell audit gate survived source generation"]];
If[Length[StringCases[generatedText,s125FixedCellFinalPassPattern]]=!=0,S125BStop["fixed 42-cell final-pass gate survived source generation"]];
If[StringContainsQ[generatedText,s125MatchedTrainingStartMarker],S125BStop["canonical single-seed matched training survived source generation"]];
If[!And@@(StringContainsQ[generatedText,#]&/@{"PHASE 5C: PREREGISTERED 3-SEED MATCHED REASONER SELECTION","MatchedSelectedSelectionSeed","MatchedSelectedFinalSeed","PHASE 5B: STRONG TRANSFORMER REASONER TRAINING","StrongNeuralReasonerFrozen=True","T5BStrongNeuralSignature","S125-C PILOT: MULTI-RESTART MATCHED + STRONG REASONER EVALUATION","PilotProtocolPass","S125C_pilot_summary.wl"}),S125BStop["S125-C baseline injection audit failed"]];
If[StringPosition[generatedText,"PHASE 5C: PREREGISTERED 3-SEED MATCHED REASONER SELECTION"][[1,1]]>StringPosition[generatedText,"PHASE 6: FIRST OPENING OF FRESH HIGH-ORDER HOLDOUT"][[1,1]],S125BStop["matched multi-restart selection occurs after high-order opening"]];
If[StringPosition[generatedText,"StrongNeuralReasonerFrozen=True"][[1,1]]>StringPosition[generatedText,"PHASE 6: FIRST OPENING OF FRESH HIGH-ORDER HOLDOUT"][[1,1]],S125BStop["strong baseline freeze occurs after high-order opening"]];
If[s125ExecutionMode==="JupyterKernel"&&StringContainsQ[generatedText,s125JupyterStopLiteral],S125BStop["Jupyter Abort definition survived source generation"]];
Export[generatedFile,generatedText,"Text",CharacterEncoding->"UTF-8"];
generatedHash=FileHash[generatedFile,"SHA256","HexString"];
If[
s125PreflightOnly,
Print["PREFLIGHT GENERATED SOURCE=",generatedFile];
Print["PREFLIGHT GeneratedSourceSHA256=",generatedHash];
Return[<|"Stage"->"S125-C-Pilot5","PreflightOnly"->True,"WorldSeed"->seed,"GeneratedSourceFile"->generatedFile,"GeneratedSourceSHA256"->generatedHash|>]
];
Print["------------------------------------------------------------"];
Print["RUN START ",index,"/",total," seed=",seed];
Print["GeneratedSourceSHA256=",generatedHash];
started=AbsoluteTime[];
If[
s125ExecutionMode==="ExternalKernel",
processResult=Quiet@Check[
RunProcess[S125KernelCommand[generatedFile],All],
<|"ExitCode"->-999,"StandardOutput"->"","StandardError"->"RunProcess failed"|>
];
exitCode=Lookup[processResult,"ExitCode",-999];
stdout=ToString[Lookup[processResult,"StandardOutput",""]];
stderr=ToString[Lookup[processResult,"StandardError",""]];
Export[logFile,stdout,"Text",CharacterEncoding->"UTF-8"];
Export[errorFile,stderr,"Text",CharacterEncoding->"UTF-8"],
stdoutStream=OpenWrite[logFile,PageWidth->Infinity];
stderrStream=OpenWrite[errorFile,PageWidth->Infinity];
evaluationStatus=Catch[
CheckAbort[
Block[
{
$Context="Global`",
$ContextPath={"System`","Global`"},
$Output={stdoutStream},
$Messages={stderrStream}
},
Get[generatedFile]
];
"Completed",
"Aborted"
],
"T5SFatal",
Function[{value,tag},"Fatal"]
];
Close[stdoutStream];
Close[stderrStream];
stdout=Quiet@Check[Import[logFile,"Text",CharacterEncoding->"UTF-8"],""];
stderr=Quiet@Check[Import[errorFile,"Text",CharacterEncoding->"UTF-8"],""];
fatalFile=FileNameJoin[{runDirectory,"S125C_fatal.txt"}];
fatalText=If[FileExistsQ[fatalFile],Quiet@Check[Import[fatalFile,"Text"],""],""];
If[StringQ[fatalText]&&StringLength[StringTrim[fatalText]]>0,stderr=stderr<>"\nFATAL: "<>StringTrim[fatalText]];
exitCode=If[evaluationStatus==="Completed",0,2]
];
summaryFile=FileNameJoin[{runDirectory,"S125C_pilot_summary.wl"}];
If[
s125ExecutionMode==="JupyterKernel"&&FileExistsQ[summaryFile],
summaryAssociation=Quiet@Check[Get[summaryFile],$Failed];
metrics=If[
AssociationQ[summaryAssociation],
Association@KeyValueMap[Function[{key,value},key->ToString[value,InputForm]],summaryAssociation],
<||>
];
AssociateTo[metrics,"S125ManifestHash"->s125ManifestHash];
AssociateTo[metrics,"S125BaseSourceSHA256"->s125BaseSourceHash],
metrics=S125Metrics[stdout]
];
strictValue=S125Metric[metrics,{"PILOT PROTOCOL PASS","PilotProtocolPass"}];
prospectiveValue=S125Metric[metrics,{"StrictProspective","STRICT_PROSPECTIVE"}];
sharedPerceptionValue=S125Metric[metrics,{"SharedPerception","SHARED PERCEPTION"}];
orderValue=S125Metric[metrics,{"MaximumTrainingInteractionOrder"}];
touchedValue=S125Metric[metrics,{"HighOrderTouchedBeforeFreeze"}];
protocolHashValue=S125Metric[metrics,{"PreWorldProtocolHash"}];
checks=<|
"ProcessExitCodeZero"->TrueQ[exitCode===0],
"NoFatalMarker"->StringFreeQ[stdout<>stderr,"FATAL:"],
"PilotProtocolPass"->S125TrueStringQ[strictValue],
"StrictProspective"->S125TrueStringQ[prospectiveValue],
"SharedPerception"->S125TrueStringQ[sharedPerceptionValue],
"MaximumTrainingInteractionOrderTwo"->S125TwoStringQ[orderValue],
"NoHighOrderLeakage"->S125ZeroStringQ[touchedValue],
"PreWorldProtocolHashPresent"->StringQ[protocolHashValue]&&StringLength[protocolHashValue]>=32,
"ManifestEchoMatches"->S125Metric[metrics,{"S125ManifestHash"}]===s125ManifestHash,
"BaseSourceEchoMatches"->S125Metric[metrics,{"S125BaseSourceSHA256"}]===s125BaseSourceHash
|>;
runCompleted=If[
s125ExecutionMode==="JupyterKernel",
MemberQ[{"Completed","Fatal"},evaluationStatus],
TrueQ[checks["ManifestEchoMatches"]]&&
TrueQ[checks["BaseSourceEchoMatches"]]&&
(TrueQ[exitCode===0]||!StringFreeQ[stdout<>stderr,"FATAL:"])
];
runPassed=And@@Values[checks];
result=<|
"Stage"->"S125-C-Pilot5",
"Completed"->runCompleted,
"RunIndex"->index,
"WorldSeed"->seed,
"BaseSourceSHA256"->s125BaseSourceHash,
"ManifestSHA256"->s125ManifestHash,
"GeneratedSourceSHA256"->generatedHash,
"ProcessExitCode"->exitCode,
"ElapsedSeconds"->N[AbsoluteTime[]-started],
"RunPassed"->runPassed,
"Checks"->checks,
"Metrics"->metrics,
"GeneratedSourceFile"->generatedFile,
"StandardOutputFile"->logFile,
"StandardErrorFile"->errorFile
|>;
Put[result,resultFile];
Print["RUN END ",index,"/",total," seed=",seed," passed=",runPassed," elapsedSeconds=",result["ElapsedSeconds"]];
If[!runPassed,Print["FAILED CHECKS=",Keys@Select[checks,Not@TrueQ[#]&]]];
If[s125ExecutionMode==="JupyterKernel",ClearAll["Global`*"];ClearSystemCache[]];
result
];
If[
s125PreflightOnly,
s125PreflightResult=S125RunWorld[First[s125WorldSeeds],1,Length[s125WorldSeeds]];
If[!TrueQ[Lookup[s125PreflightResult,"PreflightOnly",False]],S125BStop["preflight source generation failed"]];
Print["S125-C PREFLIGHT COMPLETE; NO HIDDEN WORLD WAS OPENED"];
Throw[Null,"S125BFatal"]
];
s125Results=MapIndexed[
S125RunWorld[#1,First[#2],Length[s125WorldSeeds]]&,
s125WorldSeeds
];
If[!AllTrue[s125Results,AssociationQ],S125BStop["one or more per-world results are invalid"]];
s125CompletedCount=Count[Lookup[s125Results,"Completed",False],True];
s125PassedCount=Count[Lookup[s125Results,"RunPassed",False],True];
s125FailedCount=Length[s125Results]-s125PassedCount;
s125PassRate=N[s125PassedCount/Length[s125Results]];
s125ProtocolHashes=DeleteDuplicates@DeleteMissing[
S125Metric[Lookup[#,"Metrics",<||>],{"PreWorldProtocolHash"}]&/@s125Results
];
s125ProtocolHashStable=Length[s125ProtocolHashes]===1;
s125ExecutionComplete=s125CompletedCount===Length[s125WorldSeeds];
s125OverallPass=
s125ExecutionComplete&&
s125ProtocolHashStable&&
s125PassRate>=s125RequiredPassRate;
s125Aggregate=<|
"Stage"->"S125-C-Pilot5",
"Protocol"->"MultiRestartMatchedAndStrongTransformerComparison",
"BaseSourceSHA256"->s125BaseSourceHash,
"ManifestSHA256"->s125ManifestHash,
"WorldCount"->Length[s125WorldSeeds],
"CompletedWorlds"->s125CompletedCount,
"PilotPassedWorlds"->s125PassedCount,
"PilotFailedWorlds"->s125FailedCount,
"PilotProtocolPassRate"->s125PassRate,
"RequiredPassRate"->s125RequiredPassRate,
"PreWorldProtocolHashes"->s125ProtocolHashes,
"PreWorldProtocolHashStable"->s125ProtocolHashStable,
"ExecutionComplete"->s125ExecutionComplete,
"S125COverallPass"->s125OverallPass,
"Results"->s125Results
|>;
s125AggregateFile=FileNameJoin[{s125OutputRoot,"S125C_pilot_aggregate_summary.wl"}];
s125CSVFile=FileNameJoin[{s125OutputRoot,"S125C_pilot_per_world_summary.csv"}];
Put[s125Aggregate,s125AggregateFile];
S125CSVNumber[value_]:=Which[
NumericQ[value],value,
StringQ[value],Quiet@Check[ToExpression[value,InputForm],Missing["NotNumeric"]],
True,Missing["NotNumeric"]
];
S125CSVExactCount[metrics_Association,accuracyKey_String,countKey_String]:=
Module[{accuracy,count},
accuracy=S125CSVNumber[Lookup[metrics,accuracyKey,Missing[]]];
count=S125CSVNumber[Lookup[metrics,countKey,Missing[]]];
If[NumericQ[accuracy]&&NumericQ[count],Round[accuracy*count],""]
];
S125CSVMetricValue[result_Association,column_String]:=
Module[{metrics=Lookup[result,"Metrics",<||>]},
Switch[
column,
"ExpectedConditionalTransitionCells",
Lookup[metrics,column,Lookup[metrics,"ConditionalTransitionCells",""]],
"TCCTHighOrderExact",
S125CSVExactCount[metrics,"TCCTHighOrderExactAccuracy","HighOrderHoldoutStates"],
"NeuralHighOrderExact",
S125CSVExactCount[metrics,"NeuralHighOrderExactAccuracy","HighOrderHoldoutStates"],
"TCCTTransitionExact",
S125CSVExactCount[metrics,"TCCTTransitionExactAccuracy","HighOrderTransitionCases"],
"NeuralTransitionExact",
S125CSVExactCount[metrics,"NeuralTransitionExactAccuracy","HighOrderTransitionCases"],
_,Lookup[metrics,column,""]
]
];
s125MetricColumns={
"FreshWorldSeed","StrictProspective","SharedPerception","PreWorldProtocolHash",
"PerceptionValidationAccuracy","TrainingMembershipPerceptionAccuracy",
"MaximumTrainingInteractionOrder","HighOrderTouchedBeforeFreeze","InferredFactors",
"LocalStateCounts","LearnedInteractionEdges","ConditionalTransitionCells",
"ExpectedConditionalTransitionCells",
"MembershipQueriesBeforeFreeze","ReasonValidationAccuracy",
"ReasonValidationBalancedAccuracy","FinalReasonTrainingAccuracy",
"FinalReasonTrainingBalancedAccuracy","TrueJointStates","HighOrderHoldoutStates",
"TCCTHighOrderExact","TCCTHighOrderExactAccuracy","NeuralHighOrderExact",
"NeuralHighOrderExactAccuracy","TCCTProbeAccuracy","TCCTProbeBalancedAccuracy",
"NeuralProbeAccuracy","NeuralZeroAccuracy","NeuralOneAccuracy","NeuralBalancedAccuracy",
"HighOrderTransitionCases","TCCTTransitionExact","TCCTTransitionExactAccuracy",
"NeuralTransitionExact","NeuralTransitionExactAccuracy","TCCTTransitionProbeAccuracy",
"NeuralTransitionProbeAccuracy","NeuralTransitionZeroAccuracy",
"NeuralTransitionOneAccuracy","NeuralTransitionBalancedAccuracy",
"TCCTMinusNeuralExact","TCCTMinusNeuralProbe","TCCTMinusNeuralTransitionExact",
"WinnerMargin","StrictProtocolPass",
"GeneralizationDiagnosis",
"MatchedRestartSpec","MatchedSelectionCandidateMetrics","MatchedFinalCandidateMetrics",
"MatchedSelectedSelectionSeed","MatchedSelectedFinalSeed",
"MatchedReasonParameterCount","StrongReasonParameterCount","StrongReasonSpec",
"StrongReasonValidationAccuracy","StrongReasonValidationBalancedAccuracy",
"StrongFinalReasonTrainingAccuracy","StrongFinalReasonTrainingBalancedAccuracy",
"StrongReasonFreezeFileHash","StrongHighOrderExact","StrongHighOrderExactAccuracy",
"StrongProbeAccuracy","StrongProbeZeroAccuracy","StrongProbeOneAccuracy",
"StrongProbeBalancedAccuracy","StrongTransitionExact","StrongTransitionExactAccuracy",
"StrongTransitionProbeAccuracy","StrongTransitionZeroAccuracy","StrongTransitionOneAccuracy",
"StrongTransitionBalancedAccuracy","BestNeuralStateExactAccuracy",
"BestNeuralTransitionExactAccuracy","TCCTMinusBestNeuralStateExact",
"TCCTMinusBestNeuralTransitionExact","PilotProtocolPass","PilotOutcome",
"AllModelsFrozenBeforeHighOrder"
};
s125TopColumns={"RunIndex","WorldSeed","ProcessExitCode","ElapsedSeconds","RunPassed"};
s125CSVColumns=Join[s125TopColumns,s125MetricColumns];
s125CSVRows=Table[
Join[
Lookup[result,s125TopColumns,""],
S125CSVMetricValue[result,#]&/@s125MetricColumns
],
{result,s125Results}
];
Export[s125CSVFile,Prepend[s125CSVRows,s125CSVColumns],"CSV"];
Print["============================================================"];
Print["S125-C PILOT FINAL AGGREGATE SUMMARY"];
Print["============================================================"];
Print["WorldCount=",Length[s125WorldSeeds]];
Print["CompletedWorlds=",s125CompletedCount];
Print["PilotPassedWorlds=",s125PassedCount];
Print["PilotFailedWorlds=",s125FailedCount];
Print["PilotProtocolPassRate=",s125PassRate];
Print["RequiredPassRate=",s125RequiredPassRate];
Print["PreWorldProtocolHashStable=",s125ProtocolHashStable];
Print["ExecutionComplete=",s125ExecutionComplete];
Print["S125-C PILOT OVERALL PASS=",s125OverallPass];
Print["AggregateSummaryFile=",s125AggregateFile];
Print["PerWorldCSVFile=",s125CSVFile];
Print["============================================================"];
Null,
"S125BFatal"
];
End[];
EndPackage[];
