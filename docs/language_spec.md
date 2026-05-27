# Mini-C Language Specification

**Version:** 1.0  
**Date:** 2026-05-25  
**Status:** Final

---

## 1. Introduction

Mini-C is a statically-typed, imperative programming language that is a subset of the C
programming language. It supports integer and floating-point arithmetic, control flow
constructs, functions, arrays, structs, and pointers. Mini-C is designed as the source
language for an educational compiler targeting x86-64 assembly.

---

## 2. Lexical Elements

### 2.1 Character Set

Mini-C source files are encoded in ASCII. The following characters are significant:

- Letters: `a-z`, `A-Z`
- Digits: `0-9`
- Underscore: `_`
- Whitespace: space (` `), tab (`\t`), newline (`\n`), carriage return (`\r`)
- Special characters: `+ - * / % = ! < > & | ( ) { } [ ] ; , . "`

### 2.2 Keywords

The following identifiers are reserved as keywords and cannot be used as variable
or function names:

| Keyword    | Description                          |
|------------|--------------------------------------|
| `int`      | 32-bit signed integer type           |
| `float`    | 32-bit IEEE 754 floating-point type  |
| `void`     | No-value type (functions only)       |
| `if`       | Conditional branch                   |
| `else`     | Alternative conditional branch       |
| `for`      | Counted/conditional loop             |
| `while`    | Conditional loop                     |
| `return`   | Function return statement            |
| `struct`   | User-defined aggregate type          |

### 2.3 Identifiers

Identifiers name variables, functions, struct types, and struct members.

```
identifier ::= [a-zA-Z_][a-zA-Z0-9_]*
```

- Identifiers are case-sensitive (`foo` ≠ `Foo`).
- Maximum length: 255 characters.
- Identifiers must not collide with reserved keywords.

**Examples:** `x`, `count`, `_temp`, `myStruct2`, `MAX_SIZE`

### 2.4 Literals

#### 2.4.1 Integer Literals

```
integer_literal ::= [0-9]+
```

- Represent 32-bit signed integer values.
- Range: −2,147,483,648 to 2,147,483,647.
- Leading zeros are permitted but not meaningful (e.g., `007` equals `7`).

**Examples:** `0`, `42`, `1000`, `2147483647`

#### 2.4.2 Float Literals

```
float_literal ::= [0-9]+ '.' [0-9]+
```

- Represent 32-bit IEEE 754 single-precision floating-point values.
- Both the integer part and the fractional part are required.
- Scientific notation is **not** supported.

**Examples:** `3.14`, `0.0`, `100.5`, `0.001`

#### 2.4.3 String Literals (Optional Extension)

```
string_literal ::= '"' [^"\n]* '"'
```

- Enclosed in double quotes.
- Cannot span multiple lines.
- Supported escape sequences: `\\`, `\"`, `\n`, `\t`, `\0`.
- Strings are stored as null-terminated character arrays.

**Examples:** `"hello"`, `"world\n"`, `""`

### 2.5 Operators

#### 2.5.1 Arithmetic Operators

| Operator | Description       |
|----------|-------------------|
| `+`      | Addition          |
| `-`      | Subtraction / Unary negation |
| `*`      | Multiplication / Pointer dereference |
| `/`      | Division          |
| `%`      | Modulo (integers only) |

#### 2.5.2 Relational Operators

| Operator | Description            |
|----------|------------------------|
| `==`     | Equal to               |
| `!=`     | Not equal to           |
| `<`      | Less than              |
| `>`      | Greater than           |
| `<=`     | Less than or equal     |
| `>=`     | Greater than or equal  |

#### 2.5.3 Logical Operators

| Operator | Description  |
|----------|--------------|
| `&&`     | Logical AND  |
| `\|\|`   | Logical OR   |
| `!`      | Logical NOT  |

#### 2.5.4 Assignment Operator

| Operator | Description |
|----------|-------------|
| `=`      | Assignment  |

