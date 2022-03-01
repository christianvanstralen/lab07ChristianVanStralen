import pyrtl
from pyrtl import Const

i_mem = pyrtl.MemBlock(bitwidth=32, addrwidth=32, name='i_mem')
d_mem = pyrtl.MemBlock(bitwidth=32, addrwidth=32, name='d_mem', asynchronous=True)
rf    = pyrtl.MemBlock(bitwidth=32, addrwidth=5, name='rf', asynchronous=True)

PC = pyrtl.Register(bitwidth=32, name='PC')
instr = pyrtl.WireVector(bitwidth=32, name = 'instr')
instr <<= i_mem[PC]

op = pyrtl.WireVector(bitwidth=6, name='op')
rs = pyrtl.WireVector(bitwidth=5, name='rs')
rt = pyrtl.WireVector(bitwidth=5, name='rt')
rd = pyrtl.WireVector(bitwidth=5, name='rd')
sh = pyrtl.WireVector(bitwidth=5, name='sh')
funct = pyrtl.WireVector(bitwidth=6, name='funct')
imm = pyrtl.WireVector(bitwidth=16, name='imm')
addr = pyrtl.WireVector(bitwidth=26, name='addr')

read_reg1 = pyrtl.WireVector(bitwidth=5, name='read_reg1')
read_reg2 = pyrtl.WireVector(bitwidth=5, name='read_reg2')
write_reg = pyrtl.WireVector(bitwidth=5, name='write_reg')
w_data_reg = pyrtl.WireVector(bitwidth=32, name='w_data_reg')
sign_ext_immed = pyrtl.WireVector(bitwidth=32, name='sign_ext_immed')
zero_ext_immed = pyrtl.WireVector(bitwidth=32, name='zerp_ext_immed')
read_data1 = pyrtl.WireVector(bitwidth=32, name='read_data1')
read_data2 = pyrtl.WireVector(bitwidth=32, name='read_data2')
data3 = pyrtl.WireVector(bitwidth=32, name='data3')
result = pyrtl.WireVector(bitwidth=32, name='result')
w_data_mem = pyrtl.WireVector(bitwidth=32, name='w_data_mem')
read_data_mem = pyrtl.WireVector(bitwidth=32, name='read_data_mem')

op <<= instr[26:32]
rs <<= instr[21:26]
rt <<= instr[16:21]
rd <<= instr[11:16]
sh <<= instr[6:11]
funct <<= instr[0:6]
imm <<= instr[0:16]
addr <<= instr[0:26]
read_reg1 <<= rs #may not need?
read_reg2 <<= rt
read_data1 <<= rf[rs]
read_data2 <<= rf[rt]
sign_ext_immed <<= imm.sign_extended(32)
zero_ext_immed <<= imm.zero_extended(32)

control_signals = pyrtl.WireVector(bitwidth=10, name='control_signals')
with pyrtl.conditional_assignment:
    with op == 0:
        with funct == 32: #add
            control_signals |= 0x280
        with funct == 36: #and
            control_signals |= 0x281
        with funct == 42: #slt
            control_signals |= 0x284
    with op == 8: #addi
        control_signals |= 0x0A0
    with op == 15: #lui
        control_signals |= 0x0C2
    with op == 13: #ori
        control_signals |= 0x0C3
    with op == 35: #lw
        control_signals |= 0x0A8
    with op == 43: #sw
        control_signals |= 0x030
    with op == 4: #beq
        control_signals |= 0x107

reg_dst = pyrtl.WireVector(bitwidth=1, name='reg_dst')
branch = pyrtl.WireVector(bitwidth=1, name='branch')
reg_write = pyrtl.WireVector(bitwidth=1, name='reg_write')
alu_src = pyrtl.WireVector(bitwidth=2, name='alu_src')
mem_write = pyrtl.WireVector(bitwidth=1, name='mem_write')
mem_to_reg = pyrtl.WireVector(bitwidth=1, name='mem_to_reg')
alu_op = pyrtl.WireVector(bitwidth=3, name='alu_op')
zero = pyrtl.WireVector(bitwidth=1, name='zero')

reg_dst <<= control_signals[9]
branch <<= control_signals[8]
reg_write <<= control_signals[7]
alu_src <<= control_signals[5:7]
mem_write <<= control_signals[4]
mem_to_reg <<= control_signals[3]
alu_op <<= control_signals[0:3]

