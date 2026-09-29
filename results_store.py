import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

HISTORY_PATH = os.path.join(os.path.dirname(__file__), "results", "history.jsonl")
WEAK_ACCURACY_THRESHOLD = 0.7
MIN_ATTEMPTED_FOR_SUGGESTION = 2  # ignore topics barely touched before flagging them as weak


def _ensure_dir() -> None:
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)


def record_attempt(student: str, stage: int, topic_scores: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
    """topic_scores: {topic: {"correct": int, "attempted": int, "not_attempted": int}}.
    Questions left unanswered when the test is ended early are tracked as
    not_attempted and don't count against accuracy - accuracy is always
    correct/attempted. Appends one JSON line to results/history.jsonl."""
    _ensure_dir()
    overall_correct = sum(v.get("correct", 0) for v in topic_scores.values())
    overall_attempted = sum(v.get("attempted", 0) for v in topic_scores.values())
    overall_not_attempted = sum(v.get("not_attempted", 0) for v in topic_scores.values())

    entry = {
        "student": student or "Student",
        "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "stage": int(stage),
        "topics": {
            topic: {
                "correct": v.get("correct", 0),
                "attempted": v.get("attempted", 0),
                "not_attempted": v.get("not_attempted", 0),
                "accuracy": round(v["correct"] / v["attempted"], 3) if v.get("attempted") else 0.0,
            }
            for topic, v in topic_scores.items()
        },
        "overall": {
            "correct": overall_correct,
            "attempted": overall_attempted,
            "not_attempted": overall_not_attempted,
            "accuracy": round(overall_correct / overall_attempted, 3) if overall_attempted else 0.0,
        },
    }
    with open(HISTORY_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def load_history(student: Optional[str] = None) -> List[Dict[str, Any]]:
    if not os.path.exists(HISTORY_PATH):
        return []
    entries = []
    with open(HISTORY_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if student is None or entry.get("student") == student:
                entries.append(entry)
    return entries


def suggest_weak_topics(
    student: str, stage: int, threshold: float = WEAK_ACCURACY_THRESHOLD, lookback: int = 5
) -> Dict[str, float]:
    """Looks at the student's most recent attempts for this stage and returns
    {topic: accuracy} for topics averaging below `threshold` across the last
    `lookback` attempts (only counting questions actually attempted). Empty
    dict if there's no history yet - this is a suggestion surfaced in the
    picker UI, never applied automatically."""
    entries = [e for e in load_history(student) if e.get("stage") == int(stage)][-lookback:]
    if not entries:
        return {}

    totals: Dict[str, List[int]] = {}
    for entry in entries:
        for topic, scores in entry.get("topics", {}).items():
            bucket = totals.setdefault(topic, [0, 0])
            bucket[0] += scores.get("correct", 0)
            bucket[1] += scores.get("attempted", scores.get("total", 0))

    weak = {}
    for topic, (correct, attempted) in totals.items():
        if attempted < MIN_ATTEMPTED_FOR_SUGGESTION:
            continue
        accuracy = correct / attempted
        if accuracy < threshold:
            weak[topic] = round(accuracy, 3)
    return weak
