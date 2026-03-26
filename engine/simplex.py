"""
Simplex Method Core Engine
Handles: Standard form conversion, pivot selection, row operations, iteration loop.
Detects: Optimal, Infeasible, Unbounded, and Degenerate solutions.
"""

import numpy as np
import pandas as pd
from copy import deepcopy

MAX_ITERATIONS = 100


class SimplexResult:
    """Container for the complete result of a Simplex solve."""

    def __init__(self):
        self.status = ""            # 'optimal', 'infeasible', 'unbounded', 'max_iterations'
        self.optimal_value = None
        self.variables = {}         # {'x1': 3.0, 'x2': 5.0, ...}
        self.iterations = 0
        self.tableaux = []          # list of tableau snapshots (DataFrames)
        self.pivot_cells = []       # list of (row_idx, col_idx) for highlighting
        self.messages = []          # informational messages

    def to_dict(self):
        return {
            "status": self.status,
            "optimal_value": self.optimal_value,
            "variables": self.variables,
            "iterations": self.iterations,
            "messages": self.messages,
        }


def solve(problem: dict) -> SimplexResult:
    """
    Main entry point. Accepts a problem dict with keys:
        goal:        'maximize' or 'minimize'
        variables:   ['x1', 'x2', ...]
        objective:   [c1, c2, ...]
        constraints: [{'coefficients': [...], 'sign': '<=', 'rhs': float}, ...]

    Returns a SimplexResult.
    """
    result = SimplexResult()

    # ── Validate input ──────────────────────────────────────────────
    try:
        _validate_problem(problem)
    except ValueError as e:
        result.status = "error"
        result.messages.append(str(e))
        return result

    goal = problem["goal"].lower()
    variables = list(problem["variables"])
    objective = list(map(float, problem["objective"]))
    constraints = deepcopy(problem["constraints"])
    num_vars = len(variables)
    num_constraints = len(constraints)

    # ── Handle minimisation by negating objective ────────────────────
    is_min = goal == "minimize"
    if is_min:
        objective = [-c for c in objective]

    # ── Build augmented matrix (Standard Form) ──────────────────────
    # Columns: decision vars | slack/surplus/artificial | RHS
    slack_count = 0
    surplus_count = 0
    artificial_count = 0
    artificial_indices = []

    col_names = list(variables)
    rows = []

    for i, con in enumerate(constraints):
        coeffs = list(map(float, con["coefficients"]))
        sign = con["sign"].strip()
        rhs = float(con["rhs"])

        # Ensure RHS >= 0 (multiply through by -1 if needed)
        if rhs < 0:
            coeffs = [-c for c in coeffs]
            rhs = -rhs
            if sign == "<=":
                sign = ">="
            elif sign == ">=":
                sign = "<="

        if sign == "<=":
            slack_count += 1
            col_names.append(f"s{slack_count}")
            slack_col = [0.0] * len(rows)
            for r in rows:
                r.insert(len(r) - 1, 0.0)  # add 0 for this slack in previous rows
            row = coeffs + [0.0] * (len(col_names) - num_vars - 1) + [1.0, rhs]
            # Pad to correct length
            while len(row) < len(col_names) + 1:
                row.insert(-1, 0.0)
            rows.append(row)

        elif sign == ">=":
            surplus_count += 1
            artificial_count += 1
            s_name = f"su{surplus_count}"
            a_name = f"a{artificial_count}"
            col_names.append(s_name)
            col_names.append(a_name)
            artificial_indices.append(len(col_names) - 1)  # 0-based col index of artificial
            for r in rows:
                r.insert(len(r) - 1, 0.0)
                r.insert(len(r) - 1, 0.0)
            row = coeffs + [0.0] * (len(col_names) - num_vars - 2) + [-1.0, 1.0, rhs]
            while len(row) < len(col_names) + 1:
                row.insert(-1, 0.0)
            rows.append(row)

        elif sign == "=":
            artificial_count += 1
            a_name = f"a{artificial_count}"
            col_names.append(a_name)
            artificial_indices.append(len(col_names) - 1)
            for r in rows:
                r.insert(len(r) - 1, 0.0)
            row = coeffs + [0.0] * (len(col_names) - num_vars - 1) + [1.0, rhs]
            while len(row) < len(col_names) + 1:
                row.insert(-1, 0.0)
            rows.append(row)

    total_cols = len(col_names)  # excluding RHS

    # ── Normalise all rows to same width ─────────────────────────────
    width = total_cols + 1  # +1 for RHS
    for r in rows:
        while len(r) < width:
            r.insert(-1, 0.0)

    # ── Build objective row (Z row) ──────────────────────────────────
    # Z row: -c1, -c2, ... 0 (slacks) ... | 0 (RHS)
    z_row = [-c for c in objective] + [0.0] * (total_cols - num_vars) + [0.0]
    while len(z_row) < width:
        z_row.insert(-1, 0.0)

    # ── Big-M for artificial variables ───────────────────────────────
    M = 1e6
    if artificial_indices:
        for ai in artificial_indices:
            z_row[ai] = M  # penalise artificial in objective
        # Adjust Z row to remove artificial from basis representation
        for i, row in enumerate(rows):
            for ai in artificial_indices:
                if abs(row[ai] - 1.0) < 1e-9:
                    # This row has this artificial as basic — subtract M * row from z_row
                    z_row = [z_row[j] - M * row[j] for j in range(width)]
                    break

    # ── Assemble full tableau (Z row on top) ─────────────────────────
    tableau = np.array([z_row] + rows, dtype=float)
    col_labels = col_names + ["RHS"]

    # Track basic variable for each constraint row
    basis = []
    for i in range(num_constraints):
        row_idx = i + 1  # +1 because Z row is row 0
        # find which column is the basic variable (identity column for this row)
        found_basis = False
        for j in range(total_cols):
            col = tableau[:, j]
            if abs(col[row_idx] - 1.0) < 1e-9 and abs(sum(col) - 1.0) < 1e-9:
                basis.append(col_labels[j])
                found_basis = True
                break
        if not found_basis:
            basis.append(f"a{i+1}" if artificial_indices else f"s{i+1}")

    # ── Snapshot initial tableau ─────────────────────────────────────
    result.tableaux.append(_snapshot(tableau, col_labels, basis))

    # ── Iteration loop ───────────────────────────────────────────────
    for iteration in range(1, MAX_ITERATIONS + 1):
        z_row_vals = tableau[0, :total_cols]

        # Check optimality: all Z-row coefficients >= 0
        if all(v >= -1e-9 for v in z_row_vals):
            # Check if any artificial variable is still in basis with nonzero value
            if artificial_indices:
                for bi, bname in enumerate(basis):
                    if bname.startswith("a"):
                        val = tableau[bi + 1, -1]
                        if abs(val) > 1e-9:
                            result.status = "infeasible"
                            result.iterations = iteration - 1
                            result.messages.append("No feasible solution exists. An artificial variable remained in the basis with a nonzero value.")
                            return result

            result.status = "optimal"
            result.iterations = iteration - 1

            # Extract solution
            opt_val = tableau[0, -1]
            if is_min:
                opt_val = -opt_val
            result.optimal_value = round(opt_val, 6)

            for v in variables:
                if v in col_labels:
                    ci = col_labels.index(v)
                    col = tableau[:, ci]
                    if _is_basic_column(col):
                        row_i = np.argmax(np.abs(col))
                        result.variables[v] = round(tableau[row_i, -1], 6)
                    else:
                        result.variables[v] = 0.0
                else:
                    result.variables[v] = 0.0

            return result

        # ── Pivot column: most negative in Z row ─────────────────────
        pivot_col = int(np.argmin(z_row_vals))

        # ── Ratio test for pivot row ─────────────────────────────────
        ratios = []
        for i in range(1, tableau.shape[0]):
            if tableau[i, pivot_col] > 1e-9:
                ratios.append((tableau[i, -1] / tableau[i, pivot_col], i))

        if not ratios:
            result.status = "unbounded"
            result.iterations = iteration
            result.messages.append("Problem is unbounded. No valid ratio test row exists.")
            return result

        ratios.sort()
        pivot_row = ratios[0][1]
        result.pivot_cells.append((pivot_row, pivot_col))

        # Check degeneracy
        if abs(ratios[0][0]) < 1e-9:
            result.messages.append(f"Degeneracy detected at iteration {iteration}.")

        # ── Row operations ───────────────────────────────────────────
        pivot_element = tableau[pivot_row, pivot_col]
        tableau[pivot_row] = tableau[pivot_row] / pivot_element

        for i in range(tableau.shape[0]):
            if i != pivot_row:
                factor = tableau[i, pivot_col]
                tableau[i] = tableau[i] - factor * tableau[pivot_row]

        # Update basis
        basis[pivot_row - 1] = col_labels[pivot_col]

        # Snapshot
        result.tableaux.append(_snapshot(tableau, col_labels, basis))

    # If we reach here, max iterations exceeded
    result.status = "max_iterations"
    result.iterations = MAX_ITERATIONS
    result.messages.append(f"Max iterations ({MAX_ITERATIONS}) reached. Problem may be cycling or too large.")
    return result


