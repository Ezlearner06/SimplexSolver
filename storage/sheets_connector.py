"""
Google Sheets Connector: Save/load problem history using Google Sheets API.
Falls back gracefully if credentials are not available.
"""

import streamlit as st
import json
import os
from datetime import datetime

# Flag to track if Google Sheets is available
SHEETS_AVAILABLE = False

try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    SHEETS_AVAILABLE = True
except ImportError:
    pass

# Google Sheets configuration
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_NAME = "SimplexHistory"

def _get_spreadsheet_id():
    """Load .env automatically and return GOOGLE_SHEET_ID."""
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ[k.strip()] = v.strip()
    return os.environ.get("GOOGLE_SHEET_ID", "")


def _get_service():
    """Build and return the Google Sheets API service."""
    if not SHEETS_AVAILABLE:
        raise RuntimeError("Google API libraries not installed. Install google-api-python-client.")

    creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS", "")
    if not creds_json:
        # Try loading from file
        creds_file = os.path.join(os.path.dirname(__file__), "..", "credentials.json")
        if os.path.exists(creds_file):
            creds = Credentials.from_service_account_file(creds_file, scopes=SCOPES)
        else:
            raise RuntimeError("Google Sheets credentials not found. Set GOOGLE_SHEETS_CREDENTIALS env var or provide credentials.json.")
    else:
        import json as _json
        creds_info = _json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)

    service = build("sheets", "v4", credentials=creds)
    return service


def save_problem(problem: dict, result_summary: dict, name: str = ""):
    """
    Save a solved problem to Google Sheets.
    Returns True on success, raises on failure.
    """
    service = _get_service()
    sheet = service.spreadsheets()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    problem_name = name or f"Problem_{timestamp}"

    row = [
        timestamp,
        problem_name,
        result_summary.get("status", ""),
        str(result_summary.get("optimal_value", "")),
        str(result_summary.get("iterations", "")),
        json.dumps(problem),
    ]

    spreadsheet_id = _get_spreadsheet_id()
    body = {"values": [row]}
    sheet.values().append(
        spreadsheetId=spreadsheet_id,
        range=f"{SHEET_NAME}!A:F",
        valueInputOption="RAW",
        body=body,
    ).execute()

    return True


def load_history() -> list:
    """
    Load all saved problems from Google Sheets.
    Returns a list of dicts with keys: timestamp, name, status, optimal_value, iterations, problem.
    """
    service = _get_service()
    sheet = service.spreadsheets()

    spreadsheet_id = _get_spreadsheet_id()
    result = sheet.values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{SHEET_NAME}!A:F",
    ).execute()

    values = result.get("values", [])
    history = []
    for row in values:
        if len(row) >= 6:
            try:
                problem = json.loads(row[5])
            except json.JSONDecodeError:
                problem = {}

            history.append({
                "timestamp": row[0],
                "name": row[1],
                "status": row[2],
                "optimal_value": row[3],
                "iterations": row[4],
                "problem": problem,
            })

    return history


def is_available() -> bool:
    """Check if Google Sheets integration is configured and available."""
    if not SHEETS_AVAILABLE:
        return False
    spreadsheet_id = _get_spreadsheet_id()
    if not spreadsheet_id:
        return False
    try:
        _get_service()
        return True
    except Exception:
        return False
