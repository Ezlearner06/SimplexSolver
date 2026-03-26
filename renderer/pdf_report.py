"""
PDF Report Generator — Professional, modern PDF export with fpdf2.
Generates a comprehensive report with problem formulation, solution summary,
graphical plot (embedded image for 2-var), sensitivity tables, and tableaux.
"""

import io
import tempfile
import os
from datetime import datetime

import numpy as np
from fpdf import FPDF


class SimplexPDF(FPDF):
    """Custom PDF class with modern header/footer styling."""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(100, 100, 140)
        self.cell(0, 8, "Simplex Method Solver - Report", ln=True, align="R")
        self.set_draw_color(120, 120, 180)
        self.set_line_width(0.4)
        self.line(10, self.get_y(), self.w - 10, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}  |  Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}", align="C")


def generate_pdf_report(problem: dict, result, sensitivity_result=None, fig=None) -> bytes:
    """
    Generate a professional PDF report.

    Parameters
    ----------
    problem : dict
        The LP problem definition.
    result : SimplexResult
        The solver result.
    sensitivity_result : SensitivityResult, optional
        Sensitivity analysis output.
    fig : plotly.graph_objects.Figure, optional
        The graphical solution figure (for 2-var problems).

    Returns
    -------
    bytes
        The PDF file content.
    """
    pdf = SimplexPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # ── Title ──────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(60, 60, 100)
    pdf.cell(0, 14, "Simplex Method - Solution Report", ln=True, align="C")
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}", ln=True, align="C")
    pdf.ln(8)

    # ── Problem Formulation ────────────────────────────────────────
    _section_header(pdf, "1. Problem Formulation")

    variables = problem["variables"]
    objective = [float(c) for c in problem["objective"]]
    goal = problem["goal"].capitalize()

    obj_str = _format_objective(objective, variables)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 7, f"Objective: {goal}  Z = {obj_str}", ln=True)
    pdf.ln(2)

    pdf.cell(0, 7, "Subject to:", ln=True)
    for i, con in enumerate(problem["constraints"]):
        coeffs = [float(c) for c in con["coefficients"]]
        sign = con["sign"].strip()
        rhs = float(con["rhs"])
        lhs = _format_constraint_lhs(coeffs, variables)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(10)
        pdf.cell(0, 6, f"C{i+1}:  {lhs}  {sign}  {rhs:g}", ln=True)

    pdf.cell(10)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(100, 100, 100)
    non_neg = ", ".join([f"{v} >= 0" for v in variables])
    pdf.cell(0, 6, f"Non-negativity: {non_neg}", ln=True)
    pdf.ln(6)

    # ── Solution Summary ───────────────────────────────────────────
    _section_header(pdf, "2. Solution Summary")

    status_labels = {
        "optimal": "Optimal Solution Found",
        "infeasible": "Infeasible - No Solution Exists",
        "unbounded": "Unbounded - No Finite Optimum",
        "max_iterations": "Max Iterations Reached",
        "error": "Input Error",
    }

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(40, 40, 40)
    status_text = status_labels.get(result.status, result.status)
    pdf.cell(0, 7, f"Status: {status_text}", ln=True)

    opt_val_str = f"{result.optimal_value:.6f}" if result.optimal_value is not None else "N/A"
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Optimal Value: {opt_val_str}", ln=True)
    pdf.cell(0, 7, f"Iterations: {result.iterations}", ln=True)
    pdf.ln(3)

    if result.variables:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, "Variable Values:", ln=True)

        # Table
        col_w = 50
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(230, 230, 245)
        pdf.cell(col_w, 7, "Variable", border=1, fill=True, align="C")
        pdf.cell(col_w, 7, "Value", border=1, fill=True, align="C")
        pdf.ln()

        pdf.set_font("Helvetica", "", 9)
        pdf.set_fill_color(255, 255, 255)
        for var, val in result.variables.items():
            pdf.cell(col_w, 6, str(var), border=1, align="C")
            pdf.cell(col_w, 6, f"{val:.6f}", border=1, align="C")
            pdf.ln()

    pdf.ln(6)

    # ── Graphical Solution (embed image) ───────────────────────────
    if fig is not None:
        _section_header(pdf, "3. Graphical Solution")
        try:
            img_bytes = fig.to_image(format="png", width=900, height=550, scale=2)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(img_bytes)
                tmp_path = tmp.name
            pdf.image(tmp_path, x=15, w=pdf.w - 30)
            os.unlink(tmp_path)
        except Exception as e:
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(150, 100, 100)
            pdf.cell(0, 7, f"(Graphical export unavailable: {e})", ln=True)
        pdf.ln(6)

    # ── Sensitivity Analysis ───────────────────────────────────────
    if sensitivity_result and sensitivity_result.is_available:
        section_num = "4" if fig is not None else "3"
        _section_header(pdf, f"{section_num}. Sensitivity Analysis")

        # Objective ranging table
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, "Objective Coefficient Ranges:", ln=True)

        headers = ["Variable", "Current", "Allow. Dec.", "Allow. Inc.", "Lower", "Upper"]
        col_w = (pdf.w - 20) / len(headers)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(230, 230, 245)
        for h in headers:
            pdf.cell(col_w, 6, h, border=1, fill=True, align="C")
        pdf.ln()

        pdf.set_font("Helvetica", "", 8)
        for r in sensitivity_result.objective_ranges:
            cells = [
                r.variable,
                f"{r.current_value:.4f}",
                _fmt_inf(r.allowable_decrease),
                _fmt_inf(r.allowable_increase),
                _fmt_bound(r.current_value - r.allowable_decrease),
                _fmt_bound(r.current_value + r.allowable_increase),
            ]
            for c in cells:
                pdf.cell(col_w, 5.5, c, border=1, align="C")
            pdf.ln()

        pdf.ln(4)

        # RHS ranging table
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, "RHS Constraint Ranges:", ln=True)

        rhs_headers = ["Constraint", "Current RHS", "Shadow Price", "Allow. Dec.", "Allow. Inc."]
        col_w2 = (pdf.w - 20) / len(rhs_headers)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(230, 230, 245)
        for h in rhs_headers:
            pdf.cell(col_w2, 6, h, border=1, fill=True, align="C")
        pdf.ln()

        pdf.set_font("Helvetica", "", 8)
        for r in sensitivity_result.rhs_ranges:
            sign = problem["constraints"][r.constraint_index - 1]["sign"].strip()
            cells = [
                f"C{r.constraint_index} ({sign})",
                f"{r.current_rhs:.4f}",
                f"{r.shadow_price:.4f}",
                _fmt_inf(r.allowable_decrease),
                _fmt_inf(r.allowable_increase),
            ]
            for c in cells:
                pdf.cell(col_w2, 5.5, c, border=1, align="C")
            pdf.ln()

        pdf.ln(6)

    # ── Tableaux (first and last) ──────────────────────────────────
    if result.tableaux:
        section_num_t = "5" if fig is not None and sensitivity_result and sensitivity_result.is_available else \
                        "4" if (fig is not None) or (sensitivity_result and sensitivity_result.is_available) else "3"
        _section_header(pdf, f"{section_num_t}. Tableau Snapshots")

        tableaux_to_show = []
        if len(result.tableaux) >= 1:
            tableaux_to_show.append(("Initial Tableau", result.tableaux[0]))
        if len(result.tableaux) >= 2:
            tableaux_to_show.append((f"Final Tableau (Iteration {len(result.tableaux) - 1})", result.tableaux[-1]))

        for title, tab_df in tableaux_to_show:
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 7, title, ln=True)

            cols = list(tab_df.columns)
            rows = list(tab_df.index)
            n_cols = len(cols) + 1  # +1 for row label
            col_w_tab = min((pdf.w - 20) / n_cols, 22)

            # Check if table fits, if not reduce font
            total_w = col_w_tab * n_cols
            if total_w > pdf.w - 20:
                col_w_tab = (pdf.w - 20) / n_cols

            # Header
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_fill_color(230, 230, 245)
            pdf.cell(col_w_tab, 5.5, "Basis", border=1, fill=True, align="C")
            for c in cols:
                pdf.cell(col_w_tab, 5.5, str(c), border=1, fill=True, align="C")
            pdf.ln()

            # Data
            pdf.set_font("Helvetica", "", 7)
            for row_label in rows:
                pdf.cell(col_w_tab, 5, str(row_label), border=1, align="C")
                for col in cols:
                    val = tab_df.loc[row_label, col]
                    pdf.cell(col_w_tab, 5, f"{val:.3f}", border=1, align="C")
                pdf.ln()

            pdf.ln(4)

    # ── Output ─────────────────────────────────────────────────────
    return bytes(pdf.output())


