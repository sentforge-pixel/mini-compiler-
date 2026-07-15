"""
vm.py - A tiny stack-based virtual machine for MiniLang bytecode

Stage 7 (the "back end") of the pipeline. Executes the bytecode list
produced by codegen.py, exactly the way a real target machine (or a
bytecode interpreter like CPython's) would: fetch instruction, execute,
advance program counter, repeat until HALT.

This is what actually lets you *run* a compiled MiniLang program and
see its output, which is the best way to prove every earlier stage
(lexer -> parser -> semantic analysis -> IR -> optimizer -> codegen)
did its job correctly.
"""


class VMError(Exception):
    """Raised for runtime errors: stack underflow, division by zero, etc."""
    pass


class VM:
    def __init__(self, bytecode):
        self.bytecode = bytecode
        self.stack = []
        self.variables = {}
        self.pc = 0            # program counter
        self.output = []       # collected PRINT output, useful for testing

    def push(self, value):
        self.stack.append(value)

    def pop(self):
        if not self.stack:
            raise VMError("Stack underflow")
        return self.stack.pop()

    def run(self):
        while True:
            if self.pc >= len(self.bytecode):
                raise VMError("Ran off the end of the program without HALT")

            instr = self.bytecode[self.pc]
            op = instr[0]

            if op == "HALT":
                break

            elif op == "PUSH_CONST":
                self.push(instr[1])
                self.pc += 1

            elif op == "LOAD":
                name = instr[1]
                if name not in self.variables:
                    raise VMError(f"Runtime error: variable '{name}' not defined")
                self.push(self.variables[name])
                self.pc += 1

            elif op == "STORE":
                name = instr[1]
                self.variables[name] = self.pop()
                self.pc += 1

            elif op in ("ADD", "SUB", "MUL", "DIV"):
                b = self.pop()
                a = self.pop()
                if op == "ADD":
                    self.push(a + b)
                elif op == "SUB":
                    self.push(a - b)
                elif op == "MUL":
                    self.push(a * b)
                elif op == "DIV":
                    if b == 0:
                        raise VMError("Runtime error: division by zero")
                    self.push(a // b)
                self.pc += 1

            elif op in ("LT", "GT", "LE", "GE", "EQ", "NE"):
                b = self.pop()
                a = self.pop()
                result = {
                    "LT": a < b, "GT": a > b, "LE": a <= b,
                    "GE": a >= b, "EQ": a == b, "NE": a != b,
                }[op]
                self.push(int(result))
                self.pc += 1

            elif op == "JMP":
                self.pc = instr[1]

            elif op == "JMP_IF_FALSE":
                value = self.pop()
                if value == 0:
                    self.pc = instr[1]
                else:
                    self.pc += 1

            elif op == "PRINT":
                value = self.pop()
                print(value)
                self.output.append(value)
                self.pc += 1

            else:
                raise VMError(f"Unknown bytecode instruction: {instr}")

        return self.output


if __name__ == "__main__":
    from lexer import Lexer
    from parser import Parser
    from ir_generator import IRGenerator
    from optimizer import optimize
    from codegen import generate_bytecode

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
    ir = optimize(IRGenerator().generate(ast))
    bytecode = generate_bytecode(ir)
    print("Running program (expect 120 = 5!):")
    VM(bytecode).run()
