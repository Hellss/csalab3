from __future__ import annotations

import logging
import sys
from typing import ClassVar

from isa import (
    ALUOpcode,
    Opcode,
    Selectors,
    branch_instructions,
    one_parameter_instructions,
    read_code,
    two_parameter_instructions,
    zero_parameters_instructions,
)


class ALU:
    alu_operations: ClassVar[list[ALUOpcode]] = [
        ALUOpcode.INC_A,
        ALUOpcode.INC_B,
        ALUOpcode.DEC_A,
        ALUOpcode.DEC_B,
        ALUOpcode.ADD,
        ALUOpcode.SUB,
        ALUOpcode.MUL,
        ALUOpcode.DIV,
        ALUOpcode.MOD,
        ALUOpcode.TEST,
        ALUOpcode.SKIP_A,
        ALUOpcode.SKIP_B,
    ]

    def __init__(self):
        self.result = {
            "opcode": Opcode.NOP.value,
            "arg_1": None,
            "is_indirect_1": None,
            "arg_2": None,
            "is_indirect_2": None,
        }
        self.src_a = {
            "opcode": Opcode.NOP.value,
            "arg_1": None,
            "is_indirect_1": None,
            "arg_2": None,
            "is_indirect_2": None,
        }
        self.src_b = {
            "opcode": Opcode.NOP.value,
            "arg_1": None,
            "is_indirect_1": False,
            "arg_2": None,
            "is_indirect_2": None,
        }
        self.operation = None
        self.n_flag = False
        self.z_flag = True

    def calc(self):
        match self.operation:
            case ALUOpcode.INC_A:
                self.result = self.src_a.copy()
                self.result["arg_1"] = int(self.result["arg_1"]) + 1
                self.set_flags()
            case ALUOpcode.INC_B:
                self.result = self.src_b.copy()
                self.result["arg_1"] = int(self.result["arg_1"]) + 1
                self.set_flags()
            case ALUOpcode.DEC_A:
                self.result = self.src_a.copy()
                self.result["arg_1"] = int(self.result["arg_1"]) - 1
                self.set_flags()
            case ALUOpcode.DEC_B:
                self.result = self.src_b.copy()
                self.result["arg_1"] = int(self.result["arg_1"]) - 1
                self.set_flags()
            case ALUOpcode.ADD:
                self.result = self.src_a.copy()
                self.result["arg_1"] = int(self.src_a["arg_1"]) + int(self.src_b["arg_1"])
                self.set_flags()
            case ALUOpcode.SUB:
                self.result = self.src_a.copy()
                self.result["arg_1"] = int(self.src_a["arg_1"]) - int(self.src_b["arg_1"])
                self.set_flags()
            case ALUOpcode.MUL:
                self.result = self.src_a.copy()
                self.result["arg_1"] = int(self.src_a["arg_1"]) * int(self.src_b["arg_1"])
                self.set_flags()
            case ALUOpcode.DIV:
                self.result = self.src_a.copy()
                self.result["arg_1"] = int(self.src_a["arg_1"]) / int(self.src_b["arg_1"])
                self.set_flags()
            case ALUOpcode.MOD:
                self.result = self.src_a.copy()
                self.result["arg_1"] = int(self.src_a["arg_1"]) % int(self.src_b["arg_1"])
                self.set_flags()
            case ALUOpcode.TEST:
                self.result = self.src_a.copy()
                self.result["arg_1"] = int(self.src_a["arg_1"]) & int(self.src_b["arg_1"])
                self.set_flags()
            case ALUOpcode.SKIP_A:
                self.result = self.src_a.copy()
            case ALUOpcode.SKIP_B:
                self.result = self.src_b.copy()
            case _:
                error_message = f"Unknown ALU operation: {self.operation}"
                raise AssertionError(error_message)

    def set_flags(self):
        """Установка флагов на АЛУ"""

        self.n_flag = int(self.result["arg_1"]) < 0
        self.z_flag = int(self.result["arg_1"]) == 0 or self.result["arg_1"] is None

    def set_details(self, src_a: dict, src_b: dict, operation: ALUOpcode):
        """Обработка АЛУ команд с ControlUnit

        Указываются данные на входах в АЛУ и исполняемая операция
        """
        assert operation in ALU.alu_operations, f"Unknown ALU operation: {operation}"
        self.src_a = src_a
        self.src_b = src_b
        self.operation = operation


