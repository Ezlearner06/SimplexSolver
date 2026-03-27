"""
Sensitivity Analysis Display — Modern Streamlit UI with animated cards,
gradient tables, and interactive tooltips for sensitivity ranges.
"""

import streamlit as st
import pandas as pd
import numpy as np


def render_sensitivity_analysis(problem: dict, result, sensitivity_result):
    """
    Render the sensitivity / post-optimality analysis section.
    Shows objective coefficient ranging and RHS constraint ranging
    with shadow prices in styled, interactive tables.
    """
    if not sensitivity_result.is_available:
        return

    st.markdown("---")

    # Section header with gradient styling
    st.markdown("""
    <div style="
        text-align: center;
        padding: 1rem;
        margin-bottom: 1.5rem;
        background: linear-gradient(135deg, rgba(99,102,241,0.08) 0%, rgba(168,85,247,0.08) 100%);
        border: 1px solid rgba(139,92,246,0.2);
        border-radius: 16px;
        backdrop-filter: blur(10px);
    ">
        <h3 style="margin:0; background: linear-gradient(135deg, #a78bfa, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 700;">
            📈 Sensitivity / Post-Optimality Analysis
        </h3>
        <p style="color: #94a3b8; font-size: 0.9rem; margin: 0.3rem 0 0 0;">
            How stable is the current optimal solution?
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_obj, col_rhs = st.columns(2)

    # ── Objective Coefficient Ranging ──────────────────────────────
    with col_obj:
        st.markdown("""
        <div style="
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 1rem;
        ">
            <h4 style="color: #e2e8f0; margin-bottom: 0.5rem;">🎯 Objective Coefficient Ranges</h4>
            <p style="color: #64748b; font-size: 0.8rem; margin-bottom: 0.8rem;">
                Range within which each coefficient can change without altering the optimal basis.
            </p>
        </div>
        """, unsafe_allow_html=True)

        obj_data = []
        for r in sensitivity_result.objective_ranges:
            obj_data.append({
                "Variable": r.variable,
                "Current": f"{r.current_value:.4f}",
                "↓ Allow. Decrease": _format_inf(r.allowable_decrease),
                "↑ Allow. Increase": _format_inf(r.allowable_increase),
                "Lower Bound": _format_bound(r.current_value - r.allowable_decrease),
                "Upper Bound": _format_bound(r.current_value + r.allowable_increase),
            })

        if obj_data:
            df_obj = pd.DataFrame(obj_data)
            st.dataframe(
                df_obj.style
                .set_properties(**{
                    "text-align": "center",
                    "font-size": "0.9rem",
                })
                .hide(axis="index"),
                use_container_width=True,
                height=min(38 * (len(obj_data) + 1) + 10, 300),
            )

    # ── RHS / Constraint Ranging ──────────────────────────────────
    with col_rhs:
        st.markdown("""
        <div style="
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 1rem;
        ">
            <h4 style="color: #e2e8f0; margin-bottom: 0.5rem;">🔒 RHS Constraint Ranges</h4>
            <p style="color: #64748b; font-size: 0.8rem; margin-bottom: 0.8rem;">
                Shadow prices and allowable RHS changes preserving the current basis.
            </p>
        </div>
        """, unsafe_allow_html=True)

        rhs_data = []
        for r in sensitivity_result.rhs_ranges:
            sign = problem["constraints"][r.constraint_index - 1]["sign"].strip()
            rhs_data.append({
                "Constraint": f"C{r.constraint_index} ({sign})",
                "Current RHS": f"{r.current_rhs:.4f}",
                "Shadow Price": f"{r.shadow_price:.4f}",
                "↓ Allow. Decrease": _format_inf(r.allowable_decrease),
                "↑ Allow. Increase": _format_inf(r.allowable_increase),
            })

        if rhs_data:
            df_rhs = pd.DataFrame(rhs_data)
            st.dataframe(
                df_rhs.style
                .set_properties(**{
                    "text-align": "center",
                    "font-size": "0.9rem",
                })
                .hide(axis="index"),
                use_container_width=True,
                height=min(38 * (len(rhs_data) + 1) + 10, 300),
            )

    # ── Interpretation ─────────────────────────────────────────────
    with st.expander("💡 How to Interpret Sensitivity Analysis", expanded=False):
        st.markdown("""
**Objective Coefficient Ranges** tell you how much each coefficient in the objective function can change
(while keeping everything else fixed) before the current optimal solution changes to a different vertex.

**Shadow Prices** (Dual Values) represent the marginal value of relaxing a constraint by one unit:
- A shadow price of **$5** on constraint C1 means: if you increase C1's RHS by 1, the optimal value improves by **$5**.
- A shadow price of **$0** means the constraint is **not binding** (has slack).

**Allowable Ranges** indicate the interval over which these interpretations remain valid.
Outside these ranges, the basis changes and a new sensitivity analysis would be needed.
        """)


def _format_inf(val):
    """Format infinity values for display."""
    if val == np.inf or val == float('inf'):
        return "∞"
    return f"{val:.4f}"


def _format_bound(val):
    """Format bound values."""
    if val == np.inf or val == float('inf'):
        return "∞"
    if val == -np.inf or val == float('-inf'):
        return "-∞"
    return f"{val:.4f}"
