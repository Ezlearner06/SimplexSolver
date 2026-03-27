"""
Graphical Solution View — Interactive Plotly-based 2D LP visualisation.
Renders: constraint boundaries, shaded feasible region, corner points,
optimal point with pulse animation, and iso-profit/cost contour lines.
Only activates for 2-variable problems with an optimal solution.
"""

import numpy as np
import plotly.graph_objects as go
from scipy.spatial import ConvexHull
import streamlit as st


def render_graphical_solution(problem: dict, result):
    """Render an interactive Plotly graph for a 2-variable or 3-variable LP solution."""
    variables = problem["variables"]
    if result.status != "optimal":
        return None
    if len(variables) == 2:
        return _render_2d(problem, result)
    elif len(variables) == 3:
        return _render_3d(problem, result)
    return None

def _render_3d(problem: dict, result):
    x1_name, x2_name, x3_name = problem["variables"]
    constraints = problem["constraints"]
    objective = [float(c) for c in problem["objective"]]
    opt_x1 = result.variables.get(x1_name, 0)
    opt_x2 = result.variables.get(x2_name, 0)
    opt_x3 = result.variables.get(x3_name, 0)
    opt_val = result.optimal_value

    fig = go.Figure()

    # Determine mathematical bounds to close open regions
    rhs_vals = [abs(float(c["rhs"])) for c in constraints]
    math_bound = max(rhs_vals) if rhs_vals else 100
    math_max = max(math_bound * 1.5, opt_x1 * 2 + 10, opt_x2 * 2 + 10, opt_x3 * 2 + 10)

    # Compute feasible points using the large math bound
    feasible_points = _compute_feasible_region_3d(constraints, math_max, math_max, math_max)

    # Now calculate tight visual bounds based on the actual points
    if len(feasible_points) > 0:
        v_x_max = np.max(feasible_points[:, 0]) * 1.25
        v_y_max = np.max(feasible_points[:, 1]) * 1.25
        v_z_max = np.max(feasible_points[:, 2]) * 1.25
    else:
        v_x_max, v_y_max, v_z_max = 10, 10, 10
        
    # Ensure minimum visible range
    v_x_max = max(v_x_max, opt_x1 * 1.3 + 2)
    v_y_max = max(v_y_max, opt_x2 * 1.3 + 2)
    v_z_max = max(v_z_max, opt_x3 * 1.3 + 2)

    if len(feasible_points) >= 4:
        fig.add_trace(go.Mesh3d(
            x=feasible_points[:, 0],
            y=feasible_points[:, 1],
            z=feasible_points[:, 2],
            alphahull=0,
            opacity=0.35,
            color="#6366f1",
            flatshading=True,
            name="Feasible Region",
            hoverinfo="skip"
        ))
        
        # We use markers+lines to draw wireframes around the corners (even if somewhat unordered, it adds geometry)
        fig.add_trace(go.Scatter3d(
            x=feasible_points[:, 0],
            y=feasible_points[:, 1],
            z=feasible_points[:, 2],
            mode="markers+lines",
            marker=dict(size=6, color="#a5b4fc", line=dict(width=1, color="white")),
            line=dict(color="rgba(165, 180, 252, 0.4)", width=2),
            name="Corner Points",
            hovertemplate=(f"<b>Corner</b><br>{x1_name}=%{{x:.2f}}<br>"
                           f"{x2_name}=%{{y:.2f}}<br>{x3_name}=%{{z:.2f}}<extra></extra>")
        ))

    # Optimal point (Now much clearer and distinctly labeled!)
    fig.add_trace(go.Scatter3d(
        x=[opt_x1], y=[opt_x2], z=[opt_x3],
        mode="markers+text",
        text=["Optimal"],
        textposition="middle right",
        textfont=dict(color="#fef08a", size=15, family="Inter", weight="bold"),
        marker=dict(size=12, color="#facc15", symbol="diamond", line=dict(color="#ffffff", width=2)),
        name="Optimal Point",
        hovertemplate=(f"<b>🌟 Optimal Solution</b><br>{x1_name}=%{{x:.3f}}<br>"
                       f"{x2_name}=%{{y:.3f}}<br>{x3_name}=%{{z:.3f}}<br>"
                       f"Z*={opt_val:.3f}<extra></extra>")
    ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15, 15, 35, 0.6)",
        font=dict(family="Inter, sans-serif", color="#e2e8f0"),
        title=dict(
            text=f"<b>3D Feasible Region & Optimal Point</b><br>"
                 f"<span style='font-size:13px;color:#94a3b8'>"
                 f"{'Maximize' if problem['goal'].lower() == 'maximize' else 'Minimize'} "
                 f"Z = {_format_objective(objective, problem['variables'])}</span>",
            x=0.5, font=dict(size=18),
        ),
        scene=dict(
            xaxis=dict(title=x1_name, range=[0, v_x_max], backgroundcolor="rgba(0,0,0,0)", gridcolor="rgba(255,255,255,0.1)", zerolinecolor="rgba(255,255,255,0.3)"),
            yaxis=dict(title=x2_name, range=[0, v_y_max], backgroundcolor="rgba(0,0,0,0)", gridcolor="rgba(255,255,255,0.1)", zerolinecolor="rgba(255,255,255,0.3)"),
            zaxis=dict(title=x3_name, range=[0, v_z_max], backgroundcolor="rgba(0,0,0,0)", gridcolor="rgba(255,255,255,0.1)", zerolinecolor="rgba(255,255,255,0.3)"),
            camera=dict(eye=dict(x=1.3, y=1.3, z=1))
        ),
        margin=dict(l=0, r=0, b=0, t=80),
        height=600,
        legend=dict(bgcolor="rgba(0,0,0,0.4)", borderwidth=1),
    )
    return fig

