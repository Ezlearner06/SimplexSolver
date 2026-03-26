**PRODUCT REQUIREMENTS DOCUMENT**
Simplex Method Solver — Linear Programming
*EM-4 (BSC07) Mini Project  |  INFT Engineering*

| Version | V1.0 — MVP |
|---|---|
| Date | March 2026 |
| Status | Draft — Ready for Team Review |
| Course | Statistical & Optimization Methods (BSC07) |
| Topic | Simplex Method — Linear Programming Problem Solver |
| Stack | Python · Streamlit · pandas · Google Sheets API |


*Confidential — Internal Academic Use Only*

# **1. Product Overview**
This document defines the requirements for a web-based Simplex Method solver built entirely in Python using Streamlit. The application enables students and educators to input Linear Programming Problems (LPPs) — via manual form or file upload — and receive a full step-by-step solution with an interactive tableau viewer.

## **1.1 Purpose**
Most Simplex implementations are either black-box calculators (show only the final answer) or CLI scripts (unreadable output). This tool fills the gap: a transparent, step-by-step solver that shows every tableau iteration in a clean UI, built by a beginner Python team as a graded academic project.

## **1.2 Scope — What This Document Covers**
Core Simplex algorithm engine (Standard Form, Pivot, Iteration loop)
Input system: Manual form + CSV / JSON / Excel file upload
Tableau iteration viewer with prev/next navigation
Problem history saved to Google Sheets
Deployment on Streamlit Community Cloud (free, shareable URL)
Documentation, sample files, README, and PPT/poster deliverables

# **2. Problem Statement**
## **2.1 The Core Problem**
The Simplex Method requires iterative tableau operations across multiple variables and constraints. As input size grows, three challenges emerge:

| Challenge | Impact |
|---|---|
| Large input volume | Manual entry of 15+ constraints is error-prone and slow |
| Many iterations | Displaying 30+ tableau tables at once is unreadable |
| No existing tool | Online solvers show only the final answer, not the process |
| Team collaboration | Unclear module ownership leads to uneven GitHub contributions |


## **2.2 Why Build This**
Existing online solvers (Desmos, WolframAlpha) do not show intermediate tableaux
A step-by-step viewer is genuinely useful for exam preparation and concept clarity
File upload support makes the tool practical for large real-world LPPs
A live deployed web app differentiates this submission from CLI-only alternatives

# **3. Target Users**
| User | Need | How This Helps |
|---|---|---|
| INFT Students (Primary) | Understand each iteration of Simplex for exams | Step-by-step tableau viewer with highlights |
| EM-4 Faculty (Secondary) | Evaluate the project; possibly use as teaching tool | Clean UI, correct output, sharable live URL |
| Project Team (Builders) | Demonstrate individual GitHub contributions | Clear module ownership, one module per member |


# **4. Core User Flows**
## **4.1 Flow A — Manual Entry (Small Problems)**
| Step | Action |
|---|---|
| 1 | User opens the Streamlit app in browser |
| 2 | Selects 'Manual Entry' tab |
| 3 | Enters number of variables (e.g. 3) and constraints (e.g. 4) |
| 4 | Dynamic form renders — user fills in objective coefficients, constraint matrix, RHS values, and signs (<=, >=, =) |
| 5 | Selects Maximize or Minimize goal |
| 6 | Clicks 'Solve' — spinner displays while computing |
| 7 | Results page shows: Optimal value, variable values, number of iterations |
| 8 | User navigates iterations with Prev / Next buttons — each tableau is displayed as a formatted table |
| 9 | Optionally saves problem to history (Google Sheets) |
| 10 | Optionally downloads result as CSV |


## **4.2 Flow B — File Upload (Large Problems)**
| Step | Action |
|---|---|
| 1 | User selects 'Upload File' tab |
| 2 | Uploads a .csv, .json, or .xlsx file (see schema in Section 6) |
| 3 | App auto-detects file type and parses it |
| 4 | Preview table renders: 'Is this your problem? Confirm / Re-upload' |
| 5 | User confirms — same Solve → Iterate flow as Flow A |


## **4.3 Flow C — Load from History**
| Step | Action |
|---|---|
| 1 | User selects 'History' tab |
| 2 | App fetches saved problems from Google Sheets |
| 3 | User selects a saved problem from the list |
| 4 | Problem is pre-loaded into the solver — user clicks Solve again |


