# Mini Compiler

A small compiler for **MiniLang**, a toy language with integers,
variables, arithmetic, comparisons, `if`/`else`, `while` loops, and
`print`. Built in Python as a compiler-construction learning project,
following the classic multi-stage pipeline:

```
source (.mini)
    │
    ▼
  Lexer            lexer.py              → tokens
    │
    ▼
  Parser           parser.py             → AST (ast_nodes.py)
    │
    ▼
  Semantic         semantic_analyzer.py  → checked AST
  Analyzer
    │
    ▼
  IR Generator     ir_generator.py       → three-address code (TAC)
    │
    ▼
  Optimizer        optimizer.py          → optimized TAC (constant folding)
    │
    ▼
  Code Generator   codegen.py            → stack-machine bytecode
    │
    ▼
  Virtual Machine  vm.py                 → program output
```

`main.py` wires every stage together into one CLI tool.

## Language (MiniLang)

```
n = 5;
result = 1;
i = 1;
while (i <= n) {
    result = result * i;
    i = i + 1;
}
print(result);   // 120
```

Supported features:
- Integer literals and variables
- Arithmetic: `+ - * /` with standard precedence and parentheses
- Comparisons: `== != < > <= >=`
- `if (cond) { ... } else { ... }` (else optional)
- `while (cond) { ... }`
- `print(expr);`
- `// comment` (single-line)

## Project layout

```
mini_compiler/
├── lexer.py               Tokenizer
├── ast_nodes.py           AST node class definitions
├── parser.py               Recursive-descent parser → AST
├── semantic_analyzer.py   Checks variables are defined before use
├── ir_generator.py        Lowers AST → three-address code (TAC)
├── optimizer.py           Constant folding pass over TAC
├── codegen.py             Lowers TAC → stack-machine bytecode
├── vm.py                  Stack-based bytecode interpreter
├── main.py                CLI entry point
├── examples/              Sample .mini programs
│   ├── factorial.mini
│   ├── if_else.mini
│   └── arithmetic.mini
└── tests/
    └── test_compiler.py   Automated test suite (unittest)
```

## Usage

Run a program:

```bash
python main.py examples/factorial.mini
```

Inspect intermediate stages:

```bash
python main.py examples/factorial.mini --show-ir         # optimized TAC
python main.py examples/factorial.mini --show-bytecode   # stack bytecode
python main.py examples/factorial.mini --show-all        # both
```

Run the test suite:

```bash
python tests/test_compiler.py
```

## Example: how `y = (2 + 3) * 4;` moves through the pipeline

1. **Lexer**: `IDENT(y) ASSIGN LPAREN NUMBER(2) PLUS NUMBER(3) RPAREN STAR NUMBER(4) SEMI`
2. **Parser (AST)**: `Assign(y, BinOp(*, BinOp(+, 2, 3), 4))`
3. **IR (TAC)**:
   ```
   t0 = 2
   t1 = 3
   t2 = t0 + t1
   t3 = 4
   t4 = t2 * t3
   y = t4
   ```
4. **Optimizer**: folds constants down to `y = 20`
5. **Bytecode**: `PUSH_CONST 20 / STORE y`
6. **VM**: stores `20` in variable `y`

## Extending it

Ideas for taking this further:
- Add more types (e.g. booleans, strings)
- Add functions/procedures with parameters and a call stack
- Add `for` loops (desugar to `while` in the parser or IR generator)
- Add more optimizations: dead-code elimination, common subexpression elimination
- Target real assembly (x86/ARM) or LLVM IR instead of the toy bytecode/VM
