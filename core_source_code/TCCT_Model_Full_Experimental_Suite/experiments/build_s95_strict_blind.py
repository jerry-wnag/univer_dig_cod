"""Build the pre-registered, resumable TCCT S95 strict blind test."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
S94H_NOTEBOOK = ROOT / "TCCT_S94H_R3_Resumable_GUI_Compat.ipynb"
TEST_DEFINITIONS = ROOT / "TCCT_S95_TestDefinitions.wl"
PRECOMMIT = ROOT / "TCCT_S95_Precommit.json"
NOTEBOOK = ROOT / "TCCT_S95_StrictBlind.ipynb"
SOURCE = ROOT / "TCCT_S95_StrictBlind.wl"
PREFLIGHT_SOURCE = ROOT / "TCCT_S95_Preflight.wl"
LAUNCHER = ROOT / "Start_TCCT_S95_Jupyter.cmd"
BUILD_RECORD = ROOT / "TCCT_S95_BuildRecord.json"

S94H_CERT = Path(r"E:\engine_wolf\TCCT_S94H_R3_IndependentFullQueryConfirmation.json")
FROZEN_CANDIDATE = Path(r"E:\engine_wolf\TCCT_S94H_FrozenFullQueryReadout.wxf")

EXPECTED_S94H_RESULT_HASH = "bfeeb9c4696135be4cb8f918758cb133bc27aade8c04336f829a17d6224a044d"
EXPECTED_CANDIDATE_OBJECT_HASH = "5ec0e4eb89e9bb447a1e103537c7b4a82eab0c807023cd5862048372efdb418b"
EXPECTED_CANDIDATE_FILE_HASH = "8cbf7184200c6a04072f9b375af3137534dc3764bff7a32bf57db4a320187e1e"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def code_cell(source: str, cell_id: str) -> dict:
    return {
        "cell_type": "code",
        "id": cell_id,
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": [line + "\n" for line in source.strip().splitlines()],
    }


if not S94H_NOTEBOOK.exists() or not S94H_CERT.exists() or not FROZEN_CANDIDATE.exists():
    raise SystemExit("Locked S94H inputs are missing")
if sha256(FROZEN_CANDIDATE) != EXPECTED_CANDIDATE_FILE_HASH:
    raise SystemExit("Frozen S94H candidate file hash mismatch")
s94h_certificate = json.loads(S94H_CERT.read_text(encoding="utf-8"))
if not (
    s94h_certificate.get("ResultHash") == EXPECTED_S94H_RESULT_HASH
    and s94h_certificate.get("Outcome") == "S94H_INDEPENDENT_CONFIRMATION_PASS"
    and s94h_certificate.get("IntegrityPassed") is True
    and s94h_certificate.get("CoreChanged") is False
):
    raise SystemExit("S94H certificate is not the locked passing result")

s94h_nb = json.loads(S94H_NOTEBOOK.read_text(encoding="utf-8"))
s94h_code = [cell for cell in s94h_nb["cells"] if cell["cell_type"] == "code"]
if len(s94h_code) < 3:
    raise SystemExit("S94H setup cells are unavailable")
setup_cells = ["".join(cell["source"]).strip() for cell in s94h_code[:3]]
for idx, source in enumerate(setup_cells):
    setup_cells[idx] = source.replace(
        'resultCertificatePath94H="E:/engine_wolf/TCCT_S94H_R3_IndependentFullQueryConfirmation.json";',
        'resultCertificatePath94H="E:/engine_wolf/TCCT_S95_StrictBlindCertificate.json";',
    )

test_definitions = r'''
ClearAll[
SerialPrivateDiamondPath95,HeterogeneousSerialDiamondIn95,
UnilateralNestedDiamondIn95,TopologyTransform95,ExpectedContractions95,
ContextAction95,Case95,World95,Pair95
];

SerialPrivateDiamondPath95[parent_,target_,levels_Integer,start_Integer]:=Module[
{next=start,current=parent,edges={},s1,s2,g},
Do[
s1=next;s2=next+1;g=next+2;next+=3;
edges=Join[edges,{DirectedEdge[current,s1],DirectedEdge[current,s2],
DirectedEdge[s1,g],DirectedEdge[s2,g]}];current=g,
{levels}];
<|"Edges"->Append[edges,DirectedEdge[current,target]],"Next"->next|>
];

HeterogeneousSerialDiamondIn95[c_List]:=Module[
{x=c[[1]],answer=c[[2]],e,f,mx,next,new,ordinal=0,m,incs,removed,
added={},levels,built,i,j},
e=x[[1]];f=x[[6]];mx=Max@Flatten[List@@@e];next=mx+1;new=e;
Do[
m=f[[i]];
incs=SortBy[Cases[e,DirectedEdge[u_,v_]/;v===m:>{u,v}],
ToString[#,InputForm]&];
removed=DirectedEdge@@@incs;added={};
Do[ordinal++;levels=1+Mod[ordinal-1,3];
built=SerialPrivateDiamondPath95[incs[[j,1]],m,levels,next];
next=built["Next"];added=Join[added,built["Edges"]],{j,Length[incs]}];
new=Join[Complement[new,removed],added],{i,Length[f]}];
{{Union[new],x[[2]],x[[3]],x[[4]],x[[5]],x[[6]]},answer}
];

UnilateralNestedDiamondIn95[c_List]:=Module[
{x=c[[1]],answer=c[[2]],e,f,mx,next,new,m,incs,removed,added,
parent,s1,s2,g,b1,b2,bg,i,j},
e=x[[1]];f=x[[6]];mx=Max@Flatten[List@@@e];next=mx+1;new=e;
Do[m=f[[i]];
incs=SortBy[Cases[e,DirectedEdge[u_,v_]/;v===m:>{u,v}],
ToString[#,InputForm]&];removed=DirectedEdge@@@incs;added={};
Do[parent=incs[[j,1]];s1=next;s2=next+1;g=next+2;
b1=next+3;b2=next+4;bg=next+5;next+=6;
added=Join[added,{DirectedEdge[parent,b1],DirectedEdge[parent,b2],
DirectedEdge[b1,bg],DirectedEdge[b2,bg],DirectedEdge[bg,s1],
DirectedEdge[parent,s2],DirectedEdge[s1,g],DirectedEdge[s2,g],
DirectedEdge[g,m]}],{j,Length[incs]}];
new=Join[Complement[new,removed],added],{i,Length[f]}];
{{Union[new],x[[2]],x[[3]],x[[4]],x[[5]],x[[6]]},answer}
];

TopologyTransform95[name_String,c_List]:=Switch[name,
"HeterogeneousSerialDiamondIn",HeterogeneousSerialDiamondIn95[c],
"UnilateralNestedDiamondIn",UnilateralNestedDiamondIn95[c],_,$Failed];

ExpectedContractions95[name_String,baseCase_List]:=Module[{count},
count=DecisionIncomingEdgeCount79B[baseCase];Switch[name,
"HeterogeneousSerialDiamondIn",Total[1+Mod[Range[count]-1,3]],
"UnilateralNestedDiamondIn",2 count,_,Missing["UnknownTopology"]]];

ContextAction95[i_Integer,pattern_String,n_Integer]:=Switch[pattern,
"BinaryWeightOdd",If[OddQ[DigitCount[i,2,1]],"Continue","Stop"],
"AlternatingBlocksFour",If[EvenQ[Quotient[i-1,4]],"Continue","Stop"],
"EndpointOrSquare",If[i===1||i===n||IntegerQ[Sqrt[i]],"Continue","Stop"],
_,"Undefined"];

Case95[depth_Integer,answer_Integer,target_String,topologyIndex_Integer,
contextIndex_Integer,branchCount_Integer,pattern_String]:=Module[
{seed,bb,K,c,v,q,e,f={},ib,m,safe,u,dummy,r1,r2,wrong,main,perm,anc,
branchAction,i},
seed=95100000+100000 topologyIndex+10000 contextIndex+100 branchCount+depth;
bb=1000000000 seed;K=bb+1;c=Table[bb+100+i,{i,branchCount}];
v=Table[bb+200+i,{i,branchCount}];q=Table[bb+300+i,{i,branchCount}];
e=Flatten[Table[{DirectedEdge[K,c[[i]]],DirectedEdge[c[[i]],v[[i]]]},{i,branchCount}],1];
Do[ib=bb+20000000 i;m=ib+1;safe=ib+2;u=ib+3;dummy=ib+4;
r1=ib+10;r2=ib+20;wrong=c[[1+Mod[i,branchCount]]];
main=Join[P59[q[[i]],r1,depth,ib+1000000],P59[q[[i]],r2,depth,ib+2000000],
{DirectedEdge[r1,m],DirectedEdge[r2,m]},P59[q[[i]],safe,depth+1,ib+3000000]];
branchAction=If[i===answer,target,ContextAction95[i,pattern,branchCount]];
perm=If[branchAction==="Continue",{DirectedEdge[m,c[[i]]],
DirectedEdge[safe,dummy],DirectedEdge[u,wrong]},
{DirectedEdge[m,wrong],DirectedEdge[safe,c[[i]]],DirectedEdge[u,dummy]}];
anc=Join[A59[m,i,bb+970000000+10000 i],A59[c[[i]],i,bb+980000000+10000 i]];
e=Join[e,main,perm,anc];AppendTo[f,m],{i,branchCount}];
{{Union[e],q,K,v,c,f},answer}
];

World95[scenario_Association,target_String,answer_Integer]:=Module[
{baseCase,topologyCase,canonicalization,canonicalCase,traceSeconds,trace,
levels,pack,vertexList,queryNodes,rawMap,codeMap,slotMap,vector},
baseCase=Case95[scenario["Depth"],answer,target,scenario["TopologyIndex"],
scenario["ContextIndex"],scenario["BranchCount"],scenario["Context"]];
topologyCase=TopologyTransform95[scenario["Topology"],baseCase];
canonicalization=CanonicalizePrivateDiamonds79B[topologyCase];
canonicalCase=canonicalization["Case"];
{traceSeconds,trace}=AbsoluteTiming[RejectTrace78[canonicalCase]];
levels=SigLevels61[canonicalCase,3];pack=Pack60[canonicalCase];vertexList=pack[[12]];
queryNodes=Select[Range[Length[vertexList]],TrueQ[
NodeRole94H[vertexList[[#]],canonicalCase,answer]["QueryBranchRelated"]]&];
rawMap=AssociationThread[vertexList[[queryNodes]],
({Lookup[levels[[3]],#],Lookup[levels[[4]],#]}&)/@queryNodes];
codeMap=AssociationThread[Keys[rawMap],EncodePair94H/@Values[rawMap]];
If[!AssociationQ[codeMap]||!SameQ[Keys[codeMap],Keys[rawMap]]||
!SameQ[Length[codeMap],Length[rawMap]],Return[$Failed]];
slotMap=SemanticAlignedMap94H[codeMap,canonicalCase,answer];
vector=SlotRawVector94H[slotMap];
<|"Vector"->vector,"ReferenceAction"->ReferenceAction94H[canonicalCase],
"CanonicalCaseExactlyBase"->SameQ[canonicalCase,baseCase],
"ContractionCount"->canonicalization["Contractions"],
"ExpectedContractions"->ExpectedContractions95[scenario["Topology"],baseCase],
"ContractionCountCorrect"->SameQ[canonicalization["Contractions"],
ExpectedContractions95[scenario["Topology"],baseCase]],
"ProtectedNodesPreserved"->canonicalization["ProtectedNodesPreserved"],
"TerminatedNaturally"->trace["TerminatedNaturally"],
"HitSafetyCap"->trace["HitSafetyCap"],"TraceSeconds"->traceSeconds|>
];

Pair95[scenario_Association,answer_Integer]:=Module[
{continue,stop,difference,score,reverse,worldsValid},
continue=World95[scenario,"Continue",answer];stop=World95[scenario,"Stop",answer];
If[!AssociationQ[continue]||!AssociationQ[stop],Return[$Failed]];
difference=continue["Vector"]-stop["Vector"];
score=N[Total[candidateReloaded95["Weights"]
(difference/candidateReloaded95["Scale"])]];reverse=-score;
worldsValid=And[continue["CanonicalCaseExactlyBase"],
stop["CanonicalCaseExactlyBase"],continue["ContractionCountCorrect"],
stop["ContractionCountCorrect"],continue["ProtectedNodesPreserved"],
stop["ProtectedNodesPreserved"],continue["TerminatedNaturally"],
stop["TerminatedNaturally"],!continue["HitSafetyCap"],!stop["HitSafetyCap"]];
Join[KeyTake[scenario,{"Topology","Context","Depth","BranchCount"}],
<|"Answer"->answer,"Score"->score,"ReverseScore"->reverse,
"PairCorrect"->And[score>0,reverse<0],"ZeroScore"->Abs[score]<10^-12,
"ReferenceActionsCorrect"->And[SameQ[continue["ReferenceAction"],"Continue"],
SameQ[stop["ReferenceAction"],"Stop"]],"WorldsValid"->worldsValid,
"TraceSeconds"->continue["TraceSeconds"]+stop["TraceSeconds"]|>]
];
'''.strip()

TEST_DEFINITIONS.write_text(test_definitions + "\n", encoding="utf-8")
test_def_hash = sha256(TEST_DEFINITIONS)
s94h_cert_hash = sha256(S94H_CERT)

precommit_payload = {
    "Stage": "S95",
    "Name": "PreRegisteredStrictBlindHeterogeneousTopologyTest",
    "PreRegistered": True,
    "BlindTest": True,
    "CandidateFrozenBeforeProtocol": True,
    "CandidateSearchAllowed": False,
    "CandidateReexportAllowed": False,
    "TrainingAllowed": False,
    "CoreChangeAllowed": False,
    "RuleChangeAllowed": False,
    "DeduplicationChangeAllowed": False,
    "UndirectedFreezeChangeAllowed": False,
    "Topologies": ["HeterogeneousSerialDiamondIn", "UnilateralNestedDiamondIn"],
    "Contexts": ["BinaryWeightOdd", "AlternatingBlocksFour", "EndpointOrSquare"],
    "Scales": [
        {"Depth": 29, "BranchCount": 11},
        {"Depth": 61, "BranchCount": 19},
    ],
    "ExpectedScenarios": 12,
    "ExpectedPairs": 180,
    "ExpectedWorlds": 360,
    "PassAccuracy": 0.95,
    "PassWorstAxisGroupAccuracy": 0.8,
    "CheckpointCount": 12,
    "FrozenCandidateObjectSHA256": EXPECTED_CANDIDATE_OBJECT_HASH,
    "FrozenCandidateFileSHA256": EXPECTED_CANDIDATE_FILE_HASH,
    "LockedS94HR3ResultHash": EXPECTED_S94H_RESULT_HASH,
    "LockedS94HR3CertificateFileSHA256": s94h_cert_hash,
    "TestDefinitionFile": TEST_DEFINITIONS.name,
    "TestDefinitionFileSHA256": test_def_hash,
}
PRECOMMIT.write_text(json.dumps(precommit_payload, indent=2), encoding="utf-8")
precommit_hash = sha256(PRECOMMIT)

candidate_lock = f'''
If[!TrueQ[preflightPassed94H],
Print["S95 blocked: inherited locked-input preflight failed."];Abort[]];
s94hR3CertificatePath95="E:/engine_wolf/TCCT_S94H_R3_IndependentFullQueryConfirmation.json";
frozenCandidatePath95="E:/engine_wolf/TCCT_S94H_FrozenFullQueryReadout.wxf";
resultCertificatePath95="E:/engine_wolf/TCCT_S95_StrictBlindCertificate.json";
checkpointDirectory95="E:/engine_wolf/TCCT_S95_Blind_Checkpoints";
precommitPath95=FileNameJoin[{{Directory[],"TCCT_S95_Precommit.json"}}];
testDefinitionPath95=FileNameJoin[{{Directory[],"TCCT_S95_TestDefinitions.wl"}}];
expectedPrecommitFileHash95="{precommit_hash}";
expectedTestDefinitionFileHash95="{test_def_hash}";
expectedS94HR3CertificateFileHash95="{s94h_cert_hash}";
expectedS94HR3ResultHash95="{EXPECTED_S94H_RESULT_HASH}";
expectedCandidateObjectHash95="{EXPECTED_CANDIDATE_OBJECT_HASH}";
expectedCandidateFileHash95="{EXPECTED_CANDIDATE_FILE_HASH}";
If[FileExistsQ[resultCertificatePath95]&&FileByteCount[resultCertificatePath95]>0,
Print["S95 blocked: a prior S95 certificate exists. Preserve it."];Abort[]];
requiredFiles95={{s94hR3CertificatePath95,frozenCandidatePath95,
precommitPath95,testDefinitionPath95}};
If[!And@@(FileExistsQ/@requiredFiles95),
Print["S95 blocked: one or more locked inputs are missing."];
Dataset[AssociationThread[requiredFiles95,FileExistsQ/@requiredFiles95]];Abort[]];
s94hR3Certificate95=Quiet@Check[Import[s94hR3CertificatePath95,"RawJSON"],$Failed];
precommit95=Quiet@Check[Import[precommitPath95,"RawJSON"],$Failed];
candidateReloaded95=Quiet@Check[Import[frozenCandidatePath95,"WXF"],$Failed];
candidateObjectHash95=If[AssociationQ[candidateReloaded95],
Hash[Normal@KeyDrop[candidateReloaded95,{{"CandidateHash"}}],"SHA256","HexString"],
Missing["CandidateNotLoaded"]];
lockChecks95=<|
"S94HCertificateAssociation"->AssociationQ[s94hR3Certificate95],
"PrecommitAssociation"->AssociationQ[precommit95],
"CandidateAssociation"->AssociationQ[candidateReloaded95],
"S94HCertificateFileHash"->SameQ[FileSHA256Hex94H[s94hR3CertificatePath95],
expectedS94HR3CertificateFileHash95],
"S94HResultHash"->SameQ[s94hR3Certificate95["ResultHash"],
expectedS94HR3ResultHash95],
"S94HOutcome"->SameQ[s94hR3Certificate95["Outcome"],
"S94H_INDEPENDENT_CONFIRMATION_PASS"],
"S94HIntegrity"->TrueQ[s94hR3Certificate95["IntegrityPassed"]],
"S94HCoreUnchanged"->SameQ[s94hR3Certificate95["CoreChanged"],False],
"CandidateFileHash"->SameQ[FileSHA256Hex94H[frozenCandidatePath95],
expectedCandidateFileHash95],
"StoredCandidateHash"->SameQ[candidateReloaded95["CandidateHash"],
expectedCandidateObjectHash95],
"RecomputedCandidateHash"->SameQ[candidateObjectHash95,
expectedCandidateObjectHash95],
"PrecommitFileHash"->SameQ[FileSHA256Hex94H[precommitPath95],
expectedPrecommitFileHash95],
"TestDefinitionFileHash"->SameQ[FileSHA256Hex94H[testDefinitionPath95],
expectedTestDefinitionFileHash95],
"PreRegistered"->TrueQ[precommit95["PreRegistered"]],
"BlindTest"->TrueQ[precommit95["BlindTest"]],
"CandidateSearchForbidden"->SameQ[precommit95["CandidateSearchAllowed"],False],
"TrainingForbidden"->SameQ[precommit95["TrainingAllowed"],False],
"PrecommitCandidateHash"->SameQ[precommit95["FrozenCandidateFileSHA256"],
expectedCandidateFileHash95]
|>;
candidateFrozenAndLocked95=And@@Values[lockChecks95];
If[!TrueQ[candidateFrozenAndLocked95],
Print["S95 blocked: frozen candidate or precommit lock failed."];
Print[InputForm[lockChecks95]];Abort[]];
modelHashBefore95=Hash[Normal[frozen75D],"SHA256","HexString"];
coreHashBefore95=Hash[CoreDefinitionBundle94H[],"SHA256","HexString"];
lockedFileHashesBefore95=FileSHA256Hex94H/@requiredFiles95;
Dataset[{{<|"Stage"->"S95","PreRegistered"->True,"BlindTest"->True,
"CandidateFrozenAndLocked"->candidateFrozenAndLocked95,
"CandidateHash"->candidateObjectHash95,"CandidateFileHash"->
FileSHA256Hex94H[frozenCandidatePath95],"CandidateSearchPerformed"->False,
"TrainingPerformed"->False,"CoreChanged"->False|>}}]
'''.strip()

scenario_setup = r'''
Get[testDefinitionPath95];
topologies95=precommit95["Topologies"];
contexts95=precommit95["Contexts"];
scales95=precommit95["Scales"];
scenarios95=Flatten[Table[<|"ScenarioIndex"->(1+(ti-1) Length[contexts95]
Length[scales95]+(ci-1) Length[scales95]+si),
"Topology"->topologies95[[ti]],"TopologyIndex"->ti,
"Context"->contexts95[[ci]],"ContextIndex"->ci,
"Depth"->scales95[[si,"Depth"]],
"BranchCount"->scales95[[si,"BranchCount"]]|>,
{ti,Length[topologies95]},{ci,Length[contexts95]},{si,Length[scales95]}],2];
scenarioShapePassed95=And[
SameQ[Length[scenarios95],precommit95["ExpectedScenarios"]],
SameQ[Total@Lookup[scenarios95,"BranchCount"],precommit95["ExpectedPairs"]],
SameQ[2 Total@Lookup[scenarios95,"BranchCount"],precommit95["ExpectedWorlds"]],
SameQ[DeleteDuplicates@Lookup[scenarios95,"Topology"],topologies95],
SameQ[DeleteDuplicates@Lookup[scenarios95,"Context"],contexts95]];
If[!TrueQ[scenarioShapePassed95],
Print["S95 blocked: pre-registered scenario shape mismatch."];Abort[]];
If[!DirectoryQ[checkpointDirectory95],
Quiet@Check[CreateDirectory[checkpointDirectory95],Null]];
If[!DirectoryQ[checkpointDirectory95],
Print["S95 blocked: checkpoint directory unavailable."];Abort[]];
protocolHash95=expectedPrecommitFileHash95;
testDefinitionHash95=expectedTestDefinitionFileHash95;
Dataset[scenarios95]
'''.strip()

checkpoint_runtime = r'''
ClearAll[CheckpointValid95,CheckpointProgress95,RunScenario95];
CheckpointValid95[obj_,idx_Integer,scenario_Association]:=And[
AssociationQ[obj],SameQ[obj["Stage"],"S95"],
SameQ[obj["ScenarioIndex"],idx],SameQ[obj["Scenario"],scenario],
SameQ[obj["CandidateHash"],candidateObjectHash95],
SameQ[obj["CandidateFileHash"],expectedCandidateFileHash95],
SameQ[obj["ProtocolHash"],protocolHash95],
SameQ[obj["TestDefinitionHash"],testDefinitionHash95],
SameQ[obj["PairCount"],scenario["BranchCount"]],
SameQ[obj["WorldCount"],2 scenario["BranchCount"]],
VectorQ[obj["Pairs"],AssociationQ],
SameQ[Length[obj["Pairs"]],scenario["BranchCount"]],
TrueQ[obj["ScenarioValidityPassed"]],
SameQ[obj["CheckpointHash"],Hash[Normal@KeyDrop[obj,{"CheckpointHash"}],
"SHA256","HexString"]]];

CheckpointProgress95[]:=Module[{paths,valid},
paths=FileNameJoin[{checkpointDirectory95,
"scenario_"<>IntegerString[#,10,2]<>".wxf"}]&/@Range[Length[scenarios95]];
valid=MapThread[Function[{path,idx},If[FileExistsQ[path]&&FileByteCount[path]>0,
With[{obj=Quiet@Check[Import[path,"WXF"],$Failed]},
TrueQ[CheckpointValid95[obj,idx,scenarios95[[idx]]]]],False]],
{paths,Range[Length[paths]]}];
<|"Completed"->Count[valid,True],"Expected"->Length[scenarios95],
"CompletedScenarioIndices"->Pick[Range[Length[scenarios95]],valid,True],
"RemainingScenarioIndices"->Pick[Range[Length[scenarios95]],valid,False],
"CandidateSearchPerformed"->False,"TrainingPerformed"->False|>];

RunScenario95[idx_Integer]:=Module[
{scenario,path,existing,elapsed,pairs,validity,payload,checkpoint,
exportResult,reloaded},
scenario=scenarios95[[idx]];
path=FileNameJoin[{checkpointDirectory95,
"scenario_"<>IntegerString[idx,10,2]<>".wxf"}];
If[FileExistsQ[path]&&FileByteCount[path]>0,
existing=Quiet@Check[Import[path,"WXF"],$Failed];
If[TrueQ[CheckpointValid95[existing,idx,scenario]],
Return[<|"ScenarioIndex"->idx,"Status"->"VALID_CHECKPOINT_REUSED",
"Scenario"->scenario,"PairCount"->existing["PairCount"],
"ElapsedSeconds"->existing["ElapsedSeconds"],
"Progress"->CheckpointProgress95[]|>],
Print["S95 blocked: existing checkpoint failed validation: ",path];Abort[]]];
{elapsed,pairs}=AbsoluteTiming[Table[Pair95[scenario,answer],
{answer,scenario["BranchCount"]}]];
validity=And[VectorQ[pairs,AssociationQ],
SameQ[Length[pairs],scenario["BranchCount"]],
And@@Lookup[pairs,"ReferenceActionsCorrect",False],
And@@Lookup[pairs,"WorldsValid",False],
And@@Map[Abs[#Score+#ReverseScore]<10^-12&,pairs]];
If[!TrueQ[validity],
Print["S95 blocked: scenario validity failed before export: ",idx];Abort[]];
payload=<|"Stage"->"S95","ScenarioIndex"->idx,"Scenario"->scenario,
"Pairs"->pairs,"PairCount"->Length[pairs],"WorldCount"->2 Length[pairs],
"ElapsedSeconds"->elapsed,"ScenarioValidityPassed"->validity,
"CandidateHash"->candidateObjectHash95,
"CandidateFileHash"->expectedCandidateFileHash95,
"ProtocolHash"->protocolHash95,"TestDefinitionHash"->testDefinitionHash95,
"CandidateSearchPerformed"->False,"TrainingPerformed"->False,
"CoreChanged"->False,"RulesChanged"->False|>;
checkpoint=Append[payload,"CheckpointHash"->
Hash[Normal[payload],"SHA256","HexString"]];
exportResult=Quiet@Check[Export[path,checkpoint,"WXF"],$Failed];
If[!StringQ[exportResult]||!FileExistsQ[path]||FileByteCount[path]<=0,
Print["S95 blocked: checkpoint export failed: ",idx];Abort[]];
reloaded=Quiet@Check[Import[path,"WXF"],$Failed];
If[!TrueQ[CheckpointValid95[reloaded,idx,scenario]],
Print["S95 blocked: checkpoint reload validation failed: ",idx];Abort[]];
<|"ScenarioIndex"->idx,"Status"->"CHECKPOINT_EXPORTED",
"Scenario"->scenario,"PairCount"->Length[pairs],
"ElapsedSeconds"->elapsed,"Progress"->CheckpointProgress95[]|>
];
Dataset[{CheckpointProgress95[]}]
'''.strip()

merge = r'''
checkpointPaths95=FileNameJoin[{checkpointDirectory95,
"scenario_"<>IntegerString[#,10,2]<>".wxf"}]&/@Range[Length[scenarios95]];
If[!And@@Map[FileExistsQ[#]&&FileByteCount[#]>0&,checkpointPaths95],
Print["S95 final merge blocked: checkpoints are incomplete."];Abort[]];
checkpoints95=Quiet@Check[Import[#,"WXF"]&/@checkpointPaths95,$Failed];
checkpointSetValidityPassed95=And@@MapThread[
CheckpointValid95[#1,#2,scenarios95[[#2]]]&,{checkpoints95,Range[Length[scenarios95]]}];
If[!TrueQ[checkpointSetValidityPassed95],
Print["S95 final merge blocked: checkpoint validation failed."];Abort[]];
pairs95=Flatten[Lookup[checkpoints95,"Pairs"],1];
axisGroups95=Flatten[Map[Function[axis,Map[Function[value,Module[{rows,correct},
rows=Select[pairs95,SameQ[Lookup[#,axis],value]&];
correct=Count[rows,p_/;TrueQ[p["PairCorrect"]]];
<|"Axis"->axis,"Value"->ToString[value],"Pairs"->Length[rows],
"Correct"->correct,"Accuracy"->N[correct/Length[rows]],
"MinimumMargin"->Min@Lookup[rows,"Score"]|>]],
DeleteDuplicates@Lookup[pairs95,axis]]],
{"Topology","Context","Depth","BranchCount","Answer"}],1];
accuracy95=N[Count[pairs95,p_/;TrueQ[p["PairCorrect"]]]/Length[pairs95]];
worstAxisGroupAccuracy95=Min@Lookup[axisGroups95,"Accuracy"];
validityPassed95=And[checkpointSetValidityPassed95,
SameQ[Length[scenarios95],precommit95["ExpectedScenarios"]],
SameQ[Length[pairs95],precommit95["ExpectedPairs"]],
SameQ[Total@Lookup[checkpoints95,"WorldCount"],precommit95["ExpectedWorlds"]],
And@@Lookup[pairs95,"ReferenceActionsCorrect",False],
And@@Lookup[pairs95,"WorldsValid",False],
And@@Map[Abs[#Score+#ReverseScore]<10^-12&,pairs95]];
criterionPassed95=And[validityPassed95,
accuracy95>=precommit95["PassAccuracy"],
worstAxisGroupAccuracy95>=precommit95["PassWorstAxisGroupAccuracy"]];
modelHashAfter95=Hash[Normal[frozen75D],"SHA256","HexString"];
coreHashAfter95=Hash[CoreDefinitionBundle94H[],"SHA256","HexString"];
lockedFileHashesAfter95=FileSHA256Hex94H/@requiredFiles95;
integrityPassed95=And[SameQ[modelHashBefore95,modelHashAfter95],
SameQ[coreHashBefore95,coreHashAfter95],
SameQ[lockedFileHashesBefore95,lockedFileHashesAfter95],
SameQ[FileSHA256Hex94H[frozenCandidatePath95],expectedCandidateFileHash95],
SameQ[candidateObjectHash95,expectedCandidateObjectHash95]];
payload95=<|"Stage"->"S95","Name"->"PreRegisteredStrictBlindTest",
"PreRegistered"->True,"BlindTest"->True,"ExecutionMode"->"CheckpointedResumableGUI",
"CandidateFrozenBeforeProtocol"->True,"CandidateFrozenBeforeDataGeneration"->True,
"CandidateSearchPerformed"->False,"CandidateReexported"->False,
"TrainingPerformed"->False,"CheckpointCount"->Length[checkpoints95],
"CheckpointSetValidityPassed"->checkpointSetValidityPassed95,
"CandidateHash"->candidateObjectHash95,
"CandidateFileHash"->expectedCandidateFileHash95,
"LockedS94HR3ResultHash"->expectedS94HR3ResultHash95,
"PrecommitFileHash"->expectedPrecommitFileHash95,
"TestDefinitionFileHash"->expectedTestDefinitionFileHash95,
"Topologies"->topologies95,"Contexts"->contexts95,"Scales"->scales95,
"Scenarios"->Length[scenarios95],"Pairs"->Length[pairs95],
"Worlds"->Total@Lookup[checkpoints95,"WorldCount"],
"CorrectPairs"->Count[pairs95,p_/;TrueQ[p["PairCorrect"]]],
"Accuracy"->accuracy95,"WorstAxisGroupAccuracy"->worstAxisGroupAccuracy95,
"MinimumMargin"->Min@Lookup[pairs95,"Score"],
"ZeroScores"->Count[pairs95,p_/;TrueQ[p["ZeroScore"]]],
"TotalScenarioSeconds"->Total@Lookup[checkpoints95,"ElapsedSeconds"],
"AxisGroups"->axisGroups95,"BlindValidityPassed"->validityPassed95,
"BlindCriterionPassed"->criterionPassed95,"IntegrityPassed"->integrityPassed95,
"CoreChanged"->!SameQ[coreHashBefore95,coreHashAfter95],
"OriginalFrozenModelChanged"->!SameQ[modelHashBefore95,modelHashAfter95],
"RulesChanged"->False,"DeduplicationMechanismChanged"->False,
"UndirectedFreezeMechanismChanged"->False,
"Outcome"->Which[!TrueQ[integrityPassed95],"S95_INTEGRITY_FAILURE",
!TrueQ[validityPassed95],"S95_INVALID_BLIND_TEST",
TrueQ[criterionPassed95],"S95_STRICT_BLIND_PASS",True,"S95_STRICT_BLIND_FAIL"]|>;
resultHash95=Hash[Normal[payload95],"SHA256","HexString"];
certificate95=Append[payload95,"ResultHash"->resultHash95];
exportResult95=Quiet@Check[Export[resultCertificatePath95,certificate95,"RawJSON"],$Failed];
If[!StringQ[exportResult95]||!FileExistsQ[resultCertificatePath95]||
FileByteCount[resultCertificatePath95]<=0,
Print["S95 failed to export the final certificate."];Abort[]];
Dataset[{KeyTake[certificate95,{"Stage","Name","PreRegistered","BlindTest",
"Scenarios","Pairs","Worlds","CorrectPairs","Accuracy",
"WorstAxisGroupAccuracy","MinimumMargin","ZeroScores","BlindValidityPassed",
"BlindCriterionPassed","IntegrityPassed","CoreChanged",
"OriginalFrozenModelChanged","RulesChanged","DeduplicationMechanismChanged",
"UndirectedFreezeMechanismChanged","CandidateSearchPerformed",
"TrainingPerformed","Outcome","ResultHash"}]}]
'''.strip()

cells = [{
    "cell_type": "markdown",
    "id": "s95-intro",
    "metadata": {},
    "source": [
        "# TCCT S95 - Pre-Registered Strict Blind Test\n",
        "\n",
        "Run with **Kernel -> Restart Kernel and Run All Cells**.\n",
        "\n",
        "The S94H candidate, S95 protocol, test-definition file, axes and pass thresholds are hash-locked before any S95 world is generated. Each scenario is checkpointed.\n",
        "\n",
        "No training, candidate search, candidate re-export, core change, rule change, deduplication change, or undirected-freeze change is permitted.\n",
    ],
}]
for idx, setup in enumerate(setup_cells, 1):
    cells.append(code_cell(setup, f"s95-locked-setup-{idx}"))
cells.append(code_cell(candidate_lock, "s95-precommit-and-candidate-lock"))
cells.append(code_cell(scenario_setup, "s95-blind-scenario-generation"))
cells.append(code_cell(checkpoint_runtime, "s95-checkpoint-runtime"))
for idx in range(1, 13):
    cells.append(code_cell(f"Dataset[{{RunScenario95[{idx}]}}]", f"s95-scenario-{idx:02d}"))
cells.append(code_cell(merge, "s95-final-merge"))

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Wolfram Language 15",
                       "language": "Wolfram Language", "name": "wolframlanguage15"},
        "language_info": {"file_extension": ".wl",
                          "mimetype": "application/vnd.wolfram.mathematica",
                          "name": "Wolfram Language", "version": "15.0"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
NOTEBOOK.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
all_code = "\n\n".join("".join(cell["source"]) for cell in cells if cell["cell_type"] == "code")
SOURCE.write_text(all_code, encoding="utf-8")
PREFLIGHT_SOURCE.write_text(
    "\n\n".join(setup_cells + [candidate_lock, scenario_setup, r'''
Print[InputForm[<|
"Stage"->"S95","PreflightOnly"->True,
"CandidateFrozenAndLocked"->candidateFrozenAndLocked95,
"ScenarioShapePassed"->scenarioShapePassed95,
"Scenarios"->Length[scenarios95],
"Pairs"->Total@Lookup[scenarios95,"BranchCount"],
"Worlds"->2 Total@Lookup[scenarios95,"BranchCount"],
"Topologies"->DeleteDuplicates@Lookup[scenarios95,"Topology"],
"Contexts"->DeleteDuplicates@Lookup[scenarios95,"Context"],
"S95WorldsExecuted"->0,"CandidateSearchPerformed"->False,
"TrainingPerformed"->False,"CoreChanged"->False,"RulesChanged"->False|>]];
Quit[];
'''.strip()]),
    encoding="utf-8",
)

LAUNCHER.write_text(
    '@echo off\nchcp 65001 >nul\nsetlocal\n'
    'set "TCCT_DIR=%~dp0"\n'
    'set "TCCT_NOTEBOOK=%TCCT_DIR%TCCT_S95_StrictBlind.ipynb"\n'
    'set "JUPYTER_LAB=E:\\anaconda\\Scripts\\jupyter-lab.exe"\n'
    'set "JUPYTER_DATA_DIR=E:\\engine_wolf\\jupyter\\data"\n'
    'set "JUPYTER_CONFIG_DIR=%TCCT_DIR%.jupyter_config_s95"\n'
    'set "JUPYTER_RUNTIME_DIR=%TCCT_DIR%.jupyter_runtime_s95"\n'
    'set "PYTHONUTF8=1"\n'
    'if not exist "%JUPYTER_LAB%" (echo JupyterLab not found & pause & exit /b 1)\n'
    'if not exist "%TCCT_NOTEBOOK%" (echo S95 notebook not found & pause & exit /b 1)\n'
    'if not exist "%JUPYTER_CONFIG_DIR%" mkdir "%JUPYTER_CONFIG_DIR%"\n'
    'if not exist "%JUPYTER_RUNTIME_DIR%" mkdir "%JUPYTER_RUNTIME_DIR%"\n'
    'start "TCCT S95 JupyterLab" /min "%JUPYTER_LAB%" "%TCCT_NOTEBOOK%" '
    '--ServerApp.root_dir="%TCCT_DIR%" --ServerApp.port=8896 --ServerApp.port_retries=5\n'
    'exit /b 0\n',
    encoding="utf-8",
)

record = {
    "Stage": "S95",
    "PrecommitSHA256": precommit_hash,
    "TestDefinitionSHA256": test_def_hash,
    "NotebookSHA256": sha256(NOTEBOOK),
    "SourceSHA256": sha256(SOURCE),
    "PreflightSourceSHA256": sha256(PREFLIGHT_SOURCE),
    "LauncherSHA256": sha256(LAUNCHER),
    "S94HR3CertificateSHA256": s94h_cert_hash,
    "FrozenCandidateSHA256": EXPECTED_CANDIDATE_FILE_HASH,
    "S95WorldsExecutedDuringBuild": 0,
}
BUILD_RECORD.write_text(json.dumps(record, indent=2), encoding="utf-8")
for path in (TEST_DEFINITIONS, PRECOMMIT, NOTEBOOK, SOURCE,
             PREFLIGHT_SOURCE, LAUNCHER, BUILD_RECORD):
    print(path.name, path.stat().st_size, sha256(path))
