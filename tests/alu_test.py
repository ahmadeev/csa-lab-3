import unittest

from alu import ALU
from isa import Opcode


class TestALU(unittest.TestCase):
    def test_inc_left_dec_right(self):
        alu = ALU()
        alu.signal_sel_left(1, True)
        alu.signal_sel_right(-1, True)
        # -1 - 1
        alu.signal_alu_operation(Opcode.SUB)
        assert -2 == alu.out
