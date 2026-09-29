import os
import sys
import argparse
import subprocess
from datetime import datetime
import jinja2
import yaml
from generator import generate_workbook_pipeline

def setup_jinja_env():
    return jinja2.Environment(
        block_start_string=r'\BLOCK{',
        block_end_string='}',
        variable_start_string=r'\VAR{',
        variable_end_string='}',
        comment_start_string=r'\#{',
        comment_end_string='}',
        line_statement_prefix='%%',
        line_comment_prefix='%#',
        trim_blocks=True,
        autoescape=False,
        loader=jinja2.FileSystemLoader(os.path.curdir)
    )

def get_default_output_path(output_path: str = None) -> str:
    today_str = datetime.now().strftime("%Y%m%d")
    if not output_path or output_path == "output/workbook.pdf":
        return f"output/{today_str}_workbook.pdf"
    if os.path.isdir(output_path) or output_path.endswith("/"):
        return os.path.join(output_path, f"{today_str}_workbook.pdf")
    return output_path

def build_pdf(config_path: str = "config.yaml", output_pdf: str = None, seed_override: int = None):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file '{config_path}' not found.")

    output_pdf = get_default_output_path(output_pdf)

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    if seed_override is not None:
        config["seed"] = seed_override

    # Run generator pipeline
    workbook_data = generate_workbook_pipeline(config)

    # Render LaTeX template
    env = setup_jinja_env()
    template = env.get_template("template.tex.j2")
    rendered_tex = template.render(**workbook_data)

    output_dir = os.path.dirname(output_pdf) or "output"
    os.makedirs(output_dir, exist_ok=True)
    
    base_name = os.path.splitext(os.path.basename(output_pdf))[0]
    output_tex = os.path.join(output_dir, f"{base_name}.tex")

    with open(output_tex, "w", encoding="utf-8") as f:
        f.write(rendered_tex)

    print(f"[*] Generated LaTeX source: {output_tex}")
    print("[*] Compiling PDF with latexmk...")

    # Compile with latexmk
    cmd = ["latexmk", "-pdf", "-interaction=nonstopmode", f"-output-directory={output_dir}", output_tex]
    subprocess.run(cmd, check=True)

    # Clean intermediate files
    subprocess.run(["latexmk", "-c", f"-output-directory={output_dir}", output_tex], check=False)

    print(f"[+] Successfully generated PDF: {os.path.join(output_dir, base_name + '.pdf')}")

def main():
    parser = argparse.ArgumentParser(description="Dynamic Mathematics Practice Workbook Generator")
    parser.add_argument("--config", "-c", default="config.yaml", help="Path to config.yaml file")
    parser.add_argument("--output", "-o", default=None, help="Output PDF file path (defaults to output/YYYYMMDD_workbook.pdf)")
    parser.add_argument("--seed", "-s", type=int, default=None, help="Random seed override for reproducible generation")

    args = parser.parse_args()
    build_pdf(config_path=args.config, output_pdf=args.output, seed_override=args.seed)

if __name__ == "__main__":
    main()