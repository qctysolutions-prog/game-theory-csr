"""Reproducible coalition MILP and cooperative-game calculations for Chapter 4."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import itertools
import json
import math
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable

from ortools.linear_solver import pywraplp


TOL = 1e-6


def coalition_name(coalition: frozenset[str], players: list[str]) -> str:
    if not coalition:
        return "empty"
    return "+".join(player for player in players if player in coalition)


def powerset(players: list[str]) -> list[frozenset[str]]:
    return [
        frozenset(combo)
        for size in range(len(players) + 1)
        for combo in itertools.combinations(players, size)
    ]


def create_solver(requested: str) -> tuple[pywraplp.Solver, str]:
    candidates = [requested, "CBC"] if requested.upper() != "CBC" else ["CBC"]
    for name in candidates:
        solver = pywraplp.Solver.CreateSolver(name)
        if solver is not None:
            return solver, name
    raise RuntimeError(f"No requested MILP solver is available: {candidates}")


def governance_cost(
    data: dict[str, Any], coalition: frozenset[str], scenario: dict[str, Any]
) -> float:
    if not coalition:
        return 0.0
    cfg = data["governance_cost"]
    manufacturer = data["manufacturer"]
    retailer_count = sum(player in data["retailers"] for player in coalition)
    value = cfg["manufacturer_platform"] if manufacturer in coalition else 0.0
    if retailer_count:
        value += cfg["coalition_base"] + cfg["per_retailer"] * retailer_count
    return value * scenario.get("governance_cost_multiplier", 1.0)


def solve_coalition(
    data: dict[str, Any],
    coalition: frozenset[str],
    scenario: dict[str, Any],
    requested_solver: str,
) -> dict[str, Any]:
    players = data["players"]
    manufacturer = data["manufacturer"]
    retailers = [player for player in players if player in coalition and player in data["retailers"]]
    g_cost = governance_cost(data, coalition, scenario)
    service_rate = scenario.get(
        "formal_service_rate", data["service"]["formal_service_rate"]
    )
    if not 0.0 <= service_rate <= 1.0:
        raise ValueError(f"formal_service_rate must be in [0,1], got {service_rate}")
    if not coalition:
        return {
            "coalition": "empty",
            "members": [],
            "cost": 0.0,
            "service_rate": 0.0,
            "required_volume": 0.0,
            "recovered_output": 0.0,
            "unit_cost": 0.0,
            "open_centers": [],
            "open_processors": [],
            "solver": "none",
            "objective_recomputed": 0.0,
        }
    if not retailers:
        return {
            "coalition": coalition_name(coalition, players),
            "members": sorted(coalition, key=players.index),
            "cost": g_cost,
            "service_rate": service_rate,
            "required_volume": 0.0,
            "recovered_output": 0.0,
            "unit_cost": 0.0,
            "open_centers": [],
            "open_processors": [],
            "solver": "none",
            "objective_recomputed": g_cost,
        }

    # Two linear-programming modes support the structural diagnosis; neither
    # adds a model parameter. "relax_integrality" lets y and z take any value
    # in [0, 1]. "fixed_binaries" pins y and z at a known MILP configuration so
    # the remaining flow problem is an LP whose shadow prices are exact local
    # derivatives of c(S) within that configuration.
    relax = bool(scenario.get("relax_integrality", False))
    fixed = scenario.get("fixed_binaries")
    linear_mode = relax or fixed is not None
    if linear_mode:
        solver, solver_name = create_solver("GLOP")
    else:
        solver, solver_name = create_solver(requested_solver)
    centers = list(data["centers"])
    processors = list(data["processors"])
    volume_multiplier = scenario.get("volume_multiplier", 1.0)
    transport_multiplier = scenario.get("transport_multiplier", 1.0)
    recovery_multiplier = scenario.get("recovery_multiplier", 1.0)
    capacity_override = scenario.get("processor_capacity_override", {})
    processor_capacity = {
        l: float(capacity_override.get(l, data["processors"][l]["capacity"]))
        for l in processors
    }
    has_manufacturer = manufacturer in coalition

    # Mean-preserving volume dispersion: t = 1 is the case data, t = 0 gives
    # every retailer the mean volume, and total volume is unchanged for any t.
    dispersion = scenario.get("volume_dispersion", 1.0)
    mean_volume = sum(r["volume"] for r in data["retailers"].values()) / len(data["retailers"])
    return_volumes = {
        i: (mean_volume + dispersion * (data["retailers"][i]["volume"] - mean_volume))
        * volume_multiplier
        for i in retailers
    }
    required_volumes = {i: service_rate * return_volumes[i] for i in retailers}
    q = {(i, j): solver.NumVar(0.0, solver.infinity(), f"q_{i}_{j}") for i in retailers for j in centers}
    x = {(j, l): solver.NumVar(0.0, solver.infinity(), f"x_{j}_{l}") for j in centers for l in processors}
    if fixed is not None:
        y = {j: solver.NumVar(float(j in fixed["centers"]), float(j in fixed["centers"]), f"y_{j}") for j in centers}
        z = {l: solver.NumVar(float(l in fixed["processors"]), float(l in fixed["processors"]), f"z_{l}") for l in processors}
    elif relax:
        y = {j: solver.NumVar(0.0, 1.0, f"y_{j}") for j in centers}
        z = {l: solver.NumVar(0.0, 1.0, f"z_{l}") for l in processors}
    else:
        y = {j: solver.BoolVar(f"y_{j}") for j in centers}
        z = {l: solver.BoolVar(f"z_{l}") for l in processors}

    demand_rows = {}
    for i in retailers:
        demand_rows[i] = solver.Add(sum(q[i, j] for j in centers) == required_volumes[i])
    for j in centers:
        solver.Add(sum(q[i, j] for i in retailers) == sum(x[j, l] for l in processors))
        solver.Add(sum(q[i, j] for i in retailers) <= data["centers"][j]["capacity"] * y[j])
    access_override = scenario.get("processor_access_override", {})
    eligibility: dict[str, float] = {}
    for l in processors:
        if l in access_override:
            eligibility[l] = float(access_override[l])
        else:
            requires_m = data["processors"][l].get(
                "requires_manufacturer_platform", False
            )
            eligibility[l] = 1.0 if (not requires_m or has_manufacturer) else 0.0
    capacity_rows = {}
    for l in processors:
        capacity_rows[l] = solver.Add(sum(x[j, l] for j in centers) <= processor_capacity[l] * z[l])
        if fixed is None:
            solver.Add(z[l] <= eligibility[l])
        elif l in fixed["processors"] and not eligibility[l]:
            raise ValueError(f"fixed configuration opens ineligible processor {l}")

    objective = solver.Objective()
    collection_constant = sum(
        data["retailers"][i]["collection_cost"] * required_volumes[i] / 1000.0
        for i in retailers
    )
    objective.SetOffset(collection_constant + g_cost)
    for i in retailers:
        for j in centers:
            unit = (
                data["retailer_center_transport"][i][j] * transport_multiplier
                + data["centers"][j]["handling_cost"]
            )
            objective.SetCoefficient(q[i, j], unit / 1000.0)
    for j in centers:
        objective.SetCoefficient(y[j], data["centers"][j]["fixed_cost"])
        for l in processors:
            processor = data["processors"][l]
            processing = processor["processing_cost"]
            recovery = recovery_multiplier * processor["base_recovery_value"]
            unit = (
                data["center_processor_transport"][j][l] * transport_multiplier
                + processing
                - processor["recovery_efficiency"] * recovery
            )
            objective.SetCoefficient(x[j, l], unit / 1000.0)
    for l in processors:
        objective.SetCoefficient(z[l], data["processors"][l]["fixed_cost"])
    objective.SetMinimization()

    status = solver.Solve()
    if status != pywraplp.Solver.OPTIMAL:
        debug_model = solver.ExportModelAsLpFormat(False)
        raise RuntimeError(
            f"Coalition {coalition_name(coalition, players)} was not optimal; status={status}\n"
            f"service_rate={service_rate}; eligibility={eligibility}\n"
            f"{debug_model}"
        )

    q_values = {(i, j): q[i, j].solution_value() for i in retailers for j in centers}
    x_values = {(j, l): x[j, l].solution_value() for j in centers for l in processors}
    y_values = {j: y[j].solution_value() for j in centers}
    z_values = {l: z[l].solution_value() for l in processors}
    required_volume = sum(required_volumes.values())
    recovered_output = sum(
        data["processors"][l]["recovery_efficiency"] * x_values[j, l]
        for j in centers
        for l in processors
    )

    recomputed = collection_constant + g_cost
    recomputed += sum(
        (
            data["retailer_center_transport"][i][j] * transport_multiplier
            + data["centers"][j]["handling_cost"]
        )
        * q_values[i, j]
        / 1000.0
        for i in retailers
        for j in centers
    )
    recomputed += sum(data["centers"][j]["fixed_cost"] * y_values[j] for j in centers)
    for j in centers:
        for l in processors:
            processor = data["processors"][l]
            processing = processor["processing_cost"]
            recovery = recovery_multiplier * processor["base_recovery_value"]
            unit = (
                data["center_processor_transport"][j][l] * transport_multiplier
                + processing
                - processor["recovery_efficiency"] * recovery
            )
            recomputed += unit * x_values[j, l] / 1000.0
    recomputed += sum(
        data["processors"][l]["fixed_cost"] * z_values[l]
        for l in processors
    )
    if abs(recomputed - objective.Value()) > 1e-4:
        raise AssertionError(
            f"Objective reconciliation failed for {coalition_name(coalition, players)}: "
            f"solver={objective.Value()}, recomputed={recomputed}"
        )

    result = {
        "coalition": coalition_name(coalition, players),
        "members": sorted(coalition, key=players.index),
        "cost": objective.Value(),
        "service_rate": service_rate,
        "required_volume": required_volume,
        "recovered_output": recovered_output,
        "unit_cost": 1000.0 * objective.Value() / required_volume,
        "open_centers": [j for j in centers if y_values[j] > 0.5],
        "open_processors": [l for l in processors if z_values[l] > 0.5],
        "solver": solver_name,
        "objective_recomputed": recomputed,
    }
    if linear_mode:
        # Duals are in thousand USD per ton. Because the capacity row is
        # sum(x) - K*z <= 0, dc(S)/dK_l = capacity_dual * z_l.
        result["lp"] = {
            "y": y_values,
            "z": z_values,
            "demand_duals": {i: demand_rows[i].dual_value() for i in retailers},
            "capacity_duals": {l: capacity_rows[l].dual_value() for l in processors},
            "processor_flow": {l: sum(x_values[j, l] for j in centers) for l in processors},
        }
    return result


def shapley_value(costs: dict[frozenset[str], float], players: list[str]) -> dict[str, float]:
    n = len(players)
    factorial = math.factorial
    shapley: dict[str, float] = {}
    for player in players:
        value = 0.0
        others = [candidate for candidate in players if candidate != player]
        for size in range(len(others) + 1):
            for combo in itertools.combinations(others, size):
                predecessor = frozenset(combo)
                weight = factorial(size) * factorial(n - size - 1) / factorial(n)
                value += weight * (costs[predecessor | {player}] - costs[predecessor])
        shapley[player] = value
    return shapley


def solve_game(
    data: dict[str, Any], scenario: dict[str, Any], requested_solver: str
) -> dict[str, Any]:
    players = data["players"]
    coalitions = powerset(players)
    results = {
        coalition: solve_coalition(data, coalition, scenario, requested_solver)
        for coalition in coalitions
    }
    costs = {coalition: result["cost"] for coalition, result in results.items()}
    shapley = shapley_value(costs, players)
    grand = frozenset(players)
    if abs(sum(shapley.values()) - costs[grand]) > 1e-5:
        raise AssertionError("Shapley efficiency failed")
    savings_allocated = {player: costs[frozenset({player})] - shapley[player] for player in players}
    grand_savings = sum(costs[frozenset({player})] for player in players) - costs[grand]
    if abs(sum(savings_allocated.values()) - grand_savings) > 1e-5:
        raise AssertionError("Savings-game identity failed")
    core_rows = []
    for coalition in coalitions:
        if not coalition or coalition == grand:
            continue
        payment = sum(shapley[player] for player in coalition)
        core_rows.append(
            {
                "coalition": coalition_name(coalition, players),
                "members": sorted(coalition, key=players.index),
                "payment": payment,
                "coalition_cost": costs[coalition],
                "slack": costs[coalition] - payment,
            }
        )
    core_rows.sort(key=lambda row: (row["slack"], row["coalition"]))
    return {
        "results": results,
        "costs": costs,
        "shapley": shapley,
        "savings_allocated": savings_allocated,
        "grand_savings": grand_savings,
        "core_rows": core_rows,
        "minimum_core_slack": core_rows[0]["slack"],
    }


def allocation_slack(
    allocation: dict[str, float], costs: dict[frozenset[str], float], players: list[str]
) -> float:
    grand = frozenset(players)
    return min(
        costs[coalition] - sum(allocation[player] for player in coalition)
        for coalition in powerset(players)
        if coalition and coalition != grand
    )


def least_core_l1(
    costs: dict[frozenset[str], float], shapley: dict[str, float], players: list[str]
) -> tuple[float, dict[str, float]]:
    grand = frozenset(players)
    coalitions = [c for c in powerset(players) if c and c != grand]
    stage1, _ = create_solver("GLOP")
    a1 = {p: stage1.NumVar(0.0, stage1.infinity(), f"a_{p}") for p in players}
    epsilon = stage1.NumVar(-stage1.infinity(), stage1.infinity(), "epsilon")
    stage1.Add(sum(a1.values()) == costs[grand])
    for coalition in coalitions:
        stage1.Add(sum(a1[p] for p in coalition) <= costs[coalition] + epsilon)
    stage1.Minimize(epsilon)
    if stage1.Solve() != pywraplp.Solver.OPTIMAL:
        raise RuntimeError("Least-core stage was not optimal")
    epsilon_star = epsilon.solution_value()

    stage2, _ = create_solver("GLOP")
    a2 = {p: stage2.NumVar(0.0, stage2.infinity(), f"a_{p}") for p in players}
    deviations = {p: stage2.NumVar(0.0, stage2.infinity(), f"d_{p}") for p in players}
    stage2.Add(sum(a2.values()) == costs[grand])
    for coalition in coalitions:
        stage2.Add(sum(a2[p] for p in coalition) <= costs[coalition] + epsilon_star + 1e-7)
    for player in players:
        stage2.Add(a2[player] - shapley[player] <= deviations[player])
        stage2.Add(shapley[player] - a2[player] <= deviations[player])
    stage2.Minimize(sum(deviations.values()))
    if stage2.Solve() != pywraplp.Solver.OPTIMAL:
        raise RuntimeError("L1 projection stage was not optimal")
    allocation = {player: a2[player].solution_value() for player in players}
    if abs(sum(allocation.values()) - costs[grand]) > 1e-5:
        raise AssertionError("Least-core allocation is not efficient")
    return epsilon_star, allocation


def allocation_rules(data: dict[str, Any], game: dict[str, Any]) -> dict[str, Any]:
    players = data["players"]
    manufacturer = data["manufacturer"]
    grand_cost = game["costs"][frozenset(players)]
    volumes = {p: data["retailers"][p]["volume"] for p in data["retailers"]}
    total_volume = sum(volumes.values())
    m_weight = data["allocation"]["manufacturer_responsibility_weight"]
    proportional = {manufacturer: m_weight * grand_cost}
    proportional.update(
        {p: (1.0 - m_weight) * grand_cost * volumes[p] / total_volume for p in volumes}
    )
    theta = data["allocation"]["hybrid_shapley_weight"]
    hybrid = {
        p: theta * game["shapley"][p] + (1.0 - theta) * proportional[p] for p in players
    }
    epsilon_star, projection = least_core_l1(game["costs"], game["shapley"], players)
    support_requested = data["allocation"]["manufacturer_support_budget"]
    manufacturer_room = game["costs"][frozenset({manufacturer})] - game["shapley"][manufacturer]
    support = max(0.0, min(support_requested, manufacturer_room))
    retailer_total = sum(game["shapley"][p] for p in volumes)
    support_allocation = dict(game["shapley"])
    support_allocation[manufacturer] += support
    for p in volumes:
        support_allocation[p] -= support * game["shapley"][p] / retailer_total

    rules = {
        "Proportional responsibility": proportional,
        "Shapley baseline": game["shapley"],
        "Hybrid (theta=0.70)": hybrid,
        "Least-core L1 projection": projection,
        "Manufacturer responsibility shift": support_allocation,
    }
    return {
        "epsilon_star": epsilon_star,
        "manufacturer_support": support,
        "rules": {
            name: {
                "allocation": allocation,
                "manufacturer_share": allocation[manufacturer],
                "largest_retailer_share": max(allocation[p] for p in volumes),
                "minimum_core_slack": allocation_slack(allocation, game["costs"], players),
            }
            for name, allocation in rules.items()
        },
    }


# ---------------------------------------------------------------------------
# Structural diagnosis of coalition stability (Chapter 4 analytical deepening)
#
# Everything below reads the same cost game c(S). No model parameter is added:
# sweeps vary existing inputs, and the linear relaxation is an analytical
# device. Each result is checked by an assertion so that a run cannot export
# a number that contradicts the proposition it is meant to illustrate.
# ---------------------------------------------------------------------------


def proper_coalitions(players: list[str]) -> list[frozenset[str]]:
    grand = frozenset(players)
    return [c for c in powerset(players) if c and c != grand]


def least_core_value(
    costs: dict[frozenset[str], float], players: list[str], nonnegative: bool = False
) -> float:
    """Smallest uniform excess epsilon such that some efficient allocation
    satisfies every proper-coalition constraint within epsilon."""
    solver, _ = create_solver("GLOP")
    low = 0.0 if nonnegative else -solver.infinity()
    a = {p: solver.NumVar(low, solver.infinity(), f"a_{p}") for p in players}
    epsilon = solver.NumVar(-solver.infinity(), solver.infinity(), "epsilon")
    solver.Add(sum(a.values()) == costs[frozenset(players)])
    for coalition in proper_coalitions(players):
        solver.Add(sum(a[p] for p in coalition) <= costs[coalition] + epsilon)
    solver.Minimize(epsilon)
    if solver.Solve() != pywraplp.Solver.OPTIMAL:
        raise RuntimeError("Least-core value LP was not optimal")
    return epsilon.solution_value()


def least_core_certificate(
    costs: dict[frozenset[str], float], players: list[str], check_unique: bool = False
) -> dict[str, Any]:
    """Dual of the (unrestricted) least-core LP.

    max  mu*c(N) - sum_S lambda_S c(S)
    s.t. sum_{S contains i} lambda_S = mu for every player i,  sum_S lambda_S = 1.

    delta_S = lambda_S / mu is a balanced collection; when epsilon* > 0 it is
    the Bondareva-Shapley certificate that the core is empty.
    """
    grand = frozenset(players)
    coalitions = proper_coalitions(players)

    def build() -> tuple[pywraplp.Solver, dict, Any, Any]:
        solver, _ = create_solver("GLOP")
        lam = {S: solver.NumVar(0.0, solver.infinity(), f"l_{coalition_name(S, players)}") for S in coalitions}
        mu = solver.NumVar(-solver.infinity(), solver.infinity(), "mu")
        for player in players:
            solver.Add(sum(lam[S] for S in coalitions if player in S) == mu)
        solver.Add(sum(lam.values()) == 1.0)
        value = mu * costs[grand] - sum(lam[S] * costs[S] for S in coalitions)
        return solver, lam, mu, value

    solver, lam, mu, value = build()
    solver.Maximize(value)
    if solver.Solve() != pywraplp.Solver.OPTIMAL:
        raise RuntimeError("Least-core dual LP was not optimal")
    epsilon = solver.Objective().Value()
    weights = {S: lam[S].solution_value() for S in coalitions if lam[S].solution_value() > 1e-9}
    mu_value = mu.solution_value()

    unique = None
    if check_unique:
        # The certificate is unique if every weight is pinned on the optimal face.
        unique = True
        for S in coalitions:
            bounds = []
            for sense in ("min", "max"):
                probe, probe_lam, _, probe_value = build()
                probe.Add(probe_value >= epsilon - 1e-9)
                (probe.Minimize if sense == "min" else probe.Maximize)(probe_lam[S])
                if probe.Solve() != pywraplp.Solver.OPTIMAL:
                    raise RuntimeError("Certificate uniqueness probe was not optimal")
                bounds.append(probe_lam[S].solution_value())
            if bounds[1] - bounds[0] > 1e-7:
                unique = False
                break
    return {"epsilon": epsilon, "mu": mu_value, "weights": weights, "unique": unique}


def cost_of_stability(costs: dict[frozenset[str], float], players: list[str]) -> float:
    """Smallest external subsidy D such that some allocation of c(N) - D
    satisfies every proper-coalition constraint (cost-game form)."""
    solver, _ = create_solver("GLOP")
    a = {p: solver.NumVar(-solver.infinity(), solver.infinity(), f"a_{p}") for p in players}
    for coalition in proper_coalitions(players):
        solver.Add(sum(a[p] for p in coalition) <= costs[coalition])
    solver.Maximize(sum(a.values()))
    if solver.Solve() != pywraplp.Solver.OPTIMAL:
        raise RuntimeError("Cost-of-stability LP was not optimal")
    return max(0.0, costs[frozenset(players)] - solver.Objective().Value())


def structural_properties(game: dict[str, Any], players: list[str]) -> dict[str, Any]:
    """Monotonicity, subadditivity, and concavity (submodularity) of c(S).

    Counts use each non-trivial comparison once: nested pairs satisfy the
    lattice inequality with equality and are excluded from the concavity test.
    """
    costs = game["costs"]
    results = game["results"]
    subsets = powerset(players)
    uses_all = lambda S: len(results[S]["open_processors"]) > 1

    nested = [(S, T) for S in subsets for T in subsets if S < T]
    monotone_violations = sum(1 for S, T in nested if costs[S] > costs[T] + TOL)

    nonempty = [S for S in subsets if S]
    disjoint = [(A, B) for A, B in itertools.combinations(nonempty, 2) if not (A & B)]
    subadditive_violations = sum(1 for A, B in disjoint if costs[A] + costs[B] < costs[A | B] - TOL)

    lattice = [(A, B) for A, B in itertools.combinations(subsets, 2) if not (A <= B or B <= A)]
    violating = {(A, B) for A, B in lattice if costs[A] + costs[B] < costs[A | B] + costs[A & B] - TOL}
    two_processor = [pair for pair in lattice if uses_all(pair[0] | pair[1])]
    one_processor = [pair for pair in lattice if not uses_all(pair[0] | pair[1])]

    triples = 0
    marginal_violations = 0
    worst = None
    for player in players:
        others = [p for p in players if p != player]
        for larger in powerset(others):
            for smaller in powerset(sorted(larger, key=players.index)):
                if smaller == larger:
                    continue
                triples += 1
                early = costs[smaller | {player}] - costs[smaller]
                late = costs[larger | {player}] - costs[larger]
                if early < late - TOL:
                    marginal_violations += 1
                    if worst is None or late - early > worst["increase"]:
                        worst = {
                            "player": player,
                            "smaller": smaller,
                            "larger": larger,
                            "early": early,
                            "late": late,
                            "increase": late - early,
                        }
    return {
        "monotone": (monotone_violations, len(nested)),
        "subadditive": (subadditive_violations, len(disjoint)),
        "concave": (len(violating), len(lattice)),
        "concave_two_processor": (sum(1 for p in two_processor if p in violating), len(two_processor)),
        "concave_one_processor": (sum(1 for p in one_processor if p in violating), len(one_processor)),
        "marginal": (marginal_violations, triples),
        "worst_marginal": worst,
    }


def platform_free_processors(data: dict[str, Any], scenario: dict[str, Any]) -> list[str]:
    """Processors whose access bound z_l <= 1 is shared by every coalition."""
    override = scenario.get("processor_access_override", {})
    shared = []
    for l, processor in data["processors"].items():
        if l in override:
            if float(override[l]) > 0.0:
                shared.append(l)
        elif not processor.get("requires_manufacturer_platform", False):
            shared.append(l)
    return shared


def owen_condition(data: dict[str, Any], scenario: dict[str, Any], grand_lp: dict[str, Any]) -> bool:
    """Condition (iii) of the linear-relaxation proposition: at the grand
    coalition's LP optimum no shared upper bound (y_j <= 1, or z_l <= 1 for a
    processor open to every coalition) binds. Platform-controlled access is
    the Manufacturer's endowment and may bind."""
    lp = grand_lp["lp"]
    if any(value > 1.0 - 1e-7 for value in lp["y"].values()):
        return False
    return all(lp["z"][l] < 1.0 - 1e-7 for l in platform_free_processors(data, scenario))


