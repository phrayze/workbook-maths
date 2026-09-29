import random
import math
import os
import csv
import re
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


class QuestionBank:
    """Generates dynamic mathematics questions aligned to NESA Syllabus outcomes across EASY, MEDIUM, HARD, and GENIUS difficulties."""

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)

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
        pattern_type: str = "arithmetic",
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

        if diff == "easy":
            step = random.randint(2, 5)
            start = random.randint(1, 10)
            seq = [start + i * step for i in range(6)]
            blank_idx = 3
            ans = seq[blank_idx]
            seq_display = [str(x) if i != blank_idx else "\\underline{\\hspace{1.5cm}}" for i, x in enumerate(seq)]
            prompt = f"Find the missing number in the sequence:\\\\[0.5em] ${', '.join(seq_display)}$"
            solution = f"Missing number is $\\mathbf{{{ans}}}$ (Rule: add ${step}$)"
        elif diff == "genius":
            # Alternating step rule e.g. +3, x2, +3, x2
            start = random.randint(2, 5)
            add_val = random.randint(2, 4)
            mult_val = 2
            seq = [start]
            for i in range(5):
                if i % 2 == 0:
                    seq.append(seq[-1] + add_val)
                else:
                    seq.append(seq[-1] * mult_val)
            blank_idx = 4
            ans = seq[blank_idx]
            seq_display = [str(x) if i != blank_idx else "\\underline{\\hspace{1.5cm}}" for i, x in enumerate(seq)]
            prompt = f"Find the missing number in the two-step pattern:\\\\[0.5em] ${', '.join(seq_display)}$"
            solution = f"Missing number is $\\mathbf{{{ans}}}$ (Rule: alternate $+{add_val}$ and $\\times {mult_val}$)"
        elif diff == "hard":
            ratio = random.choice([2, 3])
            start = random.randint(1, 5)
            seq = [start * (ratio ** i) for i in range(5)]
            blank_idx = 3
            ans = seq[blank_idx]
            seq_display = [str(x) if i != blank_idx else "\\underline{\\hspace{1.5cm}}" for i, x in enumerate(seq)]
            prompt = f"Find the missing number in the geometric pattern:\\\\[0.5em] ${', '.join(seq_display)}$"
            solution = f"Missing number is $\\mathbf{{{ans}}}$ (Rule: multiply by ${ratio}$)"
        else: # medium
            step = random.randint(step_range[0], step_range[1])
            start = random.randint(5, 25)
            seq = [start + i * step for i in range(6)]
            blank_idx = random.choice([2, 3, 4])
            ans = seq[blank_idx]
            seq_display = [str(x) if i != blank_idx else "\\underline{\\hspace{1.5cm}}" for i, x in enumerate(seq)]
            prompt = f"Find the missing number in the sequence:\\\\[0.5em] ${', '.join(seq_display)}$"
            solution = f"Missing number is $\\mathbf{{{ans}}}$ (Rule: add ${step}$)"

        return Question(
            section=meta["focus_area"], topic="sequences", outcome_code=code,
            focus_area=meta["focus_area"], capability=meta["capability"], stage=meta["stage"],
            prompt_tex=prompt, solution_tex=solution, answer_value=str(ans), layout_hint="list"
        )

    # 7. Fractions
    def generate_fractions(
        self,
        op_type: str = "addition",
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

        if diff == "easy":
            denom = random.choice([4, 5, 6, 8, 10])
            num1 = random.randint(1, denom - 2)
            num2 = random.randint(1, denom - num1)
            ans_num = num1 + num2
            g = math.gcd(ans_num, denom)
            prompt = f"Calculate: $\\dfrac{{{num1}}}{{{denom}}} + \\dfrac{{{num2}}}{{{denom}}} = \\underline{{\\hspace{{2.5cm}}}}$"
            solution = f"$\\dfrac{{{num1}}}{{{denom}}} + \\dfrac{{{num2}}}{{{denom}}} = \\mathbf{{\\dfrac{{{ans_num//g}}}{{{denom//g}}}}}$"
            answer_value = f"{ans_num//g}/{denom//g}"
        elif diff == "genius":
            # Mixed numbers operations e.g. 2 (1/2) + 1 (3/4)
            w1, w2 = random.randint(1, 3), random.randint(1, 3)
            d1, d2 = 2, 4
            n1, n2 = 1, 3
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
            n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)
            ans_n, ans_d = n1 * n2, d1 * d2
            g = math.gcd(ans_n, ans_d)
            prompt = f"Multiply the fractions: $\\dfrac{{{n1}}}{{{d1}}} \\times \\dfrac{{{n2}}}{{{d2}}} = \\underline{{\\hspace{{2.5cm}}}}$"
            solution = f"$\\dfrac{{{n1} \\times {n2}}}{{{d1} \\times {d2}}} = \\mathbf{{\\dfrac{{{ans_n//g}}}{{{ans_d//g}}}}}$"
            answer_value = f"{ans_n//g}/{ans_d//g}"
        else: # medium
            d1 = random.choice([2, 3, 4, 5])
            d2 = random.choice([3, 4, 5, 6])
            while d1 == d2:
                d2 = random.choice([3, 4, 5, 6])
            n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)
            lcm = (d1 * d2) // math.gcd(d1, d2)
            ans_num = n1 * (lcm // d1) + n2 * (lcm // d2)
            g = math.gcd(ans_num, lcm)
            prompt = f"Calculate and simplify: $\\dfrac{{{n1}}}{{{d1}}} + \\dfrac{{{n2}}}{{{d2}}} = \\underline{{\\hspace{{2.5cm}}}}$"
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
            angle_type = random.choice(["acute", "right", "obtuse"])
            deg = random.randint(25, 75) if angle_type == "acute" else (90 if angle_type == "right" else random.randint(105, 155))
            prompt = (
                f"Classify this angle (Acute, Right, or Obtuse):\\\\[0.5em]\n"
                f"\\begin{{tikzpicture}}[scale=0.7]\n"
                f"  \\draw[thick,<->] (2,0) -- (0,0) -- ({deg}:2);\n"
                f"  \\draw[fill=gray!30] (0,0) -- (0.4,0) arc (0:{deg}:0.4) -- cycle;\n"
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
            shapes = [("triangle", 3), ("quadrilateral", 4), ("pentagon", 5), ("hexagon", 6)]
            s_name, sides = random.choice(shapes)
            prompt = f"How many sides does a \\textbf{{{s_name}}} have?"
            solution = f"A {s_name} has $\\mathbf{{{sides}}}$ sides."
            answer_value = str(sides)
        elif diff == "genius":
            l1, w1 = random.randint(6, 12), random.randint(4, 8)
            l2, w2 = random.randint(3, 5), random.randint(2, 4)
            area = (l1 * w1) + (l2 * w2)
            prompt = f"An L-shaped figure is formed by two rectangles: $R_1 ({l1}\\text{{ cm}} \\times {w1}\\text{{ cm}})$ and $R_2 ({l2}\\text{{ cm}} \\times {w2}\\text{{ cm}})$. Calculate the total area:"
            solution = f"$\\text{{Total Area}} = ({l1} \\times {w1}) + ({l2} \\times {w2}) = {l1*w1} + {l2*w2} = \\mathbf{{{area}\\text{{ cm}}^2}}$"
            answer_value = str(area)
        elif diff == "hard":
            triangles = ["Equilateral (3 equal sides)", "Isosceles (2 equal sides)", "Scalene (no equal sides)"]
            choice = random.choice(triangles)
            t_name = choice.split()[0]
            prompt = f"Classify a triangle that has {choice.split('(')[1][:-1]}:"
            solution = f"\\textbf{{{t_name} Triangle}}"
            answer_value = t_name
        else:
            shapes = [("Parallelogram", "2 pairs of parallel sides"), ("Rhombus", "4 equal sides"), ("Trapezium", "1 pair of parallel sides")]
            name, feat = random.choice(shapes)
            prompt = f"Name the quadrilateral that has \\textbf{{{feat}}}:"
            solution = f"\\textbf{{{name}}}"
            answer_value = name

        return Question(
            section=meta["focus_area"], topic="2d_shapes", outcome_code=code,
            focus_area=meta["focus_area"], capability=meta["capability"], stage=meta["stage"],
            prompt_tex=prompt, solution_tex=solution, answer_value=answer_value, layout_hint="list"
        )

    # 12. 3D Objects & Nets
    def generate_3d_objects(
        self,
        difficulty: str = "medium",
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
            prompt = f"A rectangular tank measures $\\mathbf{{{l}\\text{{ cm}} \\times {w}\\text{{ cm}} \\times {h}\\text{{ cm}}}}$. Calculate its capacity in litres ($1000\\text{{ cm}}^3 = 1\\text{{ L}}$):"
            solution = f"$\\text{{Volume}} = {vol}\\text{{ cm}}^3 \\implies \\text{{Capacity}} = \\mathbf{{{cap_l:.2f}\\text{{ L}}}}$"
            answer_value = f"{cap_l:.2f}"
        else:
            objs = [("Cube", 6, "square"), ("Rectangular Prism", 6, "rectangular"), ("Triangular Pyramid", 4, "triangular")]
            name, faces, f_type = random.choice(objs)
            prompt = f"How many flat faces does a \\textbf{{{name}}} have?"
            solution = f"A {name} has $\\mathbf{{{faces}}}$ {f_type} faces."
            answer_value = str(faces)

        return Question(
            section=meta["focus_area"], topic="3d_objects", outcome_code=code,
            focus_area=meta["focus_area"], capability=meta["capability"], stage=meta["stage"],
            prompt_tex=prompt, solution_tex=solution, answer_value=answer_value, layout_hint="list"
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
            prompt = "In a class survey, 8 students chose Apples, 12 chose Bananas, and 5 chose Oranges. Which fruit was most popular?"
            solution = "\\textbf{Bananas} (12 students)"
            answer_value = "Bananas"

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
            prompt = "Two fair coins are flipped simultaneously. What is the probability of getting at least one Head? Express as a fraction."
            solution = "Possible outcomes: $\\{HH, HT, TH, TT\\}$. Favourable: 3. $\\text{Probability} = \\mathbf{\\dfrac{3}{4}}$."
            answer_value = "3/4"
        elif diff == "hard":
            prompt = "What is the probability of rolling an even number on a standard 6-sided die? Express as a fraction."
            solution = "$\\mathbf{\\dfrac{3}{6} = \\dfrac{1}{2}}$"
            answer_value = "1/2"
        else:
            prompt = "Is it \\textbf{Certain}, \\textbf{Likely}, \\textbf{Unlikely}, or \\textbf{Impossible} to roll a 7 on a standard 6-sided die?"
            solution = "\\textbf{Impossible} (die only has numbers 1--6)"
            answer_value = "Impossible"

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
        duration_days = random.randint(14, 45) if diff in ["hard", "genius"] else random.randint(4, 18)
        base_date = datetime(2026, 5, start_day)
        end_date = base_date + timedelta(days=duration_days)

        start_str, end_str = base_date.strftime("%d %B"), end_date.strftime("%d %B")
        prompt = f"How many days are there between \\textbf{{{start_str}}} and \\textbf{{{end_str}}}?"
        solution = f"$\\mathbf{{{duration_days}}}$ days"

        return Question(
            section=meta["focus_area"], topic="date_duration", outcome_code=code,
            focus_area=meta["focus_area"], capability=meta["capability"], stage=meta["stage"],
            prompt_tex=prompt, solution_tex=solution, answer_value=str(duration_days), layout_hint="list"
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
            d1, t1 = 120, 2
            d2, t2 = 180, 3
            tot_d = d1 + d2
            tot_t = t1 + t2
            avg_s = tot_d // tot_t
            prompt = f"{driver} drives $\\mathbf{{{d1}\\text{{ km}}}}$ in $\\mathbf{{{t1}\\text{{ hours}}}}$ and then $\\mathbf{{{d2}\\text{{ km}}}}$ in $\\mathbf{{{t2}\\text{{ hours}}}}$. Calculate the average speed for the whole journey:"
            solution = f"$\\text{{Average Speed}} = \\dfrac{{\\text{{Total Distance}}}}{{\\text{{Total Time}}}} = \\dfrac{{{tot_d}}}{{{tot_t}}} = \\mathbf{{{avg_s}\\text{{ km/h}}}}$"
            answer_value = str(avg_s)
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
            }
        ]
        item = random.choice(mcq_bank)
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

    return method(**kwargs)


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