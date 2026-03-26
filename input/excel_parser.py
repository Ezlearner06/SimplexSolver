"""
Excel Parser: Reads an .xlsx file and converts it to the standard problem dictionary.
Uses the same schema as the CSV parser (type | x1 | x2 | ... | sign | RHS).
"""

import pandas as pd


def parse_excel(file_buffer) -> dict:
    """
    Parse an Excel (.xlsx) file and return a problem dict.
    Raises ValueError on schema issues.
    """
    try:
        df = pd.read_excel(file_buffer, engine="openpyxl")
    except Exception as e:
        raise ValueError(f"Could not read Excel file: {e}")

    # Reuse the same validation logic as csv_parser
    from input.csv_parser import _dataframe_to_problem
    return _dataframe_to_problem(df)
