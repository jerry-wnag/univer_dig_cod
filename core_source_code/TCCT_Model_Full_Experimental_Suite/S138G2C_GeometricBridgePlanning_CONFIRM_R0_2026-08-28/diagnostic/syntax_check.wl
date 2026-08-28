source = FileNameJoin[{DirectoryName[DirectoryName[$InputFileName]], "source", "run_geometric_bridge_planning.wl"}];
held = Quiet@Check[ToExpression[Import[source, "Text"], InputForm, HoldComplete], $Failed];
If[held === $Failed, Print["WOLFRAM_SYNTAX_CHECK=FAIL"]; Exit[1],
  Print["WOLFRAM_SYNTAX_CHECK=PASS"]; Exit[0]];
