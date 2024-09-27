from __future__ import annotations

import json
import re
import sys

from isa import Addressing, Instruction, Opcode


def parse_int_or_none(a: str) -> int | None:
    try:
        return int(a)
    except ValueError:
        return None


def is_label(s: str) -> bool:
    return s != "" and parse_int_or_none(s) is None and s[0] != "'" and s[-1] != "'"


def parse_lines(lines: list[str]) -> tuple[list[Instruction], int]:
    lines = expand_lines(remove_comment(lines))
    instructions = []
    labels = parse_labels(lines)
    for i in range(len(lines)):
        line = lines[i]
        if line.strip() == "":
            continue
        _, opcode, arg_raw = split_instruction(line)
        arg, addressing = parse_argument(arg_raw, labels)
        instructions += [Instruction(Opcode[opcode], arg, addressing)]
    pc = labels["START"] if "START" in labels else 0
    return instructions, pc


def parse_labels(lines: list[str]) -> dict[str, int]:
    labels = {}
    for i in range(len(lines)):
        line = lines[i]
        label, _, _ = split_instruction(line)
        if is_label(label):
            assert label not in labels, f"Labels must not have duplicates. See label {label}"
            labels[label] = i
    return labels


def parse_argument(arg: str, labels: dict[str, int]) -> tuple[int | None, Addressing | None]:
    if len(arg) == 0:
        return None, None
    addressing = parse_addressing(arg)
    if addressing is Addressing.IMMEDIATE:
        if arg[0] == "'" and arg[-1] == "'":  # is literal
            return ord(arg[1]), addressing
        if arg.isdecimal():
            return int(arg), addressing
        return labels[arg], addressing
    stripped = arg[1:-1]
    return int(stripped) if stripped.isdecimal() else labels[stripped], addressing


def parse_addressing(argument: str) -> Addressing:
    assert len(argument) != 0, "argument shouldn't be empty"
    if argument[0] == "(" and argument[-1] == ")":
        return Addressing.DIRECT
    if argument[0] == "[" and argument[-1] == "]":
        return Addressing.INDIRECT
    assert argument[0] not in ["[", "("]
    assert argument[-1] not in ["]", ")"]
    return Addressing.IMMEDIATE


def split_instruction(line: str) -> tuple[str, str, str]:
    """Парсит инструкцию и трансформирует ее в кортеж вида (метка, опкод, аргумент)"""
    pattern = re.compile(r"\s*(\w+:\s*)?(\w+)(\s*.+)?$")
    match = pattern.match(line)
    if match is None:
        return "", line, ""
    splitted = match.groups()
    label = splitted[0]
    opcode = splitted[1]
    arg = splitted[2]
    return (
        label.strip().split(":")[0] if label else "",
        opcode.strip(),
        arg.strip() if arg else "",
    )


def expand_lines(lines: list[str]) -> list[str]:
    """
    Переводит инструкции выделения памяти вида `VAR 's'`
    в набор инструкций:
    ````
    VAR 's[0]'
    VAR 's[1]'
    ...
    VAR 's[n-1]'
    VAR 0
    ```
    """
    ans = []
    var_pattern = re.compile(r"(\w+:\s)?VAR\s'(.+)'")
    for line in lines:
        match = var_pattern.match(line)
        if match is None:
            ans += [line]
            continue
        groups = match.groups()
        if len(groups) == 1:  # VAR 'test'
            label = None
            value = groups[0]
        else:
            label = groups[0]
            value = groups[1]
        if label:
            ans += [f"{label}VAR '{value[0]}'"]
            for c in value[1:]:
                ans += [f"VAR '{c}'"]
        else:
            for c in value:
                ans += [f"VAR '{c}'"]
        ans += ["VAR 0"]

    return ans


def convert_to_json(instructions: list[Instruction], pc: int) -> str:
    code = {
        "pc": pc,
        "instructions": instructions,
    }
    return json.dumps(code, indent=2)


def remove_comment(lines: list[str]) -> list[str]:
    return list(map(lambda line: line.split("#")[0].strip(), lines))


def main(input_file, output_file):
    with open(input_file, encoding="utf-8") as f:
        lines = f.readlines()
    instructions, pc = parse_lines(lines)
    json = convert_to_json(instructions, pc)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(json)
    print(f"Input file LoC: {len(lines)}")
    print(f"Code instr: {len(instructions)}")


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file> <target_file>"
    _, input_file, output_file = sys.argv
    main(input_file, output_file)
