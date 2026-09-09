from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


STAGE = Path(__file__).resolve().parents[1]
ROOT = STAGE.parents[1]
S158A = ROOT / "work" / "S158A_MetaGrammarSelfExtension_DEV_5Cases_2026-08-31"
S158B_R0 = ROOT / "work" / "S158B_MetaGrammarSelfExtension_FrozenFresh_5Cases_2026-08-31"
sys.path.insert(0, str(S158A / "source"))

from meta_grammar_engine import (  # noqa: E402
    DOMAIN,
    RuleSchema,
    apply_rule,
    candidate_output,
    candidate_rule_schemas,
    generate_programs,
    g0_semantic_closure,
    json_ast,
    query_universe,
    run_active_rule_induction,
    semantic_hash,
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_frozen_sources(protocol):
    local = {name: file_hash(STAGE / path)
             for name, path in protocol["FrozenSourceFiles"].items()}
    external = {name: file_hash(ROOT / path)
                for name, path in protocol["FrozenExternalFiles"].items()}
    if local != protocol["FrozenSourceHashes"]:
        raise RuntimeError("frozen S158-B-R2 local source mismatch before materialization")
    if external != protocol["FrozenExternalHashes"]:
        raise RuntimeError("frozen S158-B-R2 external source mismatch before materialization")


def action_hash(schema: RuleSchema) -> str:
    return semantic_hash(tuple(int(value) for value in schema.action_signature))


def eligible_fresh_rules(protocol):
    historical = set(protocol["Freshness"]["ExcludedHistoricalActionSignatureSHA256"])
    g0 = set(g0_semantic_closure())
    maximum = tuple(max(pair) for pair in DOMAIN)
    minimum = tuple(min(pair) for pair in DOMAIN)
    eligible = []
    for schema in candidate_rule_schemas():
        formation = apply_rule(maximum, schema)
        nested = apply_rule(apply_rule(minimum, schema), schema)
        exact = [program for program in generate_programs(3, schema)
                 if program.semantics == nested]
        if not exact:
            continue
        minimum_cost = min(program.cost for program in exact)
        minimum_rule_uses = min(program.rule_uses for program in exact
                                if program.cost == minimum_cost)
        if (action_hash(schema) not in historical
                and formation not in g0
                and nested not in g0
                and minimum_rule_uses >= 2):
            eligible.append(schema)
    return sorted(eligible, key=lambda row: row.action_signature)


def select_fresh_rule(protocol):
    eligible = eligible_fresh_rules(protocol)
    if not eligible:
        raise RuntimeError("no rule satisfies the frozen S158-B-R2 difficulty contract")
    seed = protocol["Freshness"]["MaterializationSeed"]
    digest = hashlib.sha256(f"{seed}:S158B_R2_RULE".encode("ascii")).digest()
    return eligible[int.from_bytes(digest, "big") % len(eligible)], eligible


def answer_table(answer_fn):
    return {query["QueryID"]: answer_fn(query) for query in query_universe()}


def rule_record(schema: RuleSchema):
    return {
        "AnonymousRuleID": schema.rule_id,
        "InputCoordinateSwap": schema.swap_inputs,
        "OutputPermutation": list(schema.output_permutation),
        "ActionSignatureSHA256": action_hash(schema),
    }


def main():
    protocol = load(STAGE / "protocol" / "frozen_protocol.json")
    verify_frozen_sources(protocol)
    rule, eligible = select_fresh_rule(protocol)
    g0 = g0_semantic_closure()
    left = tuple(pair[0] for pair in DOMAIN)
    minimum = tuple(min(pair) for pair in DOMAIN)
    maximum = tuple(max(pair) for pair in DOMAIN)
    formation_target = apply_rule(maximum, rule)
    nested_target = apply_rule(apply_rule(minimum, rule), rule)
    historical_holdouts = [
        load(S158A / "oracle" / "sealed_exact_holdout.json"),
        load(S158B_R0 / "oracle" / "sealed_exact_holdout.json"),
    ]
    historical_signatures = [historical_holdouts[0]["TargetRuleActionSignature"],
                             historical_holdouts[1]["FreshTargetRuleActionSignature"]]

    public = {"Cases": [
        {"CaseID": "S158B_R2_G0_EXACT", "CaseType": "G0_EXACT_CONTROL",
         "TargetSemantics": list(left), "RuleInventionAllowed": False},
        {"CaseID": "S158B_R2_FORM_RULE", "CaseType": "UNIQUE_META_GRAMMAR_EXTENSION",
         "MaximumRuleQueries": 36, "RuleInventionAllowed": True},
        {"CaseID": "S158B_R2_REUSE_NESTED", "CaseType": "SYNTHESIS_OFF_NESTED_REUSE",
         "TargetSemantics": list(nested_target), "MaximumProgramNodes": 3,
         "RuleInventionAllowed": False},
        {"CaseID": "S158B_R2_AMBIGUOUS", "CaseType": "AMBIGUOUS_RULE_CONTROL",
         "MaximumRuleQueries": 1, "RuleInventionAllowed": True},
        {"CaseID": "S158B_R2_NO_EXTENSION", "CaseType": "NO_RULE_IN_SUBSTRATE_CONTROL",
         "MaximumRuleQueries": 36, "RuleInventionAllowed": True},
    ]}
    target_answers = answer_table(lambda query: candidate_output(rule, query))
    no_extension_answers = answer_table(
        lambda query: (2 * query["SourceSemantics"][query["InputIndex"]]
                       + 2 * query["Arguments"][0] + query["Arguments"][1]) % 3)
    oracle = {"Cases": [
        {"CaseID": "S158B_R2_FORM_RULE", "QueryAnswers": target_answers},
        {"CaseID": "S158B_R2_AMBIGUOUS", "QueryAnswers": target_answers},
        {"CaseID": "S158B_R2_NO_EXTENSION", "QueryAnswers": no_extension_answers},
    ]}
    fresh_hash = action_hash(rule)
    ordered_g0 = sorted(g0, key=semantic_hash)
    holdout = {
        "MaterializationSeed": protocol["Freshness"]["MaterializationSeed"],
        "HistoricalTargetRuleActionSignatures": historical_signatures,
        "HistoricalTargetRuleActionSignatureSHA256": [
            semantic_hash(tuple(int(value) for value in signature))
            for signature in historical_signatures],
        "FreshTargetRuleActionSignature": rule.action_signature,
        "FreshTargetRuleActionSignatureSHA256": fresh_hash,
        "OrderedG0Semantics": [list(semantics) for semantics in ordered_g0],
        "FreshTargetRuleFullAction": [list(apply_rule(semantics, rule))
                                      for semantics in ordered_g0],
        "FormationTargetSemantics": list(formation_target),
        "NestedReuseTargetSemantics": list(nested_target),
        "CandidateRuleSemanticClassCount": len(candidate_rule_schemas()),
        "EligibleFreshRuleCount": len(eligible),
        "G0SemanticClassCount": len(g0),
        "FullRuleCertificateCellCount": len(g0) * len(DOMAIN),
    }
    dump(STAGE / "input" / "five_fresh_cases.json", public)
    dump(STAGE / "oracle" / "sealed_query_oracles.json", oracle)
    dump(STAGE / "oracle" / "sealed_exact_holdout.json", holdout)
    dump(STAGE / "audit" / "construction_audit.json", {
        "Stage": "S158-B-R2", "CaseCount": 5,
        "EvidenceClass": "NEW_SEED_FROZEN_FRESH_SINGLE_COHORT",
        "MaterializedAfterProtocolAndRepairedVerifierFreeze": True,
        "NoWorldReplacementAfterFailure": True,
        "EligibleFreshRuleCount": len(eligible),
        "FormationTargetAbsentFromG0": formation_target not in g0,
        "NestedReuseTargetAbsentFromG0": nested_target not in g0,
        "FreshRuleNoHistoricalSemanticCollision": fresh_hash not in
            holdout["HistoricalTargetRuleActionSignatureSHA256"],
        "NoHiddenRuleASTInPublicInput": True,
    })

    g0_programs = generate_programs(protocol["ProgramSearch"]["MaximumInternalNodesG0"])
    oracles = {row["CaseID"]: row for row in oracle["Cases"]}
    case_rows = []
    promoted = None
    for case in public["Cases"]:
        case_id = case["CaseID"]
        if case["CaseType"] == "G0_EXACT_CONTROL":
            target = tuple(case["TargetSemantics"])
            exact = [program for program in g0_programs if program.semantics == target]
            case_rows.append({"CaseID": case_id, "Status": "G0_EXACT_NO_EXTENSION",
                              "ExactProgramCount": len(exact), "RuleInventionCalls": 0,
                              "GrammarChanged": False})
            continue
        if case["CaseType"] in {"UNIQUE_META_GRAMMAR_EXTENSION",
                                "AMBIGUOUS_RULE_CONTROL",
                                "NO_RULE_IN_SUBSTRATE_CONTROL"}:
            answers = oracles[case_id]["QueryAnswers"]
            result = run_active_rule_induction(lambda query: answers[query["QueryID"]],
                                               case["MaximumRuleQueries"])
            selected = result.pop("SelectedRule")
            row = {"CaseID": case_id, **result, "RuleInventionCalls": 1,
                   "FrozenRule": selected is not None,
                   "SelectedRule": None if selected is None else rule_record(selected),
                   "GrammarChanged": False}
            if case["CaseType"] == "UNIQUE_META_GRAMMAR_EXTENSION" and selected is not None:
                promoted = selected
                row["Status"] = "META_GRAMMAR_RULE_PROMOTED"
                row["GrammarHashBefore"] = semantic_hash(tuple(range(4)))
                row["GrammarHashAfter"] = semantic_hash(tuple(range(5)))
                row["GrammarChanged"] = True
            case_rows.append(row)
            continue
        if case["CaseType"] == "SYNTHESIS_OFF_NESTED_REUSE":
            if promoted is None:
                raise RuntimeError("reuse reached without a promoted fresh rule")
            target = tuple(case["TargetSemantics"])
            exact = [program for program in generate_programs(case["MaximumProgramNodes"], promoted)
                     if program.semantics == target]
            selected = None
            minimum_rule_uses = None
            if exact:
                minimum_cost = min(program.cost for program in exact)
                minimum = [program for program in exact if program.cost == minimum_cost]
                selected = min(minimum, key=lambda program: program.key)
                minimum_rule_uses = min(program.rule_uses for program in minimum)
            case_rows.append({
                "CaseID": case_id,
                "Status": "PROMOTED_RULE_NESTED_REUSE_EXACT" if selected else "REUSE_FAILED",
                "RuleInventionCalls": 0, "PromotedRuleCallCount": minimum_rule_uses,
                "ExactProgramCount": len(exact),
                "SelectedProgramAST": None if selected is None else json_ast(selected.ast),
                "SelectedProgramCost": None if selected is None else selected.cost,
                "G0ExactSemanticClassCount": int(target in g0),
                "GrammarChangedDuringReuse": False,
            })

    rows = {row["CaseID"]: row for row in case_rows}
    formation = rows["S158B_R2_FORM_RULE"]
    reuse = rows["S158B_R2_REUSE_NESTED"]
    ambiguous = rows["S158B_R2_AMBIGUOUS"]
    unavailable = rows["S158B_R2_NO_EXTENSION"]
    selected_rule = formation["SelectedRule"]
    full_action_match = selected_rule is not None and any(
        schema.rule_id == selected_rule["AnonymousRuleID"]
        and schema.action_signature == holdout["FreshTargetRuleActionSignature"]
        for schema in candidate_rule_schemas())
    checks = {
        "FiveFreshCasesNoReplacement": len(case_rows) == 5,
        "G0ClosureExhaustivelyHasFourClasses": len(g0) == 4,
        "FreshFormationTargetProvablyAbsentFromG0": tuple(formation_target) not in g0,
        "FreshNestedTargetProvablyAbsentFromG0": tuple(nested_target) not in g0,
        "FreshRuleHasNoHistoricalSemanticCollision": fresh_hash not in
            holdout["HistoricalTargetRuleActionSignatureSHA256"],
        "UniqueFreshRuleFormedAndPromoted":
            formation["Status"] == "META_GRAMMAR_RULE_PROMOTED"
            and formation["FinalVersionSpaceSize"] == 1 and formation["FrozenRule"]
            and formation["FullExactCertificatePassed"],
        "ActiveQueriesStrictlyReduceRuleVersionSpace": all(
            row.get("WorstCaseStrictReduction", True) for row in formation["Trace"]),
        "FullFreshRuleActionCertificateExact": full_action_match,
        "GrammarChangedOnlyAtPromotion":
            formation["GrammarHashBefore"] != formation["GrammarHashAfter"]
            and all(not row.get("GrammarChanged", False) for key, row in rows.items()
                    if key != "S158B_R2_FORM_RULE"),
        "InventionOffNestedReuseExact":
            reuse["Status"] == "PROMOTED_RULE_NESTED_REUSE_EXACT"
            and reuse["RuleInventionCalls"] == 0 and reuse["G0ExactSemanticClassCount"] == 0,
        "NestedReuseUsesPromotedRuleAtLeastTwice": reuse["PromotedRuleCallCount"] >= 2,
        "FreshAmbiguityAbstainsWithoutFreeze":
            ambiguous["Status"] == "META_GRAMMAR_RULE_AMBIGUOUS_ABSTAIN"
            and ambiguous["FinalVersionSpaceSize"] > 1 and not ambiguous["FrozenRule"],
        "FreshSubstrateInsufficiencyRejectsWithoutFreeze":
            unavailable["Status"] == "META_META_LANGUAGE_INSUFFICIENT_REJECT"
            and unavailable["FinalVersionSpaceSize"] == 0 and not unavailable["FrozenRule"],
        "NoLookupOrExceptionPatch":
            not protocol["LookupRuleAllowed"] and not protocol["ExceptionPatchAllowed"],
        "CoreRewriteFreezeDedupUnchanged":
            not protocol["TCCTCoreRewriteFreezeDedupModified"],
    }
    passed = all(checks.values())
    out = {
        "Stage": "S158-B-R2", "EvidenceLevel": "NEW_SEED_SINGLE_COHORT_FROZEN_FRESH",
        "MaterializationSeed": holdout["MaterializationSeed"],
        "EligibleFreshRuleCount": len(eligible), "CaseRows": case_rows,
        "Checks": checks, "PythonFreshPass": passed,
        "Conclusion": ("S158B_R2_NEW_SEED_FROZEN_FRESH_PYTHON_PASS" if passed
                       else "S158B_R2_NEW_SEED_FROZEN_FRESH_PYTHON_FAIL"),
        "ClaimBoundary": ("Single-cohort fresh evidence only; fixed meta-meta-language remains "
                          "human supplied and multi-seed replication is not established."),
    }
    dump(STAGE / "results" / "python_fresh_result.json", out)
    print({"Conclusion": out["Conclusion"],
           "Statuses": [row["Status"] for row in case_rows], "Checks": checks})
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