#### 2.5.5 Pointer / Address Operators

| Operator | Description          |
|----------|----------------------|
| `&`      | Address-of           |
| `*`      | Dereference (unary)  |

### 2.6 Delimiters

| Delimiter | Description                     |
|-----------|---------------------------------|
| `(`  `)`  | Function calls, grouping        |
| `{`  `}`  | Block / compound statements     |
| `[`  `]`  | Array subscript                 |
| `;`       | Statement terminator            |
| `,`       | Parameter/argument separator    |
| `.`       | Struct member access            |

### 2.7 Comments

Mini-C supports two styles of comments:

#### 2.7.1 Single-Line Comments

```
// Everything from // to end of line is a comment
```

#### 2.7.2 Multi-Line Comments

```
/* Everything between these delimiters
   is a comment, which may span
   multiple lines */
```

- Multi-line comments do **not** nest.
- Comments are treated as whitespace by the lexer.

### 2.8 Whitespace

Whitespace characters (space, tab, newline, carriage return) serve to separate tokens
and are otherwise ignored. At least one whitespace character (or comment) is required
between two adjacent keyword or identifier tokens.

---

## 3. Types

### 3.1 Primitive Types

| Type    | Size    | Description                              |
|---------|---------|------------------------------------------|
| `int`   | 4 bytes | 32-bit signed two's-complement integer   |
| `float` | 4 bytes | 32-bit IEEE 754 single-precision float   |
| `void`  | 0 bytes | No value; valid only as function return type |

### 3.2 Pointer Types

- `int*` — pointer to `int`
- `float*` — pointer to `float`
- Pointers are 8 bytes (64-bit addresses on x86-64).
- Only one level of indirection is supported (no `int**`).

### 3.3 Array Types

- Arrays are fixed-size, stack-allocated collections of a single type.
- Syntax: `type name[SIZE]` where `SIZE` is a positive integer literal.
- Array sizes must be compile-time integer constants.
- Array indices are zero-based.
- Out-of-bounds access is **undefined behavior**.

**Examples:**
```c
int arr[10];       // array of 10 ints
float vals[100];   // array of 100 floats
```

### 3.4 Struct Types

- User-defined aggregate types containing named fields.
- Fields may be `int`, `float`, pointer types, or fixed-size arrays.
- Structs may **not** contain other structs (no nested struct types).
- Struct variables are allocated on the stack.

**Example:**
```c
struct Point {
    int x;
    int y;
};
```

### 3.5 Type Compatibility and Implicit Conversions

| From    | To      | Conversion                          |
|---------|---------|-------------------------------------|
| `int`   | `float` | Implicit widening (int → float)     |
| `float` | `int`   | **Not allowed** (compile error)     |
| `int`   | `int*`  | **Not allowed**                     |
| `int*`  | `int`   | **Not allowed**                     |

- Arithmetic on mixed `int`/`float` operands: the `int` operand is implicitly
  promoted to `float`, and the result is `float`.
- Assignment: the right-hand side must be assignment-compatible with the
  left-hand side's type.

---

## 4. Grammar (EBNF)

The following grammar defines the syntax of Mini-C using Extended Backus-Naur Form.
Terminal symbols are shown in `'single quotes'` or as UPPERCASE token names.

