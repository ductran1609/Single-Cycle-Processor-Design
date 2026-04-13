"""
processor.py — Single-Cycle Processor Entry Point
Single-Cycle Processor | Intel Semester Project

Computes:  Y = A·B + C'·D

Register Assignments:
  t0 = reg[8]   → A  (also holds final result Y after OR instruction)
  t1 = reg[9]   → B
  t3 = reg[11]  → D
  t4 = reg[12]  → Intermediate: A & B
  t5 = reg[13]  → C  (source operand for ~C operation)
  t6 = reg[14]  → Intermediate: (~C) & D

Program (3 instructions):
  Cycle 1:  and    t4, t0, t1    ; t4 = A & B           (funct = 0x24)
  Cycle 2:  andinv t6, t5, t3    ; t6 = (~C) & D         (funct = 0x26, InvertA=1)
  Cycle 3:  or     t0, t4, t6    ; t0 = t4 | t6  = Y    (funct = 0x25)

Usage:
  python processor.py                 # Run default test cases
  python processor.py --A 1 --B 0 --C 1 --D 1   # Custom values
"""

import sys
from datapath import Datapath

# ── Function field encodings ───────────────────────────────────────────────────
FUNCT_AND    = 0x24  # 0b100100  Standard AND
FUNCT_OR     = 0x25  # 0b100101  Standard OR
FUNCT_ANDINV = 0x26  # 0b100110  AND with InvertA (NOT via control signal)

# ── Register number assignments ────────────────────────────────────────────────
T0 = 8   # A  / Y (result)
T1 = 9   # B
T2 = 10  # (unused by program, C also loaded into T5)
T3 = 11  # D
T4 = 12  # intermediate A & B
T5 = 13  # C  (source for ~C)
T6 = 14  # intermediate (~C) & D

# ── Register name map (for trace output) ──────────────────────────────────────
REG_NAMES = {
    T0: "t0", T1: "t1", T2: "t2", T3: "t3",
    T4: "t4", T5: "t5", T6: "t6",
}

# ── Assembly mnemonics for trace display ───────────────────────────────────────
ASM_MNEMONICS = [
    "and    t4, t0, t1      # t4 = A & B",
    "andinv t6, t5, t3      # t6 = (~C) & D",
    "or     t0, t4, t6      # t0 = t4 | t6  →  Y",
]


def reg_name(n: int) -> str:
    return REG_NAMES.get(n, f"r{n}")


# ═══════════════════════════════════════════════════════════════════════════════
# Assembler — encode instructions as 32-bit words
# ═══════════════════════════════════════════════════════════════════════════════

def encode_rtype(rs: int, rt: int, rd: int, funct: int) -> int:
    """
    Encode an R-type 32-bit instruction.

    Format:
      [31:26] opcode = 000000
      [25:21] rs
      [20:16] rt
      [15:11] rd
      [10:06] shamt  = 00000
      [05:00] funct
    """
    opcode = 0b000000
    shamt  = 0b00000
    return (
        (opcode & 0x3F) << 26 |
        (rs     & 0x1F) << 21 |
        (rt     & 0x1F) << 16 |
        (rd     & 0x1F) << 11 |
        (shamt  & 0x1F) <<  6 |
        (funct  & 0x3F)
    )


