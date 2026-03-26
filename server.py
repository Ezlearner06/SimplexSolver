import json
import io
import math
import plotly
import pandas as pd
import numpy as np
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
import uvicorn
import os

from engine.simplex import solve
from engine.sensitivity import compute_sensitivity
import dataclasses
from renderer.graphical_display import render_graphical_solution
from renderer.pdf_report import generate_pdf_report

# Parsers
from input.json_parser import parse_json
from input.csv_parser import parse_csv

def sanitize_for_json(obj):
    """Recursively convert numpy/pandas types to JSON-safe Python types."""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize_for_json(v) for v in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        val = float(obj)
        if math.isinf(val) or math.isnan(val):
            return None
        return val
    elif isinstance(obj, np.ndarray):
        return sanitize_for_json(obj.tolist())
    elif isinstance(obj, float):
        if math.isinf(obj) or math.isnan(obj):
            return None
        return obj
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif obj is None or isinstance(obj, (int, str, bool)):
        return obj
    else:
        # Fallback to string if we really don't know what it is
        try:
            # Let's see if we can just dump it directly, else fallback to string
            json.dumps(obj)
            return obj
        except Exception:
            return str(obj)


app = FastAPI()

# Make sure static directory exists
os.makedirs("static", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def read_root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post("/api/solve")
async def api_solve(request: Request):
    """Solve the LP problem and return all results including sensitivity and graph."""
    problem = await request.json()
    
    # 1. Run Core Solver
    result = solve(problem)
    
    # 2. Serialize Tableaux (Pandas DataFrames to dict)
    tableaux_list = []
    for tab in result.tableaux:
        # We need the columns, index(basis), and data
        data_dict = []
        for row_label in tab.index:
            row_data = {"Basis": str(row_label)}
            for col_label in tab.columns:
                row_data[str(col_label)] = tab.loc[row_label, col_label]
            data_dict.append(row_data)
        tableaux_list.append({
            "columns": ["Basis"] + [str(c) for c in tab.columns],
            "data": data_dict
        })
        
    # 3. Serialize Pivot Cells
    pivot_cells = []
    for i, pc in enumerate(result.pivot_cells):
        if pc and isinstance(pc, (tuple, list)) and len(pc) == 2:
            row_idx, col_idx = pc
            if i < len(result.tableaux):
                tab = result.tableaux[i]
                try:
                    row_val = str(tab.index[row_idx])
                    col_val = str(tab.columns[col_idx])
                    val = float(tab.iloc[row_idx, col_idx])
                    pivot_cells.append({
                        "iteration": i,
                        "row": row_val,
                        "column": col_val,
                        "value": val
                    })
                except Exception:
                    pivot_cells.append(None)
            else:
                pivot_cells.append(None)
        else:
            pivot_cells.append(None)
            
    response_data = {
        "status": result.status,
        "optimal_value": result.optimal_value,
        "variables": result.variables,
        "iterations": result.iterations,
        "tableaux": tableaux_list,
        "pivot_cells": pivot_cells,
        "sensitivity": None,
        "graph_json": None
    }
    
    # 4. Sensitivity Analysis & Graphical Solution (if optimal)
    if result.status == "optimal":
        # Sensitivity
        try:
            sens_obj = compute_sensitivity(problem, result)
            response_data["sensitivity"] = dataclasses.asdict(sens_obj)
        except Exception as e:
            print(f"Sensitivity error: {e}")
            pass
            
        # Graphical
        if len(problem.get("variables", [])) in [2, 3]:
            try:
                fig = render_graphical_solution(problem, result)
                if fig:
                    # Convert plotly figure to JSON
                    response_data["graph_json"] = json.loads(fig.to_json())
            except Exception as e:
                print(f"Graphical error: {e}")
                pass
                
    return JSONResponse(content=sanitize_for_json(response_data))


@app.post("/api/pdf")
async def api_pdf(request: Request):
    """Generate and return a PDF report for the given problem."""
    problem = await request.json()
    
    # Run solver
    result = solve(problem)
    
    sens_res = None
    fig = None
    
    if result.status == "optimal":
        try:
            sens_res = compute_sensitivity(problem, result)
        except Exception as e:
            print("PDF Sensitivity error", e)
            
        if len(problem.get("variables", [])) in [2, 3]:
            try:
                fig = render_graphical_solution(problem, result)
            except Exception as e:
                print("PDF Graphical error", e)
                
    pdf_bytes = generate_pdf_report(problem, result, sens_res, fig)
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=simplex_report.pdf"}
    )
    

@app.post("/api/upload")
async def api_upload(file: UploadFile = File(...)):
    """Parse uploaded file and return problem dict."""
    content = await file.read()
    filename = file.filename.lower()
    
    try:
        if filename.endswith(".json"):
            problem = parse_json(io.BytesIO(content))
        elif filename.endswith(".csv"):
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            with open(tmp_path, "rb") as f:
                problem = parse_csv(f)
            os.unlink(tmp_path)
        else:
            return JSONResponse(status_code=400, content={"error": "Unsupported file format."})
            
        return JSONResponse(content=problem)
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


@app.get("/api/history")
async def api_history():
    """Return past solved problems from Google Sheets (or stub if missing)."""
    try:
        from storage.sheets_connector import get_history
        history = get_history()
        return JSONResponse(content=history)
    except Exception as e:
        return JSONResponse(content=[])


if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8501, reload=True)