def stability_profile(
    data: dict[str, Any],
    scenario: dict[str, Any],
    requested_solver: str,
    check_unique: bool = False,
) -> dict[str, Any]:
    players = data["players"]
    grand = frozenset(players)
    n = len(players)
    game = solve_game(data, scenario, requested_solver)
    costs = game["costs"]
    lp_scenario = dict(scenario, relax_integrality=True)
    lp_results = {S: solve_coalition(data, S, lp_scenario, requested_solver) for S in powerset(players)}
    lp_costs = {S: result["cost"] for S, result in lp_results.items()}

    epsilon = least_core_value(costs, players)
    epsilon_nonnegative = least_core_value(costs, players, nonnegative=True)
    certificate = least_core_certificate(costs, players, check_unique)
    if abs(certificate["epsilon"] - epsilon) > 1e-6:
        raise AssertionError("Least-core primal and dual values disagree")
    epsilon_lp = least_core_value(lp_costs, players)
    stability_cost = cost_of_stability(costs, players)
    integrality_gap = costs[grand] - lp_costs[grand]
    owen_ok = owen_condition(data, scenario, lp_results[grand])

    # Proposition checks. A failure here means the exported numbers would
    # contradict the chapter, so the run stops.
    if integrality_gap < -1e-6:
        raise AssertionError("LP relaxation exceeds the MILP cost for the grand coalition")
    if owen_ok and epsilon_lp > 1e-6:
        raise AssertionError(f"Owen condition holds but the relaxed game has epsilon {epsilon_lp}")
    if owen_ok and stability_cost > integrality_gap + 1e-6:
        raise AssertionError("Cost of stability exceeds the integrality gap")
    if epsilon > 1e-7:
        if not (n / (n - 1) * epsilon - 1e-6 <= stability_cost <= n * epsilon + 1e-6):
            raise AssertionError("Cost-of-stability bounds violated")
    elif stability_cost > 1e-5:
        raise AssertionError("Nonempty core but positive cost of stability")

    support = sorted(
        certificate["weights"].items(),
        key=lambda item: (-item[1], coalition_name(item[0], players)),
    )
    return {
        "game": game,
        "lp_costs": lp_costs,
        "lp_grand": lp_results[grand],
        "epsilon": epsilon,
        "epsilon_nonnegative": epsilon_nonnegative,
        "epsilon_lp": epsilon_lp,
        "cost_of_stability": stability_cost,
        "integrality_gap": integrality_gap,
        "owen_condition": owen_ok,
        "certificate": certificate,
        "certificate_support": support,
        "blocking": [row for row in game["core_rows"] if row["slack"] < -TOL],
    }


