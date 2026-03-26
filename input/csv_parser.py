"""
CSV Parser: Reads a CSV file and converts it to the standard problem dictionary.

Supports MULTIPLE CSV formats:

Format A (Recommended — with 'type' column):
    type,x1,x2,...,xN,sign,RHS
    objective,5,4,3,maximize,0
    constraint,6,4,2,<=,240

Format B (Simple — no 'type' column, first row = objective, rest = constraints):
    x1,x2,x3,sign,RHS
    5,4,3,maximize,0
    6,4,2,<=,240
    3,2,5,>=,270

Format C (Minimal — just numbers, last column = RHS, second-to-last = sign):
    5,4,3,maximize,0
    6,4,2,<=,240
    3,2,5,>=,270
"""

import pandas as pd
import io
import re


# ── Common aliases for column names ────────────────────────────────
SIGN_ALIASES = {"sign", "relation", "operator", "op", "inequality", "type_constraint", "constraint_type", "direction", "sense"}
RHS_ALIASES = {"rhs", "b", "right", "right_hand_side", "righthandside", "value", "bound", "limit", "right-hand-side"}
TYPE_ALIASES = {"type", "row_type", "rowtype", "kind", "category"}


def _find_column(columns: list, aliases: set, fallback: str = None) -> str | None:
    """Find a column name matching any of the given aliases (case-insensitive)."""
    for col in columns:
        if col.strip().lower() in aliases:
            return col
    return fallback


def parse_csv(file_buffer) -> dict:
    """
    Parse a CSV file (UploadedFile or file-like) and return a problem dict.
    Raises ValueError on schema issues.
    """
    try:
        content = file_buffer.read()
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        file_buffer = io.StringIO(content)
    except Exception as e:
        raise ValueError(f"Could not read CSV file: {e}")

    # Try to detect if the file has headers
    lines = content.strip().split("\n")
    if len(lines) < 2:
        raise ValueError("CSV file must have at least 2 rows (objective + 1 constraint).")

    # Try reading with pandas
    file_buffer.seek(0)
    try:
        df = pd.read_csv(file_buffer)
    except Exception as e:
        raise ValueError(f"Could not parse CSV: {e}")

    return _dataframe_to_problem(df)


def _dataframe_to_problem(df: pd.DataFrame) -> dict:
    """Convert a DataFrame to a problem dict, handling multiple schema variations."""
    if df.empty:
        raise ValueError("CSV file is empty.")

    # Normalize column names (strip whitespace, lowercase)
    df.columns = [str(c).strip().lower() for c in df.columns]
    # Also strip all string cell values
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()

    # ── Detect columns ──────────────────────────────────────────────
    type_col = _find_column(df.columns, TYPE_ALIASES)
    sign_col = _find_column(df.columns, SIGN_ALIASES)
    rhs_col = _find_column(df.columns, RHS_ALIASES)

    # ── Auto-detect sign column if not found ────────────────────────
    if sign_col is None:
        # Look for a column whose values contain <=, >=, =, maximize, minimize
        for col in df.columns:
            vals = df[col].astype(str).str.strip().str.lower().unique()
            sign_like = {"<=", ">=", "=", "maximize", "minimize", "max", "min"}
            if len(set(vals) & sign_like) >= 1:
                sign_col = col
                break

    # ── Auto-detect RHS column if not found ─────────────────────────
    if rhs_col is None:
        # RHS is typically the last numeric-like column
        non_meta_cols = [c for c in df.columns if c != type_col and c != sign_col]
        if non_meta_cols:
            rhs_col = non_meta_cols[-1]

    if sign_col is None:
        raise ValueError(
            "Could not find a 'sign' / 'relation' column. "
            "Please include a column with values like <=, >=, =, maximize, minimize. "
            "Accepted column names: " + ", ".join(sorted(SIGN_ALIASES))
        )

    if rhs_col is None:
        raise ValueError(
            "Could not find a 'RHS' / 'b' column. "
            "Accepted column names: " + ", ".join(sorted(RHS_ALIASES))
        )

    # ── Identify variable columns ───────────────────────────────────
    meta_cols = {type_col, sign_col, rhs_col} - {None}
    var_cols = [c for c in df.columns if c not in meta_cols]

    if not var_cols:
        raise ValueError("No variable columns found. Expected columns like x1, x2, ...")

    # ── Determine which rows are objective vs constraint ────────────
    if type_col:
        obj_mask = df[type_col].str.lower().isin(["objective", "obj", "o", "z"])
        con_mask = df[type_col].str.lower().isin(["constraint", "con", "c", "s.t.", "st"])
        # If no explicit matches, fall back: first row = objective, rest = constraints
        if obj_mask.sum() == 0 and con_mask.sum() == 0:
            obj_mask = pd.Series([True] + [False] * (len(df) - 1), index=df.index)
            con_mask = ~obj_mask
    else:
        # No type column: detect objective row by sign column value
        sign_vals = df[sign_col].str.lower()
        obj_mask = sign_vals.isin(["maximize", "minimize", "max", "min"])
        if obj_mask.sum() == 0:
            # Assume first row is objective
            obj_mask = pd.Series([True] + [False] * (len(df) - 1), index=df.index)
        con_mask = ~obj_mask

    obj_rows = df[obj_mask]
    if len(obj_rows) == 0:
        raise ValueError("No objective row found. Mark a row as 'objective' or use 'maximize'/'minimize' in the sign column.")
    obj_row = obj_rows.iloc[0]

    # ── Extract goal ────────────────────────────────────────────────
    goal_raw = str(obj_row[sign_col]).strip().lower()
    goal_map = {"maximize": "maximize", "max": "maximize", "minimize": "minimize", "min": "minimize"}
    goal = goal_map.get(goal_raw)
    if not goal:
        raise ValueError(f"Objective sign must be 'maximize' or 'minimize' (or 'max'/'min'), got '{goal_raw}'.")

    # ── Extract objective coefficients ──────────────────────────────
    objective = []
    for v in var_cols:
        try:
            objective.append(float(obj_row[v]))
        except (ValueError, TypeError):
            raise ValueError(f"Non-numeric value in objective row, column '{v}': '{obj_row[v]}'")

    variables = list(var_cols)

    # ── Extract constraints ─────────────────────────────────────────
    con_rows = df[con_mask]
    if len(con_rows) == 0:
        raise ValueError("No constraint rows found. At least one constraint is required.")

    constraints = []
    for idx, row in con_rows.iterrows():
        sign = str(row[sign_col]).strip()
        if sign not in ("<=", ">=", "="):
            raise ValueError(f"Constraint at row {idx + 1} has invalid sign: '{sign}'. Must be <=, >=, or =.")

        coefficients = []
        for v in var_cols:
            try:
                coefficients.append(float(row[v]))
            except (ValueError, TypeError):
                raise ValueError(f"Non-numeric value at row {idx + 1}, column '{v}': '{row[v]}'")

        try:
            rhs_val = float(row[rhs_col])
        except (ValueError, TypeError):
            raise ValueError(f"Non-numeric RHS at row {idx + 1}: '{row[rhs_col]}'")

        constraints.append({
            "coefficients": coefficients,
            "sign": sign,
            "rhs": rhs_val,
        })

    return {
        "goal": goal,
        "variables": variables,
        "objective": objective,
        "constraints": constraints,
    }
