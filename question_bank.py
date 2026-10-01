import csv
import os
from typing import Any, Dict, List

CSV_PATH = os.path.join(os.path.dirname(__file__), "maths-curriculum-ks1_2_3.csv")

# Single source of truth for what the web picker offers per topic. Practice
# Area grouping mirrors the section titles in config-template.yaml, so a saved
# config.yaml maps 1:1 onto this catalogue. (Layout hint / default count are
# UI/generation concerns that live here rather than in the CSV, since they're
# properties of the topic, not of an individual NESA outcome code.)
TOPIC_CATALOGUE: Dict[str, Dict[str, Any]] = {
    "representing_numbers":    {"practice_area": "Number & Place Value",       "layout_hint": "list",      "default_count": 3},
    "vertical_addition":       {"practice_area": "Column Arithmetic",          "layout_hint": "grid_3col", "default_count": 6},
    "vertical_subtraction":    {"practice_area": "Column Arithmetic",          "layout_hint": "grid_3col", "default_count": 6},
    "vertical_multiplication": {"practice_area": "Column Arithmetic",          "layout_hint": "grid_3col", "default_count": 6},
    "long_division":           {"practice_area": "Column Arithmetic",          "layout_hint": "grid_3col", "default_count": 6},
    "fractions":                {"practice_area": "Fractions & Decimals",      "layout_hint": "list",      "default_count": 3},
    "sequences":                {"practice_area": "Patterns & Algebra",        "layout_hint": "list",      "default_count": 3},
    "algebra":                  {"practice_area": "Patterns & Algebra",        "layout_hint": "list",      "default_count": 3},
    "reading_time":             {"practice_area": "Measurement & Time",        "layout_hint": "list",      "default_count": 2},
    "date_duration":            {"practice_area": "Measurement & Time",        "layout_hint": "list",      "default_count": 2},
    "speed_distance":           {"practice_area": "Measurement & Time",        "layout_hint": "list",      "default_count": 2},
    "geometry_angles":          {"practice_area": "Geometry & Shape",          "layout_hint": "list",      "default_count": 2},
    "2d_shapes":                {"practice_area": "Geometry & Shape",          "layout_hint": "list",      "default_count": 3},
    "3d_objects":               {"practice_area": "Geometry & Shape",          "layout_hint": "list",      "default_count": 3},
    "data":                     {"practice_area": "Statistics & Probability",  "layout_hint": "list",      "default_count": 3},
    "chance":                   {"practice_area": "Statistics & Probability",  "layout_hint": "list",      "default_count": 3},
    "multiple_choice":          {"practice_area": "General Quiz",              "layout_hint": "list",      "default_count": 4},
}

PRACTICE_AREA_ORDER: List[str] = [
    "Number & Place Value", "Column Arithmetic", "Fractions & Decimals", "Patterns & Algebra",
    "Measurement & Time", "Geometry & Shape", "Statistics & Probability", "General Quiz",
]

STAGE_DEFAULT_DIFFICULTY: Dict[int, str] = {1: "easy", 2: "medium", 3: "hard"}

# Per-topic extra generator.py parameters, shown in the picker under a
# collapsible "Advanced options" disclosure. Topics not listed here only
# expose count/difficulty. Field "type" drives both the form control
# (index.html) and how app.py parses the submitted value back into config.yaml.
TOPIC_ADVANCED_FIELDS: Dict[str, List[Dict[str, Any]]] = {
    "vertical_addition": [
        {"name": "digits", "label": "Digits per number", "type": "int_select", "options": [2, 3, 4], "default": 3},
        {"name": "allow_carrying", "label": "Allow carrying", "type": "bool", "default": True},
    ],
    "vertical_subtraction": [
        {"name": "digits", "label": "Digits per number", "type": "int_select", "options": [2, 3, 4], "default": 3},
        {"name": "allow_borrowing", "label": "Allow borrowing", "type": "bool", "default": True},
    ],
    "vertical_multiplication": [
        {"name": "digits_top", "label": "Top number digits", "type": "int_select", "options": [1, 2, 3], "default": 2},
        {"name": "digits_bottom", "label": "Bottom number digits", "type": "int_select", "options": [1, 2], "default": 1},
        {"name": "times_table", "label": "Target times table(s)", "type": "times_table", "default": "",
         "help": "e.g. 3   or   2-4   or   2,3,5 — leave blank for fully random"},
    ],
    "long_division": [
        {"name": "digits_dividend", "label": "Dividend digits", "type": "int_select", "options": [2, 3, 4], "default": 3},
        {"name": "digits_divisor", "label": "Divisor digits", "type": "int_select", "options": [1, 2], "default": 1},
        {"name": "times_table", "label": "Target divisor(s)", "type": "times_table", "default": "",
         "help": "e.g. 4   or   2-4   or   2,3,5 — leave blank for fully random"},
        {"name": "allow_remainder", "label": "Allow remainders", "type": "bool", "default": False},
    ],
    "sequences": [
        {"name": "step_range", "label": "Step range (min–max)", "type": "int_range", "default": [3, 12]},
        {"name": "pattern_type", "label": "Pattern type", "type": "select",
         "options": ["arithmetic", "geometric"], "default": "arithmetic"},
    ],
    "fractions": [
        {"name": "op_type", "label": "Operation", "type": "select",
         "options": ["addition", "subtraction", "multiplication"], "default": "addition"},
    ],
    "2d_shapes": [
        {"name": "shapes", "label": "Specific shape(s)", "type": "shape_list", "default": "",
         "help": "e.g. hexagon  or  rhombus,trapezium — leave blank for random. "
                 "Easy: triangle, quadrilateral/square/rectangle, pentagon, hexagon, heptagon, octagon. "
                 "Medium: parallelogram, rhombus, trapezium. Hard: equilateral, isosceles, scalene."},
    ],
    "3d_objects": [
        {"name": "objects_3d", "label": "Specific object(s)", "type": "shape_list", "default": "",
         "help": "e.g. cube  or  cube,pyramid — leave blank for random. "
                 "Supported: cube, cuboid/rectangular prism, pyramid."},
    ],
}


