"""
tests/test_compiler.py - Automated tests for the Mini Compiler

Run with:
    python -m pytest tests/          (if pytest is installed), or
    python tests/test_compiler.py    (plain unittest runner, no dependencies)

These tests exercise the full pipeline (lexer -> parser -> semantic
analysis -> IR -> optimizer -> codegen -> VM) using the public
compile_and_capture() helper, plus a couple of focused unit tests for
individual stages.
"""

import sys
import os
import io
import contextlib
import unittest

# Make the project root importable when running this file directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lexer import Lexer
from parser import Parser, ParserError
from semantic_analyzer import SemanticAnalyzer, SemanticError
from ir_generator import IRGenerator
from optimizer import optimize
from codegen import generate_bytecode
from vm import VM


def compile_and_capture(source: str):
    """Run the full pipeline and return the list of printed values."""
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    SemanticAnalyzer().analyze(ast)
    ir = optimize(IRGenerator().generate(ast))
    bytecode = generate_bytecode(ir)

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        output = VM(bytecode).run()
    return output


class TestArithmetic(unittest.TestCase):
    def test_operator_precedence(self):
        source = "x = 2 + 3 * 4; print(x);"
        self.assertEqual(compile_and_capture(source), [14])

    def test_parentheses_override_precedence(self):
        source = "x = (2 + 3) * 4; print(x);"
        self.assertEqual(compile_and_capture(source), [20])

    def test_unary_minus(self):
        source = "x = -5 + 10; print(x);"
        self.assertEqual(compile_and_capture(source), [5])

    def test_division_is_integer_division(self):
        source = "x = 7 / 2; print(x);"
        self.assertEqual(compile_and_capture(source), [3])


class TestControlFlow(unittest.TestCase):
    def test_if_true_branch(self):
        source = "x = 10; if (x > 5) { print(1); } else { print(0); }"
        self.assertEqual(compile_and_capture(source), [1])

    def test_if_false_branch(self):
        source = "x = 2; if (x > 5) { print(1); } else { print(0); }"
        self.assertEqual(compile_and_capture(source), [0])

    def test_if_without_else_skips_when_false(self):
        source = "x = 2; if (x > 5) { print(999); } print(42);"
        self.assertEqual(compile_and_capture(source), [42])

    def test_while_loop_factorial(self):
        source = """
        n = 5;
        result = 1;
        i = 1;
        while (i <= n) {
            result = result * i;
            i = i + 1;
        }
        print(result);
        """
        self.assertEqual(compile_and_capture(source), [120])

    def test_nested_while_loops(self):
        source = """
        total = 0;
        i = 0;
        while (i < 3) {
            j = 0;
            while (j < 3) {
                total = total + 1;
                j = j + 1;
            }
            i = i + 1;
        }
        print(total);
        """
        self.assertEqual(compile_and_capture(source), [9])


class TestComparisons(unittest.TestCase):
    def test_all_comparison_operators(self):
        cases = [
            ("print(1 < 2);", 1), ("print(2 < 1);", 0),
            ("print(2 > 1);", 1), ("print(1 > 2);", 0),
            ("print(3 == 3);", 1), ("print(3 == 4);", 0),
            ("print(3 != 4);", 1), ("print(3 != 3);", 0),
            ("print(3 <= 3);", 1), ("print(3 >= 3);", 1),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(compile_and_capture(source), [expected])


class TestSemanticErrors(unittest.TestCase):
    def test_undefined_variable_raises(self):
        tokens = Lexer("print(y);").tokenize()
        ast = Parser(tokens).parse()
        with self.assertRaises(SemanticError):
            SemanticAnalyzer().analyze(ast)


class TestSyntaxErrors(unittest.TestCase):
    def test_missing_semicolon_raises(self):
        tokens = Lexer("x = 5").tokenize()
        with self.assertRaises(ParserError):
            Parser(tokens).parse()


class TestOptimizer(unittest.TestCase):
    def test_constant_folding_reduces_instruction_count(self):
        source = "x = 2 + 3 * 4; print(x);"
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        ir = IRGenerator().generate(ast)
        optimized = optimize(ir)
        # every BINOP should have folded away into CONSTs
        self.assertFalse(any(instr[0] == "BINOP" for instr in optimized))


if __name__ == "__main__":
    unittest.main(verbosity=2)
