(* S72 CELL *)
ClearAll["Global`*72"];

frozenModel72=<|
"Params"->{0,-1,1,-1,-1,0},
"K"->5,
"Policy"->{1,4}
|>;

topologies72={
"ParallelOut",
"DiamondIn",
"SharedParallelIn"
};

depths72={2,5,9,15};
answers72=Range[4];
targets72={"Continue","Stop"};

protocol72=<|
"Stage"->"S72",
"Name"->"FrozenTopologyBattery",
"ProtocolFrozenBeforeEvaluation"->True,
"ModelFrozenBeforeEvaluation"->True,
"Model"->frozenModel72,
"Topologies"->topologies72,
"Depths"->depths72,
"Answers"->answers72,
"Targets"->targets72,
"Radius"->2,
"CasesPerTopology"->32,
"TotalCases"->96,
"S72UsedForSelection"->False,
"RetuningAllowed"->False
|>;

protocolHash72=Hash[
Normal[protocol72],
"SHA256",
"HexString"
];

modelLock72=SameQ[
frozenModel72,
frozen71
];

Dataset[{
Join[
KeyDrop[protocol72,"Model"],
<|
"ProtocolHash"->protocolHash72,
"ModelMatchesS71"->modelLock72
|>
]
}]

(* S72 CELL *)
ClearAll[
ParallelOut72,
DiamondIn72,
SharedParallelIn72,
Case72
];

ParallelOut72[c_List]:=Module[
{x=c[[1]],a=c[[2]],e,f,mx,next,new,m,outs,rm,
add,g1,g2,i,j},
e=x[[1]];
f=x[[6]];
mx=Max@Flatten[List@@@e];
next=mx+1;
new=e;
Do[
m=f[[i]];
outs=Cases[
new,
DirectedEdge[u_,v_]/;u===m:>{u,v}
];
rm=DirectedEdge@@@outs;
add={};
Do[
g1=next;
g2=next+1;
next=next+2;
add=Join[
add,
{
DirectedEdge[m,g1],
DirectedEdge[g1,outs[[j,2]]],
DirectedEdge[m,g2],
DirectedEdge[g2,outs[[j,2]]]
}
],
{j,Length[outs]}
];
new=Join[
Complement[new,rm],
add
],
{i,Length[f]}
];
{{
Union[new],
x[[2]],x[[3]],x[[4]],x[[5]],x[[6]]
},a}
];

DiamondIn72[c_List]:=Module[
{x=c[[1]],a=c[[2]],e,f,mx,next,new,m,incs,rm,
add,s1,s2,g,i,j},
e=x[[1]];
f=x[[6]];
mx=Max@Flatten[List@@@e];
next=mx+1;
new=e;
Do[
m=f[[i]];
incs=Cases[
new,
DirectedEdge[u_,v_]/;v===m:>{u,v}
];
rm=DirectedEdge@@@incs;
add={};
Do[
s1=next;
s2=next+1;
g=next+2;
next=next+3;
add=Join[
add,
{
DirectedEdge[incs[[j,1]],s1],
DirectedEdge[incs[[j,1]],s2],
DirectedEdge[s1,g],
DirectedEdge[s2,g],
DirectedEdge[g,m]
}
],
{j,Length[incs]}
];
new=Join[
Complement[new,rm],
add
],
{i,Length[f]}
];
{{
Union[new],
x[[2]],x[[3]],x[[4]],x[[5]],x[[6]]
},a}
];

