# Mathematics Practice Workbook Generator

A dynamic, YAML-configurable pipeline to generate LaTeX mathematics practice workbooks and compile them into high-quality PDFs with worked solutions.

---

## 🚀 Features

- ⚙️ **Fully Dynamic Generation**: Automatically generate random formulas, numbers, sequence terms, clocks, angle diagrams, and word problems based on difficulty settings.
- 🎯 **Configurable Topics**: Select which sections and math topics to include in your workbook.
- 🎚️ **Times Table & Number Targeting**: Specific multipliers (`times_table: 3`) or divisors for targeted practice sheets.
- ✏️ **Blank Working Area**: Column arithmetic omits answer digits and carried values so students can complete the calculations by hand.
- 📐 **Customizable Working Space**: Configurable whitespace (`working_space: "3.5cm"`) per section or globally to give students ample room for working out.
- 📌 **Fixed Question Overrides**: Override random generation for specific questions with fixed numbers or custom LaTeX prompts.
- 🔑 **Automated Solution Keys**: Generates an aligned Worked Solutions & Answer Key section at the end of the PDF.

---

## ⚡ Quick Start

```bash
python3 build_workbook.py
```

Find your compiled PDF in `output/workbook.pdf`.

---

## 🛠️ Configuring `config.yaml`

### 1. Global & Section Whitespace Control

You can specify working space globally or per section (e.g. `2.5cm`, `3.5cm`, `4cm`):

```yaml
working_space: "3cm" # Global default whitespace for workings under questions

sections:
  - title: "1. Column Arithmetic"
    layout: "grid_3col"
    working_space: "3.5cm" # Per-section override for extra vertical working space
    topics:
      vertical_addition:
        count: 6
        digits: 3
        allow_carrying: true
```

---

### 2. Multiplier & Times Table Targeting

#### ✖️ Vertical Multiplication (`vertical_multiplication`)
Target a specific times table (e.g. 3 times table, or a list of tables `[2, 3, 4]`):

```yaml
vertical_multiplication:
  count: 6
  digits_top: 2
  times_table: 3 # Or multiplier: 3, or multipliers: [2, 3, 4]
  difficulty: "easy"
```

#### ➗ Long Division (`long_division`)
Target a specific divisor / times table (e.g. 4 times table divisor):

```yaml
long_division:
  count: 4
  times_table: 4 # Or divisor: 4, or divisors: [2, 3, 4, 5]
  difficulty: "medium"
  allow_remainder: false
```

---

### 3. Hiding Answers in Questions vs Worked Solutions

All column arithmetic questions (`vertical_addition`, `vertical_subtraction`, `vertical_multiplication`) hide both the carried digits and the result digits on the student worksheet using `xlop` phantom styling (`[carrystyle=\phantom,resultstyle=\phantom]`).

The full step-by-step answer and final calculated value are automatically populated on the **Answer Key & Solutions Guide** page appended at the end of the PDF.
