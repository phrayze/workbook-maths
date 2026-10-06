import random
import re
from typing import List, Optional, Dict, Any

from generator import Question

# Topics whose LaTeX prompt relies on TikZ diagrams or the xlop column-arithmetic
# package - neither renders in a plain browser, so these are excluded from the
# auto-generated online multiple-choice test (they still appear in the PDF
# workbook, which compiles the real LaTeX).
UNRENDERABLE_Q_TYPES = {"tikz", "xlop"}

# Topics whose correct answer is a name/category rather than a number - only used
# as a distractor source when the actual answer_value matches one of these words,
# so a numeric answer for the same topic (e.g. "how many sides") still falls
# through to the numeric distractor strategy below.
CATEGORY_BANKS: Dict[str, List[str]] = {
    "2d_shapes": ["Parallelogram", "Rhombus", "Trapezium", "Equilateral", "Isosceles", "Scalene"],
    "chance": ["Certain", "Likely", "Unlikely", "Impossible"],
    "data": ["Apples", "Bananas", "Oranges", "Grapes", "Pears"],
    "geometry_angles": ["Acute", "Right", "Obtuse", "Reflex"],
    "compass_directions": ["North", "East", "South", "West", "North-East", "South-East", "South-West", "North-West"],
}

_FRACTION_RE = re.compile(r"^\d+/\d+$")
_TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})$")
_NUM_RE = re.compile(r"^-?\d+(\.\d+)?$")


def _numeric_distractors(value: str, count: int) -> List[str]:
    n = float(value)
    is_int = n.is_integer()
    # Preserve zero-padded widths like "090" (compass bearings) - otherwise
    # the correct answer would be the only option visibly padded.
    zero_pad_width = len(value) if is_int and value.lstrip("-").startswith("0") and len(value.lstrip("-")) > 1 else 0
    magnitude = max(abs(n), 1)
    step = max(1, round(magnitude * 0.1))
    candidates = set()
    for delta in (step, -step, step * 2, -step * 2, 10, -10, 1, -1):
        val = n + delta
        if val == n or val < 0:
            continue
        candidates.add(val)
    # Digit-transposition: a common carrying/place-value slip for 2+ digit integers
    if is_int and abs(n) >= 10:
        digits = list(str(int(abs(n))))
        digits[0], digits[1] = digits[1], digits[0]
        swapped = int("".join(digits)) * (1 if n >= 0 else -1)
        if swapped != n:
            candidates.add(float(swapped))
    results = list(candidates)
    random.shuffle(results)
    out = []
    for v in results[:count]:
        if is_int:
            out.append(str(int(v)).zfill(zero_pad_width) if zero_pad_width else str(int(v)))
        else:
            out.append(f"{v:.2f}")
    return out


def _fraction_distractors(value: str, count: int) -> List[str]:
    num, den = (int(x) for x in value.split("/"))
    candidates = set()
    for delta in (1, -1, 2, -2):
        new_num = num + delta
        if 0 < new_num and new_num != num:
            candidates.add(f"{new_num}/{den}")
    if num and num != den:
        candidates.add(f"{den}/{num}")
    candidates.add(f"{num}/{den + 1}")
    candidates.discard(value)
    results = list(candidates)
    random.shuffle(results)
    return results[:count]


def _time_distractors(value: str, count: int) -> List[str]:
    h, m = (int(x) for x in value.split(":"))
    total = h * 60 + m
    candidates = set()
    for delta in (5, -5, 15, -15, 30, -30, 60, -60):
        new_total = (total + delta) % (24 * 60)
        nh, nm = divmod(new_total, 60)
        candidates.add(f"{nh:02d}:{nm:02d}")
    candidates.discard(value)
    results = list(candidates)
    random.shuffle(results)
    return results[:count]


def _categorical_distractors(topic: str, value: str, count: int) -> List[str]:
    bank = CATEGORY_BANKS.get(topic, [])
    options = [o for o in bank if o.lower() != value.strip().lower()]
    random.shuffle(options)
    return options[:count]


def make_distractors(question: Question, count: int = 3) -> List[str]:
    """Best-effort plausible wrong answers for a question's answer_value.
    Returns fewer than `count` (possibly zero) if no strategy applies cleanly -
    callers should treat that as "can't make a fair MCQ for this one"."""
    value = (question.answer_value or "").strip()
    if not value:
        return []

    bank = CATEGORY_BANKS.get(question.topic)
    if bank and any(value.lower() == b.lower() for b in bank):
        out = _categorical_distractors(question.topic, value, count)
        if len(out) >= count:
            return out

    if _FRACTION_RE.match(value):
        out = _fraction_distractors(value, count)
        if len(out) >= count:
            return out

    if _TIME_RE.match(value):
        out = _time_distractors(value, count)
        if len(out) >= count:
            return out

    if _NUM_RE.match(value):
        out = _numeric_distractors(value, count)
        if len(out) >= count:
            return out

    return []


_MCQ_ITEM_RE = re.compile(r"\\item\s+(.*)")
_OPTION_LETTER_RE = re.compile(r"Option\s*\(?\s*([A-D])\s*\)?", re.IGNORECASE)