```ebnf
(* ============================================================ *)
(* Top-Level Structure                                           *)
(* ============================================================ *)

program
    = { top_level_decl } ;

top_level_decl
    = struct_def
    | func_def
    | global_var_decl ;

(* ============================================================ *)
(* Struct Definitions                                            *)
(* ============================================================ *)

struct_def
    = 'struct' IDENTIFIER '{' { struct_field ';' } '}' ';' ;

struct_field
    = type_spec IDENTIFIER
    | type_spec IDENTIFIER '[' INT_LITERAL ']' ;

(* ============================================================ *)
(* Function Definitions                                          *)
(* ============================================================ *)

func_def
    = type_spec IDENTIFIER '(' param_list ')' compound_stmt ;

param_list
    = (* empty *)
    | param { ',' param } ;

param
    = type_spec IDENTIFIER
    | type_spec IDENTIFIER '[' ']' ;    (* array parameter, size omitted *)

(* ============================================================ *)
(* Global Variable Declarations                                  *)
(* ============================================================ *)

global_var_decl
    = type_spec IDENTIFIER [ '=' expression ] ';'
    | type_spec IDENTIFIER '[' INT_LITERAL ']' ';' ;

(* ============================================================ *)
(* Types                                                         *)
(* ============================================================ *)

type_spec
    = base_type [ '*' ] ;

base_type
    = 'int'
    | 'float'
    | 'void'
    | 'struct' IDENTIFIER ;

(* ============================================================ *)
(* Statements                                                    *)
(* ============================================================ *)

compound_stmt
    = '{' { block_item } '}' ;

block_item
    = local_var_decl
    | statement ;

local_var_decl
    = type_spec IDENTIFIER [ '=' expression ] ';'
    | type_spec IDENTIFIER '[' INT_LITERAL ']' ';' ;

statement
    = compound_stmt
    | expression_stmt
    | if_stmt
    | while_stmt
    | for_stmt
    | return_stmt ;

expression_stmt
    = expression ';'
    | ';' ;                             (* empty statement *)

if_stmt
    = 'if' '(' expression ')' statement [ 'else' statement ] ;

while_stmt
    = 'while' '(' expression ')' statement ;

for_stmt
    = 'for' '(' for_init ';' [ expression ] ';' [ expression ] ')' statement ;

for_init
    = local_var_decl_no_semi          (* e.g., int i = 0           *)
    | expression                       (* e.g., i = 0               *)
    | (* empty *) ;

local_var_decl_no_semi
    = type_spec IDENTIFIER [ '=' expression ] ;

return_stmt
    = 'return' [ expression ] ';' ;

(* ============================================================ *)
(* Expressions (by increasing precedence — lowest first)         *)
(* ============================================================ *)

expression
    = assignment_expr ;

assignment_expr
    = logical_or_expr [ '=' assignment_expr ] ;    (* right-associative *)

logical_or_expr
    = logical_and_expr { '||' logical_and_expr } ;

logical_and_expr
    = equality_expr { '&&' equality_expr } ;

equality_expr
    = relational_expr { ( '==' | '!=' ) relational_expr } ;

relational_expr
    = additive_expr { ( '<' | '>' | '<=' | '>=' ) additive_expr } ;

additive_expr
    = multiplicative_expr { ( '+' | '-' ) multiplicative_expr } ;

multiplicative_expr
    = unary_expr { ( '*' | '/' | '%' ) unary_expr } ;

unary_expr
    = postfix_expr
    | '-' unary_expr                   (* unary negation *)
    | '!' unary_expr                   (* logical NOT    *)
    | '&' unary_expr                   (* address-of     *)
    | '*' unary_expr ;                 (* dereference    *)

postfix_expr
    = primary_expr { postfix_op } ;

postfix_op
    = '(' arg_list ')'                 (* function call   *)
    | '[' expression ']'               (* array subscript *)
    | '.' IDENTIFIER ;                 (* member access   *)

arg_list
    = (* empty *)
    | expression { ',' expression } ;

primary_expr
    = IDENTIFIER
    | INT_LITERAL
    | FLOAT_LITERAL
    | STRING_LITERAL
    | '(' expression ')' ;

(* ============================================================ *)
(* Lexical Tokens (for reference)                                *)
(* ============================================================ *)

IDENTIFIER    = [a-zA-Z_][a-zA-Z0-9_]* ;
INT_LITERAL   = [0-9]+ ;
FLOAT_LITERAL = [0-9]+ '.' [0-9]+ ;
STRING_LITERAL= '"' { any_char_except_newline_and_quote | escape_seq } '"' ;
escape_seq    = '\\' ( 'n' | 't' | '\\' | '"' | '0' ) ;
```

