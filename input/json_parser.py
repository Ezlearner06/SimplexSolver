"""
JSON Parser: Reads a JSON file and converts it to the standard problem dictionary.

Supports MULTIPLE JSON formats:

Format A (Recommended):
{
    "goal": "maximize",
    "variables": ["x1", "x2"],
    "objective": [5, 4],
    "constraints": [
        {"coefficients": [6, 4], "sign": "<=", "rhs": 240}
    ]
}

Format B (Alternative keys):
{
    "optimization": "max",
    "objective_function": [5, 4],
    "subject_to": [
        {"lhs": [6, 4], "relation": "<=", "rhs": 240}
    ]
}

Format C (Flat array format):
{
    "goal": "maximize",
    "num_variables": 2,
    "objective": [5, 4],
    "A": [[6, 4], [3, 2]],
    "b": [240, 270],
    "signs": ["<=", "<="]
}
"""

import json


# ── Key aliases ─────────────────────────────────────────────────────
GOAL_KEYS = ["goal", "optimization", "type", "direction", "sense", "opt", "objective_type", "problem_type"]
VARIABLES_KEYS = ["variables", "vars", "variable_names", "var_names", "names", "decision_variables"]
OBJECTIVE_KEYS = ["objective", "objective_function", "obj", "c", "costs", "coefficients", "obj_coeffs", "z"]
CONSTRAINTS_KEYS = ["constraints", "subject_to", "st", "s.t.", "cons", "constraint_list", "restrictions"]
COEFF_KEYS = ["coefficients", "coeff", "lhs", "a", "left", "values", "left_hand_side"]
SIGN_KEYS = ["sign", "relation", "operator", "op", "inequality", "direction", "sense", "type"]
RHS_KEYS = ["rhs", "b", "right", "right_hand_side", "value", "bound", "limit"]

# For flat-format matrices
MATRIX_KEYS = ["A", "a", "matrix", "constraint_matrix", "lhs_matrix", "coefficients_matrix"]
RHS_VECTOR_KEYS = ["b", "rhs", "rhs_vector", "bounds", "limits", "right_hand_side"]
SIGNS_VECTOR_KEYS = ["signs", "relations", "operators", "inequalities", "constraint_signs", "constraint_types"]


def _find_key(data: dict, aliases: list, required: bool = True, context: str = "") -> str | None:
    """Find the first matching key in the dict from a list of aliases (case-insensitive)."""
    data_keys_lower = {k.lower(): k for k in data.keys()}
    for alias in aliases:
        if alias.lower() in data_keys_lower:
            return data_keys_lower[alias.lower()]
    if required:
        raise ValueError(
            f"Missing required key for {context}. "
            f"Accepted keys: {', '.join(aliases[:5])}"
        )
    return None


def parse_json(file_buffer) -> dict:
    """
    Parse a JSON file (UploadedFile or file-like) and return a problem dict.
    Raises ValueError on schema issues.
    """
    try:
        content = file_buffer.read()
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")
    except Exception as e:
        raise ValueError(f"Could not read JSON file: {e}")

    return _flexible_parse(data)


def _flexible_parse(data: dict) -> dict:
    """Parse JSON data flexibly, supporting multiple schema variations."""
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object/dictionary.")

    # ── Extract goal ────────────────────────────────────────────────
    goal_key = _find_key(data, GOAL_KEYS, required=True, context="goal/optimization type")
    goal_raw = str(data[goal_key]).strip().lower()
    goal_map = {
        "maximize": "maximize", "max": "maximize", "maximise": "maximize",
        "minimize": "minimize", "min": "minimize", "minimise": "minimize",
    }
    goal = goal_map.get(goal_raw)
    if not goal:
        raise ValueError(f"Goal must be 'maximize' or 'minimize' (or 'max'/'min'), got '{goal_raw}'.")

    # ── Extract objective ───────────────────────────────────────────
    obj_key = _find_key(data, OBJECTIVE_KEYS, required=True, context="objective function")
    objective = data[obj_key]
    if not isinstance(objective, list):
        raise ValueError("Objective must be a list of numbers.")
    objective = [float(c) for c in objective]
    num_vars = len(objective)

    # ── Extract variables (optional — auto-generate if missing) ─────
    var_key = _find_key(data, VARIABLES_KEYS, required=False, context="variables")
    if var_key and data[var_key]:
        variables = [str(v) for v in data[var_key]]
        if len(variables) != num_vars:
            raise ValueError(f"Variable count ({len(variables)}) doesn't match objective count ({num_vars}).")
    else:
        variables = [f"x{i+1}" for i in range(num_vars)]

    # ── Extract constraints ─────────────────────────────────────────
    # Try structured constraints first (list of dicts)
    con_key = _find_key(data, CONSTRAINTS_KEYS, required=False, context="constraints")

    if con_key and isinstance(data[con_key], list) and len(data[con_key]) > 0:
        if isinstance(data[con_key][0], dict):
            return _parse_structured_constraints(data[con_key], variables, objective, goal, num_vars)
        elif isinstance(data[con_key][0], list):
            # Constraints as list of lists — need signs and rhs separately
            return _parse_matrix_format(data, variables, objective, goal, num_vars, matrix_key=con_key)

    # Try flat matrix format (A, b, signs)
    matrix_key = _find_key(data, MATRIX_KEYS, required=False, context="constraint matrix")
    if matrix_key:
        return _parse_matrix_format(data, variables, objective, goal, num_vars, matrix_key=matrix_key)

    raise ValueError(
        "Could not find constraints. Provide either:\n"
        "  - 'constraints': [{coefficients, sign, rhs}, ...]\n"
        "  - 'A' (matrix), 'b' (RHS vector), 'signs' (relations)"
    )


