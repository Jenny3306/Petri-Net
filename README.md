# Petri Net Instruction

This is source code for the big assignment of subject Mathematical Modelling (Semester: 251) of group League of MM.

## Note

- On macOS, replace `python` with `python3` and `pip` with `pip3`.
- You may execute the program from the project root without changing into `./src`.  
  Then please replace `main.py` with `src/main.py` in the commands.

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Running the Program

Firstly, go to `./src`.

You can run using a command + `.pnml` file:

```bash
python main.py <command> <pnml_file> -v
```

You can also run **WITHOUT arguments** and choose the files and commands interactively:

```bash
python main.py -v                     # fully interactive
```

#### Available Commands

```
parse       – Parse PNML file
explicit    – Explicit reachability
bdd         – Symbolic BDD reachability
deadlock    – Detect deadlocks
optimize    – Solve marking optimization
full        – Run all analyses
compare     – Compare explicit and bdd reachability (time and space)
```

#### Available Test Files

The `sample_pnml/` directory contains test Petri net models:

| **Model**        | **Places** | **Transitions** | **Arcs** | **Notes**                                                                                 | **Source**                                                   |
| ---------------- | ---------- | --------------- | -------- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| Simple01         | 3          | 2               | 4        | Linear; no branches, no cycles                                                            | Manually created                                             |
| Simple02         | 5          | 4               | 10       | With sync, fork, and cycles                                                               | Manually created                                             |
| CircadianClock01 | 14         | 16              | 58       | Deadlock-free, conservative. Detail: https://mcc.lip6.fr/2025/pdf/CircadianClock-form.pdf | https://mcc.lip6.fr/2025/archives/CircadianClock-pnml.tar.gz |
| AutonomousCar03a | 41         | 121             | 745      | Densely connected. Detail: https://mcc.lip6.fr/2025/pdf/AutonomousCar-form.pdf            | https://mcc.lip6.fr/2025/archives/AutonomousCar-pnml.tar.gz  |
| AutonomousCar04a | 49         | 193             | 1306     | Densely connected. Detail: https://mcc.lip6.fr/2025/pdf/AutonomousCar-form.pdf            | https://mcc.lip6.fr/2025/archives/AutonomousCar-pnml.tar.gz  |

#### Examples

```bash
python main.py parse Simple01.pnml -v
python main.py explicit Simple02.pnml
python main.py bdd CircadianClock01.pnml
python main.py deadlock AutonomousCar03a.pnml
python main.py optimize Simple02.pnml
python main.py full Simple01.pnml -v
python main.py                      # fully interactive
```

#### Options

```
-v, --verbose   Show detailed output (Recommended)
```

### Running Tests

#### Recommended (PyTest)

```bash
python -m pytest
python -m pytest -v                 # verbose
python -m pytest -k "full"          # only full tests
python -m pytest --cov=.            # coverage
```

#### unittest alternative

```bash
python -m unittest discover tests/
```

### Coverage

```bash
coverage run -m unittest discover tests/
coverage report --omit="tests/*"
coverage html
```

---

## Overview

This application provides comprehensive analysis tools for 1-safe Petri nets, including:

1. **PNML Parser** - Parse 1-safe PNML (Petri Net Markup Language) files
2. **Explicit Reachability** - Compute reachable markings using explicit BFS
3. **BDD-based Symbolic Reachability** - Efficient symbolic reachability using Binary Decision Diagrams
4. **ILP + BDD Deadlock Detection** - Detect deadlock states using Integer Linear Programming and BDDs
5. **Linear Objective Optimization** - Optimize linear objectives over reachable markings

## Project Structure

```
.
├── pnml_parser/           # PNML file parsing module
│   ├── __init__.py
│   └── parser.py
├── explicit_reachability/ # Explicit BFS reachability analysis
│   ├── __init__.py
│   └── reachability.py
├── bdd_reachability/      # BDD-based symbolic reachability
│   ├── __init__.py
│   └── symbolic_reachability.py
├── ilp_deadlock/          # ILP + BDD deadlock detection
│   ├── __init__.py
│   └── deadlock_detector.py
├── optimization/          # Linear objective optimization
│   ├── __init__.py
│   └── optimizer.py
├── utils/                 # Data structures and utils
│   ├── __init__.py
│   ├── petri_net.py
│   └── marking.py
├── tests/                 # Unit tests for all modules
│   ├── __init__.py
│   ├── test_pnml_parser.py
│   ├── test_explicit_reachability.py
│   ├── test_bdd_reachability.py
│   ├── test_ilp_deadlock.py
│   ├── test_optimization.py
│   └── test_utils.py
├── sample_pnml           # Sample PNML files for testing
│   ├── simple.pnml
│   └── ...
├── main.py                # Main entry point
└── README.md              # This file
```

## Tasks

### 1. PNML Parser (`pnml_parser/`)

Parse 1-safe PNML files to extract:

- Places and their initial markings
- Transitions
- Arcs (input/output connections)
- Validate consistency

### 2. Explicit Reachability (`explicit_reachability/`)

Compute the reachability graph using explicit BFS:

- Start from initial marking
- Explore all enabled transitions
- Build complete state space

### 3. BDD-based Symbolic Reachability (`bdd_reachability/`)

Efficient symbolic reachability using Binary Decision Diagrams:

- Encode Petri net structure symbolically
- Compute reachable states using BDD operations
- Handle large state spaces efficiently
- Extract explicit markings when needed

### 4. ILP + BDD Deadlock Detection (`ilp_deadlock/`)

Detect deadlock states using hybrid approach:

- Formulate deadlock detection as ILP problem with dead marking and marking equation constraints
- Check reachable with BDD

### 5. Linear Objective Optimization (`optimization/`)

Optimize linear objectives over reachable markings:

- Define linear objective functions over places
- Maximize or minimize objectives
- Find optimal reachable markings
- Support custom objective functions

## Requirements

The application requires Python 3.7 or higher. Additional dependencies include:

- BDD operations (`dd`)
- ILP solving (`pulp`)
- Testing (`pytest`)

## Contributing

This is an academic project for Mathematical Modelling (Semester: 251). For questions or contributions, please contact the League of MM team.
