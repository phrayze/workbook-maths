import random
import math
import os
import csv
import re
import calendar
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

class Question(BaseModel):
    id: int = 0
    section: str = ""
    topic: str = ""
    stage: int = 2
    outcome_code: str = ""      # e.g. "MA1-2DS-01"
    focus_area: str = ""        # e.g. "Two-dimensional (2D) spatial structure"
    capability: str = ""        # NESA Capability statement
    q_type: str = "math"        # 'xlop', 'tikz', 'word', 'math', 'mcq'
    prompt_tex: str
    solution_tex: str
    answer_value: str = ""      # Plain-text canonical answer (e.g. "742", "3/4", "14:45"), for auto-marking/MCQ
    layout_hint: str = "list"   # 'grid_3col' or 'list'

# ==============================================================================
# EXHAUSTIVE NESA MATHEMATICS K–6 SYLLABUS OUTCOME REGISTRY (STAGES ES1, 1, 2 & 3)
# Loaded dynamically from maths-curriculum-ks1_2_3.csv if available
# ==============================================================================

def _load_csv_outcomes() -> Dict[str, Dict[str, Any]]:
    csv_dict = {}
    csv_filename = "maths-curriculum-ks1_2_3.csv"
    search_paths = [
        csv_filename,
        os.path.join(os.path.dirname(__file__), csv_filename),
        os.path.join(os.path.dirname(__file__), "..", csv_filename)
    ]
    found_path = None
    for p in search_paths:
        if os.path.exists(p):
            found_path = p
            break
            
    if found_path:
        try:
            with open(found_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    key = row.get("Key", "").strip()
                    stage_raw = row.get("Stage", "").strip()
                    stage_num = 0 if stage_raw.upper() == "ES1" else (int(stage_raw) if stage_raw.isdigit() else 2)
                    focus = row.get("Focus Area", "").strip()
                    cap = row.get("Capability", "").strip()
                    
                    if key:
                        csv_dict[key] = {
                            "stage": stage_num,
                            "stage_raw": stage_raw,
                            "focus_area": focus,
                            "capability": cap,
                        }
        except Exception as e:
            print(f"Warning: Could not read {found_path}: {e}")
    return csv_dict

OUTCOME_REGISTRY: Dict[str, Dict[str, Any]] = {
    # Early Stage 1 (ES1)
    "MAE-RWN-01": {"stage": 0, "focus_area": "Representing numbers", "capability": "demonstrates an understanding of how whole numbers indicate quantity", "topic": "representing_numbers"},
    "MAE-RWN-02": {"stage": 0, "focus_area": "Representing numbers", "capability": "reads numerals and represents whole numbers to at least 20", "topic": "representing_numbers"},
    "MAE-CSQ-01": {"stage": 0, "focus_area": "Combining and separating quantities", "capability": "reasons about number relations to model addition and subtraction by combining and separating, and comparing collections", "topic": "vertical_addition"},
    "MAE-CSQ-02": {"stage": 0, "focus_area": "Combining and separating quantities", "capability": "represents the relations between the parts that form the whole, with numbers up to 10", "topic": "vertical_addition"},
    "MAE-FG-01": {"stage": 0, "focus_area": "Forming groups", "capability": "recognises, describes and continues repeating patterns", "topic": "sequences"},
    "MAE-FG-02": {"stage": 0, "focus_area": "Forming groups", "capability": "forms equal groups by sharing and counting collections of objects", "topic": "vertical_multiplication"},
    "MAE-GM-01": {"stage": 0, "focus_area": "Geometric measure", "capability": "describes position and gives and follows simple directions", "topic": "geometry_angles"},
    "MAE-GM-02": {"stage": 0, "focus_area": "Geometric measure", "capability": "describes and compares lengths", "topic": "length"},
    "MAE-GM-03": {"stage": 0, "focus_area": "Geometric measure", "capability": "identifies half the length and the halfway point", "topic": "length"},
    "MAE-2DS-01": {"stage": 0, "focus_area": "Two-dimensional (2D) spatial structure", "capability": "sorts, describes, names and makes two-dimensional shapes, including triangles, circles, squares and rectangles", "topic": "2d_shapes"},
    "MAE-2DS-02": {"stage": 0, "focus_area": "Two-dimensional (2D) spatial structure", "capability": "describes and compares areas of similar shapes", "topic": "area"},
    "MAE-3DS-01": {"stage": 0, "focus_area": "Three-dimensional (3D) spatial structure", "capability": "manipulates, describes and sorts three-dimensional objects", "topic": "3d_objects"},
    "MAE-3DS-02": {"stage": 0, "focus_area": "Three-dimensional (3D) spatial structure", "capability": "describes and compares volumes", "topic": "volume"},
    "MAE-NSM-01": {"stage": 0, "focus_area": "Non-spatial measure", "capability": "describes and compares the masses of objects", "topic": "mass"},
    "MAE-NSM-02": {"stage": 0, "focus_area": "Non-spatial measure", "capability": "sequences events and reads hour time on clocks", "topic": "reading_time"},
    "MAE-DATA-01": {"stage": 0, "focus_area": "Data", "capability": "contributes to collecting data and interprets data displays made from objects", "topic": "data"},

    # Stage 1 (Years 1–2)
    "MA1-RWN-01": {"stage": 1, "focus_area": "Representing numbers", "capability": "applies an understanding of place value and the role of zero to read, write and order two- and three-digit numbers", "topic": "representing_numbers"},
    "MA1-RWN-02": {"stage": 1, "focus_area": "Representing numbers", "capability": "reasons about representations of whole numbers to 1000, partitioning numbers to use and record quantity values", "topic": "representing_numbers"},
    "MA1-CSQ-01": {"stage": 1, "focus_area": "Combining and separating quantities", "capability": "uses number bonds and the relationship between addition and subtraction to solve problems involving partitioning", "topic": "vertical_addition"},
    "MA1-FG-01": {"stage": 1, "focus_area": "Forming groups", "capability": "uses the structure of equal groups to solve multiplication problems, and shares or groups to solve division problems", "topic": "vertical_multiplication"},
    "MA1-GM-01": {"stage": 1, "focus_area": "Geometric measure", "capability": "represents and describes the positions of objects in familiar locations", "topic": "geometry_angles"},
    "MA1-GM-02": {"stage": 1, "focus_area": "Geometric measure", "capability": "measures, records, compares and estimates lengths and distances using uniform informal units, as well as metres and centimetres", "topic": "length"},
    "MA1-GM-03": {"stage": 1, "focus_area": "Geometric measure", "capability": "creates and recognises halves, quarters and eighths as part measures of a whole length", "topic": "fractions"},
    "MA1-2DS-01": {"stage": 1, "focus_area": "Two-dimensional (2D) spatial structure", "capability": "recognises, describes and represents shapes including quadrilaterals and other common polygons", "topic": "2d_shapes"},
    "MA1-2DS-02": {"stage": 1, "focus_area": "Two-dimensional (2D) spatial structure", "capability": "measures and compares areas using uniform informal units in rows and columns", "topic": "area"},
    "MA1-3DS-01": {"stage": 1, "focus_area": "Three-dimensional (3D) spatial structure", "capability": "recognises, describes and represents familiar three-dimensional objects", "topic": "3d_objects"},
    "MA1-3DS-02": {"stage": 1, "focus_area": "Three-dimensional (3D) spatial structure", "capability": "measures, records, compares and estimates internal volumes (capacities) and volumes using uniform informal units", "topic": "volume"},
    "MA1-NSM-01": {"stage": 1, "focus_area": "Non-spatial measure", "capability": "measures, records, compares and estimates the masses of objects using uniform informal units", "topic": "mass"},
    "MA1-NSM-02": {"stage": 1, "focus_area": "Non-spatial measure", "capability": "describes, compares and orders durations of events, and reads half- and quarter-hour time", "topic": "reading_time"},
    "MA1-DATA-01": {"stage": 1, "focus_area": "Data", "capability": "gathers and organises data, displays data in lists, tables and picture graphs", "topic": "data"},
    "MA1-DATA-02": {"stage": 1, "focus_area": "Data", "capability": "reasons about representations of data to describe and interpret the results", "topic": "data"},
    "MA1-CHAN-01": {"stage": 1, "focus_area": "Chance", "capability": "recognises and describes the element of chance in everyday events", "topic": "chance"},

    # Stage 2 (Years 3–4)
    "MA2-RN-01": {"stage": 2, "focus_area": "Representing numbers", "capability": "applies an understanding of place value and the role of zero to represent numbers to at least tens of thousands", "topic": "representing_numbers"},
    "MA2-RN-02": {"stage": 2, "focus_area": "Representing numbers", "capability": "represents and compares decimals up to 2 decimal places using place value", "topic": "decimals"},
    "MA2-AR-01": {"stage": 2, "focus_area": "Additive relations", "capability": "selects and uses mental and written strategies for addition and subtraction involving 2- and 3-digit numbers", "topic": "vertical_addition"},
    "MA2-AR-02": {"stage": 2, "focus_area": "Additive relations", "capability": "completes number sentences involving addition and subtraction by finding missing values", "topic": "algebra"},
    "MA2-MR-01": {"stage": 2, "focus_area": "Multiplicative relations", "capability": "represents and uses the structure of multiplicative relations to 10 × 10 to solve problems", "topic": "vertical_multiplication"},
    "MA2-MR-02": {"stage": 2, "focus_area": "Multiplicative relations", "capability": "completes number sentences involving multiplication and division by finding missing values", "topic": "long_division"},
    "MA2-PF-01": {"stage": 2, "focus_area": "Fractions", "capability": "represents and compares halves, quarters, thirds and fifths as lengths on a number line and their related fractions formed by halving (eighths, sixths and tenths)", "topic": "fractions"},
    "MA2-GM-01": {"stage": 2, "focus_area": "Geometric measure", "capability": "uses grid maps and directional language to locate positions and follow routes", "topic": "geometry_angles"},
    "MA2-GM-02": {"stage": 2, "focus_area": "Geometric measure", "capability": "measures and estimates lengths in metres, centimetres and millimetres", "topic": "length"},
    "MA2-GM-03": {"stage": 2, "focus_area": "Geometric measure", "capability": "identifies angles and classifies them by comparing to a right angle", "topic": "geometry_angles"},
    "MA2-2DS-01": {"stage": 2, "focus_area": "Two-dimensional (2D) spatial structure", "capability": "compares two-dimensional shapes and describes their features", "topic": "2d_shapes"},
    "MA2-2DS-02": {"stage": 2, "focus_area": "Two-dimensional (2D) spatial structure", "capability": "performs transformations by combining and splitting two-dimensional shapes", "topic": "2d_shapes"},
    "MA2-2DS-03": {"stage": 2, "focus_area": "Two-dimensional (2D) spatial structure", "capability": "estimates, measures and compares areas using square centimetres and square metres", "topic": "area"},
    "MA2-3DS-01": {"stage": 2, "focus_area": "Three-dimensional (3D) spatial structure", "capability": "makes and sketches models and nets of three-dimensional objects including prisms and pyramids", "topic": "3d_objects"},
    "MA2-3DS-02": {"stage": 2, "focus_area": "Three-dimensional (3D) spatial structure", "capability": "estimates, measures and compares capacities (internal volumes) using litres, millilitres and volumes using cubic centimetres", "topic": "volume"},
    "MA2-NSM-01": {"stage": 2, "focus_area": "Non-spatial measure", "capability": "estimates, measures and compares the masses of objects using kilograms and grams", "topic": "mass"},
    "MA2-NSM-02": {"stage": 2, "focus_area": "Non-spatial measure", "capability": "represents and interprets analog and digital time in hours, minutes and seconds", "topic": "reading_time"},
    "MA2-DATA-01": {"stage": 2, "focus_area": "Data", "capability": "collects discrete data and constructs graphs using a given scale", "topic": "data"},
    "MA2-DATA-02": {"stage": 2, "focus_area": "Data", "capability": "interprets data in tables, dot plots and column graphs", "topic": "data"},
    "MA2-CHAN-01": {"stage": 2, "focus_area": "Chance", "capability": "records and compares the results of chance experiments", "topic": "chance"},

    # Stage 3 (Years 5–6)
    "MA3-RN-01": {"stage": 3, "focus_area": "Representing numbers", "capability": "applies an understanding of place value and the role of zero to represent the properties of numbers", "topic": "representing_numbers"},
    "MA3-RN-02": {"stage": 3, "focus_area": "Representing numbers", "capability": "compares and orders decimals up to 3 decimal places", "topic": "decimals"},
    "MA3-RN-03": {"stage": 3, "focus_area": "Representing numbers", "capability": "determines percentages of quantities, and finds equivalent fractions and decimals for benchmark percentage values", "topic": "percentages"},
    "MA3-AR-01": {"stage": 3, "focus_area": "Additive relations", "capability": "selects and applies appropriate strategies to solve addition and subtraction problems", "topic": "vertical_addition"},
    "MA3-MR-01": {"stage": 3, "focus_area": "Multiplicative relations", "capability": "selects and applies appropriate strategies to solve multiplication and division problems", "topic": "vertical_multiplication"},
    "MA3-MR-02": {"stage": 3, "focus_area": "Multiplicative relations", "capability": "constructs and completes number sentences involving multiplicative relations, applying the order of operations to calculations", "topic": "order_of_operations"},
    "MA3-RQF-01": {"stage": 3, "focus_area": "Fractions", "capability": "compares and orders fractions with denominators of 2, 3, 4, 5, 6, 8 and 10", "topic": "fractions"},
    "MA3-RQF-02": {"stage": 3, "focus_area": "Fractions", "capability": "determines 1/2, 1/4, 1/5 and 1/10 of measures and quantities", "topic": "fractions"},
    "MA3-GM-01": {"stage": 3, "focus_area": "Geometric measure", "capability": "locates and describes points on a coordinate plane", "topic": "geometry_angles"},
    "MA3-GM-02": {"stage": 3, "focus_area": "Geometric measure", "capability": "selects and uses the appropriate unit and device to measure lengths and distances including perimeters", "topic": "length"},
    "MA3-GM-03": {"stage": 3, "focus_area": "Geometric measure", "capability": "measures and constructs angles, and identifies the relationships between angles on a straight line and angles at a point", "topic": "geometry_angles"},
    "MA3-2DS-01": {"stage": 3, "focus_area": "Two-dimensional (2D) spatial structure", "capability": "investigates and classifies two-dimensional shapes, including triangles and quadrilaterals based on their properties", "topic": "2d_shapes"},
    "MA3-2DS-02": {"stage": 3, "focus_area": "Two-dimensional (2D) spatial structure", "capability": "selects and uses the appropriate unit to calculate areas, including areas of rectangles", "topic": "area"},
    "MA3-2DS-03": {"stage": 3, "focus_area": "Two-dimensional (2D) spatial structure", "capability": "combines, splits and rearranges shapes to determine the area of parallelograms and triangles", "topic": "area"},
    "MA3-3DS-01": {"stage": 3, "focus_area": "Three-dimensional (3D) spatial structure", "capability": "visualises, sketches and constructs three-dimensional objects, including prisms and pyramids, making connections to two-dimensional representations", "topic": "3d_objects"},
    "MA3-3DS-02": {"stage": 3, "focus_area": "Three-dimensional (3D) spatial structure", "capability": "selects and uses the appropriate unit to estimate, measure and calculate volumes and capacities", "topic": "volume"},
    "MA3-NSM-01": {"stage": 3, "focus_area": "Non-spatial measure", "capability": "selects and uses the appropriate unit and device to measure the masses of objects", "topic": "mass"},
    "MA3-NSM-02": {"stage": 3, "focus_area": "Non-spatial measure", "capability": "measures and compares duration, using 12- and 24-hour time and am and pm notation", "topic": "reading_time"},
    "MA3-DATA-01": {"stage": 3, "focus_area": "Data", "capability": "constructs graphs using many-to-one scales", "topic": "data"},
    "MA3-DATA-02": {"stage": 3, "focus_area": "Data", "capability": "interprets data displays, including timelines and line graphs", "topic": "data"},
    "MA3-CHAN-01": {"stage": 3, "focus_area": "Chance", "capability": "conducts chance experiments and quantifies the probability", "topic": "chance"}
}

# Synchronize with CSV
_csv_outcomes = _load_csv_outcomes()
for k, v in _csv_outcomes.items():
    if k in OUTCOME_REGISTRY:
        OUTCOME_REGISTRY[k]["focus_area"] = v["focus_area"]
        OUTCOME_REGISTRY[k]["capability"] = v["capability"]
        OUTCOME_REGISTRY[k]["stage"] = v["stage"]
    else:
        topic = "representing_numbers"
        if "RWN" in k or "RN" in k:
            topic = "representing_numbers"
        elif "CSQ" in k or "AR" in k:
            topic = "vertical_addition"
        elif "FG" in k or "MR" in k:
            topic = "vertical_multiplication"
        elif "PF" in k or "RQF" in k:
            topic = "fractions"
        elif "GM" in k:
            topic = "geometry_angles" if "03" in k else "length"
        elif "2DS" in k:
            topic = "area" if ("02" in k or "03" in k) else "2d_shapes"
        elif "3DS" in k:
            topic = "volume" if "02" in k else "3d_objects"
        elif "NSM" in k:
            topic = "reading_time" if "02" in k else "mass"
        elif "DATA" in k:
            topic = "data"
        elif "CHAN" in k:
            topic = "chance"

        OUTCOME_REGISTRY[k] = {
            "stage": v["stage"],
            "focus_area": v["focus_area"],
            "capability": v["capability"],
            "topic": topic
        }


def _has_addition_carry(a: int, b: int) -> bool:
    """Whether column addition of a+b needs a carry in any place. xlop only
    reserves vertical space for the (phantom) carry row when this is true, so
    a set of side-by-side problems where some carry and some don't will not
    line up - callers use this to keep a whole topic's carry-ness consistent
    with its allow_carrying setting."""
    carry = 0
    any_carry = False
    while a > 0 or b > 0:
        total = (a % 10) + (b % 10) + carry
        carry = 1 if total >= 10 else 0
        any_carry = any_carry or bool(carry)
        a //= 10
        b //= 10
    return any_carry


def _has_subtraction_borrow(a: int, b: int) -> bool:
    """Whether column subtraction of a-b (a >= b) needs a borrow in any
    place - same rationale as _has_addition_carry, for allow_borrowing."""
    borrow = 0
    any_borrow = False
    while a > 0 or b > 0:
        da, db = (a % 10) - borrow, b % 10
        borrow = 1 if da < db else 0
        any_borrow = any_borrow or bool(borrow)
        a //= 10
        b //= 10
    return any_borrow


def _rand_sub_pair(a_lo: int, a_hi: int, b_lo: int):
    a = random.randint(a_lo, a_hi)
    b = random.randint(b_lo, a - 1)
    return a, b


def _regenerate_until(pair_fn, check_fn, want: bool, max_attempts: int = 200):
    """Calls pair_fn() -> (a, b) until check_fn(a, b) == want, or gives up
    after max_attempts and returns whatever was last generated."""
    a, b = pair_fn()
    for _ in range(max_attempts):
        if check_fn(a, b) == want:
            break
        a, b = pair_fn()
    return a, b


# ------------------------------------------------------------------------
# TikZ shape helpers (Geometry & Shape questions). Every helper folds in a
# random rotation/scale/dimension so two calls for the same shape kind still
# produce different coordinate values embedded in the LaTeX source - this is
# what keeps otherwise-identical "classify this triangle" style questions
# from rendering as byte-identical duplicates when a tier only has a
# handful of valid categories (see build_question_for_topic's dedup pass).
# ------------------------------------------------------------------------

def _tikz_regular_polygon(sides: int) -> str:
    rotate = random.uniform(0, 360 / sides)
    size = round(random.uniform(1.0, 1.3), 2)
    pts = []
    for i in range(sides):
        angle = math.radians(90 + rotate + i * 360 / sides)
        pts.append(f"({size * math.cos(angle):.3f},{size * math.sin(angle):.3f})")
    path = " -- ".join(pts) + " -- cycle"
    return (
        "\\begin{tikzpicture}[scale=1]\n"
        f"  \\draw[very thick, fill=gray!10] {path};\n"
        "\\end{tikzpicture}"
    )


def _tikz_triangle(kind: str) -> str:
    if kind == "Equilateral":
        s = round(random.uniform(1.6, 2.2), 2)
        pts = [(0, 0), (s, 0), (s / 2, s * math.sqrt(3) / 2)]
    elif kind == "Isosceles":
        w = round(random.uniform(0.8, 1.5), 2)
        h = round(random.uniform(1.5, 2.3), 2)
        pts = [(-w, 0), (w, 0), (0, h)]
    else:  # Scalene
        bx = round(random.uniform(1.8, 2.6), 2)
        apex_x = round(random.uniform(0.2, bx - 0.6), 2)
        apex_y = round(random.uniform(1.2, 2.1), 2)
        pts = [(0, 0), (bx, 0), (apex_x, apex_y)]
    rotate = round(random.uniform(0, 359), 1)
    path = " -- ".join(f"({x:.3f},{y:.3f})" for x, y in pts) + " -- cycle"
    return (
        f"\\begin{{tikzpicture}}[scale=0.9, rotate={rotate}]\n"
        f"  \\draw[very thick, fill=gray!10] {path};\n"
        "\\end{tikzpicture}"
    )


def _tikz_quadrilateral(kind: str) -> str:
    if kind == "Rhombus":
        a = round(random.uniform(1.0, 1.6), 2)
        b = round(random.uniform(0.7, 1.3), 2)
        pts = [(0, b), (a, 0), (0, -b), (-a, 0)]
    elif kind == "Trapezium":
        bottom_w = round(random.uniform(2.0, 2.8), 2)
        top_w = round(random.uniform(0.8, bottom_w - 0.8), 2)
        h = round(random.uniform(1.1, 1.7), 2)
        x_off = (bottom_w - top_w) / 2
        pts = [(0, 0), (bottom_w, 0), (bottom_w - x_off, h), (x_off, h)]
    else:  # Parallelogram
        w = round(random.uniform(1.8, 2.4), 2)
        h = round(random.uniform(1.0, 1.5), 2)
        skew = round(random.uniform(0.4, 0.9), 2)
        pts = [(0, 0), (w, 0), (w + skew, h), (skew, h)]
    rotate = round(random.uniform(0, 359), 1)
    path = " -- ".join(f"({x:.3f},{y:.3f})" for x, y in pts) + " -- cycle"
    return (
        f"\\begin{{tikzpicture}}[scale=0.9, rotate={rotate}]\n"
        f"  \\draw[very thick, fill=gray!10] {path};\n"
        "\\end{tikzpicture}"
    )


def _tikz_l_shape(l1: int, w1: int, l2: int, w2: int) -> str:
    sx = sy = 0.3
    L1, W1, L2, W2 = l1 * sx, w1 * sy, l2 * sx, w2 * sy
    return (
        "\\begin{tikzpicture}[scale=1]\n"
        "  \\draw[very thick, fill=gray!10]\n"
        f"    (0,0) -- ({L1:.2f},0) -- ({L1:.2f},{W1:.2f}) -- ({L2:.2f},{W1:.2f})"
        f" -- ({L2:.2f},{W1 + W2:.2f}) -- (0,{W1 + W2:.2f}) -- cycle;\n"
        f"  \\node at ({L1 / 2:.2f},{-0.35:.2f}) {{\\scriptsize {l1} cm}};\n"
        f"  \\node[rotate=90] at ({-0.35:.2f},{W1 / 2:.2f}) {{\\scriptsize {w1} cm}};\n"
        f"  \\node at ({L2 / 2:.2f},{W1 + W2 + 0.35:.2f}) {{\\scriptsize {l2} cm}};\n"
        f"  \\node[rotate=90] at ({L2 + 0.35:.2f},{W1 + W2 / 2:.2f}) {{\\scriptsize {w2} cm}};\n"
        "\\end{tikzpicture}"
    )


def _tikz_cuboid(w_disp: float, h_disp: float, label_w=None, label_h=None, label_d=None) -> str:
    dx, dy = round(random.uniform(0.4, 0.6), 2), round(random.uniform(0.25, 0.4), 2)
    labels = ""
    if label_w is not None:
        labels += f"  \\node at ({w_disp / 2:.2f},{-0.3:.2f}) {{\\scriptsize {label_w}}};\n"
    if label_h is not None:
        labels += f"  \\node[rotate=90] at ({-0.3:.2f},{h_disp / 2:.2f}) {{\\scriptsize {label_h}}};\n"
    if label_d is not None:
        labels += f"  \\node at ({w_disp + dx / 2:.2f},{h_disp + dy + 0.25:.2f}) {{\\scriptsize {label_d}}};\n"
    return (
        "\\begin{tikzpicture}[scale=0.9, line join=round]\n"
        f"  \\draw[dashed] ({dx:.2f},{dy:.2f}) -- ({w_disp + dx:.2f},{dy:.2f}) -- "
        f"({w_disp + dx:.2f},{h_disp + dy:.2f}) -- ({dx:.2f},{h_disp + dy:.2f}) -- cycle;\n"
        f"  \\draw[dashed] (0,0) -- ({dx:.2f},{dy:.2f});\n"
        f"  \\draw ({w_disp:.2f},0) -- ({w_disp + dx:.2f},{dy:.2f});\n"
        f"  \\draw (0,{h_disp:.2f}) -- ({dx:.2f},{h_disp + dy:.2f});\n"
        f"  \\draw ({w_disp:.2f},{h_disp:.2f}) -- ({w_disp + dx:.2f},{h_disp + dy:.2f});\n"
        f"  \\draw[very thick, fill=gray!10] (0,0) -- ({w_disp:.2f},0) -- "
        f"({w_disp:.2f},{h_disp:.2f}) -- (0,{h_disp:.2f}) -- cycle;\n"
        f"{labels}"
        "\\end{tikzpicture}"
    )


def _tikz_pyramid() -> str:
    base_w = round(random.uniform(1.8, 2.4), 2)
    height = round(random.uniform(1.9, 2.5), 2)
    back_x = round(base_w * random.uniform(0.55, 0.7), 2)
    back_y = round(random.uniform(0.3, 0.5), 2)
    apex_x = round(base_w * random.uniform(0.25, 0.4), 2)
    return (
        "\\begin{tikzpicture}[scale=0.9]\n"
        f"  \\draw[very thick, fill=gray!10] (0,0) -- ({base_w:.2f},0) -- ({back_x:.2f},{back_y:.2f}) -- cycle;\n"
        f"  \\draw[very thick] (0,0) -- ({apex_x:.2f},{height:.2f});\n"
        f"  \\draw[very thick] ({base_w:.2f},0) -- ({apex_x:.2f},{height:.2f});\n"
        f"  \\draw[very thick, dashed] ({back_x:.2f},{back_y:.2f}) -- ({apex_x:.2f},{height:.2f});\n"
        "\\end{tikzpicture}"
    )


# Shape/object pools for 2d_shapes and 3d_objects, keyed by difficulty tier.
# Each entry's last element is a tuple of lowercase aliases that a config's
# `shapes` / `objects_3d` option can match against - see _select_shape_entry.
EASY_2D_SHAPES = [
    ("triangle", 3, ("triangle",)),
    ("quadrilateral", 4, ("quadrilateral", "square", "rectangle")),
    ("pentagon", 5, ("pentagon",)),
    ("hexagon", 6, ("hexagon",)),
    ("heptagon", 7, ("heptagon",)),
    ("octagon", 8, ("octagon",)),
]
MEDIUM_2D_QUADS = [
    ("Parallelogram", ("parallelogram",)),
    ("Rhombus", ("rhombus",)),
    ("Trapezium", ("trapezium", "trapezoid")),
]
HARD_2D_TRIANGLES = [
    ("Equilateral", ("equilateral",)),
    ("Isosceles", ("isosceles",)),
    ("Scalene", ("scalene",)),
]
OBJ_3D_POOL = [
    ("Cube", 6, "square", ("cube",)),
    ("Rectangular Prism", 6, "rectangular", ("cuboid", "rectangular prism", "prism", "rectangularprism")),
    ("Triangular Pyramid", 4, "triangular", ("pyramid", "triangular pyramid", "tetrahedron")),
]


def _draw_from_bag(bag: list, pool: List[tuple], requested: Optional[List[str]] = None) -> tuple:
    """Pops a random entry from `bag` (a per-QuestionBank, per-tier list the
    caller keeps across calls), refilling and reshuffling it from `pool`
    whenever it runs dry. This samples *without* replacement within each lap
    through the pool - e.g. a 3-item pool won't repeat the same category
    twice before the other two have each appeared once, which plain
    random.choice() each time can easily do (visually distinct TikZ
    coordinates still make each draw's rendered prompt_tex unique even on a
    later lap, but repeating the same shape/object back-to-back is still a
    meaningful duplicate from the learner's point of view).

    When `requested` is given, entries are restricted to those whose alias
    list (pool[i][-1]) intersects it case-insensitively; an empty/no match
    falls back to the full pool rather than erroring - e.g. a 3d_objects
    config asking for a "cylinder" (not yet implemented) still gets a valid
    question. The filtered pool is recomputed each refill so a mid-run
    config change would be respected, though in practice `requested` is
    fixed for the life of one QuestionBank."""
    if not bag:
        candidates = pool
        if requested:
            wanted = {r.strip().lower() for r in requested if r and r.strip()}
            filtered = [entry for entry in pool if wanted & set(entry[-1])]
            if filtered:
                candidates = filtered
        bag.extend(candidates)
        random.shuffle(bag)
    return bag.pop()


# ------------------------------------------------------------------------
# Calendar grid helper (Measurement & Time - date duration questions). Renders
# real month(s) as a LaTeX table so the learner reads the day-count off the
# grid themselves, rather than being handed the duration directly.
# ------------------------------------------------------------------------

def _month_calendar_tex(year: int, month: int, marks: Dict[int, str]) -> str:
    cal = calendar.Calendar(firstweekday=0)
    weeks = cal.monthdayscalendar(year, month)
    rows = []
    for week in weeks:
        cells = []
        for day in week:
            if day == 0:
                cells.append("")
            elif marks.get(day) == "start":
                cells.append(f"\\fbox{{\\textbf{{{day}}}}}")
            elif marks.get(day) == "end":
                cells.append(f"\\underline{{\\textbf{{{day}}}}}")
            else:
                cells.append(str(day))
        rows.append(" & ".join(cells) + " \\\\\n\\hline")
    body = "\n".join(rows)
    return (
        f"\\textbf{{{calendar.month_name[month]} {year}}}\\\\[0.2em]\n"
        "\\begin{tabular}{|c|c|c|c|c|c|c|}\n\\hline\n"
        "Mon & Tue & Wed & Thu & Fri & Sat & Sun \\\\\n\\hline\n"
        f"{body}\n"
        "\\end{tabular}"
    )


def _calendar_block_for_range(start_date: datetime, end_date: datetime) -> str:
    months = []
    cur = start_date.replace(day=1)
    end_marker = end_date.replace(day=1)
    while cur <= end_marker:
        months.append((cur.year, cur.month))
        cur = cur.replace(year=cur.year + 1, month=1) if cur.month == 12 else cur.replace(month=cur.month + 1)

    blocks = []
    for y, m in months:
        marks: Dict[int, str] = {}
        if (y, m) == (start_date.year, start_date.month):
            marks[start_date.day] = "start"
        if (y, m) == (end_date.year, end_date.month):
            marks[end_date.day] = "start" if marks.get(end_date.day) == "start" else "end"
        blocks.append(_month_calendar_tex(y, m, marks))
    return "\\\\[0.6em]\n".join(blocks)


class QuestionBank:
    """Generates dynamic mathematics questions aligned to NESA Syllabus outcomes across EASY, MEDIUM, HARD, and GENIUS difficulties."""

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
        self._seen_prompts: Dict[str, set] = {}
        self._category_bags: Dict[str, list] = {}

    def _draw(self, bag_key: str, pool: List[tuple], requested: Optional[List[str]] = None) -> tuple:
        """Convenience wrapper around _draw_from_bag that keeps this
        instance's per-bag_key state (see _draw_from_bag's docstring)."""
        return _draw_from_bag(self._category_bags.setdefault(bag_key, []), pool, requested)

    def _meta(self, outcome_code: str) -> Dict[str, Any]:
        return OUTCOME_REGISTRY.get(outcome_code, {
            "stage": 2, "focus_area": "Mathematics", "capability": ""
        })

    def _norm_diff(self, difficulty: str) -> str:
        return str(difficulty).strip().lower()

    # 1. Representing Whole Numbers
    def generate_representing_numbers(
        self,
        difficulty: str = "medium",
        fixed_questions: Optional[List[Dict[str, Any]]] = None,
        index: int = 0
    ) -> Question:
        diff = self._norm_diff(difficulty)
        if diff == "easy":
            code = "MA1-RWN-01"
        elif diff == "hard":
            code = "MA3-RN-01"
        elif diff == "genius":
            code = "MA3-RN-03"
        else:
            code = "MA2-RN-01"

        meta = self._meta(code)

        if fixed_questions and index < len(fixed_questions):
            fq = fixed_questions[index]
            if "prompt" in fq and "solution" in fq:
                return Question(
                    section=meta["focus_area"], topic="representing_numbers", outcome_code=code,
                    focus_area=meta["focus_area"], capability=meta["capability"],
                    prompt_tex=fq["prompt"], solution_tex=fq["solution"], layout_hint="list"
                )

        if diff == "easy":
            num = random.randint(12, 98)
            prompt = f"Write the place value decomposition of $\\mathbf{{{num}}}$ (Tens and Ones):"
            solution = f"$\\mathbf{{{num}}} = {num//10} \\text{{ tens}} + {num%10} \\text{{ ones}}$"
            answer_value = f"{num//10} tens + {num%10} ones"
        elif diff == "genius":
            pct = random.choice([15, 25, 35, 45, 65, 75])
            amount = random.choice([200, 320, 480, 640, 800])
            val = (amount * pct) // 100
            rem = amount - val
            g = math.gcd(rem, amount)
            prompt = f"Determine $\\mathbf{{{pct}\\%}}$ of $\\mathbf{{\\${amount}}}$, and express the remaining amount as a fraction of the total in simplest form:"
            solution = f"${pct}\\% \\text{{ of }} \\${amount} = \\mathbf{{\\${val}}}$. Remaining amount is $\\${rem} = \\mathbf{{\\dfrac{{{rem//g}}}{{{amount//g}}}}}$ of the total."
            answer_value = str(val)
        elif diff == "hard":
            num = random.randint(100000, 999999)
            prompt = f"Round $\\mathbf{{{num:,}}}$ to the nearest thousand:"
            rounded = round(num, -3)
            solution = f"$\\mathbf{{{rounded:,}}}$"
            answer_value = str(rounded)
        else: # medium
            num = random.randint(1000, 9999)
            prompt = f"State the value of the digit in the hundreds place for $\\mathbf{{{num:,}}}$:"
            val = (num // 100) % 10
            solution = f"Digit is ${val}$, representing $\\mathbf{{{val * 100}}}$"
            answer_value = str(val * 100)

        return Question(
            section=meta["focus_area"], topic="representing_numbers", outcome_code=code,
            focus_area=meta["focus_area"], capability=meta["capability"], stage=meta["stage"],
            prompt_tex=prompt, solution_tex=solution, answer_value=answer_value, layout_hint="list"
        )

    # 2. Vertical Addition
    def generate_vertical_addition(
        self,
        digits: int = 3,
        allow_carrying: bool = True,
        difficulty: str = "medium",
        fixed_questions: Optional[List[Dict[str, Any]]] = None,
        index: int = 0
    ) -> Question:
        diff = self._norm_diff(difficulty)
        if diff == "easy":
            code = "MA1-CSQ-01"
        elif diff in ["hard", "genius"]:
            code = "MA3-AR-01"
        else:
            code = "MA2-AR-01"

        meta = self._meta(code)

        if fixed_questions and index < len(fixed_questions):
            fq = fixed_questions[index]
            if "prompt" in fq and "solution" in fq:
                return Question(
                    section=meta["focus_area"], topic="vertical_addition", outcome_code=code,
                    focus_area=meta["focus_area"], capability=meta["capability"], q_type="xlop",
                    prompt_tex=fq["prompt"], solution_tex=fq["solution"], layout_hint="grid_3col"
                )
            a = fq.get("top", 123)
            b = fq.get("bottom", 456)
            ans = a + b
            prompt = f"\\opadd[carrystyle=\\phantom,resultstyle=\\phantom]{{{a}}}{{{b}}}"
            solution = f"${a} + {b} = \\mathbf{{{ans}}}$"
            return Question(
                section=meta["focus_area"], topic="vertical_addition", outcome_code=code,
                focus_area=meta["focus_area"], capability=meta["capability"], stage=meta["stage"],
                q_type="xlop", prompt_tex=prompt, solution_tex=solution, answer_value=str(ans), layout_hint="grid_3col"
            )

        if diff == "easy":
            a_digits = [random.randint(1, 4) for _ in range(2)]
            b_digits = [random.randint(1, 4) for _ in range(2)]
            a = int("".join(map(str, a_digits)))
            b = int("".join(map(str, b_digits)))
            ans = a + b
            prompt = f"\\opadd[carrystyle=\\phantom,resultstyle=\\phantom]{{{a}}}{{{b}}}"
            solution = f"${a} + {b} = \\mathbf{{{ans}}}$"
        elif diff == "genius":
            a = random.randint(10000, 89999)
            b = random.randint(10000, 89999)
            c = random.randint(5000, 49999)
            ans = a + b + c
            prompt = (
                f"$\\begin{{array}}[t]{{r@{{\\quad}}r}}\n"
                f"  & {a:,} \\\\\n"
                f"  & {b:,} \\\\\n"
                f"+ & {c:,} \\\\\n"
                f"\\hline\n"
                f"\\end{{array}}$"
            )
            solution = f"${a:,} + {b:,} + {c:,} = \\mathbf{{{ans:,}}}$"
            return Question(
                section=meta["focus_area"], topic="vertical_addition", outcome_code=code,
                focus_area=meta["focus_area"], capability=meta["capability"], stage=meta["stage"],
                q_type="math", prompt_tex=prompt, solution_tex=solution, answer_value=str(ans), layout_hint="grid_3col"
            )
        elif diff == "hard":
            a, b = _regenerate_until(
                lambda: (random.randint(1000, 9999), random.randint(1000, 9999)),
                _has_addition_carry, allow_carrying
            )
            ans = a + b
            prompt = f"\\opadd[carrystyle=\\phantom,resultstyle=\\phantom]{{{a}}}{{{b}}}"
            solution = f"${a} + {b} = \\mathbf{{{ans}}}$"
        else: # medium
            a, b = _regenerate_until(
                lambda: (random.randint(100, 999), random.randint(100, 999)),
                _has_addition_carry, allow_carrying
            )
            ans = a + b
            prompt = f"\\opadd[carrystyle=\\phantom,resultstyle=\\phantom]{{{a}}}{{{b}}}"
            solution = f"${a} + {b} = \\mathbf{{{ans}}}$"

        return Question(
            section=meta["focus_area"], topic="vertical_addition", outcome_code=code,
            focus_area=meta["focus_area"], capability=meta["capability"], stage=meta["stage"],
            q_type="xlop", prompt_tex=prompt, solution_tex=solution, answer_value=str(ans), layout_hint="grid_3col"
        )

    # 3. Vertical Subtraction
    def generate_vertical_subtraction(
        self,
        digits: int = 3,
        allow_borrowing: bool = True,
        difficulty: str = "medium",
        fixed_questions: Optional[List[Dict[str, Any]]] = None,
        index: int = 0
    ) -> Question:
        diff = self._norm_diff(difficulty)
        if diff == "easy":
            code = "MA1-CSQ-01"
        elif diff in ["hard", "genius"]:
            code = "MA3-AR-01"
        else:
            code = "MA2-AR-01"

        meta = self._meta(code)

        if fixed_questions and index < len(fixed_questions):
            fq = fixed_questions[index]
            if "prompt" in fq and "solution" in fq:
                return Question(
                    section=meta["focus_area"], topic="vertical_subtraction", outcome_code=code,
                    focus_area=meta["focus_area"], capability=meta["capability"], q_type="xlop",
                    prompt_tex=fq["prompt"], solution_tex=fq["solution"], layout_hint="grid_3col"
                )
            a = fq.get("top", 500)
            b = fq.get("bottom", 234)
        else:
            if diff == "easy":
                a_digits, b_digits = [], []
                for _ in range(2):
                    d1 = random.randint(3, 9)
                    d2 = random.randint(0, d1)
                    a_digits.append(d1)
                    b_digits.append(d2)
                a = int("".join(map(str, a_digits)))
                b = int("".join(map(str, b_digits)))
            elif diff == "genius":
                # Subtraction across zeros e.g. 100,000 - 34,782
                a = random.choice([50000, 100000, 70000, 90000])
                b = random.randint(12345, a - 1000)
            elif diff == "hard":
                a, b = _regenerate_until(
                    lambda: _rand_sub_pair(1000, 9999, 100),
                    _has_subtraction_borrow, allow_borrowing
                )
            else: # medium
                a, b = _regenerate_until(
                    lambda: _rand_sub_pair(100, 999, 10),
                    _has_subtraction_borrow, allow_borrowing
                )

        ans = a - b
        prompt = f"\\opsub[carrystyle=\\phantom,resultstyle=\\phantom]{{{a}}}{{{b}}}"
        solution = f"${a:,} - {b:,} = \\mathbf{{{ans:,}}}$"
        return Question(
            section=meta["focus_area"], topic="vertical_subtraction", outcome_code=code,
            focus_area=meta["focus_area"], capability=meta["capability"], stage=meta["stage"],
            q_type="xlop", prompt_tex=prompt, solution_tex=solution, answer_value=str(ans), layout_hint="grid_3col"
        )

    # 4. Vertical Multiplication
    def generate_vertical_multiplication(
        self,
        digits_top: int = 2,
        digits_bottom: int = 1,
        difficulty: str = "medium",
        multiplier: Optional[Union[int, List[int]]] = None,
        times_table: Optional[Union[int, List[int]]] = None,
        fixed_questions: Optional[List[Dict[str, Any]]] = None,
        index: int = 0
    ) -> Question:
        diff = self._norm_diff(difficulty)
        if diff == "easy":
            code = "MA1-FG-01"
        elif diff in ["hard", "genius"]:
            code = "MA3-MR-01"
        else:
            code = "MA2-MR-01"

        meta = self._meta(code)

        if fixed_questions and index < len(fixed_questions):
            fq = fixed_questions[index]
            if "prompt" in fq and "solution" in fq:
                return Question(
                    section=meta["focus_area"], topic="vertical_multiplication", outcome_code=code,
                    focus_area=meta["focus_area"], capability=meta["capability"], q_type="xlop",
                    prompt_tex=fq["prompt"], solution_tex=fq["solution"], layout_hint="grid_3col"
                )
            a = fq.get("top", 45)
            b = fq.get("bottom", 6)
        else:
            mult_val = multiplier if multiplier is not None else times_table
            if mult_val is not None:
                b = random.choice(mult_val) if isinstance(mult_val, list) else int(mult_val)
                a = random.randint(10, 49) if diff == "easy" else (random.randint(100, 999) if diff in ["hard", "genius"] else random.randint(11, 99))
            else:
                if diff == "easy":
                    b = random.randint(2, 5)
                    a = random.randint(11, 49)
                elif diff == "genius":
                    a = random.randint(1000, 4999)
                    b = random.randint(12, 49)
                elif diff == "hard":
                    a = random.randint(100, 499)
                    b = random.randint(12, 35)
                else:
                    a = random.randint(12, 89)
                    b = random.randint(3, 9)

        ans = a * b
        prompt = f"\\opmul[carrystyle=\\phantom,resultstyle=\\phantom]{{{a}}}{{{b}}}"
        solution = f"${a:,} \\times {b:,} = \\mathbf{{{ans:,}}}$"
        return Question(
            section=meta["focus_area"], topic="vertical_multiplication", outcome_code=code,
            focus_area=meta["focus_area"], capability=meta["capability"], stage=meta["stage"],
            q_type="xlop", prompt_tex=prompt, solution_tex=solution, answer_value=str(ans), layout_hint="grid_3col"
        )

    # 5. Long Division
    def generate_long_division(
        self,
        digits_dividend: int = 3,
        digits_divisor: int = 1,
        allow_remainder: bool = False,
        difficulty: str = "medium",
        divisor: Optional[Union[int, List[int]]] = None,
        times_table: Optional[Union[int, List[int]]] = None,
        fixed_questions: Optional[List[Dict[str, Any]]] = None,
        index: int = 0
    ) -> Question:
        diff = self._norm_diff(difficulty)
        if diff == "easy":
            code = "MA1-FG-01"
        elif diff in ["hard", "genius"]:
            code = "MA3-MR-01"
        else:
            code = "MA2-MR-02"

        meta = self._meta(code)

        if fixed_questions and index < len(fixed_questions):
            fq = fixed_questions[index]
            if "prompt" in fq and "solution" in fq:
                return Question(
                    section=meta["focus_area"], topic="long_division", outcome_code=code,
                    focus_area=meta["focus_area"], capability=meta["capability"], q_type="math",
                    prompt_tex=fq["prompt"], solution_tex=fq["solution"], layout_hint="grid_3col"
                )
            dividend = fq.get("dividend", 144)
            divisor_val = fq.get("divisor", 12)
        else:
            div_spec = divisor if divisor is not None else times_table
            if div_spec is not None:
                divisor_val = random.choice(div_spec) if isinstance(div_spec, list) else int(div_spec)
                quotient = random.randint(3, 12) if diff == "easy" else (random.randint(25, 99) if diff in ["hard", "genius"] else random.randint(5, 30))
                rem = random.randint(1, divisor_val - 1) if (allow_remainder and divisor_val > 1) else 0
                dividend = divisor_val * quotient + rem
            else:
                if diff == "easy":
                    divisor_val = random.randint(2, 5)
                    quotient = random.randint(5, 12)
                    dividend = divisor_val * quotient
                elif diff == "genius":
                    divisor_val = random.randint(12, 45)
                    quotient = random.randint(100, 350)
                    rem = random.randint(1, divisor_val - 1) if allow_remainder else 0
                    dividend = divisor_val * quotient + rem
                elif diff == "hard":
                    divisor_val = random.randint(6, 12)
                    quotient = random.randint(15, 85)
                    rem = random.randint(1, divisor_val - 1) if allow_remainder else 0
                    dividend = divisor_val * quotient + rem
                else: # medium
                    divisor_val = random.randint(3, 9)
                    quotient = random.randint(10, 50)
                    dividend = divisor_val * quotient

        quotient = dividend // divisor_val
        remainder = dividend % divisor_val

        prompt = f"$\\begin{{array}}[t]{{r@{{\\quad}}r}} & {dividend:,} \\\\ \\div & {divisor_val} \\\\ \\hline \\end{{array}}$"
        solution = f"${dividend:,} \\div {divisor_val} = \\mathbf{{{quotient:,} \\text{{ r }} {remainder}}}$" if remainder > 0 else f"${dividend:,} \\div {divisor_val} = \\mathbf{{{quotient:,}}}$"
        answer_value = f"{quotient} r {remainder}" if remainder > 0 else str(quotient)

        return Question(
            section=meta["focus_area"], topic="long_division", outcome_code=code,
            focus_area=meta["focus_area"], capability=meta["capability"], stage=meta["stage"],
            q_type="math", prompt_tex=prompt, solution_tex=solution, answer_value=answer_value, layout_hint="grid_3col"
        )

    # 6. Sequences & Patterns
    def generate_sequence(
        self,
        step_range: List[int] = [2, 10],
        pattern_type: Optional[str] = None,
        difficulty: str = "medium",
        fixed_questions: Optional[List[Dict[str, Any]]] = None,
        index: int = 0
    ) -> Question:
        diff = self._norm_diff(difficulty)
        if diff == "easy":
            code = "MA1-RWN-01"
        elif diff in ["hard", "genius"]:
            code = "MA3-MR-02"
        else:
            code = "MA2-MR-01"

        meta = self._meta(code)

        if fixed_questions and index < len(fixed_questions):
            fq = fixed_questions[index]
            if "prompt" in fq and "solution" in fq:
                return Question(
                    section=meta["focus_area"], topic="sequences", outcome_code=code,
                    focus_area=meta["focus_area"], capability=meta["capability"],
                    prompt_tex=fq["prompt"], solution_tex=fq["solution"], layout_hint="list"
                )

        # Per-tier fallback preserves each tier's historical default exactly
        # when pattern_type isn't set in config (hard defaulted to geometric
        # before pattern_type was wired up at all; everything else to
        # arithmetic). Genius is a fixed two-step extension tier, like
        # fractions' genius tier - not gated by pattern_type.
        requested_pattern = (pattern_type or "").strip().lower()
        valid_patterns = ("arithmetic", "geometric")
        default_pattern = "geometric" if diff == "hard" else "arithmetic"
        pattern = requested_pattern if requested_pattern in valid_patterns else default_pattern

        if diff == "genius":
            # Alternating step rule e.g. +3, x2, +3, x2
            start = random.randint(2, 6)
            add_val = random.randint(2, 6)
            mult_val = random.choice([2, 3])
            seq = [start]
            for i in range(5):
                if i % 2 == 0:
                    seq.append(seq[-1] + add_val)
                else:
                    seq.append(seq[-1] * mult_val)
            blank_idx = random.choice([2, 3, 4])
            ans = seq[blank_idx]
            seq_display = [str(x) if i != blank_idx else "\\underline{\\hspace{1.5cm}}" for i, x in enumerate(seq)]
            prompt = f"Find the missing number in the two-step pattern:\\\\[0.5em] ${', '.join(seq_display)}$"
            solution = f"Missing number is $\\mathbf{{{ans}}}$ (Rule: alternate $+{add_val}$ and $\\times {mult_val}$)"
        elif diff == "easy":
            if pattern == "geometric":
                ratio = random.choice([2, 3])
                start = random.randint(1, 4)
                seq = [start * (ratio ** i) for i in range(5)]
                blank_idx = 2
                rule = f"multiply by ${ratio}$"
            else:
                step = random.randint(2, 5)
                start = random.randint(1, 10)
                seq = [start + i * step for i in range(6)]
                blank_idx = 3
                rule = f"add ${step}$"
            ans = seq[blank_idx]
            seq_display = [str(x) if i != blank_idx else "\\underline{\\hspace{1.5cm}}" for i, x in enumerate(seq)]
            label = "geometric pattern" if pattern == "geometric" else "sequence"
            prompt = f"Find the missing number in the {label}:\\\\[0.5em] ${', '.join(seq_display)}$"
            solution = f"Missing number is $\\mathbf{{{ans}}}$ (Rule: {rule})"
        elif diff == "hard":
            if pattern == "arithmetic":
                step = random.randint(10, 50)
                start = random.randint(5, 40)
                seq = [start + i * step for i in range(6)]
                blank_idx = random.choice([2, 3, 4])
                rule = f"add ${step}$"
            else:
                ratio = random.choice([2, 3, 4])
                start = random.randint(1, 6)
                seq = [start * (ratio ** i) for i in range(5)]
                blank_idx = random.choice([1, 2, 3])
                rule = f"multiply by ${ratio}$"
            ans = seq[blank_idx]
            seq_display = [str(x) if i != blank_idx else "\\underline{\\hspace{1.5cm}}" for i, x in enumerate(seq)]
            label = "sequence" if pattern == "arithmetic" else "geometric pattern"
            prompt = f"Find the missing number in the {label}:\\\\[0.5em] ${', '.join(seq_display)}$"
            solution = f"Missing number is $\\mathbf{{{ans}}}$ (Rule: {rule})"
        else:  # medium
            if pattern == "geometric":
                ratio = random.choice([2, 3])
                start = random.randint(1, 5)
                seq = [start * (ratio ** i) for i in range(5)]
                blank_idx = random.choice([1, 2, 3])
                rule = f"multiply by ${ratio}$"
            else:
                step = random.randint(step_range[0], step_range[1])
                start = random.randint(5, 25)
                seq = [start + i * step for i in range(6)]
                blank_idx = random.choice([2, 3, 4])
                rule = f"add ${step}$"
            ans = seq[blank_idx]
            seq_display = [str(x) if i != blank_idx else "\\underline{\\hspace{1.5cm}}" for i, x in enumerate(seq)]
            label = "geometric pattern" if pattern == "geometric" else "sequence"
            prompt = f"Find the missing number in the {label}:\\\\[0.5em] ${', '.join(seq_display)}$"
            solution = f"Missing number is $\\mathbf{{{ans}}}$ (Rule: {rule})"

        return Question(
            section=meta["focus_area"], topic="sequences", outcome_code=code,
            focus_area=meta["focus_area"], capability=meta["capability"], stage=meta["stage"],
            prompt_tex=prompt, solution_tex=solution, answer_value=str(ans), layout_hint="list"
        )

    # 7. Fractions
    def generate_fractions(
        self,
        op_type: Optional[str] = None,
        difficulty: str = "medium",
        fixed_questions: Optional[List[Dict[str, Any]]] = None,
        index: int = 0
    ) -> Question:
        diff = self._norm_diff(difficulty)
        if diff == "easy":
            code = "MA2-PF-01"
        elif diff in ["hard", "genius"]:
            code = "MA3-RQF-01"
        else:
            code = "MA2-PF-01"

        meta = self._meta(code)

        if fixed_questions and index < len(fixed_questions):
            fq = fixed_questions[index]
            if "prompt" in fq and "solution" in fq:
                return Question(
                    section=meta["focus_area"], topic="fractions", outcome_code=code,
                    focus_area=meta["focus_area"], capability=meta["capability"],
                    prompt_tex=fq["prompt"], solution_tex=fq["solution"], layout_hint="list"
                )

        # Per-tier fallback preserves each tier's historical default exactly
        # when op_type isn't set in config (hard defaulted to multiplication
        # before op_type was wired up at all; everything else to addition).
        requested_op = (op_type or "").strip().lower()
        valid_ops = ("addition", "subtraction", "multiplication")
        default_op = "multiplication" if diff == "hard" else "addition"
        op = requested_op if requested_op in valid_ops else default_op

        if diff == "easy":
            denom = random.choice([4, 5, 6, 8, 10])
            if op == "multiplication":
                num1, num2 = random.randint(1, denom - 1), random.randint(1, denom - 1)
                ans_n, ans_d = num1 * num2, denom * denom
                g = math.gcd(ans_n, ans_d)
                prompt = f"Multiply: $\\dfrac{{{num1}}}{{{denom}}} \\times \\dfrac{{{num2}}}{{{denom}}} = \\underline{{\\hspace{{2.5cm}}}}$"
                solution = f"$\\dfrac{{{num1} \\times {num2}}}{{{denom} \\times {denom}}} = \\mathbf{{\\dfrac{{{ans_n//g}}}{{{ans_d//g}}}}}$"
                answer_value = f"{ans_n//g}/{ans_d//g}"
            elif op == "subtraction":
                num1 = random.randint(2, denom - 1)
                num2 = random.randint(1, num1 - 1)
                ans_num = num1 - num2
                g = math.gcd(ans_num, denom)
                prompt = f"Calculate: $\\dfrac{{{num1}}}{{{denom}}} - \\dfrac{{{num2}}}{{{denom}}} = \\underline{{\\hspace{{2.5cm}}}}$"
                solution = f"$\\dfrac{{{num1}}}{{{denom}}} - \\dfrac{{{num2}}}{{{denom}}} = \\mathbf{{\\dfrac{{{ans_num//g}}}{{{denom//g}}}}}$"
                answer_value = f"{ans_num//g}/{denom//g}"
            else:  # addition
                num1 = random.randint(1, denom - 2)
                num2 = random.randint(1, denom - num1)
                ans_num = num1 + num2
                g = math.gcd(ans_num, denom)
                prompt = f"Calculate: $\\dfrac{{{num1}}}{{{denom}}} + \\dfrac{{{num2}}}{{{denom}}} = \\underline{{\\hspace{{2.5cm}}}}$"
                solution = f"$\\dfrac{{{num1}}}{{{denom}}} + \\dfrac{{{num2}}}{{{denom}}} = \\mathbf{{\\dfrac{{{ans_num//g}}}{{{denom//g}}}}}$"
                answer_value = f"{ans_num//g}/{denom//g}"
        elif diff == "genius":
            # Mixed numbers operations e.g. 2 (1/2) + 1 (3/4) - a fixed extension
            # tier (not gated by op_type, like the other topics' genius tiers).
            w1, w2 = random.randint(1, 5), random.randint(1, 5)
            d1, d2 = random.choice([(2, 4), (3, 6), (2, 6), (3, 4), (2, 8), (4, 8), (3, 9)])
            n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)
            tot_num = (w1 * d1 + n1) * d2 + (w2 * d2 + n2) * d1
            tot_den = d1 * d2
            g = math.gcd(tot_num, tot_den)
            fin_num, fin_den = tot_num // g, tot_den // g
            w_ans, r_num = divmod(fin_num, fin_den)
            prompt = f"Calculate and simplify: ${w1}\\dfrac{{{n1}}}{{{d1}}} + {w2}\\dfrac{{{n2}}}{{{d2}}} = \\underline{{\\hspace{{2.5cm}}}}$"
            solution = f"${w1}\\dfrac{{{n1}}}{{{d1}}} + {w2}\\dfrac{{{n2}}}{{{d2}}} = \\mathbf{{{w_ans}\\dfrac{{{r_num}}}{{{fin_den}}}}}$" if r_num > 0 else f"$\\mathbf{{{w_ans}}}$"
            answer_value = f"{w_ans} {r_num}/{fin_den}" if r_num > 0 else str(w_ans)
        elif diff == "hard":
            d1, d2 = random.choice([(3, 4), (2, 5), (3, 5), (4, 5)])
            if op == "multiplication":
                n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)
                ans_n, ans_d = n1 * n2, d1 * d2
                g = math.gcd(ans_n, ans_d)
                prompt = f"Multiply the fractions: $\\dfrac{{{n1}}}{{{d1}}} \\times \\dfrac{{{n2}}}{{{d2}}} = \\underline{{\\hspace{{2.5cm}}}}$"
                solution = f"$\\dfrac{{{n1} \\times {n2}}}{{{d1} \\times {d2}}} = \\mathbf{{\\dfrac{{{ans_n//g}}}{{{ans_d//g}}}}}$"
                answer_value = f"{ans_n//g}/{ans_d//g}"
            else:
                lcm = (d1 * d2) // math.gcd(d1, d2)
                n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)
                v1, v2 = n1 * (lcm // d1), n2 * (lcm // d2)
                if op == "subtraction":
                    if v1 < v2:
                        d1, d2, n1, n2, v1, v2 = d2, d1, n2, n1, v2, v1
                    ans_num = v1 - v2
                    sym = "-"
                else:  # addition
                    ans_num = v1 + v2
                    sym = "+"
                g = math.gcd(ans_num, lcm) if ans_num else lcm
                prompt = f"Calculate and simplify: $\\dfrac{{{n1}}}{{{d1}}} {sym} \\dfrac{{{n2}}}{{{d2}}} = \\underline{{\\hspace{{2.5cm}}}}$"
                solution = f"$\\dfrac{{{v1}}}{{{lcm}}} {sym} \\dfrac{{{v2}}}{{{lcm}}} = \\dfrac{{{ans_num}}}{{{lcm}}} = \\mathbf{{\\dfrac{{{ans_num//g}}}{{{lcm//g}}}}}$"
                answer_value = f"{ans_num//g}/{lcm//g}"
        else:  # medium
            d1 = random.choice([2, 3, 4, 5])
            d2 = random.choice([3, 4, 5, 6])
            while d1 == d2:
                d2 = random.choice([3, 4, 5, 6])
            if op == "multiplication":
                n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)
                ans_n, ans_d = n1 * n2, d1 * d2
                g = math.gcd(ans_n, ans_d)
                prompt = f"Multiply the fractions: $\\dfrac{{{n1}}}{{{d1}}} \\times \\dfrac{{{n2}}}{{{d2}}} = \\underline{{\\hspace{{2.5cm}}}}$"
                solution = f"$\\dfrac{{{n1} \\times {n2}}}{{{d1} \\times {d2}}} = \\mathbf{{\\dfrac{{{ans_n//g}}}{{{ans_d//g}}}}}$"
                answer_value = f"{ans_n//g}/{ans_d//g}"
            else:
                lcm = (d1 * d2) // math.gcd(d1, d2)
                n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)
                v1, v2 = n1 * (lcm // d1), n2 * (lcm // d2)
                if op == "subtraction":
                    if v1 < v2:
                        d1, d2, n1, n2, v1, v2 = d2, d1, n2, n1, v2, v1
                    ans_num = v1 - v2
                    sym = "-"
                else:  # addition
                    ans_num = v1 + v2
                    sym = "+"
                g = math.gcd(ans_num, lcm) if ans_num else lcm
                prompt = f"Calculate and simplify: $\\dfrac{{{n1}}}{{{d1}}} {sym} \\dfrac{{{n2}}}{{{d2}}} = \\underline{{\\hspace{{2.5cm}}}}$"
                solution = f"$\\dfrac{{{ans_num}}}{{{lcm}}} = \\mathbf{{\\dfrac{{{ans_num//g}}}{{{lcm//g}}}}}$"
                answer_value = f"{ans_num//g}/{lcm//g}"

        return Question(
            section=meta["focus_area"], topic="fractions", outcome_code=code,
            focus_area=meta["focus_area"], capability=meta["capability"], stage=meta["stage"],
            prompt_tex=prompt, solution_tex=solution, answer_value=answer_value, layout_hint="list"
        )

    # 8. Algebra
    def generate_algebra(
        self,
        difficulty: str = "medium",
        fixed_questions: Optional[List[Dict[str, Any]]] = None,
        index: int = 0
    ) -> Question:
        diff = self._norm_diff(difficulty)
        if diff == "easy":
            code = "MA1-CSQ-01"
        elif diff in ["hard", "genius"]:
            code = "MA3-MR-02"
        else:
            code = "MA2-AR-02"

        meta = self._meta(code)

        if fixed_questions and index < len(fixed_questions):
            fq = fixed_questions[index]
            if "prompt" in fq and "solution" in fq:
                return Question(
                    section=meta["focus_area"], topic="algebra", outcome_code=code,
                    focus_area=meta["focus_area"], capability=meta["capability"],
                    prompt_tex=fq["prompt"], solution_tex=fq["solution"], layout_hint="list"
                )

        if diff == "easy":
            x_val = random.randint(2, 15)
            a = random.randint(3, 20)
            b = x_val + a
            prompt = f"Solve for $x$: $x + {a} = {b}$"
            solution = f"$x = {b} - {a} \\implies x = \\mathbf{{{x_val}}}$"
        elif diff == "genius":
            x_val = random.randint(2, 8)
            k = random.randint(2, 4)
            b = random.randint(1, 9)
            target = k * (x_val + b)
            prompt = f"Solve for $x$: ${k}(x + {b}) = {target}$"
            solution = f"$x + {b} = {target//k} \\implies x = \\mathbf{{{x_val}}}$"
        elif diff == "hard":
            x_val = random.randint(2, 9)
            c = random.randint(2, 5)
            a = c + random.randint(2, 4)
            d = random.randint(15, 40)
            b = (c * x_val + d) - (a * x_val)
            prompt = f"Solve for $x$: ${a}x + {b} = {c}x + {d}$" if b >= 0 else f"Solve for $x$: ${a}x - {abs(b)} = {c}x + {d}$"
            solution = f"${a - c}x = {d - b} \\implies x = \\mathbf{{{x_val}}}$"
        else: # medium
            x_val = random.randint(2, 10)
            a, b = random.randint(2, 6), random.randint(1, 15)
            c = a * x_val + b
            prompt = f"Solve for $x$: ${a}x + {b} = {c}$"
            solution = f"${a}x = {c - b} \\implies x = \\mathbf{{{x_val}}}$"

        return Question(
            section=meta["focus_area"], topic="algebra", outcome_code=code,
            focus_area=meta["focus_area"], capability=meta["capability"], stage=meta["stage"],
            prompt_tex=prompt, solution_tex=solution, answer_value=str(x_val), layout_hint="list"
        )

    # 9. Reading Time
    def generate_reading_time(
        self,
        difficulty: str = "medium",
        fixed_questions: Optional[List[Dict[str, Any]]] = None,
        index: int = 0
    ) -> Question:
        diff = self._norm_diff(difficulty)
        if diff == "easy":
            code = "MA1-NSM-02"
        elif diff in ["hard", "genius"]:
            code = "MA3-NSM-02"
        else:
            code = "MA2-NSM-02"

        meta = self._meta(code)

        if fixed_questions and index < len(fixed_questions):
            fq = fixed_questions[index]
            if "prompt" in fq and "solution" in fq:
                return Question(
                    section=meta["focus_area"], topic="reading_time", outcome_code=code,
                    focus_area=meta["focus_area"], capability=meta["capability"],
                    prompt_tex=fq["prompt"], solution_tex=fq["solution"], layout_hint="list"
                )
            hour, minute = fq.get("hour", 3), fq.get("minute", 30)
        else:
            hour = random.randint(1, 12)
            if diff == "easy":
                minute = random.choice([0, 30])
            elif diff in ["hard", "genius"]:
                minute = random.choice([5, 10, 20, 25, 35, 40, 50, 55])
            else:
                minute = random.choice([0, 15, 30, 45])

        if diff == "genius":
            dep_h = random.randint(18, 22)
            dep_m = random.choice([15, 30, 45])
            dur_h = random.randint(4, 7)
            dur_m = random.choice([15, 30, 45])
            arr_h = (dep_h + dur_h + (dep_m + dur_m) // 60) % 24
            arr_m = (dep_m + dur_m) % 60
            prompt = f"A flight departs at \\textbf{{{dep_h:02d}:{dep_m:02d}}} and takes \\textbf{{{dur_h} hours {dur_m} mins}}. What is the arrival time in 24-hour notation?"
            solution = f"Arrival time is \\textbf{{{arr_h:02d}:{arr_m:02d}}} next day."
            return Question(
                section=meta["focus_area"], topic="reading_time", outcome_code=code,
                focus_area=meta["focus_area"], capability=meta["capability"], stage=meta["stage"],
                q_type="word", prompt_tex=prompt, solution_tex=solution,
                answer_value=f"{arr_h:02d}:{arr_m:02d}", layout_hint="list"
            )

        h_angle = 90 - (hour * 30 + minute * 0.5)
        m_angle = 90 - (minute * 6)

        prompt = (
            f"Write the time shown on the clock face:\\\\[0.5em]\n"
            f"\\begin{{tikzpicture}}[scale=0.8]\n"
            f"  \\draw[very thick] (0,0) circle (1.2cm);\n"
            f"  \\foreach \\x in {{1,...,12}} {{\n"
            f"     \\node[font=\\tiny\\bfseries] at (90-\\x*30:0.95cm) {{\\x}};\n"
            f"  }}\n"
            f"  \\draw[line width=1.5pt,-stealth] (0,0) -- ({h_angle}:0.55cm);\n"
            f"  \\draw[line width=1.0pt,-stealth] (0,0) -- ({m_angle}:0.85cm);\n"
            f"  \\fill (0,0) circle (2pt);\n"
            f"\\end{{tikzpicture}}\\\\[0.5em]\n"
            f"Time: \\underline{{\\hspace{{3cm}}}}"
        )
        time_str = f"{hour:02d}:{minute:02d}"
        solution = f"Clock shows $\\mathbf{{{time_str}}}$"

        return Question(
            section=meta["focus_area"], topic="reading_time", outcome_code=code,
            focus_area=meta["focus_area"], capability=meta["capability"], stage=meta["stage"],
            q_type="tikz", prompt_tex=prompt, solution_tex=solution, answer_value=time_str, layout_hint="list"
        )

    # 10. Geometry & Angles
    def generate_geometry_angles(
        self,
        difficulty: str = "medium",
        fixed_questions: Optional[List[Dict[str, Any]]] = None,
        index: int = 0
    ) -> Question:
        diff = self._norm_diff(difficulty)
        if diff == "easy":
            code = "MA2-GM-03"
        elif diff in ["hard", "genius"]:
            code = "MA3-GM-03"
        else:
            code = "MA2-GM-03"

        meta = self._meta(code)

        if fixed_questions and index < len(fixed_questions):
            fq = fixed_questions[index]
            if "prompt" in fq and "solution" in fq:
                return Question(
                    section=meta["focus_area"], topic="geometry_angles", outcome_code=code,
                    focus_area=meta["focus_area"], capability=meta["capability"],
                    prompt_tex=fq["prompt"], solution_tex=fq["solution"], layout_hint="list"
                )

        if diff == "genius":
            a1, a2 = random.randint(35, 75), random.randint(40, 80)
            missing = 180 - (a1 + a2)
            prompt = f"In a triangle, two interior angles measure ${a1}^\\circ$ and ${a2}^\\circ$. Calculate the third angle $x$:"
            solution = f"$x = 180^\\circ - ({a1}^\\circ + {a2}^\\circ) = \\mathbf{{{missing}^\\circ}}$"
            answer_value = str(missing)
        elif diff == "hard":
            known_deg = random.randint(35, 145)
            missing_deg = 180 - known_deg
            prompt = (
                f"Find the missing angle $x$ on the straight line:\\\\[0.5em]\n"
                f"\\begin{{tikzpicture}}[scale=0.8]\n"
                f"  \\draw[thick,<->] (-2,0) -- (2,0);\n"
                f"  \\draw[thick,->] (0,0) -- ({known_deg}:1.8);\n"
                f"  \\node at (0.4, 0.3) {{${known_deg}^\\circ$}};\n"
                f"  \\node at (-0.4, 0.3) {{$x$}};\n"
                f"\\end{{tikzpicture}}\\\\[0.5em]\n"
                f"$x = \\underline{{\\hspace{{3cm}}}}$"
            )
            solution = f"$x = 180^\\circ - {known_deg}^\\circ = \\mathbf{{{missing_deg}^\\circ}}$"
            answer_value = str(missing_deg)
        else:
            (angle_type,) = self._draw("angle_type", [("acute",), ("right",), ("obtuse",)])
            deg = random.randint(25, 75) if angle_type == "acute" else (90 if angle_type == "right" else random.randint(105, 155))
            # "right" is always exactly 90 degrees, so without some other
            # source of variety a repeated draw (once the acute/right/obtuse
            # bag above completes a lap) would render byte-identical TikZ -
            # jitter the ray length/arc radius slightly so it never does.
            ray_len = round(random.uniform(1.8, 2.2), 2)
            arc_r = round(random.uniform(0.35, 0.45), 2)
            prompt = (
                f"Classify this angle (Acute, Right, or Obtuse):\\\\[0.5em]\n"
                f"\\begin{{tikzpicture}}[scale=0.7]\n"
                f"  \\draw[thick,<->] ({ray_len},0) -- (0,0) -- ({deg}:{ray_len});\n"
                f"  \\draw[fill=gray!30] (0,0) -- ({arc_r},0) arc (0:{deg}:{arc_r}) -- cycle;\n"
                f"\\end{{tikzpicture}}\\\\[0.5em]\n"
                f"Angle Type: \\underline{{\\hspace{{3cm}}}}"
            )
            solution = f"Angle is ${deg}^\\circ$, which is an \\textbf{{{angle_type.capitalize()} Angle}}."
            answer_value = angle_type.capitalize()

        return Question(
            section=meta["focus_area"], topic="geometry_angles", outcome_code=code,
            focus_area=meta["focus_area"], capability=meta["capability"], stage=meta["stage"],
            q_type="tikz" if diff != "genius" else "math", prompt_tex=prompt, solution_tex=solution,
            answer_value=answer_value, layout_hint="list"
        )

    # 11. 2D Shapes & Spatial Structure
    def generate_2d_shapes(
        self,
        difficulty: str = "medium",
        shapes: Optional[List[str]] = None,
        fixed_questions: Optional[List[Dict[str, Any]]] = None,
        index: int = 0
    ) -> Question:
        diff = self._norm_diff(difficulty)
        if diff == "easy":
            code = "MA1-2DS-01"
        elif diff in ["hard", "genius"]:
            code = "MA3-2DS-01"
        else:
            code = "MA2-2DS-01"

        meta = self._meta(code)

        if diff == "easy":
            s_name, sides, _ = self._draw("2d_easy", EASY_2D_SHAPES, shapes)
            diagram = _tikz_regular_polygon(sides)
            prompt = f"How many sides does this shape have?\\\\[0.4em]\n{diagram}\\\\[0.3em]\nSides: \\underline{{\\hspace{{2cm}}}}"
            solution = f"A {s_name} has $\\mathbf{{{sides}}}$ sides."
            answer_value = str(sides)
        elif diff == "genius":
            l1, w1 = random.randint(6, 12), random.randint(4, 8)
            l2, w2 = random.randint(3, 5), random.randint(2, 4)
            area = (l1 * w1) + (l2 * w2)
            diagram = _tikz_l_shape(l1, w1, l2, w2)
            prompt = (
                f"An L-shaped figure is formed by two rectangles, as shown below. Calculate the total area:"
                f"\\\\[0.4em]\n{diagram}\\\\[0.3em]\n"
                f"Area: \\underline{{\\hspace{{2.5cm}}}}"
            )
            solution = f"$\\text{{Total Area}} = ({l1} \\times {w1}) + ({l2} \\times {w2}) = {l1*w1} + {l2*w2} = \\mathbf{{{area}\\text{{ cm}}^2}}$"
            answer_value = str(area)
        elif diff == "hard":
            t_name, _ = self._draw("2d_hard", HARD_2D_TRIANGLES, shapes)
            diagram = _tikz_triangle(t_name)
            prompt = f"Classify the triangle shown below (Equilateral, Isosceles, or Scalene):\\\\[0.4em]\n{diagram}\\\\[0.3em]\nClassification: \\underline{{\\hspace{{3cm}}}}"
            solution = f"\\textbf{{{t_name} Triangle}}"
            answer_value = t_name
        else:
            name, _ = self._draw("2d_medium", MEDIUM_2D_QUADS, shapes)
            diagram = _tikz_quadrilateral(name)
            prompt = f"Name the quadrilateral shown below:\\\\[0.4em]\n{diagram}\\\\[0.3em]\nName: \\underline{{\\hspace{{3cm}}}}"
            solution = f"\\textbf{{{name}}}"
            answer_value = name

        return Question(
            section=meta["focus_area"], topic="2d_shapes", outcome_code=code,
            focus_area=meta["focus_area"], capability=meta["capability"], stage=meta["stage"],
            q_type="tikz", prompt_tex=prompt, solution_tex=solution, answer_value=answer_value, layout_hint="list"
        )

    # 12. 3D Objects & Nets
    def generate_3d_objects(
        self,
        difficulty: str = "medium",
        objects_3d: Optional[List[str]] = None,
        fixed_questions: Optional[List[Dict[str, Any]]] = None,
        index: int = 0
    ) -> Question:
        diff = self._norm_diff(difficulty)
        if diff == "easy":
            code = "MA1-3DS-01"
        elif diff in ["hard", "genius"]:
            code = "MA3-3DS-01"
        else:
            code = "MA2-3DS-01"

        meta = self._meta(code)

        if diff == "genius":
            l, w, h = random.randint(4, 10), random.randint(3, 8), random.randint(5, 12)
            vol = l * w * h
            cap_l = vol / 1000.0
            diagram = _tikz_cuboid(min(2.4, 0.9 + w * 0.12), min(2.0, 0.9 + h * 0.1), label_w=f"{w} cm", label_h=f"{h} cm", label_d=f"{l} cm")
            prompt = (
                f"A rectangular tank measures $\\mathbf{{{l}\\text{{ cm}} \\times {w}\\text{{ cm}} \\times {h}\\text{{ cm}}}}$, as shown below. "
                f"Calculate its capacity in litres ($1000\\text{{ cm}}^3 = 1\\text{{ L}}$):\\\\[0.4em]\n{diagram}\\\\[0.3em]\n"
                f"Capacity: \\underline{{\\hspace{{2.5cm}}}}"
            )
            solution = f"$\\text{{Volume}} = {vol}\\text{{ cm}}^3 \\implies \\text{{Capacity}} = \\mathbf{{{cap_l:.2f}\\text{{ L}}}}$"
            answer_value = f"{cap_l:.2f}"
        else:
            name, faces, f_type, _ = self._draw("3d_objects", OBJ_3D_POOL, objects_3d)
            if name == "Cube":
                s = round(random.uniform(1.3, 1.7), 2)
                diagram = _tikz_cuboid(s, s)
            elif name == "Rectangular Prism":
                diagram = _tikz_cuboid(round(random.uniform(1.6, 2.1), 2), round(random.uniform(1.1, 1.5), 2))
            else:
                diagram = _tikz_pyramid()
            prompt = f"How many flat faces does this \\textbf{{{name}}} have?\\\\[0.4em]\n{diagram}\\\\[0.3em]\nFaces: \\underline{{\\hspace{{2cm}}}}"
            solution = f"A {name} has $\\mathbf{{{faces}}}$ {f_type} faces."
            answer_value = str(faces)

        return Question(
            section=meta["focus_area"], topic="3d_objects", outcome_code=code,
            focus_area=meta["focus_area"], capability=meta["capability"], stage=meta["stage"],
            q_type="tikz", prompt_tex=prompt, solution_tex=solution, answer_value=answer_value, layout_hint="list"
        )

    # 13. Data & Graphing
    def generate_data(
        self,
        difficulty: str = "medium",
        fixed_questions: Optional[List[Dict[str, Any]]] = None,
        index: int = 0
    ) -> Question:
        diff = self._norm_diff(difficulty)
        if diff == "easy":
            code = "MA1-DATA-01"
        elif diff in ["hard", "genius"]:
            code = "MA3-DATA-01"
        else:
            code = "MA2-DATA-01"

        meta = self._meta(code)

        if diff == "genius":
            dataset = sorted([random.randint(10, 50) for _ in range(5)])
            mean_val = sum(dataset) / len(dataset)
            median_val = dataset[2]
            prompt = f"Calculate the mean and median of the dataset: ${', '.join(map(str, dataset))}$"
            solution = f"$\\text{{Mean}} = \\mathbf{{{mean_val:.1f}}}$, $\\text{{Median}} = \\mathbf{{{median_val}}}$"
            answer_value = f"Mean {mean_val:.1f}, Median {median_val}"
        else:
            fruit_pool = ["Apples", "Bananas", "Oranges", "Grapes", "Pears"]
            n_items = random.choice([3, 4])
            items = random.sample(fruit_pool, n_items)
            counts = random.sample(range(4, 20), n_items)
            best_idx = counts.index(max(counts))
            subject = random.choice(["class survey", "canteen survey", "school fete stall", "lunchtime poll"])
            parts = ", ".join(f"{c} chose {name}" for name, c in zip(items, counts))
            prompt = f"In a {subject}, {parts}. Which was most popular?"
            solution = f"\\textbf{{{items[best_idx]}}} ({counts[best_idx]} votes)"
            answer_value = items[best_idx]

        return Question(
            section=meta["focus_area"], topic="data", outcome_code=code,
            focus_area=meta["focus_area"], capability=meta["capability"], stage=meta["stage"],
            prompt_tex=prompt, solution_tex=solution, answer_value=answer_value, layout_hint="list"
        )

    # 14. Chance & Probability
    def generate_chance(
        self,
        difficulty: str = "medium",
        fixed_questions: Optional[List[Dict[str, Any]]] = None,
        index: int = 0
    ) -> Question:
        diff = self._norm_diff(difficulty)
        if diff == "easy":
            code = "MA1-CHAN-01"
        elif diff in ["hard", "genius"]:
            code = "MA3-CHAN-01"
        else:
            code = "MA2-CHAN-01"

        meta = self._meta(code)

        if diff == "genius":
            genius_bank = [
                ("at least one Head when two fair coins are flipped", 3, 4, "\\{HH, HT, TH, TT\\}", "HH, HT, TH"),
                ("exactly two Heads when two fair coins are flipped", 1, 4, "\\{HH, HT, TH, TT\\}", "HH"),
                ("no Heads at all when two fair coins are flipped", 1, 4, "\\{HH, HT, TH, TT\\}", "TT"),
                ("at least one Tail when two fair coins are flipped", 3, 4, "\\{HH, HT, TH, TT\\}", "HT, TH, TT"),
                ("a total of 7 when two fair 6-sided dice are rolled together", 6, 36, "36 equally likely pairs", "(1,6),(2,5),(3,4),(4,3),(5,2),(6,1)"),
                ("doubles (both dice showing the same number) when two fair 6-sided dice are rolled", 6, 36, "36 equally likely pairs", "(1,1),(2,2),(3,3),(4,4),(5,5),(6,6)"),
                ("a total of 2 or 12 when two fair 6-sided dice are rolled together", 2, 36, "36 equally likely pairs", "(1,1),(6,6)"),
                ("a total greater than 10 when two fair 6-sided dice are rolled together", 3, 36, "36 equally likely pairs", "(5,6),(6,5),(6,6)"),
                ("a total of 4 when two fair 6-sided dice are rolled together", 3, 36, "36 equally likely pairs", "(1,3),(2,2),(3,1)"),
                ("an even total when two fair 6-sided dice are rolled together", 18, 36, "36 equally likely pairs", "half of all pairs sum to an even total"),
                ("a total that is a multiple of 3 when two fair 6-sided dice are rolled together", 12, 36, "36 equally likely pairs", "totals of 3, 6, 9 or 12"),
                ("at least one 6 showing when two fair 6-sided dice are rolled together", 11, 36, "36 equally likely pairs", "any pair containing a 6"),
            ]
            desc, favourable, total, outcomes, fav_list = self._draw("chance_genius", genius_bank)
            g = math.gcd(favourable, total)
            prompt = f"What is the probability of getting {desc}? Express as a fraction in simplest form."
            solution = f"Possible outcomes: {outcomes}. Favourable: {fav_list}. $\\text{{Probability}} = \\dfrac{{{favourable}}}{{{total}}} = \\mathbf{{\\dfrac{{{favourable//g}}}{{{total//g}}}}}$."
            answer_value = f"{favourable//g}/{total//g}"
        elif diff == "hard":
            hard_bank = [
                ("an even number on a standard 6-sided die", 3),
                ("an odd number on a standard 6-sided die", 3),
                ("a multiple of 3 on a standard 6-sided die", 2),
                ("a number greater than 4 on a standard 6-sided die", 2),
                ("a number less than 3 on a standard 6-sided die", 2),
                ("a 1 on a standard 6-sided die", 1),
                ("a number greater than 2 on a standard 6-sided die", 4),
                ("a multiple of 2 on a standard 6-sided die", 3),
                ("a number that is not 6 on a standard 6-sided die", 5),
                ("a prime number (2, 3 or 5) on a standard 6-sided die", 3),
                ("a number that is at least 4 on a standard 6-sided die", 3),
                ("a square number (1 or 4) on a standard 6-sided die", 2),
            ]
            desc, favourable = self._draw("chance_hard", hard_bank)
            g = math.gcd(favourable, 6)
            prompt = f"What is the probability of rolling {desc}? Express as a fraction."
            solution = f"$\\mathbf{{\\dfrac{{{favourable}}}{{6}} = \\dfrac{{{favourable//g}}}{{{6//g}}}}}$"
            answer_value = f"{favourable//g}/{6//g}"
        else:
            medium_bank = [
                ("Is it \\textbf{Certain}, \\textbf{Likely}, \\textbf{Unlikely}, or \\textbf{Impossible} to roll a 7 on a standard 6-sided die?", "Impossible", "\\textbf{Impossible} (die only has numbers 1--6)"),
                ("Is it \\textbf{Certain}, \\textbf{Likely}, \\textbf{Unlikely}, or \\textbf{Impossible} to roll a number from 1 to 6 on a standard 6-sided die?", "Certain", "\\textbf{Certain} (every face is 1--6)"),
                ("A bag contains only blue marbles. Is it \\textbf{Certain}, \\textbf{Likely}, \\textbf{Unlikely}, or \\textbf{Impossible} to pick a blue marble?", "Certain", "\\textbf{Certain} (there are no other colours in the bag)"),
                ("A bag contains only blue marbles. Is it \\textbf{Certain}, \\textbf{Likely}, \\textbf{Unlikely}, or \\textbf{Impossible} to pick a red marble?", "Impossible", "\\textbf{Impossible} (there are no red marbles in the bag)"),
                ("Is it \\textbf{Certain}, \\textbf{Likely}, \\textbf{Unlikely}, or \\textbf{Impossible} that the sun rises tomorrow morning?", "Certain", "\\textbf{Certain} (this happens every day)"),
                ("Is it \\textbf{Certain}, \\textbf{Likely}, \\textbf{Unlikely}, or \\textbf{Impossible} that it snows in Sydney in the middle of summer?", "Unlikely", "\\textbf{Unlikely} (Sydney summers are almost never cold enough to snow)"),
                ("Is it \\textbf{Certain}, \\textbf{Likely}, \\textbf{Unlikely}, or \\textbf{Impossible} to meet a talking dinosaur on the way to school?", "Impossible", "\\textbf{Impossible} (dinosaurs are extinct and cannot talk)"),
                ("Is it \\textbf{Certain}, \\textbf{Likely}, \\textbf{Unlikely}, or \\textbf{Impossible} that a tossed coin lands on either Heads or Tails?", "Certain", "\\textbf{Certain} (a coin only has two sides)"),
                ("Is it \\textbf{Certain}, \\textbf{Likely}, \\textbf{Unlikely}, or \\textbf{Impossible} that a new puppy will grow into a cat?", "Impossible", "\\textbf{Impossible} (puppies always grow into dogs)"),
                ("A calendar shows every month has at least 28 days. Is it \\textbf{Certain}, \\textbf{Likely}, \\textbf{Unlikely}, or \\textbf{Impossible} that next month has at least 28 days?", "Certain", "\\textbf{Certain} (every month has at least 28 days)"),
                ("Is it \\textbf{Certain}, \\textbf{Likely}, \\textbf{Unlikely}, or \\textbf{Impossible} to draw a spade from a deck containing only hearts?", "Impossible", "\\textbf{Impossible} (there are no spades in the deck)"),
                ("Most days in Australia's desert regions are hot and dry. Is it \\textbf{Certain}, \\textbf{Likely}, \\textbf{Unlikely}, or \\textbf{Impossible} that tomorrow will be hot and dry there?", "Likely", "\\textbf{Likely} (hot, dry days are the most common in that climate)"),
                ("Is it \\textbf{Certain}, \\textbf{Likely}, \\textbf{Unlikely}, or \\textbf{Impossible} that you will grow one year older on your next birthday?", "Certain", "\\textbf{Certain} (everyone turns one year older on their next birthday)"),
                ("A spinner is divided into 4 equal red sections only. Is it \\textbf{Certain}, \\textbf{Likely}, \\textbf{Unlikely}, or \\textbf{Impossible} to spin green?", "Impossible", "\\textbf{Impossible} (there is no green section on the spinner)"),
                ("Most students in a class finish their homework most weeks. Is it \\textbf{Certain}, \\textbf{Likely}, \\textbf{Unlikely}, or \\textbf{Impossible} that most of the class finishes homework this week?", "Likely", "\\textbf{Likely} (this matches the usual pattern for the class)"),
                ("Is it \\textbf{Certain}, \\textbf{Likely}, \\textbf{Unlikely}, or \\textbf{Impossible} to find a fish that can ride a bicycle?", "Impossible", "\\textbf{Impossible} (fish cannot ride bicycles)"),
            ]
            prompt, answer_value, solution = self._draw("chance_medium", medium_bank)

        return Question(
            section=meta["focus_area"], topic="chance", outcome_code=code,
            focus_area=meta["focus_area"], capability=meta["capability"], stage=meta["stage"],
            prompt_tex=prompt, solution_tex=solution, answer_value=answer_value, layout_hint="list"
        )

    # 15. Date Duration
    def generate_date_duration(
        self,
        difficulty: str = "medium",
        fixed_questions: Optional[List[Dict[str, Any]]] = None,
        index: int = 0
    ) -> Question:
        diff = self._norm_diff(difficulty)
        if diff in ["hard", "genius"]:
            code = "MA3-NSM-02"
        else:
            code = "MA2-NSM-02"

        meta = self._meta(code)

        start_day = random.randint(1, 12)
        duration_days = random.randint(14, 30) if diff in ["hard", "genius"] else random.randint(4, 18)
        base_date = datetime(2026, 5, start_day)
        end_date = base_date + timedelta(days=duration_days)

        start_str, end_str = base_date.strftime("%d %B"), end_date.strftime("%d %B")
        calendar_tex = _calendar_block_for_range(base_date, end_date)
        prompt = (
            f"Using the calendar below, how many days are there between \\textbf{{{start_str}}} (boxed) "
            f"and \\textbf{{{end_str}}} (underlined)?\\\\[0.4em]\n{calendar_tex}\\\\[0.3em]\n"
            f"Number of days: \\underline{{\\hspace{{2.5cm}}}}"
        )
        solution = f"$\\mathbf{{{duration_days}}}$ days"

        return Question(
            section=meta["focus_area"], topic="date_duration", outcome_code=code,
            focus_area=meta["focus_area"], capability=meta["capability"], stage=meta["stage"],
            q_type="tikz", prompt_tex=prompt, solution_tex=solution, answer_value=str(duration_days), layout_hint="list"
        )

    # 16. Speed & Distance
    def generate_speed_distance(
        self,
        difficulty: str = "medium",
        fixed_questions: Optional[List[Dict[str, Any]]] = None,
        index: int = 0
    ) -> Question:
        diff = self._norm_diff(difficulty)
        if diff in ["hard", "genius"]:
            code = "MA3-GM-02"
        else:
            code = "MA2-GM-02"

        meta = self._meta(code)

        speed, hours = random.choice([40, 50, 60, 80]), random.randint(2, 5)
        dist = speed * hours
        driver = random.choice(["Liam", "Sophia", "Noah", "Olivia", "Ethan"])

        if diff == "genius":
            # Multi-leg journey e.g. Leg 1: 120km in 2h, Leg 2: 180km in 3h. Average speed?
            t1, t2 = random.randint(2, 4), random.randint(2, 4)
            speed_bank = [40, 50, 60, 70, 80, 90, 100, 110, 120]
            d1, d2, tot_d, tot_t = 0, 0, 0, 1
            for _ in range(50):
                s1, s2 = random.choice(speed_bank), random.choice(speed_bank)
                if s1 == s2:
                    continue
                d1, d2 = s1 * t1, s2 * t2
                tot_d, tot_t = d1 + d2, t1 + t2
                if tot_d % tot_t == 0:
                    break
            avg_s_raw = tot_d / tot_t
            avg_s = str(int(avg_s_raw)) if avg_s_raw == int(avg_s_raw) else f"{avg_s_raw:.1f}"
            prompt = f"{driver} drives $\\mathbf{{{d1}\\text{{ km}}}}$ in $\\mathbf{{{t1}\\text{{ hours}}}}$ and then $\\mathbf{{{d2}\\text{{ km}}}}$ in $\\mathbf{{{t2}\\text{{ hours}}}}$. Calculate the average speed for the whole journey:"
            solution = f"$\\text{{Average Speed}} = \\dfrac{{\\text{{Total Distance}}}}{{\\text{{Total Time}}}} = \\dfrac{{{tot_d}}}{{{tot_t}}} = \\mathbf{{{avg_s}\\text{{ km/h}}}}$"
            answer_value = avg_s
        else:
            prompt = f"{driver} drives a car at a constant speed of $\\mathbf{{{speed}\\text{{ km/h}}}}$ for $\\mathbf{{{hours}\\text{{ hours}}}}$. How far did {driver} travel?"
            solution = f"$\\text{{Distance}} = \\text{{Speed}} \\times \\text{{Time}} = {speed} \\times {hours} = \\mathbf{{{dist}\\text{{ km}}}}$"
            answer_value = str(dist)

        return Question(
            section=meta["focus_area"], topic="speed_distance", outcome_code=code,
            focus_area=meta["focus_area"], capability=meta["capability"], stage=meta["stage"],
            prompt_tex=prompt, solution_tex=solution, answer_value=answer_value, layout_hint="list"
        )

    # 17. Multiple Choice Quiz
    def generate_multiple_choice(
        self,
        difficulty: str = "medium",
        fixed_questions: Optional[List[Dict[str, Any]]] = None,
        index: int = 0
    ) -> Question:
        code = "MA2-RN-01"
        meta = self._meta(code)

        if fixed_questions and index < len(fixed_questions):
            fq = fixed_questions[index]
            if "prompt" in fq and "solution" in fq:
                return Question(
                    section="General Mathematics Quiz", topic="multiple_choice", outcome_code=code,
                    focus_area=meta["focus_area"], capability=meta["capability"], q_type="mcq",
                    prompt_tex=fq["prompt"], solution_tex=fq["solution"], layout_hint="list"
                )

        mcq_bank = [
            {
                "q": "Which of the following is a prime number?",
                "opts": ["15", "21", "29", "33"],
                "ans": "C",
                "explain": "29 has no divisors other than 1 and itself."
            },
            {
                "q": "What is the perimeter of a square with a side length of $7\\text{ cm}$?",
                "opts": ["14 cm", "28 cm", "49 cm", "21 cm"],
                "ans": "B",
                "explain": "$\\text{Perimeter} = 4 \\times 7\\text{ cm} = 28\\text{ cm}$."
            },
            {
                "q": "What is $15\\%$ of $80$?",
                "opts": ["8", "10", "12", "15"],
                "ans": "C",
                "explain": "$10\\% = 8$, $5\\% = 4 \\implies 15\\% = 8 + 4 = 12$."
            },
            {
                "q": "Which shape has exactly 5 sides?",
                "opts": ["Hexagon", "Pentagon", "Octagon", "Heptagon"],
                "ans": "B",
                "explain": "A pentagon is a 5-sided polygon."
            },
            {
                "q": "What is $\\dfrac{3}{4}$ expressed as a decimal?",
                "opts": ["0.34", "0.75", "0.43", "1.33"],
                "ans": "B",
                "explain": "$\\dfrac{3}{4} = 3 \\div 4 = 0.75$."
            },
            {
                "q": "Which of these numbers is divisible by both 2 and 3?",
                "opts": ["14", "15", "18", "20"],
                "ans": "C",
                "explain": "$18 = 2 \\times 9 = 3 \\times 6$, so it is divisible by both."
            },
            {
                "q": "What is the value of $x$ in $3x = 21$?",
                "opts": ["6", "7", "8", "9"],
                "ans": "B",
                "explain": "$x = 21 \\div 3 = 7$."
            },
            {
                "q": "How many millimetres are there in $4.5\\text{ cm}$?",
                "opts": ["4.5 mm", "45 mm", "450 mm", "0.45 mm"],
                "ans": "B",
                "explain": "$1\\text{ cm} = 10\\text{ mm}$, so $4.5\\text{ cm} = 45\\text{ mm}$."
            },
            {
                "q": "A rectangle has length $9\\text{ cm}$ and width $4\\text{ cm}$. What is its area?",
                "opts": ["13 cm$^2$", "26 cm$^2$", "36 cm$^2$", "40 cm$^2$"],
                "ans": "C",
                "explain": "$\\text{Area} = \\text{length} \\times \\text{width} = 9 \\times 4 = 36\\text{ cm}^2$."
            },
            {
                "q": "Which fraction is equivalent to $\\dfrac{2}{3}$?",
                "opts": ["$\\dfrac{3}{4}$", "$\\dfrac{4}{6}$", "$\\dfrac{5}{9}$", "$\\dfrac{6}{10}$"],
                "ans": "B",
                "explain": "$\\dfrac{2}{3} = \\dfrac{2 \\times 2}{3 \\times 2} = \\dfrac{4}{6}$."
            },
            {
                "q": "What is the next number in the pattern: $3, 6, 12, 24, \\_\\_$?",
                "opts": ["30", "36", "48", "27"],
                "ans": "C",
                "explain": "Each term doubles the one before it: $24 \\times 2 = 48$."
            },
            {
                "q": "What is $6^2$?",
                "opts": ["12", "26", "36", "62"],
                "ans": "C",
                "explain": "$6^2 = 6 \\times 6 = 36$."
            },
            {
                "q": "Which unit would best measure the mass of an apple?",
                "opts": ["Millilitres", "Grams", "Kilometres", "Litres"],
                "ans": "B",
                "explain": "Grams are used for everyday small masses like an apple."
            },
            {
                "q": "What is $\\dfrac{1}{2} + \\dfrac{1}{3}$?",
                "opts": ["$\\dfrac{2}{5}$", "$\\dfrac{5}{6}$", "$\\dfrac{1}{6}$", "$\\dfrac{2}{6}$"],
                "ans": "B",
                "explain": "$\\dfrac{1}{2} + \\dfrac{1}{3} = \\dfrac{3}{6} + \\dfrac{2}{6} = \\dfrac{5}{6}$."
            },
            {
                "q": "How many degrees are there in a right angle?",
                "opts": ["45$^\\circ$", "90$^\\circ$", "180$^\\circ$", "360$^\\circ$"],
                "ans": "B",
                "explain": "A right angle measures exactly $90^\\circ$."
            },
            {
                "q": "What is $1000 - 457$?",
                "opts": ["453", "553", "543", "643"],
                "ans": "C",
                "explain": "$1000 - 457 = 543$."
            }
        ]
        item = self._draw("mcq_bank", mcq_bank)
        prompt = f"{item['q']}\\\\[0.3em]\n\\begin{{enumerate}}[label=(\\Alph*), itemsep=0pt]\n"
        for opt in item['opts']:
            prompt += f"  \\item {opt}\n"
        prompt += "\\end{enumerate}"

        solution = f"\\textbf{{Option ({item['ans']})}} -- {item['explain']}"

        return Question(
            section="General Mathematics Quiz", topic="multiple_choice", outcome_code=code,
            focus_area=meta["focus_area"], capability=meta["capability"], stage=meta["stage"],
            q_type="mcq", prompt_tex=prompt, solution_tex=solution, answer_value=item['ans'], layout_hint="list"
        )


TOPIC_GENERATORS = {
    "representing_numbers": "generate_representing_numbers",
    "vertical_addition": "generate_vertical_addition",
    "vertical_subtraction": "generate_vertical_subtraction",
    "long_subtraction": "generate_vertical_subtraction",
    "vertical_multiplication": "generate_vertical_multiplication",
    "long_multiplication": "generate_vertical_multiplication",
    "long_division": "generate_long_division",
    "sequences": "generate_sequence",
    "fractions": "generate_fractions",
    "fractions_decimals": "generate_fractions",
    "algebra": "generate_algebra",
    "algebra_equations": "generate_algebra",
    "reading_time": "generate_reading_time",
    "geometry_angles": "generate_geometry_angles",
    "2d_shapes": "generate_2d_shapes",
    "3d_objects": "generate_3d_objects",
    "data": "generate_data",
    "chance": "generate_chance",
    "date_duration": "generate_date_duration",
    "speed_distance": "generate_speed_distance",
    "distance_problem": "generate_speed_distance",
    "multiple_choice": "generate_multiple_choice",
}


def build_question_for_topic(
    qb: QuestionBank,
    topic: str,
    topic_config: Dict[str, Any],
    index: int = 0
) -> Question:
    method_name = TOPIC_GENERATORS.get(topic)
    if not method_name or not hasattr(qb, method_name):
        raise ValueError(f"Unsupported topic: '{topic}'")

    method = getattr(qb, method_name)
    kwargs = {
        "difficulty": topic_config.get("difficulty", "medium"),
        "fixed_questions": topic_config.get("fixed_questions"),
        "index": index
    }

    if "digits" in topic_config:
        kwargs["digits"] = topic_config["digits"]
    if "allow_carrying" in topic_config:
        kwargs["allow_carrying"] = topic_config["allow_carrying"]
    if "allow_borrowing" in topic_config:
        kwargs["allow_borrowing"] = topic_config["allow_borrowing"]
    if "digits_top" in topic_config:
        kwargs["digits_top"] = topic_config["digits_top"]
    if "digits_bottom" in topic_config:
        kwargs["digits_bottom"] = topic_config["digits_bottom"]
    if "multiplier" in topic_config:
        kwargs["multiplier"] = topic_config["multiplier"]
    if "times_table" in topic_config:
        kwargs["times_table"] = topic_config["times_table"]
    if "divisor" in topic_config:
        kwargs["divisor"] = topic_config["divisor"]
    if "digits_dividend" in topic_config:
        kwargs["digits_dividend"] = topic_config["digits_dividend"]
    if "digits_divisor" in topic_config:
        kwargs["digits_divisor"] = topic_config["digits_divisor"]
    if "allow_remainder" in topic_config:
        kwargs["allow_remainder"] = topic_config["allow_remainder"]
    if "step_range" in topic_config:
        kwargs["step_range"] = topic_config["step_range"]
    if "pattern_type" in topic_config:
        kwargs["pattern_type"] = topic_config["pattern_type"]
    if "op_type" in topic_config:
        kwargs["op_type"] = topic_config["op_type"]
    if "shapes" in topic_config:
        kwargs["shapes"] = topic_config["shapes"]
    if "objects_3d" in topic_config:
        kwargs["objects_3d"] = topic_config["objects_3d"]

    fixed_questions = kwargs.get("fixed_questions")
    bypass_dedup = bool(fixed_questions and index < len(fixed_questions))

    q = method(**kwargs)
    if not bypass_dedup:
        # Some generators draw from a small template/category pool (e.g. a
        # handful of fixed shape names or scenario strings), so a run asking
        # for more questions than there are distinct options can otherwise
        # repeat the exact same question verbatim. Retry a bounded number of
        # times until we get a prompt this QuestionBank hasn't produced yet
        # for this topic; if the pool is well and truly exhausted, accept the
        # last draw rather than looping forever.
        seen = qb._seen_prompts.setdefault(topic, set())
        attempts = 1
        while q.prompt_tex in seen and attempts < 60:
            q = method(**kwargs)
            attempts += 1
        seen.add(q.prompt_tex)

    return q


def tex_escape(text: str) -> str:
    if not isinstance(text, str):
        return text
    return re.sub(r'(?<!\\)&', r'\\&', text)


def generate_workbook_pipeline(config: Dict[str, Any]) -> Dict[str, Any]:
    """Pipeline method that processes config.yaml and builds sections and questions."""
    seed = config.get("seed")
    qb = QuestionBank(seed=seed)

    title = tex_escape(config.get("title", f"Stage {config.get('stage', 2)} Mathematics Practice Workbook"))
    subtitle = tex_escape(config.get("subtitle", "NESA Curriculum Aligned Practice Sheet"))
    stage = config.get("stage", 2)
    header_left = tex_escape(config.get("header_left", f"NSW Stage {stage} Primary Mathematics Practice"))
    include_solutions = config.get("include_solutions", True)
    default_working_space = config.get("working_space", "2.5cm")

    processed_sections = []
    all_questions: List[Question] = []
    global_id = 1

    if "sections" in config and isinstance(config["sections"], list):
        for sec_cfg in config["sections"]:
            sec_title = tex_escape(sec_cfg.get("title", sec_cfg.get("name", "Practice Section")))
            sec_desc = tex_escape(sec_cfg.get("description", ""))
            sec_layout = sec_cfg.get("layout", "list")
            sec_working_space = sec_cfg.get("working_space", default_working_space)
            sec_questions = []

            topics_map = sec_cfg.get("topics", {})
            for topic, topic_cfg in topics_map.items():
                if isinstance(topic_cfg, int):
                    topic_cfg = {"count": topic_cfg}
                count = topic_cfg.get("count", 1)
                for i in range(count):
                    q = build_question_for_topic(qb, topic, topic_cfg, index=i)
                    q.id = global_id
                    q.section = tex_escape(q.section)
                    global_id += 1
                    sec_questions.append(q)
                    all_questions.append(q)

            processed_sections.append({
                "title": sec_title,
                "description": sec_desc,
                "layout": sec_layout,
                "working_space": sec_working_space,
                "questions": sec_questions
            })
    else:
        topics_map = config.get("topics", {})
        column_qs = []
        list_qs = []

        for topic, topic_cfg in topics_map.items():
            if isinstance(topic_cfg, int):
                topic_cfg = {"count": topic_cfg}
            count = topic_cfg.get("count", 1)
            for i in range(count):
                q = build_question_for_topic(qb, topic, topic_cfg, index=i)
                q.section = tex_escape(q.section)
                if q.layout_hint == "grid_3col":
                    column_qs.append(q)
                else:
                    list_qs.append(q)

        for q in column_qs + list_qs:
            q.id = global_id
            global_id += 1
            all_questions.append(q)

        if column_qs:
            processed_sections.append({
                "title": "1. Column Arithmetic",
                "description": "Solve each problem vertically.",
                "layout": "grid_3col",
                "working_space": default_working_space,
                "questions": column_qs
            })
        if list_qs:
            processed_sections.append({
                "title": "2. Practice Questions \\& Applications",
                "description": "",
                "layout": "list",
                "working_space": default_working_space,
                "questions": list_qs
            })

    font_size = config.get("font_size", "12pt")
    if isinstance(font_size, (int, float)):
        font_size = f"{int(font_size)}pt"
    elif not str(font_size).endswith("pt"):
        font_size = f"{font_size}pt"

    return {
        "title": title,
        "subtitle": subtitle,
        "stage": stage,
        "header_left": header_left,
        "font_size": font_size,
        "include_solutions": include_solutions,
        "sections": processed_sections,
        "all_questions": all_questions
    }