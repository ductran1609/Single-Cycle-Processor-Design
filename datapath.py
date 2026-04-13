"""
datapath.py — Single-Cycle 32-bit Datapath
Single-Cycle Processor | Intel Semester Project

Integrates all datapath components:
  - RegisterFile   (register_file.py)
  - ALU            (alu.py)
  - MUX2to1        (mux.py)
  - ControlUnit    (control_unit.py)

Execution Model — Single-Cycle (all stages in one clock cycle):
  1. FETCH     — Instruction provided externally (no PC/memory in this design)
  2. DECODE    — Control Unit decodes opcode + funct → generates control signals
  3. READ      — Register File reads rs and rt
  4. EXECUTE   — ALU performs operation (with optional input inversion)
  5. WRITEBACK — ALU result written back to rd (if RegWrite asserted)

Instruction Format (R-type, 32-bit):
  Bits [31:26]  opcode  — 000000 (R-type)
  Bits [25:21]  rs      — source register 1 (operand A)
  Bits [20:16]  rt      — source register 2 (operand B)
  Bits [15:11]  rd      — destination register
  Bits [10:06]  shamt   — 00000 (unused)
  Bits [05:00]  funct   — operation selector
"""

from register_file import RegisterFile
from alu           import ALU
from mux           import MUX2to1
from control_unit  import ControlUnit, ControlSignals


class Datapath:
    """
    Complete single-cycle datapath.

    Each call to execute_instruction() represents one full clock cycle.
    Returns a detailed trace dictionary for verification and debugging.
    """

    def __init__(self):
        self.register_file = RegisterFile()
        self.alu            = ALU()
        self.mux            = MUX2to1()
        self.control_unit   = ControlUnit()

    # ── Public API ─────────────────────────────────────────────────────────────

    def load_registers(self, init_values: dict) -> None:
        """Load initial register values (A, B, C, D) before execution."""
        self.register_file.load_initial_values(init_values)

    def execute_instruction(self, instruction: int) -> dict:
        """
        Execute one 32-bit instruction through the full single-cycle datapath.

        Args:
            instruction: 32-bit encoded R-type instruction

        Returns:
            Trace dictionary containing all intermediate values,
            control signals, and results for this instruction.
        """

        # ══════════════════════════════════════════════════════════════════════
        # STAGE 1 — FETCH
        # In a real processor this stage loads the instruction from memory
        # using the PC. Here the instruction is injected directly.
        # ══════════════════════════════════════════════════════════════════════
        raw_instr = instruction & 0xFFFF_FFFF

        # ══════════════════════════════════════════════════════════════════════
        # STAGE 2 — DECODE
        # Extract instruction fields and generate control signals.
        # ══════════════════════════════════════════════════════════════════════
        opcode = (raw_instr >> 26) & 0x3F   # bits [31:26]
        rs     = (raw_instr >> 21) & 0x1F   # bits [25:21]
        rt     = (raw_instr >> 16) & 0x1F   # bits [20:16]
        rd     = (raw_instr >> 11) & 0x1F   # bits [15:11]
        shamt  = (raw_instr >>  6) & 0x1F   # bits [10:06]  (unused)
        funct  = (raw_instr >>  0) & 0x3F   # bits [05:00]

        signals: ControlSignals = self.control_unit.decode(opcode, funct)

        # ══════════════════════════════════════════════════════════════════════
        # STAGE 3 — REGISTER READ
        # Two simultaneous combinational reads from the register file.
        # ══════════════════════════════════════════════════════════════════════
        read_data_1, read_data_2 = self.register_file.read_two(rs, rt)

        # ══════════════════════════════════════════════════════════════════════
        # STAGE 4 — EXECUTE (ALU)
        # The InvertA MUX is driven by the control signal before the ALU gate.
        # When signals.invert_a == 1, input A is bitwise-inverted by the ALU
        # before the AND/OR operation — this is how NOT is realized.
        # ══════════════════════════════════════════════════════════════════════
        alu_result = self.alu.execute(
            input_a  = read_data_1,
            input_b  = read_data_2,
            alu_op   = signals.alu_op,
            invert_a = signals.invert_a,
        )

        # ══════════════════════════════════════════════════════════════════════
        # STAGE 5 — WRITE-BACK
        # Write ALU result to destination register rd, gated by RegWrite.
        # ══════════════════════════════════════════════════════════════════════
        self.register_file.write(rd, alu_result, signals.reg_write)

        # ── Build trace record ────────────────────────────────────────────────
        return {
            # Raw instruction
            "instruction":  raw_instr,
            # Decoded fields
            "opcode":       opcode,
            "rs":           rs,
            "rt":           rt,
            "rd":           rd,
            "shamt":        shamt,
            "funct":        funct,
            # Control signals
            "reg_write":    signals.reg_write,
            "alu_op":       signals.alu_op,
            "invert_a":     signals.invert_a,
            "op_name":      signals.op_name,
            # Data values
            "read_data_1":  read_data_1,
            "read_data_2":  read_data_2,
            "alu_result":   alu_result,
            "zero_flag":    self.alu.zero_flag,
        }
