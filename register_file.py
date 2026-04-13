"""
register_file.py — 32-Register, 32-bit Register File
Single-Cycle Processor | Intel Semester Project

Supports:
  - 2 simultaneous read ports (rs, rt)
  - 1 write port (rd), gated by RegWrite control signal
  - Register 0 hardwired to 0 (MIPS convention)
"""


class RegisterFile:
    """
    32 x 32-bit general-purpose register file.

    All values are masked to 32 bits on read and write.
    Register 0 is hardwired to 0 and cannot be written.
    """

    def __init__(self):
        self.registers = [0] * 32  # 32 registers, each 32 bits wide

    # ── Read Port ──────────────────────────────────────────────────────────────
    def read(self, reg_num: int) -> int:
        """
        Read a register value.

        Args:
            reg_num: Register index (0–31)
        Returns:
            32-bit unsigned integer stored in that register.
            Always returns 0 for register 0.
        """
        if not (0 <= reg_num <= 31):
            raise ValueError(f"Register index out of range: {reg_num}")
        if reg_num == 0:
            return 0
        return self.registers[reg_num] & 0xFFFF_FFFF

    def read_two(self, rs: int, rt: int) -> tuple[int, int]:
        """
        Read two registers simultaneously (combinational, one cycle).

        Returns:
            Tuple (read_data_1, read_data_2)
        """
        return self.read(rs), self.read(rt)

    # ── Write Port ─────────────────────────────────────────────────────────────
    def write(self, reg_num: int, value: int, write_enable: bool) -> None:
        """
        Write to a register, gated by the RegWrite control signal.

        Args:
            reg_num:       Destination register index (0–31)
            value:         32-bit value to write
            write_enable:  RegWrite control signal — must be True to write
        """
        if write_enable and reg_num != 0:
            self.registers[reg_num] = value & 0xFFFF_FFFF

    # ── Utility ────────────────────────────────────────────────────────────────
    def load_initial_values(self, reg_values: dict) -> None:
        """
        Bulk-initialize registers (used to set up A, B, C, D before execution).

        Args:
            reg_values: {reg_index: value} mapping
        """
        for reg_num, value in reg_values.items():
            if reg_num != 0:
                self.registers[reg_num] = value & 0xFFFF_FFFF

    def dump(self, reg_map: dict = None) -> None:
        """
        Print all non-zero register values.

        Args:
            reg_map: Optional {reg_index: name} for pretty labels
        """
        reg_map = reg_map or {}
        print("  Register File State:")
        for i, v in enumerate(self.registers):
            if v != 0:
                label = reg_map.get(i, f"reg[{i:2d}]")
                print(f"    {label:12s} = {v} (0x{v:08X}, {v:032b}b)")
