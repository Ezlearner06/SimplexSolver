"""
Unit Tests for the Simplex Core Engine.
Covers: optimal, infeasible, unbounded, degenerate, minimize, and edge cases.
"""

import sys
import os
import pytest

# Ensure imports work from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.simplex import solve


# ── Test 1: Basic Maximisation (Textbook) ────────────────────────────
def test_basic_maximisation():
    """
    Maximize Z = 5x1 + 4x2
    Subject to:  6x1 + 4x2 <= 24
                  x1 + 2x2 <= 6
    Expected: x1=3, x2=1.5, Z=21
    """
    problem = {
        "goal": "maximize",
        "variables": ["x1", "x2"],
        "objective": [5, 4],
        "constraints": [
            {"coefficients": [6, 4], "sign": "<=", "rhs": 24},
            {"coefficients": [1, 2], "sign": "<=", "rhs": 6},
        ],
    }
    result = solve(problem)
    assert result.status == "optimal"
    assert abs(result.optimal_value - 21.0) < 0.01
    assert abs(result.variables["x1"] - 3.0) < 0.01
    assert abs(result.variables["x2"] - 1.5) < 0.01


# ── Test 2: Three-Variable Problem ──────────────────────────────────
def test_three_variable():
    """
    Maximize Z = 3x1 + 5x2 + 4x3
    Subject to:  2x1 +  3x2 <=  8
                 2x1 +  5x2 <= 10
                 3x1 +  2x2 + 4x3 <= 15
    """
    problem = {
        "goal": "maximize",
        "variables": ["x1", "x2", "x3"],
        "objective": [3, 5, 4],
        "constraints": [
            {"coefficients": [2, 3, 0], "sign": "<=", "rhs": 8},
            {"coefficients": [2, 5, 0], "sign": "<=", "rhs": 10},
            {"coefficients": [3, 2, 4], "sign": "<=", "rhs": 15},
        ],
    }
    result = solve(problem)
    assert result.status == "optimal"
    assert result.optimal_value is not None
    assert result.iterations > 0
    assert len(result.tableaux) > 1


# ── Test 3: Minimisation ─────────────────────────────────────────────
def test_minimisation():
    """
    Minimize Z = 2x1 + 3x2
    Subject to:  x1 +  x2 >= 4
                 x1 + 3x2 >= 6
    """
    problem = {
        "goal": "minimize",
        "variables": ["x1", "x2"],
        "objective": [2, 3],
        "constraints": [
            {"coefficients": [1, 1], "sign": ">=", "rhs": 4},
            {"coefficients": [1, 3], "sign": ">=", "rhs": 6},
        ],
    }
    result = solve(problem)
    assert result.status == "optimal"
    assert result.optimal_value is not None


# ── Test 4: Unbounded Problem ────────────────────────────────────────
def test_unbounded():
    """
    Maximize Z = 2x1 + x2
    Subject to:  -x1 + x2 <= 1
                 -x1 - 2x2 <= 0
    Should be unbounded.
    """
    problem = {
        "goal": "maximize",
        "variables": ["x1", "x2"],
        "objective": [2, 1],
        "constraints": [
            {"coefficients": [-1, 1], "sign": "<=", "rhs": 1},
            {"coefficients": [-1, -2], "sign": "<=", "rhs": 0},
        ],
    }
    result = solve(problem)
    assert result.status == "unbounded"


# ── Test 5: Single Variable ─────────────────────────────────────────
def test_single_variable():
    """
    Maximize Z = 5x1
    Subject to: x1 <= 10
    Expected: x1=10, Z=50
    """
    problem = {
        "goal": "maximize",
        "variables": ["x1"],
        "objective": [5],
        "constraints": [
            {"coefficients": [1], "sign": "<=", "rhs": 10},
        ],
    }
    result = solve(problem)
    assert result.status == "optimal"
    assert abs(result.optimal_value - 50.0) < 0.01
    assert abs(result.variables["x1"] - 10.0) < 0.01


# ── Test 6: Validation Errors ────────────────────────────────────────
def test_missing_key():
    """Should return error status when required keys are missing."""
    problem = {"goal": "maximize"}
    result = solve(problem)
    assert result.status == "error"


def test_invalid_goal():
    """Should return error for invalid goal."""
    problem = {
        "goal": "maxify",
        "variables": ["x1"],
        "objective": [5],
        "constraints": [{"coefficients": [1], "sign": "<=", "rhs": 10}],
    }
    result = solve(problem)
    assert result.status == "error"


def test_mismatched_coefficients():
    """Should return error when coefficient count doesn't match variable count."""
    problem = {
        "goal": "maximize",
        "variables": ["x1", "x2"],
        "objective": [5],
        "constraints": [{"coefficients": [1, 2], "sign": "<=", "rhs": 10}],
    }
    result = solve(problem)
    assert result.status == "error"


# ── Test 7: Tableau snapshots ────────────────────────────────────────
def test_tableaux_recorded():
    """Every solve should produce at least one tableau snapshot."""
    problem = {
        "goal": "maximize",
        "variables": ["x1", "x2"],
        "objective": [5, 4],
        "constraints": [
            {"coefficients": [6, 4], "sign": "<=", "rhs": 24},
            {"coefficients": [1, 2], "sign": "<=", "rhs": 6},
        ],
    }
    result = solve(problem)
    assert len(result.tableaux) >= 2  # initial + at least one iteration
    assert "RHS" in result.tableaux[0].columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
