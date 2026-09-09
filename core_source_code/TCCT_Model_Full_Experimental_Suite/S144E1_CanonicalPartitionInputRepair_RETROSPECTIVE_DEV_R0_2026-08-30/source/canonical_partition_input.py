from __future__ import annotations

from typing import Any


def canonical_partition(value: list[list[str]]) -> tuple[tuple[str, ...], ...]:
    if any(len(block) == 0 for block in value):
        raise ValueError("partition contains an empty block")
    flat = [item for block in value for item in block]
    if len(flat) != len(set(flat)):
        raise ValueError("partition blocks overlap")
    return tuple(sorted(tuple(sorted(str(item) for item in block)) for block in value))


def meet(left: tuple[tuple[str, ...], ...], right: tuple[tuple[str, ...], ...]):
    return tuple(sorted(tuple(sorted(set(a) & set(b))) for a in left for b in right if set(a) & set(b)))


def refines(left: tuple[tuple[str, ...], ...], right: tuple[tuple[str, ...], ...]) -> bool:
    return all(any(set(block) <= set(target) for target in right) for block in left)


def term_value(term: dict[str, Any], app: dict[str, Any]):
    if term["Op"] == "Var":
        return canonical_partition(app[term["Name"]])
    if term["Op"] == "PartitionMeet":
        return meet(*(term_value(arg, app) for arg in term["Args"]))
    raise ValueError(term)


def atom_value(atom: dict[str, Any], app: dict[str, Any]) -> bool:
    left, right = (term_value(arg, app) for arg in atom["Args"])
    if atom["Name"] == "Equal":
        return left == right
    if atom["Name"] == "PartitionRefines":
        return refines(left, right)
    if atom["Name"] == "StrictPartitionRefines":
        return left != right and refines(left, right)
    raise ValueError(atom["Name"])


def signal_values(definitions: list[dict[str, Any]], app: dict[str, Any]) -> list[bool]:
    return [atom_value(atom, app) for atom in definitions]