# **5. Feature List**
## **5.1 MVP Features (V1 — Must Have)**
| Feature | Description | Owner |
|---|---|---|
| Simplex Core Engine | Standard form conversion, pivot selection (most negative), ratio test, row operations, termination check | Member 1 |
| Manual Input Form | Dynamic form based on variable/constraint count, validates all fields before solving | Member 2 |
| CSV File Upload | Parse .csv with defined schema, show preview before solving | Member 2 |
| JSON File Upload | Parse .json structured input, same preview flow | Member 2 |
| Excel (.xlsx) Upload | Parse .xlsx using openpyxl, same preview flow | Member 2 |
| Tableau Iteration Viewer | Show one tableau per screen, Prev/Next navigation, highlight pivot cell | Member 3 |
| Solution Summary | Display optimal value, variable values, iteration count, status badge | Member 3 |
| Google Sheets History | Save problem name + result to Sheets; load history list back into app | Member 4 |
| CSV Result Download | Export final answer + all tableaux as a downloadable CSV | Member 4 |
| Sample Input Files | 5 sample files: small, medium, large, infeasible, unbounded | Member 5 |
| README Documentation | Install steps, usage guide, schema reference, team credits | Member 5 |


## **5.2 Future Features (Post-V1 — Do Not Build Now)**
| Feature | Reason Deferred |
|---|---|
| Big-M Method | Adds complexity to engine; two-phase is sufficient for V1 scope |
| Graphical Solution (2-variable) | Visualization library adds scope; not needed for correctness evaluation |
| Sensitivity Analysis | Advanced topic beyond BSC07 syllabus requirements |
| User Authentication / Login | Overkill for academic project; Google Sheets handles persistence |
| Async / Background Jobs | Not needed at this scale; Streamlit caching is sufficient |
| PDF Report Export | ReportLab adds complexity; CSV download covers the requirement |
| Mobile-Optimized UI | Streamlit handles basic responsiveness; deep mobile work is out of scope |


# **6. Input File Schema**
## **6.1 CSV Format**
This schema must be agreed by the full team in Week 1. It is the contract between the Input Handler and the Core Engine.

| type | x1 | x2 | x3 | sign | RHS |
|---|---|---|---|---|---|
| objective | 5 | 4 | 3 | maximize | 0 |
| constraint | 6 | 4 | 2 | <= | 240 |
| constraint | 3 | 2 | 5 | <= | 270 |
| constraint | 5 | 6 | 5 | >= | 420 |


Column 'type': always 'objective' or 'constraint'
Columns x1..xN: integer or float coefficients
Column 'sign': <=, >=, or = (objective row uses 'maximize' or 'minimize' here)
Column 'RHS': right-hand side value (0 for objective row)

## **6.2 Internal Data Dictionary (Python)**
All input formats — form, CSV, JSON, Excel — must produce this exact dictionary before being passed to the Core Engine:

| Key | Value / Type |
|---|---|
| goal | String: 'maximize' or 'minimize' |
| variables | List of strings: ['x1', 'x2', 'x3'] |
| objective | List of floats: [5.0, 4.0, 3.0] |
| constraints | List of dicts, each with keys: coefficients (list), sign (str), rhs (float) |


# **7. Edge Cases & Error Handling**
| Edge Case | How It Arises | Required Handling |
|---|---|---|
| Infeasible Problem | Constraints are contradictory — no feasible region exists | Detect during Phase 1 / Big-M. Show clear message: 'No feasible solution exists.' |
| Unbounded Problem | Objective can increase infinitely — no finite optimum | Detect when no valid ratio test row exists. Show: 'Problem is unbounded.' |
| Degenerate Solution | One or more BFS values = 0 in RHS — risk of cycling | Flag degeneracy in output; limit max iterations to 100 to prevent infinite loops |
| Zero Coefficients | User enters all zeros for an objective coefficient | Validate: warn but allow — zero coefficient is mathematically valid |
| Non-numeric Input (Form) | User types text in a coefficient field | Streamlit number_input prevents this — also validate in handler before passing to engine |
| Wrong CSV Schema | Uploaded file missing 'sign' or 'RHS' column | Detect missing columns; show specific error: 'Column RHS not found. Check sample file.' |
| Empty File Upload | User uploads a blank or 0-byte file | Detect file size before parsing; show: 'File appears to be empty.' |
| One Variable / One Constraint | Trivial edge case — valid but degenerate input | Engine should handle gracefully; show solution normally |
| Max Iteration Limit Reached | Cycling or very large problem exceeds 100 iterations | Stop and show: 'Max iterations reached. Problem may be cycling or too large.' |
| Google Sheets Unavailable | API credentials missing or quota exceeded | Catch exception gracefully; disable Save/History tabs with a warning — do not crash the app |


