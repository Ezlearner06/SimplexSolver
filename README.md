<div align="center">

<img src="https://img.shields.io/badge/Simplex%20Method-Solver-7c3aed?style=for-the-badge&logo=python&logoColor=white" alt="Simplex Solver" />

# 📐 Simplex Method Solver

**A professional, step-by-step Linear Programming Problem solver with interactive tableau navigation.**

[![Live App](https://img.shields.io/badge/Live%20App-Streamlit%20Cloud-ff4b4b?style=flat-square&logo=streamlit)](https://your-app-link.streamlit.app)
[![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-181717?style=flat-square&logo=github)](https://github.com/your-repo-link)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-ff4b4b?style=flat-square&logo=streamlit)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

*EM-4 (BSC07) Mini Project — Statistical & Optimization Methods | INFT Engineering*

</div>

---

## 📖 Overview

Most Simplex solvers are either black-box calculators (show only the final answer) or unreadable CLI scripts. **Simplex Method Solver** fills the gap — a transparent, step-by-step solver that shows **every tableau iteration** in a clean, interactive web UI.

Built with Python and Streamlit, this tool enables students and educators to input Linear Programming Problems (LPPs) via a manual form or file upload, and receive a full solution with interactive iteration navigation.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Simplex Core Engine** | Standard form conversion, pivot selection (most negative), ratio test, row operations, full termination check |
| **Manual Entry Form** | Dynamic form supporting up to 50 variables and constraints — validates all fields before solving |
| **File Upload Support** | Parse `.csv`, `.json`, and `.xlsx` files — schema auto-detected with confirmation preview |
| **Interactive Tableau Viewer** | Step through every iteration with Prev / Next navigation; pivot cell highlighted |
| **Solution Summary** | Displays optimal value, variable values, iteration count, and status badge |
| **Smart Edge Case Detection** | Detects infeasible, unbounded, and degenerate problems with clear messages |
| **Google Sheets History** | Save named problems and results to Google Sheets; reload and re-solve from history tab |
| **CSV Result Download** | Export the full solution + all tableau snapshots as a downloadable `.csv` |
| **Sample Input Files** | 5 ready-to-use sample files: small, medium, large, infeasible, and unbounded |

---

## 🖥️ App Tabs

### 📝 Manual Entry
1. Set the number of variables and constraints
2. Fill in the objective coefficients, constraint matrix, RHS values, and signs (`<=`, `>=`, `=`)
3. Select **Maximize** or **Minimize**
4. Click **Solve** — view the solution summary and navigate each tableau step

### 📁 Upload File
1. Upload a `.csv`, `.json`, or `.xlsx` file
2. Preview the extracted problem data
3. Confirm and solve — get the same full step-by-step output

### 📜 History
- View all previously saved problems from Google Sheets
- Reload any past problem and re-solve it in one click

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend / UI** | Streamlit ≥ 1.30 |
| **Data Processing** | pandas ≥ 2.0, NumPy ≥ 1.24 |
| **Excel Parsing** | openpyxl ≥ 3.1 |
| **History Storage** | Google Sheets API (`google-api-python-client`) |
| **Testing** | pytest ≥ 7.4 |
| **Deployment** | Streamlit Community Cloud |

---

## 📁 Project Structure

```
simplex-solver/
├── app.py                    # Main Streamlit app — wires all modules
│
├── engine/
│   └── simplex.py            # Core Simplex algorithm engine
│
├── input/
│   ├── input_handler.py      # Manual form UI
│   ├── csv_parser.py         # CSV file parser
│   ├── json_parser.py        # JSON file parser
│   └── excel_parser.py       # Excel (.xlsx) parser
│
├── renderer/
│   └── tableau_display.py    # Tableau viewer + solution summary
│
├── storage/
│   └── sheets_connector.py   # Google Sheets save/load
│
├── sample_inputs/
│   ├── small_problem.csv
│   ├── medium_problem.csv
│   ├── large_problem.csv
│   ├── infeasible_problem.csv
│   ├── unbounded_problem.csv
│   └── sample_problem.json
│
├── tests/
│   └── test_simplex.py
│
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- pip

### 1. Clone the Repository

```bash
git clone https://github.com/your-repo-link/simplex-solver.git
cd simplex-solver
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables (Optional — for Google Sheets History)

Create a `.env` file in the root directory:

```env
GOOGLE_SHEET_ID=your_google_sheet_id
```

Also place your `credentials.json` (Google Service Account key) in the project root.

> ⚠️ **Never commit your `.env` file or `credentials.json` to GitHub.**  
> The app works fully without Google Sheets — history features will be disabled with a clear warning.

### 4. Run the App

```bash
streamlit run app.py
```

The application will start at: **http://localhost:8501**

---

## 📄 Input File Schema

### CSV Format

Your CSV must follow this schema:

```
type,       x1, x2, x3, sign,     RHS
objective,   5,  4,  3, maximize,   0
constraint,  6,  4,  2, <=,       240
constraint,  3,  2,  5, <=,       270
constraint,  5,  6,  5, >=,       420
```

- `type`: `objective` or `constraint`
- `x1..xN`: integer or float coefficients
- `sign`: `<=`, `>=`, `=` for constraints; `maximize` or `minimize` for the objective row
- `RHS`: right-hand side value (`0` for objective row)

### JSON Format

```json
{
  "goal": "maximize",
  "variables": ["x1", "x2"],
  "objective": [5, 4],
  "constraints": [
    { "coefficients": [6, 4], "sign": "<=", "rhs": 240 },
    { "coefficients": [3, 2], "sign": "<=", "rhs": 270 }
  ]
}
```

---

## ⚠️ Edge Case Handling

| Condition | Behavior |
|---|---|
| **Infeasible Problem** | Shows: *"No feasible solution exists."* |
| **Unbounded Problem** | Shows: *"Problem is unbounded."* |
| **Degenerate Solution** | Flags degeneracy; limits to 100 iterations |
| **Empty / Invalid File** | Shows specific, human-readable error |
| **Wrong CSV Schema** | Shows: *"Column RHS not found. Check sample file."* |
| **Google Sheets Unavailable** | Gracefully disables Save/History — app does not crash |

---

## 🧪 Running Tests

```bash
pytest tests/
```

---

## 👥 Team Module Ownership

| Member | Module | Files |
|---|---|---|
| Member 1 | Core Engine | `engine/simplex.py` |
| Member 2 | Input Handler | `input/input_handler.py`, `csv_parser.py`, `json_parser.py`, `excel_parser.py` |
| Member 3 | Tableau Renderer | `renderer/tableau_display.py` |
| Member 4 | Storage & Export | `storage/sheets_connector.py` |
| Member 5 | Docs, Tests & Samples | `tests/test_simplex.py`, `sample_inputs/`, `README.md` |

---

## 🔮 Future Enhancements

- [ ] Big-M Method support
- [ ] Graphical solution view for 2-variable problems
- [ ] Sensitivity / post-optimality analysis
- [ ] PDF report export
- [ ] Mobile-optimized layout

---

## Poster 
<img width="1842" height="2304" alt="Simple_Poster" src="https://github.com/user-attachments/assets/dd28e095-dfb0-4cc7-aa95-0b2684dc7ae6" />


<div align="center">

Built for the **EM-4 (BSC07) Mini Project** — Statistical & Optimization Methods | INFT Engineering | March 2026

</div>
