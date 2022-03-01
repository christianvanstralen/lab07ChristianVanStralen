"""
cpu_tests.py File to test implementation of single-cycle MIPS CPU as
specified in assignment07.

Usage:  Place this file in the same directory as your cpu.py
        You can then run `pytest cpu_tests.py` to run all tests in this file
        Alternatively you can run specific tests by `pytest cpu_tests.py::test_name` such as
        `pytest cpu_tests.py::test_add_instr`

Note: If you fail a test, you can render the trace by adding `sim_trace.render_trace()` in the failing test
"""
from cpu import i_mem, d_mem, rf
from pyrtl import Simulation, SimulationTrace


def twos_comp(val, bits):
    """
    Compute the 2's complement of a value.
    NOTE: The code for this function was copied from:
        https://stackoverflow.com/questions/1604464/twos-complement-in-python

    :param val: Value to compute the 2's complement of
    :param bits: Number of bits to represent the val parameter
    :return: Two's complement of val
    """
    if (val & (1 << (bits - 1))) != 0: # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)        # compute negative value
    return val


def run_simulation(instruction_file=None, instruction_list=None, reg_map={}, mem_map={}):
    """
    Setup and run the simulation of CPU design.

    :param instruction_file: Text file containing MIPS instructions translated into hex.
    :param instruction_list: List of strings, each containing the hex of a MIPS instruction
    :param reg_map: Mapping of register initial values
    :param mem_map: Mapping of the data memory initial values
    :return: Tuple of (sim, sim_trace) where sim is of type pyrtl.Simulation and sim_trace is
        of type pyrtl.SimulationTrace
    """
    # Start a simulation trace
    sim_trace = SimulationTrace()

    # Initialize the i_mem with your instructions.
    i_mem_init = {}

    if instruction_file is not None:
        with open(instruction_file, 'r') as fin:
            i = 0
            for line in fin.readlines():
                i_mem_init[i] = int(line, 16)
                i += 1
    elif instruction_list is not None:
        i = 0
        for instr in instruction_list:
            i_mem_init[i] = int(instr, 16)
            i += 1
    else:
        raise Exception("You must provide a list of instructions or, a file containing the instructions")

    sim = Simulation(tracer=sim_trace, memory_value_map={
        i_mem: i_mem_init,
        rf: reg_map,
        d_mem: mem_map
    })

    # Run for an arbitrarily large number of cycles.
    for cycle in range(500):
        sim.step({})

    return sim, sim_trace


def test_given_instr():
    """
    Test the instructions given in the homework assignment
    """

    instructions = ['01004024', '01204824', '2129000a', '11090006', '01405024', '8d4b0000',
                    '216b0001', 'ad4b0000', '21080001', '1000fff9', '8c020000', '1042fffe']

    sim, sim_trace = run_simulation(instruction_list=instructions)

    assert (sim.inspect_mem(d_mem)[0] == 10)
    assert (sim.inspect_mem(rf)[8] == 10)  # $v0 = rf[8]


def test_lui_instr():
    """
    Test the LUI instruction.

    Perform 3 lui instructions
    First to $a1 expected value of 268500992
    Second to $zero, shouldn't do anything
    Third to $t8 expected value of 4294901760
    """

    instructions = ['3C051001', '3C001001', '3C18FFFF']

    sim, sim_trace = run_simulation(instruction_list=instructions)
    rf_result = sim.inspect_mem(rf)

    assert(rf_result[5] == 268500992)
    assert(0 not in rf_result)  # Assert lui to $zero, remains zero
    assert(rf_result[24] == 4294901760)


def test_add_instr():
    """
    Test the ADD instruction

    instr 0: add $t2, $t0, $t1 => $t2 = 5 + 10
    instr 1: add $t3, $t2, $t2 => $t2 = 15 + 15
    instr 2: add $zero, $t3, $t3 => $zero = 30 + 30 (shouldn't save to $zero)
    """
    initial_regs = {
        8: 5,
        9: 10
    }

    instructions = ['01095020', '014A5820', '016B0020']
    
    
    sim, sim_trace = run_simulation(instruction_list=instructions, reg_map=initial_regs)
    rf_result = sim.inspect_mem(rf)
    assert(rf_result[10] == 15)
    assert(rf_result[11] == 30)
    assert(0 not in rf_result)
    #sim_trace.render_trace(symbol_len=20, segement_size=1)

