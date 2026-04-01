"""
Simplex Method Core Engine
Standard Simplex only. Shows standardized form conversion.
Detects: Optimal, Infeasible, Unbounded, Degenerate, Multiple Optimal.
"""

import numpy as np
import pandas as pd
from copy import deepcopy

MAX_ITERATIONS = 200
EPSILON = 1e-6


class SimplexResult:
    """Container for the complete result of a Simplex solve."""

    def __init__(self):
        self.status = ""
        self.optimal_value = None
        self.variables = {}
        self.iterations = 0
        self.tableaux = []
        self.pivot_cells = []
        self.messages = []
        self.method_used = "Standard Simplex"
        self.standard_form = {"objective": "", "constraints": []}

    def to_dict(self):
        return {
            "status": self.status,
            "optimal_value": self.optimal_value,
            "variables": self.variables,
            "iterations": self.iterations,
            "messages": self.messages,
            "method_used": self.method_used,
            "standard_form": self.standard_form,
        }


def solve(problem: dict) -> SimplexResult:
    result = SimplexResult()

    try:
        _validate_problem(problem)
    except ValueError as e:
        result.status = "error"
        result.messages.append(f"❌ {e}")
        return result

    goal = problem["goal"].lower()
    variables = list(problem["variables"])
    objective = list(map(float, problem["objective"]))
    constraints = deepcopy(problem["constraints"])
    num_vars = len(variables)
    num_constraints = len(constraints)

    is_min = goal == "minimize"
    if is_min:
        objective = [-c for c in objective]
        result.messages.append("Converted Minimization to Maximization (Z → −Z).")

    # ── Standardization ──────────────────────────────────────────────
    slack_count = 0
    artificial_indices = []   # always empty; prevents NameError in basis loop
    col_names = list(variables)
    rows = []
    rhs_list = []
    std_constraints_display = []

    for i, con in enumerate(constraints):
        coeffs = list(map(float, con["coefficients"]))
        sign = con["sign"].strip()
        rhs = float(con["rhs"])

        # Normalize negative RHS
        if rhs < 0:
            coeffs = [-c for c in coeffs]
            rhs = -rhs
            sign = ">=" if sign == "<=" else "<=" if sign == ">=" else "="
            result.messages.append(f"🟡 Constraint {i+1}: multiplied by −1 (RHS was negative)")

        # Reject unsupported forms
        if sign == "=":
            result.status = "error"
            result.messages.append(
                f"❌ Constraint {i+1} is an equality (=). "
                "Standard Simplex only handles ≤ constraints. "
                "Use the Big-M or Two-Phase method for equality constraints."
            )
            return result

        if sign == ">=" and rhs > 0:
            result.status = "error"
            result.messages.append(
                f"❌ Constraint {i+1} is a ≥ constraint (positive RHS). "
                "Standard Simplex cannot handle this. "
                "Use the Big-M or Two-Phase method instead."
            )
            return result

        if sign == ">=" and rhs == 0:
            # 0 >= 0 — trivially true, no slack needed
            result.messages.append(f"🟡 Constraint {i+1} (≥ 0) is trivially satisfied — skipped.")
            num_constraints -= 1
            continue

        # Only <= with rhs >= 0 reaches here — add slack
        slack_count += 1
        s_name = f"S{slack_count}"
        result.messages.append(f"Slack variable {s_name} added to Constraint {i+1}")
        col_names.append(s_name)
        for r in rows:
            r.append(0.0)
        row = coeffs + [0.0] * (slack_count - 1) + [1.0]
        rows.append(row)
        rhs_list.append(rhs)

        lhs_parts = []
        for vi, cv in enumerate(coeffs):
            if abs(cv) < EPSILON:
                continue
            if not lhs_parts:
                lhs_parts.append(f"{cv:g}{variables[vi]}")
            elif cv > 0:
                lhs_parts.append(f"+ {cv:g}{variables[vi]}")
            else:
                lhs_parts.append(f"- {abs(cv):g}{variables[vi]}")
        lhs_parts.append(f"+ {s_name}")
        std_constraints_display.append(" ".join(lhs_parts) + f" = {rhs:g}")

    # ── Standard form display ────────────────────────────────────────
    orig_obj = list(map(float, problem["objective"]))
    obj_parts = []
    for vi, cv in enumerate(orig_obj):
        if abs(cv) < EPSILON:
            continue
        if not obj_parts:
            obj_parts.append(f"{cv:g}{variables[vi]}")
        elif cv > 0:
            obj_parts.append(f"+ {cv:g}{variables[vi]}")
        else:
            obj_parts.append(f"- {abs(cv):g}{variables[vi]}")

    goal_label = "Minimize" if is_min else "Maximize"
    result.standard_form["objective"] = (
        f"{goal_label} Z = " + " ".join(obj_parts) if obj_parts else f"{goal_label} Z = 0"
    )
    result.standard_form["constraints"] = std_constraints_display

    # ── Build tableau ────────────────────────────────────────────────
    total_cols = len(col_names)
    width = total_cols + 1

    for r in rows:
        while len(r) < total_cols:
            r.append(0.0)

    z_row = [-c for c in objective] + [0.0] * (total_cols - num_vars + 1)
    while len(z_row) < width:
        z_row.insert(-1, 0.0)

    tableau = np.array([z_row] + [r + [rhs_list[i]] for i, r in enumerate(rows)], dtype=float)
    col_labels = col_names + ["RHS"]

    # ── Initial basis ────────────────────────────────────────────────
    basis = []
    for i in range(len(rows)):
        found = False
        for j in range(total_cols):
            col = tableau[:, j]
            if abs(col[i + 1] - 1.0) < EPSILON and _is_basic_column(col):
                basis.append(col_labels[j])
                found = True
                break
        if not found:
            basis.append(f"S{i+1}")

    result.tableaux.append(_snapshot(tableau, col_labels, basis))

    # ── Simplex iterations ───────────────────────────────────────────
    for iteration in range(1, MAX_ITERATIONS + 1):
        z_vals = tableau[0, :total_cols]

        if all(v >= -EPSILON for v in z_vals):
            result.status = "optimal"
            result.iterations = iteration - 1
            opt_val = tableau[0, -1]
            result.optimal_value = round(-opt_val if is_min else opt_val, 6)

            for v in variables:
                ci = col_labels.index(v) if v in col_labels else -1
                if ci >= 0 and _is_basic_column(tableau[:, ci]):
                    row_i = np.argmax(np.abs(tableau[:, ci]))
                    result.variables[v] = round(tableau[row_i, -1], 6)
                else:
                    result.variables[v] = 0.0

            # Multiple optimal: non-basic decision variable with zero reduced cost
            for j in range(num_vars):
                if abs(z_vals[j]) < EPSILON and col_labels[j] not in basis:
                    result.messages.append("🟡 Multiple optimal solutions exist")
                    break

            return result

        pivot_col = int(np.where(z_vals < -EPSILON)[0][0])

        ratios = [
            (tableau[i, -1] / tableau[i, pivot_col], i)
            for i in range(1, tableau.shape[0])
            if tableau[i, pivot_col] > EPSILON
        ]

        if not ratios:
            result.status = "unbounded"
            result.iterations = iteration
            result.messages.append("❌ The solution is unbounded")
            return result

        ratios.sort(key=lambda x: (x[0], x[1]))
        pivot_row = ratios[0][1]
        result.pivot_cells.append((pivot_row, pivot_col))

        if abs(ratios[0][0]) < EPSILON:
            msg = "🟡 Degeneracy detected — applying Bland's Rule"
            if msg not in result.messages:
                result.messages.append(msg)

        tableau[pivot_row] /= tableau[pivot_row, pivot_col]
        for i in range(tableau.shape[0]):
            if i != pivot_row:
                tableau[i] -= tableau[i, pivot_col] * tableau[pivot_row]
        tableau[np.abs(tableau) < 1e-10] = 0.0

        basis[pivot_row - 1] = col_labels[pivot_col]
        result.tableaux.append(_snapshot(tableau, col_labels, basis))

    result.status = "max_iterations"
    result.iterations = MAX_ITERATIONS
    result.messages.append(f"Max iterations ({MAX_ITERATIONS}) reached.")
    return result


