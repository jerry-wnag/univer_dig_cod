"""Build the standalone TCCT S91 post-hoc baseline/ablation benchmark."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WL = ROOT / "TCCT_S91_BaselineAblationBenchmark.wl"
NB = ROOT / "TCCT_S91_BaselineAblationBenchmark.ipynb"
LAUNCHER = ROOT / "Start_TCCT_S91_Jupyter.cmd"
PRECOMMIT = ROOT / "TCCT_S91_Precommit.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


environment = r'''
ClearAll["Global`*"];
$HistoryLength=0;
<|"WolframVersion"->$Version,"SystemID"->$SystemID,
"ProcessorCount"->$ProcessorCount|>
'''.strip()

preflight = r'''
ClearAll[FileSHA256Hex91];
FileSHA256Hex91[path_String]:=IntegerString[FileHash[path,"SHA256"],16,64];

projectDirectory91=Directory[];
archivePath91=FileNameJoin[{projectDirectory91,"artifacts",
"TCCT_S90_BenchmarkWorlds.json"}];
archiveManifestPath91=FileNameJoin[{projectDirectory91,"artifacts",
"TCCT_S90_BenchmarkWorlds_Manifest.json"}];
decoderRuntimePath91="E:/engine_wolf/TCCT_S87D_FrozenDecoderRuntime.wl";
decoderCandidatePath91="E:/engine_wolf/TCCT_S87D_FrozenWorldMultisetDecoder.wxf";
s90CertificatePath91="E:/engine_wolf/TCCT_S90_BlindResultCertificate.json";
s91CertificatePath="E:/engine_wolf/TCCT_S91_BenchmarkCertificate.json";

expectedArchiveFileHash91=
"39b1b822153e33e01d0294168507c06a8c6c96726f7a875394026d257603f0c0";
expectedArchiveManifestFileHash91=
"9e948cc950cd638eae1aaebcf40496280361c5d6ffd3bb6a48bb879539858a24";
expectedArchivePayloadHash91=
"b7867e7f1deab9584f89349bd08d1d9a4b08b69a5790c3d7527a7178cb30f10b";
expectedDecoderCandidateFileHash91=
"82616c6acde25ecd7bbbc51bc80d03771ec8653bf033167ac9ccd74d7da01d91";
expectedDecoderCandidateHash91=
"703e1365490a0123eac61745876dbcf29066abac4c753bb6ec1f61b790e222fe";
expectedDecoderRuntimeFileHash91=
"7d45fffdb3e33a0f0759ae9fa93c84429743cbe39fc7f02c38eeef11739740ee";
expectedS90CertificateFileHash91=
"0e8c9df9e63ea68d59226416de33243440ef4b84a007be0812b2970ed53deb30";
expectedS90ProtocolHash91=
"ed241ba2ada54af6e44f9dc009a70f4155767de6994072c7c05e5b75515df518";
expectedS90TestDefinitionHash91=
"ef31b96fa3a1ff1b4c7f4aec17456d60ec3381eca4df7f6ee8b9bf25f320539c";

requiredFiles91={archivePath91,archiveManifestPath91,decoderRuntimePath91,
decoderCandidatePath91,s90CertificatePath91};
If[!And@@(FileExistsQ/@requiredFiles91),
Print["S91 aborted: one or more locked input files are missing."];
Dataset[AssociationThread[requiredFiles91,FileExistsQ/@requiredFiles91]];
Abort[]];
If[FileExistsQ[s91CertificatePath],
Print["S91 aborted: a prior benchmark certificate already exists. Preserve it."];
Print[s91CertificatePath];Abort[]];

archiveFileHashBefore91=FileSHA256Hex91[archivePath91];
archiveManifestFileHashBefore91=FileSHA256Hex91[archiveManifestPath91];
decoderCandidateFileHashBefore91=FileSHA256Hex91[decoderCandidatePath91];
decoderRuntimeFileHashBefore91=FileSHA256Hex91[decoderRuntimePath91];
s90CertificateFileHashBefore91=FileSHA256Hex91[s90CertificatePath91];

archive91=Quiet@Check[Import[archivePath91,"RawJSON"],$Failed];
archiveManifest91=Quiet@Check[Import[archiveManifestPath91,"RawJSON"],$Failed];
s90Certificate91=Quiet@Check[Import[s90CertificatePath91,"RawJSON"],$Failed];
If[!AssociationQ[archive91]||!AssociationQ[archiveManifest91]||
!AssociationQ[s90Certificate91],
Print["S91 aborted: a locked JSON input could not be imported."];Abort[]];

Get[decoderRuntimePath91];
decoder91=Quiet@Check[TCCTLoadFrozenDecoderS87D[decoderCandidatePath91],$Failed];
If[!AssociationQ[decoder91],
Print["S91 aborted: the frozen S87D decoder failed its internal hash checks."];
Abort[]];

rows91=Lookup[archive91,"Rows",$Failed];
vectors91=If[ListQ[rows91],Lookup[rows91,"FeatureVector",$Failed],$Failed];
targets91=If[ListQ[rows91],Lookup[rows91,"Target",$Failed],$Failed];
cachedFullPredictions91=If[ListQ[rows91],Lookup[rows91,"Prediction",$Failed],$Failed];
cachedLegacyPredictions91=If[ListQ[rows91],Lookup[rows91,"LegacyPrediction",$Failed],$Failed];
classifier91=Lookup[decoder91,"Classifier",$Failed];

preflightPassed91=And[
SameQ[archiveFileHashBefore91,expectedArchiveFileHash91],
SameQ[archiveManifestFileHashBefore91,expectedArchiveManifestFileHash91],
SameQ[decoderCandidateFileHashBefore91,expectedDecoderCandidateFileHash91],
SameQ[decoderRuntimeFileHashBefore91,expectedDecoderRuntimeFileHash91],
SameQ[s90CertificateFileHashBefore91,expectedS90CertificateFileHash91],
SameQ[Lookup[archive91,"ArchivePayloadHash",Missing[]],expectedArchivePayloadHash91],
SameQ[Lookup[archiveManifest91,"ArchivePayloadHash",Missing[]],expectedArchivePayloadHash91],
SameQ[Lookup[archive91,"SourceProtocolHash",Missing[]],expectedS90ProtocolHash91],
SameQ[Lookup[archive91,"SourceTestDefinitionHash",Missing[]],
expectedS90TestDefinitionHash91],
SameQ[Lookup[s90Certificate91,"ProtocolHash",Missing[]],expectedS90ProtocolHash91],
SameQ[Lookup[s90Certificate91,"TestDefinitionHash",Missing[]],
expectedS90TestDefinitionHash91],
SameQ[Lookup[s90Certificate91,"Outcome",Missing[]],
"S90_BLIND_INTERVENTION_ALGEBRA_PASS"],
SameQ[Lookup[decoder91,"CandidateHash",Missing[]],expectedDecoderCandidateHash91],
SameQ[Lookup[archive91,"SourceCandidateHash",Missing[]],expectedDecoderCandidateHash91],
ListQ[rows91],SameQ[Length[rows91],1296],
ListQ[vectors91],SameQ[Length[vectors91],1296],
And@@(VectorQ[#,IntegerQ]&&Length[#]===27&/@vectors91),
SameQ[Counts[targets91],<|"Stop"->144,"Continue"->1152|>],
And@@(MemberQ[{"Continue","Stop"},#]&/@cachedFullPredictions91),
And@@(MemberQ[{"Continue","Stop"},#]&/@cachedLegacyPredictions91),
Head[classifier91]===ClassifierFunction
];
If[!TrueQ[preflightPassed91],
Print["S91 aborted: locked-input preflight failed."];Abort[]];

Dataset[{<|"Stage"->"S91-PREFLIGHT","Passed"->preflightPassed91,
"ArchivedWorlds"->Length[rows91],"ContinueTargets"->Count[targets91,"Continue"],
"StopTargets"->Count[targets91,"Stop"],
"CandidateHash"->decoder91["CandidateHash"],
"CoreLoaded"->False,"TrainingRun"->False|>}]
'''.strip()

protocol = r'''
ClearAll[ZeroPositions91,KeepPositions91,TransformVector91,
ScorePredictions91,PredictionBundle91,ResultRow91,GroupedRows91];

ZeroPositions91[vector_List,positions_List]:=ReplacePart[
vector,Thread[positions->0]];
KeepPositions91[vector_List,positions_List]:=ZeroPositions91[
vector,Complement[Range[Length[vector]],positions]];
TransformVector91[vector_List,mode_String,positions_List]:=Switch[mode,
"Identity",vector,
"Drop",ZeroPositions91[vector,positions],
"Keep",KeepPositions91[vector,positions],
_,$Failed];

modelSpecs91={
<|"Model"->"FrozenS87DFull","Kind"->"FrozenDecoder",
"Transform"->"Identity","Positions"->{}|>,
<|"Model"->"LegacyK33ExactRole","Kind"->"CachedBaseline",
"Transform"->"CachedLegacyPrediction","Positions"->{}|>,
<|"Model"->"AlwaysContinue","Kind"->"ConstantBaseline",
"Transform"->"ConstantContinue","Positions"->{}|>,
<|"Model"->"AlwaysStop","Kind"->"ConstantBaseline",
"Transform"->"ConstantStop","Positions"->{}|>,
<|"Model"->"DropPairwiseStatistics","Kind"->"FrozenFeatureAblation",
"Transform"->"Drop","Positions"->Range[18,27]|>,
<|"Model"->"DropUnaryCodeStatistics","Kind"->"FrozenFeatureAblation",
"Transform"->"Drop","Positions"->Range[1,17]|>,
<|"Model"->"DropModuloArithmetic","Kind"->"FrozenFeatureAblation",
"Transform"->"Drop","Positions"->{11,12,13}|>,
<|"Model"->"DropCoordinateMoments","Kind"->"FrozenFeatureAblation",
"Transform"->"Drop","Positions"->Range[3,10]|>,
<|"Model"->"DropOrderAndDistance","Kind"->"FrozenFeatureAblation",
"Transform"->"Drop","Positions"->Range[14,17]|>,
<|"Model"->"DropCardinality","Kind"->"FrozenFeatureAblation",
"Transform"->"Drop","Positions"->{1,2,18}|>,
<|"Model"->"KeepOnlyModuloArithmetic","Kind"->"FrozenFeatureAblation",
"Transform"->"Keep","Positions"->{1,2,11,12,13,18}|>,
<|"Model"->"KeepOnlyCoordinateMoments","Kind"->"FrozenFeatureAblation",
"Transform"->"Keep","Positions"->Join[{1,2},Range[3,10],{18}]|>,
<|"Model"->"KeepOnlyOrderAndDistance","Kind"->"FrozenFeatureAblation",
"Transform"->"Keep","Positions"->Join[{1,2},Range[14,18]]|>,
<|"Model"->"KeepOnlyPairwiseStatistics","Kind"->"FrozenFeatureAblation",
"Transform"->"Keep","Positions"->Join[{1,2},Range[18,27]]|>
};

transformDefinitionHashBeforeScoring91=Hash[{
DownValues[ZeroPositions91],DownValues[KeepPositions91],
DownValues[TransformVector91],Normal[modelSpecs91]},"SHA256","HexString"];

protocol91=<|
"Stage"->"S91","Name"->"BaselineAblationBenchmark",
"EvaluationType"->"PostHocLockedS90Benchmark",
"BlindTest"->False,"S90ResultsAlreadyRevealed"->True,
"BenchmarkArchiveHash"->expectedArchiveFileHash91,
"BenchmarkArchivePayloadHash"->expectedArchivePayloadHash91,
"SourceS90ProtocolHash"->expectedS90ProtocolHash91,
"SourceS90TestDefinitionHash"->expectedS90TestDefinitionHash91,
"FrozenCandidateHash"->expectedDecoderCandidateHash91,
"Models"->modelSpecs91,
"AblationType"->"FrozenInputSensitivityWithoutRetraining",
"AllTrainableParametersFrozen"->True,
"TransformInputs"->{"FeatureVector"},
"TransformUsesTargets"->False,
"NoS88S89S90LabelUsedForTraining"->True,
"TrainingRun"->False,"CandidateSearchRun"->False,
"HyperparameterSearchRun"->False,"RetuningApplied"->False,
"CoreLoaded"->False,"CoreEditApplied"->False,
"OriginalFrozenPolicyEditApplied"->False,
"DeduplicationMechanismEditApplied"->False,
"CanonicalizerEditApplied"->False,
"InterventionRuleEditApplied"->False,
"TimingScope"->"DecoderOnlyOnCachedS90FeatureVectors",
"TransformDefinitionHash"->transformDefinitionHashBeforeScoring91
|>;
protocolHashBeforeScoring91=Hash[Normal[protocol91],"SHA256","HexString"];
Dataset[{Append[protocol91,"ProtocolHash"->protocolHashBeforeScoring91]}]
'''.strip()

evaluation = r'''
PredictionBundle91[spec_Association]:=Module[
{kind,mode,positions,transformed,timed,predictions,seconds},
kind=spec["Kind"];mode=spec["Transform"];positions=spec["Positions"];
Switch[kind,
"FrozenDecoder"|"FrozenFeatureAblation",
transformed=TransformVector91[#,mode,positions]&/@vectors91;
timed=AbsoluteTiming[Quiet@Check[classifier91/@transformed,$Failed]];
seconds=N[timed[[1]]];predictions=timed[[2]],
"CachedBaseline",predictions=cachedLegacyPredictions91;seconds="NotMeasuredCached",
"ConstantBaseline",predictions=If[SameQ[mode,"ConstantContinue"],
ConstantArray["Continue",Length[targets91]],ConstantArray["Stop",Length[targets91]]];
seconds="NotMeasuredConstant",
_,predictions=$Failed;seconds="Invalid"];
<|"Spec"->spec,"Predictions"->predictions,"DecoderSeconds"->seconds|>
];

predictionBundles91=PredictionBundle91/@modelSpecs91;
freshFullPredictions91=Lookup[First[predictionBundles91],"Predictions",$Failed];
freshFullMatchesCachedS9091=SameQ[freshFullPredictions91,cachedFullPredictions91];

ScorePredictions91[predictions_List]:=Module[
{continuePositions,stopPositions,continueCorrect,stopCorrect,score,invalid},
continuePositions=Flatten@Position[targets91,"Continue"];
stopPositions=Flatten@Position[targets91,"Stop"];
continueCorrect=Count[predictions[[continuePositions]],"Continue"];
stopCorrect=Count[predictions[[stopPositions]],"Stop"];
score=Count[MapThread[SameQ,{predictions,targets91}],True];
invalid=Count[predictions,x_/;!MemberQ[{"Continue","Stop"},x]];
<|"Score"->score,"Cases"->Length[targets91],
"Accuracy"->N[score/Length[targets91]],
"ContinueCorrect"->continueCorrect,"ContinueCases"->Length[continuePositions],
"ContinueAccuracy"->N[continueCorrect/Length[continuePositions]],
"StopCorrect"->stopCorrect,"StopCases"->Length[stopPositions],
"StopAccuracy"->N[stopCorrect/Length[stopPositions]],
"BalancedAccuracy"->N@Mean[{continueCorrect/Length[continuePositions],
stopCorrect/Length[stopPositions]}],"InvalidPredictions"->invalid|>
];

ResultRow91[bundle_Association]:=Module[{spec,predictions,score,changed},
spec=bundle["Spec"];predictions=bundle["Predictions"];
If[!ListQ[predictions]||!SameQ[Length[predictions],Length[targets91]],
Return[Join[spec,<|"Score"->0,"Cases"->Length[targets91],
"Accuracy"->0.,"BalancedAccuracy"->0.,"InvalidPredictions"->Length[targets91],
"ChangedVsFull"->Length[targets91],"DecoderSeconds"->bundle["DecoderSeconds"]|>]]];
score=ScorePredictions91[predictions];
changed=Count[MapThread[Function[{a,b},!SameQ[a,b]],
{predictions,freshFullPredictions91}],True];
Join[spec,score,<|"ChangedVsFull"->changed,
"DecoderSeconds"->bundle["DecoderSeconds"]|>]
];

resultRows91=ResultRow91/@predictionBundles91;
fullResult91=First[resultRows91];
resultRows91=Map[Append[#,"AccuracyGapFromFull"->
N[fullResult91["Accuracy"]-#1["Accuracy"]]]&,resultRows91];

GroupedRows91[model_String,predictions_List,key_String]:=Map[
Function[group,Module[{positions,subTargets,subPredictions,correct},
positions=Flatten@Position[Lookup[rows91,key],group];
subTargets=targets91[[positions]];subPredictions=predictions[[positions]];
correct=Count[MapThread[SameQ,{subPredictions,subTargets}],True];
<|"Model"->model,key->group,"Score"->correct,"Cases"->Length[positions],
"Accuracy"->N[correct/Length[positions]]|>]],
DeleteDuplicates[Lookup[rows91,key]]];

fullByTopology91=GroupedRows91["FrozenS87DFull",freshFullPredictions91,"Topology"];
legacyByTopology91=GroupedRows91["LegacyK33ExactRole",cachedLegacyPredictions91,"Topology"];
fullByDepth91=GroupedRows91["FrozenS87DFull",freshFullPredictions91,"Depth"];
legacyByDepth91=GroupedRows91["LegacyK33ExactRole",cachedLegacyPredictions91,"Depth"];

ablationRows91=Select[resultRows91,SameQ[#1["Kind"],"FrozenFeatureAblation"]&];
baselineRows91=Select[resultRows91,MemberQ[{"CachedBaseline","ConstantBaseline"},#1["Kind"]]&];

Column[{
Dataset[resultRows91],
Dataset[Join[fullByTopology91,legacyByTopology91]],
Dataset[Join[fullByDepth91,legacyByDepth91]]
}]
'''.strip()

audit = r'''
protocolHashAfterScoring91=Hash[Normal[protocol91],"SHA256","HexString"];
transformDefinitionHashAfterScoring91=Hash[{
DownValues[ZeroPositions91],DownValues[KeepPositions91],
DownValues[TransformVector91],Normal[modelSpecs91]},"SHA256","HexString"];
archiveFileHashAfter91=FileSHA256Hex91[archivePath91];
archiveManifestFileHashAfter91=FileSHA256Hex91[archiveManifestPath91];
decoderCandidateFileHashAfter91=FileSHA256Hex91[decoderCandidatePath91];
decoderRuntimeFileHashAfter91=FileSHA256Hex91[decoderRuntimePath91];
s90CertificateFileHashAfter91=FileSHA256Hex91[s90CertificatePath91];

allRowsValid91=And@@Map[Function[row,And[
SameQ[row["Cases"],1296],Between[row["Score"],{0,1296}],
Between[row["ContinueCorrect"],{0,1152}],Between[row["StopCorrect"],{0,144}],
SameQ[row["InvalidPredictions"],0]]],resultRows91];
fullFrozenPerfect91=And[SameQ[fullResult91["Score"],1296],
SameQ[fullResult91["ContinueCorrect"],1152],SameQ[fullResult91["StopCorrect"],144]];
degradedAblations91=Count[ablationRows91,row_/;row["Score"]<fullResult91["Score"]];
legacyResult91=SelectFirst[resultRows91,SameQ[#1["Model"],"LegacyK33ExactRole"]&];
fullOutperformsLegacy91=And[
fullResult91["Score"]>legacyResult91["Score"],
fullResult91["BalancedAccuracy"]>legacyResult91["BalancedAccuracy"]];

benchmarkValidityPassed91=And[
TrueQ[preflightPassed91],TrueQ[freshFullMatchesCachedS9091],
TrueQ[allRowsValid91],TrueQ[fullFrozenPerfect91],
SameQ[protocolHashBeforeScoring91,protocolHashAfterScoring91],
SameQ[transformDefinitionHashBeforeScoring91,transformDefinitionHashAfterScoring91],
SameQ[archiveFileHashBefore91,archiveFileHashAfter91],
SameQ[archiveManifestFileHashBefore91,archiveManifestFileHashAfter91],
SameQ[decoderCandidateFileHashBefore91,decoderCandidateFileHashAfter91],
SameQ[decoderRuntimeFileHashBefore91,decoderRuntimeFileHashAfter91],
SameQ[s90CertificateFileHashBefore91,s90CertificateFileHashAfter91]
];

benchmarkPayload91=<|
"Stage"->"S91","Name"->"BaselineAblationBenchmark",
"EvaluationType"->"PostHocLockedS90Benchmark","BlindTest"->False,
"ProtocolHash"->protocolHashAfterScoring91,
"TransformDefinitionHash"->transformDefinitionHashAfterScoring91,
"BenchmarkArchiveFileHash"->archiveFileHashAfter91,
"BenchmarkArchivePayloadHash"->archive91["ArchivePayloadHash"],
"S90CertificateFileHash"->s90CertificateFileHashAfter91,
"FrozenCandidateHash"->decoder91["CandidateHash"],
"FrozenCandidateFileHash"->decoderCandidateFileHashAfter91,
"Worlds"->Length[rows91],"ContinueTargets"->Count[targets91,"Continue"],
"StopTargets"->Count[targets91,"Stop"],"ModelsEvaluated"->Length[resultRows91],
"BaselinesEvaluated"->Length[baselineRows91],
"FrozenFeatureAblationsEvaluated"->Length[ablationRows91],
"FrozenFullScore"->fullResult91["Score"],
"FrozenFullAccuracy"->fullResult91["Accuracy"],
"FrozenFullBalancedAccuracy"->fullResult91["BalancedAccuracy"],
"LegacyScore"->legacyResult91["Score"],
"LegacyAccuracy"->legacyResult91["Accuracy"],
"LegacyBalancedAccuracy"->legacyResult91["BalancedAccuracy"],
"FullOutperformsLegacy"->fullOutperformsLegacy91,
"DegradedAblations"->degradedAblations91,
"BestAblationScore"->Max[Lookup[ablationRows91,"Score"]],
"WorstAblationScore"->Min[Lookup[ablationRows91,"Score"]],
"ModelResults"->resultRows91,
"FreshFullPredictionsMatchArchivedS90"->freshFullMatchesCachedS9091,
"BenchmarkValidityPassed"->benchmarkValidityPassed91,
"OriginalFrozenModelChanged"->False,"CoreChanged"->False,
"CanonicalizerChanged"->False,"InterventionRulesChanged"->False,
"DeduplicationMechanismChanged"->False,"UndirectedFreezeMechanismChanged"->False,
"FrozenDecoderChanged"->!SameQ[decoderCandidateFileHashBefore91,
decoderCandidateFileHashAfter91],
"S90CertificateChanged"->!SameQ[s90CertificateFileHashBefore91,
s90CertificateFileHashAfter91],
"BenchmarkArchiveChanged"->!SameQ[archiveFileHashBefore91,archiveFileHashAfter91],
"TrainingRun"->False,"CandidateSearchRun"->False,
"HyperparameterSearchRun"->False,"RetuningApplied"->False,
"AblationsRetrained"->False,"TransformUsesTargets"->False,
"MayClaimNewBlindGeneralization"->False,
"MayClaimAblationCausality"->False
|>;
benchmarkResultHash91=Hash[Normal[benchmarkPayload91],"SHA256","HexString"];
cert91=Join[benchmarkPayload91,<|
"BenchmarkResultHash"->benchmarkResultHash91,
"Outcome"->If[TrueQ[benchmarkValidityPassed91],
"S91_VALID_POSTHOC_BASELINE_ABLATION_COMPLETE",
"S91_INVALID_BENCHMARK_DO_NOT_INTERPRET"],
"SuggestedNextStage"->If[TrueQ[benchmarkValidityPassed91],
"S92_RETRAINED_ABLATIONS_AND_NEW_BLIND_HOLDOUT",
"S91R_REPAIR_BENCHMARK_HARNESS_WITHOUT_MODEL_CHANGE"]|>];
certificateExportResult91=Quiet@Check[
Export[s91CertificatePath,cert91,"RawJSON"],$Failed];
certificateExported91=And[StringQ[certificateExportResult91],
FileExistsQ[s91CertificatePath]];

Column[{
Dataset[{KeyDrop[cert91,{"ModelResults"}]}],
Dataset[resultRows91],
Dataset[{<|"CertificateExported"->certificateExported91,
"CertificatePath"->s91CertificatePath,
"CertificateFileHash"->If[certificateExported91,
FileSHA256Hex91[s91CertificatePath],"NOT_EXPORTED"]|>}]
}]
'''.strip()

cells = [environment, preflight, protocol, evaluation, audit]
WL.write_text("\n\n".join(f"(* S91 CELL {i} *)\n{cell}" for i, cell in enumerate(cells, 1)) + "\n", encoding="utf-8")


def code_cell(source: str, stage: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {"tcct_stage": stage},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


markdown = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "# TCCT S91 - Locked Baseline and Ablation Benchmark\n",
        "\n",
        "This is a post-hoc benchmark over the immutable 1,296-world S90 archive. "
        "It is not a new blind test. The S87D decoder is loaded by hash and is never "
        "trained, searched, retuned, or edited.\n",
        "\n",
        "The benchmark compares the frozen decoder with the cached legacy K=33 policy, "
        "constant class baselines, and pre-registered frozen-input feature deletions. "
        "Feature deletions are sensitivity tests, not retrained ablation models.\n",
        "\n",
        "Run **Kernel -> Restart Kernel and Run All Cells**. Expected runtime is a few "
        "minutes or less because propagation is not rerun.\n",
    ],
}

notebook = {
    "cells": [
        markdown,
        code_cell(environment, "S91-ENVIRONMENT"),
        code_cell(preflight, "S91-LOCKED-INPUT-PREFLIGHT"),
        code_cell(protocol, "S91-PROTOCOL"),
        code_cell(evaluation, "S91-EVALUATION"),
        code_cell(audit, "S91-AUDIT"),
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
NB.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

LAUNCHER.write_text(r'''@echo off
chcp 65001 >nul
setlocal
set "TCCT_DIR=%~dp0"
set "TCCT_NOTEBOOK=%TCCT_DIR%TCCT_S91_BaselineAblationBenchmark.ipynb"
set "TCCT_ARCHIVE=%TCCT_DIR%artifacts\TCCT_S90_BenchmarkWorlds.json"
set "TCCT_DECODER=E:\engine_wolf\TCCT_S87D_FrozenWorldMultisetDecoder.wxf"
set "TCCT_S90_RESULT=E:\engine_wolf\TCCT_S90_BlindResultCertificate.json"
set "TCCT_S91_RESULT=E:\engine_wolf\TCCT_S91_BenchmarkCertificate.json"
set "JUPYTER_LAB=E:\anaconda\Scripts\jupyter-lab.exe"
set "JUPYTER_DATA_DIR=E:\engine_wolf\jupyter\data"
set "JUPYTER_CONFIG_DIR=%TCCT_DIR%.jupyter_config_s91"
set "JUPYTER_RUNTIME_DIR=%TCCT_DIR%.jupyter_runtime_s91"
set "PYTHONUTF8=1"
if not exist "%JUPYTER_LAB%" (echo JupyterLab not found & pause & exit /b 1)
if not exist "%TCCT_NOTEBOOK%" (echo S91 notebook not found & pause & exit /b 1)
if not exist "%TCCT_ARCHIVE%" (echo Locked S90 benchmark archive not found & pause & exit /b 1)
if not exist "%TCCT_DECODER%" (echo Frozen S87D decoder not found & pause & exit /b 1)
if not exist "%TCCT_S90_RESULT%" (echo Locked S90 certificate not found & pause & exit /b 1)
if exist "%TCCT_S91_RESULT%" (
  echo A prior S91 benchmark certificate already exists.
  echo Preserve it and do not overwrite it.
  pause & exit /b 1
)
if not exist "%JUPYTER_CONFIG_DIR%" mkdir "%JUPYTER_CONFIG_DIR%"
if not exist "%JUPYTER_RUNTIME_DIR%" mkdir "%JUPYTER_RUNTIME_DIR%"
start "TCCT S91 JupyterLab" /min "%JUPYTER_LAB%" "%TCCT_NOTEBOOK%" --ServerApp.root_dir="%TCCT_DIR%" --ServerApp.port=8904 --ServerApp.port_retries=5
exit /b 0
''', encoding="utf-8")

precommit = {
    "Stage": "S91",
    "Name": "BaselineAblationBenchmark",
    "EvaluationType": "PostHocLockedS90Benchmark",
    "BlindTest": False,
    "TrainingRun": False,
    "CandidateSearchRun": False,
    "RetuningApplied": False,
    "CoreEditApplied": False,
    "ExpectedWorlds": 1296,
    "ExpectedContinueTargets": 1152,
    "ExpectedStopTargets": 144,
    "ExpectedModels": 14,
    "ExpectedBaselines": 3,
    "ExpectedFrozenFeatureAblations": 10,
    "ProtocolHash": "815c367c88a669939a9361553415d6396333be7e976d72f0ca5dbc0ea692ff1b",
    "ArchiveSHA256": "39b1b822153e33e01d0294168507c06a8c6c96726f7a875394026d257603f0c0",
    "ArchivePayloadHash": "b7867e7f1deab9584f89349bd08d1d9a4b08b69a5790c3d7527a7178cb30f10b",
    "FrozenCandidateHash": "703e1365490a0123eac61745876dbcf29066abac4c753bb6ec1f61b790e222fe",
    "S90CertificateSHA256": "0e8c9df9e63ea68d59226416de33243440ef4b84a007be0812b2970ed53deb30",
    "DynamicPreflightPassed": True,
    "AuditCellValidatedWithTemporaryCertificate": True,
    "RealS91CertificateCreatedDuringValidation": False,
    "WolframSourceSHA256": sha256(WL),
    "NotebookSHA256": sha256(NB),
}
PRECOMMIT.write_text(json.dumps(precommit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

for path in (WL, NB, LAUNCHER, PRECOMMIT):
    print(path)