MEMORY_SIZE = 65536
MAX_ARG = 281474976710656  # 2 в 48 степени
INPUT_BUFFER_INDEX = 1
OUTPUT_STR_BUFFER_INDEX = 2
OUTPUT_INT_BUFFER_INDEX = 3


class DataPath:
    memory: list[dict[str, str]]  # Память, инициализируется nop-ами
    registers: list  # Регистры общего назначения, инициализируется нулями
    ps: dict[str, bool]  # Регистр состояния, инициализируется данным АЛУ
    dr: dict  # Регистр данных, инициализируется nop-ом
    ir: dict  # Регистр исполняемой инструкции, инициализируется nop-ом
    pc: dict  # Счетчик команд, инициализируется 0 адресом
    ar: int  # Регистр адреса, инициализируется 0 адресом
    input_buffer: list  # Входной буффер данных
    output_str_buffer: list  # Выходной буфер символов
    output_int_buffer: list  # Выходной буфер цифр
    alu: ALU  # АЛУ

    def __init__(self, input_buffer: list):
        self.alu = ALU()
        self.memory = [{"opcode": Opcode.NOP.value}] * MEMORY_SIZE
        self.registers = [
            {
                "opcode": Opcode.NOP.value,
                "arg_1": 0,
                "is_indirect_1": False,
                "arg_2": None,
                "is_indirect_2": None,
            }
        ] * 4
        self.ps = {"N": self.alu.n_flag, "Z": self.alu.z_flag}
        self.dr = {
            "opcode": Opcode.NOP.value,
            "arg_1": 0,
            "is_indirect_1": False,
            "arg_2": None,
            "is_indirect_2": None,
        }
        self.ir = {
            "opcode": Opcode.NOP.value,
            "arg_1": None,
            "is_indirect_1": None,
            "arg_2": None,
            "is_indirect_2": None,
        }
        self.pc = {
            "opcode": Opcode.NOP.value,
            "arg_1": 0,
            "is_indirect_1": False,
            "arg_2": None,
            "is_indirect_2": None,
        }
        self.ar = 0
        self.input_buffer = input_buffer
        self.output_str_buffer = []
        self.output_int_buffer = []

    def signal_fill_memory(self, program: list):
        """Заполнить память программой"""
        for mem_cell in program:
            index = mem_cell["index"]
            mem_cell.pop("index")
            self.memory[index] = mem_cell

    def read_from_input_buffer(self) -> dict:
        """Прочесть данные из входного буффера"""
        assert self.input_buffer != [], "Attempt to read from an empty input buffer"
        arg = ord(self.input_buffer[0]) if isinstance(self.input_buffer[0], str) else self.input_buffer[0]
        logging.debug("input: %s", repr(self.input_buffer[0]))
        self.input_buffer = self.input_buffer[1::]
        return {
            "opcode": Opcode.NOP.value,
            "arg_1": arg,
            "is_indirect_1": False,
            "arg_2": None,
            "is_indirect_2": None,
        }

    def read_from_memory(self) -> dict:
        """Прочесть данные из памяти"""
        assert self.ar >= 0, "Address below memory limit"
        assert self.ar <= MEMORY_SIZE, "Address above memory limit"
        assert self.ar not in [OUTPUT_STR_BUFFER_INDEX, OUTPUT_INT_BUFFER_INDEX], "Attempt to read from output buffer"

        if self.ar == INPUT_BUFFER_INDEX:
            result = self.read_from_input_buffer()
        else:
            result = self.memory[self.ar]
        return result

    def signal_latch_general_register(self, num: int, sel: Selectors):
        """Защелкнуть регистр общего назначения r<num>"""
        assert sel in [f"from_alu_to_r{num}", f"from_memory_to_r{num}"], f"Unknown selector '{sel}'"
        if sel == f"from_alu_to_r{num}":
            self.registers[num] = self.alu.result
        else:
            self.registers[num] = self.read_from_memory()

    def signal_latch_ps(self):
        """Защелкнуть регистр состояния"""
        self.ps["N"] = self.alu.n_flag
        self.ps["Z"] = self.alu.z_flag

    def signal_latch_dr(self):
        """Защелкнуть регистр данных"""
        self.dr = self.read_from_memory()

    def signal_latch_ir(self):
        """Защелкнуть регистр инструкции"""
        self.ir = self.read_from_memory()

    def signal_latch_pc(self):
        """Защелкнуть счетчик команд"""
        self.pc["arg_1"] = int(self.alu.result["arg_1"])

    def signal_latch_ar(self, sel: Selectors):
        """Защелкнуть регистр адреса"""
        assert sel in [Selectors.FROM_ADDR1_TO_AR, Selectors.FROM_ADDR2_TO_AR], f"Unknown selector '{sel}'"
        if sel == Selectors.FROM_ADDR1_TO_AR:
            self.ar = int(self.alu.result["arg_1"])
        else:
            self.ar = int(self.alu.result["arg_2"])

    def parse_data_to_write(self, sel: Selectors) -> dict:
        """Выделяет данные из регистров для записи в память"""
        reg_num = {
            Selectors.FROM_R0_TO_MEMORY: 0,
            Selectors.FROM_R1_TO_MEMORY: 1,
            Selectors.FROM_R2_TO_MEMORY: 2,
            Selectors.FROM_R3_TO_MEMORY: 3,
        }.get(sel)
        assert reg_num is not None, f"Unknown selector '{sel}'"
        return self.registers[reg_num]

    def signal_write(self, sel: Selectors):
        assert self.ar >= 0, "Address below memory limit"
        assert self.ar <= MEMORY_SIZE, "Address above memory limit"
        assert self.ar != INPUT_BUFFER_INDEX, "Attempt to write to input buffer"

        data_to_write = self.parse_data_to_write(sel)

        if self.ar == OUTPUT_STR_BUFFER_INDEX:
            logging.debug(
                "output_str_buffer: %s << %s",
                repr("".join(self.output_str_buffer)),
                repr(chr(int(data_to_write["arg_1"]))),
            )
            self.output_str_buffer.append(chr(int(data_to_write["arg_1"])))

        elif self.ar == OUTPUT_INT_BUFFER_INDEX:
            logging.debug(
                "output_int_buffer: [%s] << %d",
                ", ".join(map(str, self.output_int_buffer)),
                int(data_to_write["arg_1"]),
            )
            self.output_int_buffer.append(int(data_to_write["arg_1"]))
        else:
            self.memory[self.ar] = data_to_write

    def set_scr_a(self, left_sel: Selectors | None) -> dict:
        src_a = {}
        if left_sel is not None:
            assert left_sel in [
                Selectors.FROM_R0_TO_ALU_A,
                Selectors.FROM_R1_TO_ALU_A,
                Selectors.FROM_R2_TO_ALU_A,
                Selectors.FROM_R3_TO_ALU_A,
                Selectors.FROM_PC_TO_ALU_A,
            ], f"Unknown left selector '{left_sel}'"
            if left_sel == Selectors.FROM_R0_TO_ALU_A:
                src_a = self.registers[0]
            elif left_sel == Selectors.FROM_R1_TO_ALU_A:
                src_a = self.registers[1]
            elif left_sel == Selectors.FROM_R2_TO_ALU_A:
                src_a = self.registers[2]
            elif left_sel == Selectors.FROM_R3_TO_ALU_A:
                src_a = self.registers[3]
            elif left_sel == Selectors.FROM_PC_TO_ALU_A:
                src_a = self.pc
            else:
                error_message = f"Unknown left selector '{left_sel}"
                raise AssertionError(error_message)
        return src_a

    def set_scr_b(self, right_sel: Selectors | None) -> dict:
        src_b = {}
        if right_sel is not None:
            assert right_sel in [
                Selectors.FROM_R0_TO_ALU_B,
                Selectors.FROM_R1_TO_ALU_B,
                Selectors.FROM_R2_TO_ALU_B,
                Selectors.FROM_R3_TO_ALU_B,
                Selectors.FROM_DR_TO_ALU_B,
                Selectors.FROM_IR_TO_ALU_B,
            ], f"Unknown right selector '{right_sel}'"
            if right_sel == Selectors.FROM_R0_TO_ALU_B:
                src_b = self.registers[0]
            elif right_sel == Selectors.FROM_R1_TO_ALU_B:
                src_b = self.registers[1]
            elif right_sel == Selectors.FROM_R2_TO_ALU_B:
                src_b = self.registers[2]
            elif right_sel == Selectors.FROM_R3_TO_ALU_B:
                src_b = self.registers[3]
            elif right_sel == Selectors.FROM_DR_TO_ALU_B:
                src_b = self.dr
            elif right_sel == Selectors.FROM_IR_TO_ALU_B:
                src_b = self.ir
            else:
                error_message = f"Unknown right selector '{right_sel}'"
                raise AssertionError(error_message)
        return src_b

    def signal_execute_alu_op(self, operation, left_sel: Selectors | None = None, right_sel: Selectors | None = None):
        src_a = self.set_scr_a(left_sel)
        src_b = self.set_scr_b(right_sel)

        self.alu.set_details(src_a, src_b, operation)
        self.alu.calc()


