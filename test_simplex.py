import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from engine.simplex import solve

# Test 1: MAX with <=  (standard)
print("=== TEST 1: MAX with <= ===")
r1 = solve({
    "goal": "maximize",
    "variables": ["x1", "x2"],
    "objective": [3.0, 5.0],
    "constraints": [
        {"coefficients": [1.0, 2.0], "sign": "<=", "rhs": 10.0},
        {"coefficients": [3.0, 1.0], "sign": "<=", "rhs": 15.0}
    ]
})
print(f"Status: {r1.status}, Z={r1.optimal_value}, vars={r1.variables}")

# Test 2: MIN with >= (should convert to MAX with <=)
print("\n=== TEST 2: MIN with >= ===")
r2 = solve({
    "goal": "minimize",
    "variables": ["x1", "x2"],
    "objective": [1.0, 1.0],
    "constraints": [
        {"coefficients": [1.0, 1.0], "sign": ">=", "rhs": 4.0},
        {"coefficients": [1.0, 2.0], "sign": ">=", "rhs": 6.0}
    ]
})
print(f"Status: {r2.status}, Z={r2.optimal_value}, vars={r2.variables}")
print(f"Messages: {r2.messages}")

# Test 3: = constraint (should error)
print("\n=== TEST 3: Equality constraint ===")
r3 = solve({
    "goal": "minimize",
    "variables": ["x1", "x2"],
    "objective": [1.0, 1.0],
    "constraints": [
        {"coefficients": [1.0, 1.0], "sign": "=", "rhs": 4.0}
    ]
})
print(f"Status: {r3.status}")
print(f"Messages: {r3.messages}")
