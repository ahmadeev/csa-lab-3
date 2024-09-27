import unittest

import pytest
from machine import DataPath


class DataPathTest(unittest.TestCase):
    def test_read_input(self):
        datapath = DataPath("kek")
        datapath.address_register = 2046
        datapath.signal_read_memory()
        assert ord("k") == datapath.mem_out.arg
        datapath.signal_read_memory()
        assert ord("e") == datapath.mem_out.arg
        datapath.signal_read_memory()
        assert ord("k") == datapath.mem_out.arg
        pytest.raises(EOFError, datapath.signal_read_memory)

    def test_write_memory(self):
        datapath = DataPath("")
        datapath.alu.out = 1024
        datapath.address_register = 521
        datapath.signal_write_memory()
        assert 1024 == datapath.memory[521].arg