---

## 5. Operator Precedence and Associativity

Operators are listed from **highest** precedence (top) to **lowest** precedence (bottom).

| Precedence | Operator(s)              | Description                  | Associativity  |
|:----------:|--------------------------|------------------------------|:--------------:|
| 1          | `()` `[]` `.`            | Call, subscript, member      | Left-to-right  |
| 2          | `-` `!` `&` `*` (unary) | Negation, NOT, addr, deref   | Right-to-left  |
| 3          | `*` `/` `%`             | Multiplication, division, mod| Left-to-right  |
| 4          | `+` `-`                 | Addition, subtraction        | Left-to-right  |
| 5          | `<` `>` `<=` `>=`       | Relational comparison        | Left-to-right  |
| 6          | `==` `!=`               | Equality comparison          | Left-to-right  |
| 7          | `&&`                    | Logical AND                  | Left-to-right  |
| 8          | `\|\|`                  | Logical OR                   | Left-to-right  |
| 9          | `=`                     | Assignment                   | Right-to-left  |

**Notes:**
- Parentheses `()` can be used to override precedence in any expression.
- The unary `*` (dereference) and binary `*` (multiplication) are disambiguated by
  context: unary `*` appears where an operand is expected (prefix position), while
  binary `*` appears between two operands (infix position).
- Similarly, unary `-` (negation) vs. binary `-` (subtraction) is resolved by position.

---

## 6. Scoping Rules

### 6.1 Scope Levels

Mini-C uses **lexical (static) scoping** with the following scope levels:

1. **Global Scope** — The outermost scope. Contains:
   - Global variable declarations
   - Function definitions
   - Struct type definitions

2. **Function Scope** — Created by each function definition. Contains:
   - The function's formal parameters.
   - Parameters are accessible throughout the entire function body.

3. **Block Scope** — Created by each compound statement `{ ... }`. Contains:
   - Local variable declarations within the block.
   - A block scope is nested inside its enclosing scope.

### 6.2 Name Resolution

- When a name is referenced, the compiler searches scopes from innermost to outermost.
- The first matching declaration is used (inner scopes **shadow** outer scopes).
- A name must be **declared before use** (no forward references for variables).
- Functions may be called before their definition if a prototype appears earlier
  (forward declarations are allowed for functions only via the grammar — a function
  definition itself serves as its declaration).

### 6.3 Name Uniqueness

- No two declarations in the **same scope** may share the same name.
- Struct type names and variable/function names occupy separate namespaces
  (a variable may be named `Point` even if `struct Point` exists).

### 6.4 Lifetime

- **Global variables** persist for the entire program execution.
- **Local variables** and **parameters** are allocated on the stack frame
  and are destroyed when their enclosing scope exits.

---

## 7. Semantic Rules

### 7.1 Type Checking

1. **Arithmetic operations** (`+`, `-`, `*`, `/`):
   - Both operands must be numeric (`int` or `float`).
   - If either operand is `float`, the other is promoted to `float`;
     the result type is `float`.
   - If both are `int`, the result is `int`.

2. **Modulo** (`%`):
   - Both operands must be `int`. Result is `int`.

3. **Relational and equality operators** (`<`, `>`, `<=`, `>=`, `==`, `!=`):
   - Both operands must be numeric.
   - Mixed `int`/`float` follows the same promotion rule.
   - Result type is always `int` (0 for false, 1 for true).

4. **Logical operators** (`&&`, `||`, `!`):
   - Operands must be numeric or pointer types.
   - Zero is false; any non-zero value is true.
   - Result type is `int`.

5. **Assignment** (`=`):
   - The left-hand side must be an **lvalue** (variable, array element,
     struct member, or dereferenced pointer).
   - The right-hand side must be type-compatible with the left-hand side.
   - `int` can be assigned to `float` (implicit promotion).
   - `float` cannot be assigned to `int` (error).

