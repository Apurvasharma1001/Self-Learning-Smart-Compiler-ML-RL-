# 🧠 Self-Learning Smart Compiler (ML + RL)

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=for-the-badge&logo=flask&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4+-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![License](https://img.shields.io/badge/License-Educational-blue?style=for-the-badge)

**A complete end-to-end compiler for a C-like language (Mini-C) with intelligent optimization selection powered by Machine Learning and Reinforcement Learning.**

*The compiler doesn't just optimize code — it **learns** to pick the best optimization strategy for each unique program.*

[Quick Start](#-quick-start) · [Features](#-features) · [Architecture](#%EF%B8%8F-architecture) · [Web Interface](#-web-interface) · [ML/RL Details](#-mlrl-optimization-details) · [Results](#-optimization-results)

</div>

---

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [CLI Usage](#-cli-usage)
- [Web Interface](#-web-interface)
- [Architecture](#%EF%B8%8F-architecture)
- [Project Structure](#-project-structure)
- [Compiler Pipeline](#-compiler-pipeline)
- [Optimization Passes](#-optimization-passes)
- [ML/RL Optimization Details](#-mlrl-optimization-details)
- [Mini-C Language](#-mini-c-language)
- [Optimization Results](#-optimization-results)
- [Testing](#-testing)
- [Technologies](#-technologies)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### Compiler Core
- **Full Compiler Pipeline** — Source Code → Lexer → Parser → AST → Three-Address Code (IR) → Optimizer → Pseudo-Assembly
- **PLY-based Lexer & Parser** — Tokenizer with 30+ token types; LALR(1) parser producing a rich AST with 20+ node types
- **Three-Address Code IR** — 19 instruction types for a clean intermediate representation
- **Pseudo-Assembly Code Generation** — Register allocation and instruction selection for x86-64-style output

### Smart Optimization
- **5 Classical Optimization Passes** — Constant Folding, Dead Code Elimination, Common Sub-expression Elimination (CSE), Copy Propagation, Loop-Invariant Code Motion (LICM)
- **ML-Based Optimization** — A RandomForest classifier predicts the optimal pass combination from 12 IR features
- **RL-Based Optimization** — A Q-Learning agent learns adaptive optimization strategies through 300 training episodes across 20 programs
- **3 Compilation Modes** — `normal` (all passes), `ml` (ML-predicted passes), `rl` (RL-learned passes)

### Developer Experience
- **Interactive Web Interface** — Browser-based playground with a CodeMirror editor, real-time compilation, metrics dashboard, and side-by-side mode comparison
- **Full CLI** — Compile, compare, train, test, and launch the web UI from the command line
- **12 Sample Programs** — Covering arithmetic, recursion, arrays, sorting, control flow, and more

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### 1. Clone the Repository

```bash
git clone https://github.com/Apurvasharma1001/Self-Learning-Smart-Compiler-ML-RL-.git
cd Self-Learning-Smart-Compiler-ML-RL-
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install ply flask scikit-learn numpy pytest
```

### 3. Train the ML & RL Models

```bash
python train_models.py
```

> **Note:** Pre-trained model files (`trained_model.json`, `trained_model_model.pkl`, `q_table.json`) are included in the repo. You can skip this step if you just want to try the compiler.

### 4. Launch the Web Interface

```bash
python main.py web
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

### 5. Or Use the CLI

```bash
python main.py compile tests/programs/fibonacci.mc --mode ml
```

---

## 💻 CLI Usage

```bash
# Compile a file with default (normal) mode
python main.py compile <file>

# Compile with ML-predicted optimization
python main.py compile <file> --mode ml

# Compile with RL-learned optimization
python main.py compile <file> --mode rl

# Compare all three modes side by side
python main.py compare <file>

# Train ML and RL models from scratch
python main.py train

# Start the web interface (default port: 5000)
python main.py web
python main.py web --port 8080

# Run all test suites
python main.py test
```

### Example: Comparing Modes

```bash
$ python main.py compare tests/programs/constant_heavy.mc

============================================================
COMPILATION COMPARISON
============================================================

--- NORMAL ---
  TAC: 13 -> 1 instructions
  ASM: 3 instructions
  Time: 12ms
  Improvement: 92.3%
  Passes: constant_folding, dead_code, cse, copy_propagation, licm

--- ML ---
  TAC: 13 -> 1 instructions
  ASM: 3 instructions
  Time: 8ms
  Improvement: 92.3%
  Passes: constant_folding, dead_code

--- RL ---
  TAC: 13 -> 1 instructions
  ASM: 3 instructions
  Time: 6ms
  Improvement: 92.3%
  Passes: constant_folding, dead_code
```

---

## 🌐 Web Interface

The web interface provides an interactive playground for writing, compiling, and analyzing Mini-C programs.

**Features:**
- **CodeMirror Editor** — Syntax-highlighted code editor with sample programs
- **One-click Compilation** — Compile in Normal, ML, or RL mode
- **Metrics Dashboard** — View TAC instruction counts, assembly output, optimization percentages
- **Mode Comparison** — Compare all three modes side-by-side with visual bar charts
- **Sample Programs** — Preloaded programs (Fibonacci, GCD, Factorial, Bubble Sort, etc.)

```bash
python main.py web
# Open http://localhost:5000
```

---

## 🏗️ Architecture

```
┌─────────────┐    ┌──────────┐    ┌──────────┐    ┌───────┐    ┌──────────────┐    ┌───────────┐
│ Source Code  │───▶│  Lexer   │───▶│  Parser  │───▶│  AST  │───▶│ TAC (IR)     │───▶│ Assembly  │
│  (.mc file)  │    │  (PLY)   │    │  (PLY)   │    │       │    │ Generator    │    │ Codegen   │
└─────────────┘    └──────────┘    └──────────┘    └───────┘    └──────┬───────┘    └───────────┘
                                                                       │
                                                                ┌──────▼───────┐
                                                                │  Optimizer   │
                                                                │  PassManager │
                                                                ├──────────────┤
                                                                │ • Const Fold │
                                                                │ • Dead Code  │
                                                                │ • CSE        │
                                                                │ • Copy Prop  │
                                                                │ • LICM       │
                                                                └──────┬───────┘
                                                                       │
                                                       ┌───────────────┼───────────────┐
                                                       │               │               │
                                                 ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
                                                 │  Normal    │  │  ML Model │  │  RL Agent │
                                                 │ (all pass) │  │ (predict) │  │ (Q-table) │
                                                 └───────────┘  └───────────┘  └───────────┘
```

### How the Smart Pipeline Works

1. **Parse** the input Mini-C program into an AST
2. **Generate** Three-Address Code (TAC) from the AST
3. **Extract features** from the TAC (instruction counts, variable usage, loop depth, etc.)
4. **Select optimization passes** based on the chosen mode:
   - **Normal**: applies all 5 passes sequentially
   - **ML**: RandomForest classifier predicts which passes will be effective
   - **RL**: Q-Learning agent selects passes based on learned Q-values
5. **Apply** selected passes via the PassManager
6. **Generate** pseudo-assembly from the optimized TAC

---

## 📁 Project Structure

```
mini-compiler/
├── main.py                      # CLI entry point (compile, compare, train, web, test)
├── train_models.py              # ML/RL training script with 20 training programs
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore rules
│
├── lexer/                       # Phase 2: Tokenizer
│   └── lexer.py                 #   PLY-based lexer, 30+ token types
│
├── parser/                      # Phase 3: LALR(1) Parser
│   └── parser.py                #   PLY-based parser → AST
│
├── ast_nodes/                   # Phase 3: AST Node Definitions
│   └── nodes.py                 #   20+ node types using @dataclass
│
├── ir/                          # Phase 4: Intermediate Representation
│   └── tac_generator.py         #   Three-Address Code generator (19 instruction types)
│
├── optimizer/                   # Phases 6–9: Optimization Engine
│   ├── __init__.py              #   PassManager — applies passes in sequence
│   ├── passes/                  #   Classical optimization passes
│   │   ├── constant_folding.py  #     Evaluate constant expressions at compile time
│   │   ├── dead_code.py         #     Remove unused variables and unreachable code
│   │   ├── cse.py               #     Eliminate redundant sub-expression computations
│   │   ├── copy_propagation.py  #     Replace copies with original variables
│   │   └── loop_optimization.py #     Hoist loop-invariant computations
│   ├── ml/                      #   Machine Learning optimization
│   │   ├── feature_extractor.py #     12-feature IR feature extractor
│   │   ├── model.py             #     RandomForest classifier + training pipeline
│   │   ├── trained_model.json   #     Saved model metadata
│   │   └── trained_model_model.pkl #  Saved sklearn model (pickle)
│   └── rl/                      #   Reinforcement Learning optimization
│       ├── q_agent.py           #     Q-Learning agent (ε-greedy, decay)
│       └── q_table.json         #     Learned Q-table (21 states)
│
├── codegen/                     # Phase 5: Code Generation
│   └── asm_generator.py         #   Pseudo-assembly output (x86-64 style)
│
├── runtime/                     # Phase 9: Smart Pipeline
│   └── pipeline.py              #   End-to-end CompilerPipeline class
│
├── web/                         # Phase 10: Web Interface
│   ├── app.py                   #   Flask application with REST API
│   └── templates/
│       └── index.html           #   Interactive playground (CodeMirror + Chart.js)
│
├── tests/                       # Phase 11: Testing
│   ├── __init__.py
│   ├── programs/                #   12 sample Mini-C programs
│   │   ├── arithmetic.mc
│   │   ├── fibonacci.mc
│   │   ├── factorial.mc
│   │   ├── gcd.mc
│   │   ├── bubble_sort.mc
│   │   ├── array_sum.mc
│   │   ├── prime_check.mc
│   │   ├── matrix_mult.mc
│   │   ├── nested_control.mc
│   │   ├── constant_heavy.mc
│   │   ├── pointer_ops.mc
│   │   └── struct_point.mc
│   ├── test_pipeline_quick.py
│   ├── test_optimizer_quick.py
│   ├── test_smart_pipeline.py
│   ├── test_interpreter.py
│   └── test_optimization_demo.py
│
├── docs/                        # Documentation
│   └── language_spec.md         #   Full Mini-C language specification (EBNF grammar)
│
└── logs/
    └── PROGRESS.md              #   Development progress tracker (13 phases)
```

---

## 🔄 Compiler Pipeline

### Phase 1 — Lexical Analysis (Lexer)
The PLY-based lexer tokenizes Mini-C source code into 30+ token types including keywords (`int`, `float`, `if`, `while`, `return`, `struct`), operators, literals, and identifiers.

### Phase 2 — Syntax Analysis (Parser)
An LALR(1) parser consumes tokens and produces an Abstract Syntax Tree (AST) with 20+ node types defined as Python `@dataclass` classes (e.g., `FunctionDef`, `IfStatement`, `BinaryOp`, `WhileLoop`, `ForLoop`, `ArrayAccess`).

### Phase 3 — IR Generation (Three-Address Code)
The AST is walked to generate Three-Address Code (TAC) — a flat list of instructions with at most 3 operands each. Supports 19 instruction types including `ASSIGN`, `BINOP`, `GOTO`, `IF_FALSE`, `CALL`, `RETURN`, `LABEL`, `PARAM`, and more.

### Phase 4 — Optimization
The PassManager applies selected optimization passes (see below). The key innovation is **how passes are selected** — via ML prediction or RL-learned policy.

### Phase 5 — Code Generation
Optimized TAC is translated to pseudo-assembly instructions with register allocation, producing x86-64-style output.

---

## ⚡ Optimization Passes

| Pass | Description | Example |
|------|-------------|---------|
| **Constant Folding** | Evaluates constant expressions at compile time | `a = 3 + 5` → `a = 8` |
| **Dead Code Elimination** | Removes variables that are never read | `int unused = 30;` → *(removed)* |
| **Common Sub-expression Elimination (CSE)** | Reuses previously computed expressions | `c = a+b; d = a+b` → `c = a+b; d = c` |
| **Copy Propagation** | Replaces copy chains with the original | `b = a; c = b` → `c = a` |
| **Loop-Invariant Code Motion (LICM)** | Hoists invariant computations out of loops | Moves `x = a * b` before the loop if `a`, `b` are unchanged |

---

## 🤖 ML/RL Optimization Details

### ML Model — RandomForest Classifier

**Goal:** Predict which optimization passes will be effective for a given program.

**Feature Extraction (12 features):**

| Feature | Description |
|---------|-------------|
| `total_instructions` | Total number of TAC instructions |
| `assign_count` | Number of assignment instructions |
| `binop_count` | Number of binary operation instructions |
| `goto_count` | Number of goto/jump instructions |
| `if_count` | Number of conditional branch instructions |
| `call_count` | Number of function call instructions |
| `return_count` | Number of return instructions |
| `label_count` | Number of label instructions |
| `param_count` | Number of parameter instructions |
| `unique_vars` | Number of unique variables used |
| `unique_temps` | Number of unique temporaries generated |
| `constant_ratio` | Ratio of constants to total operands |

**Training:**
- 20 diverse training programs × 32 pass combinations = 640 training samples
- The model learns which feature patterns map to which pass combinations
- Trained using scikit-learn's `RandomForestClassifier`

---

### RL Agent — Q-Learning

**Goal:** Learn an optimal pass selection policy through trial and error.

**Design:**
- **States (21):** Discretized IR feature vectors (instruction count buckets × constant ratio buckets)
- **Actions (32):** All possible subsets of the 5 optimization passes
- **Reward:** Percentage reduction in TAC instruction count after applying selected passes
- **Training:** 300 episodes × 20 programs with ε-greedy exploration

**Hyperparameters:**

| Parameter | Value |
|-----------|-------|
| Learning rate (α) | 0.2 |
| Discount factor (γ) | 0.95 |
| Initial ε | 1.0 |
| ε decay | 0.99 |
| Minimum ε | 0.05 |
| Training episodes | 300 |

**Key Insight:** The RL agent often converges to selecting only the passes that matter (e.g., `constant_folding` + `dead_code` for constant-heavy programs), avoiding unnecessary overhead from passes like LICM when no loops exist.

---

## 📝 Mini-C Language

Mini-C is a statically-typed, imperative language — a subset of C designed for educational compiler construction.

### Supported Features

| Feature | Syntax |
|---------|--------|
| **Types** | `int`, `float`, `void`, `bool`, `char` |
| **Variables** | `int x = 10;` |
| **Arrays** | `int arr[10];` / `arr[0] = 5;` |
| **Functions** | `int add(int a, int b) { return a + b; }` |
| **If/Else** | `if (x > 0) { ... } else { ... }` |
| **While** | `while (x < 10) { x = x + 1; }` |
| **For** | `for (int i = 0; i < n; i = i + 1) { ... }` |
| **Structs** | `struct Point { int x; int y; };` |
| **Pointers** | `int* p = &x; int val = *p;` |
| **Recursion** | Fully supported |
| **Comments** | `// single-line` and `/* multi-line */` |

### Example Program

```c
// Fibonacci — recursive
int fib(int n) {
    if (n <= 1) {
        return n;
    }
    return fib(n - 1) + fib(n - 2);
}

int main() {
    int result = fib(10);
    return result;
}
```

> 📄 **Full language specification:** See [`docs/language_spec.md`](docs/language_spec.md) for the complete EBNF grammar, type system, scoping rules, and semantic rules.

---

## 📊 Optimization Results

### Constant-Heavy Programs

| Mode | TAC Instructions | Reduction | Passes Applied |
|------|:---:|:---:|---|
| Unoptimized | 13 | — | — |
| Normal (all passes) | 1 | **92.3%** | all 5 passes |
| ML Optimized | 1 | **92.3%** | constant_folding, dead_code |
| RL Optimized | 1 | **92.3%** | constant_folding, dead_code |

### Dead-Code-Heavy Programs

| Mode | TAC Instructions | Reduction | Passes Applied |
|------|:---:|:---:|---|
| Unoptimized | 9 | — | — |
| Normal (all passes) | 1 | **88.9%** | all 5 passes |
| ML Optimized | 1 | **88.9%** | dead_code |
| RL Optimized | 1 | **88.9%** | dead_code |

### Key Takeaway

> ML and RL modes achieve the **same optimization quality** as applying all passes, but with **fewer passes** — reducing compilation overhead by selecting only the relevant optimizations for each program.

---

## 🧪 Testing

### Run All Tests

```bash
python main.py test
```

### Individual Test Suites

```bash
# Pipeline tests (end-to-end compilation)
python -m pytest tests/test_pipeline_quick.py -v

# Optimizer tests (pass correctness)
python -m pytest tests/test_optimizer_quick.py -v

# Smart pipeline tests (ML/RL mode integration)
python -m pytest tests/test_smart_pipeline.py -v

# Interpreter tests
python -m pytest tests/test_interpreter.py -v

# Optimization demo
python -m pytest tests/test_optimization_demo.py -v
```

### Test Coverage

| Suite | Tests | Status |
|-------|:-----:|:------:|
| Pipeline (Quick) | End-to-end compilation | ✅ Passing |
| Optimizer (Quick) | Individual pass correctness | ✅ Passing |
| Smart Pipeline | ML/RL mode integration | ✅ Passing |
| Interpreter | AST interpretation | ✅ Passing |
| Optimization Demo | Comparison & metrics | ✅ Passing |

---

## 🛠 Technologies

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Lexer / Parser** | [PLY](https://www.dabeaz.com/ply/) (Python Lex-Yacc) | Tokenization & LALR(1) parsing |
| **ML Model** | [scikit-learn](https://scikit-learn.org/) (RandomForestClassifier) | Pass prediction from IR features |
| **RL Agent** | Custom Q-Learning implementation | Adaptive pass selection policy |
| **Web Interface** | [Flask](https://flask.palletsprojects.com/) + [CodeMirror](https://codemirror.net/) | Interactive compiler playground |
| **Charts** | [Chart.js](https://www.chartjs.org/) | Visual metrics comparison |
| **Language** | Python 3.10+ | Core implementation |
| **Testing** | [pytest](https://docs.pytest.org/) | Test framework |

---

## 🤝 Contributing

Contributions are welcome! Here are some ideas:

- 🆕 **New optimization passes** (e.g., Strength Reduction, Register Allocation)
- 🧠 **Better ML models** (e.g., Neural Networks, XGBoost)
- 🎮 **Advanced RL** (e.g., Deep Q-Networks, Policy Gradient methods)
- 📝 **Language extensions** (e.g., `switch`, `break`, `continue`, `do-while`)
- 🎨 **Web UI improvements** (e.g., AST visualization, step-through debugger)

### Steps

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📜 License

This project is developed for **educational purposes** as part of a PBL (Project-Based Learning) course in the 6th semester, B.Tech CSE program.

---

## 👤 Author

**Apurva Sharma**
- GitHub: [@Apurvasharma1001](https://github.com/Apurvasharma1001)

---

<div align="center">

⭐ **Star this repository** if you found it useful!

*Built with ❤️ and a lot of compiler theory.*

</div>