SharedParallelIn72[c_List]:=Module[
{x=c[[1]],a=c[[2]],e,f,mx,next,new,m,ps,rm,
g1,g2,add,i},
e=x[[1]];
f=x[[6]];
mx=Max@Flatten[List@@@e];
next=mx+1;
new=e;
Do[
m=f[[i]];
ps=Cases[
new,
DirectedEdge[u_,v_]/;v===m:>u
];
rm=(DirectedEdge[#,m]&)/@ps;
g1=next;
g2=next+1;
next=next+2;
add=Join[
Flatten[
Table[
{
DirectedEdge[ps[[j]],g1],
DirectedEdge[ps[[j]],g2]
},
{j,Length[ps]}
],
1
],
{
DirectedEdge[g1,m],
DirectedEdge[g2,m]
}
];
new=Join[
Complement[new,rm],
add
],
{i,Length[f]}
];
{{
Union[new],
x[[2]],x[[3]],x[[4]],x[[5]],x[[6]]
},a}
];

Case72[
topology_String,
d_Integer,
a_Integer,
t_String
]:=Switch[
topology,
"ParallelOut",
ParallelOut72[Case59[d,a,t]],
"DiamondIn",
DiamondIn72[Case59[d,a,t]],
"SharedParallelIn",
SharedParallelIn72[Case59[d,a,t]],
_,
$Failed
];

(* S72 CELL *)
ClearAll[TopologyAudit72];

TopologyAudit72[topology_String]:=Module[
{base,changed,baseEdges,newEdges},
base=Case59[2,1,"Continue"];
changed=Case72[topology,2,1,"Continue"];
baseEdges=base[[1,1]];
newEdges=changed[[1,1]];
<|
"Topology"->topology,
"ShapeOK"->MatchQ[changed,{{_List,_List,_Integer,_List,_List,_List},_Integer}],
"MetadataPreserved"->SameQ[
changed[[1,2;;6]],
base[[1,2;;6]]
],
"AnswerPreserved"->SameQ[changed[[2]],base[[2]]],
"DirectedEdgesOnly"->AllTrue[
newEdges,
MatchQ[#,DirectedEdge[_,_]]&
],
"EdgeCountBefore"->Length[baseEdges],
"EdgeCountAfter"->Length[newEdges],
"EdgeCountIncreased"->Length[newEdges]>Length[baseEdges]
|>
];

audit72=TopologyAudit72/@topologies72;

auditPass72=And@@Flatten[
Lookup[
audit72,
{
"ShapeOK",
"MetadataPreserved",
"AnswerPreserved",
"DirectedEdgesOnly",
"EdgeCountIncreased"
}
]
];

Dataset[audit72]

(* S72 CELL *)
spec72=Tuples[{
topologies72,
depths72,
answers72,
targets72
}];

testRows72=Map[
Function[spec,
<|
"Grammar"->spec[[1]],
"Depth"->spec[[2]],
"Answer"->spec[[3]],
"Target"->spec[[4]],
"States"->DecisionStates64[
Case72@@spec,
protocol72["Radius"]
]
|>
],
spec72
];

caseBuildCert72=<|
"ExpectedCases"->protocol72["TotalCases"],
"BuiltCases"->Length[testRows72],
"CasesByTopology"->Counts[Lookup[testRows72,"Grammar"]],
"CasesByTarget"->Counts[Lookup[testRows72,"Target"]],
"AuditPassed"->auditPass72,
"ModelLockPassed"->modelLock72
|>;

Dataset[{caseBuildCert72}]

(* S72 CELL *)
encodedRows72=If[
TrueQ[modelLock72]&&TrueQ[auditPass72],
EncodeRows69[
testRows72,
frozenModel72["Params"],
frozenModel72["K"]
],
$Failed
];

caseResults72=If[
ListQ[encodedRows72],
Map[
Function[row,
Module[{prediction},
prediction=If[
AnyTrue[
row["Codes"],
MemberQ[frozenModel72["Policy"],#]&
],
"Continue",
"Stop"
];
Join[
row,
<|
"Prediction"->prediction,
"Passed"->Boole[prediction===row["Target"]]
|>
]
]
],
encodedRows72
],
{}
];

scoresByTopology72=GroupBy[
caseResults72,
# ["Grammar"]&,
Total[Lookup[#,"Passed"]]&
];

scoresByTopologyTarget72=GroupBy[
caseResults72,
{# ["Grammar"],# ["Target"]}&,
Total[Lookup[#,"Passed"]]&
];

scoresByTopologyDepth72=GroupBy[
caseResults72,
{# ["Grammar"],# ["Depth"]}&,
Total[Lookup[#,"Passed"]]&
];

(* S72 CELL *)
cert72=<|
"Stage"->"S72",
"Name"->"FrozenTopologyBattery",
"ProtocolHash"->protocolHash72,
"ProtocolFrozenBeforeEvaluation"->True,
"ModelFrozenBeforeEvaluation"->True,
"S72UsedForSelection"->False,
"RetuningAllowed"->False,
"Model"->frozenModel72,
"Topologies"->topologies72,
"Cases"->Length[caseResults72],
"ScoresByTopology"->scoresByTopology72,
"ScoresByTopologyTarget"->scoresByTopologyTarget72,
"AllTopologiesPerfect"->And@@MapThread[
SameQ,
{
Lookup[scoresByTopology72,topologies72],
ConstantArray[protocol72["CasesPerTopology"],Length[topologies72]]
}
],
"TotalPassed"->Total[Lookup[caseResults72,"Passed"]],
"Accuracy"->N[Mean[Lookup[caseResults72,"Passed"]]]
|>;

Dataset[{cert72}]

(* S72 CELL *)
Dataset[
Map[
Function[row,
KeyTake[
row,
{
"Grammar",
"Depth",
"Answer",
"Target",
"Prediction",
"Passed"
}
]
],
Select[caseResults72,# ["Passed"]==0&]
]
]

(* S72 CELL *)
BarChart[
Lookup[scoresByTopology72,topologies72],
ChartLabels->Placed[topologies72,Below],
PlotRange->{0,protocol72["CasesPerTopology"]},
AxesLabel->{"Blind topology","Passed cases"},
PlotLabel->"S72 frozen-model blind topology battery",
ImageSize->Large
]
