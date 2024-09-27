import unittest

from isa import Addressing, Instruction, Opcode
from machine import ControlUnit, DataPath


class ControlUnitTest(unittest.TestCase):
    def test_program_fetch(self):
        program = [Instruction(Opcode.LD, 50, Addressing.IMMEDIATE)]
        data_path = DataPath("", program)
        control_unit = ControlUnit(0, data_path)
        control_unit.program_fetch()
        assert program[0] == control_unit.program

    def test_address_fetch_direct(self):
        program = [Instruction(Opcode.LD, 50, Addressing.DIRECT)]
        data_path = DataPath("", program)
        control_unit = ControlUnit(0, data_path)
        control_unit.program_fetch()
        control_unit.address_fetch()
        assert 50 == control_unit.data_path.address_register

    def test_address_fetch_indirect(self):
        program = [
            Instruction(Opcode.LD, 1, Addressing.INDIRECT),
            Instruction(Opcode.VAR, 512, Addressing.IMMEDIATE),
        ]
        data_path = DataPath("", program)
        control_unit = ControlUnit(0, data_path)
        control_unit.program_fetch()
        control_unit.address_fetch()
        assert 512 == control_unit.data_path.address_register

    def test_operand_fetch_immediate(self):
        program = [
            Instruction(Opcode.LD, 50, Addressing.IMMEDIATE),
        ]
        data_path = DataPath("", program)
        control_unit = ControlUnit(0, data_path)
        control_unit.program_fetch()
        control_unit.address_fetch()
        control_unit.operand_fetch()
        assert 50 == control_unit.data_path.mem_out.arg

    def test_operand_fetch_direct(self):
        program = [
            Instruction(Opcode.LD, 1, Addressing.DIRECT),
            Instruction(Opcode.VAR, 512, Addressing.IMMEDIATE),
        ]
        data_path = DataPath("", program)
        control_unit = ControlUnit(0, data_path)
        control_unit.program_fetch()
        control_unit.address_fetch()
        control_unit.operand_fetch()
        assert 512 == control_unit.data_path.mem_out.arg

    def test_operand_fetch_indirect(self):
        program = [
            Instruction(Opcode.LD, 1, Addressing.INDIRECT),
            Instruction(Opcode.VAR, 2, Addressing.IMMEDIATE),
            Instruction(Opcode.VAR, 512, Addressing.IMMEDIATE),
        ]
        data_path = DataPath("", program)
        control_unit = ControlUnit(0, data_path)
        control_unit.program_fetch()
        control_unit.address_fetch()
        control_unit.operand_fetch()
        assert 512 == control_unit.data_path.mem_out.arg

    def test_execute_load(self):
        program = [
            Instruction(Opcode.LD, 42, Addressing.IMMEDIATE),
            Instruction(Opcode.ST, 2, Addressing.IMMEDIATE),
        ]
        data_path = DataPath("", program)
        control_unit = ControlUnit(0, data_path)
        control_unit.decode_and_execute()
        assert 42 == data_path.accumulator
        control_unit.decode_and_execute()
        assert 42 == data_path.memory[2].arg

    def test_execute_add(self):
        program = [
            Instruction(Opcode.LD, 42, Addressing.IMMEDIATE),
            Instruction(Opcode.ADD, 42, Addressing.IMMEDIATE),
        ]
        data_path = DataPath("", program)
        control_unit = ControlUnit(0, data_path)
        control_unit.decode_and_execute()
        assert 1 == control_unit.program_counter
        control_unit.decode_and_execute()
        assert 2 == control_unit.program_counter
        assert 84 == data_path.accumulator

    def test_execute_mod(self):
        program = [
            Instruction(Opcode.LD, 42, Addressing.IMMEDIATE),
            Instruction(Opcode.MOD, 2, Addressing.IMMEDIATE),
        ]
        data_path = DataPath("", program)
        control_unit = ControlUnit(0, data_path)
        control_unit.decode_and_execute()
        assert 1 == control_unit.program_counter
        control_unit.decode_and_execute()
        assert 2 == control_unit.program_counter
        assert 0 == data_path.accumulator

    def test_execute_jmp(self):
        program = [
            Instruction(Opcode.JMP, 200, Addressing.IMMEDIATE),
        ]
        data_path = DataPath("", program)
        control_unit = ControlUnit(0, data_path)
        control_unit.decode_and_execute()
        assert 200 == control_unit.program_counter
        assert 0 == data_path.accumulator

    def test_jz(self):
        program = [
            Instruction(Opcode.JZ, 2, Addressing.IMMEDIATE),  # 0
            Instruction(Opcode.VAR, 2, Addressing.IMMEDIATE),  # 1
            Instruction(Opcode.ADD, 420, Addressing.IMMEDIATE),  # 2, sets NZ to 00
            Instruction(Opcode.JZ, 0, Addressing.IMMEDIATE),  # 3
        ]
        data_path = DataPath("", program)
        control_unit = ControlUnit(0, data_path)
        control_unit.decode_and_execute()
        assert 2 == control_unit.program_counter
        control_unit.decode_and_execute()
        assert 420 == data_path.accumulator
        assert False is data_path.alu.zero
        assert 3 == control_unit.program_counter
        control_unit.decode_and_execute()
        assert 4 == control_unit.program_counter

    def test_cmp(self):
        program = [
            Instruction(Opcode.LD, 420, Addressing.IMMEDIATE),
            Instruction(Opcode.CMP, 0, Addressing.IMMEDIATE),
            Instruction(Opcode.LD, -420, Addressing.IMMEDIATE),
            Instruction(Opcode.CMP, 0, Addressing.IMMEDIATE),
        ]
        data_path = DataPath("", program)
        control_unit = ControlUnit(0, data_path)
        control_unit.decode_and_execute()
        control_unit.decode_and_execute()
        assert control_unit.data_path.alu.zero is False
        assert control_unit.data_path.alu.negative is False
        assert control_unit.data_path.accumulator == 420
        control_unit.decode_and_execute()
        control_unit.decode_and_execute()
        assert control_unit.data_path.alu.zero is False
        assert control_unit.data_path.alu.negative is True
        assert control_unit.data_path.accumulator == -420