def profile_row(profile: dict[str, Any], players: list[str], key: str, value: float) -> dict[str, str]:
    grand = frozenset(players)
    game = profile["game"]
    certificate = (
        ";".join(coalition_name(S, players) for S, _ in profile["certificate_support"])
        if profile["epsilon"] > 1e-7
        else ""
    )
    return {
        key: f"{value:.6f}",
        "grand_cost": f"{game['costs'][grand]:.6f}",
        "epsilon_star": f"{profile['epsilon']:.6f}",
        "epsilon_lp": f"{profile['epsilon_lp']:.6f}",
        "cost_of_stability": f"{profile['cost_of_stability']:.6f}",
        "integrality_gap": f"{profile['integrality_gap']:.6f}",
        "shapley_min_slack": f"{game['minimum_core_slack']:.6f}",
        "blocking_coalitions": str(len(profile["blocking"])),
        "grand_processors": ";".join(game["results"][grand]["open_processors"]),
        "owen_condition": str(profile["owen_condition"]).lower(),
        "certificate": certificate,
    }


def derivative_game(
    data: dict[str, Any], game: dict[str, Any], parameter: str, requested_solver: str
) -> dict[frozenset[str], float]:
    """dc(S)/dtheta for every coalition, holding each coalition's facility
    configuration fixed (envelope theorem on the residual LP)."""
    players = data["players"]
    derivative: dict[frozenset[str], float] = {}
    for coalition, result in game["results"].items():
        has_retailer = any(p in data["retailers"] for p in coalition)
        if parameter == "coalition_base":
            derivative[coalition] = 1.0 if has_retailer else 0.0
        elif parameter.startswith("capacity:"):
            l = parameter.split(":", 1)[1]
            if not has_retailer or l not in result["open_processors"]:
                derivative[coalition] = 0.0
                continue
            fixed = {"centers": result["open_centers"], "processors": result["open_processors"]}
            residual = solve_coalition(data, coalition, {"fixed_binaries": fixed}, requested_solver)
            if abs(residual["cost"] - result["cost"]) > 1e-5:
                raise AssertionError(f"Residual LP does not reproduce c({result['coalition']})")
            derivative[coalition] = residual["lp"]["capacity_duals"][l] * residual["lp"]["z"][l]
        else:
            raise ValueError(parameter)
    return derivative