def parse_times_table(raw: str):
    """Parses the picker's times-table text field into whatever generator.py
    expects: "3" -> 3, "2-4" -> [2, 3, 4], "2,3,5" -> [2, 3, 5], "" -> None."""
    raw = (raw or "").strip()
    if not raw:
        return None
    if "-" in raw:
        lo, _, hi = raw.partition("-")
        try:
            lo, hi = int(lo.strip()), int(hi.strip())
            if lo <= hi:
                return list(range(lo, hi + 1))
        except ValueError:
            pass
    if "," in raw:
        try:
            return [int(x.strip()) for x in raw.split(",") if x.strip()]
        except ValueError:
            return None
    try:
        return int(raw)
    except ValueError:
        return None


def parse_shape_list(raw: str):
    """Parses the picker's comma-separated shape/object names into a list for
    generator.py's `shapes` / `objects_3d` options: "" -> None, "hexagon" ->
    ["hexagon"], "rhombus, trapezium" -> ["rhombus", "trapezium"]."""
    raw = (raw or "").strip()
    if not raw:
        return None
    items = [s.strip() for s in raw.split(",") if s.strip()]
    return items or None


def format_shape_list(value) -> str:
    """Inverse of parse_shape_list, for pre-filling the picker from a saved config.yaml."""
    if not value:
        return ""
    if isinstance(value, list):
        return ", ".join(value)
    return str(value)


def format_times_table(value) -> str:
    """Inverse of parse_times_table, for pre-filling the picker from a saved config.yaml."""
    if value is None:
        return ""
    if isinstance(value, list):
        if not value:
            return ""
        sorted_vals = sorted(value)
        if sorted_vals == list(range(sorted_vals[0], sorted_vals[-1] + 1)) and len(sorted_vals) > 1:
            return f"{sorted_vals[0]}-{sorted_vals[-1]}"
        return ",".join(str(v) for v in value)
    return str(value)


def _load_csv_rows() -> List[Dict[str, str]]:
    if not os.path.exists(CSV_PATH):
        return []
    with open(CSV_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _outcomes_for_topic(rows: List[Dict[str, str]], topic: str) -> List[Dict[str, str]]:
    matches = []
    for row in rows:
        topics = [t.strip() for t in row.get("Topic", "").split(",") if t.strip()]
        if topic in topics:
            matches.append(row)
    return matches


def get_catalogue() -> Dict[str, List[Dict[str, Any]]]:
    """Groups the practice topics by Practice Area for the picker UI, each
    enriched with the NESA outcome codes/capabilities that apply, read from
    maths-curriculum-ks1_2_3.csv."""
    rows = _load_csv_rows()
    grouped: Dict[str, List[Dict[str, Any]]] = {area: [] for area in PRACTICE_AREA_ORDER}

    for topic, props in TOPIC_CATALOGUE.items():
        outcomes = _outcomes_for_topic(rows, topic)
        entry = {
            "topic": topic,
            "layout_hint": props["layout_hint"],
            "default_count": props["default_count"],
            "advanced_fields": TOPIC_ADVANCED_FIELDS.get(topic, []),
            "outcomes": [
                {
                    "key": o.get("Key", ""),
                    "stage": o.get("Stage", ""),
                    "capability": o.get("Capability", ""),
                    "difficulty": o.get("Difficulty", ""),
                }
                for o in outcomes
            ],
        }
        grouped.setdefault(props["practice_area"], []).append(entry)

    return grouped


def default_difficulty_for_stage(stage: int) -> str:
    try:
        return STAGE_DEFAULT_DIFFICULTY.get(int(stage), "medium")
    except (TypeError, ValueError):
        return "medium"