# Our generator.py prompts/solutions are authored as real LaTeX for the PDF
# pipeline, so plain prose freely uses commands like \textbf{} or a \\[1em]
# forced line break *outside* any $...$ math. MathJax in the browser only
# ever processes the $...$ portions - everything else is dumped as literal
# text - so these would otherwise show up as raw backslashes/braces on the
# quiz page. _MATH_SPLIT_RE walks the string keeping $...$ math spans intact
# (for MathJax) while the prose in between gets converted to plain HTML.
_MATH_SPLIT_RE = re.compile(r'(\$(?:\\\$|[^$])*\$)')
_LINEBREAK_RE = re.compile(r'\\\\(?:\[[^\]]*\])?')
_TEXTBF_RE = re.compile(r'\\textbf\{([^{}]*)\}')
_TEXTIT_RE = re.compile(r'\\textit\{([^{}]*)\}|\\emph\{([^{}]*)\}')
_UNDERLINE_RE = re.compile(r'\\underline\{([^{}]*)\}')


def _prose_segment_to_html(segment: str) -> str:
    segment = _LINEBREAK_RE.sub('<br>', segment)
    segment = _TEXTBF_RE.sub(r'<strong>\1</strong>', segment)
    segment = _TEXTIT_RE.sub(lambda m: f"<em>{m.group(1) or m.group(2)}</em>", segment)
    segment = _UNDERLINE_RE.sub(r'<u>\1</u>', segment)
    return segment


def prepare_for_web(text: str) -> str:
    """Converts the plain-prose LaTeX our prompts/solutions use outside of
    $...$ math mode into HTML, leaving math spans untouched for MathJax."""
    if not text:
        return text
    parts = _MATH_SPLIT_RE.split(text)
    return "".join(part if i % 2 == 1 else _prose_segment_to_html(part) for i, part in enumerate(parts))


def _parse_native_mcq(question: Question) -> Optional[Dict[str, Any]]:
    """The multiple_choice topic already renders its own (\\Alph*)-labelled
    \\begin{enumerate} options in prompt_tex. Pull the question text + options
    out of that LaTeX so the quiz page can render plain radio buttons instead
    of raw \\begin{enumerate} markup."""
    prompt = question.prompt_tex
    if "\\begin{enumerate}" not in prompt:
        return None
    q_text, _, rest = prompt.partition("\\begin{enumerate}")
    q_text = q_text.strip()
    options = [opt.strip() for opt in _MCQ_ITEM_RE.findall(rest)]
    if not options:
        return None

    letter = (question.answer_value or "").strip().upper()
    if not letter or not letter.isalpha():
        m = _OPTION_LETTER_RE.search(question.solution_tex or "")
        letter = m.group(1).upper() if m else ""

    if not letter:
        return None
    idx = ord(letter) - ord("A")
    if not (0 <= idx < len(options)):
        return None

    return {"prompt_tex": q_text, "options": options, "correct_index": idx}


def to_mcq(question: Question, num_options: int = 4) -> Optional[Dict[str, Any]]:
    """Convert a generated Question into a multiple-choice presentation for the
    online test. Returns None when the question can't fairly be turned into an
    MCQ (TikZ/xlop diagrams that won't render in a browser, an answer shape
    with no reliable distractor strategy, or - for the native multiple_choice
    topic - options/correct letter that couldn't be confidently parsed)."""
    if question.q_type in UNRENDERABLE_Q_TYPES:
        return None

    if question.q_type == "mcq":
        parsed = _parse_native_mcq(question)
        if parsed is None:
            return None
        return {
            "id": question.id,
            "topic": question.topic,
            "outcome_code": question.outcome_code,
            "prompt_tex": prepare_for_web(parsed["prompt_tex"]),
            "is_native_mcq": True,
            "options": [prepare_for_web(o) for o in parsed["options"]],
            "correct_index": parsed["correct_index"],
            "correct_letter": question.answer_value or None,
            "solution_tex": prepare_for_web(question.solution_tex),
        }

    value = (question.answer_value or "").strip()
    if not value:
        return None

    distractors = make_distractors(question, count=num_options - 1)
    if len(distractors) < num_options - 1:
        return None

    options = distractors[: num_options - 1] + [value]
    random.shuffle(options)
    correct_index = options.index(value)

    return {
        "id": question.id,
        "topic": question.topic,
        "outcome_code": question.outcome_code,
        "prompt_tex": prepare_for_web(question.prompt_tex),
        "is_native_mcq": False,
        "options": [prepare_for_web(o) for o in options],
        "correct_index": correct_index,
        "correct_letter": None,
        "solution_tex": prepare_for_web(question.solution_tex),
    }


def build_mcq_set(questions: List[Question], num_options: int = 4) -> List[Dict[str, Any]]:
    """Convert as many questions as possible into MCQs, skipping any that can't
    be fairly presented that way (see to_mcq)."""
    mcqs = []
    for q in questions:
        mcq = to_mcq(q, num_options=num_options)
        if mcq is not None:
            mcqs.append(mcq)
    return mcqs