def envelope_check(
    data: dict[str, Any], baseline: dict[str, Any], requested_solver: str
) -> list[dict[str, Any]]:
    """Proposition B1/B2: compare the two-level envelope prediction with a
    central finite difference of the fully re-solved game."""
    players = data["players"]
    grand = frozenset(players)
    weights = baseline["certificate"]["weights"]
    mu = baseline["certificate"]["mu"]
    game = baseline["game"]
    worst = frozenset(game["core_rows"][0]["members"])
    platform = next(l for l, p in data["processors"].items() if p.get("requires_manufacturer_platform"))
    checks = [
        ("coalition_base", "Coalition-level governance cost", 10.0),
        (f"capacity:{platform}", f"Capacity of processor {platform}", 50.0),
    ]
    rows = []
    for parameter, label, step in checks:
        d = derivative_game(data, game, parameter, requested_solver)
        predicted_epsilon = mu * d[grand] - sum(w * d[S] for S, w in weights.items())
        d_shapley = shapley_value(d, players)
        predicted_slack = d[worst] - sum(d_shapley[p] for p in worst)

        profiles = []
        for sign in (-1.0, 1.0):
            shifted = copy.deepcopy(data)
            if parameter == "coalition_base":
                shifted["governance_cost"]["coalition_base"] += sign * step
            else:
                shifted["processors"][platform]["capacity"] += sign * step
            shifted_game = solve_game(shifted, {}, requested_solver)
            shifted_certificate = least_core_certificate(shifted_game["costs"], players)
            profiles.append((shifted_game, shifted_certificate))
        fd_epsilon = (profiles[1][1]["epsilon"] - profiles[0][1]["epsilon"]) / (2 * step)
        slack_of = lambda g: g["costs"][worst] - sum(g["shapley"][p] for p in worst)
        fd_slack = (slack_of(profiles[1][0]) - slack_of(profiles[0][0])) / (2 * step)
        configuration_stable = all(
            set(p[1]["weights"]) == set(weights)
            and all(
                p[0]["results"][S]["open_centers"] == game["results"][S]["open_centers"]
                and p[0]["results"][S]["open_processors"] == game["results"][S]["open_processors"]
                for S in game["results"]
            )
            for p in profiles
        )
        agree = abs(predicted_epsilon - fd_epsilon) <= 1e-6 and abs(predicted_slack - fd_slack) <= 1e-6
        if configuration_stable and not agree:
            raise AssertionError(
                f"Envelope prediction failed for {parameter}: "
                f"eps {predicted_epsilon} vs {fd_epsilon}, slack {predicted_slack} vs {fd_slack}"
            )
        rows.append(
            {
                "parameter": parameter,
                "label": label,
                "step": step,
                "grand_derivative": d[grand],
                "predicted_d_epsilon": predicted_epsilon,
                "finite_difference_d_epsilon": fd_epsilon,
                "slack_coalition": coalition_name(worst, players),
                "predicted_d_shapley_slack": predicted_slack,
                "finite_difference_d_shapley_slack": fd_slack,
                "configuration_stable": configuration_stable,
                "agree": agree,
            }
        )
    return rows


def strategic_equivalence_check(
    data: dict[str, Any], baseline: dict[str, Any], requested_solver: str
) -> list[dict[str, Any]]:
    """Proposition A1: removing cost components that are additive across
    members must leave epsilon* and every Shapley core slack unchanged."""
    players = data["players"]
    reference = {row["coalition"]: row["slack"] for row in baseline["game"]["core_rows"]}
    variants = []
    no_collection = copy.deepcopy(data)
    for retailer in no_collection["retailers"].values():
        retailer["collection_cost"] = 0.0
    variants.append(("Retailer collection cost set to zero", no_collection))
    no_additive_governance = copy.deepcopy(data)
    no_additive_governance["governance_cost"]["manufacturer_platform"] = 0.0
    no_additive_governance["governance_cost"]["per_retailer"] = 0.0
    variants.append(("Platform and per-retailer governance cost set to zero", no_additive_governance))
    rows = []
    for label, variant in variants:
        game = solve_game(variant, {}, requested_solver)
        epsilon = least_core_value(game["costs"], players)
        slack_gap = max(abs(row["slack"] - reference[row["coalition"]]) for row in game["core_rows"])
        if abs(epsilon - baseline["epsilon"]) > 1e-6 or slack_gap > 1e-6:
            raise AssertionError(f"Strategic equivalence failed: {label}")
        rows.append({"variant": label, "epsilon_star": epsilon, "max_slack_change": slack_gap})
    return rows


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def fmt(value: float, decimals: int = 1) -> str:
    text = f"{value:,.{decimals}f}"
    # A value that rounds to zero from below would print as "-0.0".
    return text[1:] if text.startswith("-") and float(text[1:].replace(",", "")) == 0.0 else text


def latex_escape(value: str) -> str:
    return value.replace("&", r"\&").replace("%", r"\%").replace("_", r"\_")


def latex_player(player: str) -> str:
    if player.startswith("R") and player[1:].isdigit():
        return f"R_{player[1:]}"
    return player


def pct(value: float, decimals: int = 1) -> str:
    return f"{fmt(value, decimals)}\\%"


def latex_coalition(coalition: frozenset[str], players: list[str]) -> str:
    # \allowbreak lets a long coalition set wrap at a comma inside a paragraph.
    members = r",\allowbreak ".join(latex_player(p) for p in players if p in coalition)
    return f"$\\{{{members}\\}}$"


def fraction_text(value: float) -> str:
    fraction = Fraction(value).limit_denominator(24)
    if abs(float(fraction) - value) < 1e-9:
        return f"{fraction.numerator}/{fraction.denominator}"
    return fmt(value, 3)


def sweep_value(rows: list[dict[str, str]], key: str, value: float) -> dict[str, str]:
    return next(row for row in rows if abs(float(row[key]) - value) < 1e-9)


def empty_core_window(rows: list[dict[str, str]]) -> tuple[int, int]:
    """Indices of the contiguous run of positive epsilon* around its maximum."""
    peak = max(range(len(rows)), key=lambda k: float(rows[k]["epsilon_star"]))
    low = high = peak
    while low > 0 and float(rows[low - 1]["epsilon_star"]) > 1e-7:
        low -= 1
    while high < len(rows) - 1 and float(rows[high + 1]["epsilon_star"]) > 1e-7:
        high += 1
    return low, high


