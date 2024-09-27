import unittest

from machine import ControlUnit, DataPath, simulate
from translator import parse_lines


class IntegrationTest(unittest.TestCase):
    def test_sum(self):
        lines = ["RESULT: VAR 0", "START: LD 5", "ADD 10", "ST RESULT", "HLT"]
        instructions, pc = parse_lines(lines)
        data_path = DataPath("", instructions)
        control_unit = ControlUnit(pc, data_path)
        try:
            for i in range(10):
                control_unit.decode_and_execute()
        except StopIteration:
            pass
        assert data_path.memory[0].arg == 10 + 5

    def test_mul_input(self):
        lines = [
            "RESULT: VAR 0",
            "START: LD (2046) # read from input device",
            "SUB '0'",
            "MUL 10",
            "ST RESULT",
            "HLT",
        ]
        instructions, pc = parse_lines(lines)
        data_path = DataPath("5", instructions)
        control_unit = ControlUnit(pc, data_path)
        try:
            for i in range(100):
                control_unit.decode_and_execute()
        except StopIteration:
            pass
        assert data_path.memory[0].arg == 50

    def test_output(self):
        lines = ["START: LD 'h'", "ST 2047", "HLT"]
        instructions, pc = parse_lines(lines)
        data_path = DataPath("", instructions)
        control_unit = ControlUnit(pc, data_path)
        try:
            for i in range(100):
                control_unit.decode_and_execute()
        except StopIteration:
            pass
        assert data_path.output == ["h"]

    def test_hello_world(self):
        lines = [
            "HELLO: VAR 'hello, world'",
            "I: VAR HELLO",
            "START: LD [I]",
            "ST 2047",
            "CMP 0",
            "JZ STOP",
            "LD (I)",
            "ADD 1",
            "ST I",
            "JMP START",
            "STOP: HLT",
        ]
        instructions, pc = parse_lines(lines)
        output, _, _ = simulate(instructions, pc, "")
        assert "hello, world\x00" == output

    def test_username(self):
        lines = [
            "BUFFER_START: VAR 500",
            "I: VAR 0",
            "START: LD (BUFFER_START)",
            "ST I",
            "CYCLE: LD (2046)",
            "ST (I)",
            "CMP 0",
            "JZ STOP",
            "LD (I)",
            "ADD 1",
            "ST I",
            "JMP CYCLE",
            "STOP: HLT",
        ]
        instructions, pc = parse_lines(lines)
        name = "Danis Akhmadeev\0"
        output, data_path, control_unit = simulate(instructions, pc, name)
        buffer = ""
        i = 500
        print(data_path.memory[i])
        while data_path.memory[i].arg != 0:
            buffer += chr(data_path.memory[i].arg)
            i += 1
        buffer += "\0"
        assert buffer == name
