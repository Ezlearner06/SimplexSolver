"""
Tableau Display: Streamlit UI components for step-by-step tableau iteration viewing.
Shows one iteration at a time with Prev/Next navigation and pivot cell highlighting.
"""

import streamlit as st
import pandas as pd


def render_solution_summary(result):
    """Display the solution summary dashboard."""
    st.markdown("---")
    st.subheader("📊 Solution Summary")

    # Status badge
    status_map = {
        "optimal": ("✅ Optimal Solution Found", "success"),
        "infeasible": ("❌ Infeasible — No Solution Exists", "error"),
        "unbounded": ("⚠️ Unbounded — No Finite Optimum", "warning"),
        "max_iterations": ("🔄 Max Iterations Reached", "warning"),
        "error": ("🚫 Input Error", "error"),
    }

    label, msg_type = status_map.get(result.status, ("❓ Unknown", "info"))
    if msg_type == "success":
        st.success(label)
    elif msg_type == "error":
        st.error(label)
    elif msg_type == "warning":
        st.warning(label)
    else:
        st.info(label)

    # Show messages
    for msg in result.messages:
        st.info(msg)

    # Safely format optimal_value to handle None
    opt_val_text = f"{result.optimal_value:.3f}" if result.optimal_value is not None else "N/A"

    # Always show metrics regardless of status
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Value" if result.status != "optimal" else "Optimal Value", opt_val_text)
    with col2:
        st.metric("Iterations", f"{result.iterations}")
    with col3:
        st.metric("Variables", f"{len(result.variables)}")

    st.markdown("**Variable Values:**")
    var_df = pd.DataFrame(
        list(result.variables.items()),
        columns=["Variable", "Value"]
    )
    styled_var = var_df.style.hide(axis="index").format({"Value": "{:.3f}"})
    st.dataframe(styled_var, use_container_width=True)

    # ── Final English Suggestion ────────────────────────────────
    st.markdown("### 💡 Final Suggestion / Recommendation")
    
    if result.status == "optimal":
        non_zero_vars = [f"**{k}** = `{v:.3f}`" for k, v in result.variables.items()]
        explanation = f"Based on the Simplex algorithm, the optimal strategy to optimize your objective function is to set: "
        explanation += ", ".join(non_zero_vars) + ". "
        explanation += f"This configuration yields an optimal value of **`{opt_val_text}`**."
        st.success(explanation)
    elif result.status == "infeasible":
        st.error(f"The model is **infeasible**. The constraints are contradictory, meaning no valid configuration exists that satisfies all of them simultaneously. The final relaxed objective value attempted was **`{opt_val_text}`**.")
    elif result.status == "unbounded":
        st.warning(f"The model is **unbounded**. The objective function can be improved infinitely without violating any constraints. A feasible boundary configuration starts with objective **`{opt_val_text}`**.")
    else:
        st.info(f"The solver stopped at iteration {result.iterations} with an objective value of **`{opt_val_text}`**.")



def render_tableau_viewer(result):
    """
    Render the step-by-step tableau iteration viewer.
    Allows navigation with Prev/Next buttons.
    """
    if not result.tableaux:
        st.info("No tableaux to display.")
        return

    st.markdown("---")
    st.subheader("📋 Tableau Iterations")

    total = len(result.tableaux)

    # Navigation
    if "tableau_index" not in st.session_state:
        st.session_state.tableau_index = 0

    col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
    with col1:
        if st.button("⬅️ Prev", disabled=st.session_state.tableau_index <= 0, use_container_width=True):
            st.session_state.tableau_index -= 1
            st.rerun()
    with col2:
        if st.button("Next ➡️", disabled=st.session_state.tableau_index >= total - 1, use_container_width=True):
            st.session_state.tableau_index += 1
            st.rerun()
    with col3:
        idx = st.session_state.tableau_index
        if idx == 0:
            st.markdown(f"**Initial Tableau** (1 of {total})")
        else:
            st.markdown(f"**Iteration {idx}** ({idx + 1} of {total})")
    with col4:
        # Jump to specific iteration
        jump = st.number_input("Jump to Step", min_value=1, max_value=total, value=idx + 1, key="jump_to")
        if jump - 1 != st.session_state.tableau_index:
            st.session_state.tableau_index = jump - 1
            st.rerun()

    idx = st.session_state.tableau_index
    tableau_df = result.tableaux[idx]

    # ── Highlight pivot cell ────────────────────────────────────────
    # The pivot cell at index `idx` corresponds to the pivot that produced tableau idx+1
    # So we highlight on the tableau BEFORE the pivot was applied
    def highlight_pivot(df):
        styles = pd.DataFrame("", index=df.index, columns=df.columns)
        if idx < len(result.pivot_cells):
            pivot_row, pivot_col = result.pivot_cells[idx]
            row_label = df.index[pivot_row]
            col_label = df.columns[pivot_col]
            styles.loc[row_label, col_label] = "background-color: #FFEB3B; font-weight: bold; color: #000;"
        return styles

    styled = tableau_df.style.apply(highlight_pivot, axis=None).format("{:.3f}")
    st.dataframe(styled, use_container_width=True)

    # Legend
    if idx < len(result.pivot_cells):
        pr, pc = result.pivot_cells[idx]
        st.caption(f"🟡 Pivot element: Row **{tableau_df.index[pr]}**, Column **{tableau_df.columns[pc]}**")