def assemble() -> list[int]:
    """
    Assemble the three-instruction program and return 32-bit machine words.

    Returns:
        [instr_0, instr_1, instr_2] as 32-bit integers
    """
    return [
        encode_rtype(rs=T0, rt=T1, rd=T4, funct=FUNCT_AND),     # and    t4, t0, t1
        encode_rtype(rs=T5, rt=T3, rd=T6, funct=FUNCT_ANDINV),  # andinv t6, t5, t3
        encode_rtype(rs=T4, rt=T6, rd=T0, funct=FUNCT_OR),      # or     t0, t4, t6
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# Pretty-print helpers
# ═══════════════════════════════════════════════════════════════════════════════

W = 62  # Box width

def banner(text: str) -> None:
    print("\n" + "═" * W)
    print(f"  {text}")
    print("═" * W)

def section(text: str) -> None:
    print(f"\n  {'─' * (W - 4)}")
    print(f"  {text}")
    print(f"  {'─' * (W - 4)}")

def print_control_table(trace: dict, cycle: int, mnemonic: str) -> None:
    """Print one cycle's full execution trace."""
    t = trace
    invert_a_str = "1 → (~A) applied" if t['invert_a'] else "0 → pass-through"
    alu_op_str   = f"{t['alu_op']:02b} ({t['op_name']})"

    print(f"\n  ┌─ Cycle {cycle} ─── {mnemonic}")
    print(f"  │  32-bit encoding : 0x{t['instruction']:08X}  ({t['instruction']:032b})")
    print(f"  │")
    print(f"  │  ─── Decoded Fields ────────────────────────────────")
    print(f"  │  opcode = {t['opcode']:06b}   funct  = {t['funct']:06b} (0x{t['funct']:02X})")
    print(f"  │  rs     = {t['rs']:5d}  ({reg_name(t['rs'])})")
    print(f"  │  rt     = {t['rt']:5d}  ({reg_name(t['rt'])})")
    print(f"  │  rd     = {t['rd']:5d}  ({reg_name(t['rd'])})")
    print(f"  │")
    print(f"  │  ─── Control Signals ───────────────────────────────")
    print(f"  │  RegWrite = {int(t['reg_write'])}  (write result → {reg_name(t['rd'])})")
    print(f"  │  ALU_op   = {alu_op_str}")
    print(f"  │  InvertA  = {invert_a_str}")
    print(f"  │")
    print(f"  │  ─── ALU Inputs & Execution ─────────────────────────")
    a_raw = t['read_data_1']
    if t['invert_a']:
        a_eff = (~a_raw) & 0xFFFF_FFFF
        print(f"  │  A (rs={reg_name(t['rs'])}) = {a_raw} → ~A = {a_eff}  [InvertA asserted]")
    else:
        print(f"  │  A (rs={reg_name(t['rs'])}) = {a_raw}")
    print(f"  │  B (rt={reg_name(t['rt'])}) = {t['read_data_2']}")
    print(f"  │  Result          = {t['alu_result']}  (ZeroFlag={int(t['zero_flag'])})")
    print(f"  │")
    print(f"  └─ Write-back: {reg_name(t['rd'])} ← {t['alu_result']}")


# ═══════════════════════════════════════════════════════════════════════════════
# Main simulation
# ═══════════════════════════════════════════════════════════════════════════════

def run_processor(A: int, B: int, C: int, D: int) -> int:
    """
    Run the full processor simulation for inputs A, B, C, D.

    Returns:
        Y = A·B + C'·D  (as integer 0 or 1)
    """
    # ── Expected result (ground truth) ────────────────────────────────────────
    expected = int(bool((A & B) | ((1 - C) & D)))

    banner(f"Single-Cycle 32-bit Processor  |  Inputs: A={A} B={B} C={C} D={D}")
    print(f"\n  Expression : Y = A·B + C'·D")
    print(f"  Inputs     : A={A}  B={B}  C={C}  D={D}")
    print(f"  Expected Y : {expected}")

    # ── Initialize processor & load registers ──────────────────────────────────
    cpu = Datapath()
    cpu.load_registers({
        T0: A,   # t0 = A
        T1: B,   # t1 = B
        T5: C,   # t5 = C  (used as ~C source)
        T3: D,   # t3 = D
    })

    # ── Assemble program ───────────────────────────────────────────────────────
    program = assemble()

    section("Assembled Program (machine words)")
    print(f"  {'Cycle':<6}  {'Hex':>12}  {'Binary':>34}  Mnemonic")
    print(f"  {'─'*6}  {'─'*12}  {'─'*34}  {'─'*30}")
    for i, (instr, mnem) in enumerate(zip(program, ASM_MNEMONICS)):
        print(f"  {i+1:<6}  0x{instr:08X}  {instr:032b}  {mnem}")

    section("Instruction Execution Trace")

    traces = []
    for cycle, (instr, mnem) in enumerate(zip(program, ASM_MNEMONICS)):
        trace = cpu.execute_instruction(instr)
        traces.append(trace)
        print_control_table(trace, cycle + 1, mnem)

    # ── Register file after execution ──────────────────────────────────────────
    section("Register State After All Instructions")
    rf = cpu.register_file
    reg_display = [
        (T0, "t0 → Y (result)"),
        (T1, "t1 → B"),
        (T3, "t3 → D"),
        (T4, "t4 → A & B"),
        (T5, "t5 → C"),
        (T6, "t6 → (~C) & D"),
    ]
    print(f"  {'Register':<20}  Value")
    print(f"  {'─'*20}  {'─'*10}")
    for reg, label in reg_display:
        print(f"  {label:<20}  {rf.read(reg)}")

    # ── Final verification ─────────────────────────────────────────────────────
    section("Verification")
    Y   = rf.read(T0)
    t4v = rf.read(T4)
    t6v = rf.read(T6)
    print(f"  t4  =  A & B     =  {A} & {B}  =  {t4v}")
    print(f"  t6  =  (~C) & D  = ~{C} & {D}  =  {t6v}")
    print(f"  Y   =  t4 | t6   =  {t4v} | {t6v}  =  {Y}")
    status = "✓ PASS" if Y == expected else "✗ FAIL"
    print(f"\n  {status}  —  Y = {Y}  (expected {expected})")

    return Y


# ═══════════════════════════════════════════════════════════════════════════════
# Entry point — run all truth table test cases
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Run four representative test cases covering the expression Y = A·B + C'·D."""

    test_cases = [
        # A  B  C  D    # Expected Y = A·B + C'·D
        (1, 1, 0, 1),   # Y = 1·1 + 1·1 = 1  (both terms = 1)
        (0, 1, 0, 1),   # Y = 0·1 + 1·1 = 1  (only C'·D contributes)
        (1, 1, 1, 0),   # Y = 1·1 + 0·0 = 1  (only A·B contributes)
        (0, 0, 1, 0),   # Y = 0·0 + 0·0 = 0  (both terms = 0)
    ]

    all_pass = True
    results  = []
    for A, B, C, D in test_cases:
        Y = run_processor(A, B, C, D)
        expected = int(bool((A & B) | ((1 - C) & D)))
        results.append((A, B, C, D, Y, expected, Y == expected))
        if Y != expected:
            all_pass = False

    # ── Summary table ──────────────────────────────────────────────────────────
    banner("Full Test Summary")
    print(f"\n  {'A':>3}  {'B':>3}  {'C':>3}  {'D':>3}  {'Expected':>9}  {'Got':>5}  Status")
    print(f"  {'─'*3}  {'─'*3}  {'─'*3}  {'─'*3}  {'─'*9}  {'─'*5}  {'─'*6}")
    for A, B, C, D, Y, exp, ok in results:
        status = "PASS ✓" if ok else "FAIL ✗"
        print(f"  {A:>3}  {B:>3}  {C:>3}  {D:>3}  {exp:>9}  {Y:>5}  {status}")
    print(f"\n  Overall: {'ALL TESTS PASSED ✓' if all_pass else 'SOME TESTS FAILED ✗'}")


if __name__ == "__main__":
    main()