def write_structural_outputs(
    output: Path,
    data: dict[str, Any],
    baseline: dict[str, Any],
    grand_result: dict[str, Any],
    standalone_total: float,
    sweeps: dict[str, list[dict[str, Any]]],
    diagnosis: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    players = data["players"]
    grand = frozenset(players)
    n = len(players)
    profile = diagnosis["profiles"]["baseline"]
    structure = diagnosis["structure"]
    certificate = profile["certificate"]
    support = profile["certificate_support"]
    mu = certificate["mu"]
    grand_cost = baseline["costs"][grand]
    savings = baseline["grand_savings"]
    volume = grand_result["required_volume"]
    epsilon = profile["epsilon"]
    stability_cost = profile["cost_of_stability"]
    worst_row = baseline["core_rows"][0]
    worst_coalition = frozenset(worst_row["members"])

    # --- Structural properties -------------------------------------------
    share = lambda pair: 100.0 * pair[0] / pair[1]
    properties = [
        ("Monotonicity", r"$S\subseteq T\Rightarrow c(S)\leq c(T)$", structure["monotone"]),
        ("Subadditivity", r"$c(A)+c(B)\geq c(A\cup B)$ for disjoint $A,B$", structure["subadditive"]),
        ("Concavity (submodularity)", r"$c(A)+c(B)\geq c(A\cup B)+c(A\cap B)$", structure["concave"]),
        ("Decreasing marginal cost", r"$\Delta_x c(S)\geq \Delta_x c(T)$ for $S\subset T$", structure["marginal"]),
    ]
    property_csv = [
        {"property": name, "violations": v, "comparisons": t, "percent": f"{share((v, t)):.6f}"}
        for name, _, (v, t) in properties
    ]
    for name, key in (
        ("Concavity, union uses two processors", "concave_two_processor"),
        ("Concavity, union uses one processor", "concave_one_processor"),
    ):
        v, t = structure[key]
        property_csv.append({"property": name, "violations": v, "comparisons": t, "percent": f"{share((v, t)):.6f}"})
    write_csv(output / "structural_properties.csv", property_csv, ["property", "violations", "comparisons", "percent"])
    property_lines = [
        f"{name} & {condition} & {v:,} & {t:,} & {pct(share((v, t)))} \\\\"
        for name, condition, (v, t) in properties
    ]
    property_lines.append(r"\bottomrule")
    (output / "structural_property_rows.tex").write_text("\n".join(property_lines) + "\n", encoding="utf-8")

    # --- Balancedness certificate ----------------------------------------
    certificate_csv = []
    certificate_lines = []
    weighted_cost = 0.0
    for coalition, weight in support:
        result = baseline["results"][coalition]
        delta = weight / mu
        weighted_cost += delta * baseline["costs"][coalition]
        certificate_csv.append(
            {
                "coalition": coalition_name(coalition, players),
                "lambda": f"{weight:.8f}",
                "delta": f"{delta:.8f}",
                "cost": f"{baseline['costs'][coalition]:.8f}",
                "required_volume": f"{result['required_volume']:.6f}",
                "open_processors": ";".join(result["open_processors"]),
                "open_centers": ";".join(result["open_centers"]),
            }
        )
        certificate_lines.append(
            f"{latex_coalition(coalition, players)} & {fmt(baseline['costs'][coalition])} & "
            f"{fmt(result['required_volume'], 0)} & {latex_escape(', '.join(result['open_processors']))} & "
            f"{fraction_text(delta)} \\\\"
        )
    certificate_lines.append(r"\midrule")
    certificate_lines.append(
        rf"\multicolumn{{4}}{{l}}{{Weighted total $\sum_S\delta_S c(S)$ versus $c(N)={fmt(grand_cost)}$}} & {fmt(weighted_cost)} \\"
    )
    certificate_lines.append(r"\bottomrule")
    write_csv(
        output / "balanced_certificate.csv",
        certificate_csv,
        ["coalition", "lambda", "delta", "cost", "required_volume", "open_processors", "open_centers"],
    )
    (output / "certificate_rows.tex").write_text("\n".join(certificate_lines) + "\n", encoding="utf-8")
    coverage = {p: sum(1 for S, _ in support if p in S) for p in players}
    weights = [w for _, w in support]
    uniform_weight = max(weights) - min(weights) < 1e-9 if weights else False
    uniform_coverage = len(set(coverage.values())) == 1

    # --- Envelope and equivalence checks ---------------------------------
    envelope = diagnosis["envelope"]
    write_csv(
        output / "envelope_check.csv",
        (
            {key: (f"{value:.10f}" if isinstance(value, float) else str(value).lower() if isinstance(value, bool) else value)
             for key, value in row.items()}
            for row in envelope
        ),
        list(envelope[0]),
    )
    envelope_lines = []
    for row in envelope:
        scale, unit = (1000.0, "per 1,000 t") if row["parameter"].startswith("capacity:") else (1.0, "per unit")
        envelope_lines.append(
            f"{latex_escape(row['label'])} ({unit}) & {fmt(scale * row['predicted_d_epsilon'], 3)} & "
            f"{fmt(scale * row['finite_difference_d_epsilon'], 3)} & {fmt(scale * row['predicted_d_shapley_slack'], 3)} & "
            f"{fmt(scale * row['finite_difference_d_shapley_slack'], 3)} \\\\"
        )
    envelope_lines.append(r"\bottomrule")
    (output / "envelope_rows.tex").write_text("\n".join(envelope_lines) + "\n", encoding="utf-8")
    write_csv(
        output / "strategic_equivalence.csv",
        (
            {"variant": r["variant"], "epsilon_star": f"{r['epsilon_star']:.8f}", "max_slack_change": f"{r['max_slack_change']:.3e}"}
            for r in diagnosis["equivalence"]
        ),
        ["variant", "epsilon_star", "max_slack_change"],
    )

    # --- Heterogeneity table ----------------------------------------------
    dispersion = sweeps["dispersion_sweep"]
    dispersion_lines = [
        f"{fmt(float(row['dispersion']), 3)} & {fmt(float(row['volume_range']), 0)} & {fmt(float(row['epsilon_star']))} & "
        f"{fmt(float(row['shapley_min_slack']))} & {row['blocking_coalitions']} \\\\"
        for row in dispersion
    ]
    dispersion_lines.append(r"\bottomrule")
    (output / "dispersion_rows.tex").write_text("\n".join(dispersion_lines) + "\n", encoding="utf-8")

    # --- Regime summaries from the sweeps ---------------------------------
    capacity = sweeps["capacity_sweep"]
    cap_low, cap_high = empty_core_window(capacity)
    cap_peak = max(capacity, key=lambda r: float(r["epsilon_star"]))
    service = sweeps["service_stability_sweep"]
    service_peak = max(service, key=lambda r: float(r["epsilon_star"]))
    service_first_unstable = next(r for r in service if float(r["epsilon_star"]) > 1e-7)
    equal = sweep_value(dispersion, "dispersion", 0.0)
    dispersion_low = min(dispersion, key=lambda r: float(r["epsilon_star"]))
    platform = next(l for l, p in data["processors"].items() if p.get("requires_manufacturer_platform"))
    platform_capacity = data["processors"][platform]["capacity"]
    fits = sweep_value(capacity, "capacity", volume)
    all_points = capacity + service + dispersion + [
        profile_row(p, players, "scenario", 0.0) for p in diagnosis["profiles"].values()
    ]
    relaxed_max = max(float(r["epsilon_lp"]) for r in all_points)
    owen_points = sum(1 for r in all_points if r["owen_condition"] == "true")
    governance = next(r for r in envelope if r["parameter"] == "coalition_base")
    capacity_check = next(r for r in envelope if r["parameter"].startswith("capacity:"))
    worst_marginal = structure["worst_marginal"]

    macros = [
        "% Structural diagnosis (Chapter 4 analytical deepening).",
        rf"\newcommand{{\ChFourGrandSavings}}{{{fmt(savings, 1)}}}",
        rf"\newcommand{{\ChFourRequiredVolume}}{{{fmt(volume, 0)}}}",
        rf"\newcommand{{\ChFourPlayerCount}}{{{n}}}",
        rf"\newcommand{{\ChFourBlockingCount}}{{{len(profile['blocking'])}}}",
        rf"\newcommand{{\ChFourWorstCoalition}}{{{latex_coalition(worst_coalition, players)}}}",
        rf"\newcommand{{\ChFourWorstCoalitionPayment}}{{{fmt(worst_row['payment'])}}}",
        rf"\newcommand{{\ChFourWorstCoalitionCost}}{{{fmt(worst_row['coalition_cost'])}}}",
        rf"\newcommand{{\ChFourWorstCoalitionGain}}{{{fmt(-worst_row['slack'])}}}",
        rf"\newcommand{{\ChFourLeastCoreEpsilonShort}}{{{fmt(epsilon, 1)}}}",
        # Structural properties
        rf"\newcommand{{\ChFourMonotoneViolations}}{{{structure['monotone'][0]:,}}}",
        rf"\newcommand{{\ChFourMonotonePairs}}{{{structure['monotone'][1]:,}}}",
        rf"\newcommand{{\ChFourSubadditiveViolations}}{{{structure['subadditive'][0]:,}}}",
        rf"\newcommand{{\ChFourSubadditivePairs}}{{{structure['subadditive'][1]:,}}}",
        rf"\newcommand{{\ChFourConcaveViolations}}{{{structure['concave'][0]:,}}}",
        rf"\newcommand{{\ChFourConcavePairs}}{{{structure['concave'][1]:,}}}",
        rf"\newcommand{{\ChFourConcavePercent}}{{{pct(share(structure['concave']))}}}",
        rf"\newcommand{{\ChFourMarginalViolations}}{{{structure['marginal'][0]:,}}}",
        rf"\newcommand{{\ChFourMarginalTriples}}{{{structure['marginal'][1]:,}}}",
        rf"\newcommand{{\ChFourMarginalPercent}}{{{pct(share(structure['marginal']))}}}",
        rf"\newcommand{{\ChFourConcaveTwoProcessorPercent}}{{{pct(share(structure['concave_two_processor']))}}}",
        rf"\newcommand{{\ChFourConcaveOneProcessorPercent}}{{{pct(share(structure['concave_one_processor']))}}}",
        rf"\newcommand{{\ChFourWorstMarginalPlayer}}{{${latex_player(worst_marginal['player'])}$}}",
        rf"\newcommand{{\ChFourWorstMarginalSmall}}{{{latex_coalition(worst_marginal['smaller'], players)}}}",
        rf"\newcommand{{\ChFourWorstMarginalLarge}}{{{latex_coalition(worst_marginal['larger'], players)}}}",
        rf"\newcommand{{\ChFourWorstMarginalEarly}}{{{fmt(worst_marginal['early'])}}}",
        rf"\newcommand{{\ChFourWorstMarginalLate}}{{{fmt(worst_marginal['late'])}}}",
        # Balancedness certificate
        rf"\newcommand{{\ChFourCertificateSize}}{{{len(support)}}}",
        rf"\newcommand{{\ChFourCertificateWithManufacturer}}{{{sum(1 for S, _ in support if data['manufacturer'] in S)}}}",
        rf"\newcommand{{\ChFourCertificateWeight}}{{{fraction_text(weights[0] / mu) if uniform_weight else 'unequal'}}}",
        rf"\newcommand{{\ChFourCertificateCoverage}}{{{next(iter(coverage.values())) if uniform_coverage else 'unequal'}}}",
        rf"\newcommand{{\ChFourCertificateCost}}{{{fmt(weighted_cost)}}}",
        rf"\newcommand{{\ChFourCertificateUnique}}{{{'unique' if certificate['unique'] else 'not unique'}}}",
        rf"\newcommand{{\ChFourEnvelopeMu}}{{{fmt(mu, 2)}}}",
        rf"\newcommand{{\ChFourEnvelopeLambda}}{{{fmt(weights[0], 2) if uniform_weight else 'unequal'}}}",
        # Linear relaxation and bounds
        rf"\newcommand{{\ChFourRelaxedGrandCost}}{{{fmt(profile['lp_costs'][grand])}}}",
        rf"\newcommand{{\ChFourRelaxedEpsilon}}{{{fmt(profile['epsilon_lp'], 2)}}}",
        rf"\newcommand{{\ChFourRelaxedEpsilonMax}}{{{fmt(relaxed_max, 2)}}}",
        rf"\newcommand{{\ChFourRelaxedShapleySlack}}{{{fmt(allocation_slack(shapley_value(profile['lp_costs'], players), profile['lp_costs'], players), 1)}}}",
        rf"\newcommand{{\ChFourIntegralityGap}}{{{fmt(profile['integrality_gap'])}}}",
        rf"\newcommand{{\ChFourOwenPoints}}{{{owen_points}}}",
        rf"\newcommand{{\ChFourDiagnosisPoints}}{{{len(all_points)}}}",
        rf"\newcommand{{\ChFourCostOfStability}}{{{fmt(stability_cost)}}}",
        rf"\newcommand{{\ChFourCoSLowerBound}}{{{fmt(n / (n - 1) * epsilon, 2)}}}",
        rf"\newcommand{{\ChFourCoSUpperBound}}{{{fmt(n * epsilon, 2)}}}",
        rf"\newcommand{{\ChFourEpsilonShareCost}}{{{pct(100.0 * epsilon / grand_cost, 2)}}}",
        rf"\newcommand{{\ChFourEpsilonPerTon}}{{{fmt(1000.0 * epsilon / volume, 2)}}}",
        rf"\newcommand{{\ChFourEpsilonShareSavings}}{{{pct(100.0 * epsilon / savings)}}}",
        rf"\newcommand{{\ChFourCoSShareSavings}}{{{pct(100.0 * stability_cost / savings)}}}",
        rf"\newcommand{{\ChFourMinSlackShareCost}}{{{pct(-100.0 * worst_row['slack'] / grand_cost, 2)}}}",
        rf"\newcommand{{\ChFourMinSlackPerTon}}{{{fmt(-1000.0 * worst_row['slack'] / volume, 2)}}}",
        rf"\newcommand{{\ChFourMinSlackShareCoalition}}{{{pct(-100.0 * worst_row['slack'] / worst_row['coalition_cost'], 2)}}}",
        # Comparative statics
        rf"\newcommand{{\ChFourEnvGovPredicted}}{{{fmt(governance['predicted_d_epsilon'], 2)}}}",
        rf"\newcommand{{\ChFourEnvGovDifference}}{{{fmt(governance['finite_difference_d_epsilon'], 2)}}}",
        rf"\newcommand{{\ChFourEnvGovSlack}}{{{fmt(governance['predicted_d_shapley_slack'], 2)}}}",
        rf"\newcommand{{\ChFourShadowPricePlatform}}{{{fmt(-1000.0 * capacity_check['grand_derivative'], 1)}}}",
        rf"\newcommand{{\ChFourEnvCapPredicted}}{{{fmt(1000.0 * capacity_check['predicted_d_epsilon'], 3)}}}",
        rf"\newcommand{{\ChFourEnvCapDifference}}{{{fmt(1000.0 * capacity_check['finite_difference_d_epsilon'], 3)}}}",
        rf"\newcommand{{\ChFourPlatformCapacity}}{{{fmt(platform_capacity, 0)}}}",
        rf"\newcommand{{\ChFourCapWindowLow}}{{{fmt(float(capacity[cap_low]['capacity']), 0)}}}",
        rf"\newcommand{{\ChFourCapWindowHigh}}{{{fmt(float(capacity[cap_high]['capacity']), 0)}}}",
        rf"\newcommand{{\ChFourCapStableBelow}}{{{fmt(float(capacity[cap_low - 1]['capacity']), 0) if cap_low > 0 else 'none'}}}",
        rf"\newcommand{{\ChFourCapStableBelowEpsilon}}{{{fmt(float(capacity[cap_low - 1]['epsilon_star'])) if cap_low > 0 else 'none'}}}",
        rf"\newcommand{{\ChFourCapStableAbove}}{{{fmt(float(capacity[cap_high + 1]['capacity']), 0) if cap_high + 1 < len(capacity) else 'none'}}}",
        rf"\newcommand{{\ChFourCapPeakEpsilon}}{{{fmt(float(cap_peak['epsilon_star']))}}}",
        rf"\newcommand{{\ChFourCapPeakAt}}{{{fmt(float(cap_peak['capacity']), 0)}}}",
        rf"\newcommand{{\ChFourCapFitsEpsilon}}{{{fmt(float(fits['epsilon_star']))}}}",
        rf"\newcommand{{\ChFourCapFitsShapleySlack}}{{{fmt(float(fits['shapley_min_slack']))}}}",
        rf"\newcommand{{\ChFourServiceThreshold}}{{{fmt(platform_capacity / (volume / grand_result['service_rate']), 3)}}}",
        rf"\newcommand{{\ChFourServiceLowAt}}{{{fmt(float(service[0]['service_rate']), 2)}}}",
        rf"\newcommand{{\ChFourServiceLowEpsilon}}{{{fmt(float(service[0]['epsilon_star']))}}}",
        rf"\newcommand{{\ChFourServiceLowShapleySlack}}{{{fmt(float(service[0]['shapley_min_slack']))}}}",
        rf"\newcommand{{\ChFourServiceFirstUnstable}}{{{fmt(float(service_first_unstable['service_rate']), 2)}}}",
        rf"\newcommand{{\ChFourServicePeakEpsilon}}{{{fmt(float(service_peak['epsilon_star']))}}}",
        rf"\newcommand{{\ChFourServicePeakAt}}{{{fmt(float(service_peak['service_rate']), 2)}}}",
        # Heterogeneity
        rf"\newcommand{{\ChFourEqualVolumeEach}}{{{fmt(volume / grand_result['service_rate'] / len(data['retailers']), 0)}}}",
        rf"\newcommand{{\ChFourEqualVolumeEpsilon}}{{{fmt(float(equal['epsilon_star']))}}}",
        rf"\newcommand{{\ChFourEqualVolumeBlocking}}{{{equal['blocking_coalitions']}}}",
        rf"\newcommand{{\ChFourDispersionMinEpsilon}}{{{fmt(float(dispersion_low['epsilon_star']))}}}",
        rf"\newcommand{{\ChFourDispersionMinAt}}{{{fmt(float(dispersion_low['dispersion']), 3)}}}",
    ]

    summary = {
        "structural_properties": {
            key: {"violations": value[0], "comparisons": value[1]}
            for key, value in structure.items()
            if key != "worst_marginal"
        },
        "worst_marginal_violation": {
            "player": worst_marginal["player"],
            "smaller": coalition_name(worst_marginal["smaller"], players),
            "larger": coalition_name(worst_marginal["larger"], players),
            "early": worst_marginal["early"],
            "late": worst_marginal["late"],
        },
        "epsilon_unrestricted": epsilon,
        "epsilon_nonnegative": profile["epsilon_nonnegative"],
        "nonnegativity_binds": abs(profile["epsilon_nonnegative"] - epsilon) > 1e-6,
        "certificate": {
            "mu": mu,
            "unique": certificate["unique"],
            "coalitions": {coalition_name(S, players): w for S, w in support},
            "weighted_cost": weighted_cost,
            "coverage": coverage,
        },
        "relaxed_grand_cost": profile["lp_costs"][grand],
        "relaxed_epsilon": profile["epsilon_lp"],
        "relaxed_epsilon_max_over_all_points": relaxed_max,
        "integrality_gap": profile["integrality_gap"],
        "owen_condition_points": f"{owen_points}/{len(all_points)}",
        "cost_of_stability": stability_cost,
        "envelope_check": envelope,
        "strategic_equivalence": diagnosis["equivalence"],
    }
    return summary, macros


def write_generated(
    output: Path,
    data: dict[str, Any],
    games: dict[str, dict[str, Any]],
    rule_results: dict[str, Any],
    sweeps: dict[str, list[dict[str, float]]],
    diagnosis: dict[str, Any],
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    players = data["players"]
    baseline = games["baseline"]
    grand = frozenset(players)
    grand_result = baseline["results"][grand]

    coalition_rows = []
    for scenario_name, game in games.items():
        for coalition in powerset(players):
            result = game["results"][coalition]
            coalition_rows.append(
                {
                    "scenario": scenario_name,
                    "coalition": result["coalition"],
                    "cost": f"{result['cost']:.8f}",
                    "service_rate": f"{result['service_rate']:.6f}",
                    "required_volume": f"{result['required_volume']:.6f}",
                    "recovered_output": f"{result['recovered_output']:.6f}",
                    "unit_cost": f"{result['unit_cost']:.8f}",
                    "open_centers": ";".join(result["open_centers"]),
                    "open_processors": ";".join(result["open_processors"]),
                    "solver": result["solver"],
                }
            )
    write_csv(
        output / "coalition_costs.csv",
        coalition_rows,
        [
            "scenario", "coalition", "cost", "service_rate", "required_volume",
            "recovered_output", "unit_cost", "open_centers", "open_processors", "solver",
        ],
    )

    allocation_rows = []
    for player in players:
        standalone = baseline["costs"][frozenset({player})]
        allocation = baseline["shapley"][player]
        allocation_rows.append(
            {
                "player": player,
                "standalone_cost": f"{standalone:.8f}",
                "shapley_allocation": f"{allocation:.8f}",
                "savings": f"{standalone - allocation:.8f}",
                "savings_percent": f"{100.0 * (standalone - allocation) / standalone:.6f}",
                "individual_rational": str(allocation <= standalone + TOL).lower(),
            }
        )
    write_csv(
        output / "baseline_allocations.csv",
        allocation_rows,
        ["player", "standalone_cost", "shapley_allocation", "savings", "savings_percent", "individual_rational"],
    )
    write_csv(
        output / "core_slacks.csv",
        (
            {
                "coalition": row["coalition"],
                "payment": f"{row['payment']:.8f}",
                "coalition_cost": f"{row['coalition_cost']:.8f}",
                "slack": f"{row['slack']:.8f}",
            }
            for row in baseline["core_rows"]
        ),
        ["coalition", "payment", "coalition_cost", "slack"],
    )

    profiles = diagnosis["profiles"]
    sensitivity_rows = []
    for scenario_name, game in games.items():
        sensitivity_rows.append(
            {
                "scenario": scenario_name,
                "grand_cost": f"{game['costs'][grand]:.8f}",
                "manufacturer_allocation": f"{game['shapley'][data['manufacturer']]:.8f}",
                "minimum_core_slack": f"{game['minimum_core_slack']:.8f}",
                "epsilon_star": f"{profiles[scenario_name]['epsilon']:.8f}",
                "cost_of_stability": f"{profiles[scenario_name]['cost_of_stability']:.8f}",
            }
        )
    write_csv(
        output / "sensitivity.csv",
        sensitivity_rows,
        [
            "scenario", "grand_cost", "manufacturer_allocation", "minimum_core_slack",
            "epsilon_star", "cost_of_stability",
        ],
    )
    rule_rows = []
    for name, result in rule_results["rules"].items():
        rule_rows.append(
            {
                "rule": name,
                "manufacturer_share": f"{result['manufacturer_share']:.8f}",
                "largest_retailer_share": f"{result['largest_retailer_share']:.8f}",
                "minimum_core_slack": f"{result['minimum_core_slack']:.8f}",
            }
        )
    write_csv(
        output / "allocation_rules.csv",
        rule_rows,
        ["rule", "manufacturer_share", "largest_retailer_share", "minimum_core_slack"],
    )
    for name, rows in sweeps.items():
        fields = list(rows[0])
        write_csv(output / f"{name}.csv", rows, fields)

    standalone_total = sum(baseline["costs"][frozenset({p})] for p in players)
    structural_summary, structural_macros = write_structural_outputs(
        output, data, baseline, grand_result, standalone_total, sweeps, diagnosis
    )
    summary = {
        "dataset": data["metadata"],
        "players": players,
        "coalitions_solved_per_scenario": len(powerset(players)),
        "baseline": {
            "grand_cost": baseline["costs"][grand],
            "standalone_total": standalone_total,
            "grand_savings": baseline["grand_savings"],
            "grand_savings_percent": 100.0 * baseline["grand_savings"] / standalone_total,
            "minimum_core_slack": baseline["minimum_core_slack"],
            "shapley": baseline["shapley"],
            "service_rate": grand_result["service_rate"],
            "required_volume": grand_result["required_volume"],
            "recovered_output": grand_result["recovered_output"],
            "unit_cost": grand_result["unit_cost"],
            "open_centers": grand_result["open_centers"],
            "open_processors": grand_result["open_processors"],
        },
        "least_core_epsilon": rule_results["epsilon_star"],
        "manufacturer_support_used": rule_results["manufacturer_support"],
        "allocation_rules": rule_results["rules"],
        "sensitivity": {
            name: {
                "grand_cost": game["costs"][grand],
                "manufacturer_allocation": game["shapley"][data["manufacturer"]],
                "minimum_core_slack": game["minimum_core_slack"],
            }
            for name, game in games.items()
        },
    }
    summary["structural_diagnosis"] = structural_summary
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    macros = [
        "% Generated by solve_chapter4.py; do not edit.",
        rf"\newcommand{{\ChFourGrandCost}}{{{fmt(baseline['costs'][grand], 1)}}}",
        rf"\newcommand{{\ChFourStandaloneTotal}}{{{fmt(standalone_total, 1)}}}",
        rf"\newcommand{{\ChFourSavingsPercent}}{{{fmt(summary['baseline']['grand_savings_percent'], 1)}\%}}",
        rf"\newcommand{{\ChFourServiceRate}}{{{fmt(100.0 * grand_result['service_rate'], 1)}\%}}",
        rf"\newcommand{{\ChFourRecoveredOutput}}{{{fmt(grand_result['recovered_output'], 1)}}}",
        rf"\newcommand{{\ChFourMinSlack}}{{{fmt(baseline['minimum_core_slack'], 1)}}}",
        rf"\newcommand{{\ChFourManufacturerAllocation}}{{{fmt(baseline['shapley'][data['manufacturer']], 1)}}}",
        rf"\newcommand{{\ChFourOpenCenters}}{{{latex_escape(', '.join(grand_result['open_centers']))}}}",
        rf"\newcommand{{\ChFourOpenProcessors}}{{{latex_escape(', '.join(grand_result['open_processors']))}}}",
        rf"\newcommand{{\ChFourLeastCoreEpsilon}}{{{fmt(rule_results['epsilon_star'], 2)}}}",
        rf"\newcommand{{\ChFourSupportBudget}}{{{fmt(rule_results['manufacturer_support'], 1)}}}",
    ]
    macros.extend(structural_macros)
    (output / "case_results.tex").write_text("\n".join(macros) + "\n", encoding="utf-8")

    allocation_lines = []
    for row in allocation_rows:
        player = row["player"]
        standalone = float(row["standalone_cost"])
        allocation = float(row["shapley_allocation"])
        savings_pct = float(row["savings_percent"])
        allocation_lines.append(
            f"${latex_player(player)}$ & {fmt(standalone)} & {fmt(allocation)} & {fmt(savings_pct, 1)}\\% \\\\"
        )
    allocation_lines.append(
        rf"\textbf{{Total}} & \textbf{{{fmt(standalone_total)}}} & \textbf{{{fmt(baseline['costs'][grand])}}} & \textbf{{{fmt(summary['baseline']['grand_savings_percent'], 1)}\%}} \\"
    )
    allocation_lines.append(r"\bottomrule")
    (output / "allocation_table_rows.tex").write_text("\n".join(allocation_lines) + "\n", encoding="utf-8")

    core_lines = []
    for row in baseline["core_rows"][:6]:
        members = ",".join(latex_player(member) for member in row["members"])
        core_lines.append(
            f"$\\{{{members}\\}}$ & {fmt(row['payment'])} & {fmt(row['coalition_cost'])} & {fmt(row['slack'])} \\\\"
        )
    core_lines.append(r"\bottomrule")
    (output / "core_table_rows.tex").write_text("\n".join(core_lines) + "\n", encoding="utf-8")

    rule_lines = [
        f"{latex_escape(name)} & {fmt(result['manufacturer_share'])} & {fmt(result['largest_retailer_share'])} & {fmt(result['minimum_core_slack'])} \\\\"
        for name, result in rule_results["rules"].items()
    ]
    rule_lines.append(r"\bottomrule")
    (output / "allocation_rule_rows.tex").write_text("\n".join(rule_lines) + "\n", encoding="utf-8")

    scenario_labels = {
        "baseline": "Baseline network",
        "service_target_90": r"Formal-service target reduced to 90\%",
        "restricted_processor_access": r"High-standard processor unavailable",
        "governance_cost_25": r"Governance cost increases by 25\%",
        "volume_20": r"Return volume increases by 20\%",
        "recovery_value_20": r"Recovered-material value increases by 20\%",
        "transportation_25": r"Transportation cost increases by 25\%",
    }
    sensitivity_lines = [
        f"{scenario_labels[name]} & {fmt(game['costs'][grand])} & {fmt(game['shapley'][data['manufacturer']])} & {fmt(game['minimum_core_slack'])} \\\\"
        for name, game in games.items()
    ]
    support_result = rule_results["rules"]["Manufacturer responsibility shift"]
    sensitivity_lines.append(
        f"Manufacturer responsibility shift & {fmt(baseline['costs'][grand])} & {fmt(support_result['manufacturer_share'])} & {fmt(support_result['minimum_core_slack'])} \\\\"
    )
    sensitivity_lines.append(r"\bottomrule")
    (output / "sensitivity_table_rows.tex").write_text("\n".join(sensitivity_lines) + "\n", encoding="utf-8")

    # Same scenarios with the structural stability measure alongside the
    # Shapley slack, so rule-specific and structural instability can be told apart.
    stability_lines = [
        f"{scenario_labels[name]} & {fmt(game['costs'][grand])} & {fmt(game['shapley'][data['manufacturer']])} & {fmt(game['minimum_core_slack'])} & {fmt(profiles[name]['epsilon'])} \\\\"
        for name, game in games.items()
    ]
    stability_lines.append(
        f"Manufacturer responsibility shift & {fmt(baseline['costs'][grand])} & {fmt(support_result['manufacturer_share'])} & {fmt(support_result['minimum_core_slack'])} & {fmt(profiles['baseline']['epsilon'])} \\\\"
    )
    stability_lines.append(r"\bottomrule")
    (output / "sensitivity_stability_rows.tex").write_text("\n".join(stability_lines) + "\n", encoding="utf-8")


    parameters = [
        "% Generated parameter rows; do not edit.",
        r"NV & 6,500 & 300 & 35 \\",
        r"TN & 6,000 & 260 & 32 \\",
        r"MI & 5,000 & 230 & 30 \\",
        r"GA & 5,000 & 220 & 28 \\",
        r"\bottomrule",
    ]
    (output / "center_parameter_rows.tex").write_text("\n".join(parameters) + "\n", encoding="utf-8")

    digest = hashlib.sha256()
    for path in sorted(output.iterdir(), key=lambda p: p.name):
        if path.name == "manifest.sha256":
            continue
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    (output / "manifest.sha256").write_text(digest.hexdigest() + "\n", encoding="utf-8")


def run_sweep(
    data: dict[str, Any], requested_solver: str, kind: str, values: list[float]
) -> list[dict[str, float]]:
    players = data["players"]
    grand = frozenset(players)
    rows: list[dict[str, float]] = []
    for value in values:
        if kind == "service_rate_sweep":
            scenario = {"formal_service_rate": value}
            result = solve_coalition(data, grand, scenario, requested_solver)
            rows.append({"service_rate": value, "grand_cost": result["cost"]})
        elif kind == "recovery_sweep":
            game = solve_game(data, {"recovery_multiplier": value}, requested_solver)
            rows.append({"recovery_index": value, "grand_savings": game["grand_savings"]})
        elif kind == "capacity_sweep":
            platform = next(
                l for l, p in data["processors"].items() if p.get("requires_manufacturer_platform")
            )
            profile = stability_profile(
                data, {"processor_capacity_override": {platform: value}}, requested_solver
            )
            rows.append(profile_row(profile, players, "capacity", value))
        elif kind == "service_stability_sweep":
            profile = stability_profile(data, {"formal_service_rate": value}, requested_solver)
            rows.append(profile_row(profile, players, "service_rate", value))
        elif kind == "dispersion_sweep":
            profile = stability_profile(data, {"volume_dispersion": value}, requested_solver)
            row = profile_row(profile, players, "dispersion", value)
            mean = sum(r["volume"] for r in data["retailers"].values()) / len(data["retailers"])
            volumes = [mean + value * (r["volume"] - mean) for r in data["retailers"].values()]
            row["volume_range"] = f"{max(volumes) - min(volumes):.6f}"
            rows.append(row)
        elif kind == "governance_sweep":
            game = solve_game(
                data, {"governance_cost_multiplier": value}, requested_solver
            )
            rows.append(
                {
                    "governance_cost_index": value,
                    "manufacturer_allocation": game["shapley"][data["manufacturer"]],
                }
            )
        else:
            raise ValueError(kind)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--solver", default="SCIP")
    args = parser.parse_args()
    data = json.loads(args.data.read_text(encoding="utf-8"))
    scenarios = {
        "baseline": {},
        "service_target_90": {"formal_service_rate": 0.90},
        "restricted_processor_access": {"processor_access_override": {"H": 0}},
        "governance_cost_25": {"governance_cost_multiplier": 1.25},
        "volume_20": {"volume_multiplier": 1.20},
        "recovery_value_20": {"recovery_multiplier": 1.20},
        "transportation_25": {"transport_multiplier": 1.25},
    }
    profiles = {
        name: stability_profile(data, scenario, args.solver, check_unique=(name == "baseline"))
        for name, scenario in scenarios.items()
    }
    games = {name: profile["game"] for name, profile in profiles.items()}
    rule_results = allocation_rules(data, games["baseline"])
    baseline_profile = profiles["baseline"]
    capacity_grid = sorted(set(range(6000, 15001, 250)) | {9800, 10600, 12400})
    diagnosis = {
        "profiles": profiles,
        "structure": structural_properties(games["baseline"], data["players"]),
        "envelope": envelope_check(data, baseline_profile, args.solver),
        "equivalence": strategic_equivalence_check(data, baseline_profile, args.solver),
    }
    sweeps = {
        "service_rate_sweep": run_sweep(
            data, args.solver, "service_rate_sweep", [0.80, 0.85, 0.90, 0.95, 1.00]
        ),
        "recovery_sweep": run_sweep(data, args.solver, "recovery_sweep", [0.80, 0.90, 1.00, 1.10, 1.20]),
        "governance_sweep": run_sweep(
            data, args.solver, "governance_sweep", [0.80, 0.90, 1.00, 1.10, 1.25]
        ),
        "allocation_slack": [
            {"rule": name, "minimum_core_slack": result["minimum_core_slack"]}
            for name, result in rule_results["rules"].items()
        ],
        "capacity_sweep": run_sweep(data, args.solver, "capacity_sweep", capacity_grid),
        "service_stability_sweep": run_sweep(
            data, args.solver, "service_stability_sweep", [round(0.80 + 0.01 * k, 2) for k in range(21)]
        ),
        "dispersion_sweep": run_sweep(
            data, args.solver, "dispersion_sweep", [k / 8 for k in range(9)]
        ),
    }
    write_generated(args.output, data, games, rule_results, sweeps, diagnosis)
    print(json.dumps({
        "grand_cost": games["baseline"]["costs"][frozenset(data["players"])],
        "grand_savings": games["baseline"]["grand_savings"],
        "minimum_core_slack": games["baseline"]["minimum_core_slack"],
        "least_core_epsilon": rule_results["epsilon_star"],
        "cost_of_stability": baseline_profile["cost_of_stability"],
        "relaxed_least_core_epsilon": baseline_profile["epsilon_lp"],
        "output": str(args.output),
    }, indent=2))


if __name__ == "__main__":
    main()
