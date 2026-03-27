"""
Sensitivity / Post-Optimality Analysis Engine.
Computes objective coefficient ranging and RHS (right-hand side) ranging
from the final simplex tableau, along with shadow prices (dual values).
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field


@dataclass
class ObjRange:
    """Ranging result for one objective coefficient."""
    variable: str
    current_value: float
    allowable_increase: float  # can be np.inf
    allowable_decrease: float  # can be np.inf


@dataclass
class RhsRange:
    """Ranging result for one RHS constraint."""
    constraint_index: int  # 1-based
    current_rhs: float
    shadow_price: float
    allowable_increase: float
    allowable_decrease: float


@dataclass
class SensitivityResult:
    """Full sensitivity analysis output."""
    objective_ranges: list = field(default_factory=list)
    rhs_ranges: list = field(default_factory=list)
    is_available: bool = False


def compute_sensitivity(problem: dict, result) -> SensitivityResult:
    """
    Compute sensitivity analysis from the final simplex tableau.

    Parameters
    ----------
    problem : dict
        The original problem dict with keys: goal, variables, objective, constraints.
    result : SimplexResult
        The result object from the simplex solver (must have status='optimal').

    Returns
    -------
    SensitivityResult
    """
    sens = SensitivityResult()

    if result.status != "optimal" or not result.tableaux:
        return sens

    final_tableau = result.tableaux[-1]
    variables = list(problem["variables"])
    constraints = problem["constraints"]
    objective = [float(c) for c in problem["objective"]]
    num_vars = len(variables)
    num_constraints = len(constraints)
    is_min = problem["goal"].lower() == "minimize"

    # Convert final tableau to numpy
    tab = final_tableau.values.astype(float)
    col_labels = list(final_tableau.columns)
    row_labels = list(final_tableau.index)

    # Z row is row 0
    z_row = tab[0, :]

    # ── Identify basic variables and their rows ────────────────────
    basis_map = {}  # variable_name -> row_index (0-based in tab)
    for r in range(1, tab.shape[0]):
        basis_map[row_labels[r]] = r

    # ── 1. Objective Coefficient Ranging ───────────────────────────
    for i, var in enumerate(variables):
        c_current = objective[i]
        col_idx = col_labels.index(var) if var in col_labels else -1
        if col_idx < 0:
            sens.objective_ranges.append(ObjRange(var, c_current, np.inf, np.inf))
            continue

        if var in basis_map:
            # Variable is basic → use ratios of Z-row to column entries
            basic_row = basis_map[var]
            allow_inc = np.inf
            allow_dec = np.inf

            for j in range(len(col_labels) - 1):  # exclude RHS
                if j == col_idx:
                    continue
                col_name = col_labels[j]
                z_j = z_row[j]
                a_ij = tab[basic_row, j]

                if abs(a_ij) < 1e-12:
                    continue

                ratio = z_j / a_ij

                if a_ij > 1e-12:
                    # Positive element
                    if ratio >= -1e-12:
                        allow_inc = min(allow_inc, abs(ratio))
                    else:
                        allow_dec = min(allow_dec, abs(ratio))
                else:
                    # Negative element
                    if ratio >= -1e-12:
                        allow_dec = min(allow_dec, abs(ratio))
                    else:
                        allow_inc = min(allow_inc, abs(ratio))

            if is_min:
                allow_inc, allow_dec = allow_dec, allow_inc

            sens.objective_ranges.append(ObjRange(var, c_current, allow_inc, allow_dec))
        else:
            # Variable is non-basic → range is determined by reduced cost
            reduced_cost = z_row[col_idx]
            if is_min:
                reduced_cost = -reduced_cost
            sens.objective_ranges.append(ObjRange(
                var, c_current,
                np.inf,
                abs(reduced_cost) if abs(reduced_cost) > 1e-12 else np.inf,
            ))

    # ── 2. RHS Ranging & Shadow Prices ─────────────────────────────
    # Shadow prices come from the Z row entries for slack/surplus variables
    slack_surplus_cols = []
    for j, name in enumerate(col_labels):
        if name.startswith("s") and not name.startswith("su"):
            slack_surplus_cols.append((j, name))
        elif name.startswith("su"):
            slack_surplus_cols.append((j, name))

    for c_idx in range(num_constraints):
        rhs = float(constraints[c_idx]["rhs"])
        sign = constraints[c_idx]["sign"].strip()

        # Shadow price from the Z-row coefficient of the slack/surplus
        shadow = 0.0
        slack_col_idx = -1
        if c_idx < len(slack_surplus_cols):
            slack_col_idx = slack_surplus_cols[c_idx][0]
            shadow = z_row[slack_col_idx]
            if sign == ">=":
                shadow = -shadow
            if is_min:
                shadow = -shadow

        # RHS ranging
        allow_inc = np.inf
        allow_dec = np.inf

        if slack_col_idx >= 0:
            for r in range(1, tab.shape[0]):
                entry = tab[r, slack_col_idx]
                rhs_val = tab[r, -1]

                if abs(entry) < 1e-12:
                    continue

                ratio = rhs_val / entry
                if entry > 1e-12:
                    allow_inc = min(allow_inc, ratio)
                else:
                    allow_dec = min(allow_dec, -ratio)

        sens.rhs_ranges.append(RhsRange(
            constraint_index=c_idx + 1,
            current_rhs=rhs,
            shadow_price=round(shadow, 6),
            allowable_increase=round(allow_inc, 6) if allow_inc != np.inf else np.inf,
            allowable_decrease=round(allow_dec, 6) if allow_dec != np.inf else np.inf,
        ))

    sens.is_available = True
    return sens
