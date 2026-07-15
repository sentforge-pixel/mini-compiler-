"""
lexer.py - Lexical Analyzer for MiniLang

Converts raw source code (a string) into a list of Tokens.
This is Stage 1 of the compiler pipeline:

    source code --> [LEXER] --> tokens --> parser --> ...

MiniLang supports:
    - integer literals            : 5, 42, 0
    - identifiers                 : x, count, result
    - keywords                    : if, else, while, print
    - operators                   : + - * / = == != < > <= >=
    - punctuation                 : ( ) { } ;
"""


class Token:
    """A single lexical token: a type tag + the matched text + line number."""

    def __init__(self, type_, value, line):
        self.type = type_
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, line={self.line})"

    def __eq__(self, other):
        return (
            isinstance(other, Token)
            and self.type == other.type
            and self.value == other.value
        )


# Reserved words map directly to their own token type
KEYWORDS = {
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "print": "PRINT",
}


class LexerError(Exception):
    """Raised when the lexer encounters an unrecognized character."""
    pass


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.length = len(source)

    def error(self, message):
        raise LexerError(f"Lexer error on line {self.line}: {message}")

    def peek(self, offset=0):
        idx = self.pos + offset
        if idx < self.length:
            return self.source[idx]
        return None

    def advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
        return ch

    def tokenize(self):
        """Return the full list of Tokens for the source, ending in EOF."""
        tokens = []
        while self.pos < self.length:
            ch = self.peek()

            # Skip whitespace
            if ch in (" ", "\t", "\r", "\n"):
                self.advance()
                continue

            # Skip single-line comments: // ...
            if ch == "/" and self.peek(1) == "/":
                while self.pos < self.length and self.peek() != "\n":
                    self.advance()
                continue

            # Numbers (integers)
            if ch.isdigit():
                tokens.append(self._read_number())
                continue

            # Identifiers / keywords
            if ch.isalpha() or ch == "_":
                tokens.append(self._read_identifier())
                continue

            # Two-character operators
            two_char = self.source[self.pos:self.pos + 2]
            if two_char in ("==", "!=", "<=", ">="):
                start_line = self.line
                self.advance()
                self.advance()
                type_map = {
                    "==": "EQ", "!=": "NE", "<=": "LE", ">=": "GE"
                }
                tokens.append(Token(type_map[two_char], two_char, start_line))
                continue

            # Single-character tokens
            single_char_map = {
                "+": "PLUS", "-": "MINUS", "*": "STAR", "/": "SLASH",
                "=": "ASSIGN", "<": "LT", ">": "GT",
                "(": "LPAREN", ")": "RPAREN",
                "{": "LBRACE", "}": "RBRACE",
                ";": "SEMI",
            }
            if ch in single_char_map:
                start_line = self.line
                self.advance()
                tokens.append(Token(single_char_map[ch], ch, start_line))
                continue

            self.error(f"unexpected character {ch!r}")

        tokens.append(Token("EOF", None, self.line))
        return tokens

    def _read_number(self):
        start_line = self.line
        start = self.pos
        while self.pos < self.length and self.peek().isdigit():
            self.advance()
        text = self.source[start:self.pos]
        return Token("NUMBER", int(text), start_line)

    def _read_identifier(self):
        start_line = self.line
        start = self.pos
        while self.pos < self.length and (self.peek().isalnum() or self.peek() == "_"):
            self.advance()
        text = self.source[start:self.pos]
        tok_type = KEYWORDS.get(text, "IDENT")
        return Token(tok_type, text, start_line)


if __name__ == "__main__":
    # Quick manual smoke test when running this file directly
    sample = """
    x = 10;
    if (x > 5) {
        print(x);
    }
    """
    for tok in Lexer(sample).tokenize():
        print(tok)