# ── Helpers ──────────────────────────────────────────────────────────

def _validate_problem(problem: dict):
    required = ["goal", "variables", "objective", "constraints"]
    for key in required:
        if key not in problem:
            raise ValueError(f"Missing required key: '{key}'")

    if problem["goal"].lower() not in ("maximize", "minimize"):
        raise ValueError("Goal must be 'maximize' or 'minimize'.")

    num_vars = len(problem["variables"])
    if num_vars == 0:
        raise ValueError("At least one variable is required.")

    if len(problem["objective"]) != num_vars:
        raise ValueError(f"Objective has {len(problem['objective'])} coefficients but {num_vars} variables declared.")

    for x in problem["objective"]:
        if not isinstance(x, (int, float)):
            raise ValueError("Only linear programming problems are supported by the Simplex method.")

    for i, con in enumerate(problem["constraints"]):
        if "coefficients" not in con or "sign" not in con or "rhs" not in con:
            raise ValueError(f"Constraint {i+1} is missing required keys.")
        if len(con["coefficients"]) != num_vars:
            raise ValueError(f"Constraint {i+1} coefficient count mismatch.")
        if con["sign"].strip() not in ("<=", ">=", "="):
            raise ValueError(f"Constraint {i+1} has invalid sign: '{con['sign']}'.")


def _is_basic_column(col: np.ndarray) -> bool:
    ones = 0
    for v in col:
        if abs(v - 1.0) < EPSILON:
            ones += 1
        elif abs(v) > EPSILON:
            return False
    return ones == 1


def _snapshot(tableau: np.ndarray, col_labels: list, basis: list) -> pd.DataFrame:
    row_labels = ["Z"] + list(basis)
    df = pd.DataFrame(tableau, columns=col_labels, index=row_labels)
    return df.round(4)