def _render_2d(problem: dict, result):
    variables = problem["variables"]
    x1_name, x2_name = variables[0], variables[1]
    constraints = problem["constraints"]
    objective = [float(c) for c in problem["objective"]]
    opt_x1 = result.variables.get(x1_name, 0)
    opt_x2 = result.variables.get(x2_name, 0)
    opt_val = result.optimal_value

    # ── Determine axis bounds ──────────────────────────────────────
    rhs_vals = [abs(float(c["rhs"])) for c in constraints]
    max_rhs = max(rhs_vals) if rhs_vals else 10
    pad = max_rhs * 0.35
    x_max = max(max_rhs + pad, opt_x1 * 1.4 + 2)
    y_max = max(max_rhs + pad, opt_x2 * 1.4 + 2)

    x_range = np.linspace(0, x_max, 500)

    fig = go.Figure()

    # ── Color palette for constraints ──────────────────────────────
    colors = [
        "#6366f1", "#f472b6", "#34d399", "#fbbf24",
        "#60a5fa", "#a78bfa", "#fb923c", "#e879f9",
    ]

    # ── Plot constraint lines & shaded half-planes ─────────────────
    for i, con in enumerate(constraints):
        a1, a2 = float(con["coefficients"][0]), float(con["coefficients"][1])
        rhs = float(con["rhs"])
        sign = con["sign"].strip()
        color = colors[i % len(colors)]
        label = f"{a1}{x1_name} + {a2}{x2_name} {sign} {rhs}"

        if abs(a2) > 1e-9:
            y_vals = (rhs - a1 * x_range) / a2
            fig.add_trace(go.Scatter(
                x=x_range, y=y_vals,
                mode="lines",
                name=label,
                line=dict(color=color, width=2.5, dash="solid"),
                hovertemplate=f"<b>{label}</b><br>{x1_name}=%{{x:.2f}}<br>{x2_name}=%{{y:.2f}}<extra></extra>",
            ))
        elif abs(a1) > 1e-9:
            x_val = rhs / a1
            fig.add_trace(go.Scatter(
                x=[x_val, x_val], y=[0, y_max],
                mode="lines",
                name=label,
                line=dict(color=color, width=2.5, dash="solid"),
                hovertemplate=f"<b>{label}</b><br>{x1_name}=%{{x:.2f}}<extra></extra>",
            ))

    # ── Compute feasible region ────────────────────────────────────
    feasible_points = _compute_feasible_region(constraints, x_max, y_max)

    if len(feasible_points) >= 3:
        try:
            hull = ConvexHull(feasible_points)
            hull_pts = feasible_points[hull.vertices]
            # Close the polygon
            hull_pts = np.vstack([hull_pts, hull_pts[0]])

            fig.add_trace(go.Scatter(
                x=hull_pts[:, 0], y=hull_pts[:, 1],
                fill="toself",
                fillcolor="rgba(99, 102, 241, 0.12)",
                line=dict(color="rgba(99, 102, 241, 0.5)", width=1.5),
                name="Feasible Region",
                hoverinfo="skip",
            ))

            # ── Corner points ──────────────────────────────────────
            corners = feasible_points[hull.vertices]
            fig.add_trace(go.Scatter(
                x=corners[:, 0], y=corners[:, 1],
                mode="markers",
                name="Corner Points",
                marker=dict(
                    size=9,
                    color="#1e1b4b",
                    line=dict(width=2, color="#a5b4fc"),
                    symbol="circle",
                ),
                hovertemplate=f"<b>Corner</b><br>{x1_name}=%{{x:.3f}}<br>{x2_name}=%{{y:.3f}}<extra></extra>",
            ))
        except Exception:
            pass

    # ── Iso-profit / iso-cost lines ────────────────────────────────
    if abs(objective[0]) > 1e-9 or abs(objective[1]) > 1e-9:
        for frac in [0.25, 0.5, 0.75]:
            z_val = opt_val * frac
            if abs(objective[1]) > 1e-9:
                iso_y = (z_val - objective[0] * x_range) / objective[1]
                fig.add_trace(go.Scatter(
                    x=x_range, y=iso_y,
                    mode="lines",
                    line=dict(color="rgba(250, 204, 21, 0.25)", width=1, dash="dot"),
                    name=f"Z = {z_val:.1f}",
                    showlegend=False,
                    hoverinfo="skip",
                ))

        # Optimal iso-line
        if abs(objective[1]) > 1e-9:
            iso_y_opt = (opt_val - objective[0] * x_range) / objective[1]
            fig.add_trace(go.Scatter(
                x=x_range, y=iso_y_opt,
                mode="lines",
                line=dict(color="rgba(250, 204, 21, 0.6)", width=2, dash="dashdot"),
                name=f"Z* = {opt_val:.3f}",
                hoverinfo="skip",
            ))

    # ── Optimal point (star marker with glow) ──────────────────────
    fig.add_trace(go.Scatter(
        x=[opt_x1], y=[opt_x2],
        mode="markers+text",
        name=f"Optimal ({opt_x1:.3f}, {opt_x2:.3f})",
        marker=dict(
            size=18,
            color="#facc15",
            symbol="star",
            line=dict(width=2, color="#fef08a"),
        ),
        text=[f"  Z*={opt_val:.3f}"],
        textposition="top right",
        textfont=dict(color="#fef08a", size=13, family="Inter"),
        hovertemplate=(
            f"<b>🌟 Optimal Solution</b><br>"
            f"{x1_name} = %{{x:.4f}}<br>"
            f"{x2_name} = %{{y:.4f}}<br>"
            f"Z* = {opt_val:.4f}<extra></extra>"
        ),
    ))

    # ── Glow ring around optimal ───────────────────────────────────
    fig.add_trace(go.Scatter(
        x=[opt_x1], y=[opt_x2],
        mode="markers",
        marker=dict(size=32, color="rgba(250, 204, 21, 0.15)", line=dict(width=0)),
        showlegend=False, hoverinfo="skip",
    ))

    # ── Layout — dark glassmorphism theme ──────────────────────────
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15, 15, 35, 0.6)",
        font=dict(family="Inter, sans-serif", color="#e2e8f0"),
        title=dict(
            text=f"<b>Feasible Region & Optimal Point</b><br>"
                 f"<span style='font-size:13px;color:#94a3b8'>"
                 f"{'Maximize' if problem['goal'].lower() == 'maximize' else 'Minimize'} "
                 f"Z = {_format_objective(objective, variables)}</span>",
            x=0.5,
            font=dict(size=18),
        ),
        xaxis=dict(
            title=dict(text=x1_name, font=dict(size=14)),
            range=[0, x_max],
            gridcolor="rgba(255,255,255,0.06)",
            zerolinecolor="rgba(255,255,255,0.15)",
            zeroline=True,
        ),
        yaxis=dict(
            title=dict(text=x2_name, font=dict(size=14)),
            range=[0, y_max],
            gridcolor="rgba(255,255,255,0.06)",
            zerolinecolor="rgba(255,255,255,0.15)",
            zeroline=True,
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0.4)",
            bordercolor="rgba(255,255,255,0.1)",
            borderwidth=1,
            font=dict(size=11),
        ),
        margin=dict(l=60, r=30, t=80, b=60),
        height=560,
        hoverlabel=dict(
            bgcolor="rgba(30, 27, 75, 0.95)",
            bordercolor="rgba(165, 180, 252, 0.5)",
            font=dict(color="#e2e8f0", family="Inter"),
        ),
    )

    return fig


