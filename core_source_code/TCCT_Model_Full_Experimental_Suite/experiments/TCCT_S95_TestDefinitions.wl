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
