"""
ast_nodes.py - Abstract Syntax Tree node definitions for MiniLang

The parser (stage 2) builds a tree of these nodes out of the token
stream produced by the lexer. Every later stage (semantic analysis,
IR generation) walks this tree.

    tokens --> [PARSER] --> AST (these node types) --> semantic analyzer --> ...
"""


class Node:
    """Base class - useful for isinstance checks and a generic repr."""

    def __repr__(self):
        fields = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({fields})"


class Program(Node):
    """The root node: a sequence of statements."""
    def __init__(self, statements):
        self.statements = statements


class Num(Node):
    """An integer literal, e.g. 42."""
    def __init__(self, value, line=None):
        self.value = value
        self.line = line


class Var(Node):
    """A reference to a variable, e.g. x."""
    def __init__(self, name, line=None):
        self.name = name
        self.line = line


class BinOp(Node):
    """A binary arithmetic operation: left <op> right, op in + - * /."""
    def __init__(self, op, left, right, line=None):
        self.op = op
        self.left = left
        self.right = right
        self.line = line


class Compare(Node):
    """A comparison: left <op> right, op in == != < > <= >=."""
    def __init__(self, op, left, right, line=None):
        self.op = op
        self.left = left
        self.right = right
        self.line = line


class UnaryOp(Node):
    """A unary operation, currently only unary minus: -expr."""
    def __init__(self, op, operand, line=None):
        self.op = op
        self.operand = operand
        self.line = line


class Assign(Node):
    """An assignment statement: name = expr;"""
    def __init__(self, name, expr, line=None):
        self.name = name
        self.expr = expr
        self.line = line


class Print(Node):
    """A print statement: print(expr);"""
    def __init__(self, expr, line=None):
        self.expr = expr
        self.line = line


class Block(Node):
    """A brace-delimited list of statements: { stmt* }"""
    def __init__(self, statements):
        self.statements = statements


class If(Node):
    """An if statement, with an optional else branch."""
    def __init__(self, condition, then_block, else_block=None, line=None):
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block  # Block or None
        self.line = line


class While(Node):
    """A while loop."""
    def __init__(self, condition, body, line=None):
        self.condition = condition
        self.body = body
        self.line = line
