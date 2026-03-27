"""
Simplex Method Solver — Main Streamlit Application

Wires together: Input Handler, Core Engine, Tableau Renderer, Storage.
"""

import streamlit as st
import pandas as pd
import io
import sys
import os

# Ensure project root is on path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.simplex import solve
from engine.sensitivity import compute_sensitivity
from input.input_handler import render_manual_input_form
from input.csv_parser import parse_csv
from input.json_parser import parse_json
from input.excel_parser import parse_excel
from renderer.tableau_display import render_solution_summary, render_tableau_viewer
from renderer.graphical_display import render_graphical_solution
from renderer.sensitivity_display import render_sensitivity_analysis
from renderer.pdf_report import generate_pdf_report
from storage.sheets_connector import save_problem, load_history, is_available as sheets_available

# ── Page Config ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="Simplex Solver",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Modern UI Reset & Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Full width & remove top padding */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 100% !important;
    }

    /* Main Header Styling */
    .main-header {
        text-align: center;
        padding: 1.5rem 0 2rem 0;
        margin-bottom: 2rem;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }
    .main-header h1 {
        background: linear-gradient(135deg, #a8c0ff 0%, #3f2b96 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: #a0aec0;
        font-size: 1.1rem;
        font-weight: 500;
    }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        border-bottom: 2px solid rgba(255,255,255,0.05);
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1.05rem;
        font-weight: 600;
        padding: 1rem 0;
        color: #a0aec0;
    }
    .stTabs [aria-selected="true"] {
        color: #fff !important;
    }

    /* Card Styling for content blocks */
    div[data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Sleek Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0e1117;
        border-right: 1px solid rgba(255,255,255,0.05);
    }
    .sidebar-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1.5rem;
    }
    .sidebar-card h3 {
        color: #e2e8f0;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        padding-bottom: 0.5rem;
    }
    .sidebar-card p, .sidebar-card li {
        color: #a0aec0;
        font-size: 0.9rem;
        line-height: 1.5;
    }
    .sidebar-card code {
        background: rgba(0,0,0,0.3);
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        color: #cbd5e0;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2.2rem;
        font-weight: 700;
        color: #a8c0ff;
    }

    /* Force tables to full width */
    [data-testid="stDataFrame"] {
        width: 100% !important;
    }
    [data-testid="stDataFrame"] > div {
        width: 100% !important;
    }
    canvas {
        width: 100% !important;
    }
    
</style>
""", unsafe_allow_html=True)

# ── Header ──────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>📐 Simplex Method Solver</h1>
    <p>Step-by-step Linear Programming Problem solver with interactive tableau viewer</p>
</div>
""", unsafe_allow_html=True)


# ── Helper: Export CSV ──────────────────────────────────────────────
def _export_csv(result) -> str:
    """Export solution and all tableaux to a CSV string."""
    output = io.StringIO()

    output.write("=== SOLUTION SUMMARY ===\n")
    output.write(f"Status,{result.status}\n")
    output.write(f"Optimal Value,{result.optimal_value}\n")
    output.write(f"Iterations,{result.iterations}\n")
    output.write("\n")

    output.write("=== VARIABLE VALUES ===\n")
    for var, val in result.variables.items():
        output.write(f"{var},{val}\n")
    output.write("\n")

    for i, tableau in enumerate(result.tableaux):
        label = "Initial Tableau" if i == 0 else f"Iteration {i}"
        output.write(f"=== {label} ===\n")
        tableau.to_csv(output)
        output.write("\n")

    return output.getvalue()


# ── Tabs ────────────────────────────────────────────────────────────
tab_manual, tab_upload, tab_history = st.tabs(["📝 Manual Entry", "📁 Upload File", "📜 History"])

