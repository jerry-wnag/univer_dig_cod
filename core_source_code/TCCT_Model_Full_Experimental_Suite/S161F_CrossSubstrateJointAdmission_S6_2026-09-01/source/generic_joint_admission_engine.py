from __future__ import annotations

import collections
import hashlib
import itertools
from dataclasses import dataclass


@dataclass(frozen=True)
class Program:
    word: tuple[str, ...]
    semantics: tuple[int, ...]

    @property
    def cost(self): return len(self.word)


def semantic_hash(semantics): return hashlib.sha256(bytes(semantics)).hexdigest()
def identity(carrier): return tuple(carrier)
def compose(outer, inner): return tuple(outer[inner[index]] for index in range(len(inner)))


def enumerate_programs(atoms, maximum_cost, carrier):
    grouped = collections.defaultdict(list)
    frontier = [Program((), identity(carrier))]
    grouped[identity(carrier)].extend(frontier)
    for _ in range(maximum_cost):
        next_frontier = []
        for program in frontier:
            for name, atom in sorted(atoms.items()):
                candidate = Program(program.word + (name,), compose(atom, program.semantics))
                grouped[candidate.semantics].append(candidate)
                next_frontier.append(candidate)
        frontier = next_frontier
    return dict(grouped)


def proposal_space(base, carrier):
    current = enumerate_programs(base, 2, carrier)
    constructors = [semantics for semantics, programs in current.items()
                    if min(program.cost for program in programs) == 2]
    entries = set()
    for constructor in constructors:
        extended = enumerate_programs({**base, "R": constructor}, 2, carrier)
        for task, programs in extended.items():
            if task not in current and any("R" in program.word for program in programs):
                entries.add((constructor, task))
    return current, sorted(constructors, key=semantic_hash), sorted(entries)


def matches(semantics, observations): return all(semantics[x] == y for x, y in observations.items())


def compatible_joint(current, entries, observations):
    return ([semantics for semantics in current if matches(semantics, observations)],
            [(constructor, task) for constructor, task in entries if matches(task, observations)])


def constructor_classes(entries): return sorted({constructor for constructor, _ in entries}, key=semantic_hash)


def decision_classes(current_matches, constructor_matches):
    classes = [("CURRENT_GRAMMAR",)] if current_matches else []
    classes.extend(("CONSTRUCTOR", semantic_hash(c)) for c in constructor_classes(constructor_matches))
    return tuple(classes)


def choose_joint_query(current_matches, constructor_matches, unused):
    before = len(decision_classes(current_matches, constructor_matches)); choices = []
    for query in unused:
        outcomes = {semantics[query] for semantics in current_matches}
        outcomes.update(task[query] for _, task in constructor_matches)
        if len(outcomes) < 2: continue
        worst = 0
        for outcome in outcomes:
            rc = [semantics for semantics in current_matches if semantics[query] == outcome]
            re = [(constructor, task) for constructor, task in constructor_matches if task[query] == outcome]
            worst = max(worst, len(decision_classes(rc, re)))
        if worst < before: choices.append((worst, -len(outcomes), query))
    return None if not choices else min(choices)[-1]


def joint_residual_propose(base, target, initial_inputs, maximum_queries, carrier):
    current, constructors, all_entries = proposal_space(base, carrier)
    observations = {x: target[x] for x in initial_inputs}
    current_matches, constructor_matches = compatible_joint(current, all_entries, observations)
    trace = [{"Step": 0, "CurrentGrammarSemanticCandidates": len(current_matches),
              "ConstructorClasses": len(constructor_classes(constructor_matches)),
              "JointDecisionClasses": len(decision_classes(current_matches, constructor_matches)),
              "Action": "ANALYZE_JOINT_RESIDUAL_VERSION_SPACE"}]
    queries = []; unused = [x for x in carrier if x not in observations]
    while len(decision_classes(current_matches, constructor_matches)) > 1 and len(queries) < maximum_queries:
        query = choose_joint_query(current_matches, constructor_matches, unused)
        if query is None: break
        before = len(decision_classes(current_matches, constructor_matches)); outcome = target[query]
        observations[query] = outcome; unused.remove(query)
        current_matches, constructor_matches = compatible_joint(current, all_entries, observations)
        after = len(decision_classes(current_matches, constructor_matches))
        queries.append({"Input": query, "TaskOutput": outcome})
        trace.append({"Step": len(queries), "Input": query, "BeforeJointDecisionClasses": before,
                      "AfterJointDecisionClasses": after,
                      "CurrentGrammarSemanticCandidates": len(current_matches),
                      "ConstructorClasses": len(constructor_classes(constructor_matches)),
                      "Action": "JOINT_TASK_OUTPUT_DISAGREEMENT_QUERY"})
    classes = constructor_classes(constructor_matches)
    exact_current = [semantics for semantics in current if semantics == target]
    exact_constructors = sorted({constructor for constructor, task in all_entries if task == target}, key=semantic_hash)
    selected = None
    if current_matches:
        status = "CURRENT_GRAMMAR_SUFFICIENT_NO_PROPOSAL" if exact_current else "RESIDUAL_NOT_ESTABLISHED_NO_PROPOSAL"
        promoted, certificate = False, bool(exact_current)
    elif len(classes) == 1:
        selected = classes[0]
        if exact_constructors == [selected]:
            status, promoted, certificate = "UNIQUE_RESIDUAL_CONSTRUCTOR_PROMOTED", True, True
        elif not exact_constructors:
            status, promoted, certificate = "CONSTRUCTOR_SUBSTRATE_INSUFFICIENT_REJECT", False, False
        else:
            status, promoted, certificate = "IRREDUCIBLE_CONSTRUCTOR_AMBIGUITY_ABSTAIN", False, False
    elif not classes:
        status, promoted, certificate = "CONSTRUCTOR_SUBSTRATE_INSUFFICIENT_REJECT", False, False
    else:
        status, promoted, certificate = "IRREDUCIBLE_CONSTRUCTOR_AMBIGUITY_ABSTAIN", False, False
    return {"Status": status, "Observations": observations, "Queries": queries, "Trace": trace,
            "ProposedConstructor": list(selected) if promoted else None, "Promoted": promoted,
            "InitialCurrentGrammarCandidateCount": trace[0]["CurrentGrammarSemanticCandidates"],
            "FinalCurrentGrammarCandidateCount": len(current_matches),
            "InitialConstructorClassCount": trace[0]["ConstructorClasses"],
            "FinalConstructorClassCount": len(classes),
            "InitialJointDecisionClassCount": trace[0]["JointDecisionClasses"],
            "FinalJointDecisionClassCount": len(decision_classes(current_matches, constructor_matches)),
            "FullExactCurrentGrammarCount": len(exact_current),
            "FullExactConstructorClassCount": len(exact_constructors),
            "FullExactCertificatePassed": certificate,
            "CandidateConstructorsGeneratedAtRuntime": len(constructors),
            "CandidateExplanationEntriesGeneratedAtRuntime": len(all_entries)}


def all_subsets(carrier):
    for size in range(1, len(carrier) + 1): yield from itertools.combinations(carrier, size)


def inverse(permutation):
    result = [0] * len(permutation)
    for index, value in enumerate(permutation): result[value] = index
    return tuple(result)


def canonical_pair(first, second, carrier):
    best = None
    for relabel in itertools.permutations(carrier):
        inv = inverse(relabel)
        candidate = (compose(relabel, compose(first, inv)), compose(relabel, compose(second, inv)))
        if best is None or candidate < best: best = candidate
    return best