def test_and_instr():
    """
    Test the AND instruction

    instr 0: and $6, $4, $5 => 0xFFFFFFFF & 0x0000FFFF => 0x0000FFFF
    instr 1: and $7, $4, $4 => 0xFFFFFFFF & 0xFFFFFFFF => 0xFFFFFFFF
    instr 2: and $8, $4, $0 => 0xFFFFFFFF & 0x0000000 => 0x00000000
    instr 3: and $0, $4, $5 => 0xFFFFFFFF & 0x0000FFFF => 0x0000FFFF (shouldn't over write $0 though)
    """

    initial_regs = {
        4: 0xFFFFFFFF,
        5: 0x0000FFFF
    }

    instructions = ['00853024', '00843824', '00804024', '00850024']

    sim, sim_trace = run_simulation(instruction_list=instructions, reg_map=initial_regs)
    rf_result = sim.inspect_mem(rf)
    assert(rf_result[6] == 0x0000FFFF)
    assert(rf_result[7] == 0xFFFFFFFF)
    assert(rf_result[8] == 0)
    assert(0 not in rf_result)


def test_addi_instr():
    """
    Test the ADDI instruction

    instr 0: addi $10, $8, 5 => $10 should have (5+5)
    instr 1: addi $11, $8, -10 => $11 should have (5-10)=-5
    instr 2: addi $0, $8, 5 => (5+5) but shouldn't over write the $zero register
    """
    initial_regs = {
        8: 5,
    }

    instructions = ['210A0005', '210BFFF6', '21000005']

    sim, sim_trace = run_simulation(instruction_list=instructions, reg_map=initial_regs)
    rf_result = sim.inspect_mem(rf)

    assert(rf_result[10] == 10)
    assert(twos_comp(rf_result[11], 32) == -5)  # Need to get two's complement of value to compare
    assert(0 not in rf_result)


def test_sw_instr():
    """
    Test the sw instruction

    instr 0: sw $8, 1($zero) => save 5 in memory location (1+0)
    instr 1: sw $9, 2($zero) => save 15 in memory location (2+0)
    instr 2: sw $9, -2($8) => save 15 in memory location (5-2)
    """
    initial_regs = {
        8: 5,
        9: 15
    }

    instructions = ['AC080001', 'AC090002', 'AD09FFFE']

    sim, sim_trace = run_simulation(instruction_list=instructions, reg_map=initial_regs)
    d_mem_result = sim.inspect_mem(d_mem)

    assert(d_mem_result[1] == 5)
    assert(d_mem_result[2] == 15)
    assert(d_mem_result[3] == 15)


def test_lw_instr():
    """
    Test the lw instruction

    instr 0: lw $4, 1($0) => load value of 15 into register $a0 from data memory location 1
    instr 1: lw $5, -2($24) => load value of 30 into register $a1 from data memory location 3
    instr 2: lw $6, 0($4) => load value of -5 into register $a2 from data memory location 15 (from $a0)
    """
    initial_mem = {
        1: 15,
        3: 30,
        15: 0xFFFFFFFB
    }

    initial_regs = {
        24: 5
    }

    instructions = ['8C040001', '8F05FFFE', '8C860000']

    sim, sim_trace = run_simulation(instruction_list=instructions, mem_map=initial_mem, reg_map=initial_regs)
    rf_result = sim.inspect_mem(rf)

    assert(rf_result[4] == 15)
    assert(rf_result[5] == 30)
    assert(twos_comp(rf_result[6], 32) == -5)


