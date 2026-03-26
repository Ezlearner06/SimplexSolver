# 📐 Simplex Method Solver

A web-based **step-by-step Simplex Method solver** for Linear Programming Problems (LPPs), built with Python and Streamlit.

> EM-4 (BSC07) Mini Project — Statistical & Optimization Methods

---

## ✨ Features

- **Manual Entry:** Dynamic form to input variables, constraints, and objective function
- **File Upload:** Supports `.csv`, `.json`, and `.xlsx` formats
- **Step-by-Step Tableau Viewer:** Navigate each iteration with Prev/Next buttons and pivot cell highlighting
- **Edge Case Detection:** Identifies Optimal, Infeasible, Unbounded, and Degenerate solutions
- **Google Sheets History:** Save and reload past problems (optional)
- **CSV Export:** Download results and all tableaux as a CSV file

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

---

## 📄 Input File Schema

### CSV Format

| type       | x1 | x2 | x3 | sign     | RHS |
|------------|----|----|-----|----------|-----|
| objective  | 5  | 4  | 3   | maximize | 0   |
| constraint | 6  | 4  | 2   | <=       | 240 |
| constraint | 3  | 2  | 5   | <=       | 270 |

### JSON Format

```json
{
    "goal": "maximize",
    "variables": ["x1", "x2", "x3"],
    "objective": [5, 4, 3],
    "constraints": [
        {"coefficients": [6, 4, 2], "sign": "<=", "rhs": 240},
        {"coefficients": [3, 2, 5], "sign": "<=", "rhs": 270}
    ]
}
```

### Excel Format

Same structure as CSV — use a single sheet with the same column headers.

---

## 📁 Project Structure

```
EM-4/
├── app.py                      # Main Streamlit app
├── requirements.txt            # Python dependencies
├── engine/
│   └── simplex.py              # Core Simplex algorithm
├── input/
│   ├── input_handler.py        # Manual entry form
│   ├── csv_parser.py           # CSV file parser
│   ├── json_parser.py          # JSON file parser
│   └── excel_parser.py         # Excel file parser
├── renderer/
│   └── tableau_display.py      # Tableau viewer & solution summary
├── storage/
│   └── sheets_connector.py     # Google Sheets integration
├── tests/
│   └── test_simplex.py         # Unit tests
└── sample_inputs/
    ├── small_problem.csv
    ├── medium_problem.csv
    ├── large_problem.csv
    ├── infeasible_problem.csv
    ├── unbounded_problem.csv
    └── sample_problem.json
```

---

## 🧪 Running Tests

```bash
pytest tests/test_simplex.py -v
```

---

## ☁️ Google Sheets Setup (Optional)

1. Create a Google Cloud project and enable the Sheets API
2. Create a Service Account and download `credentials.json`
3. Place `credentials.json` in the project root
4. Set the environment variable: `GOOGLE_SHEET_ID=your_spreadsheet_id`

---

## 🚀 Deployment (Streamlit Cloud)

1. Push the repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo and set `app.py` as the entry point
4. Add secrets for Google Sheets (if applicable)

---

## 👥 Team

| Member   | Module              |
|----------|---------------------|
| Member 1 | Core Engine         |
| Member 2 | Input Handler       |
| Member 3 | Tableau Renderer    |
| Member 4 | Storage & Export    |
| Member 5 | Docs, Tests & Samples |

---

*Built for EM-4 (BSC07) — INFT Engineering, March 2026*
