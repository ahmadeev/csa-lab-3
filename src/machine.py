from __future__ import annotations

import logging
import sys
from enum import Enum

from alu import ALU
from isa import Addressing, Instruction, Opcode, is_arithmetic_instruction, read_json


class RegisterSelector(Enum):
    ALU = "alu"
    MEM = "mem"
    PC = "pc"


class DataPath:
    accumulator: int
    address_register: int
    mem_out: Instruction | None

    def __init__(self, input_str: str, initial_memory: list[Instruction] = []):
        """
        Для простоты реализации в памяти хранятся инструкции.
        чтобы сохранить число необходимо указать `Opcode.VAR` и `Addressing.Immediate`
        """
        self.memory = [Instruction(Opcode.VAR, 0, Addressing.IMMEDIATE)] * 2046

        for i in range(len(initial_memory)):
            self.memory[i] = initial_memory[i]

        self.address_register: int = 0
        self.accumulator: int = 0
        self.input = input_str
        self.output: list[str] = []
        self.alu = ALU()
        self.mem_out = None
        self.logger = logging.getLogger(self.__class__.__name__)
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(
            logging.Formatter(
                "%(name)s\t%(levelname)s\tacc: %(acc)5d, ar: %(ar)4d, alu: %(alu_out)5d, mem_out: %(mem_out)5d\t\t\t\t%(message)s"
            )
        )
        self.logger.addHandler(sh)
        self.logger.setLevel(logging.DEBUG)

    def _get_extra(self):
        return {
            "acc": self.accumulator,
            "ar": self.address_register,
            "alu_out": self.alu.out,
            "mem_out": self.mem_out.arg if (self.mem_out is not None and self.mem_out.arg is not None) else 0,
        }

    def signal_read_memory(self):
        assert self.address_register != 2047, "program tried to read from output port"
        self.logger.debug(f"Reading memory on AR #{self.address_register}", extra=self._get_extra())
        if self.address_register == 2046:  # Input
            if len(self.input) == 0:
                self.logger.warning("Input buffer is empty!")
                raise EOFError()
            symbol = ord(self.input[0])
            self.logger.info(f"Input: {self.input[0]!r} ({symbol})", extra=self._get_extra())
            self.input = self.input[1:]
            self.mem_out = Instruction(Opcode.VAR, symbol, Addressing.IMMEDIATE)
            self.logger.debug(f"MEM_OUT <- {chr(symbol)!r} ({symbol})", extra=self._get_extra())
            return
        assert 0 <= self.address_register < 2046
        self.mem_out = self.memory[self.address_register]
        self.logger.debug(f"MEM_OUT <- MEM[{self.address_register}]", extra=self._get_extra())

    def signal_write_memory(self):
        assert self.address_register != 2046, "program tried to write to input port"
        self.logger.debug(f"Writing to memory on AR #{self.address_register}", extra=self._get_extra())
        if self.address_register == 2047:
            char = chr(self.alu.out)
            self.logger.info(f"Output: {chr(self.alu.out)!r} ({self.alu.out})", extra=self._get_extra())
            self.output += [char]
            return
        assert 0 <= self.address_register < 2046
        self.memory[self.address_register] = Instruction(Opcode.VAR, self.alu.out)
        self.logger.debug(f"MEM[{self.address_register}] <- {self.alu.out}", extra=self._get_extra())

    def signal_latch_address_register(self, sel: RegisterSelector, pc: int):
        if sel is RegisterSelector.ALU:
            self.address_register = self.alu.out
            self.logger.debug("AR <- ALU_OUT", extra=self._get_extra())
        elif sel is RegisterSelector.PC:
            self.address_register = pc
            self.logger.debug("AR <- PC", extra=self._get_extra())
        elif sel is RegisterSelector.MEM:
            assert self.mem_out is not None, "mem_out should not be None"
            assert self.mem_out.arg is not None, "mem_out should have an argument"
            self.address_register = self.mem_out.arg
            self.logger.debug("AR <- MEM_OUT", extra=self._get_extra())

    def signal_latch_accumulator(self, sel: RegisterSelector, pc: int):
        if sel is RegisterSelector.ALU:
            self.accumulator = self.alu.out
            self.logger.debug("ACC <- ALU_OUT", extra=self._get_extra())
        elif sel is RegisterSelector.PC:
            self.accumulator = pc
            self.logger.debug("ACC <- PC", extra=self._get_extra())
        elif sel is RegisterSelector.MEM:
            assert self.mem_out is not None, "mem_out should not be None"
            assert self.mem_out.arg is not None, "mem_out should have an argument"
            self.accumulator = self.mem_out.arg
            self.logger.debug("ACC <- MEM_OUT", extra=self._get_extra())


