import os
import traceback
from typing import Any, Dict, List

import yaml
from flask import Flask, jsonify, redirect, render_template, request, send_file, url_for

from build_workbook import build_pdf
from generator import QuestionBank, build_question_for_topic
from mcq_utils import build_mcq_set
import question_bank
import results_store

app = Flask(__name__)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")
PDF_OUTPUT_PATH = "output/web_workbook.pdf"


def _load_existing_config() -> Dict[str, Any]:
    if not os.path.exists(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError:
        return {}


def _existing_topic_settings(config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """topic -> its full saved topic_cfg dict (count, difficulty, and any
    advanced params like digits/times_table/step_range) pulled out of a
    previously saved config.yaml, used to pre-fill the picker form."""
    settings: Dict[str, Dict[str, Any]] = {}
    for section in config.get("sections", []) or []:
        for topic, topic_cfg in (section.get("topics") or {}).items():
            if isinstance(topic_cfg, dict):
                settings[topic] = topic_cfg
    return settings


def _advanced_field_value(field: Dict[str, Any], saved_cfg: Dict[str, Any]):
    """Current value for one advanced-options field, formatted for the HTML
    form: saved config.yaml value if present, else the field's default."""
    raw = saved_cfg.get(field["name"], field["default"])
    if field["type"] == "times_table":
        return question_bank.format_times_table(raw)
    if field["type"] == "shape_list":
        return question_bank.format_shape_list(raw)
    return raw


def _build_picker_context(student: str = "") -> Dict[str, Any]:
    config = _load_existing_config()
    stage = int(config.get("stage", 2))
    existing = _existing_topic_settings(config)
    default_diff = question_bank.default_difficulty_for_stage(stage)

    catalogue = question_bank.get_catalogue()
    for area_entries in catalogue.values():
        for entry in area_entries:
            saved = existing.get(entry["topic"])
            entry["enabled"] = saved is not None or not existing  # nothing saved yet -> default everything on
            entry["count"] = saved["count"] if saved else entry["default_count"]
            entry["difficulty"] = saved["difficulty"] if saved else default_diff
            entry["advanced_values"] = {
                field["name"]: _advanced_field_value(field, saved or {})
                for field in entry["advanced_fields"]
            }

    weak_topics = results_store.suggest_weak_topics(student, stage) if student else {}

    return {
        "catalogue": catalogue,
        "areas": question_bank.PRACTICE_AREA_ORDER,
        "stage": stage,
        "student": student,
        "seed": config.get("seed") or "",
        "weak_topics": weak_topics,
    }


@app.route("/", methods=["GET"])
def index():
    student = request.args.get("student", "")
    return render_template("index.html", error=None, **_build_picker_context(student))


def _read_advanced_field(field: Dict[str, Any], topic: str, form) -> Any:
    name = f"adv_{topic}_{field['name']}"
    field_type = field["type"]

    if field_type == "bool":
        return form.get(name) == "on"
    if field_type == "int_select":
        try:
            return int(form.get(name, field["default"]))
        except (TypeError, ValueError):
            return field["default"]
    if field_type == "select":
        return form.get(name, field["default"])
    if field_type == "times_table":
        return question_bank.parse_times_table(form.get(name, ""))
    if field_type == "shape_list":
        return question_bank.parse_shape_list(form.get(name, ""))
    if field_type == "int_range":
        try:
            lo = int(form.get(f"{name}_min", field["default"][0]))
            hi = int(form.get(f"{name}_max", field["default"][1]))
        except (TypeError, ValueError):
            return field["default"]
        return [min(lo, hi), max(lo, hi)]
    return form.get(name)


def _save_config_from_form(form) -> Dict[str, Any]:
    stage = int(form.get("stage", 2))
    seed_raw = (form.get("seed") or "").strip()
    seed = int(seed_raw) if seed_raw.lstrip("-").isdigit() else None

    catalogue = question_bank.get_catalogue()
    sections: List[Dict[str, Any]] = []

    for area in question_bank.PRACTICE_AREA_ORDER:
        topics_cfg: Dict[str, Any] = {}
        layout_hint = "list"
        for entry in catalogue[area]:
            topic = entry["topic"]
            if form.get(f"enable_{topic}") != "on":
                continue
            try:
                count = int(form.get(f"count_{topic}", entry["default_count"]))
            except ValueError:
                count = entry["default_count"]
            if count <= 0:
                continue
            difficulty = form.get(f"difficulty_{topic}", "medium")
            topic_cfg: Dict[str, Any] = {"count": count, "difficulty": difficulty}
            for field in entry["advanced_fields"]:
                value = _read_advanced_field(field, topic, form)
                if value is None:
                    continue  # e.g. blank times_table -> fully random, matches generator.py default
                topic_cfg[field["name"]] = value
            topics_cfg[topic] = topic_cfg
            layout_hint = entry["layout_hint"]

        if not topics_cfg:
            continue

        section: Dict[str, Any] = {
            "title": area,
            "description": "",
            "working_space": "3.5cm" if layout_hint == "grid_3col" else "2.5cm",
            "topics": topics_cfg,
        }
        if layout_hint != "list":  # "list" is generate_workbook_pipeline's own default - no need to spell it out
            section["layout"] = layout_hint
        sections.append(section)

    config = {
        "title": f"Stage {stage} Mathematics Practice Workbook",
        "subtitle": f"NSW Curriculum Aligned (NESA 2022 Stage {stage})",
        "stage": stage,
        "header_left": "NSW Primary Mathematics Practice",
        "seed": seed,
        "include_solutions": True,
        "font_size": "14pt",
        "working_space": "2.5cm",
        "sections": sections,
    }

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, sort_keys=False, allow_unicode=True)

    return config


@app.route("/build", methods=["POST"])
def build():
    student = request.form.get("student", "").strip()
    action = request.form.get("action", "pdf")

    try:
        _save_config_from_form(request.form)
    except Exception as exc:  # noqa: BLE001 - surface any config error to the picker page
        return render_template("index.html", error=str(exc), **_build_picker_context(student))

    if action == "quiz":
        return redirect(url_for("quiz", student=student))

    try:
        build_pdf(config_path=CONFIG_PATH, output_pdf=PDF_OUTPUT_PATH)
    except Exception as exc:  # noqa: BLE001 - latexmk/pdflatex failure, etc.
        traceback.print_exc()
        return render_template(
            "index.html",
            error=f"PDF generation failed: {exc}",
            **_build_picker_context(student),
        )

    return send_file(PDF_OUTPUT_PATH, as_attachment=False, download_name="workbook.pdf")


def _build_question_pool(config: Dict[str, Any]) -> list:
    qb = QuestionBank(seed=config.get("seed"))
    questions = []
    global_id = 1
    for section in config.get("sections", []) or []:
        for topic, topic_cfg in (section.get("topics") or {}).items():
            if isinstance(topic_cfg, int):
                topic_cfg = {"count": topic_cfg}
            count = topic_cfg.get("count", 1)
            for i in range(count):
                q = build_question_for_topic(qb, topic, topic_cfg, index=i)
                q.id = global_id
                global_id += 1
                questions.append(q)
    return questions


@app.route("/quiz", methods=["GET"])
def quiz():
    student = request.args.get("student", "Student").strip() or "Student"
    config = _load_existing_config()
    if not config:
        return redirect(url_for("index"))

    stage = int(config.get("stage", 2))
    questions = _build_question_pool(config)
    mcqs = build_mcq_set(questions)

    return render_template(
        "quiz.html",
        student=student,
        stage=stage,
        mcqs=mcqs,
        total_generated=len(questions),
        total_mcq=len(mcqs),
    )


@app.route("/quiz/submit", methods=["POST"])
def quiz_submit():
    data = request.get_json(force=True)
    student = (data.get("student") or "Student").strip()
    stage = int(data.get("stage", 2))
    topic_scores = data.get("topic_scores", {})

    entry = results_store.record_attempt(student, stage, topic_scores)
    return jsonify(entry)


@app.route("/history", methods=["GET"])
def history():
    student = request.args.get("student", "").strip() or None
    entries = list(reversed(results_store.load_history(student)))
    return render_template("history.html", entries=entries, student=student or "")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
