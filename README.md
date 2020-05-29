# AGH compilers course
### tc
Interpreter for a simple language. 

Features:
* strong typing
* variable and function definitions
* proper name scoping
* lexical closures
* some optimizations: 
  * redundant code removal and reusing common
  subexpressions based on reaching definitions 
  * trivial algebraic optimizations

### parsing
basic parser generators for LL(1), SLR(1), LALR(1) and LR(1) grammars (WIP)