### 7.2 Function Rules

1. Every program **must** contain a function named `main` that returns `int`.
2. A function's return type must match the type of the expression in its
   `return` statement(s). A `void` function must use `return;` with no expression.
3. The number and types of arguments in a function call must match the
   function's parameter list.
4. Recursive calls are permitted.
5. Functions may not be defined inside other functions (no nested functions).

### 7.3 Array Rules

1. Array size must be a positive integer literal (compile-time constant).
2. Array indexing uses zero-based indices.
3. The index expression must evaluate to type `int`.
4. Arrays are passed to functions by reference (pointer to first element).
5. Arrays may not be assigned as a whole (`arr1 = arr2` is illegal).
6. Multi-dimensional arrays are not directly supported; simulate with
   1D arrays and manual index calculation.

### 7.4 Struct Rules

1. Struct types must be defined before use.
2. Struct members are accessed with the `.` operator.
3. Structs may be passed to and returned from functions by value.
4. Struct assignment copies all fields (`p1 = p2` is valid if same struct type).

### 7.5 Pointer Rules

1. The `&` operator may only be applied to lvalues.
2. The `*` (dereference) operator may only be applied to pointer types.
3. Pointer arithmetic is **not** supported (no `ptr + 1`).
4. Pointers may be compared with `==` and `!=`.
5. The null pointer is represented by the integer literal `0`.

### 7.6 Control Flow Rules

1. The condition expression in `if`, `while`, and `for` must be numeric or pointer.
2. `for` loop: the init clause may declare a new variable scoped to the loop body.
3. `break` and `continue` are **not** supported in this version.

---

## 8. Program Structure

A valid Mini-C program consists of:

1. Zero or more **struct definitions** (global only).
2. Zero or more **global variable declarations**.
3. One or more **function definitions**, one of which must be `int main()`.

The order of top-level declarations is significant only in that:
- Struct types must be defined before variables/parameters of that type.
- Functions must be defined before they are called (single-pass compilation),
  unless forward-declared.

---

## 9. Example Program

```c
// Compute the sum of an array using a helper function

int sum(int arr[], int n) {
    int total = 0;
    for (int i = 0; i < n; i = i + 1) {
        total = total + arr[i];
    }
    return total;
}

int main() {
    int data[5];
    data[0] = 10;
    data[1] = 20;
    data[2] = 30;
    data[3] = 40;
    data[4] = 50;
    int result = sum(data, 5);
    return result;
}
```

---

## 10. Differences from Standard C

| Feature                   | Standard C           | Mini-C                      |
|---------------------------|----------------------|-----------------------------|
| Preprocessor (`#include`) | Yes                  | No                          |
| Multiple indirection      | `int **p`            | Single level only           |
| Pointer arithmetic        | Yes                  | No                          |
| `switch`/`case`           | Yes                  | No                          |
| `break`/`continue`        | Yes                  | No                          |
| `do-while`                | Yes                  | No                          |
| `typedef`                 | Yes                  | No                          |
| `enum`                    | Yes                  | No                          |
| `union`                   | Yes                  | No                          |
| Nested structs            | Yes                  | No                          |
| Variable-length arrays    | C99+                 | No                          |
| Multi-dim arrays          | Yes                  | Simulate with 1D            |
| String type               | `char*` / `char[]`   | Optional `"..."` literals   |
| Standard library          | `<stdio.h>` etc.     | No (only built-in `main`)   |
| Casting                   | `(type)expr`         | No                          |
| Comma operator            | Yes                  | No                          |
| Ternary operator          | `?:`                 | No                          |
| Compound assignment       | `+=`, `-=`, etc.     | No                          |
| Increment/decrement       | `++`, `--`           | No (use `x = x + 1`)       |

---

*End of Mini-C Language Specification v1.0*
