"""
ir_generator.py - Intermediate Representation generator for MiniLang

Stage 4 of the pipeline. Lowers the AST into a flat list of simple
three-address code (TAC) instructions - the classic compiler IR that
sits between the source-level AST and the target machine code.

Each instruction is a tuple. The instruction set is small on purpose:

    ('ASSIGN', dest, src)              dest = src
    ('CONST',  dest, value)            dest = <int literal>
    ('BINOP',  dest, op, left, right)  dest = left <op> right   (op: + - * /)
    ('CMP',    dest, op, left, right)  dest = left <op> right   (op: == != < > <= >=)
    ('LABEL',  name)                   name:
    ('GOTO',   name)                   jump to label
    ('IF_FALSE', cond, name)           jump to label if cond is 0 (false)
    ('PRINT',  src)                    print value of src

"dest"/"src"/"left"/"right" are either a variable name (str) or a
temporary name like "t0", "t1", ... generated here to hold intermediate
results, e.g. for `y = (x + 1) * 2`:

    t0 = x + 1
    t1 = t0 * 2
    y  = t1
"""

from ast_nodes import (
    Program, Num, Var, BinOp, Compare, UnaryOp,
    Assign, Print, Block, If, While,
)


class IRGenerator:
    def __init__(self):
        self.instructions = []
        self.temp_count = 0
        self.label_count = 0

    def new_temp(self):
        name = f"t{self.temp_count}"
        self.temp_count += 1
        return name

    def new_label(self, hint):
        name = f"L{self.label_count}_{hint}"
        self.label_count += 1
        return name

    def emit(self, instruction):
        self.instructions.append(instruction)

    def generate(self, program: Program):
        for stmt in program.statements:
            self.visit_statement(stmt)
        return self.instructions

    # -- statements ---------------------------------------------------

    def visit_statement(self, node):
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name)
        method(node)

    def visit_Assign(self, node: Assign):
        src = self.visit_expr(node.expr)
        self.emit(("ASSIGN", node.name, src))

    def visit_Print(self, node: Print):
        src = self.visit_expr(node.expr)
        self.emit(("PRINT", src))

    def visit_If(self, node: If):
        cond = self.visit_expr(node.condition)
        else_label = self.new_label("else")
        end_label = self.new_label("endif")

        if node.else_block is not None:
            self.emit(("IF_FALSE", cond, else_label))
            for stmt in node.then_block.statements:
                self.visit_statement(stmt)
            self.emit(("GOTO", end_label))
            self.emit(("LABEL", else_label))
            for stmt in node.else_block.statements:
                self.visit_statement(stmt)
            self.emit(("LABEL", end_label))
        else:
            self.emit(("IF_FALSE", cond, end_label))
            for stmt in node.then_block.statements:
                self.visit_statement(stmt)
            self.emit(("LABEL", end_label))

    def visit_While(self, node: While):
        start_label = self.new_label("while_start")
        end_label = self.new_label("while_end")

        self.emit(("LABEL", start_label))
        cond = self.visit_expr(node.condition)
        self.emit(("IF_FALSE", cond, end_label))
        for stmt in node.body.statements:
            self.visit_statement(stmt)
        self.emit(("GOTO", start_label))
        self.emit(("LABEL", end_label))

    # -- expressions (return the name holding the result) ----------------

    def visit_expr(self, node):
        if isinstance(node, Num):
            dest = self.new_temp()
            self.emit(("CONST", dest, node.value))
            return dest

        if isinstance(node, Var):
            return node.name

        if isinstance(node, BinOp):
            left = self.visit_expr(node.left)
            right = self.visit_expr(node.right)
            dest = self.new_temp()
            self.emit(("BINOP", dest, node.op, left, right))
            return dest

        if isinstance(node, Compare):
            left = self.visit_expr(node.left)
            right = self.visit_expr(node.right)
            dest = self.new_temp()
            self.emit(("CMP", dest, node.op, left, right))
            return dest

        if isinstance(node, UnaryOp):
            # Represent unary minus as (0 - operand)
            operand = self.visit_expr(node.operand)
            zero = self.new_temp()
            self.emit(("CONST", zero, 0))
            dest = self.new_temp()
            self.emit(("BINOP", dest, "-", zero, operand))
            return dest

        raise ValueError(f"No IR handler for expression type {type(node).__name__}")


def format_instructions(instructions):
    """Pretty-print a TAC instruction list, mainly for debugging/teaching."""
    lines = []
    for instr in instructions:
        tag = instr[0]
        if tag == "LABEL":
            lines.append(f"{instr[1]}:")
        elif tag == "GOTO":
            lines.append(f"    goto {instr[1]}")
        elif tag == "IF_FALSE":
            lines.append(f"    if_false {instr[1]} goto {instr[2]}")
        elif tag == "CONST":
            lines.append(f"    {instr[1]} = {instr[2]}")
        elif tag == "ASSIGN":
            lines.append(f"    {instr[1]} = {instr[2]}")
        elif tag == "BINOP":
            lines.append(f"    {instr[1]} = {instr[3]} {instr[2]} {instr[4]}")
        elif tag == "CMP":
            lines.append(f"    {instr[1]} = {instr[3]} {instr[2]} {instr[4]}")
        elif tag == "PRINT":
            lines.append(f"    print {instr[1]}")
        else:
            lines.append(f"    {instr}")
    return "\n".join(lines)


if __name__ == "__main__":
    from lexer import Lexer
    from parser import Parser

    sample = """
    result = 1;
    i = 1;
    while (i <= 5) {
        result = result * i;
        i = i + 1;
    }
    print(result);
    """
    tokens = Lexer(sample).tokenize()
    ast = Parser(tokens).parse()
    ir = IRGenerator().generate(ast)
    print(format_instructions(ir))