with pyrtl.conditional_assignment:
    with branch == 1:
        with zero == 1:
            PC.next |= PC + 1 + sign_ext_immed
    with branch == 0:
        PC.next |= PC + 1


with pyrtl.conditional_assignment:
    with alu_src == 0:
        data3 |= read_data2
    with alu_src == 1:
        data3 |= sign_ext_immed
    with alu_src == 2:
        data3 |= zero_ext_immed

with pyrtl.conditional_assignment:
    with alu_op == 0: #add (add, addi, lw, sw)
        result |= read_data1 + data3
    with alu_op == 1: #and (and)
        result |= read_data1 & data3
    with alu_op == 2: #sll (lui)
        result |= pyrtl.shift_left_logical(data3, Const(16))
    with alu_op == 3: #or (ori)
        result |= read_data1 | data3
    with alu_op == 4: #slt (slt)
        result |= pyrtl.corecircuits.signed_lt(read_data1,data3)
    with alu_op == 7: #equal (beq)
        with read_data1 == data3:
            zero |= 1

read_data_mem <<= d_mem[result]
d_mem[result] <<= pyrtl.MemBlock.EnabledWrite(read_data2,enable=mem_write)

with pyrtl.conditional_assignment:
    with mem_to_reg == 1:
        w_data_reg |= result
    with mem_to_reg == 0:
        w_data_reg |= read_data_mem
        
with pyrtl.conditional_assignment:
    with reg_dst == 1:
        write_reg |= rd
    with reg_dst == 0:
        write_reg |= rt

rf[write_reg] <<= pyrtl.MemBlock.EnabledWrite(w_data_reg,enable=reg_write)
    
    
        


if __name__ == '__main__':

    """

    Here is how you can test your code.
    This is very similar to how the autograder will test your code too.

    1. Write a MIPS program. It can do anything as long as it tests the
       instructions you want to test.

    2. Assemble your MIPS program to convert it to machine code. Save
       this machine code to the "i_mem_init.txt" file.
       You do NOT want to use QtSPIM for this because QtSPIM sometimes
       assembles with errors. One assembler you can use is the following:

       https://alanhogan.com/asu/assembler.php

    3. Initialize your i_mem (instruction memory).

    4. Run your simulation for N cycles. Your program may run for an unknown
       number of cycles, so you may want to pick a large number for N so you
       can be sure that the program has "finished" its business logic.

    5. Test the values in the register file and memory to make sure they are
       what you expect them to be.

    6. (Optional) Debug. If your code didn't produce the values you thought
       they should, then you may want to call sim.render_trace() on a small
       number of cycles to see what's wrong. You can also inspect the memory
       and register file after every cycle if you wish.

    Some debugging tips:

        - Make sure your assembly program does what you think it does! You
          might want to run it in a simulator somewhere else (SPIM, etc)
          before debugging your PyRTL code.

        - Test incrementally. If your code doesn't work on the first try,
          test each instruction one at a time.

        - Make use of the render_trace() functionality. You can use this to
          print all named wires and registers, which is extremely helpful
          for knowing when values are wrong.

        - Test only a few cycles at a time. This way, you don't have a huge
          500 cycle trace to go through!

    """

    # Start a simulation trace
    sim_trace = pyrtl.SimulationTrace()

    # Initialize the i_mem with your instructions.
    i_mem_init = {}
    with open('i_mem_init.txt', 'r') as fin:
        i = 0
        for line in fin.readlines():
            i_mem_init[i] = int(line, 16)
            i += 1

    sim = pyrtl.Simulation(tracer=sim_trace, memory_value_map={
        i_mem : i_mem_init
    })

    # Run for an arbitrarily large number of cycles.
    for cycle in range(500):
        sim.step({})

    # Use render_trace() to debug if your code doesn't work.
    # sim_trace.render_trace()

    # You can also print out the register file or memory like so if you want to debug:
    # print(sim.inspect_mem(d_mem))
    # print(sim.inspect_mem(rf))

    # Perform some sanity checks to see if your program worked correctly
    assert(sim.inspect_mem(d_mem)[0] == 10)
    assert(sim.inspect_mem(rf)[8] == 10)    # $v0 = rf[8]
    print('Passed!')