# ── Helpers ────────────────────────────────────────────────────────

def _section_header(pdf, title):
    """Draw a styled section header."""
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(70, 70, 120)
    pdf.cell(0, 10, title, ln=True)
    pdf.set_draw_color(160, 160, 200)
    pdf.set_line_width(0.3)
    pdf.line(10, pdf.get_y(), pdf.w - 10, pdf.get_y())
    pdf.ln(4)
    pdf.set_text_color(40, 40, 40)


def _format_objective(coeffs, variables):
    terms = []
    for i, (c, v) in enumerate(zip(coeffs, variables)):
        if abs(c) < 1e-9:
            continue
        if c == 1:
            term = v
        elif c == -1:
            term = f"-{v}"
        else:
            term = f"{c:g}{v}"
        if terms and c > 0:
            term = f"+ {term}"
        terms.append(term)
    return " ".join(terms) if terms else "0"


def _format_constraint_lhs(coeffs, variables):
    terms = []
    for i, (c, v) in enumerate(zip(coeffs, variables)):
        if abs(c) < 1e-9:
            continue
        if c == 1:
            term = v
        elif c == -1:
            term = f"-{v}"
        else:
            term = f"{c:g}{v}"
        if terms and c > 0:
            term = f"+ {term}"
        terms.append(term)
    return " ".join(terms) if terms else "0"


def _fmt_inf(val):
    if val == np.inf or val == float('inf'):
        return "Inf"
    return f"{val:.4f}"


def _fmt_bound(val):
    if val == np.inf or val == float('inf'):
        return "Inf"
    if val == -np.inf or val == float('-inf'):
        return "-Inf"
    return f"{val:.4f}"
