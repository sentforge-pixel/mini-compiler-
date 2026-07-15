"""
codegen.py - Code generator for MiniLang

Stage 6 of the pipeline. Translates the (optimized) TAC instructions
into bytecode for the simple stack-based virtual machine implemented
in vm.py.

Bytecode instructions (each a tuple):

    ('PUSH_CONST', value)      push an integer literal
    ('LOAD',  name)            push the value of variable `name`
    ('STORE', name)            pop the top of stack, store into `name`
    ('ADD') ('SUB') ('MUL') ('DIV')             pop b, pop a, push a op b
    ('LT') ('GT') ('LE') ('GE') ('EQ') ('NE')   pop b, pop a, push int(a op b)
    ('JMP', addr)              unconditional jump to instruction index `addr`
    ('JMP_IF_FALSE', addr)     pop value; if it's 0, jump to `addr`
    ('PRINT')                  pop and print the top of stack
    ('HALT')                   stop execution

Labels from the TAC (e.g. 'L0_while_start') are resolved into concrete
instruction indices in a two-pass process: first emit instructions with
label names as jump targets, then patch them to integer addresses once
every label's final position is known.
"""


BINOP_TO_INSTR = {"+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV"}
CMP_TO_INSTR = {"==": "EQ", "!=": "NE", "<": "LT", ">": "GT", "<=": "LE", ">=": "GE"}


def generate_bytecode(instructions):
    """Two-pass translation of TAC -> bytecode with resolved jump addresses."""
    bytecode = []          # list of instruction tuples, jump targets still label names
    label_positions = {}   # label name -> index into `bytecode`

    # Pass 1: emit instructions, recording where each label ends up.
    for instr in instructions:
        tag = instr[0]

        if tag == "LABEL":
            label_positions[instr[1]] = len(bytecode)
            continue

        if tag == "CONST":
            _, dest, value = instr
            bytecode.append(("PUSH_CONST", value))
            bytecode.append(("STORE", dest))
            continue

        if tag == "ASSIGN":
            _, dest, src = instr
            bytecode.append(("LOAD", src))
            bytecode.append(("STORE", dest))
            continue

        if tag == "BINOP":
            _, dest, op, left, right = instr
            bytecode.append(("LOAD", left))
            bytecode.append(("LOAD", right))
            bytecode.append((BINOP_TO_INSTR[op],))
            bytecode.append(("STORE", dest))
            continue

        if tag == "CMP":
            _, dest, op, left, right = instr
            bytecode.append(("LOAD", left))
            bytecode.append(("LOAD", right))
            bytecode.append((CMP_TO_INSTR[op],))
            bytecode.append(("STORE", dest))
            continue

        if tag == "GOTO":
            bytecode.append(("JMP", instr[1]))  # label name for now, patched below
            continue

        if tag == "IF_FALSE":
            _, cond, label = instr
            bytecode.append(("LOAD", cond))
            bytecode.append(("JMP_IF_FALSE", label))
            continue

        if tag == "PRINT":
            bytecode.append(("LOAD", instr[1]))
            bytecode.append(("PRINT",))
            continue

        raise ValueError(f"Unknown TAC instruction: {instr}")

    bytecode.append(("HALT",))

    # Pass 2: patch label names in jump instructions to concrete addresses.
    patched = []
    for instr in bytecode:
        if instr[0] in ("JMP", "JMP_IF_FALSE"):
            label = instr[1]
            if label not in label_positions:
                raise ValueError(f"Undefined label: {label}")
            patched.append((instr[0], label_positions[label]))
        else:
            patched.append(instr)

    return patched


def format_bytecode(bytecode):
    """Pretty-print bytecode with instruction addresses, for debugging."""
    lines = []
    for addr, instr in enumerate(bytecode):
        if len(instr) == 1:
            lines.append(f"{addr:3}: {instr[0]}")
        else:
            lines.append(f"{addr:3}: {instr[0]} {instr[1]}")
    return "\n".join(lines)


if __name__ == "__main__":
    from lexer import Lexer
    from parser import Parser
    from ir_generator import IRGenerator
    from optimizer import optimize

    sample = """
    i = 0;
    while (i < 3) {
        print(i);
        i = i + 1;
    }
    """
    tokens = Lexer(sample).tokenize()
    ast = Parser(tokens).parse()
    ir = optimize(IRGenerator().generate(ast))
    bytecode = generate_bytecode(ir)
    print(format_bytecode(bytecode))
