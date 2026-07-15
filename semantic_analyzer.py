"""
semantic_analyzer.py - Semantic analysis for MiniLang

Stage 3 of the pipeline. Walks the AST produced by parser.py and checks
things the grammar alone can't guarantee, e.g.:

    - a variable is not read before it has been assigned
    - (extensible: type checks, if the language grows beyond integers)

MiniLang only has one type (integer), so this stage is intentionally
small, but it's structured so more checks can be added without touching
earlier stages - that's the whole point of separating semantic analysis
from parsing.
"""

from ast_nodes import (
    Program, Num, Var, BinOp, Compare, UnaryOp,
    Assign, Print, Block, If, While,
)


class SemanticError(Exception):
    """Raised when a program is syntactically valid but semantically wrong."""
    pass


class SymbolTable:
    """Tracks which variable names have been defined so far."""

    def __init__(self):
        self.defined = set()

    def declare(self, name):
        self.defined.add(name)

    def is_declared(self, name):
        return name in self.defined


class SemanticAnalyzer:
    def __init__(self):
        self.symbols = SymbolTable()

    def analyze(self, program: Program):
        for stmt in program.statements:
            self.visit_statement(stmt)
        return self.symbols

    # -- statements ---------------------------------------------------

    def visit_statement(self, node):
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, None)
        if method is None:
            raise SemanticError(f"No semantic handler for node type {type(node).__name__}")
        method(node)

    def visit_Assign(self, node: Assign):
        self.visit_expr(node.expr)
        self.symbols.declare(node.name)

    def visit_Print(self, node: Print):
        self.visit_expr(node.expr)

    def visit_If(self, node: If):
        self.visit_expr(node.condition)
        for stmt in node.then_block.statements:
            self.visit_statement(stmt)
        if node.else_block is not None:
            for stmt in node.else_block.statements:
                self.visit_statement(stmt)

    def visit_While(self, node: While):
        self.visit_expr(node.condition)
        for stmt in node.body.statements:
            self.visit_statement(stmt)

    # -- expressions ----------------------------------------------------

    def visit_expr(self, node):
        if isinstance(node, Num):
            return
        if isinstance(node, Var):
            if not self.symbols.is_declared(node.name):
                raise SemanticError(
                    f"Line {node.line}: variable '{node.name}' used before assignment"
                )
            return
        if isinstance(node, (BinOp, Compare)):
            self.visit_expr(node.left)
            self.visit_expr(node.right)
            return
        if isinstance(node, UnaryOp):
            self.visit_expr(node.operand)
            return
        raise SemanticError(f"No semantic handler for expression type {type(node).__name__}")


if __name__ == "__main__":
    from lexer import Lexer
    from parser import Parser

    # This should raise a SemanticError: y is used before it's assigned
    bad_program = "x = 1; print(y);"
    tokens = Lexer(bad_program).tokenize()
    ast = Parser(tokens).parse()
    try:
        SemanticAnalyzer().analyze(ast)
        print("No error raised (unexpected)")
    except SemanticError as e:
        print(f"Caught expected error: {e}")

    # This should pass cleanly
    good_program = "x = 1; y = x + 2; print(y);"
    tokens = Lexer(good_program).tokenize()
    ast = Parser(tokens).parse()
    SemanticAnalyzer().analyze(ast)
    print("Good program passed semantic analysis")
