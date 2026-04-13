"""
alu.py — 32-bit Arithmetic Logic Unit
Single-Cycle Processor | Intel Semester Project

Supported Operations:
  - AND  (alu_op = 0b00)
  - OR   (alu_op = 0b01)

NOT Functionality:
  - NOT is NOT a separate instruction.
  - It is implemented via the InvertA control signal, which bitwise-inverts
    ALU input A before the operation.
  - This is controlled by the function field (funct) via the Control Unit.
  - Example: ANDINV  →  (~A) & B   (implements ~C when A = C)
"""

# ALU operation select constants (match control_unit.py)
ALU_OP_AND = 0b00  # Bitwise AND
ALU_OP_OR  = 0b01  # Bitwise OR

MASK_32 = 0xFFFF_FFFF


class ALU:
    """
    32-bit ALU supporting AND and OR with optional input A inversion.

    Attributes:
        result     (int):  Result of the last operation
        zero_flag  (bool): True when result == 0
    """

    def __init__(self):
        self.result    = 0
        self.zero_flag = False

    def execute(
        self,
        input_a:  int,
        input_b:  int,
        alu_op:   int,
        invert_a: bool = False,
    ) -> int:
        """
        Perform the ALU operation.

        Pipeline stage: Execute

        Args:
            input_a:  First 32-bit operand  (from rs register read)
            input_b:  Second 32-bit operand (from rt register read)
            alu_op:   Operation selector (ALU_OP_AND or ALU_OP_OR)
            invert_a: When True, bitwise-invert input_a before operation.
                      This implements NOT without a separate instruction.

        Returns:
            32-bit result (also stored in self.result)

        Control Signal Truth Table:
            alu_op | invert_a | Operation
            ──────────────────────────────
              00   |    0     | A  & B   (AND)
              00   |    1     | ~A & B   (ANDINV — encodes NOT via funct)
              01   |    0     | A  | B   (OR)
        """
        a = input_a & MASK_32
        b = input_b & MASK_32

        # ── InvertA stage (controlled by funct field via Control Unit) ────────
        if invert_a:
            a = (~a) & MASK_32  # Bitwise NOT, clamped to 32 bits

        # ── ALU operation select ──────────────────────────────────────────────
        if alu_op == ALU_OP_AND:
            self.result = (a & b) & MASK_32
        elif alu_op == ALU_OP_OR:
            self.result = (a | b) & MASK_32
        else:
            raise ValueError(
                f"Unknown ALU operation: {alu_op:02b}. "
                f"Valid ops: ALU_OP_AND=00, ALU_OP_OR=01"
            )

        # ── Zero flag ─────────────────────────────────────────────────────────
        self.zero_flag = self.result == 0

        return self.result

    def operation_name(self, alu_op: int, invert_a: bool) -> str:
        """Human-readable operation string for trace output."""
        if alu_op == ALU_OP_AND and not invert_a:
            return "AND (A & B)"
        elif alu_op == ALU_OP_AND and invert_a:
            return "ANDINV (~A & B)"
        elif alu_op == ALU_OP_OR:
            return "OR (A | B)"
        return f"UNKNOWN (op={alu_op:02b})"
