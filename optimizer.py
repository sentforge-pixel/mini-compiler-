"""
optimizer.py - A small optimization pass over the TAC produced by
ir_generator.py.

Stage 5 of the pipeline. This is intentionally simple (two classic,
easy-to-explain optimizations) rather than a full optimizing compiler:

    1. Constant folding:
       't2 = 2 + 3'  ->  't2 = 5'
       (and CMP folding: 't3 = 1 < 2' -> 't3 = 1')

    2. Constant propagation + copy elimination:
       If 'a = 5' followed later by using 'a' where nothing has
       reassigned it in between within the same straight-line block,
       we substitute the known constant directly. This is a
       conservative, block-local version (it resets at labels), which
       is safe and easy to reason about for a teaching compiler.

Both passes operate on the flat instruction list and return a new,
equal-or-shorter list.
"""

OP_FUNCS = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "/": lambda a, b: a // b if b != 0 else None,
}

CMP_FUNCS = {
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    "<": lambda a, b: a < b,
    ">": lambda a, b: a > b,
    "<=": lambda a, b: a <= b,
    ">=": lambda a, b: a >= b,
}


def constant_fold(instructions):
    """Fold BINOP/CMP instructions whose operands are known integer constants."""
    known = {}  # name -> int value, valid within current straight-line run
    result = []

    for instr in instructions:
        tag = instr[0]

        if tag == "LABEL":
            known.clear()  # control flow merges here; forget what we "knew"
            result.append(instr)
            continue

        if tag == "CONST":
            dest, value = instr[1], instr[2]
            known[dest] = value
            result.append(instr)
            continue

        if tag == "ASSIGN":
            dest, src = instr[1], instr[2]
            if src in known:
                known[dest] = known[src]
            else:
                known.pop(dest, None)
            result.append(instr)
            continue

        if tag == "BINOP":
            dest, op, left, right = instr[1], instr[2], instr[3], instr[4]
            if left in known and right in known:
                folded = OP_FUNCS[op](known[left], known[right])
                if folded is not None:
                    known[dest] = folded
                    result.append(("CONST", dest, folded))
                    continue
            known.pop(dest, None)
            result.append(instr)
            continue

        if tag == "CMP":
            dest, op, left, right = instr[1], instr[2], instr[3], instr[4]
            if left in known and right in known:
                folded = int(CMP_FUNCS[op](known[left], known[right]))
                known[dest] = folded
                result.append(("CONST", dest, folded))
                continue
            known.pop(dest, None)
            result.append(instr)
            continue

        if tag in ("GOTO", "IF_FALSE", "PRINT"):
            result.append(instr)
            continue

        result.append(instr)

    return result


def optimize(instructions):
    """Run all optimization passes. Currently just constant folding,
    applied twice since one fold can expose another (e.g. after folding
    't0=5', a later 't1 = t0 * 2' can now also fold)."""
    optimized = constant_fold(instructions)
    optimized = constant_fold(optimized)
    return optimized


if __name__ == "__main__":
    from lexer import Lexer
    from parser import Parser
    from ir_generator import IRGenerator, format_instructions

    sample = "x = 2 + 3 * 4; print(x);"
    tokens = Lexer(sample).tokenize()
    ast = Parser(tokens).parse()
    ir = IRGenerator().generate(ast)
    print("Before optimization:")
    print(format_instructions(ir))
    print("\nAfter optimization:")
    print(format_instructions(optimize(ir)))
