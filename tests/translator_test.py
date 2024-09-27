import unittest

import pytest
from isa import Addressing, Instruction, Opcode
from translator import expand_lines, parse_labels, parse_lines, remove_comment, split_instruction


class TestTranslator(unittest.TestCase):
    def test_translate_no_arg(self):
        lines = ["HLT", "", ""]
        transformed, _ = parse_lines(lines)
        expected = [Instruction(Opcode.HLT, None, None)]
        assert transformed == expected

    def test_translate_complex(self):
        lines = ["START: LD (KEKW)", "JMP (START)", "KEKW: VAR 'a'"]
        transformed, _ = parse_lines(lines)
        expected = [
            Instruction(Opcode.LD, 2, Addressing.DIRECT),
            Instruction(Opcode.JMP, 0, Addressing.DIRECT),
            Instruction(Opcode.VAR, ord("a"), Addressing.IMMEDIATE),
            Instruction(Opcode.VAR, 0, Addressing.IMMEDIATE),
        ]
        assert transformed == expected

    def test_first_pass(self):
        lines = [
            "LABEL1: HLT",
            "LABEL2: JMP LABEL1",
        ]
        expected_labels = {
            "LABEL1": 0,
            "LABEL2": 1,
        }
        actual = parse_labels(lines)
        assert actual == expected_labels

    def test_parse_instruction_no_label(self):
        line = "\t\t\tLD\t\tABSD\t\t"
        expected = ("", "LD", "ABSD")
        assert split_instruction(line) == expected

    def test_parse_instruction_no_arg(self):
        line = "\t\tKEKW:\t\tHLT\t\t\t\t"
        expected = ("KEKW", "HLT", "")
        assert split_instruction(line) == expected

    def test_parse_instruction_no_arg_no_label(self):
        line = "\t\t\tHLT\t\t\t\t"
        expected = ("", "HLT", "")
        assert split_instruction(line) == expected

    def test_parse_instruction(self):
        line = "\t\tCOOLLABEL: \tADD\t\tSOMETHING\t\t\t\n"
        expected = ("COOLLABEL", "ADD", "SOMETHING")
        assert split_instruction(line) == expected

    def test_parse_no_arg(self):
        lines = ["HLT"]
        expected = [Instruction(Opcode.HLT, None, None)]
        transformed, _ = parse_lines(lines)
        assert transformed == expected

    def test_translate_indirect(self):
        lines = ["KEK: LD [LOL]", "LOL: LD [KEK]"]
        expected = [
            Instruction(Opcode.LD, 1, Addressing.INDIRECT),
            Instruction(Opcode.LD, 0, Addressing.INDIRECT),
        ]
        transformed, _ = parse_lines(lines)
        assert transformed == expected

    def test_immediate(self):
        lines = ["ADD 10", "LD 'a'"]
        expected = [
            Instruction(Opcode.ADD, 10, Addressing.IMMEDIATE),
            Instruction(Opcode.LD, ord("a"), Addressing.IMMEDIATE),
        ]
        transformed, _ = parse_lines(lines)
        assert transformed == expected

    def test_expand_instructions_with_label(self):
        lines = ["ADD 'a'", "TEST: VAR 'hell'"]
        expected = [
            "ADD 'a'",
            "TEST: VAR 'h'",
            "VAR 'e'",
            "VAR 'l'",
            "VAR 'l'",
            "VAR 0",
        ]
        assert expand_lines(lines) == expected

    def test_expand_instructions_without_label(self):
        lines = ["ADD 'a'", "VAR 'hell'"]
        expected = ["ADD 'a'", "VAR 'h'", "VAR 'e'", "VAR 'l'", "VAR 'l'", "VAR 0"]
        assert expand_lines(lines) == expected

    def test_expand_instructions_long_word(self):
        lines = ["VAR 'hello, world'"]
        expected = [
            "VAR 'h'",
            "VAR 'e'",
            "VAR 'l'",
            "VAR 'l'",
            "VAR 'o'",
            "VAR ','",
            "VAR ' '",
            "VAR 'w'",
            "VAR 'o'",
            "VAR 'r'",
            "VAR 'l'",
            "VAR 'd'",
            "VAR 0",
        ]
        assert expand_lines(lines) == expected

    def test_label_duplicate(self):
        lines = ["LABEL: HLT", "LABEL: HLT"]
        pytest.raises(AssertionError, lambda: parse_lines(lines))

    def test_remove_comment(self):
        lines = ["# comment", "VAR 'a' # comment"]
        expected = ["", "VAR 'a'"]
        actual = remove_comment(lines)
        assert actual == expected