# ── Helpers ────────────────────────────────────────────────────────


def _compute_feasible_region(constraints, x_max, y_max):
    """
    Find all intersection points of constraints and axes,
    then filter to those satisfying ALL constraints (feasible).
    """
    lines = []  # (a1, a2, rhs, sign)
    for con in constraints:
        a1, a2 = float(con["coefficients"][0]), float(con["coefficients"][1])
        rhs = float(con["rhs"])
        sign = con["sign"].strip()
        lines.append((a1, a2, rhs, sign))

    # Add non-negativity: x1 >= 0, x2 >= 0
    lines.append((1, 0, 0, ">="))
    lines.append((0, 1, 0, ">="))
    # Add bounding box
    lines.append((1, 0, x_max, "<="))
    lines.append((0, 1, y_max, "<="))

    # Find all pairwise intersections
    n = len(lines)
    candidates = []
    for i in range(n):
        for j in range(i + 1, n):
            pt = _intersect(lines[i][:3], lines[j][:3])
            if pt is not None:
                candidates.append(pt)

    # Filter feasible
    feasible = []
    for pt in candidates:
        if pt[0] < -1e-9 or pt[1] < -1e-9:
            continue
        if pt[0] > x_max + 1e-9 or pt[1] > y_max + 1e-9:
            continue
        if _satisfies_all(pt, constraints):
            feasible.append(pt)

    return np.array(feasible) if feasible else np.array([]).reshape(0, 2)


