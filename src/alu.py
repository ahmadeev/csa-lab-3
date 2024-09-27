from __future__ import annotations

from typing import Callable

from isa import Opcode

operations: dict[Opcode, Callable[[int, int], int]] = {
    Opcode.ADD: lambda x, y: x + y,
    Opcode.SUB: lambda x, y: x - y,
    Opcode.MUL: lambda x, y: x * y,
    Opcode.DIV: lambda x, y: x // y,
    Opcode.MOD: lambda x, y: x % y,
    Opcode.CMP: lambda x, y: x - y,
}


class ALU:
    right = 0
    left = 0
    out = 0
    negative = False
    zero = True

    def __init__(self):
        pass

    def signal_sel_left(self, buffer: int, signal: bool):
        self.left = buffer if signal else 0

    def signal_sel_right(self, accumulator: int, signal: bool):
        self.right = accumulator if signal else 0

    def signal_alu_operation(self, operation: Opcode):
        out = operations[operation](self.right, self.left)
        if operation is not Opcode.CMP:
            self.out = out
        self.negative = out < 0
        self.zero = out == 0
