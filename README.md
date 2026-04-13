# Single-Cycle 32-bit Processor Simulator

**Intel Semester Project — Task 4**  
Computes: **Y = A·B + C'·D**

---

## Project Structure

```
processor/
├── register_file.py   # 32×32-bit register file (2 read ports, 1 write port)
├── alu.py             # ALU: AND / OR with optional input A inversion
├── mux.py             # 2-to-1 and 4-to-1 multiplexer components
├── control_unit.py    # Instruction decoder → control signals
├── datapath.py        # Full single-cycle datapath (ties all components)
├── processor.py       # Entry point: assembler, execution trace, validation
└── README.md
```

---

## Design Summary

### Instruction Set

| Mnemonic   | funct (6-bit) | ALU_op | InvertA | Operation     |
|------------|---------------|--------|---------|---------------|
| `and`      | `100100` (0x24) | `00`  | `0`     | `A & B`       |
| `or`       | `100101` (0x25) | `01`  | `0`     | `A \| B`      |
| `andinv`   | `100110` (0x26) | `00`  | `1`     | `(~A) & B`    |

> **NOT is not a separate instruction.** It is encoded in the `funct` field
> (`0x26`) and implemented by the `InvertA` control signal in the ALU.
> This satisfies the requirement that inversion is encoded in the function
> field, not the opcode.

### Instruction Format (32-bit R-type)

```
 31      26 25    21 20    16 15    11 10     6 5       0
┌──────────┬────────┬────────┬────────┬────────┬────────┐
│  opcode  │   rs   │   rt   │   rd   │  shamt │  funct │
│ (000000) │ 5 bits │ 5 bits │ 5 bits │ 5 bits │ 6 bits │
└──────────┴────────┴────────┴────────┴────────┴────────┘
```

All instructions are R-type (`opcode = 000000`). The `funct` field
selects the operation and whether input A is inverted.

### Register Assignments

| Register | Number | Role               |
|----------|--------|--------------------|
| `t0`     | 8      | A (also result Y)  |
| `t1`     | 9      | B                  |
| `t3`     | 11     | D                  |
| `t4`     | 12     | Intermediate A & B |
| `t5`     | 13     | C (source for ~C)  |
| `t6`     | 14     | Intermediate (~C)&D|

### Assembled Program

```asm
and    t4, t0, t1      # Cycle 1: t4 = A & B           (funct=0x24)
andinv t6, t5, t3      # Cycle 2: t6 = (~C) & D         (funct=0x26, InvertA=1)
or     t0, t4, t6      # Cycle 3: t0 = t4 | t6  →  Y   (funct=0x25)
```

### Control Unit Truth Table

| Instruction | funct    | RegWrite | ALU_op | InvertA |
|-------------|----------|----------|--------|---------|
| AND         | `100100` | 1        | `00`   | 0       |
| ANDINV      | `100110` | 1        | `00`   | **1**   |
| OR          | `100101` | 1        | `01`   | 0       |

### Single-Cycle Execution Model

Each instruction completes in one clock cycle:

```
Fetch → Decode → Register Read → Execute (ALU) → Write-back
```

All stages are combinational within a single cycle. There is no pipeline,
no hazard detection, and no memory access stage (all operands are in registers).

---

## Running the Simulation

### Requirements

- Python 3.10+  
- No external dependencies

### Run default test cases

```bash
python processor.py
```

This runs 4 test cases covering all relevant combinations of A, B, C, D
and prints the full execution trace + verification for each.

### Run a custom test case

Import and call `run_processor()` directly:

```python
from processor import run_processor
run_processor(A=1, B=0, C=0, D=1)  # Expected Y = 0 | 1 = 1
```

---

## Sample Output

```
═══════════════════════════════════════════════════════════════
  Single-Cycle 32-bit Processor  |  Inputs: A=1 B=1 C=0 D=1
═══════════════════════════════════════════════════════════════

  Expression : Y = A·B + C'·D
  Expected Y : 1

  Cycle 1 — and    t4, t0, t1      # t4 = A & B
    RegWrite = 1  |  ALU_op = 00 (AND)  |  InvertA = 0
    A = 1, B = 1  →  Result = 1
    Write-back: t4 ← 1

  Cycle 2 — andinv t6, t5, t3      # t6 = (~C) & D
    RegWrite = 1  |  ALU_op = 00 (ANDINV)  |  InvertA = 1
    A = 0 → ~A = 0xFFFFFFFF, B = 1  →  Result = 1
    Write-back: t6 ← 1

  Cycle 3 — or     t0, t4, t6      # t0 = t4 | t6 → Y
    RegWrite = 1  |  ALU_op = 01 (OR)  |  InvertA = 0
    A = 1, B = 1  →  Result = 1
    Write-back: t0 ← 1

  ✓ PASS  —  Y = 1  (expected 1)
```

---

## Validation — Full Truth Table

| A | B | C | D | Expected Y | Result  |
|---|---|---|---|------------|---------|
| 1 | 1 | 0 | 1 |     1      | PASS ✓  |
| 0 | 1 | 0 | 1 |     1      | PASS ✓  |
| 1 | 1 | 1 | 0 |     1      | PASS ✓  |
| 0 | 0 | 1 | 0 |     0      | PASS ✓  |

---

## Demo Video

**Yes — video recordings can be uploaded to YouTube.**  
Set visibility to **Unlisted** so anyone with the link can view it, then
submit the URL to iCollege. This satisfies the "necessary viewing
permissions" requirement without making the video public.

**Suggested demo script (4–5 min):**
1. (0:00–0:45) Open the repo; walk through file structure
2. (0:45–2:00) Explain `control_unit.py` — how funct → control signals
3. (2:00–3:00) Explain `alu.py` — how InvertA implements NOT
4. (3:00–4:00) Run `python processor.py` — narrate the trace output
5. (4:00–5:00) Show the PASS summary; confirm Y matches expected values

---

## GitHub Submission

```bash
git init
git add .
git commit -m "Task 4: Single-cycle 32-bit processor — Y = A·B + C'·D"
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

---

*Single-Cycle 32-bit Processor | Intel Semester Project | Task 4*