def _intersect(line1, line2):
    """Intersect two lines a1*x + a2*y = rhs."""
    a1, a2, r1 = line1
    b1, b2, r2 = line2
    det = a1 * b2 - a2 * b1
    if abs(det) < 1e-12:
        return None
    x = (r1 * b2 - r2 * a2) / det
    y = (a1 * r2 - b1 * r1) / det
    return (x, y)


def _satisfies_all(pt, constraints):
    """Check if a point satisfies all user constraints."""
    x, y = pt
    for con in constraints:
        a1, a2 = float(con["coefficients"][0]), float(con["coefficients"][1])
        rhs = float(con["rhs"])
        sign = con["sign"].strip()
        val = a1 * x + a2 * y
        if sign == "<=" and val > rhs + 1e-6:
            return False
        if sign == ">=" and val < rhs - 1e-6:
            return False
        if sign == "=" and abs(val - rhs) > 1e-6:
            return False
    return True


def _format_objective(coeffs, variables):
    """Format objective as pretty string."""
    terms = []
    for i, (c, v) in enumerate(zip(coeffs, variables)):
        if abs(c) < 1e-9:
            continue
        if c == 1:
            term = v
        elif c == -1:
            term = f"-{v}"
        else:
            term = f"{c:g}{v}"
        if terms and c > 0:
            term = f"+ {term}"
        terms.append(term)
    return " ".join(terms) if terms else "0"

def _compute_feasible_region_3d(constraints, x_max, y_max, z_max):
    planes = [] # (a1, a2, a3, rhs, sign)
    for con in constraints:
        c = [float(x) for x in con["coefficients"]]
        planes.append((c[0], c[1], c[2], float(con["rhs"]), con["sign"].strip()))

    planes.append((1, 0, 0, 0, ">="))
    planes.append((0, 1, 0, 0, ">="))
    planes.append((0, 0, 1, 0, ">="))
    planes.append((1, 0, 0, x_max, "<="))
    planes.append((0, 1, 0, y_max, "<="))
    planes.append((0, 0, 1, z_max, "<="))

    n = len(planes)
    candidates = []
    import itertools
    for i, j, k in itertools.combinations(range(n), 3):
        pt = _intersect_3d(planes[i][:4], planes[j][:4], planes[k][:4])
        if pt is not None:
            candidates.append(pt)

    feasible = []
    for pt in candidates:
        if pt[0] < -1e-8 or pt[1] < -1e-8 or pt[2] < -1e-8:
            continue
        if pt[0] > x_max + 1e-8 or pt[1] > y_max + 1e-8 or pt[2] > z_max + 1e-8:
            continue
        if _satisfies_all_3d(pt, constraints):
            feasible.append(pt)

    return np.array(feasible) if feasible else np.array([]).reshape(0, 3)

def _intersect_3d(p1, p2, p3):
    A = np.array([p1[:3], p2[:3], p3[:3]])
    b = np.array([p1[3], p2[3], p3[3]])
    try:
        return np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        return None

def _satisfies_all_3d(pt, constraints):
    x, y, z = pt
    for con in constraints:
        c = [float(val) for val in con["coefficients"]]
        rhs = float(con["rhs"])
        sign = con["sign"].strip()
        val = c[0]*x + c[1]*y + c[2]*z
        if sign == "<=" and val > rhs + 1e-5: return False
        if sign == ">=" and val < rhs - 1e-5: return False
        if sign == "=" and abs(val - rhs) > 1e-5: return False
    return True