# ══════════════════════════════════════════════════════════════════════
# TAB 1: Manual Entry
# ══════════════════════════════════════════════════════════════════════
with tab_manual:
    problem = render_manual_input_form()
    if problem is not None:
        with st.spinner("Solving..."):
            result = solve(problem)
        st.session_state["last_result"] = result
        st.session_state["last_problem"] = problem
        st.session_state["tableau_index"] = 0
        render_solution_summary(result)
        render_tableau_viewer(result)

        # ── Graphical Solution (2-var only) ─────────────────────
        render_graphical_solution(problem, result)

        # ── Sensitivity Analysis ────────────────────────────────
        if result.status == "optimal":
            sens = compute_sensitivity(problem, result)
            render_sensitivity_analysis(problem, result, sens)
        else:
            sens = None

        # Download & Save row
        col_dl, col_pdf, col_save = st.columns(3)
        with col_dl:
            if result.status == "optimal" and result.tableaux:
                csv_buf = _export_csv(result)
                st.download_button(
                    "⬇️ Download CSV",
                    data=csv_buf,
                    file_name="simplex_result.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
        with col_pdf:
            if result.tableaux:
                try:
                    pdf_bytes = generate_pdf_report(problem, result, sens)
                    st.download_button(
                        "📄 Download PDF Report",
                        data=pdf_bytes,
                        file_name="simplex_report.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.error(f"PDF generation failed: {e}")
        with col_save:
            if sheets_available():
                name = st.text_input("Problem name", value="", key="save_name_manual")
                if st.button("💾 Save to History", key="save_manual", use_container_width=True):
                    try:
                        save_problem(problem, result.to_dict(), name)
                        st.success("Saved to Google Sheets!")
                    except Exception as e:
                        st.error(f"Could not save: {e}")
            else:
                st.info("Google Sheets not configured. Set GOOGLE_SHEET_ID and credentials to enable history.")

# ══════════════════════════════════════════════════════════════════════
# TAB 2: File Upload
# ══════════════════════════════════════════════════════════════════════
with tab_upload:
    st.subheader("📁 Upload a Problem File")
    st.markdown("Supported formats: `.csv`, `.json`, `.xlsx`")

    uploaded = st.file_uploader(
        "Choose a file",
        type=["csv", "json", "xlsx"],
        key="file_uploader",
    )

    if uploaded is not None:
        file_size = uploaded.size
        if file_size == 0:
            st.error("File appears to be empty. Please upload a valid file.")
        else:
            try:
                fname = uploaded.name.lower()
                # Check if this is a newly uploaded file
                current_file_signature = fname + str(file_size)
                if st.session_state.get("last_uploaded_signature") != current_file_signature:
                    st.session_state["last_uploaded_signature"] = current_file_signature
                    # Clear previous results since file changed
                    st.session_state.pop("upload_result", None)
                    st.session_state.pop("upload_problem", None)

                if fname.endswith(".csv"):
                    problem = parse_csv(uploaded)
                elif fname.endswith(".json"):
                    problem = parse_json(uploaded)
                elif fname.endswith(".xlsx"):
                    problem = parse_excel(uploaded)
                else:
                    st.error("Unsupported file type.")
                    problem = None

                if problem:
                    st.markdown("### Validate & Solve")
                    
                    col_confirm, col_reupload = st.columns([1, 1])
                    with col_confirm:
                        if st.button("🚀 Confirm & Solve", type="primary", use_container_width=True, key="confirm_upload"):
                            with st.spinner("Solving..."):
                                result = solve(problem)
                            st.session_state["upload_result"] = result
                            st.session_state["upload_problem"] = problem
                            st.session_state["tableau_index"] = 0

                    with col_reupload:
                        st.markdown("<div style='padding-top:10px;'><em>Or upload a different file above.</em></div>", unsafe_allow_html=True)

                    # Preview extracted data hidden in an expander
                    with st.expander("🔍 View Extracted Data Schema from File", expanded=False):
                        st.json(problem)

                    # ── Render results outside the button block so it persists ──
                    if "upload_result" in st.session_state and st.session_state.get("upload_problem") == problem:
                        result = st.session_state["upload_result"]
                        render_solution_summary(result)
                        render_tableau_viewer(result)

                        # ── Graphical Solution (2-var only) ─────────
                        render_graphical_solution(problem, result)

                        # ── Sensitivity Analysis ────────────────────
                        if result.status == "optimal":
                            sens_up = compute_sensitivity(problem, result)
                            render_sensitivity_analysis(problem, result, sens_up)
                        else:
                            sens_up = None

                        # Download & Save row
                        col_dl_up, col_pdf_up, col_save_up = st.columns(3)
                        with col_dl_up:
                            if result.status == "optimal" and result.tableaux:
                                csv_buf = _export_csv(result)
                                st.download_button(
                                    "⬇️ Download CSV",
                                    data=csv_buf,
                                    file_name="simplex_result.csv",
                                    mime="text/csv",
                                    use_container_width=True,
                                    key="download_upload_csv"
                                )
                        with col_pdf_up:
                            if result.tableaux:
                                try:
                                    pdf_bytes_up = generate_pdf_report(problem, result, sens_up)
                                    st.download_button(
                                        "📄 Download PDF Report",
                                        data=pdf_bytes_up,
                                        file_name="simplex_report.pdf",
                                        mime="application/pdf",
                                        use_container_width=True,
                                        key="download_upload_pdf"
                                    )
                                except Exception as e:
                                    st.error(f"PDF generation failed: {e}")
                        with col_save_up:
                            if sheets_available():
                                name = st.text_input("Problem name", value="", key="save_name_upload")
                                if st.button("💾 Save to History", key="save_upload", use_container_width=True):
                                    try:
                                        save_problem(problem, result.to_dict(), name)
                                        st.success("Saved to Google Sheets!")
                                    except Exception as e:
                                        st.error(f"Could not save: {e}")
                            else:
                                st.info("Google Sheets not configured. Set GOOGLE_SHEET_ID and credentials to enable history.")

            except ValueError as e:
                st.error(f"⚠️ File parsing error: {e}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")

# ══════════════════════════════════════════════════════════════════════
# TAB 3: History
# ══════════════════════════════════════════════════════════════════════
with tab_history:
    st.subheader("📜 Problem History")
    if not sheets_available():
        st.warning("Google Sheets is not configured. To enable history, set the `GOOGLE_SHEET_ID` environment variable and provide a `credentials.json` file.")
    else:
        try:
            history = load_history()
            if not history:
                st.info("No saved problems yet. Solve a problem and save it!")
            else:
                for i, entry in enumerate(reversed(history)):
                    with st.expander(f"**{entry['name']}** — {entry['timestamp']}  |  Status: {entry['status']}"):
                        st.markdown(f"- **Optimal Value:** {entry['optimal_value']}")
                        st.markdown(f"- **Iterations:** {entry['iterations']}")
                        if entry.get("problem"):
                            if st.button(f"🔄 Reload & Solve", key=f"reload_{i}"):
                                with st.spinner("Solving..."):
                                    result = solve(entry["problem"])
                                st.session_state["last_result"] = result
                                st.session_state["last_problem"] = entry["problem"]
                                st.session_state["tableau_index"] = 0
                                render_solution_summary(result)
                                render_tableau_viewer(result)
        except Exception as e:
            st.error(f"Could not load history: {e}")


# ── Sidebar ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
<div class="sidebar-card">
    <h3>ℹ️ Project Overview</h3>
    <p><strong>Simplex Method Solver</strong><br>
    A professional, step-by-step Linear Programming solver built for the <em>EM-4 (BSC07) Mini Project</em>.</p>
</div>

<div class="sidebar-card">
    <h3>✨ Core Features</h3>
    <ul style="padding-left: 1rem; margin-top: 0;">
        <li>Dynamic Manual Form (up to 50 vars)</li>
        <li>CSV, JSON, and Excel Uploads</li>
        <li>Interactive Tableau Viewer</li>
        <li>Pivot Cell Highlighting</li>
        <li>Smart Edge Case Detection</li>
        <li>Google Sheets Integration</li>
        <li>📊 Graphical Solution (2-var)</li>
        <li>📈 Sensitivity Analysis</li>
        <li>📄 PDF Report Export</li>
    </ul>
</div>

<div class="sidebar-card">
    <h3>📄 Input Schema (CSV)</h3>
    <p>Ensure your CSV follows this structure for upload:</p>
    <pre style="background: rgba(0,0,0,0.3); padding: 0.8rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); font-size: 0.8rem; color: #a0aec0; overflow-x: auto;">
type, x1, x2, sign, RHS
obj ,  5,  4,  max,   0
con ,  6,  4,   &lt;=, 240
con ,  3,  2,   &lt;=, 270</pre>
</div>
""", unsafe_allow_html=True)

