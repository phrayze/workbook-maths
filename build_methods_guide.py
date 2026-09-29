import argparse
import os
import subprocess

from build_workbook import setup_jinja_env
import question_bank

N = 12  # Times/division tables cover 1..N


def build_grid(n: int = N):
    return [[i * j for j in range(1, n + 1)] for i in range(1, n + 1)]


def build_topic_outcomes():
    """topic -> [{key, stage, capability, difficulty}], flattened from the
    Practice Area catalogue so the guide can show each topic's NESA outcome
    codes without duplicating that mapping by hand."""
    catalogue = question_bank.get_catalogue()
    topic_outcomes = {}
    for entries in catalogue.values():
        for entry in entries:
            topic_outcomes[entry["topic"]] = entry["outcomes"]
    return topic_outcomes


def build_methods_guide(output_pdf: str = "output/methods_guide.pdf"):
    env = setup_jinja_env()
    template = env.get_template("methods_guide.tex.j2")

    rendered = template.render(
        grid=build_grid(N),
        n=N,
        topic_outcomes=build_topic_outcomes(),
    )

    output_dir = os.path.dirname(output_pdf) or "output"
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(output_pdf))[0]
    output_tex = os.path.join(output_dir, f"{base_name}.tex")

    with open(output_tex, "w", encoding="utf-8") as f:
        f.write(rendered)

    print(f"[*] Generated LaTeX source: {output_tex}")
    print("[*] Compiling PDF with latexmk...")

    cmd = ["latexmk", "-pdf", "-interaction=nonstopmode", f"-output-directory={output_dir}", output_tex]
    subprocess.run(cmd, check=True)
    subprocess.run(["latexmk", "-c", f"-output-directory={output_dir}", output_tex], check=False)

    print(f"[+] Successfully generated PDF: {os.path.join(output_dir, base_name + '.pdf')}")


def main():
    parser = argparse.ArgumentParser(description="Build the Mathematics Methods & Reference Guide")
    parser.add_argument("--output", "-o", default="output/methods_guide.pdf", help="Output PDF path")
    args = parser.parse_args()
    build_methods_guide(output_pdf=args.output)


if __name__ == "__main__":
    main()
