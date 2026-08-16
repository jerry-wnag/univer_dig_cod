(* S74 CELL *)
ClearAll["Global`*74"];

frozenModel74=<|
"Params"->{0,-1,1,-1,-1,0},
"K"->5,
"Policy"->{1,4}
|>;

radii74={2,3,4};

expectedAccuracy73=<|
"ParallelOut"->0.25,
"DiamondIn"->0.5,
"SharedParallelIn"->0.875
|>;

modelLock74=SameQ[
frozenModel74,
frozenModel73,
frozenModel72,
frozen71
];

s73ResultLock74=And[
TrueQ[preflightPass73],
SameQ[auditCert73["CasesAudited"],96],
And@@MapThread[
Abs[#1-#2]<10^-12&,
{
Lookup[auditCert73["AccuracyByTopology"],topologies72],
Lookup[expectedAccuracy73,topologies72]
}
]
];

preflightPass74=And[
modelLock74,
s73ResultLock74
];

preflight74=<|
"Stage"->"S74",
"Name"->"LayerAttributionAudit",
"AuditOnly"->True,
"CoreTCCTChanged"->False,
"ModelChanged"->False,
"RetuningAllowed"->False,
"NewModelSearch"->False,
"ModelMatchesS71S72S73"->modelLock74,
"S73ResultMatches"->s73ResultLock74,
"RadiiAudited"->radii74,
"HigherRadiusScoresAreDiagnosticOnly"->True,
"PreflightPassed"->preflightPass74
|>;

Dataset[{preflight74}]

(* S74 CELL *)
ClearAll[
StateKey74,
BuildRadiusRows74,
LayerMetrics74,
FrozenPolicyScore74,
LayerAudit74
];

StateKey74[state_]:=Hash[
state,
"SHA256",
"HexString"
];

BuildRadiusRows74[
topology_String,
radius_Integer
]:=Flatten[
Table[
Module[{states,rawKeys,codes},
states=DecisionStates64[
Case72[topology,depth,answer,target],
radius
];
rawKeys=DeleteDuplicates[StateKey74/@states];
codes=DeleteDuplicates[
CodeState70D[
#,
frozenModel74["Params"],
frozenModel74["K"]
]&/@states
];
<|
"Topology"->topology,
"Radius"->radius,
"Depth"->depth,
"Answer"->answer,
"Target"->target,
"RawKeys"->rawKeys,
"Codes"->codes
|>
],
{depth,depths72},
{answer,answers72},
{target,targets72}
],
2
];

LayerMetrics74[
rows_List,
field_String
]:=Module[
{continueRows,stopRows,continueUniverse,stopUniverse,
shared,oracleSelected,score},
continueRows=Select[rows,# ["Target"]==="Continue"&];
stopRows=Select[rows,# ["Target"]==="Stop"&];
continueUniverse=Union@@Lookup[continueRows,field];
stopUniverse=Union@@Lookup[stopRows,field];
shared=Intersection[
continueUniverse,
stopUniverse
];
oracleSelected=Complement[
continueUniverse,
stopUniverse
];
score=Total[
Map[
Function[row,
Module[{prediction,truth},
prediction=AnyTrue[
row[field],
MemberQ[oracleSelected,#]&
];
truth=row["Target"]==="Continue";
Boole[SameQ[prediction,truth]]
]
],
rows
]
];
<|
"ContinueUniverse"->continueUniverse,
"StopUniverse"->stopUniverse,
"SharedSymbols"->shared,
"OracleSelected"->oracleSelected,
"DistinctSymbols"->Length@Union[
continueUniverse,
stopUniverse
],
"SharedCount"->Length[shared],
"OracleSelectedCount"->Length[oracleSelected],
"OracleScore"->score
|>
];

FrozenPolicyScore74[rows_List]:=Total[
Map[
Function[row,
Module[{prediction,truth},
prediction=AnyTrue[
row["Codes"],
MemberQ[frozenModel74["Policy"],#]&
];
truth=row["Target"]==="Continue";
Boole[SameQ[prediction,truth]]
]
],
rows
]
];

LayerAudit74[
topology_String,
radius_Integer
]:=Module[
{rows,rawMetrics,latentMetrics,frozenScore,failureLayer},
rows=BuildRadiusRows74[topology,radius];
rawMetrics=LayerMetrics74[rows,"RawKeys"];
latentMetrics=LayerMetrics74[rows,"Codes"];
frozenScore=FrozenPolicyScore74[rows];
failureLayer=Which[
rawMetrics["OracleScore"]<32,
"OuterRawRepresentation",
latentMetrics["OracleScore"]<32,
"LatentEncoderCompression",
frozenScore<32,
"FrozenPolicySemanticAlignment",
True,
"None"
];
<|
"Topology"->topology,
"Radius"->radius,
"Cases"->Length[rows],
"RawDistinctStates"->rawMetrics["DistinctSymbols"],
"RawSharedStates"->rawMetrics["SharedCount"],
"RawOracleSelectedStates"->rawMetrics["OracleSelectedCount"],
"RawOracleScore"->rawMetrics["OracleScore"],
"LatentDistinctCodes"->latentMetrics["DistinctSymbols"],
"LatentSharedCodes"->latentMetrics["SharedCount"],
"LatentOracleSelectedCodes"->latentMetrics["OracleSelectedCount"],
"LatentOracleScore"->latentMetrics["OracleScore"],
"FrozenPolicyScore"->frozenScore,
"FirstFailureLayer"->failureLayer
|>
];

(* S74 CELL *)
layerAuditRows74=If[
TrueQ[preflightPass74],
Flatten[
Table[
LayerAudit74[topology,radius],
{topology,topologies72},
{radius,radii74}
],
1
],
{}
];

Dataset[layerAuditRows74]

(* S74 CELL *)
ClearAll[MinimalPerfectRadius74];

MinimalPerfectRadius74[
topology_String,
scoreField_String
]:=Module[{matching},
matching=Select[
layerAuditRows74,
# ["Topology"]===topology&&# [scoreField]===32&
];
If[
Length[matching]>0,
Min[Lookup[matching,"Radius"]],
Missing["NotPerfectThroughRadius4"]
]
];

attributionSummary74=Map[
Function[topology,
Module[{radius2,radius3,radius4},
radius2=SelectFirst[
layerAuditRows74,
# ["Topology"]===topology&&# ["Radius"]===2&
];
radius3=SelectFirst[
layerAuditRows74,
# ["Topology"]===topology&&# ["Radius"]===3&
];
radius4=SelectFirst[
layerAuditRows74,
# ["Topology"]===topology&&# ["Radius"]===4&
];
<|
"Topology"->topology,
"S72FrozenScore"->radius2["FrozenPolicyScore"],
"Radius2RawOracle"->radius2["RawOracleScore"],
"Radius2LatentOracle"->radius2["LatentOracleScore"],
"Radius2FailureLayer"->radius2["FirstFailureLayer"],
"Radius3RawOracle"->radius3["RawOracleScore"],
"Radius3LatentOracle"->radius3["LatentOracleScore"],
"Radius3FrozenPolicy"->radius3["FrozenPolicyScore"],
"Radius4RawOracle"->radius4["RawOracleScore"],
"Radius4LatentOracle"->radius4["LatentOracleScore"],
"Radius4FrozenPolicy"->radius4["FrozenPolicyScore"],
"MinimalRawPerfectRadius"->MinimalPerfectRadius74[
topology,
"RawOracleScore"
],
"MinimalLatentPerfectRadius"->MinimalPerfectRadius74[
topology,
"LatentOracleScore"
]
|>
]
],
topologies72
];

Dataset[attributionSummary74]

(* S74 CELL *)
radiusScoreSummary74=Map[
Function[topology,
Module[{sub},
sub=Select[
layerAuditRows74,
# ["Topology"]===topology&
];
<|
"Topology"->topology,
"RawOracleByRadius"->AssociationThread[
Lookup[sub,"Radius"],
Lookup[sub,"RawOracleScore"]
],
"LatentOracleByRadius"->AssociationThread[
Lookup[sub,"Radius"],
Lookup[sub,"LatentOracleScore"]
],
"FrozenPolicyByRadius"->AssociationThread[
Lookup[sub,"Radius"],
Lookup[sub,"FrozenPolicyScore"]
],
"FailureLayerByRadius"->AssociationThread[
Lookup[sub,"Radius"],
Lookup[sub,"FirstFailureLayer"]
]
|>
]
],
topologies72
];

Dataset[radiusScoreSummary74]

(* S74 CELL *)
cert74=<|
"Stage"->"S74",
"Name"->"LayerAttributionAudit",
"AuditOnly"->True,
"CoreTCCTChanged"->False,
"ModelChanged"->False,
"RetuningAllowed"->False,
"PreflightPassed"->preflightPass74,
"FrozenModel"->frozenModel74,
"RadiiAudited"->radii74,
"HigherRadiusScoresAreDiagnosticOnly"->True,
"CasesPerTopologyPerRadius"->32,
"AttributionSummary"->AssociationThread[
topologies72,
KeyDrop[attributionSummary74,"Topology"]
]
|>;

Dataset[{cert74}]