class HaltError(Exception):
    def __init__(self, opcode):
        self.message = f"Met {opcode}"
        super().__init__(self.message)


class ControlUnit:
    data_path: DataPath
    ticks: int

    def __init__(self, program: list, data_path: DataPath):
        self.data_path = data_path
        self.ticks = 0
        data_path.signal_fill_memory(program)

    def tick(self):
        self.ticks += 1

    def instr_fetch(self):
        """Выборка инструкции"""
        self.data_path.signal_execute_alu_op(ALUOpcode.SKIP_A, left_sel=Selectors.FROM_PC_TO_ALU_A)
        self.tick()
        self.data_path.signal_latch_ar(Selectors.FROM_ADDR1_TO_AR)
        self.tick()
        self.data_path.signal_latch_ir()
        self.tick()

        self.data_path.signal_execute_alu_op(ALUOpcode.INC_A, left_sel=Selectors.FROM_PC_TO_ALU_A)
        self.tick()
        self.data_path.signal_latch_pc()
        self.tick()

    def operand_fetch(self):
        """Выборка операнд"""
        ir = self.data_path.ir
        if ir["is_indirect_1"]:
            self.data_path.signal_execute_alu_op(ALUOpcode.SKIP_B, right_sel=Selectors.FROM_IR_TO_ALU_B)
            self.data_path.signal_latch_ar(Selectors.FROM_ADDR1_TO_AR)
            self.data_path.signal_latch_dr()
            self.tick()

            self.data_path.signal_execute_alu_op(ALUOpcode.SKIP_B, right_sel=Selectors.FROM_DR_TO_ALU_B)
            self.data_path.signal_latch_ar(Selectors.FROM_ADDR1_TO_AR)
            self.tick()
        elif ir["is_indirect_2"]:
            self.data_path.signal_execute_alu_op(ALUOpcode.SKIP_B, right_sel=Selectors.FROM_IR_TO_ALU_B)
            self.data_path.signal_latch_ar(Selectors.FROM_ADDR2_TO_AR)
            self.data_path.signal_latch_dr()
            self.tick()

            self.data_path.signal_execute_alu_op(ALUOpcode.SKIP_B, right_sel=Selectors.FROM_DR_TO_ALU_B)
            self.data_path.signal_latch_ar(Selectors.FROM_ADDR1_TO_AR)
            self.tick()
        # теперь в AR лежит адрес данных, которые нужны

    def execute(self):
        """Выполнение инструкции"""
        ir, ps = self.data_path.ir, self.data_path.ps
        opcode = ir["opcode"]

        if opcode == Opcode.NOP:
            self.tick()
            return

        if opcode in zero_parameters_instructions:
            self.execute_zero_parameters_instruction(opcode)
        elif opcode in one_parameter_instructions:
            self.execute_one_parameters_instruction(opcode, ir)
        elif opcode in two_parameter_instructions:
            self.execute_two_parameters_instruction(opcode, ir)
        elif opcode in branch_instructions:
            self.execute_branch_instruction(opcode, ps)
        else:
            error_message = f"Unknown instruction {opcode}"
            raise AssertionError(error_message)

        if not str(self.data_path.alu.result["arg_1"]).startswith("r"):
            assert int(self.data_path.alu.result["arg_1"]) < MAX_ARG, "Value exceeded machine word"

    def execute_zero_parameters_instruction(self, opcode: Opcode):
        """Выполнение инструкции без аргументов"""
        if opcode == Opcode.HLT:
            self.tick()
            raise HaltError(Opcode.HLT)

    def set_selectors_one_params_instr(self, ir) -> tuple[int, Selectors, Selectors]:
        """Определить селекторы для инструкции с одним аргументом"""
        arg_1 = ir["arg_1"]
        assert arg_1 is not None, "None arg_1 in one parameters instruction"
        assert arg_1.startswith("r"), "Unknown register in one parameters instruction"

        num_reg = int(arg_1[1::])
        left_sel = Selectors[f"from_r{num_reg}_to_alu_a".upper()]
        result_reg_sel = Selectors[f"from_alu_to_r{num_reg}".upper()]
        return num_reg, left_sel, result_reg_sel

    def execute_one_parameters_instruction(self, opcode: Opcode, ir):
        """Выполнение инструкции с одним аргументом"""
        num_reg, left_sel, result_reg_sel = self.set_selectors_one_params_instr(ir)
        if opcode == Opcode.INC:
            self.data_path.signal_execute_alu_op(ALUOpcode.INC_A, left_sel=left_sel)
            self.data_path.signal_latch_general_register(num_reg, result_reg_sel)
            self.tick()
        elif opcode == Opcode.DEC:
            self.data_path.signal_execute_alu_op(ALUOpcode.DEC_A, left_sel=left_sel)
            self.data_path.signal_latch_general_register(num_reg, result_reg_sel)
            self.tick()

    def set_selectors_not_mov_two_params_instr(self, ir) -> tuple[int, int, Selectors, Selectors, Selectors]:
        """Определить селекторы для инструкции с двумя параметрами, не являющейся MOV"""
        arg_1 = ir["arg_1"]
        arg_2 = ir["arg_2"]
        assert arg_1 is not None, "None arg_1 in one parameters instruction"
        assert str(arg_1).startswith("r"), "Unknown register in one parameters instruction"
        assert arg_2 is not None, "None arg_2 in one parameters instruction"
        assert str(arg_2).startswith("r"), "Unknown register in one parameters instruction"

        num_reg_1 = int(arg_1[1::])
        num_reg_2 = int(arg_2[1::])
        left_sel = Selectors[f"from_r{num_reg_1}_to_alu_a".upper()]
        right_sel = Selectors[f"from_r{num_reg_2}_to_alu_b".upper()]
        result_reg_sel = Selectors[f"from_alu_to_r{num_reg_1}".upper()]
        return num_reg_1, num_reg_2, left_sel, right_sel, result_reg_sel

    def resolve_mov_instruction(self, ir):
        """Обработка операции MOV"""
        arg_1, is_indirect_1 = ir["arg_1"], ir["is_indirect_1"]
        arg_2, is_indirect_2 = ir["arg_2"], ir["is_indirect_2"]

        assert arg_1 is not None, "None arg_1 in one parameters instruction"
        assert arg_2 is not None, "None arg_2 in one parameters instruction"
        assert not (is_indirect_1 and is_indirect_2), "Double indirect addressing is prohibited"
        assert not (str(arg_1).startswith("r") and is_indirect_1), "Indirect addressing with regs is prohibited"
        assert not (str(arg_2).startswith("r") and is_indirect_2), "Indirect addressing with regs is prohibited"

        if str(arg_1).startswith("r"):  # Читаем откуда-то в регистр
            num_reg_1 = int(arg_1[1::])
            if str(arg_2).startswith("r"):  # Читаем из регистра в регистр
                num_reg_2 = int(arg_2[1::])
                self.data_path.signal_execute_alu_op(
                    ALUOpcode.SKIP_B, right_sel=Selectors[f"from_r{num_reg_2}_to_alu_b".upper()]
                )
                self.tick()
                self.data_path.signal_latch_general_register(num_reg_1, Selectors[f"from_alu_to_r{num_reg_1}".upper()])
                self.tick()
            else:  # Читаем из памяти в регистр
                if is_indirect_2:
                    self.data_path.signal_latch_general_register(
                        num_reg_1, Selectors[f"from_memory_to_r{num_reg_1}".upper()]
                    )
                    self.tick()
                else:
                    self.data_path.signal_execute_alu_op(ALUOpcode.SKIP_B, right_sel=Selectors.FROM_IR_TO_ALU_B)
                    self.tick()
                    self.data_path.signal_latch_ar(Selectors.FROM_ADDR2_TO_AR)
                    self.tick()
                    self.data_path.signal_latch_general_register(
                        num_reg_1, Selectors[f"from_memory_to_r{num_reg_1}".upper()]
                    )
                    self.tick()
        else:  # Записываем в память
            if str(arg_2).startswith("r"):  # Записываем в память из регистра
                num_reg_2 = int(arg_2[1::])
                if is_indirect_1:
                    self.data_path.signal_write(Selectors[f"from_r{num_reg_2}_to_memory".upper()])
                    self.tick()
                else:
                    self.data_path.signal_execute_alu_op(ALUOpcode.SKIP_B, right_sel=Selectors.FROM_IR_TO_ALU_B)
                    self.tick()
                    self.data_path.signal_latch_ar(Selectors.FROM_ADDR1_TO_AR)
                    self.tick()
                    self.data_path.signal_write(Selectors[f"from_r{num_reg_2}_to_memory".upper()])
                    self.tick()
            else:  # Попытка записать из памяти в память
                error_message = "Mem-to-mem operations prohibited"
                raise AssertionError(error_message)

    def execute_two_parameters_instruction(self, opcode: Opcode, ir):
        """Выполнение инструкции с одним аргументом"""
        if opcode == Opcode.MOV:
            self.resolve_mov_instruction(ir)
        else:
            num_reg_1, num_reg_2, left_sel, right_sel, result_reg_sel = self.set_selectors_not_mov_two_params_instr(ir)
            if opcode == Opcode.ADD:
                self.data_path.signal_execute_alu_op(ALUOpcode.ADD, left_sel=left_sel, right_sel=right_sel)
                self.tick()
                self.data_path.signal_latch_general_register(num_reg_1, result_reg_sel)
                self.tick()
            elif opcode == Opcode.SUB:
                self.data_path.signal_execute_alu_op(ALUOpcode.SUB, left_sel=left_sel, right_sel=right_sel)
                self.tick()
                self.data_path.signal_latch_general_register(num_reg_1, result_reg_sel)
                self.tick()
            elif opcode == Opcode.MUL:
                self.data_path.signal_execute_alu_op(ALUOpcode.MUL, left_sel=left_sel, right_sel=right_sel)
                self.tick()
                self.data_path.signal_latch_general_register(num_reg_1, result_reg_sel)
                self.tick()
            elif opcode == Opcode.DIV:
                self.data_path.signal_execute_alu_op(ALUOpcode.DIV, left_sel=left_sel, right_sel=right_sel)
                self.tick()
                self.data_path.signal_latch_general_register(num_reg_1, result_reg_sel)
                self.tick()
            elif opcode == Opcode.MOD:
                self.data_path.signal_execute_alu_op(ALUOpcode.MOD, left_sel=left_sel, right_sel=right_sel)
                self.tick()
                self.data_path.signal_latch_general_register(num_reg_1, result_reg_sel)
                self.tick()
            elif opcode == Opcode.TEST:
                self.data_path.signal_execute_alu_op(ALUOpcode.TEST, left_sel=left_sel, right_sel=right_sel)
                self.tick()
                self.data_path.signal_latch_general_register(num_reg_1, result_reg_sel)
                self.tick()

    def execute_branch_instruction(self, opcode: Opcode, ps: dict):
        if opcode == Opcode.JG:
            if not ps["N"]:
                self.data_path.signal_execute_alu_op(ALUOpcode.SKIP_B, right_sel=Selectors.FROM_IR_TO_ALU_B)
                self.data_path.signal_latch_pc()
                self.tick()
        elif opcode == Opcode.JNG:
            if ps["N"]:
                self.data_path.signal_execute_alu_op(ALUOpcode.SKIP_B, right_sel=Selectors.FROM_IR_TO_ALU_B)
                self.data_path.signal_latch_pc()
                self.tick()
        elif opcode == Opcode.JZ:
            if ps["Z"]:
                self.data_path.signal_execute_alu_op(ALUOpcode.SKIP_B, right_sel=Selectors.FROM_IR_TO_ALU_B)
                self.data_path.signal_latch_pc()
                self.tick()
        elif opcode == Opcode.JNZ:
            if not ps["Z"]:
                self.data_path.signal_execute_alu_op(ALUOpcode.SKIP_B, right_sel=Selectors.FROM_IR_TO_ALU_B)
                self.data_path.signal_latch_pc()
                self.tick()
        elif opcode == Opcode.JMP:
            self.data_path.signal_execute_alu_op(ALUOpcode.SKIP_B, right_sel=Selectors.FROM_IR_TO_ALU_B)
            self.data_path.signal_latch_pc()
            self.tick()

    def decode_and_execute_instruction(self):
        self.instr_fetch()
        self.operand_fetch()
        self.execute()
        self.data_path.signal_latch_ps()

        logging.debug("%s", self)

    def ir_to_str(self, ir: dict) -> str:
        if ir["is_indirect_1"]:
            arg_1 = f"({ir['arg_1']})"
        else:
            arg_1 = ir["arg_1"]

        if ir["is_indirect_2"]:
            arg_2 = f"({ir['arg_2']})"
        else:
            arg_2 = ir["arg_2"]

        if arg_2 is None:
            result = f"{ir['opcode']} {arg_1}"
        else:
            result = f"{ir['opcode']} {arg_1}, {arg_2}"
        return result

    def __repr__(self) -> str:
        return " INSTR: {:12} | R0: {:8} | R1: {:8} | R2: {:8} | R3: {:8} | N: {:1} | Z: {:1} | PC: {:4}".format(
            self.ir_to_str(self.data_path.ir),
            int(self.data_path.registers[0]["arg_1"]),
            int(self.data_path.registers[1]["arg_1"]),
            int(self.data_path.registers[2]["arg_1"]),
            int(self.data_path.registers[3]["arg_1"]),
            (1 if self.data_path.ps["N"] else 0),
            (1 if self.data_path.ps["Z"] else 0),
            self.data_path.pc["arg_1"],
        )


