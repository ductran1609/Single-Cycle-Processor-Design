"""
mux.py — Multiplexer Components
Single-Cycle Processor | Intel Semester Project

Provides combinational MUX logic used throughout the datapath.
In a real hardware implementation these are pure logic gates;
here they are modeled as simple Python functions/class.
"""


class MUX2to1:
    """
    2-to-1 Multiplexer (32-bit datapath width).

    Selects one of two 32-bit inputs based on a 1-bit select signal.

    Truth Table:
        sel | output
        ────────────
         0  | input_0
         1  | input_1

    Usage in datapath:
        - ALU input A select (pass-through vs inverted) — driven by InvertA signal
        - Write-data select  (ALU result vs memory)     — unused in this design
        - Any future control muxing
    """

    @staticmethod
    def select(input_0: int, input_1: int, sel: int) -> int:
        """
        Args:
            input_0: Value routed when sel = 0
            input_1: Value routed when sel = 1
            sel:     1-bit select signal (0 or 1)
        Returns:
            Selected 32-bit value
        """
        if sel not in (0, 1):
            raise ValueError(f"MUX select signal must be 0 or 1, got: {sel}")
        return input_1 if sel else input_0


class MUX4to1:
    """
    4-to-1 Multiplexer (32-bit datapath width).
    2-bit select line. Provided for extensibility.
    """

    @staticmethod
    def select(inputs: list[int], sel: int) -> int:
        """
        Args:
            inputs: List of exactly 4 32-bit values [in0, in1, in2, in3]
            sel:    2-bit select signal (0–3)
        Returns:
            Selected 32-bit value
        """
        if len(inputs) != 4:
            raise ValueError("MUX4to1 requires exactly 4 inputs")
        if not (0 <= sel <= 3):
            raise ValueError(f"MUX4to1 sel must be 0–3, got: {sel}")
        return inputs[sel]
