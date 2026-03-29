"""
Google Sheets Connector (with Local Fallback): 
Save/load problem history using Google Sheets API.
Falls back gracefully to a local JSON file if credentials are not available.
"""

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

LOCAL_HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "local_history.json")


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
    """Build and return the Google Sheets API service, or None if not configured."""
    if not SHEETS_AVAILABLE:
        return None

    try:
        creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS", "")
        if not creds_json:
            creds_file = os.path.join(os.path.dirname(__file__), "..", "credentials.json")
            if os.path.exists(creds_file):
                creds = Credentials.from_service_account_file(creds_file, scopes=SCOPES)
            else:
                return None
        else:
            creds_info = json.loads(creds_json)
            creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)

        return build("sheets", "v4", credentials=creds)
    except Exception:
        return None


def is_sheets_configured() -> bool:
    """Check if Google Sheets integration is properly configured."""
    if not SHEETS_AVAILABLE:
        return False
    if not _get_spreadsheet_id():
        return False
    if _get_service() is None:
        return False
    return True


def save_problem(problem: dict, result_summary: dict, name: str = ""):
    """
    Save a solved problem securely.
    Uses Google Sheets if configured, otherwise falls back to local JSON.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    problem_name = name or f"Problem_{timestamp}"
    
    record = {
        "timestamp": timestamp,
        "name": problem_name,
        "status": result_summary.get("status", ""),
        "optimal_value": str(result_summary.get("optimal_value", "")),
        "iterations": str(result_summary.get("iterations", "")),
        "problem": problem,
    }

    if is_sheets_configured():
        # Save to Google Sheets
        service = _get_service()
        sheet = service.spreadsheets()
        row = [
            record["timestamp"],
            record["name"],
            record["status"],
            record["optimal_value"],
            record["iterations"],
            json.dumps(record["problem"]),
        ]
        body = {"values": [row]}
        sheet.values().append(
            spreadsheetId=_get_spreadsheet_id(),
            range=f"{SHEET_NAME}!A:F",
            valueInputOption="RAW",
            body=body,
        ).execute()
    else:
        # Save to Local JSON
        history = []
        if os.path.exists(LOCAL_HISTORY_FILE):
            try:
                with open(LOCAL_HISTORY_FILE, "r") as f:
                    history = json.load(f)
            except Exception:
                pass
        
        history.append(record)
        with open(LOCAL_HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)
            
    return True


def load_history() -> list:
    """Load all saved problems from storage."""
    if is_sheets_configured():
        # Load from Google Sheets
        try:
            service = _get_service()
            sheet = service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=_get_spreadsheet_id(),
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
        except Exception as e:
            print(f"Error loading from sheets: {e}")
            return []
    else:
        # Load from Local JSON
        if os.path.exists(LOCAL_HISTORY_FILE):
            try:
                with open(LOCAL_HISTORY_FILE, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading local history: {e}")
                return []
        return []


LOCAL_HISTORY_FILE = os.path.join(os.path.dirname(__file__), "..", "history_local.json")


def _load_local() -> list:
    """Load history from local JSON file."""
    if os.path.exists(LOCAL_HISTORY_FILE):
        try:
            with open(LOCAL_HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_local(entry: dict):
    """Append one entry to local JSON file."""
    history = _load_local()
    history.insert(0, entry)  # newest first
    with open(LOCAL_HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def is_available() -> bool:
    """Check if storage is available (always True because we have local fallback)."""
    return True


def save_to_history(problem: dict, result_summary: dict, name: str = "") -> bool:
    """
    Save a solved problem. Tries Google Sheets first, falls back to local JSON.
    Returns True on success.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    problem_name = name or f"Problem_{timestamp}"

    entry = {
        "timestamp": timestamp,
        "name": problem_name,
        "status": result_summary.get("status", ""),
        "optimal_value": str(result_summary.get("optimal_value", "")),
        "iterations": str(result_summary.get("iterations", "")),
        "problem": problem,
    }

    if is_available():
        try:
            save_problem(problem, result_summary, name=problem_name)
            return True
        except Exception:
            pass

    # Fallback: local JSON
    _save_local(entry)
    return True


def get_history() -> list:
    """
    Load history. Tries Google Sheets first, falls back to local JSON.
    Returns a list of history dicts.
    """
    if is_available():
        try:
            return load_history()
        except Exception:
            pass
    return _load_local()