class ControlUnit:
    program: Instruction
    program_counter: int
    data_path: DataPath

    address: int
    operand: int

    _tick: int = 0
    _instruction_number: int = 0

    def tick(self):
        self._tick += 1
        self.logger.debug("tick!", extra=self.get_extra())

    def get_current_tick(self) -> int:
        return self._tick

    def get_instruction_number(self) -> int:
        return self._instruction_number

    def get_extra(self):
        return {
            "instruction": self._instruction_number,
            "tick": self.get_current_tick(),
            "pc": self.program_counter,
            "acc": self.data_path.accumulator,
            "ar": self.data_path.address_register,
            "mem_out": self.data_path.mem_out.arg
            if (self.data_path.mem_out is not None and self.data_path.mem_out.arg is not None)
            else 0,
        }

    def __init__(self, pc: int, data_path: DataPath):
        self.program_counter = pc
        self.data_path = data_path
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.handlers.clear()
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(
            logging.Formatter(
                "%(name)s\t%(levelname)s\tPC: %(pc)4d, tick: %(tick)6d, instr: %(instruction)5d, acc: %(acc)5d, mem_out: %(mem_out)5d, "
                "ar: %(ar)4d\t%(message)s"
            )
        )
        self.logger.addHandler(sh)
        self.logger.setLevel(logging.DEBUG)

    def signal_latch_pc(self, sel: bool):
        if sel:
            assert self.data_path.mem_out is not None, "mem_out should not be None"
            assert self.data_path.mem_out.arg is not None, "instruction should have an argument"
            self.program_counter = self.data_path.mem_out.arg
            self.logger.debug("PC <- MEM_OUT", extra=self.get_extra())
        else:
            self.program_counter = self.program_counter + 1
            self.logger.debug("PC <- PC + 1", extra=self.get_extra())

    def signal_latch_address_register(self, sel: RegisterSelector):
        self.data_path.signal_latch_address_register(sel, self.program_counter)

    def signal_latch_accumulator(self, sel: RegisterSelector):
        self.data_path.signal_latch_accumulator(sel, self.program_counter)

    def signal_latch_program(self):
        self.program = self.data_path.mem_out

    def program_fetch(self):
        self.signal_latch_address_register(
            RegisterSelector.PC,
        )
        self.data_path.signal_read_memory()
        self.signal_latch_program()
        self.tick()

    def address_fetch(self):
        """
        Цикл получения адреса операнда.
        До него в program лежит текущая программа
        После него AR содержит адрес операнда текущей инструкции.
        """
        assert self.program is not None
        if self.program.addressing is Addressing.IMMEDIATE:
            return
        if self.program.addressing is Addressing.DIRECT:
            self.signal_latch_address_register(RegisterSelector.MEM)
        if self.program.addressing is Addressing.INDIRECT:
            self.signal_latch_address_register(RegisterSelector.MEM)
            self.data_path.signal_read_memory()
            self.tick()
            self.signal_latch_address_register(RegisterSelector.MEM)

    def operand_fetch(self):
        """
        Цикл получения операнда.
        До него адрес операнда лежит в AR.
        После него MEM_OUT содержит операнд текущей инструкции.
        """
        assert self.program is not None
        if self.program.addressing is Addressing.IMMEDIATE or self.program.addressing is None:
            return
        self.data_path.signal_read_memory()
        self.tick()

    def _execute_ld(self):
        self.signal_latch_accumulator(
            RegisterSelector.MEM,
        )
        self.signal_latch_pc(False)
        self.tick()

    def _execute_arithmetic(self):
        self.data_path.alu.signal_sel_left(self.data_path.mem_out.arg, True)
        self.data_path.alu.signal_sel_right(self.data_path.accumulator, True)
        self.data_path.alu.signal_alu_operation(self.program.opcode)
        if self.program.opcode is not Opcode.CMP:
            self.signal_latch_accumulator(
                RegisterSelector.ALU,
            )
        self.signal_latch_pc(False)
        self.tick()

    def _execute_st(self):
        self.signal_latch_address_register(
            RegisterSelector.MEM,
        )
        # Pass accumulator through the ALU
        self.data_path.alu.signal_sel_left(self.data_path.mem_out.arg, False)
        self.data_path.alu.signal_sel_right(self.data_path.accumulator, True)
        self.data_path.alu.signal_alu_operation(Opcode.ADD)
        self.data_path.signal_write_memory()
        self.signal_latch_pc(False)
        self.tick()

    def execute(self):
        assert self.program.opcode is not Opcode.VAR, "program tried to execute VAR instruction"
        if self.program.opcode is Opcode.HLT:
            raise StopIteration()
        if self.program.opcode is Opcode.LD:
            self._execute_ld()
        if self.program.opcode is Opcode.ST:
            self._execute_st()
        elif is_arithmetic_instruction(self.program.opcode):
            self._execute_arithmetic()
        elif self.program.opcode is Opcode.JMP:
            self.signal_latch_pc(True)
            self.tick()
        elif self.program.opcode is Opcode.JZ:
            self.signal_latch_pc(self.data_path.alu.zero)
            self.tick()

    def decode_and_execute(self):
        ticks_before = self.get_current_tick()
        self.program_fetch()
        self.address_fetch()
        self.operand_fetch()
        self.execute()
        self._instruction_number += 1
        ticks_after = self.get_current_tick()
        self.logger.info(
            f"Executed instruction `{self.program}` in {ticks_after - ticks_before} ticks", extra=self.get_extra()
        )


def simulate(
    instructions: list[Instruction], pc: int, input_text: str, debug_mode: bool = False
) -> tuple[str, DataPath, ControlUnit]:
    data_path = DataPath(input_text, instructions)
    data_path.logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)
    control_unit = ControlUnit(pc, data_path)
    control_unit.logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)
    try:
        for i in range(1000000):
            control_unit.decode_and_execute()
    except StopIteration:
        print("Program halted successfully")
    except EOFError:
        print("Program tried to read empty input")
    return "".join(data_path.output), data_path, control_unit


def main(code_file: str, input_file: str, debug: bool):
    with open(input_file) as f:
        input_text = f.read()
        input_text += "\0"
    with open(code_file) as f:
        instructions, pc = read_json(f.read())
    output, _datapath, _control_unit = simulate(instructions, pc, input_text, debug)
    print(output)
    print("Total instructions", _control_unit.get_instruction_number())
    print("Total ticks", _control_unit.get_current_tick())


if __name__ == "__main__":
    assert len(sys.argv) in [3, 4], "Wrong arguments: machine.py <code_file> <input_file> <debug: true | false>"
    _, code_file, input_file = sys.argv[:3]
    debug = (sys.argv[3].lower() == "true") if len(sys.argv) == 4 else False
    main(code_file, input_file, debug)
