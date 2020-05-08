from collections import defaultdict
from pg.error import ConflictError, InputError
from pg.util import END, EPS, first, follow


def insert(table, non_terminal, terminal, num_prod):
    if terminal in table[non_terminal]:
        cur_num_prod = table[non_terminal][terminal]
        raise ConflictError(f'Conflict for ({non_terminal}, {terminal}): {cur_num_prod} and {num_prod}')
    else:
        table[non_terminal][terminal] = num_prod
    

def build_table(grammar):
    first_sets = first(grammar)
    follow_sets = follow(grammar, first_sets)

    parse_table = defaultdict(dict)
    for i, prod in enumerate(grammar.productions):
        nt = prod[0]

        if len(prod) == 2 and prod[1] == EPS:
            # Empty production
            for t in follow_sets[nt]:
                insert(parse_table, nt, t, i)
        else:
            for j, symbol in enumerate(prod[1:]):
                for t in first_sets[symbol]:
                    insert(parse_table, nt, t, i)
                
                if EPS not in first_sets[symbol]:
                    break
            else:
                for t in follow_sets[nt]:
                    insert(parse_table, nt, t, i)

    return dict(parse_table)


class LLParser:
    def __init__(self, grammar):
        self.grammar = grammar
        self.table = build_table(grammar)

    def run(self, string):
        string.append(END)

        stack = [self.grammar.start]
        derivation = []
        
        pos = 0
        # TODO: infinite loop on certain incorrect input?
        while stack:
            t, N = string[pos], stack[-1]

            if N in self.grammar.terminals:
                if t != N:
                    raise InputError(f'Error at {pos}: terminal mismatch, in: {t}, expected: {N}') 
                stack.pop()
                pos += 1
            else:
                num_prod = self.table[N].get(t, None)
                if num_prod is None:
                    raise InputError(f'Error at {pos}: no matching production for input {t} and non-terminal {N}')                
                
                self.apply(stack, self.grammar.productions[num_prod])
                derivation.append(num_prod)

        if pos < len(string) - 1:
            raise InputError(f'Input remaining: {"".join(string[pos:-1])}')

        return derivation

    @staticmethod
    def apply(stack, production):
        if len(production) == 2 and production[1] == EPS:
            # Empty production
            stack.pop()
        else:
            stack.pop()
            stack.extend(reversed(production[1:]))