def simulation(code: list, input_tokens: list, limit: int) -> tuple[list, list, int, int]:
    data_path = DataPath(input_tokens)
    control_unit = ControlUnit(code, data_path)
    instr_counter = 0

    try:
        while instr_counter < limit:
            control_unit.decode_and_execute_instruction()
            instr_counter += 1
    except HaltError:
        pass

    if instr_counter >= limit:
        logging.warning("Limit exceeded!")
    logging.info("output_str_buffer: %s", repr("".join(data_path.output_str_buffer)))
    logging.info("output_int_buffer: [%s]", ", ".join(str(x) for x in data_path.output_int_buffer))
    symbols = data_path.output_str_buffer
    numbers = data_path.output_int_buffer
    return symbols, numbers, instr_counter, control_unit.ticks


def parse_to_tokens(input_file: str) -> list:
    try:
        with open(input_file, encoding="utf-8") as file:
            input_text = file.read()
        input_token = eval(input_text)
    except Exception:
        input_token = []
    return input_token


def main(code_file: str, input_file: str):
    code = read_code(code_file)
    input_token = parse_to_tokens(input_file)

    output_symbols, output_numbers, instr_counter, ticks_counter = simulation(code, input_token, limit=50000)

    print("".join(output_symbols))
    print(output_numbers)
    print("instr_counter: %5d" % instr_counter)
    print("ticks_counter: %5d" % ticks_counter)


FORMAT = "%(levelname)s    %(filename)s    %(message)s"


if __name__ == "__main__":
    logging.basicConfig(format=FORMAT)
    logging.getLogger().setLevel(logging.DEBUG)

    assert len(sys.argv) == 3, "Usage: machine.py <code_file> <input_file>"
    _, code_file, input_file = sys.argv
    main(code_file, input_file)
