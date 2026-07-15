"""
parser.py - Recursive-descent parser for MiniLang

Turns the token stream (from lexer.py) into an AST (nodes from ast_nodes.py).

Grammar (EBNF-ish):

    program     := statement* EOF
    statement   := assign_stmt | if_stmt | while_stmt | print_stmt
    assign_stmt := IDENT '=' expr ';'
    if_stmt     := 'if' '(' expr ')' block ('else' block)?
    while_stmt  := 'while' '(' expr ')' block
    print_stmt  := 'print' '(' expr ')' ';'
    block       := '{' statement* '}'

    expr        := arith (( '==' | '!=' | '<' | '>' | '<=' | '>=' ) arith)?
    arith       := term (('+' | '-') term)*
    term        := factor (('*' | '/') factor)*
    factor      := NUMBER | IDENT | '(' expr ')' | '-' factor
"""

from ast_nodes import (
    Program, Num, Var, BinOp, Compare, UnaryOp,
    Assign, Print, Block, If, While,
)


class ParserError(Exception):
    """Raised on a malformed MiniLang program."""
    pass


COMPARISON_OPS = {"EQ", "NE", "LT", "GT", "LE", "GE"}
COMPARISON_SYMBOLS = {
    "EQ": "==", "NE": "!=", "LT": "<", "GT": ">", "LE": "<=", "GE": ">=",
}


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # -- token helpers --------------------------------------------------

    def current(self):
        return self.tokens[self.pos]

    def check(self, type_):
        return self.current().type == type_

    def advance(self):
        tok = self.tokens[self.pos]
        if tok.type != "EOF":
            self.pos += 1
        return tok

    def expect(self, type_):
        tok = self.current()
        if tok.type != type_:
            raise ParserError(
                f"Line {tok.line}: expected {type_} but got {tok.type} "
                f"({tok.value!r})"
            )
        return self.advance()

    # -- grammar rules ----------------------------------------------------

    def parse(self):
        statements = []
        while not self.check("EOF"):
            statements.append(self.statement())
        return Program(statements)

    def block(self):
        self.expect("LBRACE")
        statements = []
        while not self.check("RBRACE"):
            statements.append(self.statement())
        self.expect("RBRACE")
        return Block(statements)

    def statement(self):
        tok = self.current()

        if tok.type == "IF":
            return self.if_statement()
        if tok.type == "WHILE":
            return self.while_statement()
        if tok.type == "PRINT":
            return self.print_statement()
        if tok.type == "IDENT":
            return self.assign_statement()

        raise ParserError(
            f"Line {tok.line}: unexpected token {tok.type} ({tok.value!r}) "
            f"at start of statement"
        )

    def assign_statement(self):
        name_tok = self.expect("IDENT")
        line = name_tok.line
        self.expect("ASSIGN")
        expr = self.expr()
        self.expect("SEMI")
        return Assign(name_tok.value, expr, line=line)

    def print_statement(self):
        line = self.expect("PRINT").line
        self.expect("LPAREN")
        expr = self.expr()
        self.expect("RPAREN")
        self.expect("SEMI")
        return Print(expr, line=line)

    def if_statement(self):
        line = self.expect("IF").line
        self.expect("LPAREN")
        condition = self.expr()
        self.expect("RPAREN")
        then_block = self.block()
        else_block = None
        if self.check("ELSE"):
            self.advance()
            else_block = self.block()
        return If(condition, then_block, else_block, line=line)

    def while_statement(self):
        line = self.expect("WHILE").line
        self.expect("LPAREN")
        condition = self.expr()
        self.expect("RPAREN")
        body = self.block()
        return While(condition, body, line=line)

    # -- expressions (precedence climbing) ---------------------------------

    def expr(self):
        left = self.arith()
        if self.current().type in COMPARISON_OPS:
            op_tok = self.advance()
            right = self.arith()
            return Compare(COMPARISON_SYMBOLS[op_tok.type], left, right, line=op_tok.line)
        return left

    def arith(self):
        node = self.term()
        while self.current().type in ("PLUS", "MINUS"):
            op_tok = self.advance()
            op = "+" if op_tok.type == "PLUS" else "-"
            right = self.term()
            node = BinOp(op, node, right, line=op_tok.line)
        return node

    def term(self):
        node = self.factor()
        while self.current().type in ("STAR", "SLASH"):
            op_tok = self.advance()
            op = "*" if op_tok.type == "STAR" else "/"
            right = self.factor()
            node = BinOp(op, node, right, line=op_tok.line)
        return node

    def factor(self):
        tok = self.current()

        if tok.type == "NUMBER":
            self.advance()
            return Num(tok.value, line=tok.line)

        if tok.type == "IDENT":
            self.advance()
            return Var(tok.value, line=tok.line)

        if tok.type == "MINUS":
            self.advance()
            operand = self.factor()
            return UnaryOp("-", operand, line=tok.line)

        if tok.type == "LPAREN":
            self.advance()
            node = self.expr()
            self.expect("RPAREN")
            return node

        raise ParserError(f"Line {tok.line}: unexpected token {tok.type} in expression")


if __name__ == "__main__":
    from lexer import Lexer

    sample = """
    x = 10;
    if (x > 5) {
        print(x);
    } else {
        print(0);
    }
    """
    tokens = Lexer(sample).tokenize()
    ast = Parser(tokens).parse()
    for stmt in ast.statements:
        print(stmt)