def test_ori_instr():
    """
    Test the ori instruction

    instr 0: ori $4, $0, 65535 => set $a0 = 0x00000000 | 0x0000FFFF = 0x0000FFFF
    instr 1: ori $5, $16, -10 => set $a1 = 0xABCDEF00 | 0x0000FFF6 = 0xABCDFFF6
    """
    initial_regs = {
        16: 0xABCDEF00
    }

    instructions = ['3404FFFF', '3605FFF6']

    sim, sim_trace = run_simulation(instruction_list=instructions, reg_map=initial_regs)
    rf_result = sim.inspect_mem(rf)

    assert(rf_result[4] == 0x0000FFFF)
    assert(rf_result[5] == 0xABCDFFF6)


def test_slt_instr():
    """
    Test the slt instruction

    instr 0: slt $16, $4, $5 => set $16 = 1 since $4 = 5 < $5 = 10
    instr 1: slt $17, $5, $4 => set $17 = 0 since $5 = 10 !< $4 = 5
    instr 2: slt $18, $6, $7 => set $18 = 0 since $6 = -5 !< $5 = -10
    instr 3: slt $19, $7, $6 => set $19 = 1 since $5 = -10 < $6 = -5
    """
    initial_regs = {
        4: 5,
        5: 10,
        6: 0xFFFFFFFB,
        7: 0xFFFFFFF6
    }

    instructions = ['0085802A', '00A4882A', '00C7902A', '00E6982A']

    sim, sim_trace = run_simulation(instruction_list=instructions, reg_map=initial_regs)
    rf_result = sim.inspect_mem(rf)

    assert(rf_result[16] == 1)
    assert(rf_result[17] == 0)
    assert(rf_result[18] == 0)
    assert(rf_result[19] == 1)


def test_beq1_instr():
    """
    Test the beq instruction (Test 1), where a branch is taken with a positive offset

    Initialize registers 4, 5 with 10 (decimal)
    Then test the following MIPS instructions:
        beq $4, $5, 2
        add $6, $4, $5
        add $7, $4, $5
        add $8, $4, $4
    The branch should be taken, and we jump to the third add instruction.

    Note: When jumping we should not execute the first and second add instruction.
        Thus, we can test the branch was successful if nothing is saved in the rd registers
        for the first and second add instructions.
    """
    initial_regs = {
        4: 10,
        5: 10
    }
    instructions = ['10850002', '00853020', '00853820', '00844020']

    sim, sim_trace = run_simulation(instruction_list=instructions, reg_map=initial_regs)
    rf_result = sim.inspect_mem(rf)

    assert(rf_result[8] == 20)
    assert(6 not in rf_result)
    assert(7 not in rf_result)


def test_beq2_instr():
    """
    Test the beq instruction (Test 2), where a branch is not taken

    Initialize register 4 with 10 (decimal), register 5 with 5
    Then test the following MIPS instructions:
        beq $4, $5, 2
        add $6, $4, $5
        add $7, $4, $5
        add $8, $4, $4
    The branch should not be taken.
    Thus, we should execute all 3 add instructions.
    """
    initial_regs = {
        4: 10,
        5: 5
    }
    instructions = ['10850002', '00853020', '00853820', '00844020']

    sim, sim_trace = run_simulation(instruction_list=instructions, reg_map=initial_regs)
    rf_result = sim.inspect_mem(rf)

    assert(rf_result[6] == 15)
    assert(rf_result[7] == 15)
    assert(rf_result[8] == 20)


def test_beq_negative_offset():
    """
    Test the beq instruction with a negative offset.
    The test uses the following MIPS instructions with initial values in registers $5 => 5, $6 => 1, $7 => 5
        add $5, $5, $5
        add $6, $6, $6
        beq $5, $7, -3
        addi $8, $0, 1
    We expect the branch to occur, thus executing the two add instructions again.
    Therefore, we expect $5 => (5+5) => (10+10) and $6 => (1+1) => (2+2)
    """
    initial_regs = {
        5: 5,
        6: 1,
        7: 10,
    }

    instructions = ['00A52820', '00C63020', '10A7FFFD', '20080001']

    sim, sim_trace = run_simulation(instruction_list=instructions, reg_map=initial_regs)
    rf_result = sim.inspect_mem(rf)

    assert(rf_result[5] == 20)
    assert(rf_result[6] == 4)
    assert(rf_result[8] == 1)