def _parse_structured_constraints(con_list: list, variables: list, objective: list, goal: str, num_vars: int) -> dict:
    """Parse constraints provided as a list of dictionaries."""
    constraints = []
    for i, con in enumerate(con_list):
        if not isinstance(con, dict):
            raise ValueError(f"Constraint {i+1} must be a dictionary.")

        # Find coefficient key
        coeff_key = _find_key(con, COEFF_KEYS, required=True, context=f"constraint {i+1} coefficients")
        coeffs = con[coeff_key]
        if not isinstance(coeffs, list) or len(coeffs) != num_vars:
            raise ValueError(f"Constraint {i+1}: expected {num_vars} coefficients, got {len(coeffs) if isinstance(coeffs, list) else 'non-list'}.")

        # Find sign key
        sign_key = _find_key(con, SIGN_KEYS, required=True, context=f"constraint {i+1} sign/relation")
        sign = str(con[sign_key]).strip()
        if sign not in ("<=", ">=", "="):
            raise ValueError(f"Constraint {i+1} has invalid sign: '{sign}'. Must be <=, >=, or =.")

        # Find RHS key
        rhs_key = _find_key(con, RHS_KEYS, required=True, context=f"constraint {i+1} RHS")

        constraints.append({
            "coefficients": [float(c) for c in coeffs],
            "sign": sign,
            "rhs": float(con[rhs_key]),
        })

    return {
        "goal": goal,
        "variables": variables,
        "objective": objective,
        "constraints": constraints,
    }


def _parse_matrix_format(data: dict, variables: list, objective: list, goal: str, num_vars: int, matrix_key: str) -> dict:
    """Parse constraints from flat matrix + RHS vector + signs vector."""
    matrix = data[matrix_key]
    if not isinstance(matrix, list) or not all(isinstance(row, list) for row in matrix):
        raise ValueError("Constraint matrix must be a list of lists.")

    num_constraints = len(matrix)

    # RHS vector
    rhs_key = _find_key(data, RHS_VECTOR_KEYS, required=True, context="RHS vector (b)")
    rhs_vec = data[rhs_key]
    if not isinstance(rhs_vec, list) or len(rhs_vec) != num_constraints:
        raise ValueError(f"RHS vector must have {num_constraints} values.")

    # Signs vector (optional — default to <=)
    signs_key = _find_key(data, SIGNS_VECTOR_KEYS, required=False, context="signs vector")
    if signs_key and data[signs_key]:
        signs_vec = data[signs_key]
        if len(signs_vec) != num_constraints:
            raise ValueError(f"Signs vector must have {num_constraints} values.")
    else:
        signs_vec = ["<="] * num_constraints

    constraints = []
    for i in range(num_constraints):
        row = matrix[i]
        if len(row) != num_vars:
            raise ValueError(f"Constraint {i+1}: expected {num_vars} coefficients, got {len(row)}.")
        sign = str(signs_vec[i]).strip()
        if sign not in ("<=", ">=", "="):
            raise ValueError(f"Constraint {i+1} has invalid sign: '{sign}'.")
        constraints.append({
            "coefficients": [float(c) for c in row],
            "sign": sign,
            "rhs": float(rhs_vec[i]),
        })

    return {
        "goal": goal,
        "variables": variables,
        "objective": objective,
        "constraints": constraints,
    }