# **8. Non-Goals**
The following are explicitly out of scope for V1. These decisions are intentional — not oversights.

User accounts or login system — Google Sheets handles persistence without authentication
Mobile-first or responsive design — Streamlit's default layout is sufficient for desktop/laptop use
Real-time collaboration — this is a single-user solver, not a multiplayer tool
Support for Integer Programming (ILP) or Mixed-Integer Programming (MIP) — these require Branch & Bound, a separate algorithm
Sensitivity / post-optimality analysis — beyond BSC07 syllabus
PDF export — CSV download meets the requirement; PDF adds library complexity
Dark mode or custom theming — Streamlit default theme is acceptable
Multi-language support — English only
Backend server / REST API — everything runs client-side in Streamlit; no separate server needed
Handling problems with more than 20 variables or 30 constraints — not needed for academic scope; performance not guaranteed beyond this

# **9. Success Metrics**
## **9.1 Correctness**
| Metric | Target |
|---|---|
| Textbook test cases pass | 5/5 sample problems produce correct known optimal values |
| Edge case detection | All 3 types (optimal, infeasible, unbounded) correctly identified |
| Iteration accuracy | Each tableau snapshot matches manual calculation for 2-variable problems |


## **9.2 Usability**
| Metric | Target |
|---|---|
| Time to solve (small problem) | < 3 seconds for problems with <= 5 variables, <= 8 constraints |
| File upload parsing | CSV / JSON / Excel parse correctly without manual intervention |
| Error messages | All invalid inputs show a human-readable message — zero silent crashes |
| Iteration navigation | Prev/Next buttons work correctly across all iteration counts |


## **9.3 Collaboration**
| Metric | Target |
|---|---|
| GitHub contributions | Every team member has >= 10 meaningful commits on their module |
| Pull Requests | Every module merged via PR with at least 1 reviewer |
| Module separation | No module file is edited by more than 2 members |
| README completeness | Covers: install, usage, schema, sample files, team credits |


## **9.4 Deployment**
| Metric | Target |
|---|---|
| Live deployment | App accessible via public Streamlit Cloud URL |
| Uptime during demo | App loads successfully during faculty evaluation session |
| Zero paid services | All tools used are free tier — no credit card required |


# **10. Team Module Ownership & Timeline**
## **10.1 Module Ownership**
| Member | Module | Deliverable Files | GitHub Branch |
|---|---|---|---|
| Member 1 | Core Engine | engine/simplex.py | feature/core-engine |
| Member 2 | Input Handler | input/input_handler.py, csv_parser.py, json_parser.py, excel_parser.py | feature/input-handler |
| Member 3 | Tableau Renderer | renderer/tableau_display.py | feature/tableau-renderer |
| Member 4 | Storage & Export | storage/sheets_connector.py | feature/storage |
| Member 5 | Docs, Tests & Samples | tests/test_simplex.py, sample_inputs/, README.md | feature/docs-tests |


## **10.2 5-Week Timeline**
| Week | Team Milestone | Individual Focus |
|---|---|---|
| Week 1 | Repo setup, agree on input schema, install Streamlit locally | All: scaffold module files, write empty function stubs with comments |
| Week 2 | Daily standups — unblock each other | M1: Standard form + initial tableau. M2: Manual form UI. M3: Static table display. M4: Sheets connection test. M5: Sample files |
| Week 3 | Integration meeting — wire all modules into app.py | M1: Full pivot loop + termination. M2: File upload parsers. M3: Iteration navigation. M4: Save + load history |
| Week 4 | Test all 5 sample files end-to-end; fix bugs | All: Edge case handling. M5: Write unit tests for engine. Begin README |
| Week 5 | Code freeze — no new features | M5: Finalize README, PPT, poster. All: Review, deploy to Streamlit Cloud, prepare demo |