# ── Helper functions ────────────────────────────────────────────────

def _validate_problem(problem: dict):
    """Validates the problem dictionary structure."""
    required_keys = ["goal", "variables", "objective", "constraints"]
    for key in required_keys:
        if key not in problem:
            raise ValueError(f"Missing required key: '{key}'")

    if problem["goal"].lower() not in ("maximize", "minimize"):
        raise ValueError("Goal must be 'maximize' or 'minimize'.")

    num_vars = len(problem["variables"])
    if num_vars == 0:
        raise ValueError("At least one variable is required.")

    if len(problem["objective"]) != num_vars:
        raise ValueError(f"Objective has {len(problem['objective'])} coefficients but {num_vars} variables declared.")

    for i, con in enumerate(problem["constraints"]):
        if "coefficients" not in con or "sign" not in con or "rhs" not in con:
            raise ValueError(f"Constraint {i+1} is missing required keys (coefficients, sign, rhs).")
        if len(con["coefficients"]) != num_vars:
            raise ValueError(f"Constraint {i+1} has {len(con['coefficients'])} coefficients but {num_vars} variables declared.")
        if con["sign"].strip() not in ("<=", ">=", "="):
            raise ValueError(f"Constraint {i+1} has invalid sign: '{con['sign']}'. Must be <=, >=, or =.")


def _is_basic_column(col: np.ndarray) -> bool:
    """Check if a column is a unit vector (identity column)."""
    ones = 0
    for v in col:
        if abs(v - 1.0) < 1e-9:
            ones += 1
        elif abs(v) > 1e-9:
            return False
    return ones == 1


def _snapshot(tableau: np.ndarray, col_labels: list, basis: list) -> pd.DataFrame:
    """Create a DataFrame snapshot of the current tableau state."""
    row_labels = ["Z"] + list(basis)
    df = pd.DataFrame(tableau, columns=col_labels, index=row_labels)
    return df.round(4)
