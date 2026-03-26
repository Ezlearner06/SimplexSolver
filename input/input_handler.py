"""
Input Handler: Centralizes manual form inputs and routes file uploads to the correct parser.
Produces the standard problem dictionary expected by engine/simplex.py.
Scalable: handles large numbers of variables and constraints gracefully.
"""

import streamlit as st
import math


def render_manual_input_form() -> dict | None:
    """
    Renders the dynamic manual entry form in Streamlit.
    Scales for many variables/constraints using a grid layout.
    Returns a problem dict if submitted, or None if not yet submitted.
    """
    st.subheader("📝 Manual Entry")

    col1, col2 = st.columns(2)
    with col1:
        num_vars = st.number_input("Number of Variables", min_value=1, max_value=50, value=2, step=1, key="num_vars")
    with col2:
        num_constraints = st.number_input("Number of Constraints", min_value=1, max_value=50, value=2, step=1, key="num_constraints")

    goal = st.radio("Optimization Goal", ["Maximize", "Minimize"], horizontal=True, key="goal")

    variables = [f"x{i+1}" for i in range(num_vars)]

    # ── Objective function ──────────────────────────────────────────
    st.markdown("**Objective Function Coefficients**")

    # For many variables, use rows of up to 6 columns
    cols_per_row = min(num_vars, 6)
    objective = [0.0] * num_vars
    for start in range(0, num_vars, cols_per_row):
        end = min(start + cols_per_row, num_vars)
        obj_cols = st.columns(end - start)
        for i, col in enumerate(obj_cols):
            idx = start + i
            with col:
                objective[idx] = st.number_input(
                    f"{variables[idx]}",
                    value=0.0,
                    format="%.3f",
                    key=f"obj_{idx}"
                )

    # ── Constraints ─────────────────────────────────────────────────
    st.markdown("**Constraints**")

    constraints = []
    for c in range(num_constraints):
        with st.expander(f"Constraint {c + 1}", expanded=(c < 5)):
            coefficients = [0.0] * num_vars

            # Coefficient grid (rows of up to 6)
            for start in range(0, num_vars, cols_per_row):
                end = min(start + cols_per_row, num_vars)
                con_cols = st.columns(end - start)
                for i, col in enumerate(con_cols):
                    idx = start + i
                    with col:
                        coefficients[idx] = st.number_input(
                            f"{variables[idx]}",
                            value=0.0,
                            format="%.3f",
                            key=f"con_{c}_{idx}"
                        )

            # Sign and RHS on a separate row
            sign_col, rhs_col = st.columns(2)
            with sign_col:
                sign = st.selectbox("Sign", ["<=", ">=", "="], key=f"sign_{c}")
            with rhs_col:
                rhs = st.number_input("RHS", value=0.0, format="%.3f", key=f"rhs_{c}")

            constraints.append({
                "coefficients": coefficients,
                "sign": sign,
                "rhs": rhs,
            })

    # ── Solve button ────────────────────────────────────────────────
    if st.button("🚀 Solve", type="primary", use_container_width=True):
        problem = {
            "goal": goal.lower(),
            "variables": variables,
            "objective": objective,
            "constraints": constraints,
        }
        return problem

    return None
